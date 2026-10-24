"""
Civic Dispatch — Synthetic Seed Data Generator
Creates realistic departments, service zones, SLA policies, demo user accounts,
and sample municipal complaints for instant evaluator walkthrough.
"""

from datetime import datetime, timezone, timedelta
from app.extensions import db
from app.models.user import User, RoleEnum
from app.models.department import Department
from app.models.service_zone import ServiceZone
from app.models.sla import SLAPolicy, SLAEscalationEvent
from app.models.complaint import Complaint, ComplaintStatus, ComplaintPriority, ComplaintCategory, ComplaintAttachment, AttachmentType
from app.models.history import ComplaintStatusHistory, AssignmentHistory
from app.models.feedback import CitizenFeedback
from app.models.notification import Notification, NotificationType

def seed_database(reset: bool = False):
    """Populates database idempotently."""
    if reset:
        db.drop_all()
        db.create_all()
    else:
        db.create_all()

    # 1. Departments
    dept_specs = [
        {"name": "Public Works & Road Infrastructure", "code": "ROADS", "desc": "Potholes, paving, sidewalk, and bridge maintenance"},
        {"name": "Water Supply & Sewage Management", "code": "WATER", "desc": "Drinking water pipelines, sewer lines, and water contamination"},
        {"name": "Solid Waste & Sanitation", "code": "WASTE", "desc": "Garbage pickup, commercial waste dump clearance, and street sweeping"},
        {"name": "Electricity & Street Lighting", "code": "POWER", "desc": "Street lamps, power poles, loose high-voltage cables, and dark alleys"},
        {"name": "Stormwater Drainage & Flood Control", "code": "DRAIN", "desc": "Culvert desilting, storm runoff drains, and monsoon waterlogging"},
        {"name": "Public Health & Vector Control", "code": "HEALTH", "desc": "Pest control, dengue fogging, stagnant water treatment, and sanitation"},
    ]

    dept_map = {}
    for spec in dept_specs:
        dept = Department.query.filter_by(code=spec["code"]).first()
        if not dept:
            dept = Department(
                name=spec["name"],
                code=spec["code"],
                description=spec["desc"],
                contact_email=f"{spec['code'].lower()}@civicdispatch.org"
            )
            db.session.add(dept)
            db.session.flush()
        dept_map[spec["code"]] = dept

    # 2. Service Zones / Wards
    zone_specs = [
        {"name": "North Sector - Ward 1", "code": "WARD-N1", "lat": 12.9716, "lng": 77.5946, "dept": "ROADS"},
        {"name": "Central Core - Ward 2", "code": "WARD-C2", "lat": 12.9780, "lng": 77.6000, "dept": "ROADS"},
        {"name": "East Lake District - Ward 3", "code": "WARD-E3", "lat": 12.9650, "lng": 77.6150, "dept": "WATER"},
        {"name": "South Riverside - Ward 4", "code": "WARD-S4", "lat": 12.9550, "lng": 77.5850, "dept": "DRAIN"},
    ]

    zone_map = {}
    for zspec in zone_specs:
        zone = ServiceZone.query.filter_by(code=zspec["code"]).first()
        if not zone:
            zone = ServiceZone(
                name=zspec["name"],
                code=zspec["code"],
                department_id=dept_map[zspec["dept"]].id,
                center_lat=zspec["lat"],
                center_lng=zspec["lng"],
                radius_meters=2500.0,
                description=f"Municipal administrative service jurisdiction for {zspec['name']}"
            )
            db.session.add(zone)
            db.session.flush()
        zone_map[zspec["code"]] = zone

    # 3. SLA Policies
    sla_specs = [
        {"name": "Critical Hazard Emergency SLA", "cat": None, "pri": "CRITICAL", "hours": 12.0, "grace": 2.0},
        {"name": "High Priority Municipal Escalation", "cat": None, "pri": "HIGH", "hours": 24.0, "grace": 4.0},
        {"name": "Standard Road Infrastructure SLA", "cat": "ROAD_INFRASTRUCTURE", "pri": None, "hours": 48.0, "grace": 8.0},
        {"name": "Solid Waste Clearance Policy", "cat": "SOLID_WASTE", "pri": None, "hours": 36.0, "grace": 6.0},
        {"name": "Street Lighting Standard SLA", "cat": "STREET_LIGHTING", "pri": None, "hours": 72.0, "grace": 12.0},
    ]

    for sspec in sla_specs:
        policy = SLAPolicy.query.filter_by(name=sspec["name"]).first()
        if not policy:
            policy = SLAPolicy(
                name=sspec["name"],
                category=sspec["cat"],
                priority=sspec["pri"],
                duration_hours=sspec["hours"],
                grace_period_hours=sspec["grace"],
                is_active=True
            )
            db.session.add(policy)

    # 4. Demo Users (One per role)
    users_data = [
        {
            "email": "citizen@civicdispatch.org",
            "name": "Priya Sharma",
            "role": RoleEnum.CITIZEN.value,
            "dept": None,
            "phone": "+91 98765 43210"
        },
        {
            "email": "officer@civicdispatch.org",
            "name": "Rajesh Kumar",
            "role": RoleEnum.FIELD_OFFICER.value,
            "dept": "ROADS",
            "phone": "+91 98123 45678"
        },
        {
            "email": "manager@civicdispatch.org",
            "name": "Anita Desai",
            "role": RoleEnum.DEPARTMENT_MANAGER.value,
            "dept": "ROADS",
            "phone": "+91 98456 78901"
        },
        {
            "email": "admin@civicdispatch.org",
            "name": "Vikram Mehta",
            "role": RoleEnum.SYSTEM_ADMIN.value,
            "dept": None,
            "phone": "+91 99001 23456"
        },
    ]

    user_map = {}
    for u in users_data:
        usr = User.query.filter_by(email=u["email"]).first()
        if not usr:
            usr = User(
                email=u["email"],
                full_name=u["name"],
                role=u["role"],
                department_id=dept_map[u["dept"]].id if u["dept"] else None,
                phone=u["phone"],
                is_active=True
            )
            usr.set_password("Password123!")
            db.session.add(usr)
            db.session.flush()
        user_map[u["role"]] = usr

    # 5. Realistic Seed Complaints
    now = datetime.now(timezone.utc)
    roads_dept = dept_map["ROADS"]
    water_dept = dept_map["WATER"]
    power_dept = dept_map["POWER"]
    drain_dept = dept_map["DRAIN"]

    citizen_user = user_map[RoleEnum.CITIZEN.value]
    officer_user = user_map[RoleEnum.FIELD_OFFICER.value]

    if Complaint.query.count() == 0:
        complaint_samples = [
            # 1. RESOLVED with Feedback
            {
                "ref": "CD-2026-90412",
                "title": "Severe pothole cluster near Metro Pillar 142",
                "desc": "Multiple deep craters along the primary arterial road damaging two-wheelers and slowing rush-hour traffic.",
                "category": ComplaintCategory.ROAD_INFRASTRUCTURE.value,
                "priority": ComplaintPriority.HIGH.value,
                "status": ComplaintStatus.RESOLVED.value,
                "dept": roads_dept.id,
                "zone": zone_map["WARD-N1"].id,
                "officer": officer_user.id,
                "lat": 12.9716,
                "lng": 77.5946,
                "address": "Opposite Metro Pillar 142, Outer Ring Road",
                "created_at": now - timedelta(hours=36),
                "resolved_at": now - timedelta(hours=4),
                "deadline": now + timedelta(hours=12),
                "verified": True,
                "summary": "Cold-mix asphalt patch compacted and resurfaced over a 15-meter stretch. Traffic restored.",
                "feedback": {"rating": 5, "comments": "Prompt resolution within 24 hours. Well paved!"}
            },
            # 2. IN_PROGRESS
            {
                "ref": "CD-2026-81934",
                "title": "Broken storm water drain grating causing pedestrian hazard",
                "desc": "Cast iron drain grating collapsed inwards on pedestrian sidewalk; exposed 6ft drop.",
                "category": ComplaintCategory.DRAINAGE_FLOODING.value,
                "priority": ComplaintPriority.HIGH.value,
                "status": ComplaintStatus.IN_PROGRESS.value,
                "dept": drain_dept.id,
                "zone": zone_map["WARD-C2"].id,
                "officer": officer_user.id,
                "lat": 12.9780,
                "lng": 77.6000,
                "address": "4th Cross, Near Public Library",
                "created_at": now - timedelta(hours=18),
                "resolved_at": None,
                "deadline": now + timedelta(hours=6),
                "verified": True,
                "summary": None,
                "feedback": None
            },
            # 3. OVERDUE (Escalated to Level 2)
            {
                "ref": "CD-2026-72819",
                "title": "Water pipeline burst causing street flooding",
                "desc": "Fresh drinking water gushing onto roadway from main pipeline joint for over 48 hours.",
                "category": ComplaintCategory.WATER_SUPPLY.value,
                "priority": ComplaintPriority.CRITICAL.value,
                "status": ComplaintStatus.ASSIGNED.value,
                "dept": water_dept.id,
                "zone": zone_map["WARD-E3"].id,
                "officer": None,
                "lat": 12.9650,
                "lng": 77.6150,
                "address": "Behind St. Joseph High School",
                "created_at": now - timedelta(hours=30),
                "resolved_at": None,
                "deadline": now - timedelta(hours=6),  # Overdue!
                "verified": False,
                "summary": None,
                "feedback": None,
                "escalation_level": 2
            },
            # 4. SUBMITTED (New)
            {
                "ref": "CD-2026-64102",
                "title": "Three consecutive streetlights dark on 8th Main",
                "desc": "Entire stretch of 8th Main dark since Friday; unsafe for evening commuters.",
                "category": ComplaintCategory.STREET_LIGHTING.value,
                "priority": ComplaintPriority.MEDIUM.value,
                "status": ComplaintStatus.SUBMITTED.value,
                "dept": power_dept.id,
                "zone": zone_map["WARD-S4"].id,
                "officer": None,
                "lat": 12.9550,
                "lng": 77.5850,
                "address": "8th Main Road, Jayanagar 3rd Block",
                "created_at": now - timedelta(hours=3),
                "resolved_at": None,
                "deadline": now + timedelta(hours=69),
                "verified": False,
                "summary": None,
                "feedback": None
            },
        ]

        for s in complaint_samples:
            c = Complaint(
                reference_id=s["ref"],
                citizen_id=citizen_user.id,
                department_id=s["dept"],
                service_zone_id=s["zone"],
                assigned_officer_id=s["officer"],
                title=s["title"],
                description=s["desc"],
                category=s["category"],
                priority=s["priority"],
                status=s["status"],
                latitude=s["lat"],
                longitude=s["lng"],
                address=s["address"],
                created_at=s["created_at"],
                resolved_at=s["resolved_at"],
                sla_deadline=s["deadline"],
                sla_duration_hours=48.0,
                verified_location=s["verified"],
                resolution_summary=s["summary"],
                current_escalation_level=s.get("escalation_level", 0),
            )
            db.session.add(c)
            db.session.flush()

            # Status history
            h = ComplaintStatusHistory(
                complaint_id=c.id,
                previous_status=None,
                new_status=s["status"],
                acting_user_id=officer_user.id if s["officer"] else citizen_user.id,
                reason="Seed historical status record",
                created_at=s["created_at"]
            )
            db.session.add(h)

            # Feedback if present
            if s["feedback"]:
                fb = CitizenFeedback(
                    complaint_id=c.id,
                    citizen_id=citizen_user.id,
                    rating=s["feedback"]["rating"],
                    comments=s["feedback"]["comments"],
                    resolution_speed_rating=5,
                    officer_conduct_rating=5,
                    created_at=s["resolved_at"]
                )
                db.session.add(fb)

            # Escalation event if overdue
            if s.get("escalation_level", 0) >= 2:
                esc = SLAEscalationEvent(
                    complaint_id=c.id,
                    escalation_level=2,
                    trigger_type="OVERDUE_BREACH",
                    target_role=RoleEnum.DEPARTMENT_MANAGER.value,
                    notes="Automated SLA sweep detected resolution breach.",
                    created_at=s["deadline"]
                )
                db.session.add(esc)

    db.session.commit()
    print("Database seeding completed successfully.")
