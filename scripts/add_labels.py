import pandas as pd

INPUT = "ml_dataset_v2.csv"
OUTPUT = "ml_dataset_labeled.csv"

df = pd.read_csv(INPUT)


def rule_score(row):
    score = 100

    # ===== BAD STUFF (penalties) =====

    # sodium
    if row["sodium"] > 1000:
        score -= 25
    elif row["sodium"] > 500:
        score -= 10

    # added sugar
    if row["added_sugar"] > 20:
        score -= 25
    elif row["added_sugar"] > 10:
        score -= 10

    # saturated fat
    if row["sat_fat"] > 10:
        score -= 20

    # trans fat
    if row["trans_fat"] > 0:
        score -= 15

    # additives
    if row["msg"] == 1:
        score -= 10

    if row["ultra_processed"] == 1:
        score -= 20

    score -= row["colors"] * 5
    score -= row["sweeteners"] * 5

    # ===== GOOD STUFF (bonuses) =====

    if row["fiber"] > 5:
        score += 10

    if row["protein"] > 10:
        score += 5

    # clamp
    score = max(0, min(100, score))

    return score


# apply rule
df["label"] = df.apply(rule_score, axis=1)

# save
df.to_csv(OUTPUT, index=False)

print("✅ Labels added")
print("Sample:")
print(df[["sodium", "added_sugar", "label"]].head())