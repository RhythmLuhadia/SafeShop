import re
try:
    from PIL import Image
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False

def extract_product_data_from_image(image_path: str):
    if not HAS_TESSERACT:
        return {"error": "Tesseract or Pillow is not installed on this system."}
    
    try:
        # We process the image with Tesseract
        # If tesseract-ocr executable is not in PATH, this will throw an exception
        # Windows typically: pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        text = pytesseract.image_to_string(Image.open(image_path))
        
        # Simple extraction heuristics -> looking for blocks starting with "Ingredients" and "Nutrition"
        ingredients_match = re.search(r"ingredients[\s:;]+(.*?)(nutrition|energy|manufactured|weight|\n\n|$)", text, re.IGNORECASE | re.DOTALL)
        ingredients = ingredients_match.group(1).strip() if ingredients_match else ""
        
        nutrition_match = re.search(r"(nutrition.*?)(ingredients|manufactured|weight|$)", text, re.IGNORECASE | re.DOTALL)
        nutrition_text = nutrition_match.group(1).strip() if nutrition_match else text # fallback to parsed string
        
        return {
            "success": True,
            "raw_text": text.strip(),
            "ingredients": ingredients,
            "nutrition_text": nutrition_text
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to OCR image. Please ensure Tesseract is installed. Details: {str(e)}"
        }
