from collections.abc import Callable
from contextlib import AbstractAsyncContextManager

from fastapi import FastAPI

from home_ai_cluster.api.routes import router
from home_ai_cluster.api.wiring import StaticRemoteProofWiring


def create_app(
    static_remote_proof_wiring: StaticRemoteProofWiring | None = None,
    *,
    lifespan: Callable[[FastAPI], AbstractAsyncContextManager[None]] | None = None,
) -> FastAPI:
    app = FastAPI(title="Home AI Cluster", lifespan=lifespan)
    app.state.static_remote_proof_wiring = static_remote_proof_wiring
    app.state.automatic_proof_orchestrator = None
    app.include_router(router)
    return app


app = create_app()
