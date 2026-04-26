import json
import re

# ===== FILES =====
INPUT = "normalized_dataset.jsonl"
OUTPUT = "parsed_dataset_v3.jsonl"


# ===== NORMALIZATION =====
def normalize(text):
    text = text.lower()

    text = text.replace("\n", " ")
    text = text.replace(":", " ")
    text = text.replace("-", " ")
    text = text.replace(",", " ")

    # remove brackets
    text = re.sub(r"\(.*?\)", " ", text)

    # remove noisy phrases
    text = text.replace("of which", "")
    text = text.replace("per 100 g", "")
    text = text.replace("per 100g", "")
    text = text.replace("per serve", "")
    text = text.replace("nutrition_per", "")
    text = text.replace("serving_size", "")

    return text


# ===== SAFE EXTRACTION =====
def extract_value(keyword, text, unit):
    pattern = rf"{keyword}[^0-9]*([0-9]+\.?[0-9]*)\s*{unit}"
    match = re.search(pattern, text)

    if match and match.group(1):
        try:
            return float(match.group(1))
        except:
            return None

    return None


# ===== MAIN PARSER =====
def parse_nutrition(text):

    if not text:
        return {}

    raw_text = text
    text = normalize(text)

    data = {}

    data["energy_kcal"] = extract_value("energy", text, "kcal")
    data["protein_g"] = extract_value("protein", text, "g")
    data["carbohydrate_g"] = extract_value("carbohydrate", text, "g")
    data["sugar_g"] = extract_value("sugars?", text, "g")
    data["added_sugar_g"] = extract_value("added sugars?", text, "g")
    data["fat_g"] = extract_value("fat", text, "g")
    data["saturated_fat_g"] = extract_value("saturated", text, "g")
    data["trans_fat_g"] = extract_value("trans", text, "g")

    # ✅ FIXED HERE
    data["fiber_g"] = extract_value("(?:fibre|fiber)", text, "g")

    data["sodium_mg"] = extract_value("sodium", text, "mg")

    # ===== CONFIDENCE =====
    total = len(data)
    found = sum(1 for v in data.values() if v is not None)
    confidence = found / total

    data["confidence"] = round(confidence, 2)

    # ===== FALLBACK =====
    if confidence < 0.3:
        data["raw_text"] = raw_text

    return data


# ===== MAIN LOOP =====
count = 0
low_conf_count = 0

with open(INPUT, "r", encoding="utf-8") as infile, \
     open(OUTPUT, "w", encoding="utf-8") as outfile:

    for line in infile:

        try:
            product = json.loads(line)
        except:
            continue

        nutrition_text = product.get("nutrition", "")

        parsed = parse_nutrition(nutrition_text)

        product["parsed_nutrition"] = parsed

        # DEBUG LOW CONFIDENCE
        if parsed.get("confidence", 0) < 0.5:
            low_conf_count += 1
            print("\n⚠️ LOW CONF SAMPLE:")
            print(nutrition_text[:120])

        outfile.write(json.dumps(product, ensure_ascii=False) + "\n")

        count += 1


# ===== FINAL OUTPUT =====
print("\n✅ Processing Complete")
print("Total Products:", count)
print("Low Confidence Cases:", low_conf_count)
print("Output File:", OUTPUT)