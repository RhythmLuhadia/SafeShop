import json
import re

INPUT = "safeshop_dataset.jsonl"
OUTPUT = "normalized_dataset.jsonl"


# ===== NORMALIZATION MAP =====
NORMALIZATION_MAP = {
    "maida": "refined wheat flour",
    "atta": "whole wheat flour",
    "lodised salt": "salt",
    "lodized salt": "salt",
    "iodised salt": "salt",

    "palmolein": "palm oil",
    "hydrogenated vegetable fats": "hydrogenated oil",
    "hydrogenated oils": "hydrogenated oil",

    "monosodium glutamate": "ins621",
    "msg": "ins621",

    "sweetner": "sweetener",
}


# ===== GENERIC MAP =====
GENERIC_MAP = {
    "emulsifier": "generic_emulsifier",
    "stabilizer": "generic_stabilizer",
    "stabilisers": "generic_stabilizer",

    "raising agent": "raising_agent",
    "raising agents": "raising_agent",

    "acidity regulator": "acidity_regulator",
    "acid": "acidity_regulator",
    "acidulant": "acidity_regulator",

    "preservative": "generic_preservative",
    "preservatives": "generic_preservative",

    "anticaking agent": "anti_caking",

    "colour": "colour",
    "colours": "colour",

    "flavour": "flavour",
    "flavours": "flavour",

    "antioxidant": "antioxidant",
    "antioxidants": "antioxidant",
}


# ===== CLEAN TEXT =====
def clean_text(text):
    text = text.lower()

    text = re.sub(r"\(.*?\)", "", text)
    text = re.sub(r"\{.*?\}", "", text)
    text = re.sub(r"\[.*?\]", "", text)

    text = re.sub(r"ingredients?:", "", text)

    text = re.sub(r"[^a-z0-9,.\s]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ===== SPLIT SMART =====
def smart_split(text):

    # split by comma and dot
    parts = re.split(r",|\.", text)

    final = []

    for p in parts:

        # split big phrases further
        sub = re.split(
            r"\band\b|with|mix|blend|powder|extract|sauce|cream",
            p
        )

        final.extend(sub)

    return [x.strip() for x in final if x.strip()]


# ===== NORMALIZE TOKEN =====
def normalize_token(token):

    # remove numbers
    token = re.sub(r"\b\d+\b", "", token).strip()

    if len(token) < 3:
        return None

    # additive conversion
    if re.fullmatch(r"\d{3,4}", token):
        return f"ins{token}"

    if token.startswith("e") and token[1:].isdigit():
        return f"ins{token[1:]}"

    # mapping
    for k, v in NORMALIZATION_MAP.items():
        if k in token:
            return v

    for k, v in GENERIC_MAP.items():
        if k in token:
            return v

    return token


# ===== FINAL NORMALIZER =====
def normalize_ingredients(text):

    if not text:
        return []

    text = clean_text(text)

    tokens = smart_split(text)

    result = []

    for t in tokens:
        norm = normalize_token(t)

        if not norm:
            continue

        # remove garbage tokens
        if len(norm) < 3:
            continue

        result.append(norm)

    return list(set(result))


# ===== MAIN =====
with open(INPUT, encoding="utf-8") as infile, \
     open(OUTPUT, "w", encoding="utf-8") as outfile:

    count = 0

    for line in infile:
        product = json.loads(line)

        ing = product.get("ingredients", "")

        product["ingredients"] = normalize_ingredients(ing)

        outfile.write(json.dumps(product, ensure_ascii=False) + "\n")
        count += 1

print("✅ Done:", count)