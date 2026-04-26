import requests
import json
import time

BASE_URL = "https://www.bigbasket.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

# PC categories to scrape
CATEGORIES = [
    ("snacks-branded-foods", "biscuits-cookies"),
    ("snacks-branded-foods", "chocolates-candies"),
    ("snacks-branded-foods", "noodles-pasta"),
    ("snacks-branded-foods", "snacks-namkeen"),
    ("snacks-branded-foods", "spreads-sauces-ketchup"),
    ("snacks-branded-foods", "pickles-chutney"),
    ("snacks-branded-foods", "ready-to-cook-eat"),
    ("snacks-branded-foods", "breakfast-cereals"),
]

OUTPUT_FILE = "product_ids.jsonl"


def fetch_page(parent, sub, page):
    url = f"https://www.bigbasket.com/pc/{parent}/{sub}/?page={page}"
    res = requests.get(url, headers=HEADERS)

    if res.status_code != 200:
        return None

    return res.text


def extract_products(html):
    import re

    pattern = r'"id":\s*"(\d+)"'
    ids = re.findall(pattern, html)

    return list(set(ids))


def save_product(record):
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


for parent, sub in CATEGORIES:

    print(f"\nScanning category: {parent}/{sub}")

    page = 1

    while True:

        print(f"Page {page}")

        html = fetch_page(parent, sub, page)

        if not html:
            break

        product_ids = extract_products(html)

        if not product_ids:
            print("No more products")
            break

        for pid in product_ids:

            record = {
                "product_id": pid,
                "category": parent,
                "subcategory": sub
            }

            save_product(record)

        page += 1
        time.sleep(2)

print("\nFinished collecting product IDs")