"""Room-related Pydantic schemas."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RoomUploadResponse(BaseModel):
    room_id: int
    image_url: str


class RoomOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    room_type: str | None
    created_at: datetime
