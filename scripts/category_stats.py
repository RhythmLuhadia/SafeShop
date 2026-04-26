import json
from collections import defaultdict
import numpy as np

INPUT = "scored_dataset.jsonl"

categories = defaultdict(list)

with open(INPUT) as f:
    for line in f:
        product = json.loads(line)

        score = product.get("health_score")
        cat = product.get("category")

        if score is not None:
            categories[cat].append(score)


stats = {}

for cat, scores in categories.items():

    scores = np.array(scores)

    stats[cat] = {
        "count": len(scores),
        "mean": float(np.mean(scores)),
        "median": float(np.median(scores)),
        "std": float(np.std(scores)),
        "min": float(np.min(scores)),
        "max": float(np.max(scores))
    }

print(json.dumps(stats, indent=2))