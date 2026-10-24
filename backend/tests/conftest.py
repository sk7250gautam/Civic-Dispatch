import pytest
from app import create_app
from app.extensions import db
from app.models.user import User, RoleEnum
from app.models.department import Department
from app.models.service_zone import ServiceZone
from app.models.sla import SLAPolicy

@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        
        # Create base test department & zone
        dept = Department(name="Road Works", code="ROADS", description="Test Department")
        db.session.add(dept)
        db.session.flush()

        zone = ServiceZone(name="Central Zone", code="ZONE-1", department_id=dept.id, center_lat=12.97, center_lng=77.59)
        db.session.add(zone)

        # Create base SLA policy
        policy = SLAPolicy(name="Standard Test SLA", duration_hours=24.0, grace_period_hours=2.0, is_active=True)
        db.session.add(policy)

        # Create test users for each role
        citizen = User(email="test_citizen@example.com", full_name="Test Citizen", role=RoleEnum.CITIZEN.value)
        citizen.set_password("Password123!")
        db.session.add(citizen)

        citizen2 = User(email="other_citizen@example.com", full_name="Other Citizen", role=RoleEnum.CITIZEN.value)
        citizen2.set_password("Password123!")
        db.session.add(citizen2)

        officer = User(email="test_officer@example.com", full_name="Test Officer", role=RoleEnum.FIELD_OFFICER.value, department_id=dept.id)
        officer.set_password("Password123!")
        db.session.add(officer)

        manager = User(email="test_manager@example.com", full_name="Test Manager", role=RoleEnum.DEPARTMENT_MANAGER.value, department_id=dept.id)
        manager.set_password("Password123!")
        db.session.add(manager)

        admin = User(email="test_admin@example.com", full_name="Test Admin", role=RoleEnum.SYSTEM_ADMIN.value)
        admin.set_password("Password123!")
        db.session.add(admin)

        db.session.commit()
        yield app

        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def citizen_client(app):
    cl = app.test_client()
    res = cl.post("/api/v1/auth/login", json={"email": "test_citizen@example.com", "password": "Password123!"})
    assert res.status_code == 200
    return cl

@pytest.fixture
def other_citizen_client(app):
    cl = app.test_client()
    res = cl.post("/api/v1/auth/login", json={"email": "other_citizen@example.com", "password": "Password123!"})
    assert res.status_code == 200
    return cl

@pytest.fixture
def officer_client(app):
    cl = app.test_client()
    res = cl.post("/api/v1/auth/login", json={"email": "test_officer@example.com", "password": "Password123!"})
    assert res.status_code == 200
    return cl

@pytest.fixture
def manager_client(app):
    cl = app.test_client()
    res = cl.post("/api/v1/auth/login", json={"email": "test_manager@example.com", "password": "Password123!"})
    assert res.status_code == 200
    return cl

@pytest.fixture
def admin_client(app):
    cl = app.test_client()
    res = cl.post("/api/v1/auth/login", json={"email": "test_admin@example.com", "password": "Password123!"})
    assert res.status_code == 200
    return cl
