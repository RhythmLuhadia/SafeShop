import json
import re

INPUT = "normalized_dataset.jsonl"
OUTPUT = "parsed_dataset1.jsonl"


def extract(pattern, text):
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return None
    try:
        return float(match.group(1))
    except:
        return None


def parse_nutrition(text):

    if not text:
        return {}

    data = {}

    data["energy_kcal"] = extract(r"energy.*?([0-9]+\.?[0-9]*)\s*kcal", text)
    data["protein_g"] = extract(r"protein.*?([0-9]+\.?[0-9]*)\s*g", text)
    data["carbohydrate_g"] = extract(r"carbohydrate.*?([0-9]+\.?[0-9]*)\s*g", text)
    data["sugar_g"] = extract(r"sugars?.*?([0-9]+\.?[0-9]*)\s*g", text)
    data["added_sugar_g"] = extract(r"added sugars?.*?([0-9]+\.?[0-9]*)\s*g", text)
    data["fat_g"] = extract(r"total fat.*?([0-9]+\.?[0-9]*)\s*g", text)
    data["saturated_fat_g"] = extract(r"saturated.*?([0-9]+\.?[0-9]*)\s*g", text)
    data["trans_fat_g"] = extract(r"trans.*?([0-9]+\.?[0-9]*)\s*g", text)
    data["fiber_g"] = extract(r"(fiber|fibre).*?([0-9]+\.?[0-9]*)\s*g", text)
    data["sodium_mg"] = extract(r"sodium.*?([0-9]+\.?[0-9]*)\s*mg", text)

    return data


count = 0

with open(INPUT, "r", encoding="utf-8") as infile, \
     open(OUTPUT, "w", encoding="utf-8") as outfile:

    for line in infile:

        try:
            product = json.loads(line)
        except:
            continue

        nutrition_text = product.get("nutrition", "")

        product["parsed_nutrition"] = parse_nutrition(nutrition_text)

        outfile.write(json.dumps(product, ensure_ascii=False) + "\n")

        count += 1

print("Processed:", count)