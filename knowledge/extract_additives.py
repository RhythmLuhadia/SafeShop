import re

INPUT = "clean_ingredients.txt"  # change if needed

# patterns
INS_PATTERN = re.compile(r'\bins\s*\d+\b', re.IGNORECASE)
E_PATTERN = re.compile(r'\be\s*\d{3,4}\b', re.IGNORECASE)

KEYWORDS = [
    "benzoate", "sorbate", "nitrite", "nitrate",
    "colour", "color", "flavour", "flavor",
    "emulsifier", "stabilizer", "stabiliser",
    "preservative", "sweetener", "acid"
]

def extract_additives(line):
    additives = set()
    line_lower = line.lower()

    # INS codes
    for m in INS_PATTERN.findall(line_lower):
        additives.add(m.replace(" ", ""))

    # E codes
    for m in E_PATTERN.findall(line_lower):
        additives.add(m.replace(" ", ""))

    # keywords
    for word in KEYWORDS:
        if word in line_lower:
            additives.add(word)

    return additives


with open(INPUT, encoding="utf-8") as f:
    for line in f:
        line = line.strip()

        if not line:
            continue

        additives = extract_additives(line)

        if additives:
            print(f"{line}  →  {list(additives)}")