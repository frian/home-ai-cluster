"""Explicit orchestration seam for the static two-machine proof."""

from home_ai_cluster.api.wiring import StaticRemoteProofWiring
from home_ai_cluster.core.models import ClusterRequest, ClusterResult
from home_ai_cluster.core.orchestrator import orchestrate_request_with_selected_candidate
from home_ai_cluster.core.routing_candidates import (
    routing_candidates_for_request,
    select_routing_candidate,
)


class NoSelectedStaticProofCandidateError(Exception):
    """Raised when explicit static proof selection yields no candidate."""


async def orchestrate_static_remote_proof(
    request: ClusterRequest,
    wiring: StaticRemoteProofWiring,
) -> ClusterResult:
    """Compose, select, and execute one candidate from explicit proof wiring."""
    candidates = routing_candidates_for_request(
        request,
        wiring.node_registry,
        wiring.adapter_registry,
        wiring.remote_registry,
    )
    selected = select_routing_candidate(candidates, wiring.selection_mode)

    if selected is None:
        raise NoSelectedStaticProofCandidateError(
            "Static remote proof selection produced no routing candidate"
        )

    return await orchestrate_request_with_selected_candidate(
        request,
        selected,
        remote_transport=wiring.remote_transport,
    )
