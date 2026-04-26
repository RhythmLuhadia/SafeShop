import json
from collections import defaultdict

INPUT = "scored_dataset.jsonl"
OUTPUT = "final_dataset.jsonl"

categories = defaultdict(list)
products = []


with open(INPUT) as f:
    for line in f:

        p = json.loads(line)

        products.append(p)

        cat = p["category"]
        score = p["health_score"]

        categories[cat].append(score)


def percentile(score, scores):

    scores_sorted = sorted(scores)

    rank = scores_sorted.index(score)

    return round((rank / len(scores_sorted)) * 100, 2)


with open(OUTPUT,"w") as out:

    for p in products:

        cat = p["category"]
        score = p["health_score"]

        p["category_percentile"] = percentile(score, categories[cat])

        out.write(json.dumps(p) + "\n")