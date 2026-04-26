import json
import re
from collections import Counter

INPUT = "normalized_dataset.jsonl"

counter = Counter()

# words that are useless alone
STOPWORDS = {
    "powder","agent","substance","substances","extract",
    "product","pieces","added","flavour","flavouring",
    "flavouring substance","condiments"
}

def clean_text(text):

    text = text.lower()

    # remove brackets
    text = re.sub(r"\(.*?\)", "", text)

    # remove punctuation
    text = re.sub(r"[^\w\s,]", " ", text)

    # normalize spaces
    text = re.sub(r"\s+", " ", text)

    return text


def split_ingredients(text):

    return re.split(r",| and | with | contains ", text)


def normalize(ing):

    ing = ing.strip()

    if len(ing) < 3:
        return None

    if ing in STOPWORDS:
        return None

    # normalization rules
    if "refined wheat flour" in ing or "maida" in ing:
        return "refined wheat flour"

    if "whole wheat flour" in ing:
        return "whole wheat flour"

    if "palm oil" in ing or "palmolein" in ing:
        return "palm oil"

    if "sunflower oil" in ing:
        return "sunflower oil"

    if "soybean oil" in ing:
        return "soybean oil"

    if "citric acid" in ing:
        return "citric acid"

    if "sodium bicarbonate" in ing:
        return "sodium bicarbonate"

    if "salt" in ing or "iodised salt" in ing:
        return "salt"

    if "sugar" in ing:
        return "sugar"

    return ing


with open(INPUT) as f:

    for line in f:

        product = json.loads(line)

        ingredients = product.get("ingredients","")

        cleaned = clean_text(ingredients)

        parts = split_ingredients(cleaned)

        for p in parts:

            norm = normalize(p)

            if norm:
                counter[norm]+=1


for ing,count in counter.most_common(200):

    print(f"{ing} : {count}")


with open("clean_ingredients.txt","w") as f:

    for ing,count in counter.most_common():
        f.write(f"{ing},{count}\n")


print("\nSaved clean ingredient list.")