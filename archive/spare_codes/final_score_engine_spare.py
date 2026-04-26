import joblib
import pandas as pd

# load trained ML model
model = joblib.load("health_model_v2.pkl")


# ===== RULE SCORE =====
def rule_score(n, a):
    score = 100

    # safe extraction
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

    # =========================
    # 🔴 CORE PENALTIES
    # =========================

    

    # 🚨 sugar dominance (core fix)
    if energy > 0:
        sugar_ratio = (total_sugar * 4) / energy

        if sugar_ratio > 0.6:
            score -= 40
        elif sugar_ratio > 0.4:
            score -= 25

    # sodium
    
    if sodium > 1000:
        score -= 40
    elif sodium > 500:
            score -= 20

    # added sugar
    if added_sugar > 20:
        score -= 40
    elif added_sugar > 10:
        score -= 20

    # total sugar (natural included)
    if total_sugar > 40:
        score -= 30
    elif total_sugar > 20:
        score -= 15

    # refined carbs (fix noodles)
    if carbs > 60:
        score -= 15

    # saturated fat
    if sat_fat > 10:
        score -= 25

    # trans fat
    if trans_fat > 0:
        score -= 20

    # additives
    if a.get("msg"):
        score -= 15

    if a.get("ultra_processed"):
        score -= 40

    score -= len(a.get("artificial_colors", [])) * 5
    score -= len(a.get("sweeteners", [])) * 5

    # =========================
    # 🚨 SPECIAL CASE FIXES
    # =========================

    # liquid sugar drinks (Red Bull fix)
    if energy < 100 and total_sugar >= 10:
        score -= 30

    # caffeine / stimulant drinks
    if "caffeine" in raw_text:
        score -= 25

    # fake healthy low-cal processed drinks
    if energy < 20 and a.get("ultra_processed"):
        score -= 25

    # per-serving trick (jaggery fix)
    if energy < 100 and total_sugar > 5:
        score -= 20

    # missing nutrition penalty
    missing_count = sum([
        n.get("fat_g") is None,
        n.get("saturated_fat_g") is None,
        n.get("fiber_g") is None
    ])

    if missing_count >= 2:
        score -= 10

    # =========================
    # 🟢 BONUSES
    # =========================

    if fiber > 5:
        score += 5

    if protein > 10:
        score += 3

    return max(0, min(100, score))


# ===== ML SCORE =====
def ml_score(n, a):

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

    # rule dominates ML
    final = 0.8 * r + 0.2 * m

    return round(final, 2)