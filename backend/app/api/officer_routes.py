from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, timezone
from app.extensions import db
from app.models.complaint import Complaint, ComplaintAttachment, ComplaintStatus, AttachmentType
from app.models.user import RoleEnum
from app.models.audit import AuditEvent
from app.state_machine.transitions import ComplaintStateMachine, StateTransitionError
from app.security.rbac import role_required, verify_complaint_access
from app.security.file_validator import validate_and_save_upload, FileValidationError
from app.ai.duplicate_detector import haversine_distance

officer_bp = Blueprint("officers", __name__, url_prefix="/api/v1/officers")

@officer_bp.route("/queue", methods=["GET"])
@login_required
@role_required(RoleEnum.FIELD_OFFICER.value, RoleEnum.DEPARTMENT_MANAGER.value, RoleEnum.SYSTEM_ADMIN.value)
def get_work_queue():
    """
    Returns assigned complaints for the field officer.
    Orders tickets by severity (CRITICAL first) and SLA deadline urgency.
    """
    status_filter = request.args.get("status")

    # Priority case sorting
    priority_order = db.case(
        {
            "CRITICAL": 1,
            "HIGH": 2,
            "MEDIUM": 3,
            "LOW": 4,
        },
        value=Complaint.priority,
        else_=5
    )

    query = Complaint.query.filter(
        db.or_(
            Complaint.assigned_officer_id == current_user.id,
            db.and_(
                Complaint.department_id == current_user.department_id,
                Complaint.assigned_officer_id.is_(None),
                Complaint.status.in_([ComplaintStatus.SUBMITTED.value, ComplaintStatus.ACKNOWLEDGED.value])
            )
        )
    )

    if status_filter:
        query = query.filter(Complaint.status == status_filter)
    else:
        # By default exclude terminal closed/rejected tickets in active work queue
        query = query.filter(Complaint.status.notin_([ComplaintStatus.CLOSED.value, ComplaintStatus.REJECTED.value]))

    complaints = query.order_by(priority_order, Complaint.sla_deadline.asc().nullslast()).all()

    return jsonify({
        "queue": [c.to_dict(role=current_user.role, viewer_user_id=current_user.id) for c in complaints],
        "count": len(complaints)
    }), 200

