"""Design + vision-analysis Pydantic schemas.

These schemas validate the JSON returned by Claude (RoomAnalysis) and shape the
API responses for designs.
"""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr


class Style(str, Enum):
    scandinavian = "scandinavian"
    minimalist = "minimalist"
    industrial = "industrial"
    bohemian = "bohemian"
    modern_indian = "modern_indian"
    traditional_indian = "traditional_indian"
    mid_century = "mid_century"
    coastal = "coastal"


# ---- Vision model output (validated against Claude's JSON) ----


class DetectedObject(BaseModel):
    label: str
    location: str | None = None
    confidence: str | None = None


class PaletteColor(BaseModel):
    hex: str
    name: str
    usage: str


class FurnitureSuggestion(BaseModel):
    category: str
    description: str
    placement_note: str
    est_price_range_inr: str


class RoomAnalysis(BaseModel):
    """The validated structured result from the vision model."""

    room_type: str
    detected_objects: list[DetectedObject] = Field(default_factory=list)
    palette: list[PaletteColor] = Field(default_factory=list)
    furniture_suggestions: list[FurnitureSuggestion] = Field(default_factory=list)
    layout_notes: str

    # Full raw model text, attached by the vision service for debug storage.
    _raw_output: str = PrivateAttr(default="")

    @property
    def raw_output(self) -> str:
        return self._raw_output


# ---- API request/response ----


class DesignCreate(BaseModel):
    style: Style


class DesignOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    room_id: int
    style: str
    status: str
    room_type: str | None = None
    image_url: str | None = None
    detected_objects: list[DetectedObject] | None = None
    palette: list[PaletteColor] | None = None
    furniture_suggestions: list[FurnitureSuggestion] | None = None
    layout_notes: str | None = None
    created_at: datetime
