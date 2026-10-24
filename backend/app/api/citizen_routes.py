import os
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app.extensions import db, limiter
from app.models.complaint import Complaint, ComplaintAttachment, ComplaintStatus, ComplaintPriority, ComplaintCategory, AttachmentType
from app.models.department import Department
from app.models.service_zone import ServiceZone
from app.models.feedback import CitizenFeedback
from app.models.history import ComplaintStatusHistory
from app.models.audit import AuditEvent
from app.models.user import RoleEnum
from app.sla.calculator import calculate_sla_deadline
from app.state_machine.transitions import ComplaintStateMachine, StateTransitionError
from app.security.rbac import role_required, verify_complaint_access
from app.security.file_validator import validate_and_save_upload, FileValidationError

citizen_bp = Blueprint("citizens", __name__, url_prefix="/api/v1/citizens")

# Mapping of categories to default handling departments
CATEGORY_DEPARTMENT_CODES = {
    ComplaintCategory.ROAD_INFRASTRUCTURE.value: "ROADS",
    ComplaintCategory.WATER_SUPPLY.value: "WATER",
    ComplaintCategory.SOLID_WASTE.value: "WASTE",
    ComplaintCategory.STREET_LIGHTING.value: "POWER",
    ComplaintCategory.HEALTH_SANITATION.value: "HEALTH",
    ComplaintCategory.DRAINAGE_FLOODING.value: "DRAIN",
    ComplaintCategory.OTHER.value: "ROADS",
}

@citizen_bp.route("/complaints", methods=["POST"])
@login_required
@role_required(RoleEnum.CITIZEN.value, RoleEnum.SYSTEM_ADMIN.value)
@limiter.limit("30 per hour")
def submit_complaint():
    """
    Submits a new civic grievance.
    Supports multipart form data with image upload or JSON payload.
    """
    is_multipart = request.content_type and "multipart/form-data" in request.content_type
    if is_multipart:
        data = request.form
        photo_file = request.files.get("photo")
    else:
        data = request.get_json() or {}
        photo_file = None

    title = data.get("title", "").strip()
    description = data.get("description", "").strip()
    category = data.get("category", ComplaintCategory.ROAD_INFRASTRUCTURE.value).strip()
    priority = data.get("priority", ComplaintPriority.MEDIUM.value).strip()
    address = data.get("address", "").strip()

    try:
        latitude = float(data.get("latitude", 0.0))
        longitude = float(data.get("longitude", 0.0))
    except (TypeError, ValueError):
        return jsonify({"error": "VALIDATION_ERROR", "message": "Valid latitude and longitude are required."}), 400

    if not title or not description:
        return jsonify({"error": "VALIDATION_ERROR", "message": "Title and description are required."}), 400

    if not (-90.0 <= latitude <= 90.0) or not (-180.0 <= longitude <= 180.0):
        return jsonify({"error": "VALIDATION_ERROR", "message": "Coordinates are out of physical earth bounds."}), 400

    # Auto-assign Department based on category
    dept_code = CATEGORY_DEPARTMENT_CODES.get(category, "ROADS")
    department = Department.query.filter_by(code=dept_code).first()

    # Calculate SLA Deadline
    deadline, duration, policy_id = calculate_sla_deadline(category, priority)

    complaint = Complaint(
        citizen_id=current_user.id,
        department_id=department.id if department else None,
        title=title,
        description=description,
        category=category,
        priority=priority,
        status=ComplaintStatus.SUBMITTED.value,
        sla_deadline=deadline,
        sla_duration_hours=duration,
        sla_policy_id=policy_id,
        latitude=latitude,
        longitude=longitude,
        address=address or None,
    )
    db.session.add(complaint)
    db.session.flush()  # populate complaint.id

    # Handle image upload if supplied
    if photo_file:
        try:
            upload_dir = current_app.config.get("UPLOAD_FOLDER", "uploads")
            filename, orig_name, file_size, mime_type, extracted_gps = validate_and_save_upload(photo_file, upload_dir)
            
            attachment = ComplaintAttachment(
                complaint_id=complaint.id,
                uploader_id=current_user.id,
                file_path=filename,
                original_filename=orig_name,
                file_size=file_size,
                mime_type=mime_type,
                attachment_type=AttachmentType.CITIZEN_SUBMISSION.value,
            )
            db.session.add(attachment)
        except FileValidationError as e:
            db.session.rollback()
            return jsonify({"error": "FILE_VALIDATION_ERROR", "message": str(e)}), 400

    # Append-only status history for SUBMITTED
    history = ComplaintStatusHistory(
        complaint_id=complaint.id,
        previous_status=None,
        new_status=ComplaintStatus.SUBMITTED.value,
        acting_user_id=current_user.id,
        reason="Citizen grievance registered via portal.",
    )
    db.session.add(history)

    AuditEvent.log(
        action="COMPLAINT_SUBMITTED",
        entity_type="COMPLAINT",
        entity_id=complaint.id,
        actor_id=current_user.id,
        details={"reference_id": complaint.reference_id, "category": category}
    )

    db.session.commit()

    return jsonify({
        "message": "Grievance submitted successfully",
        "complaint": complaint.to_dict(role=current_user.role, viewer_user_id=current_user.id)
    }), 201

