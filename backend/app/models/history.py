from datetime import datetime, timezone
import json
from app.extensions import db

class ComplaintStatusHistory(db.Model):
    __tablename__ = "complaint_status_history"

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True)
    previous_status = db.Column(db.String(30), nullable=True)
    new_status = db.Column(db.String(30), nullable=False)
    acting_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reason = db.Column(db.Text, nullable=True)
    metadata_json = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    complaint = db.relationship("Complaint", back_populates="status_history")
    acting_user = db.relationship("User", foreign_keys=[acting_user_id])

    def to_dict(self):
        meta = None
        if self.metadata_json:
            try:
                meta = json.loads(self.metadata_json)
            except Exception:
                meta = None

        return {
            "id": self.id,
            "complaint_id": self.complaint_id,
            "previous_status": self.previous_status,
            "new_status": self.new_status,
            "acting_user_id": self.acting_user_id,
            "acting_user_name": self.acting_user.full_name if self.acting_user else "System",
            "acting_user_role": self.acting_user.role if self.acting_user else "SYSTEM",
            "reason": self.reason,
            "metadata": meta,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

class AssignmentHistory(db.Model):
    __tablename__ = "assignment_history"

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True)
    previous_officer_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    new_officer_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assigned_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    complaint = db.relationship("Complaint", back_populates="assignment_history")
    previous_officer = db.relationship("User", foreign_keys=[previous_officer_id])
    new_officer = db.relationship("User", foreign_keys=[new_officer_id])
    assigned_by = db.relationship("User", foreign_keys=[assigned_by_id])

    def to_dict(self):
        return {
            "id": self.id,
            "complaint_id": self.complaint_id,
            "previous_officer_id": self.previous_officer_id,
            "previous_officer_name": self.previous_officer.full_name if self.previous_officer else "Unassigned",
            "new_officer_id": self.new_officer_id,
            "new_officer_name": self.new_officer.full_name if self.new_officer else "Unassigned",
            "assigned_by_id": self.assigned_by_id,
            "assigned_by_name": self.assigned_by.full_name if self.assigned_by else "System",
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
