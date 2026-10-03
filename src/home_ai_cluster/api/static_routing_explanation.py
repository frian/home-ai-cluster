"""Loopback carrier for the active caller's static routing explanation."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, StrictBool, ValidationError

from home_ai_cluster.core.models import Capability
from home_ai_cluster.core.routing_candidates import (
    routing_candidates_for_capability,
    select_automatic_capability_for_capability,
)
from home_ai_cluster.core.static_capabilities import ACCEPTED_CAPABILITY_NAMES

router = APIRouter()


class StaticRoutingExplanationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capability: str
    local_only: StrictBool


@router.post("/diagnostics/static-routing-explanation")
async def static_routing_explanation(http_request: Request) -> dict[str, object]:
    """Project pre-execution facts from this ordinary process's active wiring."""
    try:
        supplied = StaticRoutingExplanationInput.model_validate(
            await http_request.json()
        )
    except (ValueError, ValidationError):
        raise HTTPException(
            status_code=422, detail="Invalid diagnostic input"
        ) from None

    # Keep the public input tied to the accepted vocabulary even if it changes.
    if supplied.capability not in ACCEPTED_CAPABILITY_NAMES:
        raise HTTPException(status_code=422, detail="Invalid diagnostic input")

    try:
        state = http_request.app.state
        if (
            state.static_remote_wiring is not None
            and state.static_remote_collection_wiring is not None
        ):
            raise ValueError("ambiguous active caller wiring")
        wiring = state.static_remote_wiring or state.static_remote_collection_wiring
        if wiring is not None:
            node_registry = wiring.node_registry
            adapter_registry = wiring.adapter_registry
            remote_registry = wiring.remote_registry
        else:
            composition = state.local_app_composition
            if composition is None:
                raise ValueError("active caller composition unavailable")
            node_registry = composition.node_registry
            adapter_registry = composition.adapter_registry
            remote_registry = None

        capability = Capability(name=supplied.capability)
        candidates = routing_candidates_for_capability(
            capability, node_registry, adapter_registry, remote_registry
        )
        selection = select_automatic_capability_for_capability(
            capability, supplied.local_only, candidates
        )
        selected = selection.selected
        initial_selection: dict[str, str] | None = None
        if selected is not None:
            if selected.local is not None:
                initial_selection = {"kind": "local"}
            elif selected.declared_remote is not None:
                initial_selection = {
                    "kind": "declared_remote",
                    "node_id": selected.declared_remote.node.id,
                }
        return {
            "capability": supplied.capability,
            "local_only": supplied.local_only,
            "local_eligible": candidates.local is not None,
            "eligible_remote_node_ids": [
                candidate.node.id for candidate in candidates.declared_remotes
            ],
            "remotes_excluded_by_local_only": (
                selection.explanation.local_only_excluded_declared_remote
            ),
            "initial_selection": initial_selection,
        }
    except Exception:
        raise HTTPException(
            status_code=503, detail="Active routing explanation unavailable"
        ) from None
