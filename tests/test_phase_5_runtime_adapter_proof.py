import argparse
import asyncio

import pytest

from home_ai_cluster.adapters.base import (
    RuntimeAdapterUnavailableError,
)
from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ClusterRequest,
    RuntimeResult,
)
from home_ai_cluster.phase_5_runtime_adapter_proof import (
    create_request,
    local_http_url,
    parse_args,
    result_summary,
    run_proof,
    selected_adapters,
)


class RecordingAdapter:
    def __init__(
        self,
        name: str,
        result: RuntimeResult | None = None,
        error: RuntimeAdapterUnavailableError | None = None,
    ) -> None:
        self._name = name
        self._result = result or RuntimeResult(
            content="ready",
            adapter=name,
            model="proof-model",
        )
        self._error = error
        self.requests: list[ClusterRequest] = []

    @property
    def name(self) -> str:
        return self._name

    def health(self) -> AdapterHealth:
        return AdapterHealth(available=True)

    def capabilities(self) -> list[Capability]:
        return [Capability(name="chat")]

    async def chat(self, request: ClusterRequest) -> RuntimeResult:
        self.requests.append(request)
        if self._error is not None:
            raise self._error
        return self._result


def test_parse_args_defaults_to_loopback_runtime_configuration() -> None:
    args = parse_args([])

    assert args.adapter is None
    assert args.ollama_base_url == "http://127.0.0.1:11434"
    assert args.ollama_model == "llama3.2"
    assert args.llama_server_base_url == "http://127.0.0.1:8080"
    assert args.llama_server_model == "phase-5-gemma"


def test_local_http_url_rejects_non_loopback_url() -> None:
    with pytest.raises(argparse.ArgumentTypeError):
        local_http_url("http://example.test:8080")


def test_selected_adapters_defaults_to_both_explicit_adapters() -> None:
    ollama = RecordingAdapter("ollama")
    llama_server = RecordingAdapter("llama-server")

    selected = selected_adapters(
        {"ollama": ollama, "llama-server": llama_server},
        None,
    )

    assert selected == [ollama, llama_server]


def test_result_summary_contains_only_normalized_proof_fields() -> None:
    summary = result_summary(
        RuntimeResult(content="ready", adapter="llama-server", model="phase-5-gemma")
    )

    assert summary == {
        "adapter": "llama-server",
        "model": "phase-5-gemma",
        "content_length": 5,
    }
    assert "content" not in summary
    assert "node_id" not in summary


def test_run_proof_executes_adapters_through_shared_boundary() -> None:
    outputs: list[str] = []
    ollama = RecordingAdapter("ollama")
    llama_server = RecordingAdapter("llama-server")

    exit_code = asyncio.run(
        run_proof([ollama, llama_server], create_request(), output=outputs.append)
    )

    assert exit_code == 0
    assert len(ollama.requests) == 1
    assert len(llama_server.requests) == 1
    assert outputs == [
        '{"adapter": "ollama", "content_length": 5, "model": "proof-model"}',
        '{"adapter": "llama-server", "content_length": 5, "model": "proof-model"}',
    ]


def test_run_proof_reports_only_cluster_owned_unavailable_error() -> None:
    outputs: list[str] = []
    error = RuntimeAdapterUnavailableError("runtime-specific details")
    adapter = RecordingAdapter("llama-server", error=error)

    exit_code = asyncio.run(
        run_proof([adapter], create_request(), output=outputs.append)
    )

    assert exit_code == 1
    assert outputs == [
        '{"adapter": "llama-server", "error": "RuntimeAdapterUnavailableError"}'
    ]
