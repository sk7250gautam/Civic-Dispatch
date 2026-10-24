from datetime import datetime, timezone
import json
from app.extensions import db

class ServiceZone(db.Model):
    __tablename__ = "service_zones"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    code = db.Column(db.String(30), unique=True, nullable=False, index=True)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    boundary_geojson = db.Column(db.Text, nullable=True)  # JSON representation of Polygon/MultiPolygon
    center_lat = db.Column(db.Float, nullable=True)
    center_lng = db.Column(db.Float, nullable=True)
    radius_meters = db.Column(db.Float, default=2000.0)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    department = db.relationship("Department", back_populates="service_zones")
    complaints = db.relationship("Complaint", back_populates="service_zone")

    def to_dict(self):
        geojson_data = None
        if self.boundary_geojson:
            try:
                geojson_data = json.loads(self.boundary_geojson)
            except Exception:
                geojson_data = None
                
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "department_id": self.department_id,
            "boundary_geojson": geojson_data,
            "center_lat": self.center_lat,
            "center_lng": self.center_lng,
            "radius_meters": self.radius_meters,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<ServiceZone {self.code} - {self.name}>"
