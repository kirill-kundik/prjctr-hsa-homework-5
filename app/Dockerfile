FROM python:3.10-alpine

RUN apk add --no-cache bash

WORKDIR /app

COPY requirements.txt /app
RUN python -m pip install \
    --no-cache \
    --disable-pip-version-check \
    -r requirements.txt

COPY main.py /app
COPY wait-for-it.sh /app

RUN chmod a+x wait-for-it.sh

EXPOSE 8080

CMD ["./wait-for-it.sh", "elasticsearch:9200", "--", "uvicorn", "main:app", "--workers=4", "--host=0.0.0.0", "--port=8080"]
