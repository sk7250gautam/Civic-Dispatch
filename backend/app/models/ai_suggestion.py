from datetime import datetime, timezone
from app.extensions import db

class AISuggestion(db.Model):
    __tablename__ = "ai_suggestions"

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey("complaints.id", ondelete="CASCADE"), nullable=True, index=True)
    suggestion_type = db.Column(db.String(50), nullable=False)  # CATEGORIZATION, PRIORITY, DUPLICATE_CHECK, SUMMARY
    model_name = db.Column(db.String(50), nullable=False)
    suggested_value = db.Column(db.Text, nullable=False)
    confidence = db.Column(db.Float, nullable=True)
    was_accepted = db.Column(db.Boolean, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    complaint = db.relationship("Complaint", back_populates="ai_suggestions")

    def to_dict(self):
        return {
            "id": self.id,
            "complaint_id": self.complaint_id,
            "suggestion_type": self.suggestion_type,
            "model_name": self.model_name,
            "suggested_value": self.suggested_value,
            "confidence": self.confidence,
            "was_accepted": self.was_accepted,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
