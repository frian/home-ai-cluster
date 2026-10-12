"""Native carrier for RFC-0144 caller-routable capability projection."""

from fastapi import APIRouter, HTTPException, Request

from home_ai_cluster.core.caller_routable_capabilities import (
    project_caller_routable_capabilities,
)
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_node import RemoteNodeDeclarationRegistry

router = APIRouter()


def _active_projection_inputs(
    request: Request,
) -> tuple[NodeRegistry, AdapterRegistry, RemoteNodeDeclarationRegistry | None]:
    """Return the active caller composition without reconstructing it."""
    state = request.app.state
    if (
        state.static_remote_wiring is not None
        and state.static_remote_collection_wiring is not None
    ):
        raise ValueError("ambiguous active caller wiring")
    wiring = state.static_remote_wiring or state.static_remote_collection_wiring
    if wiring is not None:
        return wiring.node_registry, wiring.adapter_registry, wiring.remote_registry

    composition = state.local_app_composition
    if composition is None:
        raise ValueError("active caller composition unavailable")
    return composition.node_registry, composition.adapter_registry, None


@router.get("/diagnostics/caller-routable-capabilities")
def caller_routable_capabilities(request: Request) -> dict[str, list[str]]:
    """Return the active ordinary routing surface's accepted capabilities."""
    try:
        node_registry, adapter_registry, remote_registry = _active_projection_inputs(
            request
        )
        capabilities = project_caller_routable_capabilities(
            node_registry, adapter_registry, remote_registry
        )
        return {"capabilities": list(capabilities)}
    except Exception:
        raise HTTPException(
            status_code=503, detail="Caller routable capabilities unavailable"
        ) from None
