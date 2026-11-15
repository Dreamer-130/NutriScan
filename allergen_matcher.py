import json
import re
from rapidfuzz import fuzz

def load_allergen_db(path: str = "allergens_db.json") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def split_sections(raw_text: str) -> tuple[str, str]:
    text = raw_text.strip()
    may_contain_match = re.search(
        r"(may contain|processed in a facility|manufactured on shared equipment|traces of).*",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if may_contain_match:
        precautionary = may_contain_match.group(0).strip()
        main_ingredients = text[: may_contain_match.start()].strip()
    else:
        precautionary = ""
        main_ingredients = text

    main_ingredients = re.sub(r"^.*?ingredients\s*:\s*", "", main_ingredients, flags=re.IGNORECASE | re.DOTALL)
    return main_ingredients, precautionary

def tokenize_ingredients(text: str) -> list[str]:
    tokens = re.split(r"[,;\(\)\[\]\.\n]+", text.lower())
    return [t.strip() for t in tokens if len(t.strip()) > 1]

def find_keyword_matches(tokens: list[str], keywords: list[str], fuzzy_threshold: int = 86) -> list[dict]:
    matches = {}
    joined = " ".join(tokens)

    for kw in keywords:
        kw_low = kw.lower()
        # 1. Exact word-boundary match
        if re.search(rf"\b{re.escape(kw_low)}\b", joined):
            matches[kw] = {"term": kw, "matched_text": kw_low, "score": 100, "type": "Exact"}
            continue

        # 2. Fuzzy match per ingredient token (catches OCR typos like 'caseln' -> 'casein')
        if len(kw_low) >= 4:
            for tok in tokens:
                score = fuzz.ratio(kw_low, tok)
                if score >= fuzzy_threshold:
                    if kw not in matches or score > matches[kw]["score"]:
                        matches[kw] = {
                            "term": kw,
                            "matched_text": tok,
                            "score": round(score),
                            "type": "Fuzzy OCR",
                        }
    return list(matches.values())

def scan_family_profiles(raw_text: str, family_profiles: dict, db: dict, fuzzy_threshold: int = 86) -> dict:
    main_text, precautionary_text = split_sections(raw_text)
    main_tokens = tokenize_ingredients(main_text)
    prec_tokens = tokenize_ingredients(precautionary_text)

    results = {}
    for member, allergies in family_profiles.items():
        direct_flags = []
        trace_flags = []

        for allergen_cat in allergies:
            if allergen_cat not in db:
                continue
            entry = db[allergen_cat]

            direct_hits = find_keyword_matches(main_tokens, entry["keywords"], fuzzy_threshold)
            if direct_hits:
                direct_flags.append({
                    "category": allergen_cat,
                    "icon": entry.get("icon", "⚠️"),
                    "hits": direct_hits,
                    "explanation": entry["explanation"],
                    "alternatives": entry["alternatives"],
                })

            if prec_tokens:
                trace_hits = find_keyword_matches(prec_tokens, entry["keywords"], fuzzy_threshold)
                if trace_hits:
                    trace_flags.append({
                        "category": allergen_cat,
                        "icon": entry.get("icon", "⚠️"),
                        "hits": trace_hits,
                    })

        if direct_flags:
            status = "DANGER"
        elif trace_flags:
            status = "CAUTION"
        else:
            status = "SAFE"

        results[member] = {
            "status": status,
            "direct_flags": direct_flags,
            "trace_flags": trace_flags,
        }

    return {
        "members": results,
        "tokens": main_tokens,
        "precautionary_text": precautionary_text,
    }
