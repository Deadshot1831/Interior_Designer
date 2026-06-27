"""Room upload endpoint tests."""
import io

import pytest
from PIL import Image


def _png_bytes(width: int = 500, height: int = 500) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (width, height), color=(120, 140, 130)).save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture(autouse=True)
def _tmp_storage(tmp_path, monkeypatch):
    # Redirect uploads to a per-test temp dir.
    from app.config import settings

    monkeypatch.setattr(settings, "storage_path", str(tmp_path / "uploads"))


def test_upload_requires_auth(client):
    resp = client.post(
        "/rooms", files={"image": ("room.png", _png_bytes(), "image/png")}
    )
    assert resp.status_code == 403


def test_upload_valid_image(client, auth_headers):
    headers, _ = auth_headers
    resp = client.post(
        "/rooms",
        headers=headers,
        files={"image": ("room.png", _png_bytes(), "image/png")},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["room_id"] > 0
    assert body["image_url"].startswith("/storage/")


def test_upload_rejects_small_image(client, auth_headers):
    headers, _ = auth_headers
    resp = client.post(
        "/rooms",
        headers=headers,
        files={"image": ("tiny.png", _png_bytes(100, 100), "image/png")},
    )
    assert resp.status_code == 400
    assert "at least" in resp.json()["detail"]


def test_upload_rejects_non_image(client, auth_headers):
    headers, _ = auth_headers
    resp = client.post(
        "/rooms",
        headers=headers,
        files={"image": ("notes.txt", b"hello world not an image", "text/plain")},
    )
    assert resp.status_code == 400


def test_upload_rejects_oversized_file(client, auth_headers, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "max_upload_bytes", 10)  # 10 bytes
    headers, _ = auth_headers
    resp = client.post(
        "/rooms",
        headers=headers,
        files={"image": ("room.png", _png_bytes(), "image/png")},
    )
    assert resp.status_code == 413
