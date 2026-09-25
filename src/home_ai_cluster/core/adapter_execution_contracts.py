"""Project-owned executable-admission checks for runtime adapters."""

from collections.abc import Iterable

from home_ai_cluster.adapters.base import (
    ChatExecutionAdapter,
    ClassifyExecutionAdapter,
    ImageGenerationExecutionAdapter,
    RuntimeAdapter,
    SummarizeExecutionAdapter,
)


class AdapterExecutionContractError(ValueError):
    """Raised when a positive adapter capability claim lacks its execution contract."""


def validate_adapter_execution_contracts(
    adapters: Iterable[RuntimeAdapter],
) -> None:
    """Require each positive capability claim to have HAC's execution contract."""
    for adapter in adapters:
        capability_names = {capability.name for capability in adapter.capabilities()}
        if capability_names & {"chat", "code"} and not isinstance(
            adapter, ChatExecutionAdapter
        ):
            raise AdapterExecutionContractError(
                f"Adapter {adapter.name} claims chat-shaped execution without Chat"
            )
        if "summarize" in capability_names and not isinstance(
            adapter, SummarizeExecutionAdapter
        ):
            raise AdapterExecutionContractError(
                f"Adapter {adapter.name} claims summarize without Summarize"
            )
        if "classify" in capability_names and not isinstance(
            adapter, ClassifyExecutionAdapter
        ):
            raise AdapterExecutionContractError(
                f"Adapter {adapter.name} claims classify without Classify"
            )
        if "image-generation" in capability_names and not isinstance(
            adapter, ImageGenerationExecutionAdapter
        ):
            raise AdapterExecutionContractError(
                "Adapter "
                f"{adapter.name} claims image-generation without Image Generation"
            )
