"""Vision service tests — Anthropic client fully mocked."""
import io
import json

import pytest
from PIL import Image

from app.schemas.design import RoomAnalysis
from app.services import vision
from app.services.vision import VisionServiceError, analyze_room

VALID_PAYLOAD = {
    "room_type": "bedroom",
    "detected_objects": [
        {"label": "window", "location": "left wall", "confidence": "high"},
        {"label": "bed", "location": "center", "confidence": "high"},
    ],
    "palette": [
        {"hex": "#E8E2D6", "name": "warm sand", "usage": "walls"},
        {"hex": "#3B4A3F", "name": "deep moss", "usage": "accent furniture"},
    ],
    "furniture_suggestions": [
        {
            "category": "rug",
            "description": "Jute area rug, neutral tone, ~5x7 ft",
            "placement_note": "centered under bed, walkway clear on the window side",
            "est_price_range_inr": "1500-4000",
        }
    ],
    "layout_notes": "Keep the area near the window clear for light.",
}


class _Block:
    def __init__(self, text):
        self.text = text


class _Response:
    def __init__(self, text):
        self.content = [_Block(text)]


class _FakeMessages:
    """Returns queued responses in order; records call count."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        if not self._responses:
            raise AssertionError("create() called more times than expected")
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return _Response(item)


class _FakeClient:
    def __init__(self, responses):
        self.messages = _FakeMessages(responses)


@pytest.fixture()
def image_file(tmp_path):
    p = tmp_path / "room.png"
    Image.new("RGB", (600, 600), (128, 128, 128)).save(p, format="PNG")
    return str(p)


def _patch_client(monkeypatch, responses):
    fake = _FakeClient(responses)
    monkeypatch.setattr(vision, "_get_client", lambda: fake)
    return fake


def test_analyze_room_happy_path(monkeypatch, image_file):
    fake = _patch_client(monkeypatch, [json.dumps(VALID_PAYLOAD)])
    result = analyze_room(image_file, "scandinavian")
    assert isinstance(result, RoomAnalysis)
    assert result.room_type == "bedroom"
    assert result.detected_objects[0].label == "window"
    assert result.palette[0].hex == "#E8E2D6"
    assert fake.messages.calls == 1
    assert result.raw_output  # raw text captured for debug storage


def test_analyze_room_strips_code_fences(monkeypatch, image_file):
    fenced = "```json\n" + json.dumps(VALID_PAYLOAD) + "\n```"
    _patch_client(monkeypatch, [fenced])
    result = analyze_room(image_file, "minimalist")
    assert result.room_type == "bedroom"


def test_analyze_room_retries_once_then_succeeds(monkeypatch, image_file):
    fake = _patch_client(
        monkeypatch, ["this is not json at all", json.dumps(VALID_PAYLOAD)]
    )
    result = analyze_room(image_file, "industrial")
    assert result.room_type == "bedroom"
    assert fake.messages.calls == 2  # retried exactly once


def test_analyze_room_fails_after_retry(monkeypatch, image_file):
    fake = _patch_client(monkeypatch, ["nope", "still not json"])
    with pytest.raises(VisionServiceError):
        analyze_room(image_file, "coastal")
    assert fake.messages.calls == 2  # initial + one retry, no more


def test_analyze_room_invalid_schema_retries(monkeypatch, image_file):
    # Missing required fields -> ValidationError -> retry.
    bad = json.dumps({"room_type": "bedroom"})  # missing layout_notes
    fake = _patch_client(monkeypatch, [bad, json.dumps(VALID_PAYLOAD)])
    result = analyze_room(image_file, "bohemian")
    assert result.layout_notes
    assert fake.messages.calls == 2


def test_analyze_room_api_error_raises(monkeypatch, image_file):
    _patch_client(monkeypatch, [RuntimeError("API down")])
    with pytest.raises(VisionServiceError):
        analyze_room(image_file, "modern_indian")


def test_analyze_room_missing_image(monkeypatch, tmp_path):
    _patch_client(monkeypatch, [json.dumps(VALID_PAYLOAD)])
    with pytest.raises(VisionServiceError):
        analyze_room(str(tmp_path / "nope.png"), "scandinavian")
