from datetime import datetime, timezone
import enum
import random
import string
from app.extensions import db

class ComplaintStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REOPENED = "REOPENED"
    REJECTED = "REJECTED"

class ComplaintPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class ComplaintCategory(str, enum.Enum):
    ROAD_INFRASTRUCTURE = "ROAD_INFRASTRUCTURE"
    WATER_SUPPLY = "WATER_SUPPLY"
    SOLID_WASTE = "SOLID_WASTE"
    STREET_LIGHTING = "STREET_LIGHTING"
    HEALTH_SANITATION = "HEALTH_SANITATION"
    DRAINAGE_FLOODING = "DRAINAGE_FLOODING"
    OTHER = "OTHER"

class AttachmentType(str, enum.Enum):
    CITIZEN_SUBMISSION = "CITIZEN_SUBMISSION"
    BEFORE_EVIDENCE = "BEFORE_EVIDENCE"
    AFTER_EVIDENCE = "AFTER_EVIDENCE"

def generate_reference_id() -> str:
    year = datetime.now(timezone.utc).year
    random_str = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"CD-{year}-{random_str}"

class Complaint(db.Model):
    __tablename__ = "complaints"

    id = db.Column(db.Integer, primary_key=True)
    reference_id = db.Column(db.String(30), unique=True, nullable=False, default=generate_reference_id, index=True)
    
    # Ownership and Assignment
    citizen_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    service_zone_id = db.Column(db.Integer, db.ForeignKey("service_zones.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_officer_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Grievance Details
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False, default=ComplaintCategory.ROAD_INFRASTRUCTURE.value, index=True)
    priority = db.Column(db.String(20), nullable=False, default=ComplaintPriority.MEDIUM.value, index=True)
    status = db.Column(db.String(30), nullable=False, default=ComplaintStatus.SUBMITTED.value, index=True)
    
    # SLA & Escalation
    sla_policy_id = db.Column(db.Integer, db.ForeignKey("sla_policies.id", ondelete="SET NULL"), nullable=True)
    sla_duration_hours = db.Column(db.Float, default=48.0, nullable=False)
    sla_deadline = db.Column(db.DateTime, nullable=True, index=True)
    current_escalation_level = db.Column(db.Integer, default=0, nullable=False)  # 0: None, 1: Warning, 2: Manager, 3: Admin
    
    # Geospatial data
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(255), nullable=True)
    
    # Officer Verification
    verified_location = db.Column(db.Boolean, default=False, nullable=False)
    verified_at = db.Column(db.DateTime, nullable=True)
    officer_verification_lat = db.Column(db.Float, nullable=True)
    officer_verification_lng = db.Column(db.Float, nullable=True)
    verification_distance_meters = db.Column(db.Float, nullable=True)
    location_exception_reason = db.Column(db.String(255), nullable=True)
    
    # Resolution & Lifecycle
    resolution_summary = db.Column(db.Text, nullable=True)
    internal_notes = db.Column(db.Text, nullable=True)  # Authorized staff only
    reopen_reason = db.Column(db.Text, nullable=True)
    reopen_count = db.Column(db.Integer, default=0, nullable=False)
    resolved_at = db.Column(db.DateTime, nullable=True)
    closed_at = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    citizen = db.relationship("User", foreign_keys=[citizen_id], back_populates="filed_complaints")
    assigned_officer = db.relationship("User", foreign_keys=[assigned_officer_id], back_populates="assigned_complaints")
    department = db.relationship("Department", back_populates="complaints")
    service_zone = db.relationship("ServiceZone", back_populates="complaints")
    sla_policy = db.relationship("SLAPolicy", back_populates="complaints")
    
    attachments = db.relationship("ComplaintAttachment", back_populates="complaint", cascade="all, delete-orphan")
    status_history = db.relationship("ComplaintStatusHistory", back_populates="complaint", cascade="all, delete-orphan", order_by="desc(ComplaintStatusHistory.created_at)")
    assignment_history = db.relationship("AssignmentHistory", back_populates="complaint", cascade="all, delete-orphan", order_by="desc(AssignmentHistory.created_at)")
    escalation_events = db.relationship("SLAEscalationEvent", back_populates="complaint", cascade="all, delete-orphan")
    feedback = db.relationship("CitizenFeedback", back_populates="complaint", uselist=False, cascade="all, delete-orphan")
    ai_suggestions = db.relationship("AISuggestion", back_populates="complaint", cascade="all, delete-orphan")

    def is_overdue(self) -> bool:
        if self.status in [ComplaintStatus.RESOLVED.value, ComplaintStatus.CLOSED.value, ComplaintStatus.REJECTED.value]:
            return False
        if not self.sla_deadline:
            return False
        return datetime.now(timezone.utc) > self.sla_deadline.replace(tzinfo=timezone.utc if self.sla_deadline.tzinfo is None else None)

    def to_dict(self, role: str = "CITIZEN", viewer_user_id: int = None):
        """Serialize complaint with strict role-based data isolation."""
        is_owner = viewer_user_id == self.citizen_id
        is_staff = role in ["FIELD_OFFICER", "DEPARTMENT_MANAGER", "SYSTEM_ADMIN"]

        data = {
            "id": self.id,
            "reference_id": self.reference_id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "priority": self.priority,
            "status": self.status,
            "current_escalation_level": self.current_escalation_level,
            "sla_deadline": self.sla_deadline.isoformat() if self.sla_deadline else None,
            "sla_duration_hours": self.sla_duration_hours,
            "is_overdue": self.is_overdue(),
            "department_id": self.department_id,
            "department_name": self.department.name if self.department else None,
            "service_zone_id": self.service_zone_id,
            "service_zone_name": self.service_zone.name if self.service_zone else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "resolution_summary": self.resolution_summary,
            "verified_location": self.verified_location,
            "reopen_count": self.reopen_count,
        }

        # Geospatial & Address Privacy
        if is_owner or is_staff:
            data["latitude"] = self.latitude
            data["longitude"] = self.longitude
            data["address"] = self.address
        else:
            # Anonymized / fuzzed coordinates for public views
            data["latitude"] = round(self.latitude, 2)
            data["longitude"] = round(self.longitude, 2)
            data["address"] = "Public Civic Area"

        # Staff-Only Fields
        if is_staff:
            data["assigned_officer_id"] = self.assigned_officer_id
            data["assigned_officer_name"] = self.assigned_officer.full_name if self.assigned_officer else None
            data["internal_notes"] = self.internal_notes
            data["officer_verification_lat"] = self.officer_verification_lat
            data["officer_verification_lng"] = self.officer_verification_lng
            data["verification_distance_meters"] = self.verification_distance_meters
            data["location_exception_reason"] = self.location_exception_reason
        elif is_owner:
            data["assigned_officer_name"] = self.assigned_officer.full_name if self.assigned_officer else "Pending Assignment"

        # Attachments
        data["attachments"] = [
            att.to_dict() for att in self.attachments
            if is_staff or is_owner or att.attachment_type in [AttachmentType.BEFORE_EVIDENCE.value, AttachmentType.AFTER_EVIDENCE.value]
        ]

        # Citizen feedback
        if self.feedback:
            data["feedback"] = self.feedback.to_dict()

        return data

    def __repr__(self):
        return f"<Complaint {self.reference_id} [{self.status}]>"

class ComplaintAttachment(db.Model):
    __tablename__ = "complaint_attachments"

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True)
    uploader_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    file_path = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    attachment_type = db.Column(db.String(30), nullable=False, default=AttachmentType.CITIZEN_SUBMISSION.value)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    complaint = db.relationship("Complaint", back_populates="attachments")
    uploader = db.relationship("User", foreign_keys=[uploader_id])

    def to_dict(self):
        return {
            "id": self.id,
            "complaint_id": self.complaint_id,
            "filename": self.original_filename,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "attachment_type": self.attachment_type,
            "url": f"/api/v1/attachments/{self.id}/download",
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