@officer_bp.route("/complaints/<int:complaint_id>/acknowledge", methods=["POST"])
@login_required
@role_required(RoleEnum.FIELD_OFFICER.value, RoleEnum.DEPARTMENT_MANAGER.value, RoleEnum.SYSTEM_ADMIN.value)
def acknowledge_complaint(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    
    # If not assigned, assign to current officer upon acknowledging
    if not complaint.assigned_officer_id:
        complaint.assigned_officer_id = current_user.id

    try:
        ComplaintStateMachine.transition(
            complaint=complaint,
            new_status=ComplaintStatus.ACKNOWLEDGED.value,
            user=current_user,
            reason="Grievance acknowledged by field personnel."
        )
        return jsonify({
            "message": "Ticket acknowledged",
            "complaint": complaint.to_dict(role=current_user.role, viewer_user_id=current_user.id)
        }), 200
    except StateTransitionError as e:
        return jsonify({"error": "INVALID_TRANSITION", "message": str(e)}), 400

@officer_bp.route("/complaints/<int:complaint_id>/start-work", methods=["POST"])
@login_required
@role_required(RoleEnum.FIELD_OFFICER.value, RoleEnum.DEPARTMENT_MANAGER.value, RoleEnum.SYSTEM_ADMIN.value)
def start_work(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    
    if not complaint.assigned_officer_id:
        complaint.assigned_officer_id = current_user.id

    try:
        ComplaintStateMachine.transition(
            complaint=complaint,
            new_status=ComplaintStatus.IN_PROGRESS.value,
            user=current_user,
            reason="Field officer initiated on-site work."
        )
        return jsonify({
            "message": "Work started",
            "complaint": complaint.to_dict(role=current_user.role, viewer_user_id=current_user.id)
        }), 200
    except StateTransitionError as e:
        return jsonify({"error": "INVALID_TRANSITION", "message": str(e)}), 400

@officer_bp.route("/complaints/<int:complaint_id>/resolve", methods=["POST"])
@login_required
@role_required(RoleEnum.FIELD_OFFICER.value, RoleEnum.DEPARTMENT_MANAGER.value, RoleEnum.SYSTEM_ADMIN.value)
def resolve_complaint(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    is_multipart = request.content_type and "multipart/form-data" in request.content_type

    if is_multipart:
        data = request.form
        after_photo = request.files.get("photo")
    else:
        data = request.get_json() or {}
        after_photo = None

    summary = data.get("resolution_summary", "").strip()
    if not summary:
        return jsonify({"error": "VALIDATION_ERROR", "message": "Resolution summary is required."}), 400

    # GPS Verification Logic
    tolerance_meters = current_app.config.get("DEFAULT_COORDINATE_TOLERANCE_METERS", 250.0)
    officer_lat = data.get("latitude")
    officer_lng = data.get("longitude")
    exception_reason = data.get("location_exception_reason", "").strip()

    verification_meta = {}

    if officer_lat is not None and officer_lng is not None:
        try:
            olat = float(officer_lat)
            olng = float(officer_lng)
            distance = haversine_distance(olat, olng, complaint.latitude, complaint.longitude)
            
            complaint.officer_verification_lat = olat
            complaint.officer_verification_lng = olng
            complaint.verification_distance_meters = round(distance, 1)

            if distance <= tolerance_meters:
                complaint.verified_location = True
                complaint.verified_at = datetime.now(timezone.utc)
                verification_meta = {"distance_meters": distance, "verified": True}
            else:
                complaint.verified_location = False
                if exception_reason:
                    complaint.location_exception_reason = exception_reason
                    verification_meta = {"distance_meters": distance, "verified": False, "exception": exception_reason}
                else:
                    return jsonify({
                        "error": "LOCATION_VERIFICATION_FAILED",
                        "message": f"Recorded location is {round(distance)}m from grievance site (tolerance: {tolerance_meters}m). Supply a location exception reason to proceed.",
                        "distance_meters": round(distance)
                    }), 400
        except ValueError:
            pass
    elif exception_reason:
        complaint.verified_location = False
        complaint.location_exception_reason = exception_reason
        verification_meta = {"verified": False, "exception": exception_reason}

    # Upload after-work photo if present
    if after_photo:
        try:
            upload_dir = current_app.config.get("UPLOAD_FOLDER", "uploads")
            filename, orig_name, file_size, mime_type, _ = validate_and_save_upload(after_photo, upload_dir)
            attachment = ComplaintAttachment(
                complaint_id=complaint.id,
                uploader_id=current_user.id,
                file_path=filename,
                original_filename=orig_name,
                file_size=file_size,
                mime_type=mime_type,
                attachment_type=AttachmentType.AFTER_EVIDENCE.value,
            )
            db.session.add(attachment)
        except FileValidationError as e:
            return jsonify({"error": "FILE_VALIDATION_ERROR", "message": str(e)}), 400

    try:
        ComplaintStateMachine.transition(
            complaint=complaint,
            new_status=ComplaintStatus.RESOLVED.value,
            user=current_user,
            resolution_summary=summary,
            metadata=verification_meta
        )
        return jsonify({
            "message": "Complaint successfully marked as resolved",
            "complaint": complaint.to_dict(role=current_user.role, viewer_user_id=current_user.id)
        }), 200
    except StateTransitionError as e:
        return jsonify({"error": "INVALID_TRANSITION", "message": str(e)}), 400

@officer_bp.route("/complaints/<int:complaint_id>/notes", methods=["POST"])
@login_required
@role_required(RoleEnum.FIELD_OFFICER.value, RoleEnum.DEPARTMENT_MANAGER.value, RoleEnum.SYSTEM_ADMIN.value)
def add_internal_note(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    data = request.get_json() or {}
    note = data.get("note", "").strip()

    if not note:
        return jsonify({"error": "VALIDATION_ERROR", "message": "Note content is required."}), 400

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    new_entry = f"[{timestamp} - {current_user.full_name} ({current_user.role})]: {note}\n"
    
    complaint.internal_notes = (complaint.internal_notes or "") + new_entry
    db.session.commit()

    return jsonify({"message": "Internal note appended.", "internal_notes": complaint.internal_notes}), 200
