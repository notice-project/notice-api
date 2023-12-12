import importlib.metadata
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

from notice_api import cors
from notice_api.api.v1.v1_router import router as v1_router
from notice_api.core.config import settings


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Context manager to run startup and shutdown events."""

    # Run startup events
    yield
    # Run shutdown events


app = FastAPI(
    title="Not!ce API",
    description="API Server for the Not!ce project",
    version=importlib.metadata.version("notice_api"),
    lifespan=lifespan,
)

app.include_router(v1_router, prefix=settings.API_V1_STR)

if settings.BACKEND_CORS_ORIGINS:
    cors.setup(app, settings.BACKEND_CORS_ORIGINS)


class HealthCheckResponse(BaseModel):
    """Response model for health check endpoint."""

    message: str = "Server is running 🎉"


@app.get("/")
def health_check() -> HealthCheckResponse:
    """Check if the server is running."""

    return HealthCheckResponse()
