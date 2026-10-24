from datetime import datetime, timezone
import json
from app.extensions import db

class AuditEvent(db.Model):
    __tablename__ = "audit_events"

    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = db.Column(db.String(100), nullable=False, index=True)
    entity_type = db.Column(db.String(50), nullable=False, index=True)
    entity_id = db.Column(db.Integer, nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    details_json = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    actor = db.relationship("User", foreign_keys=[actor_id])

    @staticmethod
    def log(action: str, entity_type: str, entity_id: int = None, actor_id: int = None, ip_address: str = None, details: dict = None):
        details_str = json.dumps(details) if details else None
        event = AuditEvent(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_id=actor_id,
            ip_address=ip_address,
            details_json=details_str
        )
        db.session.add(event)
        return event

    def to_dict(self):
        details = None
        if self.details_json:
            try:
                details = json.loads(self.details_json)
            except Exception:
                details = None

        return {
            "id": self.id,
            "actor_id": self.actor_id,
            "actor_name": self.actor.full_name if self.actor else "System",
            "actor_role": self.actor.role if self.actor else "SYSTEM",
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "ip_address": self.ip_address,
            "details": details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
