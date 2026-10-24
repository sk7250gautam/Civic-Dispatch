from datetime import datetime, timezone, timedelta
from app.models.complaint import Complaint, ComplaintStatus, ComplaintPriority
from app.models.user import User, RoleEnum
from app.sla.calculator import calculate_sla_deadline
from app.sla.engine import SLAEngine

def test_sla_deadline_calculation():
    # Critical should result in <= 12 hours
    deadline, duration, policy_id = calculate_sla_deadline("ROAD_INFRASTRUCTURE", "CRITICAL")
    assert duration <= 12.0

    # Low priority should be >= 48 hours
    deadline_low, duration_low, _ = calculate_sla_deadline("STREET_LIGHTING", "LOW")
    assert duration_low >= 48.0

def test_sla_escalation_detection(app):
    with app.app_context():
        citizen = User.query.filter_by(role=RoleEnum.CITIZEN.value).first()
        from app.extensions import db

        now = datetime.now(timezone.utc)
        # Create complaint that has breached deadline
        overdue_complaint = Complaint(
            citizen_id=citizen.id,
            title="Burst main pipe",
            description="Water gushing onto road",
            latitude=12.97,
            longitude=77.59,
            status=ComplaintStatus.ASSIGNED.value,
            created_at=now - timedelta(hours=30),
            sla_deadline=now - timedelta(hours=6),
            current_escalation_level=0,
        )
        db.session.add(overdue_complaint)
        db.session.commit()

        stats = SLAEngine.run_evaluation()
        assert stats["level_2_breaches"] >= 1

        # Reload complaint
        db.session.refresh(overdue_complaint)
        assert overdue_complaint.current_escalation_level == 2

        # Running again should be idempotent (no duplicate tier 2 breaches)
        stats2 = SLAEngine.run_evaluation()
        assert stats2["level_2_breaches"] == 0
