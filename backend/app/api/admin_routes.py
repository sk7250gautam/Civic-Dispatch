from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.user import User, RoleEnum
from app.models.department import Department
from app.models.service_zone import ServiceZone
from app.models.complaint import Complaint
from app.models.sla import SLAPolicy, SLAEscalationEvent
from app.models.audit import AuditEvent
from app.security.rbac import role_required
from app.sla.engine import SLAEngine

admin_bp = Blueprint("admin", __name__, url_prefix="/api/v1/admin")

@admin_bp.route("/overview", methods=["GET"])
@login_required
@role_required(RoleEnum.SYSTEM_ADMIN.value)
def get_admin_overview():
    total_users = User.query.count()
    total_officers = User.query.filter_by(role=RoleEnum.FIELD_OFFICER.value).count()
    total_managers = User.query.filter_by(role=RoleEnum.DEPARTMENT_MANAGER.value).count()
    total_citizens = User.query.filter_by(role=RoleEnum.CITIZEN.value).count()
    
    total_departments = Department.query.count()
    total_zones = ServiceZone.query.count()
    total_complaints = Complaint.query.count()
    active_sla_policies = SLAPolicy.query.filter_by(is_active=True).count()
    total_escalations = SLAEscalationEvent.query.count()

    return jsonify({
        "users": {
            "total": total_users,
            "officers": total_officers,
            "managers": total_managers,
            "citizens": total_citizens,
        },
        "operations": {
            "departments": total_departments,
            "service_zones": total_zones,
            "complaints": total_complaints,
            "active_sla_policies": active_sla_policies,
            "total_escalations_logged": total_escalations,
        }
    }), 200

@admin_bp.route("/users", methods=["GET"])
@login_required
@role_required(RoleEnum.SYSTEM_ADMIN.value)
def list_users():
    role_filter = request.args.get("role")
    dept_filter = request.args.get("department_id", type=int)
    search = request.args.get("search", "").strip()

    query = User.query
    if role_filter:
        query = query.filter_by(role=role_filter)
    if dept_filter:
        query = query.filter_by(department_id=dept_filter)
    if search:
        query = query.filter(
            db.or_(
                User.full_name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
        )

    users = query.order_by(User.created_at.desc()).all()
    return jsonify({"users": [u.to_dict() for u in users]}), 200

@admin_bp.route("/users", methods=["POST"])
@login_required
@role_required(RoleEnum.SYSTEM_ADMIN.value)
def create_staff_user():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    full_name = data.get("full_name", "").strip()
    password = data.get("password", "")
    role = data.get("role", RoleEnum.FIELD_OFFICER.value)
    department_id = data.get("department_id")

    if not email or not full_name or not password:
        return jsonify({"error": "VALIDATION_ERROR", "message": "Email, full name, and password are required."}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "CONFLICT", "message": "Email already exists."}), 409

    user = User(
        email=email,
        full_name=full_name,
        role=role,
        department_id=department_id,
        is_active=True,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    AuditEvent.log(
        action="USER_CREATED_BY_ADMIN",
        entity_type="USER",
        entity_id=user.id,
        actor_id=current_user.id,
        details={"created_role": role, "email": email}
    )
    db.session.commit()

    return jsonify({"message": "User created successfully", "user": user.to_dict()}), 201

@admin_bp.route("/sla-policies", methods=["GET"])
@login_required
@role_required(RoleEnum.SYSTEM_ADMIN.value)
def list_sla_policies():
    policies = SLAPolicy.query.order_by(SLAPolicy.id.asc()).all()
    return jsonify({"policies": [p.to_dict() for p in policies]}), 200

@admin_bp.route("/sla-policies", methods=["POST"])
@login_required
@role_required(RoleEnum.SYSTEM_ADMIN.value)
def create_sla_policy():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    category = data.get("category")
    priority = data.get("priority")
    duration_hours = float(data.get("duration_hours", 48.0))
    grace_period_hours = float(data.get("grace_period_hours", 4.0))

    if not name:
        return jsonify({"error": "VALIDATION_ERROR", "message": "Policy name is required."}), 400

    policy = SLAPolicy(
        name=name,
        category=category or None,
        priority=priority or None,
        duration_hours=duration_hours,
        grace_period_hours=grace_period_hours,
        is_active=True,
    )
    db.session.add(policy)
    db.session.commit()

    AuditEvent.log(
        action="SLA_POLICY_CREATED",
        entity_type="SLA_POLICY",
        entity_id=policy.id,
        actor_id=current_user.id,
        details={"name": name, "duration_hours": duration_hours}
    )
    db.session.commit()

    return jsonify({"message": "SLA policy created", "policy": policy.to_dict()}), 201

@admin_bp.route("/audit-logs", methods=["GET"])
@login_required
@role_required(RoleEnum.SYSTEM_ADMIN.value)
def list_audit_logs():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 30, type=int), 100)
    action_filter = request.args.get("action")

    query = AuditEvent.query
    if action_filter:
        query = query.filter(AuditEvent.action.ilike(f"%{action_filter}%"))

    pagination = query.order_by(AuditEvent.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "audit_logs": [log.to_dict() for log in pagination.items],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total_items": pagination.total,
            "total_pages": pagination.pages,
        }
    }), 200

@admin_bp.route("/trigger-sla-check", methods=["POST"])
@login_required
@role_required(RoleEnum.SYSTEM_ADMIN.value)
def trigger_sla_check():
    """Manually triggers immediate SLA sweep and escalation."""
    stats = SLAEngine.run_evaluation()
    AuditEvent.log(
        action="SLA_SWEEP_TRIGGERED_MANUALLY",
        entity_type="SYSTEM",
        actor_id=current_user.id,
        details=stats
    )
    db.session.commit()
    return jsonify({
        "message": "SLA check completed successfully",
        "results": stats
    }), 200
