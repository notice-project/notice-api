import importlib.metadata
from contextlib import asynccontextmanager

import structlog
from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

import notice_api.utils.logging.core as logging_core
import notice_api.utils.logging.middlewares as logging_middlewares
from notice_api import db
from notice_api.bookshelves.routes import router as bookshelves_router
from notice_api.core.config import settings
from notice_api.notes.routes import router as notes_router
from notice_api.playback.routes import router as playback_router
from notice_api.transcript.routes import router as transcribe_router

logging_core.setup_logging(
    json_logs=settings.LOG_JSON_FORMAT,
    log_level=settings.LOG_LEVEL,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for the application."""

    logger = structlog.get_logger("lifespan")
    await db.create_db_and_tables()
    logger.info("Finished creating database tables.")
    yield


app = FastAPI(
    title="Not!ce API",
    description=importlib.metadata.metadata(__package__)["Summary"],
    version=importlib.metadata.version(__package__),
    lifespan=lifespan,
)

logging_middlewares.install_logging_middleware(app)
app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_SECRET_KEY)
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PingResponse(BaseModel):
    """Response model for the ping endpoint."""

    message: str = "Server is running 🎉"


@app.get("/")
def ping() -> PingResponse:
    """Check if the server is running."""

    return PingResponse()


app.include_router(bookshelves_router)
app.include_router(notes_router)
app.include_router(playback_router)
app.include_router(transcribe_router)
