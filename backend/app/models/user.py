from datetime import datetime, timezone
import enum
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.extensions import db

class RoleEnum(str, enum.Enum):
    CITIZEN = "CITIZEN"
    FIELD_OFFICER = "FIELD_OFFICER"
    DEPARTMENT_MANAGER = "DEPARTMENT_MANAGER"
    SYSTEM_ADMIN = "SYSTEM_ADMIN"

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(25), nullable=True)
    role = db.Column(db.String(30), nullable=False, default=RoleEnum.CITIZEN.value, index=True)
    
    # Department assignment (for field officers and department managers)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    department = db.relationship("Department", back_populates="users", foreign_keys=[department_id])
    assigned_complaints = db.relationship("Complaint", back_populates="assigned_officer", foreign_keys="Complaint.assigned_officer_id")
    filed_complaints = db.relationship("Complaint", back_populates="citizen", foreign_keys="Complaint.citizen_id")
    notifications = db.relationship("Notification", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self, include_sensitive: bool = False):
        data = {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "phone": self.phone,
            "role": self.role,
            "department_id": self.department_id,
            "department_name": self.department.name if self.department else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        return data

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
