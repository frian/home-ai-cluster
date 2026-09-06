from collections.abc import Callable
from contextlib import AbstractAsyncContextManager

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, Response

from home_ai_cluster.api.client_disconnect import ConfirmedClientDisconnect
from home_ai_cluster.api.routes import receiver_router, router
from home_ai_cluster.api.wiring import (
    LocalAppComposition,
    StaticRemoteCollectionWiring,
    StaticRemoteWiring,
)
from home_ai_cluster.core.remote_transport import RemoteTransportError


async def _remote_transport_error_response(
    _: Request, __: RemoteTransportError
) -> PlainTextResponse:
    """Contain normalized remote failures before ASGI logging sees their cause."""
    return PlainTextResponse("Internal Server Error", status_code=500)


class _AbandonedRequestResponse(Response):
    """A handled disconnect intentionally has no response to deliver."""

    async def __call__(self, scope, receive, send) -> None:
        return


async def _confirmed_client_disconnect_response(
    _: Request, __: ConfirmedClientDisconnect
) -> Response:
    """End an already-abandoned request without exposing cancellation to ASGI."""
    return _AbandonedRequestResponse()


def create_app(
    *,
    local_app_composition: LocalAppComposition | None = None,
    static_remote_wiring: StaticRemoteWiring | None = None,
    static_remote_collection_wiring: StaticRemoteCollectionWiring | None = None,
    lifespan: Callable[[FastAPI], AbstractAsyncContextManager[None]] | None = None,
) -> FastAPI:
    app = FastAPI(title="Home AI Cluster", lifespan=lifespan)
    app.add_exception_handler(RemoteTransportError, _remote_transport_error_response)
    app.add_exception_handler(
        ConfirmedClientDisconnect, _confirmed_client_disconnect_response
    )
    app.state.static_remote_wiring = static_remote_wiring
    app.state.static_remote_collection_wiring = static_remote_collection_wiring
    app.state.local_app_composition = local_app_composition
    app.include_router(receiver_router)
    app.include_router(router)
    return app


def create_receiver_app(*, local_app_composition: LocalAppComposition) -> FastAPI:
    """Create the closed RFC-0109 receiver route surface for one composition."""
    app = FastAPI(
        title="Home AI Cluster receiver",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.add_exception_handler(RemoteTransportError, _remote_transport_error_response)
    app.add_exception_handler(
        ConfirmedClientDisconnect, _confirmed_client_disconnect_response
    )
    app.state.local_app_composition = local_app_composition
    app.include_router(receiver_router)
    return app


app = create_app()
