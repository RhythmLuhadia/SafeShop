import urllib.request
import re
try:
    req = urllib.request.Request(
        "https://www.bigbasket.com/pd/266109/maggi-2-minute-instant-noodles-masala-70-g/",
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    html = urllib.request.urlopen(req).read().decode('utf-8')
    # Try to find exactly what our Javascript querySelector is finding for h1
    h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.IGNORECASE)
    print("H1 Match:", h1_match.group(1) if h1_match else "None")
    
    # Let's extract any element that would match [class*="Title"]
    title_classes = re.findall(r'class="[^"]*Title[^"]*"(.*?)>', html, re.IGNORECASE)
    print("Title Classes Found:", len(title_classes))

    # Let's find spans with Ingredients
    ing_spans = re.findall(r'<span[^>]*>\s*ingredients\s*</span>', html, re.IGNORECASE)
    print("Ingredient Spans Found:", len(ing_spans))
except Exception as e:
    print("Error:", e)
