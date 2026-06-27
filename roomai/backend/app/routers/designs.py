"""Design creation and retrieval routes."""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import Design, Room, User
from app.schemas.design import DesignCreate, DesignOut
from app.services import vision
from app.services.credits import consume_credit, has_credits
from app.services.storage import get_storage

logger = logging.getLogger(__name__)

router = APIRouter(tags=["designs"])


def _serialize(design: Design, room: Room) -> DesignOut:
    storage = get_storage()
    return DesignOut(
        id=design.id,
        room_id=design.room_id,
        style=design.style,
        status=design.status,
        room_type=room.room_type,
        image_url=storage.url_for(room.original_image_path),
        detected_objects=design.detected_objects,
        palette=design.palette,
        furniture_suggestions=design.furniture_suggestions,
        layout_notes=design.layout_notes,
        created_at=design.created_at,
    )


def _get_owned_room(db: Session, room_id: int, user: User) -> Room:
    room = db.get(Room, room_id)
    if room is None or room.user_id != user.id:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


@router.post(
    "/rooms/{room_id}/designs",
    response_model=DesignOut,
    status_code=status.HTTP_201_CREATED,
)
def create_design(
    room_id: int,
    payload: DesignCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    room = _get_owned_room(db, room_id, current_user)

    # Credit gate BEFORE doing any paid work.
    if not has_credits(current_user):
        return JSONResponse(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            content={
                "error": "out_of_credits",
                "message": "You have no design credits remaining. Upgrade to continue.",
            },
        )

    style = payload.style.value
    storage = get_storage()
    image_path = storage.abspath(room.original_image_path)

    try:
        analysis = vision.analyze_room(image_path, style)
    except vision.VisionServiceError as exc:
        # Persist a failed design for the audit trail; do NOT consume a credit.
        logger.warning("Design analysis failed for room %s: %s", room_id, exc)
        failed = Design(room_id=room.id, style=style, status="failed")
        db.add(failed)
        db.commit()
        raise HTTPException(
            status_code=500,
            detail="Analysis failed. No credit was used — please try again.",
        )

    # Success: persist the design, update the room type, and consume one credit
    # — all in a single transaction so they stay consistent.
    design = Design(
        room_id=room.id,
        style=style,
        status="complete",
        detected_objects=[o.model_dump() for o in analysis.detected_objects],
        palette=[p.model_dump() for p in analysis.palette],
        furniture_suggestions=[f.model_dump() for f in analysis.furniture_suggestions],
        layout_notes=analysis.layout_notes,
        raw_model_output=analysis.raw_output,
    )
    room.room_type = analysis.room_type
    consume_credit(current_user)
    db.add(design)
    db.commit()
    db.refresh(design)

    return _serialize(design, room)


@router.get("/designs/{design_id}", response_model=DesignOut)
def get_design(
    design_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DesignOut:
    design = db.get(Design, design_id)
    if design is None:
        raise HTTPException(status_code=404, detail="Design not found")
    room = db.get(Room, design.room_id)
    if room is None or room.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Design not found")
    return _serialize(design, room)


@router.get("/users/me/designs", response_model=list[DesignOut])
def list_my_designs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DesignOut]:
    rows = (
        db.query(Design, Room)
        .join(Room, Design.room_id == Room.id)
        .filter(Room.user_id == current_user.id)
        .order_by(Design.created_at.desc())
        .all()
    )
    return [_serialize(design, room) for design, room in rows]
