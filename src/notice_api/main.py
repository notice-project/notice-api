import importlib.metadata

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import notice_api.utils.logging.core as logging_core
import notice_api.utils.logging.middlewares as logging_middlewares
from notice_api.core.config import settings

logging_core.setup_logging(
    json_logs=settings.LOG_JSON_FORMAT,
    log_level=settings.LOG_LEVEL,
)

app = FastAPI(
    title="Not!ce API",
    description=importlib.metadata.metadata(__package__)["Summary"],
    version=importlib.metadata.version(__package__),
)

logging_middlewares.install_logging_middleware(app)
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthCheckResponse(BaseModel):
    """Response model for health check endpoint."""

    message: str = "Server is running 🎉"


@app.get("/")
def health_check() -> HealthCheckResponse:
    """Check if the server is running."""

    return HealthCheckResponse()
