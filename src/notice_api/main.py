import importlib.metadata
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

from notice_api import cors
from notice_api.api.v1.v1_router import router as v1_router
from notice_api.core.config import settings

app = FastAPI(
    title="Not!ce API",
    description=importlib.metadata.metadata(__package__)["Summary"],
    version=importlib.metadata.version(__package__),
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
