"""Private, bounded facts for one explicitly explained ordinary request."""

from dataclasses import dataclass, field

from home_ai_cluster.core.routing_candidates import (
    AutomaticCapabilitySelectionExplanation,
)


@dataclass
class OrdinaryRequestLifecycle:
    """Request-local facts written only by ordinary fallback control flow."""

    selection: AutomaticCapabilitySelectionExplanation | None = None
    candidates: list[dict[str, str]] = field(default_factory=list)
    continuation_reasons: list[dict[str, str]] = field(default_factory=list)
    final_node_id: str | None = None

    def selected(self, explanation: AutomaticCapabilitySelectionExplanation) -> None:
        self.selection = explanation

    def local_permission(self, granted: bool, node_id: str) -> None:
        self.candidates.append(
            {
                "family": "local",
                "node_id": node_id,
                "fact": "execution-permission-granted"
                if granted
                else "execution-permission-denied",
            }
        )

    def local_adapter_invoked(self, node_id: str) -> None:
        self.candidates.append(
            {"family": "local", "node_id": node_id, "fact": "adapter-invoked"}
        )

    def remote_transport_invoked(self, node_id: str) -> None:
        self.candidates.append(
            {
                "family": "declared-remote",
                "node_id": node_id,
                "fact": "transport-invoked",
            }
        )

    def remote_refused(self, node_id: str) -> None:
        self.candidates.append(
            {
                "family": "declared-remote",
                "node_id": node_id,
                "fact": "execution-permission-refused",
            }
        )

    def continued(self, node_id: str, reason: str) -> None:
        self.continuation_reasons.append({"node_id": node_id, "reason": reason})

    def succeeded(self, node_id: str) -> None:
        self.final_node_id = node_id
