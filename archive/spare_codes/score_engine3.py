import json

# ===== LOAD KNOWLEDGE =====
ADDITIVES_DB = json.load(open("knowledge/additives.json"))
META = json.load(open("knowledge/meta_data.json"))

ADDITIVES_DB = {k.lower(): v for k, v in ADDITIVES_DB.items()}


# ===== SAFE =====
def safe(v):
    return v if v is not None else 0


# ===== ADDITIVE SEVERITY =====
def additive_score(additives):

    score = 0

    for add in additives:
        code = add.get("code", "").lower()

        if code in ADDITIVES_DB:
            risk = ADDITIVES_DB[code]["risk"]

            if risk == "high":
                score -= 8
            elif risk == "medium":
                score -= 4
            elif risk == "low":
                score -= 1
        else:
            score -= 2  # unknown

    return score


# ===== NUTRITION =====
def nutrient_score(n):

    score = 0

    sugar = safe(n.get("sugar_g"))
    added_sugar = safe(n.get("added_sugar_g"))
    sodium = safe(n.get("sodium_mg"))
    sat_fat = safe(n.get("saturated_fat_g"))
    trans_fat = safe(n.get("trans_fat_g"))
    fiber = safe(n.get("fiber_g"))
    protein = safe(n.get("protein_g"))
    energy = safe(n.get("energy_kcal"))
    carbs = safe(n.get("carbohydrate_g"))

    if energy > 0:
        ratio = (sugar * 4) / energy
        if ratio > 0.6:
            score -= 40
        elif ratio > 0.4:
            score -= 25

    if sodium > 1000:
        score -= 40
    elif sodium > 500:
        score -= 20

    if added_sugar > 20:
        score -= 40
    elif added_sugar > 10:
        score -= 20

    if sugar > 40:
        score -= 30
    elif sugar > 20:
        score -= 15

    if carbs > 60:
        score -= 15

    if sat_fat > 10:
        score -= 25

    if trans_fat > 0:
        score -= 20

    if fiber > 5:
        score += 5

    if protein > 10:
        score += 3

    return score


# ===== SIGNALS =====
def signal_score(a, n):

    score = 0

    raw = str(n.get("raw_text", "")).lower()
    sugar = safe(n.get("sugar_g"))
    energy = safe(n.get("energy_kcal"))

    if a.get("msg"):
        score -= 15

    if a.get("ultra_processed"):
        score -= 40

    score -= len(a.get("processed_oils", [])) * 5
    score -= len(a.get("sweeteners", [])) * 5
    score -= len(a.get("artificial_colors", [])) * 5

    # edge fixes
    if energy < 100 and sugar >= 10:
        score -= 30

    if "caffeine" in raw:
        score -= 25

    if energy < 20 and a.get("ultra_processed"):
        score -= 25

    if energy < 100 and sugar > 5:
        score -= 20

    missing = sum([
        n.get("fat_g") is None,
        n.get("saturated_fat_g") is None,
        n.get("fiber_g") is None
    ])

    if missing >= 2:
        score -= 10

    return score


# ===== FINAL SCORE =====
def final_score(product):

    n = product.get("parsed_nutrition", {})
    a = product.get("ingredient_analysis", {})

    score = 100

    score += nutrient_score(n)
    score += additive_score(a.get("additives", []))
    score += signal_score(a, n)

    return max(0, min(100, round(score, 2)))


# ===== BATCH MODE =====
def process_dataset(input_file, output_file):

    processed = 0

    with open(input_file) as infile, open(output_file, "w") as outfile:

        for line in infile:
            product = json.loads(line)

            product["health_score"] = final_score(product)

            outfile.write(json.dumps(product) + "\n")
            processed += 1

    print(f"Processed: {processed}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python scoring_engine.py input.jsonl output.jsonl")
    else:
        process_dataset(sys.argv[1], sys.argv[2])