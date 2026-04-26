import joblib
import pandas as pd

# ===== LAZY MODEL LOADING =====
model = None

def get_model():
    global model
    if model is None:
        print("⚡ Loading ML model...")
        model = joblib.load("health_model_v2.pkl")
        print("✅ Model loaded")
    return model


# ===== RULE SCORE =====
def rule_score(n, a):
    score = 100

    sodium = n.get("sodium_mg") or 0
    added_sugar = n.get("added_sugar_g") or 0
    total_sugar = n.get("sugar_g") or 0
    sat_fat = n.get("saturated_fat_g") or 0
    trans_fat = n.get("trans_fat_g") or 0
    fiber = n.get("fiber_g") or 0
    protein = n.get("protein_g") or 0
    energy = n.get("energy_kcal") or 0
    carbs = n.get("carbohydrate_g") or 0

    raw_text = str(n.get("raw_text", "")).lower()

    # ===== CORE PENALTIES =====

    if energy > 0:
        sugar_ratio = (total_sugar * 4) / energy
        if sugar_ratio > 0.6:
            score -= 40
        elif sugar_ratio > 0.4:
            score -= 25

    if sodium > 1000:
        score -= 40
    elif sodium > 500:
        score -= 20

    if added_sugar > 20:
        score -= 40
    elif added_sugar > 10:
        score -= 20

    if total_sugar > 40:
        score -= 30
    elif total_sugar > 20:
        score -= 15

    if carbs > 60:
        score -= 15

    if sat_fat > 10:
        score -= 25

    if trans_fat > 0:
        score -= 20

    if a.get("msg"):
        score -= 15

    if a.get("ultra_processed"):
        score -= 40

    score -= len(a.get("artificial_colors", [])) * 5
    score -= len(a.get("sweeteners", [])) * 5

    # ===== SPECIAL FIXES =====

    if energy < 100 and total_sugar >= 10:
        score -= 30

    if "caffeine" in raw_text:
        score -= 25

    if energy < 20 and a.get("ultra_processed"):
        score -= 25

    if energy < 100 and total_sugar > 5:
        score -= 20

    missing_count = sum([
        n.get("fat_g") is None,
        n.get("saturated_fat_g") is None,
        n.get("fiber_g") is None
    ])

    if missing_count >= 2:
        score -= 10

    # ===== BONUSES =====

    if fiber > 5:
        score += 5

    if protein > 10:
        score += 3

    return max(0, min(100, score))


# ===== ML SCORE =====
def ml_score(n, a):

    model = get_model()  # 🔥 LOAD ONLY WHEN NEEDED

    features = [[
        n.get("energy_kcal") or 0,
        n.get("protein_g") or 0,
        n.get("carbohydrate_g") or 0,
        n.get("sugar_g") or 0,
        n.get("added_sugar_g") or 0,
        n.get("fat_g") or 0,
        n.get("saturated_fat_g") or 0,
        n.get("trans_fat_g") or 0,
        n.get("fiber_g") or 0,
        n.get("sodium_mg") or 0,

        int(a.get("msg", False)),
        len(a.get("sweeteners", [])),
        len(a.get("artificial_colors", [])),
        len(a.get("processed_oils", [])),
        int(a.get("ultra_processed", False))
    ]]

    df = pd.DataFrame(features, columns=[
        "energy","protein","carbs","sugar","added_sugar",
        "fat","sat_fat","trans_fat","fiber","sodium",
        "msg","sweeteners","colors","processed_oils","ultra_processed"
    ])

    return model.predict(df)[0]


# ===== FINAL SCORE =====
def final_score(n, a):
    r = rule_score(n, a)
    m = ml_score(n, a)

    final = 0.8 * r + 0.2 * m
    return round(final, 2)