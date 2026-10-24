from app.ai.classifier import classify_complaint_text
from app.ai.priority import recommend_priority
from app.ai.summarizer import generate_officer_summary
from app.ai.duplicate_detector import haversine_distance, text_token_similarity

def test_local_rule_classifier_categorization():
    res = classify_complaint_text("Deep pothole in street", "The road asphalt is damaged and causing vehicle tire punctures")
    assert res["category"] == "ROAD_INFRASTRUCTURE"
    assert res["source"] == "local_rule_engine"
    assert res["confidence"] >= 0.5

def test_priority_hazard_detection():
    # Immediate critical hazard pattern
    res = recommend_priority("Live electric wire hanging", "A high voltage electric wire has snapped near the school gate", "STREET_LIGHTING")
    assert res["recommended_priority"] == "CRITICAL"
    assert res["is_safety_hazard"] is True
    assert len(res["triggers"]) > 0

def test_officer_summarizer_pii_redaction():
    res = generate_officer_summary(
        title="Garbage pile up",
        description="Call me at 9876543210 or email test@gmail.com regarding trash near temple",
        category="SOLID_WASTE",
        address="12th Main Road"
    )
    assert "[REDACTED_PHONE]" in res["summary"] or "[REDACTED_EMAIL]" in res["summary"]
    assert "9876543210" not in res["summary"]
    assert "test@gmail.com" not in res["summary"]

def test_haversine_and_similarity():
    # Distance between two nearby coordinates (approx 111 meters for 0.001 deg lat)
    dist = haversine_distance(12.9716, 77.5946, 12.9726, 77.5946)
    assert 100 < dist < 125

    sim = text_token_similarity("Pothole near metro pillar 14", "Deep pothole near metro pillar 14")
    assert sim >= 0.7
