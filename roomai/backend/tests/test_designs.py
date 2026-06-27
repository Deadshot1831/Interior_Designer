"""Design endpoint + credit logic tests (vision mocked)."""
import io

import pytest
from PIL import Image

from app.schemas.design import RoomAnalysis
from app.services import vision

ANALYSIS = RoomAnalysis(
    room_type="living room",
    detected_objects=[{"label": "sofa", "location": "center", "confidence": "high"}],
    palette=[{"hex": "#FFFFFF", "name": "white", "usage": "walls"}],
    furniture_suggestions=[
        {
            "category": "rug",
            "description": "Wool rug",
            "placement_note": "under coffee table",
            "est_price_range_inr": "2000-5000",
        }
    ],
    layout_notes="Keep the walkway to the balcony clear.",
)


def _png_bytes(w=500, h=500) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (w, h), (100, 120, 110)).save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture(autouse=True)
def _tmp_storage(tmp_path, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "storage_path", str(tmp_path / "uploads"))


def _upload_room(client, headers) -> int:
    resp = client.post(
        "/rooms", headers=headers, files={"image": ("r.png", _png_bytes(), "image/png")}
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["room_id"]


def test_create_design_success_decrements_one_credit(client, auth_headers, monkeypatch):
    headers, user = auth_headers
    assert user["credits_remaining"] == 3
    room_id = _upload_room(client, headers)

    monkeypatch.setattr(vision, "analyze_room", lambda path, style: ANALYSIS)
    resp = client.post(
        f"/rooms/{room_id}/designs", headers=headers, json={"style": "scandinavian"}
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "complete"
    assert body["room_type"] == "living room"
    assert body["palette"][0]["hex"] == "#FFFFFF"

    # Credit decremented exactly once.
    me = client.get("/auth/me", headers=headers).json()
    assert me["credits_remaining"] == 2


def test_failed_analysis_does_not_decrement_credit(client, auth_headers, monkeypatch):
    headers, _ = auth_headers
    room_id = _upload_room(client, headers)

    def _boom(path, style):
        raise vision.VisionServiceError("model unavailable")

    monkeypatch.setattr(vision, "analyze_room", _boom)
    resp = client.post(
        f"/rooms/{room_id}/designs", headers=headers, json={"style": "minimalist"}
    )
    assert resp.status_code == 500
    # CRITICAL: no credit consumed on failure.
    me = client.get("/auth/me", headers=headers).json()
    assert me["credits_remaining"] == 3


def test_out_of_credits_returns_402(client, auth_headers, monkeypatch):
    headers, _ = auth_headers
    monkeypatch.setattr(vision, "analyze_room", lambda path, style: ANALYSIS)

    # Burn all 3 credits.
    for _ in range(3):
        rid = _upload_room(client, headers)
        r = client.post(
            f"/rooms/{rid}/designs", headers=headers, json={"style": "coastal"}
        )
        assert r.status_code == 201

    rid = _upload_room(client, headers)
    resp = client.post(
        f"/rooms/{rid}/designs", headers=headers, json={"style": "coastal"}
    )
    assert resp.status_code == 402
    assert resp.json()["error"] == "out_of_credits"


def test_create_design_invalid_style_422(client, auth_headers):
    headers, _ = auth_headers
    room_id = _upload_room(client, headers)
    resp = client.post(
        f"/rooms/{room_id}/designs", headers=headers, json={"style": "art_deco"}
    )
    assert resp.status_code == 422


def test_cannot_design_other_users_room(client, auth_headers, monkeypatch):
    headers, _ = auth_headers
    room_id = _upload_room(client, headers)

    # Second user.
    other = client.post(
        "/auth/signup", json={"email": "other@example.com", "password": "password123"}
    ).json()
    other_headers = {"Authorization": f"Bearer {other['access_token']}"}

    monkeypatch.setattr(vision, "analyze_room", lambda path, style: ANALYSIS)
    resp = client.post(
        f"/rooms/{room_id}/designs", headers=other_headers, json={"style": "coastal"}
    )
    assert resp.status_code == 404


def test_get_design_and_list(client, auth_headers, monkeypatch):
    headers, _ = auth_headers
    monkeypatch.setattr(vision, "analyze_room", lambda path, style: ANALYSIS)
    room_id = _upload_room(client, headers)
    design_id = client.post(
        f"/rooms/{room_id}/designs", headers=headers, json={"style": "bohemian"}
    ).json()["id"]

    got = client.get(f"/designs/{design_id}", headers=headers)
    assert got.status_code == 200
    assert got.json()["id"] == design_id

    listed = client.get("/users/me/designs", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_e2e_signup_upload_design_fetch(client, monkeypatch):
    """End-to-end: signup -> upload -> design -> fetch; credit drops exactly once."""
    signup = client.post(
        "/auth/signup", json={"email": "e2e@example.com", "password": "password123"}
    ).json()
    headers = {"Authorization": f"Bearer {signup['access_token']}"}
    assert signup["user"]["credits_remaining"] == 3

    room_id = _upload_room(client, headers)
    monkeypatch.setattr(vision, "analyze_room", lambda path, style: ANALYSIS)
    design = client.post(
        f"/rooms/{room_id}/designs", headers=headers, json={"style": "modern_indian"}
    )
    assert design.status_code == 201
    design_id = design.json()["id"]

    fetched = client.get(f"/designs/{design_id}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["status"] == "complete"

    assert client.get("/auth/me", headers=headers).json()["credits_remaining"] == 2
