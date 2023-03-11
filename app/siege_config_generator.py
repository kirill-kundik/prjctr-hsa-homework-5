import random
import urllib.parse

from faker import Faker

ACTIONS = ["POST", "GET"]
ACTORS = ["mongo", "elastic"]
SIEGE_URLS_PATH = "../siege/urls.txt"

fake = Faker()
fake.set_arguments("5_sentences", {"nb_sentences": 5})
fake.set_arguments("2000_chars", {"max_nb_chars": 2000})


def generate_payload(num_rows=0):
    if not num_rows:
        num_rows = fake.pyint(min_value=2, max_value=10)

    data_columns = {
        "username": "user_name",
        "email": "email",
        "description": "paragraph:5_sentences",
        "text": "text:2000_chars",
    }

    return fake.json(data_columns=data_columns, num_rows=num_rows)


def generate_query(num_words=1):
    if num_words > 1:
        return urllib.parse.quote(" ".join(fake.words(nb=num_words)))
    else:
        return fake.word()


def generate_urls(num=100):
    rows = ["BASE_URL=http://localhost:8181"]

    for _ in range(num):
        action = random.choice(ACTIONS)
        actor = random.choice(ACTORS)

        if action == "POST":
            row = f"$(BASE_URL)/{actor} {action} {generate_payload()}"
        else:
            row = f"$(BASE_URL)/{actor}?q={generate_query()}"

        rows.append(row)

    return rows


def main():
    rows = generate_urls(1000)

    with open(SIEGE_URLS_PATH, "w") as f:
        for row in rows:
            print(row, file=f)


if __name__ == "__main__":
    main()
