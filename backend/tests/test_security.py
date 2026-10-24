def test_horizontal_privilege_isolation(client):
    # 1. Login as citizen 1
    r1 = client.post("/api/v1/auth/login", json={"email": "test_citizen@example.com", "password": "Password123!"})
    assert r1.status_code == 200

    # 2. Citizen 1 files a complaint
    create_res = client.post("/api/v1/citizens/complaints", json={
        "title": "Private Citizen Road Defect",
        "description": "Pothole directly in front of my gate",
        "category": "ROAD_INFRASTRUCTURE",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "address": "42 Rose Garden Lane"
    })
    assert create_res.status_code == 201
    c1_id = create_res.get_json()["complaint"]["id"]

    # 3. Citizen 1 can access their complaint
    res1 = client.get(f"/api/v1/citizens/complaints/{c1_id}")
    assert res1.status_code == 200
    assert res1.get_json()["complaint"]["title"] == "Private Citizen Road Defect"

    # 4. Citizen 1 logs out
    client.post("/api/v1/auth/logout")

    # 5. Citizen 2 logs in
    r2 = client.post("/api/v1/auth/login", json={"email": "other_citizen@example.com", "password": "Password123!"})
    assert r2.status_code == 200

    # 6. Citizen 2 attempts to access Citizen 1's complaint -> MUST BE BLOCKED (403 Forbidden)
    res2 = client.get(f"/api/v1/citizens/complaints/{c1_id}")
    assert res2.status_code == 403
    assert res2.get_json()["error"] == "FORBIDDEN"

def test_unauthenticated_request_blocked(client):
    res = client.get("/api/v1/citizens/complaints")
    assert res.status_code == 401

def test_citizen_cannot_access_manager_dashboard(citizen_client):
    res = citizen_client.get("/api/v1/managers/dashboard")
    assert res.status_code == 403
