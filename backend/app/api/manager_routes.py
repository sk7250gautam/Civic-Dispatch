import io
import csv
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, Response
from flask_login import login_required, current_user
from app.extensions import db
from app.models.complaint import Complaint, ComplaintStatus, ComplaintPriority
from app.models.history import AssignmentHistory
from app.models.user import User, RoleEnum
from app.models.notification import Notification, NotificationType
from app.models.audit import AuditEvent
from app.state_machine.transitions import ComplaintStateMachine, StateTransitionError
from app.security.rbac import role_required

manager_bp = Blueprint("managers", __name__, url_prefix="/api/v1/managers")

@manager_bp.route("/dashboard", methods=["GET"])
@login_required
@role_required(RoleEnum.DEPARTMENT_MANAGER.value, RoleEnum.SYSTEM_ADMIN.value)
def get_manager_dashboard():
    """
    Computes real-time operational metrics for the department command center.
    Never uses simulated numbers; aggregates directly from the database.
    """
    dept_id = current_user.department_id
    query = Complaint.query
    if dept_id and current_user.role != RoleEnum.SYSTEM_ADMIN.value:
        query = query.filter_by(department_id=dept_id)

    complaints = query.all()
    now = datetime.now(timezone.utc)

    total_count = len(complaints)
    submitted_count = sum(1 for c in complaints if c.status == ComplaintStatus.SUBMITTED.value)
    acknowledged_count = sum(1 for c in complaints if c.status == ComplaintStatus.ACKNOWLEDGED.value)
    assigned_count = sum(1 for c in complaints if c.status == ComplaintStatus.ASSIGNED.value)
    in_progress_count = sum(1 for c in complaints if c.status == ComplaintStatus.IN_PROGRESS.value)
    resolved_count = sum(1 for c in complaints if c.status in [ComplaintStatus.RESOLVED.value, ComplaintStatus.CLOSED.value])
    rejected_count = sum(1 for c in complaints if c.status == ComplaintStatus.REJECTED.value)
    
    # Overdue calculation
    overdue_count = sum(1 for c in complaints if c.is_overdue())

    # SLA Compliance Calculation
    resolved_tickets = [c for c in complaints if c.resolved_at and c.sla_deadline]
    if resolved_tickets:
        on_time_count = sum(1 for c in resolved_tickets if c.resolved_at <= c.sla_deadline)
        sla_compliance_rate = round((on_time_count / len(resolved_tickets)) * 100, 1)
        
        # Average resolution time in hours
        total_hours = sum(
            (c.resolved_at.replace(tzinfo=timezone.utc if c.resolved_at.tzinfo is None else None) -
             c.created_at.replace(tzinfo=timezone.utc if c.created_at.tzinfo is None else None)).total_seconds() / 3600.0
            for c in resolved_tickets
        )
        avg_resolution_hours = round(total_hours / len(resolved_tickets), 1)
    else:
        sla_compliance_rate = 100.0
        avg_resolution_hours = 0.0

    # Category breakdown
    category_counts = {}
    for c in complaints:
        category_counts[c.category] = category_counts.get(c.category, 0) + 1

    # Priority breakdown
    priority_counts = {}
    for c in complaints:
        priority_counts[c.priority] = priority_counts.get(c.priority, 0) + 1

    # Escalation levels
    escalation_counts = {
        "normal": sum(1 for c in complaints if c.current_escalation_level == 0),
        "warning_tier_1": sum(1 for c in complaints if c.current_escalation_level == 1),
        "overdue_tier_2": sum(1 for c in complaints if c.current_escalation_level == 2),
        "critical_tier_3": sum(1 for c in complaints if c.current_escalation_level == 3),
    }

    return jsonify({
        "metrics": {
            "total_complaints": total_count,
            "open_complaints": submitted_count + acknowledged_count + assigned_count + in_progress_count,
            "submitted": submitted_count,
            "acknowledged": acknowledged_count,
            "assigned": assigned_count,
            "in_progress": in_progress_count,
            "resolved": resolved_count,
            "rejected": rejected_count,
            "overdue": overdue_count,
            "sla_compliance_rate": sla_compliance_rate,
            "avg_resolution_hours": avg_resolution_hours,
        },
        "breakdown": {
            "by_category": category_counts,
            "by_priority": priority_counts,
            "by_escalation": escalation_counts,
        }
    }), 200

