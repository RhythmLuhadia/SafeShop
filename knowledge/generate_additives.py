import json

INPUT = "raw_additives.json"   # your current file
OUTPUT = "additives.json"      # final usable DB


def normalize_key(k):
    return k.lower().replace(" ", "")


def generate_db(data):

    final_db = {}

    additives = data.get("additives", {})

    for ins_code, info in additives.items():

        ins_key = normalize_key(ins_code)

        # normalize e-number
        e_number = info.get("e_number")
        e_key = normalize_key(e_number) if e_number else None

        # ===== CREATE MAIN ENTRY =====
        final_db[ins_key] = {
            "name": info.get("name"),
            "category": info.get("category"),
            "risk": info.get("risk"),
            "e_number": e_key
        }

        # ===== CREATE E-MAPPING =====
        if e_key:
            final_db[e_key] = {
                "ref": ins_key
            }

    return final_db


# ===== LOAD =====
with open(INPUT, encoding="utf-8") as f:
    data = json.load(f)

# ===== GENERATE =====
final_db = generate_db(data)

# ===== SAVE =====
with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(final_db, f, indent=2, ensure_ascii=False)

print(f"✅ Generated DB with {len(final_db)} entries → {OUTPUT}")