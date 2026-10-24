"""
Civic Dispatch — Duplicate Grievance Detection Engine
Finds potential duplicate complaints within geographic proximity and semantic similarity.
Never merges tickets automatically; returns candidates for supervisor review.
"""

import math
import re
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from app.models.complaint import Complaint, ComplaintStatus

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two GPS points in meters."""
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def text_token_similarity(text1: str, text2: str) -> float:
    """Calculates Jaccard similarity of word tokens."""
    tokens1 = set(re.findall(r"\w+", text1.lower()))
    tokens2 = set(re.findall(r"\w+", text2.lower()))
    
    # Remove common stop words
    stops = {"the", "a", "an", "is", "in", "at", "of", "on", "and", "or", "to", "for", "with", "near"}
    tokens1 = tokens1 - stops
    tokens2 = tokens2 - stops

    if not tokens1 or not tokens2:
        return 0.0

    intersection = len(tokens1 & tokens2)
    union = len(tokens1 | tokens2)
    return intersection / union if union > 0 else 0.0

def find_duplicate_candidates(
    latitude: float,
    longitude: float,
    category: str,
    title: str,
    description: str,
    exclude_complaint_id: Optional[int] = None,
    max_distance_meters: float = 400.0,
    days_window: int = 14
) -> List[Dict[str, Any]]:
    """
    Scans open or recent grievances for duplicates using geo-radius and token similarity.
    """
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_window)

    query = Complaint.query.filter(
        Complaint.created_at >= cutoff_date,
        Complaint.status.notin_([ComplaintStatus.REJECTED.value, ComplaintStatus.CLOSED.value])
    )
    if exclude_complaint_id:
        query = query.filter(Complaint.id != exclude_complaint_id)

    recent_complaints = query.all()
    candidates = []

    input_text = f"{title} {description}"

    for comp in recent_complaints:
        # 1. Geographic distance check
        distance = haversine_distance(latitude, longitude, comp.latitude, comp.longitude)
        if distance > max_distance_meters:
            continue

        # 2. Semantic text similarity
        target_text = f"{comp.title} {comp.description}"
        similarity = text_token_similarity(input_text, target_text)

        # 3. Category match bonus
        is_same_category = (category == comp.category)
        if is_same_category:
            combined_score = (similarity * 0.6) + 0.4 * (1.0 - min(distance / max_distance_meters, 1.0))
        else:
            combined_score = similarity * 0.5

        if combined_score >= 0.35:
            candidates.append({
                "id": comp.id,
                "reference_id": comp.reference_id,
                "title": comp.title,
                "category": comp.category,
                "status": comp.status,
                "created_at": comp.created_at.isoformat() if comp.created_at else None,
                "distance_meters": round(distance, 1),
                "similarity_score": round(combined_score, 2),
                "is_same_category": is_same_category,
            })

    # Sort by highest similarity
    candidates.sort(key=lambda x: x["similarity_score"], reverse=True)
    return candidates[:5]
