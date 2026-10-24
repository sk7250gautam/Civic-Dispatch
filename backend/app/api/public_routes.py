from datetime import datetime, timezone
import statistics
from flask import Blueprint, request, jsonify
from app.models.complaint import Complaint, ComplaintStatus
from app.models.department import Department
from app.models.service_zone import ServiceZone

public_bp = Blueprint("public", __name__, url_prefix="/api/v1/public")

@public_bp.route("/statistics", methods=["GET"])
@public_bp.route("/stats", methods=["GET"])
def get_public_statistics():
    """
    Public municipal transparency metrics.
    Aggregates real figures directly from the database without disclosing personal data.
    """
    complaints = Complaint.query.all()
    total_count = len(complaints)

    if total_count == 0:
        return jsonify({
            "total_complaints": 0,
            "resolved_complaints": 0,
            "open_complaints": 0,
            "sla_compliance_rate": 100.0,
            "median_resolution_hours": 0.0,
            "category_distribution": {},
            "department_performance": [],
        }), 200

    resolved = [c for c in complaints if c.status in [ComplaintStatus.RESOLVED.value, ComplaintStatus.CLOSED.value]]
    open_complaints = [c for c in complaints if c.status not in [ComplaintStatus.RESOLVED.value, ComplaintStatus.CLOSED.value, ComplaintStatus.REJECTED.value]]

    # SLA Compliance
    resolved_with_deadlines = [c for c in resolved if c.resolved_at and c.sla_deadline]
    if resolved_with_deadlines:
        met_sla = sum(1 for c in resolved_with_deadlines if c.resolved_at <= c.sla_deadline)
        sla_compliance_rate = round((met_sla / len(resolved_with_deadlines)) * 100, 1)

        durations_hours = [
            (c.resolved_at.replace(tzinfo=timezone.utc if c.resolved_at.tzinfo is None else None) -
             c.created_at.replace(tzinfo=timezone.utc if c.created_at.tzinfo is None else None)).total_seconds() / 3600.0
            for c in resolved_with_deadlines
        ]
        median_resolution_hours = round(statistics.median(durations_hours), 1) if durations_hours else 0.0
    else:
        sla_compliance_rate = 100.0
        median_resolution_hours = 0.0

    # Category Distribution
    category_dist = {}
    for c in complaints:
        category_dist[c.category] = category_dist.get(c.category, 0) + 1

    # Department breakdown
    departments = Department.query.filter_by(is_active=True).all()
    dept_stats = []
    for d in departments:
        dept_complaints = [c for c in complaints if c.department_id == d.id]
        dept_total = len(dept_complaints)
        dept_resolved = sum(1 for c in dept_complaints if c.status in [ComplaintStatus.RESOLVED.value, ComplaintStatus.CLOSED.value])
        dept_stats.append({
            "name": d.name,
            "code": d.code,
            "total": dept_total,
            "resolved": dept_resolved,
            "resolution_rate": round((dept_resolved / dept_total * 100), 1) if dept_total > 0 else 0.0
        })

    return jsonify({
        "total_complaints": total_count,
        "resolved_complaints": len(resolved),
        "open_complaints": len(open_complaints),
        "sla_compliance_rate": sla_compliance_rate,
        "median_resolution_hours": median_resolution_hours,
        "category_distribution": category_dist,
        "department_performance": dept_stats,
    }), 200

@public_bp.route("/complaints/<string:reference_id>", methods=["GET"])
def track_by_reference_id(reference_id):
    """
    Public tracking by human-readable reference ID.
    Redacts personal identity, exact phone, address, and internal notes.
    """
    complaint = Complaint.query.filter_by(reference_id=reference_id.strip()).first_or_404()

    sanitized = {
        "reference_id": complaint.reference_id,
        "title": complaint.title,
        "category": complaint.category,
        "status": complaint.status,
        "priority": complaint.priority,
        "department_name": complaint.department.name if complaint.department else "Municipal Services",
        "created_at": complaint.created_at.isoformat() if complaint.created_at else None,
        "sla_deadline": complaint.sla_deadline.isoformat() if complaint.sla_deadline else None,
        "resolved_at": complaint.resolved_at.isoformat() if complaint.resolved_at else None,
        "resolution_summary": complaint.resolution_summary if complaint.status in [ComplaintStatus.RESOLVED.value, ComplaintStatus.CLOSED.value] else None,
        "timeline": [
            {
                "status": h.new_status,
                "timestamp": h.created_at.isoformat() if h.created_at else None,
                "reason": h.reason
            }
            for h in complaint.status_history
        ]
    }
    return jsonify({"complaint": sanitized}), 200

@public_bp.route("/map-clusters", methods=["GET"])
def get_public_map_markers():
    """
    Returns anonymized geospatial markers for public dashboard.
    Coordinates are rounded to protect citizen privacy.
    """
    complaints = Complaint.query.filter(
        Complaint.status.notin_([ComplaintStatus.REJECTED.value])
    ).all()

    markers = [
        {
            "id": c.id,
            "category": c.category,
            "status": c.status,
            "priority": c.priority,
            "lat": round(c.latitude, 3),
            "lng": round(c.longitude, 3),
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in complaints
    ]
    return jsonify({"markers": markers}), 200

@public_bp.route("/departments", methods=["GET"])
def list_departments():
    departments = Department.query.filter_by(is_active=True).all()
    zones = ServiceZone.query.all()
    return jsonify({
        "departments": [d.to_dict() for d in departments],
        "service_zones": [z.to_dict() for z in zones]
    }), 200
