"""Provides middlewares for the FastAPI application.

Provided Middlewares:
    - `install_logging_middleware`: Install an access logging middleware which logs request information including the
        request id, the HTTP request metadata, and the request duration in a structured format.
"""


import time
from typing import Awaitable, Callable

import structlog
from asgi_correlation_id import correlation_id
from fastapi import FastAPI, Request, Response, status
from uvicorn.protocols.utils import get_path_with_query_string

access_logger = structlog.get_logger("api.access")


def install_logging_middleware(app: FastAPI) -> FastAPI:
    """Install an access logging middleware which logs request information including the request id,
    the HTTP request metadata, and the request duration in a structured format.

    Notes:
        This middleware mimics the Uvicorn access log format, but adds all parameters as structured information.
    """

    @app.middleware("http")
    async def log_request_span(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Log http handler span."""

        structlog.contextvars.clear_contextvars()
        # These context vars will be added to all log entries emitted during the request
        request_id = correlation_id.get()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        start_time = time.perf_counter_ns()
        response = Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        try:
            response = await call_next(request)
        except Exception:
            structlog.stdlib.get_logger("api.error").exception("Uncaught exception")
            raise
        finally:
            process_time = time.perf_counter_ns() - start_time
            status_code = response.status_code
            url = get_path_with_query_string(request.scope)  # pyright: ignore[reportGeneralTypeIssues]
            client_host = request.client.host  # pyright: ignore[reportOptionalMemberAccess]
            client_port = request.client.port  # pyright: ignore[reportOptionalMemberAccess]
            http_method = request.method
            http_version = request.scope["http_version"]
            # Recreate the Uvicorn access log format, but add all parameters as structured information
            access_logger.info(
                f'{client_host}:{client_port} - "{http_method} {url} HTTP/{http_version}" {status_code}',
                http={
                    "url": request.url,
                    "status_code": status_code,
                    "method": http_method,
                    "request_id": request_id,
                    "version": http_version,
                },
                network={"client": {"host": client_host, "port": client_port}},
                duration=process_time,
            )
            response.headers["X-Process-Time"] = str(process_time / 1e9)
        return response

    return app