@citizen_bp.route("/complaints", methods=["GET"])
@login_required
def list_my_complaints():
    """Lists complaints filed by the current citizen with pagination and status filter."""
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 50)
    status_filter = request.args.get("status")

    query = Complaint.query.filter_by(citizen_id=current_user.id)
    if status_filter:
        query = query.filter_by(status=status_filter)

    pagination = query.order_by(Complaint.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "complaints": [c.to_dict(role=current_user.role, viewer_user_id=current_user.id) for c in pagination.items],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total_items": pagination.total,
            "total_pages": pagination.pages,
        }
    }), 200

@citizen_bp.route("/complaints/<int:complaint_id>", methods=["GET"])
@login_required
def get_complaint_details(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)

    if not verify_complaint_access(complaint, current_user):
        return jsonify({"error": "FORBIDDEN", "message": "You are not authorized to view this grievance."}), 403

    data = complaint.to_dict(role=current_user.role, viewer_user_id=current_user.id)
    data["status_history"] = [h.to_dict() for h in complaint.status_history]
    return jsonify({"complaint": data}), 200

@citizen_bp.route("/complaints/<int:complaint_id>/reopen", methods=["POST"])
@login_required
def reopen_complaint(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    data = request.get_json() or {}
    reason = data.get("reason", "").strip()

    if not reason:
        return jsonify({"error": "VALIDATION_ERROR", "message": "An explanation reason is required to reopen this ticket."}), 400

    try:
        ComplaintStateMachine.transition(
            complaint=complaint,
            new_status=ComplaintStatus.REOPENED.value,
            user=current_user,
            reason=reason
        )
        return jsonify({
            "message": "Complaint reopened successfully.",
            "complaint": complaint.to_dict(role=current_user.role, viewer_user_id=current_user.id)
        }), 200
    except StateTransitionError as e:
        return jsonify({"error": "INVALID_TRANSITION", "message": str(e)}), 400

@citizen_bp.route("/complaints/<int:complaint_id>/feedback", methods=["POST"])
@login_required
def submit_feedback(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)

    if complaint.citizen_id != current_user.id:
        return jsonify({"error": "FORBIDDEN", "message": "Only the filing citizen can rate this resolution."}), 403

    if complaint.status not in [ComplaintStatus.RESOLVED.value, ComplaintStatus.CLOSED.value]:
        return jsonify({"error": "INVALID_STATE", "message": "Feedback can only be submitted for resolved or closed tickets."}), 400

    data = request.get_json() or {}
    try:
        rating = int(data.get("rating", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "VALIDATION_ERROR", "message": "Rating must be an integer between 1 and 5."}), 400

    if not (1 <= rating <= 5):
        return jsonify({"error": "VALIDATION_ERROR", "message": "Rating must be between 1 and 5."}), 400

    comments = data.get("comments", "").strip()
    speed_rating = data.get("resolution_speed_rating")
    officer_rating = data.get("officer_conduct_rating")

    existing_feedback = CitizenFeedback.query.filter_by(complaint_id=complaint.id).first()
    if existing_feedback:
        existing_feedback.rating = rating
        existing_feedback.comments = comments
        existing_feedback.resolution_speed_rating = speed_rating
        existing_feedback.officer_conduct_rating = officer_rating
    else:
        feedback = CitizenFeedback(
            complaint_id=complaint.id,
            citizen_id=current_user.id,
            rating=rating,
            comments=comments,
            resolution_speed_rating=speed_rating,
            officer_conduct_rating=officer_rating
        )
        db.session.add(feedback)

    # Automatically close complaint upon positive citizen rating
    if complaint.status == ComplaintStatus.RESOLVED.value and rating >= 4:
        try:
            ComplaintStateMachine.transition(
                complaint=complaint,
                new_status=ComplaintStatus.CLOSED.value,
                user=current_user,
                reason="Auto-closed upon satisfactory citizen feedback."
            )
        except Exception:
            pass

    db.session.commit()
    return jsonify({"message": "Thank you for your feedback!"}), 200
