from collections.abc import Callable
from contextlib import AbstractAsyncContextManager

from fastapi import FastAPI

from home_ai_cluster.api.routes import router
from home_ai_cluster.api.wiring import (
    ProofReceivingAppWiring,
    StaticRemoteCollectionWiring,
    StaticRemoteProofWiring,
    StaticRemoteWiring,
)
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry


def create_app(
    static_remote_proof_wiring: StaticRemoteProofWiring | None = None,
    *,
    static_remote_wiring: StaticRemoteWiring | None = None,
    static_remote_collection_wiring: StaticRemoteCollectionWiring | None = None,
    lifespan: Callable[[FastAPI], AbstractAsyncContextManager[None]] | None = None,
) -> FastAPI:
    app = FastAPI(title="Home AI Cluster", lifespan=lifespan)
    app.state.static_remote_proof_wiring = static_remote_proof_wiring
    app.state.static_remote_wiring = static_remote_wiring
    app.state.static_remote_collection_wiring = static_remote_collection_wiring
    app.state.proof_receiving_app_wiring = None
    app.state.automatic_proof_orchestrator = None
    app.include_router(router)
    return app


def create_proof_receiving_app(
    *,
    node_registry: NodeRegistry,
    adapter_registry: AdapterRegistry,
) -> FastAPI:
    """Construct the explicit Phase 12 receiving application proof seam."""
    app = create_app()
    app.state.proof_receiving_app_wiring = ProofReceivingAppWiring(
        node_registry=node_registry,
        adapter_registry=adapter_registry,
    )
    return app


app = create_app()
