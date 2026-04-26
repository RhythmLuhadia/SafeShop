import json

# ===== IMPORTS =====
from app.ingredient_analyzer import analyze_ingredients
from app.final_scoring_engine import final_score, get_verdict
from app.ingredient_cleaner import clean_ingredients
from app.nutrition_parser import parse_nutrition as parse_fn


INPUT = "data/normalized_dataset.jsonl"
OUTPUT = "data/scored_dataset.jsonl"


def process_product(product):

    # ===== 1. INGREDIENT CLEANING =====
    raw_ingredients = product.get("ingredients", [])
    cleaned_ingredients = clean_ingredients(raw_ingredients)

    # convert list → string for analyzer
    ingredient_text = " ".join(cleaned_ingredients)

    # ===== 2. INGREDIENT ANALYSIS =====
    ingredient_analysis = analyze_ingredients(ingredient_text)

    # ===== 3. NUTRITION PARSING =====
    nutrition_text = product.get("nutrition", "")

    try:
        parsed_nutrition = parse_fn(nutrition_text)
    except TypeError:
        # fallback if parser expects (text, existing)
        parsed_nutrition = parse_fn(nutrition_text, {})

    # ===== 4. SCORING =====
    product["ingredients"] = cleaned_ingredients
    product["ingredient_analysis"] = ingredient_analysis
    product["parsed_nutrition"] = parsed_nutrition

    score, reasons = final_score(product)

    product["health_score"] = score
    product["verdict"] = get_verdict(score)
    product["reasons"] = list(set(reasons))

    return product


def run_pipeline():

    count = 0
    errors = 0

    with open(INPUT, "r", encoding="utf-8") as infile, \
         open(OUTPUT, "w", encoding="utf-8") as outfile:

        for line in infile:

            try:
                product = json.loads(line)
            except:
                continue

            try:
                processed = process_product(product)
                outfile.write(json.dumps(processed, ensure_ascii=False) + "\n")
                count += 1

            except Exception as e:
                errors += 1
                print("Error:", e)

    print(f"\n✅ Pipeline complete: {count} products processed")
    print(f"⚠️ Errors: {errors}")
    print(f"📦 Output saved to: {OUTPUT}")


if __name__ == "__main__":
    run_pipeline()