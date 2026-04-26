from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
import re
import json
import os
import tempfile
import random
import difflib

# your modules
from app.nutrition_parser import parse_nutrition
from app.ingredient_analyzer import analyze_ingredients
from app.final_scoring_engine import final_score, get_verdict
from app.normalize_dataset import normalize_ingredients
from app.ocr_service import extract_product_data_from_image

app = FastAPI()

CATEGORY_DB = {}

@app.on_event("startup")
def load_dataset():
    dataset_path = "data/scored_dataset.jsonl"
    if not os.path.exists(dataset_path):
        print(f"Warning: Dataset not found at {dataset_path}. Alternatives will not work.")
        return
    
    with open(dataset_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                prod = json.loads(line)
                cat = prod.get("category")
                if cat:
                    if cat not in CATEGORY_DB:
                        CATEGORY_DB[cat] = []
                    CATEGORY_DB[cat].append(prod)
            except:
                continue

# =========================
# CORS
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    ingredients: Optional[str] = ""
    allergies: Optional[List[str]] = []
    region: Optional[str] = "global"


# =========================
# HEALTH FLAGS
# =========================
def get_health_flags(n):
    flags = []

    sugar = n.get("sugar_g", 0) or 0
    carbs = n.get("carbohydrate_g", 0) or 0
    sodium = n.get("sodium_mg", 0) or 0
    sat_fat = n.get("saturated_fat_g", 0) or 0
    trans_fat = n.get("trans_fat_g", 0) or 0
    energy = n.get("energy_kcal", 0) or 0

    if sugar > 10 or carbs > 60:
        flags.append({
            "type": "diabetes",
            "message": f"High sugar/carbs ({sugar}g sugar, {carbs}g carbs)"
        })

    if sodium > 500:
        flags.append({
            "type": "bp",
            "message": f"High sodium ({sodium}mg)"
        })

    if trans_fat > 0:
        flags.append({
            "type": "heart",
            "message": "Contains trans fat"
        })
    elif sat_fat > 10:
        flags.append({
            "type": "heart",
            "message": f"High saturated fat ({sat_fat}g)"
        })

    if energy > 400 or sugar > 20:
        flags.append({
            "type": "weight",
            "message": "High calorie/sugar"
        })

    return flags


# =========================
# MAIN API
# =========================
@app.post("/analyze")
def analyze_product(product: ProductInput):

    raw_text = (product.ingredients or "").lower().strip()
    has_ingredients = bool(raw_text)

    if has_ingredients:
        ins_codes = re.findall(r"\b\d{3,4}\b", raw_text)
        ins_codes = [f"ins{code}" for code in ins_codes]

        raw_text = re.sub(r"\(.*?\)", "", raw_text)

        normalized_ingredients = normalize_ingredients(raw_text)
        normalized_ingredients.extend(ins_codes)
        normalized_ingredients = list(dict.fromkeys(normalized_ingredients))

        ingredient_analysis = analyze_ingredients(normalized_ingredients)

    else:
        normalized_ingredients = []
        ingredient_analysis = {
            "additives": {
                "primary": [],
                "secondary": [],
                "generic": []
            },
            "msg": False,
            "ultra_processed": False,
            "sweeteners": []
        }

    # ===== NUTRITION =====
    parsed_nutrition = parse_nutrition(product.nutrition_text)
    has_nutrition = parsed_nutrition.get("confidence", 0) > 0

    # ===== SCORING =====
    product_data = {
        "parsed_nutrition": parsed_nutrition,
        "ingredient_analysis": ingredient_analysis,
        "tokens": normalized_ingredients
    }

    score, reasons = final_score(product_data, allergies=product.allergies, region=product.region)

    # ===== HEALTH FLAGS =====
    health_flags = get_health_flags(parsed_nutrition)

    # ===== BETTER ALTERNATIVES =====
    better_alternatives = []
    if product.category and product.category in CATEGORY_DB:
        cat_products = sorted(CATEGORY_DB[product.category], key=lambda x: x.get("health_score", 0), reverse=True)
        for p in cat_products:
            pscore = p.get("health_score", 0)
            if pscore > score and p.get("name") != product.name:
                better_alternatives.append({
                    "name": p.get("name"),
                    "brand": p.get("brand"),
                    "health_score": round(pscore, 2),
                    "image": p.get("image", "")
                })
            if len(better_alternatives) >= 3:
                break

    # ===== RESPONSE =====
    return {
        "score": round(score, 2),
        "verdict": get_verdict(score),
        "reasons": list(set(reasons)),
        "better_alternatives": better_alternatives,

        # 🔥 FIX: needed for frontend graphs
        "parsed_nutrition": parsed_nutrition,

        "health_flags": health_flags,

        "confidence": (
            parsed_nutrition.get("confidence", 0) * 0.6 +
            (1 if has_ingredients else 0) * 0.4
        ),

        "tokens": normalized_ingredients,

        "additives": ingredient_analysis.get("additives", {}),
        "flags": {
            "msg": ingredient_analysis.get("msg", False),
            "ultra_processed": ingredient_analysis.get("ultra_processed", False),
            "sweeteners": ingredient_analysis.get("sweeteners", [])
        },

        "data_quality": {
            "has_ingredients": has_ingredients,
            "has_nutrition": has_nutrition
        }
    }


# =========================
# GET SEARCH
# =========================
@app.get("/search")
def search_products(q: str):
    query = q.lower().strip()
    if not query:
        return {"results": []}

    results = []
    all_products = []
    for cat_items in CATEGORY_DB.values():
        all_products.extend(cat_items)

    # 1. Exact Substring Match
    for p in all_products:
        name = p.get("name", "").lower()
        brand = p.get("brand", "").lower()
        if query in name or query in brand:
            if p not in results:
                results.append(p)
        if len(results) >= 10:
            break
            
    # 2. Fuzzy Matching Fallback (if few results)
    if len(results) < 10:
        product_names = [p.get("name", "").lower() for p in all_products]
        close_matches = difflib.get_close_matches(query, product_names, n=10-len(results), cutoff=0.45)
        
        for p in all_products:
            if p.get("name", "").lower() in close_matches:
                if p not in results:
                    results.append(p)

    return {"results": results[:10]}

# =========================
# GET BROWSE / CATEGORIES
# =========================
@app.get("/categories")
def get_categories():
    return {"categories": list(CATEGORY_DB.keys())}

@app.get("/browse")
def browse_products(category: Optional[str] = None):
    all_products = []
    if category and category in CATEGORY_DB:
        all_products = CATEGORY_DB[category]
    else:
        for prods in CATEGORY_DB.values():
            all_products.extend(prods)
    
    if not all_products:
        return {"results": []}
        
    sample_size = min(30, len(all_products))
    results = random.sample(all_products, sample_size)
    return {"results": results}

# =========================
# OCR UPLOAD & URL
# =========================
@app.post("/upload-image")
async def analyze_image(file: UploadFile = File(...)):
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, file.filename)
    with open(temp_path, "wb") as buffer:
        buffer.write(await file.read())

    result = extract_product_data_from_image(temp_path)
    os.remove(temp_path)
    if not result.get("success"):
        return {"error": result.get("error")}
    return result

class ImageUrlInput(BaseModel):
    url: str

@app.post("/analyze-image-url")
async def analyze_image_url(data: ImageUrlInput):
    import urllib.request
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, "temp_ocr.jpg")
    try:
        req = urllib.request.Request(data.url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(temp_path, 'wb') as out_file:
            out_file.write(response.read())
        result = extract_product_data_from_image(temp_path)
        os.remove(temp_path)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

# =========================
# MOUNT FRONTEND
# =========================
if os.path.exists("frontend"):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")