@manager_bp.route("/complaints", methods=["GET"])
@login_required
@role_required(RoleEnum.DEPARTMENT_MANAGER.value, RoleEnum.SYSTEM_ADMIN.value)
def list_department_complaints():
    dept_id = current_user.department_id
    query = Complaint.query
    if dept_id and current_user.role != RoleEnum.SYSTEM_ADMIN.value:
        query = query.filter_by(department_id=dept_id)

    status_filter = request.args.get("status")
    priority_filter = request.args.get("priority")
    category_filter = request.args.get("category")
    officer_id_filter = request.args.get("officer_id", type=int)
    escalated_only = request.args.get("escalated_only", "").lower() == "true"
    search_term = request.args.get("search", "").strip()

    if status_filter:
        query = query.filter_by(status=status_filter)
    if priority_filter:
        query = query.filter_by(priority=priority_filter)
    if category_filter:
        query = query.filter_by(category=category_filter)
    if officer_id_filter:
        query = query.filter_by(assigned_officer_id=officer_id_filter)
    if escalated_only:
        query = query.filter(Complaint.current_escalation_level > 0)
    if search_term:
        query = query.filter(
            db.or_(
                Complaint.reference_id.ilike(f"%{search_term}%"),
                Complaint.title.ilike(f"%{search_term}%"),
                Complaint.description.ilike(f"%{search_term}%"),
                Complaint.address.ilike(f"%{search_term}%")
            )
        )

    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)

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

@manager_bp.route("/complaints/<int:complaint_id>/assign", methods=["POST"])
@login_required
@role_required(RoleEnum.DEPARTMENT_MANAGER.value, RoleEnum.SYSTEM_ADMIN.value)
def assign_officer(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)

    if current_user.role != RoleEnum.SYSTEM_ADMIN.value and complaint.department_id != current_user.department_id:
        return jsonify({"error": "FORBIDDEN", "message": "You can only assign tickets in your department."}), 403

    data = request.get_json() or {}
    officer_id = data.get("officer_id")
    notes = data.get("notes", "").strip()

    if not officer_id:
        return jsonify({"error": "VALIDATION_ERROR", "message": "An officer ID is required."}), 400

    officer = User.query.get(officer_id)
    if not officer or officer.role != RoleEnum.FIELD_OFFICER.value or not officer.is_active:
        return jsonify({"error": "VALIDATION_ERROR", "message": "Target user must be an active field officer."}), 400

    prev_officer_id = complaint.assigned_officer_id
    complaint.assigned_officer_id = officer.id

    # Record Assignment History
    history = AssignmentHistory(
        complaint_id=complaint.id,
        previous_officer_id=prev_officer_id,
        new_officer_id=officer.id,
        assigned_by_id=current_user.id,
        notes=notes or None,
    )
    db.session.add(history)

    # Transition state to ASSIGNED if currently SUBMITTED or ACKNOWLEDGED
    if complaint.status in [ComplaintStatus.SUBMITTED.value, ComplaintStatus.ACKNOWLEDGED.value, ComplaintStatus.REOPENED.value]:
        try:
            ComplaintStateMachine.transition(
                complaint=complaint,
                new_status=ComplaintStatus.ASSIGNED.value,
                user=current_user,
                reason=f"Assigned to {officer.full_name}. Notes: {notes or 'None'}"
            )
        except Exception:
            pass

    # Notify Assigned Officer
    notif = Notification(
        user_id=officer.id,
        complaint_id=complaint.id,
        title=f"New Grievance Assigned: {complaint.reference_id}",
        message=f"You have been assigned ticket '{complaint.title}' ({complaint.priority} priority).",
        notification_type=NotificationType.ASSIGNMENT.value,
    )
    db.session.add(notif)
    db.session.commit()

    return jsonify({
        "message": f"Successfully assigned to {officer.full_name}",
        "complaint": complaint.to_dict(role=current_user.role, viewer_user_id=current_user.id)
    }), 200

