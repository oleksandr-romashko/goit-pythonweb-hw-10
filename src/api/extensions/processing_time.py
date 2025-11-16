"""
Processing time middleware configuration.

This module adds processing time header to the response.
"""

import time
from typing import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class ProcessingTimeMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add processing duration response header.

    Calculates how much time it takes to process the request and adds it as a response header.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time_ms = (time.perf_counter() - start_time) * 1000
        response.headers["X-Process-Time"] = f"{process_time_ms:.3f}ms"
        return response


def add_processing_time_header(app: FastAPI) -> None:
    """Init processing time middleware"""
    app.add_middleware(ProcessingTimeMiddleware)
