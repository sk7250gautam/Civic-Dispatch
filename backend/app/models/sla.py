from datetime import datetime, timezone
from app.extensions import db

class SLAPolicy(db.Model):
    __tablename__ = "sla_policies"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    category = db.Column(db.String(50), nullable=True, index=True)
    priority = db.Column(db.String(20), nullable=True, index=True)
    duration_hours = db.Column(db.Float, nullable=False, default=48.0)
    grace_period_hours = db.Column(db.Float, nullable=False, default=4.0)
    warning_threshold_percent = db.Column(db.Float, default=75.0, nullable=False)  # Warn when 75% time elapsed
    escalation_target_role = db.Column(db.String(30), default="DEPARTMENT_MANAGER", nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    complaints = db.relationship("Complaint", back_populates="sla_policy")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "priority": self.priority,
            "duration_hours": self.duration_hours,
            "grace_period_hours": self.grace_period_hours,
            "warning_threshold_percent": self.warning_threshold_percent,
            "escalation_target_role": self.escalation_target_role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<SLAPolicy {self.name} ({self.duration_hours}h)>"

class SLAEscalationEvent(db.Model):
    __tablename__ = "sla_escalation_events"

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True)
    escalation_level = db.Column(db.Integer, nullable=False)  # 1: Warning, 2: Manager, 3: Admin
    trigger_type = db.Column(db.String(40), nullable=False)   # WARNING_THRESHOLD, OVERDUE, MANUAL
    target_role = db.Column(db.String(30), nullable=False)
    escalated_to_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    complaint = db.relationship("Complaint", back_populates="escalation_events")
    escalated_to = db.relationship("User", foreign_keys=[escalated_to_id])

    def to_dict(self):
        return {
            "id": self.id,
            "complaint_id": self.complaint_id,
            "escalation_level": self.escalation_level,
            "trigger_type": self.trigger_type,
            "target_role": self.target_role,
            "escalated_to_id": self.escalated_to_id,
            "escalated_to_name": self.escalated_to.full_name if self.escalated_to else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
