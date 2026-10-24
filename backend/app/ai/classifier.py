"""
Civic Dispatch — AI & Local Rule-Based Complaint Classifier
Analyzes grievance title and description to recommend optimal municipal category.
Always provides a 100% deterministic local rule fallback.
"""

import os
import re
from typing import Dict, Any
from app.models.complaint import ComplaintCategory

# Municipal Keyword Vocabulary mapping for deterministic local classifier
CATEGORY_KEYWORDS = {
    ComplaintCategory.ROAD_INFRASTRUCTURE.value: [
        "pothole", "road", "pavement", "asphalt", "crater", "divider", "sidewalk",
        "speed breaker", "tar", "flyover", "street damage", "highway", "footpath"
    ],
    ComplaintCategory.WATER_SUPPLY.value: [
        "water", "pipeline", "leakage", "contamination", "low pressure", "tap",
        "borewell", "water pipe", "drinking water", "supply stopped", "burst pipe"
    ],
    ComplaintCategory.SOLID_WASTE.value: [
        "garbage", "waste", "trash", "dump", "bin", "litter", "rubbish", "debris",
        "dead animal", "stench", "compost", "overflowing bin", "sanitation"
    ],
    ComplaintCategory.STREET_LIGHTING.value: [
        "streetlight", "street light", "lamp", "pole", "dark", "wiring", "bulb",
        "flickering", "lighting", "darkness", "fuse", "blackout"
    ],
    ComplaintCategory.DRAINAGE_FLOODING.value: [
        "drain", "drainage", "flood", "sewage", "gutter", "waterlogging", "manhole",
        "clogged", "overflow", "stormwater", "culvert", "sewer"
    ],
    ComplaintCategory.HEALTH_SANITATION.value: [
        "mosquito", "stagnant", "fogging", "dengue", "hygiene", "pest", "rodents",
        "public toilet", "urinal", "vector", "epidemic", "malaria"
    ],
}

def classify_complaint_text(title: str, description: str) -> Dict[str, Any]:
    """
    Classifies complaint into municipal category.
    Uses Gemini API if configured; falls back transparently to local keyword engine.
    """
    text = f"{title} {description}".lower()
    gemini_key = os.getenv("GEMINI_API_KEY")
    ai_provider = os.getenv("AI_PROVIDER", "local").lower()

    if ai_provider == "gemini" and gemini_key:
        try:
            return _call_gemini_classifier(title, description, gemini_key)
        except Exception:
            # Fall through seamlessly to local rule engine
            pass

    return _classify_local_rules(text)

def _classify_local_rules(text: str) -> Dict[str, Any]:
    """Deterministic, zero-dependency municipal category heuristic."""
    category_scores = {}

    for category, keywords in CATEGORY_KEYWORDS.items():
        score = 0
        matched = []
        for kw in keywords:
            pattern = r'\b' + re.escape(kw) + r'\b'
            matches = len(re.findall(pattern, text))
            if matches > 0:
                score += matches
                matched.append(kw)

        if score > 0:
            category_scores[category] = (score, matched)

    if not category_scores:
        return {
            "category": ComplaintCategory.ROAD_INFRASTRUCTURE.value,
            "confidence": 0.40,
            "source": "local_rule_engine",
            "matched_keywords": [],
            "reasoning": "Defaulting to Road Infrastructure due to generic description."
        }

    best_category = max(category_scores.items(), key=lambda item: item[1][0])
    score, matched = best_category[1]
    confidence = min(0.95, 0.50 + (score * 0.15))

    return {
        "category": best_category[0],
        "confidence": round(confidence, 2),
        "source": "local_rule_engine",
        "matched_keywords": matched,
        "reasoning": f"Identified municipal keywords: {', '.join(matched[:3])}."
    }

def _call_gemini_classifier(title: str, description: str, api_key: str) -> Dict[str, Any]:
    """Calls Gemini API for classification when configured."""
    import requests
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    prompt = f"""
    Categorize this civic complaint into exactly one of these categories:
    [ROAD_INFRASTRUCTURE, WATER_SUPPLY, SOLID_WASTE, STREET_LIGHTING, HEALTH_SANITATION, DRAINAGE_FLOODING, OTHER].
    
    Title: {title}
    Description: {description}

    Respond in JSON format:
    {{"category": "EXACT_CATEGORY_NAME", "confidence": 0.90, "reasoning": "brief reason"}}
    """
    resp = requests.post(
        url,
        json={"contents": [{"parts": [{"text": prompt}]}]},
        headers={"Content-Type": "application/json"},
        timeout=5.0
    )
    if resp.status_code == 200:
        data = resp.json()
        import json
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
        # extract json block
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if match:
            parsed = json.loads(match.group(0))
            return {
                "category": parsed.get("category", "OTHER"),
                "confidence": float(parsed.get("confidence", 0.85)),
                "source": "gemini-1.5-flash",
                "matched_keywords": [],
                "reasoning": parsed.get("reasoning", "Gemini classification")
            }
    raise RuntimeError("Gemini API call failed or timed out")
