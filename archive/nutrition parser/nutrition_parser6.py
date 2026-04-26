import json
import re

INPUT = "normalized_dataset.jsonl"
OUTPUT = "parsed_dataset_v6.jsonl"


def normalize(text):
    text = text.lower()
    text = text.replace("\n", " ")
    text = text.replace(",", " ")
    return text


def safe_float(val):
    try:
        val = val.replace("<", "").strip()
        return float(val)
    except:
        return None


# ===== STRICT PATTERN (PRIMARY) =====
def extract_strict(keyword, text, unit):
    pattern = rf"{keyword}[^0-9<]*([<]?[0-9]+\.?[0-9]*)\s*{unit}"
    match = re.search(pattern, text)
    if match:
        return safe_float(match.group(1))
    return None


# ===== LOOSE PATTERN (FALLBACK) =====
def extract_loose(text):
    return re.findall(r"([a-z\s]+?)\s*\(?\s*([<]?[0-9]+\.?[0-9]*)\s*(kcal|g|mg)\s*\)?", text)


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

    # ===== STEP 1: STRICT EXTRACTION =====
    data["energy_kcal"] = extract_strict("energy", text, "kcal")
    data["protein_g"] = extract_strict("protein", text, "g")
    data["carbohydrate_g"] = extract_strict("carbohydrate", text, "g")
    data["sugar_g"] = extract_strict("sugars?", text, "g")
    data["added_sugar_g"] = extract_strict("added sugars?", text, "g")
    data["fat_g"] = extract_strict("fat", text, "g")
    data["saturated_fat_g"] = extract_strict("saturated", text, "g")
    data["trans_fat_g"] = extract_strict("trans", text, "g")
    data["fiber_g"] = extract_strict("(?:fibre|fiber)", text, "g")

    sodium = extract_strict("sodium", text, "mg")
    salt = extract_strict("salt", text, "g")

    if sodium:
        data["sodium_mg"] = sodium
    elif salt:
        data["sodium_mg"] = salt * 400

    # ===== STEP 2: FALLBACK (ONLY IF MISSING) =====
    matches = extract_loose(text)

    for label, value, unit in matches:

        value = safe_float(value)
        if value is None:
            continue

        label = label.strip()

        if data["energy_kcal"] is None and "energy" in label and unit == "kcal":
            data["energy_kcal"] = value

        elif data["protein_g"] is None and "protein" in label:
            data["protein_g"] = value

        elif data["carbohydrate_g"] is None and ("carbohydrate" in label or "carbs" in label):
            data["carbohydrate_g"] = value

        elif data["added_sugar_g"] is None and "added sugar" in label:
            data["added_sugar_g"] = value

        elif data["sugar_g"] is None and "sugar" in label:
            data["sugar_g"] = value

        elif data["saturated_fat_g"] is None and "saturated" in label:
            data["saturated_fat_g"] = value

        elif data["trans_fat_g"] is None and "trans" in label:
            data["trans_fat_g"] = value

        elif data["fat_g"] is None and "fat" in label:
            data["fat_g"] = value

        elif data["fiber_g"] is None and ("fibre" in label or "fiber" in label):
            data["fiber_g"] = value

        elif data["sodium_mg"] is None and "sodium" in label:
            data["sodium_mg"] = value

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