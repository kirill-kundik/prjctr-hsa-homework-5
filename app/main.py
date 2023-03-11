import os
import time

from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk
from fastapi import FastAPI, Request, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from statsd import StatsClient

# START OF MONKEY-PATCHING ObjectId response rendering error
import pydantic
from bson import ObjectId

pydantic.json.ENCODERS_BY_TYPE[ObjectId] = str
# END OF MONKEY-PATCHING

STATUS_OK = {"success": True}

stats = StatsClient("telegraf", 8125, prefix="performance")

es = AsyncElasticsearch(f"http://{os.environ['ELASTIC_HOST']}:{os.environ['ELASTIC_PORT']}")

mongo = AsyncIOMotorClient(
    f"mongodb://{os.environ['MONGO_USER']}:{os.environ['MONGO_PASS']}@{os.environ['MONGO_HOST']}:{os.environ['MONGO_PORT']}/"
)
mongo_db = mongo["fastapi"]

app = FastAPI()


@app.on_event("startup")
async def startup():
    if not (await es.indices.exists(index="fastapi")):
        await es.indices.create(index="fastapi")


@app.on_event("shutdown")
async def shutdown():
    await es.close()


@app.get("/elastic")
async def get_elastic_handler(q: str):
    result = await es.search(
        index="fastapi", body={"query": {"multi_match": {"query": q}}}
    )

    return {"data": result, **STATUS_OK, }


@app.post("/elastic")
async def post_elastic_handler(request: Request):
    body = await request.json()

    if type(body) != list:
        raise HTTPException(status_code=400, detail="Body must include a JSON-array.")

    await async_bulk(es, [{"_index": "fastapi", "doc": doc} for doc in body])

    return STATUS_OK


@app.get("/mongo")
async def get_elastic_handler(q: str):
    cursor = mongo_db.test_collection.find({"name": {"$regex": q}})

    return {"data": await cursor.to_list(length=100), **STATUS_OK, }


@app.post("/mongo")
async def post_elastic_handler(request: Request):
    body = await request.json()

    if type(body) != list:
        raise HTTPException(status_code=400, detail="Body must include a JSON-array.")

    await mongo_db.test_collection.insert_many(body)

    return STATUS_OK


@app.middleware("statsd")
async def statsd_middleware(request: Request, call_next):
    start = time.monotonic_ns()

    response = await call_next(request)

    executed_time_ms = (time.monotonic_ns() - start) // 1_000_000

    actor = request.url.path.strip("/")

    if actor in ("elastic", "mongo"):
        action = "write" if request.method == "POST" else "read"

        with stats.pipeline() as pipe:
            pipe.incr(f"request.successful.count,type={actor},action={action}", 1)
            pipe.timing(f"request.successful.time,type={actor},action={action}", executed_time_ms)

    response.headers["X-Process-Time"] = str(executed_time_ms)

    return response
