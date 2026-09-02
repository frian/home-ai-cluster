"""Fixed browser assets for the RFC-0062 loopback application composition."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

_WEB_DIRECTORY = Path(__file__).parent
_CACHE_HEADERS = {"Cache-Control": "no-store"}


def add_loopback_browser_routes(app: FastAPI) -> FastAPI:
    """Attach only the fixed RFC-0062 browser page and assets to one API app."""

    @app.get("/", include_in_schema=False)
    def page() -> FileResponse:
        return FileResponse(
            _WEB_DIRECTORY / "index.html",
            media_type="text/html",
            headers=_CACHE_HEADERS,
        )

    @app.get("/assets/app.css", include_in_schema=False)
    def stylesheet() -> FileResponse:
        return FileResponse(
            _WEB_DIRECTORY / "assets" / "app.css",
            media_type="text/css",
            headers=_CACHE_HEADERS,
        )

    @app.get("/assets/app.js", include_in_schema=False)
    def script() -> FileResponse:
        return FileResponse(
            _WEB_DIRECTORY / "assets" / "app.js",
            media_type="application/javascript",
            headers=_CACHE_HEADERS,
        )

    @app.get("/assets/pdfjs-6.2.108/pdf.min.mjs", include_in_schema=False)
    def pdfjs_main() -> FileResponse:
        return FileResponse(
            _WEB_DIRECTORY / "assets" / "pdfjs-6.2.108" / "pdf.min.mjs",
            media_type="application/javascript",
            headers=_CACHE_HEADERS,
        )

    @app.get("/assets/pdfjs-6.2.108/pdf.worker.min.mjs", include_in_schema=False)
    def pdfjs_worker() -> FileResponse:
        return FileResponse(
            _WEB_DIRECTORY / "assets" / "pdfjs-6.2.108" / "pdf.worker.min.mjs",
            media_type="application/javascript",
            headers=_CACHE_HEADERS,
        )

    return app
