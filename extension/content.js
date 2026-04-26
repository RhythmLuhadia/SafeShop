// ============================
// INJECTION GUARD
// ============================
if (document.getElementById("safe-shop-injected-flag")) {
    console.log("SafeShop: Already injected.");
} else {
    let flag = document.createElement("div");
    flag.id = "safe-shop-injected-flag";
    flag.style.display = "none";
    document.body.appendChild(flag);

    console.log("%c[SafeShop v2.0] Loaded!", "color:#3b82f6;font-weight:bold;font-size:13px;");

    const style = document.createElement("style");
    style.innerHTML = `
    @keyframes ss-fadeIn { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes ss-spin    { to { transform: rotate(360deg); } }
    #safe-shop-box * { box-sizing: border-box; font-family: 'Inter', -apple-system, Arial, sans-serif; }
    #safe-shop-box ::-webkit-scrollbar { width: 4px; }
    #safe-shop-box ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 4px; }
    `;
    document.head.appendChild(style);

    // ============================
    // UTILITIES
    // ============================
    function getRiskColor(risk) {
        if (risk === "high") return "#ff4d4f";
        if (risk === "medium" || risk === "moderate") return "#ffb300";
        return "#52c41a";
    }
    function getScoreColor(score) {
        if (score >= 70) return "#22c55e";
        if (score >= 40) return "#f59e0b";
        return "#ef4444";
    }

    // Category detection matching exact dataset slugs
    function guessCategoryFromName(name) {
        if (!name) return null;
        const n = name.toLowerCase();
        const map = [
            { keys: ["chips", "crisps", "puffs", "popcorn", "nachos", "bhujia", "namkeen", "kurkure", "bingo", "lays", "doritos", "snack", "murukku", "munchies"], cat: "snacks-namkeen" },
            { keys: ["biscuit", "cookie", "cracker", "bourbon", "oreo", "marie", "digestive", "parle", "mcvities", "hide & seek"], cat: "biscuits-cookies" },
            { keys: ["noodles", "maggi", "ramen", "pasta", "vermicelli", "yippee", "top ramen"], cat: "instant-noodles" },
            { keys: ["energy drink", "red bull", "monster", "sting", "gatorade"], cat: "energy-drinks" },
            { keys: ["chocolate", "kitkat", "dairy milk", "5 star", "cadbury", "munch bar", "milkybar", "silk bar", "truffle"], cat: "chocolates" },
            { keys: ["candy", "toffee", "lollipop", "gummy", "chewing gum", "eclairs", "gems"], cat: "chocolates-candies" },
            { keys: ["cereal", "muesli", "cornflakes", "granola", "kellogg", "chocos", "corn flakes", "wheat flakes", "bagrry"], cat: "breakfast-cereals" },
            { keys: ["peanut butter", "almond butter", "nut butter", "choco spread", "hazelnut", "nutella", "jam", "jelly", "marmalade", "ketchup", "sauce", "mayo", "dressing"], cat: "spreads-sauces-ketchup" },
            { keys: ["pickle", "chutney", "achaar"], cat: "pickles-chutney" },
            { keys: ["ice cream", "gelato", "kulfi", "frozen dessert"], cat: "ice-creams" },
            { keys: ["ready to eat", "instant khichdi", "instant poha", "soup mix", "curry mix"], cat: "ready-to-cook-eat" },
        ];
        for (const { keys, cat } of map) {
            if (keys.some(k => n.includes(k))) return cat;
        }
        return null;
    }

    // ============================
    // PAGE DETECTION
    // ============================
    function isAmazon()     { return window.location.hostname.includes('amazon'); }
    function isBigBasket()  { return window.location.hostname.includes('bigbasket'); }
    function isZepto()      { return window.location.hostname.includes('zepto'); }
    function isBlinkit()    { return window.location.hostname.includes('blinkit'); }
    function isSwiggy()     { return window.location.hostname.includes('swiggy'); }

    function isProductPage() {
        const url = window.location.href;
        if (isAmazon())    return url.includes('/dp/') || url.includes('/gp/product/');
        if (isBigBasket()) return url.includes('/pd/') || url.includes('/product/');
        if (isZepto())     return url.includes('/pn/') || url.includes('/product/');
        if (isBlinkit())   return url.includes('/pr/') || url.includes('/prn/');
        if (isSwiggy())    return url.includes('/item/');
        return false;
    }

    function getProductName() {
        if (!isProductPage()) return null;

        // Amazon
        if (isAmazon()) {
            const candidates = [
                document.getElementById('productTitle'),
                document.querySelector('#titleSection .a-size-large'),
                document.querySelector('.product-title-word-break'),
                document.querySelector('h1.a-size-large'),
                document.querySelector('[data-feature-name="title"] span'),
                document.querySelector('h1'),
            ];
            for (const el of candidates) {
                if (el && el.innerText && el.innerText.trim().length > 3) {
                    return el.innerText.trim();
                }
            }
            return null;
        }

        // BigBasket / others
        const candidates = [
            document.querySelector('h1.page-title'),
            document.querySelector('h1'),
            document.querySelector('[class*="ProductTitle" i]'),
            document.querySelector('[class*="Title" i]'),
            document.querySelector('[class*="name" i]'),
        ];
        for (const el of candidates) {
            if (el && el.innerText && el.innerText.trim().length > 3) {
                return el.innerText.trim();
            }
        }
        
        // Final fallback: Title tag
        if (document.title && document.title.length > 5 && !document.title.toLowerCase().startsWith('home')) {
            let t = document.title;
            t = t.replace(/(buy|online\s+at).*?(blinkit|zepto|bigbasket|swiggy|amazon)/gi, '').trim();
            t = t.split('-')[0].split('|')[0].trim();
            if (t.length > 3) return t;
        }

        return null;
    }

    // FIXED: validateNutritionText — requires actual numbers+units to avoid false positives
    function hasRealNutritionData(text) {
        if (!text || text.length < 30) return false;
        // Must have numbers followed by nutritional units
        const hasNumbers = /\d+\.?\d*\s*(kcal|kj|g|mg)/i.test(text);
        // Must mention at least one macro
        const hasMacros  = /(energy|calorie|protein|fat|carbohydrate|sodium|sugar)/i.test(text);
        return hasNumbers && hasMacros;
    }

    function getNutritionText() {
        // First try DOM tables — most reliable (specific nutrition tables only)
        const tables = document.querySelectorAll('table');
        for (const t of tables) {
            const tc = t.textContent;
            if (hasRealNutritionData(tc)) return tc.substring(0, 3000);
        }

        // Amazon: try the product specs section
        if (isAmazon()) {
            const specRows = [...document.querySelectorAll('#productDetails_techSpec_section_1 tr, #productDetails_db_sections tr')];
            const specText = specRows.map(r => r.textContent).join(' ');
            if (hasRealNutritionData(specText)) return specText;

            // Amazon: A+ content sometimes has nutrition as text
            const aplus = document.querySelector('#aplus_feature_div, #aplus');
            if (aplus && hasRealNutritionData(aplus.textContent)) return aplus.textContent.substring(0, 3000);
        }

        // Full-page textContent scan with validation
        const fullText = document.documentElement.textContent || '';
        const patterns = [
            /Nutritional Information[\s\S]{0,3000}/i,
            /Nutrition Facts[\s\S]{0,3000}/i,
            /Nutritional Value[\s\S]{0,3000}/i,
            /Average Nutritional Value[\s\S]{0,2000}/i,
            /Energy.*?\d+.*?kcal[\s\S]{0,2000}/i,
            /Per 100\s*g[\s\S]{0,2000}/i,
        ];
        for (const pat of patterns) {
            const m = fullText.match(pat);
            // KEY: validate the match actually has numbers
            if (m && hasRealNutritionData(m[0])) {
                return m[0].substring(0, 3000);
            }
        }

        return '';
    }

    function getIngredientsText() {
        // Amazon: try every known container
        if (isAmazon()) {
            // 1. important-information section (most common for food)
            const infoDiv = document.getElementById('important-information');
            if (infoDiv) {
                const ingEl = [...infoDiv.querySelectorAll('h4, span, p, li, div')].find(e =>
                    e.children.length < 3 && e.textContent.toLowerCase().includes('ingredient'));
                if (ingEl && ingEl.nextElementSibling) {
                    const t = ingEl.nextElementSibling.innerText.trim();
                    if (t.length > 10) return t;
                }
                if (ingEl && ingEl.innerText.length > 30)
                    return ingEl.innerText.replace(/ingredients:?/i, '').trim();
                // Grab full section text as fallback
                const fullSec = infoDiv.innerText;
                const m = fullSec.match(/ingredients?[:\s]+([^\n]{10,500})/i);
                if (m) return m[1].trim();
            }
            // 2. Product detail table rows
            const rows = [...document.querySelectorAll('#productDetails_techSpec_section_1 tr, #productDetails_db_sections tr, .prodDetTable tr')];
            for (const row of rows) {
                if (row.textContent.toLowerCase().includes('ingredient')) {
                    const cells = row.querySelectorAll('td');
                    if (cells.length >= 1) return cells[cells.length - 1].innerText.trim();
                }
            }
            // 3. Feature bullet points (sometimes lists ingredients)
            const bullets = document.querySelector('#feature-bullets');
            if (bullets) {
                const bText = bullets.innerText;
                const bm = bText.match(/ingredients?[:\s]+([^\n]{10,500})/i);
                if (bm) return bm[1].trim();
            }
            // 4. Product description section
            const desc = document.querySelector('#productDescription, #dpx-product-description_feature_div');
            if (desc) {
                const dm = desc.innerText.match(/ingredients?[:\s]+([^\n]{10,500})/i);
                if (dm) return dm[1].trim();
            }
        }

        // KEY FIX: use textContent to find ingredients in hidden/collapsed sections
        const fullText = document.documentElement.textContent || '';
        const ingPatterns = [
            /Ingredients?[:\s]+([A-Za-z][\s\S]{10,1000}?)(?=\n\n|Allergen|Nutritional|Contains|Manufactured|Best Before|Storage|$)/i,
            /Made From[:\s]+([\s\S]{10,800}?)(?=\n\n|Nutritional|Contains|$)/i,
            /Composition[:\s]+([\s\S]{10,800}?)(?=\n\n|Nutritional|$)/i,
        ];
        for (const pat of ingPatterns) {
            const m = fullText.match(pat);
            if (m && m[1] && m[1].trim().length > 10) return m[1].trim().substring(0, 1000);
        }

        // DOM element fallback
        const searchTerms = ["ingredients", "ingredients:", "made from", "composition"];
        const elements = [...document.querySelectorAll("span, h2, h3, h4, div, td, th, p, strong, b")];
        const label = elements.find(el => {
            if (el.children.length > 2) return false;
            const t = el.innerText.trim().toLowerCase();
            return searchTerms.some(term => t === term || t.startsWith("ingredients:"));
        });
        if (!label) return '';
        if (label.innerText.length > 25) return label.innerText.replace(/ingredients:?/i, '').trim();
        const wrapper = label.closest("div") || label.parentElement;
        if (!wrapper) return label.nextElementSibling?.innerText?.trim() || '';
        const next = wrapper.nextElementSibling;
        const raw = next ? next.innerText.replace(/["']/g, '').trim() : label.nextSibling?.textContent?.trim() || '';
        if (raw && raw.length > 5 && raw.length < 1500) return raw;
        if (wrapper?.innerText?.length > 10 && wrapper.innerText.length < 1500) return wrapper.innerText;
        return '';
    }

    function getScoreFromAPI(productData) {
        return new Promise((resolve) => {
            chrome.runtime.sendMessage({ type: "GET_SCORE", data: productData }, (response) => {
                resolve(response || null);
            });
        });
    }

    function scoreImageForOCR(img) {
        let score = 0;
        const src = (img.src || '').toLowerCase();
        const alt = (img.alt || '').toLowerCase();
        ["ingredient", "nutrition", "back", "label", "info", "facts"].forEach(t => {
            if (src.includes(t) || alt.includes(t)) score += 30;
        });
        const area = (img.naturalWidth || img.width || 0) * (img.naturalHeight || img.height || 0);
        score += Math.min(area / 5000, 40);
        ["logo", "icon", "banner", "sprite", "badge"].forEach(t => {
            if (src.includes(t) || alt.includes(t)) score -= 40;
        });
        if ((img.width || img.naturalWidth || 0) < 100) score -= 20;
        return score;
    }

    function createTooltip() {
        let t = document.getElementById("safe-tooltip");
        if (!t) {
            t = document.createElement("div");
            t.id = "safe-tooltip";
            Object.assign(t.style, {
                position: "fixed", background: "rgba(10,10,10,0.97)", color: "white",
                padding: "10px 14px", borderRadius: "10px", fontSize: "12px",
                zIndex: "9999999", pointerEvents: "none", opacity: "0",
                transition: "opacity 0.2s ease", boxShadow: "0 4px 20px rgba(0,0,0,0.7)",
                border: "1px solid rgba(255,255,255,0.1)", backdropFilter: "blur(8px)", maxWidth: "220px"
            });
            document.body.appendChild(t);
        }
        return t;
    }

    function buildNutritionBar(label, value, maxVal, unit, dangerThreshold, warnThreshold) {
        if (value === null || value === undefined) return '';
        const pct   = Math.min(100, Math.round((value / maxVal) * 100));
        const color = value >= dangerThreshold ? '#ef4444' : value >= warnThreshold ? '#f59e0b' : '#22c55e';
        const level = value >= dangerThreshold ? 'High' : value >= warnThreshold ? 'Moderate' : 'Low';
        return `
        <div style="margin-bottom:10px;">
            <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:4px;">
                <span style="font-size:12px;color:rgba(255,255,255,0.75);font-weight:500;">${label}</span>
                <span style="font-size:11px;color:${color};font-weight:700;">${level} · ${value}${unit}</span>
            </div>
            <div style="height:5px;background:rgba(255,255,255,0.06);border-radius:3px;overflow:hidden;">
                <div style="height:100%;width:${pct}%;background:${color};border-radius:3px;"></div>
            </div>
        </div>`;
    }

    function renderErrorUI() {
        let ex = document.getElementById("safe-shop-box");
        if (ex) ex.remove();
        let box = document.createElement("div");
        box.id = "safe-shop-box";
        box.innerHTML = `
        <div style="position:fixed;top:90px;right:20px;width:300px;padding:18px 20px;border-radius:20px;background:rgba(14,14,20,0.93);backdrop-filter:blur(20px);border:1px solid rgba(239,68,68,0.4);box-shadow:0 0 30px rgba(239,68,68,0.2);color:white;z-index:999999;animation:ss-fadeIn 0.4s ease;">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:14px;">
                <div style="width:42px;height:42px;border-radius:50%;background:rgba(239,68,68,0.12);border:1px solid rgba(239,68,68,0.35);display:flex;align-items:center;justify-content:center;font-size:20px;">🔌</div>
                <div><div style="font-size:14px;font-weight:700;color:#ef4444;">SafeShop Offline</div><div style="font-size:11px;opacity:0.55;margin-top:2px;">Backend server unreachable</div></div>
            </div>
            <div style="background:rgba(255,255,255,0.04);border-radius:10px;padding:10px 12px;font-size:11px;color:rgba(255,255,255,0.55);line-height:1.7;">Start the server:<br><span style="color:#f59e0b;font-weight:600;font-family:monospace;">uvicorn app.api:app --reload</span></div>
            <div id="safe-retry-btn" style="margin-top:12px;background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.25);border-radius:8px;padding:9px;text-align:center;font-size:12px;font-weight:700;color:#ef4444;cursor:pointer;">↺ Retry</div>
        </div>`;
        document.body.appendChild(box);
        document.getElementById("safe-retry-btn").addEventListener("click", () => {
            memoryTarget = null;
            const eb = document.getElementById("safe-shop-box"); if (eb) eb.remove();
        });
    }

    // ============================
    // MAIN UI RENDERER
    // ============================
    function renderUI(result, reqData) {
        if (!result || result.error) { renderErrorUI(); return; }

        console.log("%c[SafeShop] API Result:", "color:#22c55e;font-weight:bold;", result);

        let ex = document.getElementById("safe-shop-box");
        if (ex) ex.remove();

        const score      = result.score || 0;
        const verdict    = result.verdict || "Evaluated";
        const reasons    = result.reasons || [];
        const nutrition  = result.parsed_nutrition || {};
        const additives  = [...(result.additives?.primary || []), ...(result.additives?.generic || [])];
        const scoreColor = getScoreColor(score);

        // Severe detection
        let isSevere = false, severeReason = "";
        reasons.forEach(r => {
            if (r.includes("SEVERE") || r.includes("BANNED") || r.toLowerCase().includes("allergy")) {
                isSevere = true; severeReason = r;
            }
        });

        const glow        = isSevere ? "0 0 45px rgba(239,68,68,0.8)" : score < 40 ? "0 0 25px rgba(239,68,68,0.35)" : "0 0 20px rgba(0,0,0,0.45)";
        const borderColor = isSevere ? "rgba(239,68,68,0.9)" : "rgba(255,255,255,0.08)";
        const regionIcon  = reqData.region === "eu" ? "🇪🇺 EU" : reqData.region === "usa" ? "🇺🇸 FDA" : reqData.region === "india" ? "🇮🇳 FSSAI" : "🌐 Global";
        const allergyCount = (reqData.allergies && reqData.allergies.length > 0) ? reqData.allergies.length : 0;

        // Health Risks — dual-source (API health_flags + fallback from reasons)
        let healthFlags = [...(result.health_flags || [])];
        if (healthFlags.length === 0 && score < 70) {
            const rStr = reasons.join(" ").toLowerCase();
            const checks = [
                { keys: ["sodium", "salt", "bp"],       type: "bp",      icon: "🩺" },
                { keys: ["trans fat", "heart"],          type: "heart",   icon: "🫀" },
                { keys: ["sugar", "diabetes"],           type: "diabetes",icon: "🩸" },
                { keys: ["calorie", "weight", "obese"],  type: "weight",  icon: "⚖️" },
                { keys: ["processed"],                   type: "process", icon: "⚠️" },
                { keys: ["msg", "flavour"],              type: "sensit",  icon: "⚠️" },
            ];
            checks.forEach(({ keys, type, icon }) => {
                if (keys.some(k => rStr.includes(k)) && !healthFlags.find(f => f.type === type)) {
                    const reason = reasons.find(r => keys.some(k => r.toLowerCase().includes(k)));
                    if (reason) healthFlags.push({ type, message: reason.replace(/^[🚨⚠️✅❌•\s]+/, '') });
                }
            });
        }

        const riskIcon = (t) => t === "heart" ? "🫀" : t === "bp" ? "🩺" : t === "diabetes" ? "🩸" : t === "weight" ? "⚖️" : "⚠️";
        const healthRisksHTML = healthFlags.length > 0 ? `
            <div style="background:rgba(239,68,68,0.06);border:1px solid rgba(239,68,68,0.15);border-radius:12px;padding:12px;margin-top:12px;">
                <div style="font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:0.6px;color:#ef4444;margin-bottom:8px;">🚨 Health Risks</div>
                ${healthFlags.map(f => `<div style="font-size:12px;color:rgba(255,255,255,0.82);margin-bottom:5px;display:flex;gap:7px;line-height:1.4;"><span>${riskIcon(f.type)}</span><span>${f.message}</span></div>`).join('')}
            </div>` : '';

        // Nutrition bars
        const nutFields = [
            { label: "Sodium",    val: nutrition.sodium_mg,        max: 2000, unit: "mg",   d: 1000, w: 500 },
            { label: "Sugar",     val: nutrition.sugar_g,          max: 50,   unit: "g",    d: 20,   w: 10  },
            { label: "Total Fat", val: nutrition.fat_g,            max: 60,   unit: "g",    d: 30,   w: 15  },
            { label: "Sat. Fat",  val: nutrition.saturated_fat_g,  max: 30,   unit: "g",    d: 10,   w: 5   },
            { label: "Calories",  val: nutrition.energy_kcal,      max: 600,  unit: "kcal", d: 400,  w: 250 },
        ].filter(f => f.val !== null && f.val !== undefined);

        const nutritionBarsHTML = nutFields.length > 0 ? `
            <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.06);border-radius:12px;padding:12px;margin-top:12px;">
                <div style="font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:0.6px;color:rgba(255,255,255,0.65);margin-bottom:12px;">📊 Nutrition Impact</div>
                ${nutFields.map(f => buildNutritionBar(f.label, f.val, f.max, f.unit, f.d, f.w)).join('')}
            </div>` : '';

        // Key Issues
        const negativeReasons = reasons.filter(r => !r.startsWith("✅")).slice(0, 6);
        const positiveReasons = reasons.filter(r => r.startsWith("✅"));
        const keyIssuesHTML = negativeReasons.length > 0 ? `
            <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.06);border-radius:12px;padding:12px;margin-top:12px;">
                <div style="font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:0.6px;color:rgba(255,255,255,0.65);margin-bottom:9px;">⚡ Key Issues</div>
                ${negativeReasons.map(r => `<div style="font-size:12px;color:rgba(255,255,255,0.8);margin-bottom:6px;display:flex;gap:6px;line-height:1.4;"><span style="flex-shrink:0;">•</span><span>${r}</span></div>`).join('')}
                ${positiveReasons.map(r => `<div style="font-size:12px;color:#22c55e;margin-bottom:5px;">${r}</div>`).join('')}
            </div>` : '';

        // Additives
        const additivesHTML = additives.length > 0 ? `
            <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.06);border-radius:12px;padding:12px;margin-top:12px;">
                <div style="font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:0.6px;color:rgba(255,255,255,0.65);margin-bottom:9px;">🧪 Additives (${additives.length})</div>
                <div style="display:flex;flex-wrap:wrap;gap:5px;">
                    ${additives.map(a => `<span class="safe-additive" data-name="${a.name}" data-code="${a.code||''}" data-risk="${a.risk}" data-category="${a.category||''}" style="background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.08);padding:4px 9px;border-radius:20px;font-size:11px;font-weight:600;color:${getRiskColor(a.risk)};cursor:pointer;transition:all 0.15s;">${a.name}</span>`).join('')}
                </div>
            </div>` : '';

        // Better Alternative
        const altHTML = (score < 60 && result.better_alternatives && result.better_alternatives.length > 0) ? (() => {
            const alt = result.better_alternatives[0];
            return `
            <div style="background:linear-gradient(135deg,rgba(34,197,94,0.07),rgba(16,185,129,0.1));border:1px solid rgba(34,197,94,0.25);border-radius:12px;padding:12px;margin-top:12px;">
                <div style="font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:0.5px;color:#22c55e;margin-bottom:10px;">✨ Healthier Alternative</div>
                <div style="display:flex;align-items:center;gap:10px;background:rgba(0,0,0,0.25);padding:8px;border-radius:8px;">
                    <div style="width:36px;height:36px;border-radius:8px;background:#22c55e;color:black;font-weight:800;display:flex;align-items:center;justify-content:center;font-size:14px;flex-shrink:0;">${Math.round(alt.health_score)}</div>
                    <div><div style="font-size:12px;font-weight:700;color:white;line-height:1.3;">${alt.name.substring(0,40)}${alt.name.length > 40 ? '…' : ''}</div><div style="font-size:10px;color:#aaa;margin-top:2px;">${alt.brand || 'SafeShop'}</div></div>
                </div>
                <a href="http://127.0.0.1:8000" target="_blank" style="display:block;text-align:center;margin-top:10px;background:#22c55e;color:black;padding:8px;border-radius:8px;font-size:11px;font-weight:700;text-decoration:none;text-transform:uppercase;">Buy on SafeShop Instead →</a>
            </div>`;
        })() : '';

        // Advice — from nutrition values first, then reason keywords
        const adviceItems = [];
        if (nutrition.trans_fat_g > 0)        adviceItems.push("❌ Avoid frequent consumption (heart risk)");
        if (nutrition.sodium_mg > 1000)        adviceItems.push("⚠️ Very occasional intake only");
        else if (nutrition.sodium_mg > 500)    adviceItems.push("⚠️ Limit intake (BP risk)");
        if (result.flags?.msg)                 adviceItems.push("⚠️ Contains flavour enhancers (may trigger sensitivity)");
        if (result.flags?.ultra_processed)     adviceItems.push("⚠️ Highly processed — avoid daily consumption");
        if (nutrition.sugar_g > 20)            adviceItems.push("⚠️ High sugar — not suitable for diabetics");
        if (adviceItems.length === 0) {
            const rStr = reasons.join(" ").toLowerCase();
            if (rStr.includes("trans fat"))    adviceItems.push("❌ Avoid frequent consumption (heart risk)");
            if (rStr.includes("sodium") || rStr.includes("salt")) adviceItems.push("⚠️ Limit intake (BP risk)");
            if (rStr.includes("processed"))    adviceItems.push("⚠️ Highly processed — avoid daily consumption");
            if (rStr.includes("msg") || rStr.includes("flavour")) adviceItems.push("⚠️ Contains flavour enhancers");
        }
        if (adviceItems.length === 0)          adviceItems.push("✅ Generally safe in moderation");

        // Auto-expand for unhealthy products
        const autoExpand = score < 60;

        let box = document.createElement("div");
        box.id = "safe-shop-box";
        box.innerHTML = `
        <div id="safe-main" style="position:fixed;top:85px;right:20px;width:330px;max-height:calc(100vh - 100px);border-radius:20px;background:rgba(14,14,20,0.93);backdrop-filter:blur(24px);border:1px solid ${borderColor};box-shadow:${glow};color:white;cursor:pointer;z-index:999999;animation:ss-fadeIn 0.4s ease;display:flex;flex-direction:column;overflow:hidden;">

            ${isSevere ? `<div style="background:linear-gradient(90deg,#b91c1c,#ef4444);color:white;padding:9px 18px;font-weight:800;font-size:11px;text-transform:uppercase;text-align:center;letter-spacing:1px;flex-shrink:0;">🚨 ${severeReason}</div>` : ''}

            <!-- HEADER: flex-shrink:0 so it never compresses -->
            <div style="padding:18px 18px 14px;flex-shrink:0;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div style="display:flex;align-items:center;gap:14px;">
                        <div style="position:relative;width:64px;height:64px;flex-shrink:0;">
                            <svg width="64" height="64" style="transform:rotate(-90deg);">
                                <circle cx="32" cy="32" r="27" fill="none" stroke="rgba(255,255,255,0.07)" stroke-width="5"/>
                                <circle cx="32" cy="32" r="27" fill="none" stroke="${scoreColor}" stroke-width="5"
                                    stroke-dasharray="${(2*Math.PI*27).toFixed(2)}"
                                    stroke-dashoffset="${(2*Math.PI*27*(1-score/100)).toFixed(2)}"
                                    stroke-linecap="round"/>
                            </svg>
                            <div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:17px;font-weight:800;color:${scoreColor};">${Math.round(score)}</div>
                        </div>
                        <div>
                            <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:rgba(255,255,255,0.35);margin-bottom:3px;">SAFE SCORE</div>
                            <div style="font-size:22px;font-weight:800;color:white;letter-spacing:-0.5px;">${verdict}</div>
                        </div>
                    </div>
                    <div id="safe-arrow" style="font-size:22px;opacity:0.4;transition:transform 0.3s ease;padding:4px;transform:${autoExpand ? 'rotate(180deg)' : 'rotate(0deg)'};">⌄</div>
                </div>
                <div style="display:flex;gap:7px;margin-top:12px;padding-top:12px;border-top:1px solid rgba(255,255,255,0.07);">
                    <div style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.07);padding:4px 9px;border-radius:20px;font-size:10px;font-weight:600;color:#a1a1aa;">🛡️ ${regionIcon}</div>
                    <div style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.07);padding:4px 9px;border-radius:20px;font-size:10px;font-weight:600;color:${allergyCount > 0 ? '#ef4444' : '#a1a1aa'};">🦠 ${allergyCount > 0 ? allergyCount + ' Allergen' + (allergyCount > 1 ? 's' : '') : 'No Allergens'}</div>
                </div>
            </div>

            <!-- DETAILS: flex:1 + overflow-y:auto = scrolls within the card, never clips -->
            <div id="safe-details" style="flex:1;overflow-y:${autoExpand ? 'auto' : 'hidden'};max-height:${autoExpand ? '100%' : '0'};opacity:${autoExpand ? '1' : '0'};transition:max-height 0.45s cubic-bezier(0.4,0,0.2,1),opacity 0.35s ease;padding:0 18px;">
                ${healthRisksHTML}
                ${nutritionBarsHTML}
                ${keyIssuesHTML}
                ${additivesHTML}
                ${altHTML}
                <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.06);border-radius:12px;padding:12px;margin-top:12px;margin-bottom:18px;">
                    <div style="font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:0.6px;color:rgba(255,255,255,0.65);margin-bottom:8px;">💡 Advice</div>
                    ${adviceItems.map(i => `<div style="font-size:12px;color:rgba(255,255,255,0.8);margin-bottom:6px;line-height:1.5;">${i}</div>`).join('')}
                </div>
            </div>
        </div>`;
        document.body.appendChild(box);

        const tooltip = createTooltip();
        document.querySelectorAll(".safe-additive").forEach(el => {
            el.addEventListener("mouseenter", () => {
                el.style.background = "rgba(255,255,255,0.13)";
                tooltip.innerHTML = `<b style="font-size:13px;">${el.dataset.name}</b>${el.dataset.code ? `<div style="color:#aaa;margin-top:3px;">Code: ${el.dataset.code.toUpperCase()}</div>` : ''}<div style="color:${getRiskColor(el.dataset.risk)};font-weight:600;margin-top:4px;">Risk: ${el.dataset.risk.toUpperCase()}</div><div style="color:#aaa;margin-top:2px;">Type: ${el.dataset.category}</div>`;
                tooltip.style.opacity = "1";
            });
            el.addEventListener("mousemove", (e) => {
                let x = e.clientX + 15, y = e.clientY + 15;
                if (x + 230 > window.innerWidth) x -= 245;
                if (y + 130 > window.innerHeight) y -= 140;
                tooltip.style.left = x + "px"; tooltip.style.top = y + "px";
            });
            el.addEventListener("mouseleave", () => {
                el.style.background = "rgba(255,255,255,0.07)";
                tooltip.style.opacity = "0";
            });
        });

        const main = box.querySelector("#safe-main");
        const details = box.querySelector("#safe-details");
        const arrow = box.querySelector("#safe-arrow");
        let isExpanded = autoExpand;
        main.addEventListener("click", (e) => {
            if (e.target.classList.contains("safe-additive") || e.target.tagName === "A") return;
            isExpanded = !isExpanded;
            details.style.flex       = isExpanded ? "1" : "0 0 0px";
            details.style.maxHeight  = isExpanded ? "100%" : "0";
            details.style.overflowY  = isExpanded ? "auto" : "hidden";
            details.style.opacity    = isExpanded ? "1" : "0";
            arrow.style.transform    = isExpanded ? "rotate(180deg)" : "rotate(0deg)";
        });
    }

    // ============================
    // MAIN PIPELINE
    // ============================
    async function executeSafeShopLive() {
        const name = getProductName();
        if (!name) {
            console.log("%c[SafeShop] No product name found — not a product page or still loading", "color:#f59e0b;");
            return;
        }

        console.log("%c[SafeShop] Product detected: " + name, "color:#3b82f6;font-weight:bold;");

        let ingredients  = getIngredientsText() || "";
        let nutritionTxt = getNutritionText()   || "";

        console.log("%c[SafeShop] Ingredients (" + ingredients.length + " chars): " + ingredients.substring(0, 80), "color:#a78bfa;");
        console.log("%c[SafeShop] Nutrition (" + nutritionTxt.length + " chars): " + nutritionTxt.substring(0, 80), "color:#a78bfa;");

        let ocrUsed    = false;
        // KEY FIX: use validated check — length alone is not enough (Amazon has junk "Nutrition" text)
        const hasNutrition = hasRealNutritionData(nutritionTxt);
        console.log("%c[SafeShop] hasRealNutrition: " + hasNutrition, "color:#a78bfa;");

        if ((!ingredients || ingredients.length < 15) && !hasNutrition) {
            console.log("%c[SafeShop] No text data found — starting Ghost Scanner (OCR)", "color:#f59e0b;");
            const hostname = window.location.hostname;
            let candidateImages = [];

            if (hostname.includes('amazon')) {
                await new Promise(r => setTimeout(r, 800)); // Extra wait for lazy images
                document.querySelectorAll('#altImages img, #imageBlock img, #main-image-container img, .a-button-thumbnail img').forEach(img => {
                    if (img.src && img.src.includes('images/I/'))
                        candidateImages.push({ img, url: img.src.replace(/\._.*?_\./, '.') });
                });
            } else if (hostname.includes('bigbasket')) {
                document.querySelectorAll('img').forEach(img => {
                    if (img.src && img.src.includes('media/uploads/p/'))
                        candidateImages.push({ img, url: img.src.replace('/s/', '/l/').replace('/m/', '/l/') });
                });
            } else {
                document.querySelectorAll('img').forEach(img => {
                    if (img.src && img.src.startsWith('http'))
                        candidateImages.push({ img, url: img.src });
                });
            }

            candidateImages.sort((a, b) => scoreImageForOCR(b.img) - scoreImageForOCR(a.img));
            const seen = new Set();
            candidateImages = candidateImages.filter(c => {
                if (seen.has(c.url)) return false; seen.add(c.url); return true;
            }).slice(0, 5);

            console.log("%c[SafeShop] OCR candidates: " + candidateImages.length, "color:#f59e0b;");

            if (candidateImages.length > 0 && typeof chrome !== "undefined") {
                let ex = document.getElementById("safe-shop-box"); if (ex) ex.remove();
                let loader = document.createElement("div");
                loader.id = "safe-shop-box";
                loader.innerHTML = `<div style="position:fixed;top:90px;right:20px;width:300px;padding:22px 20px;border-radius:20px;background:rgba(14,14,20,0.93);backdrop-filter:blur(20px);border:1px solid rgba(255,255,255,0.08);box-shadow:0 0 25px rgba(0,0,0,0.5);color:white;z-index:999999;display:flex;flex-direction:column;align-items:center;text-align:center;"><div style="width:42px;height:42px;border-radius:50%;border:3px solid rgba(255,255,255,0.08);border-top-color:#3b82f6;animation:ss-spin 0.9s linear infinite;margin-bottom:14px;"></div><div style="font-size:14px;font-weight:700;margin-bottom:6px;">👻 Ghost Scanner</div><div style="font-size:11px;opacity:0.5;line-height:1.5;">Scanning ${candidateImages.length} images.</div></div>`;
                document.body.appendChild(loader);

                let lastOcrError = "None";
                for (let candidate of candidateImages) {
                    const ocrRes = await new Promise(resolve => {
                        chrome.runtime.sendMessage({ type: "RUN_OCR", url: candidate.url }, resolve);
                    });
                    if (ocrRes && ocrRes.error) lastOcrError = ocrRes.error;
                    if (ocrRes && ocrRes.success && ocrRes.raw_text &&
                        (ocrRes.raw_text.toLowerCase().includes("ingredient") || ocrRes.raw_text.length > 50)) {
                        ingredients = ocrRes.raw_text;
                        // pass the OCR text to nutrition so the backend can parse macros
                        if (!hasNutrition) {
                            nutritionTxt = ocrRes.raw_text;
                        }
                        ocrUsed = true;
                        console.log("%c[SafeShop] OCR success!", "color:#22c55e;font-weight:bold;");
                        break;
                    }
                }
                window.__safeShopLastOcrError = lastOcrError;
            }
        }

        const detectedCategory = guessCategoryFromName(name);
        console.log("%c[SafeShop] Detected category: " + detectedCategory, "color:#a78bfa;");

        const data = {
            name:           name,
            category:       detectedCategory,
            nutrition_text: nutritionTxt,
            ingredients:    ingredients,
            region:         "global",
            allergies:      []
        };

        if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
            await new Promise(resolve => {
                chrome.storage.local.get(['region', 'allergies'], (cfg) => {
                    if (cfg.region)    data.region    = cfg.region;
                    if (cfg.allergies) data.allergies = cfg.allergies.split(',').map(s => s.trim()).filter(Boolean);
                    resolve();
                });
            });
        }

        console.log("%c[SafeShop] Sending to API:", "color:#3b82f6;font-weight:bold;", {
            name: data.name, category: data.category,
            ingredientLen: data.ingredients.length,
            nutritionLen:  data.nutrition_text.length,
        });

        const result = await getScoreFromAPI(data);
        console.log("%c[SafeShop] API score: " + (result ? result.score : 'NULL'), "color:#22c55e;font-weight:bold;");

        const hasIngredients   = ingredients && ingredients.length >= 15;
        const hasNutritionData = hasRealNutritionData(nutritionTxt);

        if (!hasIngredients && !hasNutritionData) {
            window.__safeShopFailedState = true;
            if (result && !result.error) {
                result.score            = 0;
                result.verdict          = "⚠️ Data Missing";
                result.reasons          = ["No ingredient or nutrition data found on this page."];
                result.additives        = { primary: [], generic: [] };
                result.parsed_nutrition = {};
                result.health_flags     = [];
            }
        } else {
            window.__safeShopFailedState = false;
        }

        if (result && ocrUsed && !result.error) result.verdict = "💡 Scanned via OCR";

        renderUI(result, data);
    }

    let memoryTarget = null, memoryImage = null;

    setInterval(() => {
        const name = getProductName();
        if (!name) return;

        let hero = document.getElementById("landingImage");
        if (!hero) hero = Array.from(document.images).find(img => img.width > 250 && img.height > 250 && img.src.startsWith('http'));
        const imgTarget = hero ? hero.src : null;

        if (name !== memoryTarget || (window.__safeShopFailedState && imgTarget !== memoryImage)) {
            memoryTarget = name;
            memoryImage  = imgTarget;
            window.__safeShopFailedState = false;
            // Amazon needs more time for JS rendering
            const delay = window.location.hostname.includes('amazon') ? 2000 : 900;
            setTimeout(executeSafeShopLive, delay);
        }
    }, 1500);
}