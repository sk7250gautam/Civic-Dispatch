"""
Civic Dispatch — Priority Recommendation Engine
Analyzes safety hazard factors and urgency cues to recommend grievance priority.
Requires explicit human verification before consequential dispatch.
"""

import re
from typing import Dict, Any, List
from app.models.complaint import ComplaintPriority

# Safety Hazard Indicators
CRITICAL_HAZARD_PATTERNS = [
    r"\blive\s+(electric\s+)?wire\b",
    r"\belectric(al)?\s+(wire|shock)\b",
    r"\bhigh\s+voltage\b",
    r"\bsparking\b",
    r"\bopen\s+manhole\b",
    r"\bsinkhole\b",
    r"\broad\s+cave(-|\s)?in\b",
    r"\bgas\s+leak\b",
    r"\btoxic\b",
    r"\bmajor\s+flood\b",
    r"\bwall\s+collapse\b",
    r"\bhospital\s+access\b",
    r"\bambulance\s+blocked\b",
    r"\bchild(ren)?\s+hazard\b",
]

HIGH_PRIORITY_PATTERNS = [
    r"\bmain\s+road\b",
    r"\bintersection\b",
    r"\bdrinking\s+water\b",
    r"\bcontamination\b",
    r"\bheavy\s+traffic\b",
    r"\bschool\s+zone\b",
    r"\bdeep\s+pothole\b",
    r"\bwaterlogging\b",
    r"\baccident\b",
    r"\bdanger\b",
]

def recommend_priority(title: str, description: str, category: str) -> Dict[str, Any]:
    """
    Evaluates urgency and potential safety hazards.
    Always returns clear rule-based reasoning and human verification advisory.
    """
    text = f"{title} {description}".lower()

    # Check Critical Hazards
    critical_triggers = []
    for pattern in CRITICAL_HAZARD_PATTERNS:
        matches = re.findall(pattern, text)
        if matches:
            critical_triggers.append(pattern.replace(r"\b", "").replace(r"\s+", " ").strip("\\"))

    if critical_triggers:
        return {
            "recommended_priority": ComplaintPriority.CRITICAL.value,
            "confidence": 0.92,
            "is_safety_hazard": True,
            "triggers": critical_triggers,
            "reasoning": f"Critical public safety cue detected: {', '.join(critical_triggers)}.",
            "disclaimer": "AI/Rule recommendation only. Field officer confirmation required; do not rely as sole emergency verification.",
        }

    # Check High Priority
    high_triggers = []
    for pattern in HIGH_PRIORITY_PATTERNS:
        matches = re.findall(pattern, text)
        if matches:
            high_triggers.append(pattern.replace(r"\b", "").replace(r"\s+", " ").strip("\\"))

    if high_triggers or category in ["DRAINAGE_FLOODING", "WATER_SUPPLY"]:
        return {
            "recommended_priority": ComplaintPriority.HIGH.value,
            "confidence": 0.80,
            "is_safety_hazard": False,
            "triggers": high_triggers,
            "reasoning": f"High municipal impact identified ({', '.join(high_triggers) if high_triggers else category}).",
            "disclaimer": "Rule-based recommendation. Final priority requires officer verification.",
        }

    # Default Medium
    return {
        "recommended_priority": ComplaintPriority.MEDIUM.value,
        "confidence": 0.70,
        "is_safety_hazard": False,
        "triggers": [],
        "reasoning": "Standard municipal grievance without immediate hazard flags.",
        "disclaimer": "Rule-based recommendation. Final priority requires officer verification.",
    }
