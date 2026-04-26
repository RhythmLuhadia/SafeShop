import json
import re

INPUT = "normalized_dataset.jsonl"
OUTPUT = "ingredient_intel_dataset.jsonl"


# ===== PATTERN BANK =====

SUGAR_KEYWORDS = [
    "sugar", "glucose", "glucose syrup", "fructose",
    "maltose", "dextrose", "corn syrup", "invert syrup",
    "caramel", "molasses"
]

REFINED_GRAINS = [
    "maida", "refined wheat flour", "wheat flour",
    "white flour", "corn flour", "rice flour"
]

BAD_OILS = [
    "palm oil", "palmolein", "hydrogenated oil",
    "refined vegetable oil", "shortening"
]

GOOD_SIGNALS = [
    "whole wheat", "oats", "millets", "brown rice",
    "multigrain"
]

ULTRA_PROCESSED_HINTS = [
    "flavour", "flavouring", "emulsifier",
    "stabilizer", "stabiliser", "thickener",
    "maltodextrin", "modified starch"
]


# ===== NORMALIZE =====
def normalize(text):
    return text.lower()


# ===== MAIN INTELLIGENCE =====
def analyze_ingredient_intelligence(text):

    if not text:
        return {}

    text = normalize(text)

    signals = {
        "has_added_sugar": False,
        "high_refined_grain": False,
        "has_bad_oil": False,
        "has_good_grain": False,
        "ultra_processed": False,
        "clean_label": True
    }

    # ===== SUGAR =====
    sugar_hits = sum(1 for s in SUGAR_KEYWORDS if s in text)
    if sugar_hits > 0:
        signals["has_added_sugar"] = True

    # ===== REFINED GRAIN =====
    refined_hits = sum(1 for g in REFINED_GRAINS if g in text)
    if refined_hits > 0:
        signals["high_refined_grain"] = True

    # ===== GOOD GRAINS =====
    if any(g in text for g in GOOD_SIGNALS):
        signals["has_good_grain"] = True

    # ===== BAD OILS =====
    if any(oil in text for oil in BAD_OILS):
        signals["has_bad_oil"] = True

    # ===== ULTRA PROCESSED =====
    if any(u in text for u in ULTRA_PROCESSED_HINTS):
        signals["ultra_processed"] = True

    # ===== CLEAN LABEL =====
    negative_flags = [
        signals["has_added_sugar"],
        signals["high_refined_grain"],
        signals["has_bad_oil"],
        signals["ultra_processed"]
    ]

    if any(negative_flags):
        signals["clean_label"] = False

    return signals


# ===== DATASET PROCESS =====
count = 0

with open(INPUT, "r", encoding="utf-8") as infile, \
     open(OUTPUT, "w", encoding="utf-8") as outfile:

    for line in infile:

        try:
            product = json.loads(line)
        except:
            continue

        ingredients = product.get("ingredients", "")

        product["ingredient_signals"] = analyze_ingredient_intelligence(ingredients)

        outfile.write(json.dumps(product, ensure_ascii=False) + "\n")

        count += 1


print("Processed:", count)