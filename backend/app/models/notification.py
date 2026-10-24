from datetime import datetime, timezone
import enum
from app.extensions import db

class NotificationType(str, enum.Enum):
    STATUS_CHANGE = "STATUS_CHANGE"
    ASSIGNMENT = "ASSIGNMENT"
    SLA_WARNING = "SLA_WARNING"
    SLA_BREACH = "SLA_BREACH"
    REOPENED = "REOPENED"
    FEEDBACK_RECEIVED = "FEEDBACK_RECEIVED"
    INFO_REQUESTED = "INFO_REQUESTED"

class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey("complaints.id", ondelete="CASCADE"), nullable=True, index=True)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(40), default=NotificationType.STATUS_CHANGE.value, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    user = db.relationship("User", back_populates="notifications")
    complaint = db.relationship("Complaint")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "complaint_id": self.complaint_id,
            "complaint_reference_id": self.complaint.reference_id if self.complaint else None,
            "title": self.title,
            "message": self.message,
            "notification_type": self.notification_type,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
