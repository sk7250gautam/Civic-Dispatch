from flask import Blueprint, request, jsonify
from flask_login import login_required
from app.ai.classifier import classify_complaint_text
from app.ai.priority import recommend_priority
from app.ai.duplicate_detector import find_duplicate_candidates
from app.ai.summarizer import generate_officer_summary

ai_bp = Blueprint("ai", __name__, url_prefix="/api/v1/ai")

@ai_bp.route("/categorize", methods=["POST"])
@login_required
def api_categorize():
    data = request.get_json() or {}
    title = data.get("title", "")
    description = data.get("description", "")
    
    result = classify_complaint_text(title, description)
    return jsonify(result), 200

@ai_bp.route("/priority", methods=["POST"])
@login_required
def api_priority():
    data = request.get_json() or {}
    title = data.get("title", "")
    description = data.get("description", "")
    category = data.get("category", "ROAD_INFRASTRUCTURE")
    
    result = recommend_priority(title, description, category)
    return jsonify(result), 200

@ai_bp.route("/duplicate-check", methods=["POST"])
@login_required
def api_duplicate_check():
    data = request.get_json() or {}
    try:
        lat = float(data.get("latitude", 0.0))
        lng = float(data.get("longitude", 0.0))
    except (TypeError, ValueError):
        return jsonify({"candidates": []}), 200

    category = data.get("category", "")
    title = data.get("title", "")
    description = data.get("description", "")
    exclude_id = data.get("exclude_id")

    candidates = find_duplicate_candidates(
        latitude=lat,
        longitude=lng,
        category=category,
        title=title,
        description=description,
        exclude_complaint_id=exclude_id
    )
    return jsonify({"candidates": candidates}), 200

@ai_bp.route("/summarize", methods=["POST"])
@login_required
def api_summarize():
    data = request.get_json() or {}
    title = data.get("title", "")
    description = data.get("description", "")
    category = data.get("category", "")
    address = data.get("address")

    result = generate_officer_summary(title, description, category, address)
    return jsonify(result), 200
