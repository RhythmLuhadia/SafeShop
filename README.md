# SafeShop – AI-Driven Product Safety Engine & Marketplace

SafeShop is an AI-driven product safety scoring system aimed at helping consumers make healthier and safer choices when purchasing food and consumer products. The project analyzes a product's ingredient list and nutritional information, detects harmful additives, and assigns a comprehensible health score and verdict (Healthy, Moderate, Unhealthy).

The repository includes a backend API, a batch-processing dataset pipeline, and a browser extension designed to overlay safety insights directly on e-commerce platforms.

## 🚀 Key Features

*   **Ingredient Analysis:** Uses NLP and regex to extract and normalize ingredient names and additive codes (E-numbers / INS codes).
*   **Nutritional Parsing:** Extracts key macros (Sugar, Sodium, Trans Fat, Saturated Fat, Carbohydrates, Calories) from raw nutrition text.
*   **Additive Risk Detection:** Cross-references additives against a built-in knowledge base (`knowledge/additives.json`) to pinpoint high/medium-risk additives, sweeteners, artificial colors, and MSG.
*   **Dynamic Health Scoring:** Aggregates penalties from poor nutrition density and bad additives to yield an objective score out of 100.
*   **Humanized Explanations:** Translates complex deductions into easy-to-understand flags (e.g., "🚨 Extremely high salt (BP risk)", "⚠️ Highly processed product").
*   **FastAPI Backend Server:** Offers an `/analyze` REST endpoint for real-time inference.
*   **Browser Extension:** A companion Chrome/browser extension for evaluating products securely while browsing.

---

## 🛠️ System Architecture & Workflow

The system is highly modular and processes data in a clear pipeline, both in batch mode for datasets and in real-time via the API.

### Workflow
1.  **Cleaner (`ingredient_cleaner.py` / `normalize_dataset.py`):** Takes raw text and standardizes wording. Strips parenthesis and irrelevant brackets.
2.  **Analyzer (`ingredient_analyzer.py`):** Uses Regex rules to find specific additive codes (e.g., *ins621*) and matches them against `additives.json`. It categorizes them into primary, secondary, or generic additives, and flags items for ultra-processing, processed oils, and MSG.
3.  **Nutrition Parser (`nutrition_parser4.py`):** Examines the nutritional label text and extracts quantitative data for carbohydrates, sugars, sodium, protein, fiber, and fats.
4.  **Final Scoring Engine (`final_scoring_engine.py`):** Calculates an aggregate penalty.
    *   *Nutrient Penalties:* Subtracts points for high sodium, added sugar, trans fats, and high sugar density.
    *   *Additive Penalties:* Subtracts points for High-risk (-8), Moderate-risk (-4), or Unknown (-2) additives.
    *   *Compression:* Converts the total penalty into a normalized 0-100 score using a non-linear decay curve: `score = 100 * (1 / (1 + penalty / 50))`.
    *   *Verdict logic:* `Healthy` (>=70), `Moderate` (40-69), `Unhealthy` (<40).

---

## 🏗️ Design Choices and Rationale

1.  **Rule-Based NLP over LLMs for Core Extraction:** Instead of using slow and unpredictable LLMs to extract ingredients and calculate metrics, the system depends on powerful regex parsers and exact string matching against a local knowledge base. This choice guarantees high throughput, extreme determinism, and minimal operating costs compared to LLM API calls.
2.  **Logarithmic/Compression Scoring Mechanism:** Instead of a pure subtraction approach where scores could go negative, a decay function (`100 * (1 / (1 + penalty / 50))`) was chosen. This cleanly binds the output to a 0-100 range and penalizes the worst products harshly without breaking the scale.
3.  **Local Knowledge Base (`knowledge/additives.json`):** Instead of calling a 3rd party API or maintaining a hefty relational database, a static JSON dictionary handles additive resolution. This loads instantly into memory on startup, ensuring the API endpoint operates with single-digit millisecond latency.
4.  **Offline Batch Pipeline (`pipeline.py`):** The repository includes tools heavily geared toward scoring an entire dataset offline into JSONL formatting (`scored_dataset.jsonl`). This decoupling of processing from the live environment enables bulk research and pre-computing for faster application loading.
5.  **FastAPI for the Backend:** Chosen for its asynchronous capabilities, auto-generated OpenAPI documentation, and inherent type checking using Pydantic, making the `/analyze` endpoint robust.

---

## 📂 Repository Structure

*   **`api.py`**: The primary FastAPI server application exposing the REST endpoints.
*   **`pipeline.py`**: A batch processing script to take input JSONL products, process them through the scoring modules, and output a `scored_dataset.jsonl`.
*   **`final_scoring_engine.py`**: Contains the mathematical logic for the scoring, the deduction rules, and the humanized string mappings.
*   **`ingredient_analyzer.py`**: Handles code normalization and resolution algorithms against the additive database.
*   **`nutrition_parser4.py`**: Extracts structured JSON metrics from raw block text of nutritional values.
*   **`safeshop extension/`**: Source code for the web browser extension (containing `manifest.json`, `content.js`, `background.js`).
*   **`knowledge/`**: The local JSON dictionaries driving the AI insights.

---

## 🚀 Getting Started

### Prerequisites
*   Python 3.9+
*   FastAPI & Uvicorn

### Running the API
1. Install dependencies:
   ```bash
   pip install fastapi uvicorn pydantic
   ```
2. Run the server:
   ```bash
   uvicorn api:app --reload
   ```
3. API is live at `http://localhost:8000`. You can test by sending a POST request to `/analyze` with a sample product JSON.

### Running Batch Pipeline
To score a dataset offline, ensure you have your `normalized_dataset.jsonl` in the root folder and run:
   ```bash
   python pipeline.py
   ```
