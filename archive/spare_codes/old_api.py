from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# your functions
from nutrition_parser4 import parse_incremental
from final_scoring_engine import final_score

app = FastAPI()

# =========================
# ✅ CORS FIX (VERY IMPORTANT)
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all (dev mode)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# Request schema
# =========================
class ProductInput(BaseModel):
    name: str
    brand: Optional[str] = None
    category: Optional[str] = None
    nutrition_text: Optional[str] = ""


# =========================
# Verdict
# =========================
def get_verdict(score):
    if score >= 70:
        return "Healthy"
    elif score >= 40:
        return "Moderate"
    else:
        return "Unhealthy"


# =========================
# Reasons
# =========================
def get_reasons(parsed):
    reasons = []

    if (parsed.get("added_sugar_g") or 0) > 15:
        reasons.append("High added sugar")

    if (parsed.get("sodium_mg") or 0) > 500:
        reasons.append("High sodium")

    if (parsed.get("protein_g") or 0) > 8:
        reasons.append("Good protein")

    if not reasons:
        reasons.append("Balanced nutrition")

    return reasons


# =========================
# MAIN API
# =========================
@app.post("/analyze")
def analyze_product(product: ProductInput):

    # STEP 1: parse nutrition (IMPORTANT FIX: pass existing = {})
    parsed = parse_incremental(product.nutrition_text, {})

    # STEP 2: FIX additives input (your model expects dict, not category)
    additives = {
        "msg": False,
        "ultra_processed": False,
        "artificial_colors": [],
        "sweeteners": [],
        "processed_oils": []
    }

    # STEP 3: score
    score = final_score(parsed, additives)

    # STEP 4: verdict
    verdict = get_verdict(score)

    # STEP 5: reasons
    reasons = get_reasons(parsed)

    return {
        "score": round(score, 2),
        "verdict": verdict,
        "reasons": reasons,
        "confidence": parsed.get("confidence", 0)
    }


# =========================
# ROOT (TEST)
# =========================
@app.get("/")
def root():
    return {"message": "SafeShop API running 🚀"}