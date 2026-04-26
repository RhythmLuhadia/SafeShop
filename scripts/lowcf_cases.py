import json

INPUT = "parsed_dataset_final.jsonl"
OUTPUT = "low_confidence_cases.jsonl"

LOW_CONF_THRESHOLD = 0.5

low_conf_count = 0
valid_products = 0

with open(INPUT, "r", encoding="utf-8") as infile, \
     open(OUTPUT, "w", encoding="utf-8") as outfile:

    for line in infile:
        try:
            product = json.loads(line)
        except:
            continue

        nutrition_text = str(product.get("nutrition", "")).strip()

        # 🚫 SKIP EMPTY NUTRITION
        if not nutrition_text or nutrition_text == "0":
            continue

        valid_products += 1

        parsed = product.get("parsed_nutrition", {})
        confidence = parsed.get("confidence", 0)

        # ⚠️ LOW CONF CASE
        if confidence < LOW_CONF_THRESHOLD:
            low_conf_count += 1

            # save full product for debugging
            outfile.write(json.dumps(product, ensure_ascii=False) + "\n")

# ===== FINAL STATS =====
print("\n📊 ANALYSIS COMPLETE")
print("Valid Nutrition Products:", valid_products)
print("Low Confidence Cases:", low_conf_count)
print("Output File:", OUTPUT)