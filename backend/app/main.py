import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.db.session import Base, engine
from app.models import Task, User  # noqa: F401 — registers tables with SQLAlchemy
from app.routers import auth, tasks

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Task Manager API",
    description="A simple task management API with JWT authentication.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(tasks.router)

# Serve the frontend. Using Path(__file__) makes this work regardless of
# where uvicorn is invoked from.
_frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"

if _frontend_dir.is_dir():
    app.mount("/static", StaticFiles(directory=str(_frontend_dir)), name="static")

    @app.get("/", include_in_schema=False)
    def serve_frontend():
        return FileResponse(str(_frontend_dir / "index.html"))


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}
