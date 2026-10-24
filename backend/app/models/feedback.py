from datetime import datetime, timezone
from app.extensions import db

class CitizenFeedback(db.Model):
    __tablename__ = "citizen_feedback"

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey("complaints.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    citizen_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1 to 5
    comments = db.Column(db.Text, nullable=True)
    resolution_speed_rating = db.Column(db.Integer, nullable=True)
    officer_conduct_rating = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    complaint = db.relationship("Complaint", back_populates="feedback")
    citizen = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "complaint_id": self.complaint_id,
            "citizen_id": self.citizen_id,
            "rating": self.rating,
            "comments": self.comments,
            "resolution_speed_rating": self.resolution_speed_rating,
            "officer_conduct_rating": self.officer_conduct_rating,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
