"""Loopback-only process for RFC-0031 compatibility access."""

import uvicorn
from fastapi import FastAPI

from home_ai_cluster.api.openai_compatibility import compatibility_router
from home_ai_cluster.main import create_app

COMPATIBILITY_HOST = "127.0.0.1"
COMPATIBILITY_PORT = 8001


def create_openai_compatibility_app() -> FastAPI:
    """Create the dedicated app without changing the ordinary application."""
    app = create_app()
    app.include_router(compatibility_router)
    return app


def main() -> None:
    """Run the RFC-0031 compatibility process on loopback only."""
    uvicorn.run(
        create_openai_compatibility_app(),
        host=COMPATIBILITY_HOST,
        port=COMPATIBILITY_PORT,
    )
