def test_register_citizen_success(client):
    res = client.post("/api/v1/auth/register", json={
        "email": "newuser@example.com",
        "password": "Password123!",
        "full_name": "New User",
        "phone": "+91 99999 88888"
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data["user"]["email"] == "newuser@example.com"
    assert data["user"]["role"] == "CITIZEN"

def test_login_invalid_credentials(client):
    res = client.post("/api/v1/auth/login", json={
        "email": "test_citizen@example.com",
        "password": "WrongPassword!"
    })
    assert res.status_code == 401

def test_demo_accounts_endpoint(client):
    res = client.get("/api/v1/auth/demo-accounts")
    assert res.status_code == 200
    data = res.get_json()
    assert len(data["accounts"]) == 4
    roles = [acc["role"] for acc in data["accounts"]]
    assert "Citizen" in roles
    assert "Field Officer" in roles
    assert "Department Manager" in roles
    assert "System Administrator" in roles
