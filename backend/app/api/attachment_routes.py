from flask import Blueprint, send_from_directory, current_app, jsonify, request
from flask_login import login_required, current_user
from app.models.complaint import ComplaintAttachment, AttachmentType
from app.security.rbac import verify_complaint_access

attachment_bp = Blueprint("attachments", __name__, url_prefix="/api/v1/attachments")

@attachment_bp.route("/<int:attachment_id>/download", methods=["GET"])
def download_attachment(attachment_id):
    attachment = ComplaintAttachment.query.get_or_404(attachment_id)
    complaint = attachment.complaint

    # Public before/after evidence can be viewed freely if not private submission
    if attachment.attachment_type == AttachmentType.CITIZEN_SUBMISSION.value:
        if not current_user.is_authenticated or not verify_complaint_access(complaint, current_user):
            return jsonify({"error": "FORBIDDEN", "message": "Access restricted to authorized stakeholders."}), 403

    upload_dir = current_app.config.get("UPLOAD_FOLDER", "uploads")
    as_attachment = request.args.get("download", "").lower() == "true"

    return send_from_directory(
        upload_dir,
        attachment.file_path,
        as_attachment=as_attachment,
        download_name=attachment.original_filename
    )
