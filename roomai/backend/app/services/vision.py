"""Vision service — calls Claude with the room image + style and returns a
validated RoomAnalysis.

Design goals (from the build spec):
- Single multimodal call: image + style -> structured JSON.
- Anti-hallucination: the model must only describe what it can actually see and
  must never suggest placements that block a visible door/window/walkway.
- Validate the model's JSON against the Pydantic schema; on validation failure,
  retry exactly once with a stricter "valid JSON only" reminder, then fail.
"""
import base64
import json
import logging
from pathlib import Path

from pydantic import ValidationError

from app.config import settings
from app.schemas.design import RoomAnalysis

logger = logging.getLogger(__name__)


class VisionServiceError(Exception):
    """Raised when analysis fails (API error or unparseable/invalid output).

    The caller is responsible for credit logic — credits must NOT be consumed
    when this is raised.
    """


_MEDIA_TYPES = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
    "heic": "image/heic",
    "heif": "image/heic",
}

_STYLE_LABELS = {
    "scandinavian": "Scandinavian",
    "minimalist": "Minimalist",
    "industrial": "Industrial",
    "bohemian": "Bohemian",
    "modern_indian": "Modern Indian",
    "traditional_indian": "Traditional Indian",
    "mid_century": "Mid-Century Modern",
    "coastal": "Coastal",
}

SYSTEM_PROMPT = (
    "You are an expert interior designer and a careful visual analyst. "
    "You analyze a single photo of a room and produce a practical design report.\n\n"
    "CRITICAL RULES (these prevent the #1 user complaint about AI design tools):\n"
    "- Only describe objects, windows, doors, and architectural features you can "
    "ACTUALLY SEE in the image. If you are not confident an element is present, "
    "OMIT it rather than guessing.\n"
    "- Never invent furniture, fixtures, or room features that the photo does not "
    "clearly show.\n"
    "- Do NOT suggest furniture placements that would block a visible door, window, "
    "or walkway. Respect the room's real geometry.\n"
    "- Prefer fewer, high-confidence observations over many speculative ones.\n\n"
    "You always respond with a single valid JSON object and nothing else — no "
    "markdown, no prose, no code fences."
)

_SCHEMA_INSTRUCTION = """Analyze this room photo for a "{style_label}" interior design.

Return ONLY a JSON object with exactly this shape:
{{
  "room_type": "string, e.g. bedroom / living room / kitchen",
  "detected_objects": [
    {{"label": "string", "location": "string e.g. 'left wall'", "confidence": "high|medium|low"}}
  ],
  "palette": [
    {{"hex": "#RRGGBB", "name": "human-friendly color name", "usage": "where to use it"}}
  ],
  "furniture_suggestions": [
    {{
      "category": "string e.g. rug / sofa / lamp",
      "description": "what to add, with size/material hints",
      "placement_note": "where it goes; must not block visible doors/windows/walkways",
      "est_price_range_inr": "string range in INR, e.g. '1500-4000'"
    }}
  ],
  "layout_notes": "2-4 sentences of practical layout advice grounded in what is visible"
}}

Only include detected_objects you can actually see. Palette should suit the
{style_label} style while complementing the existing room. Suggest 3-6 furniture items."""

_RETRY_REMINDER = (
    "\n\nYour previous response was not valid JSON matching the schema. "
    "Return ONLY a single valid JSON object matching the schema exactly. "
    "No markdown, no code fences, no commentary."
)


def _encode_image(image_path: str) -> tuple[str, str]:
    path = Path(image_path)
    if not path.exists():
        raise VisionServiceError(f"Image not found at {image_path}")
    ext = path.suffix.lstrip(".").lower()
    media_type = _MEDIA_TYPES.get(ext)
    if media_type is None:
        raise VisionServiceError(f"Unsupported image extension: {ext}")
    encoded = base64.standard_b64encode(path.read_bytes()).decode("ascii")
    return encoded, media_type


def _get_client():
    """Return an Anthropic client. Isolated for easy mocking in tests."""
    if not settings.anthropic_api_key:
        raise VisionServiceError(
            "ANTHROPIC_API_KEY is not configured; cannot call the vision model."
        )
    import anthropic  # imported lazily so tests can run without the key

    return anthropic.Anthropic(api_key=settings.anthropic_api_key)


def _extract_text(response) -> str:
    """Pull the text content out of an Anthropic Messages response."""
    parts = []
    for block in getattr(response, "content", []) or []:
        text = getattr(block, "text", None)
        if text:
            parts.append(text)
    return "".join(parts).strip()


def _parse_json_object(text: str) -> dict:
    """Parse a JSON object from model text, tolerating code fences / stray prose."""
    text = text.strip()
    if text.startswith("```"):
        # Strip ```json ... ``` fences.
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Fall back to the substring between the first { and last }.
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start : end + 1])
        raise


def _invoke_model(client, image_b64: str, media_type: str, prompt: str) -> str:
    response = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_b64,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )
    return _extract_text(response)


def analyze_room(image_path: str, style: str) -> RoomAnalysis:
    """Call Claude with the image + style and return a validated RoomAnalysis.

    Raises VisionServiceError on any failure (the caller handles credit logic;
    credits are not consumed when this raises).
    """
    image_b64, media_type = _encode_image(image_path)
    style_label = _STYLE_LABELS.get(style, style)
    prompt = _SCHEMA_INSTRUCTION.format(style_label=style_label)

    try:
        client = _get_client()
    except VisionServiceError:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        raise VisionServiceError(f"Failed to init vision client: {exc}") from exc

    raw_text = ""
    last_error: Exception | None = None
    for attempt in range(2):  # one initial try + one stricter retry
        attempt_prompt = prompt if attempt == 0 else prompt + _RETRY_REMINDER
        try:
            raw_text = _invoke_model(client, image_b64, media_type, attempt_prompt)
        except Exception as exc:
            raise VisionServiceError(f"Vision model call failed: {exc}") from exc

        try:
            data = _parse_json_object(raw_text)
            analysis = RoomAnalysis.model_validate(data)
            # Attach raw text for debug storage by the caller.
            analysis._raw_output = raw_text
            return analysis
        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = exc
            logger.warning("Vision output invalid on attempt %d: %s", attempt + 1, exc)
            continue

    raise VisionServiceError(
        f"Vision model returned invalid output after retry: {last_error}"
    )