@manager_bp.route("/complaints/<int:complaint_id>/reject", methods=["POST"])
@login_required
@role_required(RoleEnum.DEPARTMENT_MANAGER.value, RoleEnum.SYSTEM_ADMIN.value)
def reject_complaint(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    data = request.get_json() or {}
    reason = data.get("reason", "").strip()

    if not reason:
        return jsonify({"error": "VALIDATION_ERROR", "message": "A formal rejection justification is required."}), 400

    try:
        ComplaintStateMachine.transition(
            complaint=complaint,
            new_status=ComplaintStatus.REJECTED.value,
            user=current_user,
            reason=reason
        )
        return jsonify({
            "message": "Grievance marked as rejected.",
            "complaint": complaint.to_dict(role=current_user.role, viewer_user_id=current_user.id)
        }), 200
    except StateTransitionError as e:
        return jsonify({"error": "INVALID_TRANSITION", "message": str(e)}), 400

@manager_bp.route("/officers", methods=["GET"])
@login_required
@role_required(RoleEnum.DEPARTMENT_MANAGER.value, RoleEnum.SYSTEM_ADMIN.value)
def list_department_officers():
    """Lists field officers in manager's department with current active workload counts."""
    dept_id = current_user.department_id
    query = User.query.filter_by(role=RoleEnum.FIELD_OFFICER.value, is_active=True)
    if dept_id and current_user.role != RoleEnum.SYSTEM_ADMIN.value:
        query = query.filter_by(department_id=dept_id)

    officers = query.all()
    results = []
    active_statuses = [ComplaintStatus.ASSIGNED.value, ComplaintStatus.IN_PROGRESS.value, ComplaintStatus.ACKNOWLEDGED.value]

    for off in officers:
        active_load = Complaint.query.filter(
            Complaint.assigned_officer_id == off.id,
            Complaint.status.in_(active_statuses)
        ).count()

        results.append({
            "id": off.id,
            "full_name": off.full_name,
            "email": off.email,
            "phone": off.phone,
            "department_id": off.department_id,
            "active_ticket_count": active_load,
        })

    # Sort by lightest workload first for load balancing
    results.sort(key=lambda x: x["active_ticket_count"])
    return jsonify({"officers": results}), 200

@manager_bp.route("/export", methods=["GET"])
@login_required
@role_required(RoleEnum.DEPARTMENT_MANAGER.value, RoleEnum.SYSTEM_ADMIN.value)
def export_csv():
    dept_id = current_user.department_id
    query = Complaint.query
    if dept_id and current_user.role != RoleEnum.SYSTEM_ADMIN.value:
        query = query.filter_by(department_id=dept_id)

    complaints = query.order_by(Complaint.created_at.desc()).limit(1000).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Reference ID", "Title", "Category", "Priority", "Status",
        "Escalation Level", "Assigned Officer", "Latitude", "Longitude",
        "SLA Deadline", "Created At", "Resolved At"
    ])

    for c in complaints:
        writer.writerow([
            c.reference_id,
            c.title,
            c.category,
            c.priority,
            c.status,
            c.current_escalation_level,
            c.assigned_officer.full_name if c.assigned_officer else "Unassigned",
            c.latitude,
            c.longitude,
            c.sla_deadline.isoformat() if c.sla_deadline else "",
            c.created_at.isoformat() if c.created_at else "",
            c.resolved_at.isoformat() if c.resolved_at else ""
        ])

    csv_data = output.getvalue()
    filename = f"civic_dispatch_export_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )
