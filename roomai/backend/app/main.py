"""RoomAI FastAPI application entrypoint."""
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import auth, designs, rooms

app = FastAPI(title="RoomAI API", version="0.1.0")

# CORS for the Next.js dev server.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded images statically for the frontend to display.
_storage_dir = Path(settings.storage_path)
_storage_dir.mkdir(parents=True, exist_ok=True)
app.mount("/storage", StaticFiles(directory=str(_storage_dir)), name="storage")

app.include_router(auth.router)
app.include_router(rooms.router)
app.include_router(designs.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "environment": settings.environment}
