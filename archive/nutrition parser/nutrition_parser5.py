import json
import re

INPUT = "normalized_dataset.jsonl"
OUTPUT = "parsed_dataset_v5.jsonl"


def normalize(text):
    text = text.lower()
    text = text.replace("\n", " ")
    text = text.replace(":", " ")
    text = text.replace(",", " ")
    return text


# extract ALL numeric values with units
def extract_all_values(text):
    return re.findall(r"([a-z\s]+?)\s*\(?\s*([0-9]+\.?[0-9]*)\s*(kcal|g|mg)\s*\)?", text)


def parse_nutrition(text):

    if not text or text.strip() == "0":
        return {}

    raw_text = text
    text = normalize(text)

    data = {
        "energy_kcal": None,
        "protein_g": None,
        "carbohydrate_g": None,
        "sugar_g": None,
        "added_sugar_g": None,
        "fat_g": None,
        "saturated_fat_g": None,
        "trans_fat_g": None,
        "fiber_g": None,
        "sodium_mg": None
    }

    matches = extract_all_values(text)

    for label, value, unit in matches:

        try:
            value = float(value)
        except:
            continue

        label = label.strip()

        if "energy" in label and unit == "kcal":
            data["energy_kcal"] = value

        elif "protein" in label:
            data["protein_g"] = value

        elif "carbohydrate" in label or "carbs" in label:
            data["carbohydrate_g"] = value

        elif "added sugar" in label:
            data["added_sugar_g"] = value

        elif "sugar" in label:
            data["sugar_g"] = value

        elif "saturated" in label:
            data["saturated_fat_g"] = value

        elif "trans" in label:
            data["trans_fat_g"] = value

        elif "fat" in label:
            data["fat_g"] = value

        elif "fibre" in label or "fiber" in label:
            data["fiber_g"] = value

        elif "sodium" in label:
            data["sodium_mg"] = value

        elif "salt" in label:
            data["sodium_mg"] = value * 400  # convert

    # ===== CONFIDENCE =====
    total = len(data)
    found = sum(1 for v in data.values() if v is not None)
    confidence = found / total

    data["confidence"] = round(confidence, 2)

    if confidence < 0.3:
        data["raw_text"] = raw_text

    return data


# ===== MAIN LOOP =====
count = 0
low_conf = 0

with open(INPUT, "r", encoding="utf-8") as infile, \
     open(OUTPUT, "w", encoding="utf-8") as outfile:

    for line in infile:

        try:
            product = json.loads(line)
        except:
            continue

        parsed = parse_nutrition(product.get("nutrition", ""))

        product["parsed_nutrition"] = parsed

        if parsed.get("confidence", 0) < 0.5:
            low_conf += 1

        outfile.write(json.dumps(product, ensure_ascii=False) + "\n")
        count += 1


print("\n✅ Processing Complete")
print("Total Products:", count)
print("Low Confidence Cases:", low_conf)
print("Output:", OUTPUT)