# NutriScan

# 🔬 NutriScan: Hidden Allergen OCR Decoder

> **An Optical Character Recognition (OCR) and Semantic Allergen-Decoding System for Multi-User Households**  
> *Academic Year 2026–2027 | Healthcare & Assistive AI Project*

---

## 📌 Project Overview

**NutriScan: Hidden Allergen OCR Decoder** is an assistive food-safety decision-support system designed to help individuals and families with food allergies, intolerances, or strict dietary restrictions quickly evaluate packaged food products.

In commercial food packaging, common allergens are frequently listed under technical, chemical, or botanical synonyms (for example, *sodium caseinate* or *whey* for milk, *arachis hypogaea* for peanuts, or *soy lecithin* for soy) rather than plain everyday terms. Reading dense ingredient panels manually—especially while shopping for multiple family members with conflicting dietary needs—is error-prone and time-consuming.

NutriScan solves this problem by combining **computer vision preprocessing**, **optical character recognition (OCR)**, **regex-based text tokenization**, and a **curated allergen synonym knowledge base** to decode ingredient labels and evaluate every saved household member's profile simultaneously in a single scan.

---

## ✨ Key Features

1. **Multi-Mode Label Input**
   * Supports uploading packaged food label photographs (`JPG`, `PNG`, `WEBP`), capturing live images via webcam, or testing with built-in sample ingredient panels.
2. **OpenCV Image Enhancement Pipeline**
   * Prepares low-contrast, glossy, or unevenly lit packaging photos for OCR using grayscale conversion, bicubic upscaling, bilateral denoising, and local adaptive thresholding (Gaussian / Sauvola binarization).
3. **Tesseract OCR & Editable Text Verification**
   * Extracts raw ingredient strings via Tesseract OCR (`--oem 3 --psm 6`) along with word-level confidence metrics, allowing users to review and edit extracted text before running a safety check.
4. **Regex Cleaning & Section Separation**
   * Normalizes extracted text, tokenizes individual ingredients across commas and brackets, and separates primary ingredients from precautionary cross-contamination statements (*"May contain..."*, *"Processed in a facility..."*).
5. **Hidden Scientific & Chemical Synonym Decoding**
   * Maps extracted terms against a structured JSON allergen knowledge base (`allergens_db.json`) with exact word-boundary lookup and fuzzy string matching (`RapidFuzz`) to catch botanical/chemical names and minor OCR typos.
6. **Multi-User Family Safety Matrix**
   * Evaluates all configured household profiles at once and outputs a color-coded per-person safety breakdown:
     * **🚨 DANGER:** Direct allergen or hidden synonym found in the main ingredients.
     * **⚠️ CAUTION:** Allergen referenced in a precautionary trace / shared-facility warning.
     * **✅ SAFE:** No listed allergen or synonym detected for that profile.
7. **Smart Safe-Product Substitution Engine**
   * Provides plain-English explanations of *why* a flagged ingredient triggers an allergy and recommends verified allergen-free shelf alternatives from the same product category.

---

## 🏗️ System Architecture & Workflow

```text
┌─────────────────────────────┐
│  1. Food Label Image Input  │  (Upload Photo / Webcam Capture)
└──────────────┬──────────────┘
               ▼
┌─────────────────────────────┐
│  2. OpenCV Preprocessing    │  (Grayscale → 1.5x Upscale → Bilateral Denoise → Adaptive Thresholding)
└──────────────┬──────────────┘
               ▼
┌─────────────────────────────┐
│  3. Tesseract OCR Engine    │  (Character Extraction + Word Confidence Score)
└──────────────┬──────────────┘
               ▼
┌─────────────────────────────┐
│  4. Regex Text Cleaning     │  (Header Removal, Section Splitting & Ingredient Tokenization)
└──────────────┬──────────────┘
               ▼
┌─────────────────────────────┐
│  5. Allergen Matching       │  (Exact Lookup + RapidFuzz Similarity vs. allergens_db.json)
└──────────────┬──────────────┘
               ▼
┌─────────────────────────────┐
│  6. Family Safety Matrix &  │  (Per-Member SAFE / CAUTION / DANGER + Safe Product Swaps)
│     Substitution Engine     │
└─────────────────────────────┘
```

---

## 📂 Repository Structure

```text
NutriScan/
├── app.py                  # Main Streamlit web application & Family Safety Matrix UI
├── ocr_engine.py           # OpenCV preprocessing pipelines & Tesseract OCR extraction
├── allergen_matcher.py     # Regex tokenization, section splitting & exact/fuzzy allergen matching
├── allergens_db.json       # Curated knowledge base of allergens, hidden synonyms & safe alternatives
├── requirements.txt        # Python dependencies
├── packages.txt            # System-level Linux packages (tesseract-ocr) for cloud deployment
├── .streamlit/
│   └── config.toml         # Custom UI theme configuration
└── README.md               # Project documentation
```

