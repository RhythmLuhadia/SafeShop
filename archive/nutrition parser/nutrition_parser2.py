import json
import re

# ===== FILES =====
INPUT = "normalized_dataset.jsonl"
OUTPUT = "parsed_dataset_v2.jsonl"


# ===== HELPER FUNCTIONS =====
def extract_multi(patterns, text):
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except:
                continue
    return None


def normalize(text):
    text = text.lower()
    text = text.replace("\n", " ")
    text = text.replace(":", " ")
    text = text.replace("-", " ")
    return text


# ===== MAIN PARSER =====
def parse_nutrition(text):

    if not text:
        return {}

    raw_text = text
    text = normalize(text)

    data = {}

    data["energy_kcal"] = extract_multi([
        r"energy\s*\(?kcal\)?\s*([0-9]+\.?[0-9]*)",
        r"([0-9]+\.?[0-9]*)\s*kcal",
    ], text)

    data["protein_g"] = extract_multi([
        r"protein\s*\(?g\)?\s*([0-9]+\.?[0-9]*)",
        r"([0-9]+\.?[0-9]*)\s*g\s*protein",
    ], text)

    data["carbohydrate_g"] = extract_multi([
        r"carbohydrate[s]?\s*\(?g\)?\s*([0-9]+\.?[0-9]*)",
        r"carbs?\s*([0-9]+\.?[0-9]*)",
    ], text)

    data["sugar_g"] = extract_multi([
        r"sugars?\s*\(?g\)?\s*([0-9]+\.?[0-9]*)",
    ], text)

    data["added_sugar_g"] = extract_multi([
        r"added sugars?\s*\(?g\)?\s*([0-9]+\.?[0-9]*)",
    ], text)

    data["fat_g"] = extract_multi([
        r"(?:total fat|fat)\s*\(?g\)?\s*([0-9]+\.?[0-9]*)",
    ], text)

    data["saturated_fat_g"] = extract_multi([
        r"saturated\s*\(?g\)?\s*([0-9]+\.?[0-9]*)",
    ], text)

    data["trans_fat_g"] = extract_multi([
        r"trans\s*\(?g\)?\s*([0-9]+\.?[0-9]*)",
    ], text)

    data["fiber_g"] = extract_multi([
        r"(?:fiber|fibre)\s*\(?g\)?\s*([0-9]+\.?[0-9]*)",
    ], text)

    data["sodium_mg"] = extract_multi([
        r"sodium\s*\(?mg\)?\s*([0-9]+\.?[0-9]*)",
    ], text)

    # ===== CONFIDENCE SCORE =====
    total_fields = len(data)
    extracted_fields = sum(1 for v in data.values() if v is not None)
    confidence = extracted_fields / total_fields

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

        # ===== DEBUG LOW CONFIDENCE =====
        if parsed.get("confidence", 0) < 0.5:
            low_conf_count += 1
            print("\n⚠️ LOW CONFIDENCE:")
            print(nutrition_text[:120])

        outfile.write(json.dumps(product, ensure_ascii=False) + "\n")

        count += 1


# ===== FINAL STATS =====
print("\n✅ Processing Complete")
print("Total Products:", count)
print("Low Confidence Cases:", low_conf_count)