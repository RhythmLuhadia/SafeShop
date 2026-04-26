import json
import re

INPUT = "parsed_dataset_v8_1.jsonl"
OUTPUT = "parsed_dataset_v8_2.jsonl"


# ===== NORMALIZATION =====
def normalize(text):
    text = text.lower()
    text = text.replace("\n", " ")
    text = text.replace(",", " ")
    text = text.replace("-", " ")
    text = text.replace("–", " ")
    text = text.replace("?", " ")
    return text


# ===== SAFE FLOAT =====
def safe_float(val):
    try:
        if "%" in val:
            return None
        val = val.replace("<", "").strip()
        return float(val)
    except:
        return None


# ===== LABEL (UNIT) VALUE =====
def extract_label_unit_value(keyword, text, unit):
    pattern = rf"{keyword}\s*\(\s*{unit}\s*\)\s*[:\-–]?\s*\(?\s*([<]?[0-9]+\.?[0-9]*)\s*\)?"
    match = re.search(pattern, text)
    if match:
        return safe_float(match.group(1))
    return None


# ===== STRICT =====
def extract_strict(keyword, text, unit):
    pattern = rf"{keyword}[^0-9<]*([<]?[0-9]+\.?[0-9]*)\s*{unit}"
    match = re.search(pattern, text)
    if match:
        return safe_float(match.group(1))
    return None


# ===== NO UNIT =====
def extract_no_unit(keyword, text):
    pattern = rf"{keyword}[^0-9]*([0-9]+\.?[0-9]*)"
    match = re.search(pattern, text)
    if match:
        return safe_float(match.group(1))
    return None


# ===== SANITY FILTER =====
def clean_value(val, key):
    if val is None:
        return None

    if key == "carbohydrate_g" and val > 150:
        return None
    if key == "protein_g" and val > 100:
        return None
    if key == "fat_g" and val > 80:
        return None

    return val


# ===== MAIN PARSER =====
def parse_incremental(text, existing):

    if not text or text.strip() == "0":
        return existing if existing else {}

    raw_text = text
    text = normalize(text)

    data = existing.copy() if existing else {}

    keys = [
        "energy_kcal", "protein_g", "carbohydrate_g",
        "sugar_g", "added_sugar_g", "fat_g",
        "saturated_fat_g", "trans_fat_g",
        "fiber_g", "sodium_mg"
    ]

    for k in keys:
        if k not in data:
            data[k] = None

    # ===== EXTRACTION =====
    if data["energy_kcal"] is None:
        data["energy_kcal"] = extract_label_unit_value("(energy|energy value)", text, "kcal")
    if data["energy_kcal"] is None:
        data["energy_kcal"] = extract_strict("(energy|calories)", text, "kcal")

    if data["protein_g"] is None:
        data["protein_g"] = extract_label_unit_value("(protein|proteins)", text, "g")
    if data["protein_g"] is None:
        data["protein_g"] = extract_strict("(protein|proteins)", text, "g")

    if data["carbohydrate_g"] is None:
        data["carbohydrate_g"] = extract_label_unit_value("(carbohydrate|carbohydrates)", text, "g")
    if data["carbohydrate_g"] is None:
        data["carbohydrate_g"] = extract_strict("(carbohydrate|carbohydrates)", text, "g")

    if data["sugar_g"] is None:
        data["sugar_g"] = extract_label_unit_value("(sugar|sugars|total sugar)", text, "g")
    if data["sugar_g"] is None:
        data["sugar_g"] = extract_strict("(sugar|sugars|total sugar)", text, "g")

    if data["added_sugar_g"] is None:
        data["added_sugar_g"] = extract_label_unit_value("added sugars?", text, "g")

    if data["fat_g"] is None:
        data["fat_g"] = extract_label_unit_value("(fat|total fat)", text, "g")
    if data["fat_g"] is None:
        data["fat_g"] = extract_strict("(fat|total fat)", text, "g")

    if data["saturated_fat_g"] is None:
        data["saturated_fat_g"] = extract_label_unit_value("(saturated fat|saturated)", text, "g")

    if data["trans_fat_g"] is None:
        data["trans_fat_g"] = extract_label_unit_value("trans", text, "g")

    if data["fiber_g"] is None:
        data["fiber_g"] = extract_label_unit_value("(fibre|fiber|dietary fibre)", text, "g")

    if data["sodium_mg"] is None:
        data["sodium_mg"] = extract_label_unit_value("sodium", text, "mg")
    if data["sodium_mg"] is None:
        data["sodium_mg"] = extract_strict("sodium", text, "mg")

    # ===== FALLBACK =====
    if data["protein_g"] is None:
        data["protein_g"] = extract_no_unit("protein", text)
    if data["sugar_g"] is None:
        data["sugar_g"] = extract_no_unit("sugar", text)

    # ===== CLEAN =====
    for k in keys:
        data[k] = clean_value(data[k], k)

    if data["sodium_mg"] and data["sodium_mg"] < 10:
        data["sodium_mg"] *= 1000

    # ===== CONFIDENCE =====
    essential = ["energy_kcal", "protein_g", "carbohydrate_g", "fat_g"]
    found = sum(1 for k in essential if data.get(k) is not None)
    data["confidence"] = round(found / len(essential), 2)

    # always keep raw text (debug phase)
    data["raw_text"] = raw_text

    return data


# ===== MAIN LOOP =====
count = 0
low_conf = 0
valid_nutrition = 0

with open(INPUT, "r", encoding="utf-8") as infile, \
     open(OUTPUT, "w", encoding="utf-8") as outfile:

    for line in infile:
        try:
            product = json.loads(line)
        except:
            continue

        text = product.get("nutrition", "")
        existing = product.get("parsed_nutrition", {})

        parsed = parse_incremental(text, existing)
        product["parsed_nutrition"] = parsed

        # only count valid nutrition
        if text.strip():
            valid_nutrition += 1
            if parsed.get("confidence", 0) < 0.5:
                low_conf += 1

        outfile.write(json.dumps(product, ensure_ascii=False) + "\n")
        count += 1


print("\n✅ FINAL Processing Complete")
print("Total Products:", count)
print("Products with Nutrition:", valid_nutrition)
print("Low Confidence (valid only):", low_conf)
print("Output:", OUTPUT)