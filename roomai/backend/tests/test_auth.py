"""Auth endpoint tests."""


def test_signup_returns_token_and_three_credits(client):
    resp = client.post(
        "/auth/signup",
        json={"email": "new@example.com", "password": "password123"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["access_token"]
    assert data["user"]["email"] == "new@example.com"
    assert data["user"]["credits_remaining"] == 3
    assert data["user"]["plan"] == "free"


def test_signup_duplicate_email_conflicts(client):
    body = {"email": "dup@example.com", "password": "password123"}
    assert client.post("/auth/signup", json=body).status_code == 201
    resp = client.post("/auth/signup", json=body)
    assert resp.status_code == 409


def test_signup_rejects_short_password(client):
    resp = client.post(
        "/auth/signup", json={"email": "x@example.com", "password": "short"}
    )
    assert resp.status_code == 422


def test_login_succeeds_with_correct_credentials(client):
    client.post(
        "/auth/signup", json={"email": "log@example.com", "password": "password123"}
    )
    resp = client.post(
        "/auth/login", json={"email": "log@example.com", "password": "password123"}
    )
    assert resp.status_code == 200
    assert resp.json()["access_token"]


def test_login_fails_with_wrong_password(client):
    client.post(
        "/auth/signup", json={"email": "log2@example.com", "password": "password123"}
    )
    resp = client.post(
        "/auth/login", json={"email": "log2@example.com", "password": "wrongpass"}
    )
    assert resp.status_code == 401


def test_me_requires_auth(client):
    assert client.get("/auth/me").status_code == 403  # no bearer token


def test_me_returns_current_user(client, auth_headers):
    headers, user = auth_headers
    resp = client.get("/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == user["email"]
