import json
from final_scoring_engine import final_score

INPUT = "parsed_dataset_v8_2.jsonl"

count = 0

with open(INPUT, "r", encoding="utf-8") as f:
    for line in f:
        try:
            product = json.loads(line)
        except:
            continue

        n = product.get("parsed_nutrition", {})
        a = product.get("ingredient_analysis", {})

        # ❗ skip if no nutrition
        if not n:
            continue

        # compute score
        score = final_score(n, a)

        print("\n" + "="*60)
        print("Product:", product.get("name"))
        print("Brand:", product.get("brand"))
        print("Category:", product.get("category"))

        print("\nScore:", score)

        # optional debug (VERY useful)
        print("\nParsed Nutrition:")
        print(n)

        count += 1

        if count >= 20:   # test first 20 products
            break


print(f"\n✅ Tested {count} products")

from final_scoring_engine import final_score, rule_score, ml_score

score = final_score(n, a)
r = rule_score(n, a)
m = ml_score(n, a)

print(f"Rule: {r} | ML: {m} | Final: {score}")