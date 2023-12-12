from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from pydantic import AnyHttpUrl


def setup(app: FastAPI, origins: list[AnyHttpUrl | Literal["*"]]):
    """Configure CORS for the FastAPI application."""

    logger.info(f"Adding CORS origins: {origins}")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in origins],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