---

## 🧬 Allergen Knowledge Base (`allergens_db.json`)

The reference database tracks **7 major allergen categories** along with their hidden chemical/botanical synonyms, physiological trigger explanations, and safe product substitutes:

| Allergen Category | Sample Tracked Keywords & Hidden Synonyms | Sample Safe Alternatives |
| :--- | :--- | :--- |
| **Milk / Dairy** | `milk`, `casein`, `caseinate`, `sodium caseinate`, `whey`, `lactose`, `lactalbumin`, `ghee`, `curds` | Oatly Barista Oat Milk, Violife Dairy-Free Cheddar |
| **Peanuts** | `peanut`, `arachis hypogaea`, `groundnut`, `monkey nut`, `arachis oil`, `mandelonas`, `lupin` | SunButter Organic Sunflower Spread, Wowbutter |
| **Gluten / Wheat** | `wheat`, `gluten`, `barley`, `rye`, `malt extract`, `semolina`, `spelt`, `durum`, `triticum`, `seitan` | Barilla Gluten-Free Penne, Bob's Red Mill 1-to-1 GF Flour |
| **Soy** | `soy`, `soya`, `soy lecithin`, `edamame`, `tofu`, `tempeh`, `miso`, `textured vegetable protein (tvp)` | Enjoy Life Chocolate, Coconut Secret Coconut Aminos |
| **Tree Nuts** | `almond`, `cashew`, `walnut`, `pecan`, `hazelnut`, `pistachio`, `prunus dulcis`, `marzipan`, `gianduja` | Enjoy Life Seed Mix, Elmhurst Unsweetened Oat Creamer |
| **Eggs** | `egg`, `albumen`, `albumin`, `ovalbumin`, `ovomucoid`, `lysozyme`, `mayonnaise`, `meringue` | Follow Your Heart Vegenaise, JUST Egg Plant-Based |
| **Shellfish** | `shrimp`, `prawn`, `crab`, `lobster`, `krill`, `clam`, `mussel`, `oyster`, `scallop`, `crustacean` | Ocean's Halo Vegan Fish Sauce, Gardein Crabless Cakes |

---

## 🛠️ Technology Stack

* **Programming Language:** Python 3.10+
* **Computer Vision & Image Processing:** OpenCV (`opencv-python-headless`), NumPy, Pillow
* **Optical Character Recognition:** Tesseract OCR (`pytesseract`)
* **Text Processing & Fuzzy Matching:** Python `re` (Regular Expressions), `RapidFuzz`
* **Data Storage:** Structured JSON (`allergens_db.json`)
* **Frontend Interface:** Streamlit with custom HTML/CSS cards

---

## 🚀 Local Installation & Setup

### 1. Prerequisites
Install the **Tesseract OCR** system binary on your machine:
* **macOS (Homebrew):**
  ```bash
  brew install tesseract
  ```
* **Ubuntu / Debian Linux:**
  ```bash
  sudo apt-get update && sudo apt-get install -y tesseract-ocr
  ```
* **Windows:**  
  Download and install from the [UB-Mannheim Tesseract Wiki](https://github.com/UB-Mannheim/tesseract/wiki) and add the installation directory to your System `PATH`.

### 2. Clone & Run the Application
```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/nutriscan.git
cd nutriscan

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Launch the Streamlit application
streamlit run app.py
```

---

## 📊 Project Development Roadmap

* **Phase 1 — Research, Architecture & Database Curation (Completed):**
  * Literature review of peer-reviewed studies on Food Allergen Databases (FAD), Sauvola local binarization, and Tesseract OCR performance on food packaging.
  * End-to-end system flowchart and modular architecture design.
  * Curation of `allergens_db.json` mapping major allergens to hidden synonyms, trigger descriptions, and safe alternatives.
* **Phase 2 — OCR Extraction & Matching Engine:**
  * OpenCV adaptive thresholding pipelines, Tesseract OCR integration, regex tokenization, and fuzzy typo matching.
* **Phase 3 — Family Matrix UI, Benchmarking & Deployment:**
  * Interactive multi-profile Streamlit interface, accuracy benchmarking across varied lighting/glare conditions, and cloud deployment.

---

## ⚠️ Medical & Safety Disclaimer

> **Important Notice:** NutriScan is strictly an **assistive informational and educational decision-support tool**. Optical character recognition accuracy depends heavily on camera focus, ambient lighting, packaging glare, font styling, and database completeness. **A scan result indicating `"SAFE"` or `"No listed allergen detected"` is never a 100% guarantee of safety.** Individuals with severe food allergies or anaphylaxis risk must always verify physical product packaging directly and consult qualified healthcare professionals.

---
