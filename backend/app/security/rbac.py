"""
Civic Dispatch — Role-Based Access Control & Horizontal Isolation Decorators
Prevents horizontal privilege escalation and enforces strict departmental boundaries.
"""

from functools import wraps
from flask import jsonify, request, g
from flask_login import current_user
from app.models.complaint import Complaint
from app.models.user import RoleEnum

def role_required(*allowed_roles):
    """Decorator requiring the logged-in user to have one of the specified roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({"error": "UNAUTHORIZED", "message": "Authentication required"}), 401
            
            if current_user.role not in allowed_roles:
                return jsonify({
                    "error": "FORBIDDEN",
                    "message": f"Action restricted to roles: {', '.join(allowed_roles)}. Your role: {current_user.role}"
                }), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator

def verify_complaint_access(complaint: Complaint, user) -> bool:
    """
    Validates whether the user is authorized to view or interact with this specific complaint.
    Prevents horizontal privilege escalation.
    """
    if not user or not user.is_authenticated:
        return False

    if user.role == RoleEnum.SYSTEM_ADMIN.value:
        return True

    if user.role == RoleEnum.CITIZEN.value:
        return complaint.citizen_id == user.id

    if user.role == RoleEnum.FIELD_OFFICER.value:
        # Officer can access tickets assigned to them or within their department queue
        if complaint.assigned_officer_id == user.id:
            return True
        if user.department_id and complaint.department_id == user.department_id:
            return True
        return False

    if user.role == RoleEnum.DEPARTMENT_MANAGER.value:
        # Manager can only access tickets within their authorized department
        return user.department_id is None or complaint.department_id == user.department_id

    return False
