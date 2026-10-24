from flask import Blueprint, request, jsonify, session
from flask_login import login_user, logout_user, current_user, login_required
from app.extensions import db, limiter
from app.models.user import User, RoleEnum
from app.models.department import Department
from app.models.audit import AuditEvent

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")

@auth_bp.route("/register", methods=["POST"])
@limiter.limit("10 per hour")
def register():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    full_name = data.get("full_name", "").strip()
    phone = data.get("phone", "").strip()

    if not email or not password or not full_name:
        return jsonify({"error": "VALIDATION_ERROR", "message": "Email, password, and full name are required."}), 400

    if len(password) < 8:
        return jsonify({"error": "VALIDATION_ERROR", "message": "Password must be at least 8 characters long."}), 400

    existing = User.query.filter_by(email=email).first()
    if existing:
        return jsonify({"error": "CONFLICT", "message": "An account with this email already exists."}), 409

    user = User(
        email=email,
        full_name=full_name,
        phone=phone or None,
        role=RoleEnum.CITIZEN.value,
        is_active=True,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    AuditEvent.log(action="USER_REGISTERED", entity_type="USER", entity_id=user.id, actor_id=user.id)
    db.session.commit()

    login_user(user, remember=True)
    return jsonify({
        "message": "Registration successful",
        "user": user.to_dict()
    }), 201

@auth_bp.route("/login", methods=["POST"])
@limiter.limit("20 per minute")
def login():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "VALIDATION_ERROR", "message": "Email and password are required."}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "UNAUTHORIZED", "message": "Invalid email or password."}), 401

    if not user.is_active:
        return jsonify({"error": "FORBIDDEN", "message": "Your account has been deactivated. Contact administration."}), 403

    login_user(user, remember=True)
    AuditEvent.log(action="USER_LOGIN", entity_type="USER", entity_id=user.id, actor_id=user.id)
    db.session.commit()

    return jsonify({
        "message": "Login successful",
        "user": user.to_dict()
    }), 200

@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    uid = current_user.id
    logout_user()
    AuditEvent.log(action="USER_LOGOUT", entity_type="USER", entity_id=uid, actor_id=uid)
    db.session.commit()
    return jsonify({"message": "Successfully logged out"}), 200

@auth_bp.route("/me", methods=["GET"])
def get_current_user():
    if not current_user.is_authenticated:
        return jsonify({"authenticated": False, "user": None}), 200
    return jsonify({"authenticated": True, "user": current_user.to_dict()}), 200

@auth_bp.route("/demo-accounts", methods=["GET"])
def get_demo_accounts():
    """
    Returns public synthetic demo credentials for evaluation.
    Documented for local/recruiter evaluation only.
    """
    return jsonify({
        "notice": "Development-only synthetic demo accounts. Do not use in production.",
        "accounts": [
            {
                "role": "Citizen",
                "email": "citizen@civicdispatch.org",
                "password": "Password123!",
                "description": "Report grievances, view timeline history, rate resolutions"
            },
            {
                "role": "Field Officer",
                "email": "officer@civicdispatch.org",
                "password": "Password123!",
                "department": "Public Works & Road Infrastructure",
                "description": "Mobile field queue, GPS verification, start work, upload resolution evidence"
            },
            {
                "role": "Department Manager",
                "email": "manager@civicdispatch.org",
                "password": "Password123!",
                "department": "Public Works & Road Infrastructure",
                "description": "Operations dashboard, assign tickets, manage SLA escalations, export CSV"
            },
            {
                "role": "System Administrator",
                "email": "admin@civicdispatch.org",
                "password": "Password123!",
                "description": "Full municipal command center, SLA policy editor, audit log viewer, user management"
            }
        ]
    }), 200
