"""Room upload routes."""
import io

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session

try:  # Enable HEIC/HEIF support if available.
    import pillow_heif

    pillow_heif.register_heif_opener()
except Exception:  # pragma: no cover - optional dependency
    pass

from app.config import settings
from app.db import get_db
from app.deps import get_current_user
from app.models import Room, User
from app.schemas.room import RoomUploadResponse
from app.services.storage import get_storage

router = APIRouter(tags=["rooms"])

# Map Pillow format -> file extension we store under.
_ALLOWED_FORMATS = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp", "HEIF": "heic"}


@router.post("/rooms", response_model=RoomUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_room(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RoomUploadResponse:
    data = await image.read()

    if len(data) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum size of {settings.max_upload_bytes // (1024 * 1024)}MB",
        )

    # Validate it is a real image of an allowed type and meets min dimensions.
    try:
        with Image.open(io.BytesIO(data)) as img:
            fmt = img.format
            width, height = img.size
    except (UnidentifiedImageError, OSError):
        raise HTTPException(
            status_code=400,
            detail="File is not a valid image (allowed: jpg, png, webp, heic)",
        )

    if fmt not in _ALLOWED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported image type. Allowed: jpg, png, webp, heic",
        )

    min_dim = settings.min_image_dimension
    if width < min_dim or height < min_dim:
        raise HTTPException(
            status_code=400,
            detail=f"Image must be at least {min_dim}x{min_dim} pixels",
        )

    storage = get_storage()
    key = storage.save(data, _ALLOWED_FORMATS[fmt])

    room = Room(user_id=current_user.id, original_image_path=key)
    db.add(room)
    db.commit()
    db.refresh(room)

    return RoomUploadResponse(room_id=room.id, image_url=storage.url_for(key))
