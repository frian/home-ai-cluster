import asyncio
import io
import struct
import zlib

import httpx
import pytest

from home_ai_cluster import local_runtime_composition
from home_ai_cluster.adapters.base import RuntimeAdapterUnavailableError
from home_ai_cluster.api import routes
from home_ai_cluster.api.wiring import (
    LocalAppComposition,
    build_static_remote_collection_wiring,
    build_static_remote_wiring,
)
from home_ai_cluster.commands import image_generation_command
from home_ai_cluster.core.local_capability_binding import (
    LocalCapabilityBinding,
    LocalCapabilityBindings,
)
from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ImageGenerationRequest,
    NodeDescription,
    NodeHealth,
)
from home_ai_cluster.core.orchestrator import ExecutionPermissionDeniedError
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_node import RemoteNodeDeclaration
from home_ai_cluster.core.routing_candidates import RoutingCandidateSelectionMode
from home_ai_cluster.local_runtime_composition import (
    LocalRuntimeCompositionValues,
    create_textual_with_image_generation_companion_composition,
)
from home_ai_cluster.main import create_app, create_receiver_app


def _chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    )


def _png() -> bytes:
    raw = b"\0\0\0\0"
    return b"".join(
        [
            b"\x89PNG\r\n\x1a\n",
            _chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)),
            _chunk(b"IDAT", zlib.compress(raw)),
            _chunk(b"IEND", b""),
        ]
    )


class _ImageAdapter:
    name = "image-test"

    def __init__(self) -> None:
        self.requests: list[ImageGenerationRequest] = []
        self.result = _png()

    def health(self) -> AdapterHealth:
        return AdapterHealth(available=True)

    def capabilities(self) -> list[Capability]:
        return [Capability(name="image-generation")]

    async def generate_image(self, request: ImageGenerationRequest) -> bytes:
        self.requests.append(request)
        return self.result


def _composition(adapter: _ImageAdapter) -> LocalAppComposition:
    return LocalAppComposition(
        node_registry=NodeRegistry(
            [
                NodeDescription(
                    id="image-node",
                    name="Image node",
                    availability="available",
                    health=NodeHealth(healthy=True),
                    capabilities=[Capability(name="image-generation")],
                    adapters=[adapter.name],
                )
            ]
        ),
        adapter_registry=AdapterRegistry(
            [adapter],
            local_capability_bindings=LocalCapabilityBindings(
                [LocalCapabilityBinding(frozenset({"image-generation"}), adapter)]
            ),
        ),
    )


def _post(app, payload: object) -> httpx.Response:
    async def send() -> httpx.Response:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            return await client.post("/v1/image-generation", json=payload)

    return asyncio.run(send())


def test_native_image_generation_returns_exact_validated_png() -> None:
    adapter = _ImageAdapter()
    response = _post(
        create_app(local_app_composition=_composition(adapter)),
        {"instruction": "a fox"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content == adapter.result
    assert adapter.requests == [ImageGenerationRequest(instruction="a fox")]


def test_retained_style_textual_and_image_composition_selects_image_binding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class RecordingStableDiffusionAdapter(_ImageAdapter):
        def __init__(self, base_url: str) -> None:
            super().__init__()
            self.base_url = base_url
            self.name = "stable-diffusion-cpp"

    monkeypatch.setattr(
        local_runtime_composition,
        "StableDiffusionCppAdapter",
        RecordingStableDiffusionAdapter,
    )
    composition = create_textual_with_image_generation_companion_composition(
        LocalRuntimeCompositionValues(runtime="ollama", ollama_model="textual"),
        image_generation_base_url="http://127.0.0.1:7860",
    )
    image_adapter = composition.adapter_registry.bound_adapter_for(
        Capability(name="image-generation")
    )

    response = _post(
        create_app(local_app_composition=composition), {"instruction": "a fox"}
    )

    assert response.status_code == 200
    assert image_adapter.base_url == "http://127.0.0.1:7860"
    assert image_adapter.requests == [ImageGenerationRequest(instruction="a fox")]


@pytest.mark.parametrize(
    "payload",
    [
        {"instruction": "a fox", "seed": 1},
        {"instruction": "   "},
        {"instruction": "é" * 32_769},
    ],
)
def test_native_image_generation_rejects_invalid_public_bodies(payload: object) -> None:
    assert _post(create_app(), payload).status_code == 422


def test_native_image_generation_has_ordinary_no_capability_boundary() -> None:
    response = _post(create_app(), {"instruction": "a fox"})
    assert response.status_code == 404


@pytest.mark.parametrize(
    ("failure", "status_code"),
    [
        (ExecutionPermissionDeniedError(), 409),
        (RuntimeAdapterUnavailableError("unavailable"), 503),
    ],
)
def test_native_image_generation_preserves_ordinary_failure_statuses(
    monkeypatch: pytest.MonkeyPatch, failure: Exception, status_code: int
) -> None:
    async def execute(*args: object, **kwargs: object) -> object:
        raise failure

    monkeypatch.setattr(routes, "handle_static_local_cluster_request", execute)
    response = _post(create_app(), {"instruction": "a fox"})

    assert response.status_code == status_code


def test_receiver_app_does_not_expose_image_generation() -> None:
    assert (
        _post(
            create_receiver_app(local_app_composition=_composition(_ImageAdapter())),
            {"instruction": "a fox"},
        ).status_code
        == 404
    )


class _RemoteTransport:
    def __init__(self) -> None:
        self.calls = 0

    async def send(self, *args: object) -> object:
        self.calls += 1
        raise AssertionError("Image Generation must not use remote transport")


def test_static_caller_local_routing_excludes_physical_image_binding() -> None:
    adapter = _ImageAdapter()
    physical = _composition(adapter)
    transport = _RemoteTransport()
    remote = RemoteNodeDeclaration(
        node=NodeDescription(
            id="remote",
            name="Remote",
            availability="available",
            health=NodeHealth(healthy=True),
            capabilities=[Capability(name="chat")],
            adapters=["remote"],
        ),
        transport_address="http://remote.invalid",
    )
    wiring = build_static_remote_wiring(
        node_registry=NodeRegistry(),
        adapter_registry=physical.adapter_registry,
        remote_declaration=remote,
        remote_transport=transport,
        selection_mode=RoutingCandidateSelectionMode.AUTOMATIC_CAPABILITY,
        execution_intervals=physical.execution_intervals,
    )

    response = _post(
        create_app(local_app_composition=physical, static_remote_wiring=wiring),
        {"instruction": "a fox"},
    )

    assert response.status_code == 404
    assert adapter.requests == []
    assert transport.calls == 0


def test_static_collection_caller_local_routing_excludes_image_binding() -> None:
    adapter = _ImageAdapter()
    physical = _composition(adapter)
    transport = _RemoteTransport()
    wiring = build_static_remote_collection_wiring(
        node_registry=NodeRegistry(),
        adapter_registry=physical.adapter_registry,
        remote_declarations=[
            RemoteNodeDeclaration(
                node=NodeDescription(
                    id="remote",
                    name="Remote",
                    availability="available",
                    health=NodeHealth(healthy=True),
                    capabilities=[Capability(name="chat")],
                    adapters=["remote"],
                ),
                transport_address="http://remote.invalid",
            )
        ],
        remote_transport=transport,
        selection_mode=RoutingCandidateSelectionMode.AUTOMATIC_CAPABILITY,
        execution_intervals=physical.execution_intervals,
    )

    response = _post(
        create_app(
            local_app_composition=physical,
            static_remote_collection_wiring=wiring,
        ),
        {"instruction": "a fox"},
    )

    assert response.status_code == 404
    assert adapter.requests == []
    assert transport.calls == 0


def test_native_image_generation_uses_routable_disconnect_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0
    original = routes.run_routable_execution

    async def recording_boundary(request: object, execution: object) -> object:
        nonlocal calls
        calls += 1
        return await execution()  # type: ignore[operator]

    monkeypatch.setattr(routes, "run_routable_execution", recording_boundary)
    response = _post(
        create_app(local_app_composition=_composition(_ImageAdapter())),
        {"instruction": "a fox"},
    )

    assert response.status_code == 200
    assert calls == 1
    assert routes.run_routable_execution is not original


class _Response:
    def __init__(
        self,
        chunks: list[bytes],
        *,
        status_code: int = 200,
        content_type: str = "image/png",
        content_encoding: str | None = None,
    ) -> None:
        self.chunks = chunks
        self.consumed_chunks = 0
        self.status_code = status_code
        self.headers = {"content-type": content_type}
        if content_encoding is not None:
            self.headers["content-encoding"] = content_encoding

    def __enter__(self):
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def iter_raw(self):
        for chunk in self.chunks:
            self.consumed_chunks += 1
            yield chunk


class _Client:
    def __init__(
        self, response: _Response | Exception, calls: list[tuple[str, object]]
    ) -> None:
        self.response, self.calls = response, calls

    def __enter__(self):
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def stream(self, method: str, url: str, *, json: object) -> _Response:
        self.calls.append((method, url, json))
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


class _ShortWriteOutput:
    def __init__(self, sizes: list[int], *, fail_flush: bool = False) -> None:
        self.sizes = sizes
        self.fail_flush = fail_flush
        self.value = bytearray()
        self.flushes = 0

    def isatty(self) -> bool:
        return False

    def write(self, data: bytes) -> int:
        size = self.sizes.pop(0) if self.sizes else len(data)
        self.value.extend(data[:size])
        return size

    def flush(self) -> None:
        self.flushes += 1
        if self.fail_flush:
            raise OSError("flush failed")


class _PrefixThenFailureOutput(_ShortWriteOutput):
    def write(self, data: bytes) -> int:
        if self.value:
            raise OSError("write failed")
        return super().write(data)


def test_image_generation_command_writes_exact_png_to_non_tty_stdout() -> None:
    output, errors, calls = io.BytesIO(), io.StringIO(), []

    def factory(**kwargs: object) -> _Client:
        assert kwargs == {
            "timeout": 120.0,
            "follow_redirects": False,
            "trust_env": False,
        }
        return _Client(_Response([_png()]), calls)

    image_generation_command.main(
        ["a fox"], _client_factory=factory, _stdout=output, _stderr=errors
    )
    assert output.getvalue() == _png()
    assert errors.getvalue() == ""
    assert calls == [
        (
            "POST",
            "http://127.0.0.1:25042/v1/image-generation",
            {"instruction": "a fox"},
        )
    ]


def test_image_generation_command_acquires_all_streamed_png_chunks() -> None:
    candidate = _png()
    streamed = _Response([candidate[:7], candidate[7:19], candidate[19:]])
    output, errors, calls = io.BytesIO(), io.StringIO(), []

    image_generation_command.main(
        ["a fox"],
        _client_factory=lambda **kwargs: _Client(streamed, calls),
        _stdout=output,
        _stderr=errors,
    )

    assert output.getvalue() == candidate
    assert streamed.consumed_chunks == 3
    assert errors.getvalue() == ""
    assert len(calls) == 1


def test_image_generation_command_stops_streaming_when_bound_is_crossed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    streamed = _Response([b"abc", b"de", b"later"])
    output, errors, calls = io.BytesIO(), io.StringIO(), []
    original = image_generation_command._acquire_png

    def acquire_with_small_test_bound(response: object) -> bytes:
        return original(response, maximum_bytes=4)  # type: ignore[arg-type]

    monkeypatch.setattr(
        image_generation_command, "_acquire_png", acquire_with_small_test_bound
    )
    with pytest.raises(SystemExit) as raised:
        image_generation_command.main(
            ["a fox"],
            _client_factory=lambda **kwargs: _Client(streamed, calls),
            _stdout=output,
            _stderr=errors,
        )

    assert raised.value.code == 1
    assert streamed.consumed_chunks == 2
    assert output.getvalue() == b""
    assert errors.getvalue() == "error: invalid image generation response\n"
    assert len(calls) == 1


def test_streamed_acquisition_does_not_trust_content_length() -> None:
    streamed = _Response([b"abc", b"de", b"later"])
    streamed.headers["content-length"] = "4"

    with pytest.raises(ValueError):
        image_generation_command._acquire_png(streamed, maximum_bytes=4)  # type: ignore[arg-type]

    assert streamed.consumed_chunks == 2


def test_image_generation_command_rejects_encoded_response_before_body_read() -> None:
    streamed = _Response([_png()], content_encoding="gzip")
    output, errors, calls = io.BytesIO(), io.StringIO(), []

    with pytest.raises(SystemExit):
        image_generation_command.main(
            ["a fox"],
            _client_factory=lambda **kwargs: _Client(streamed, calls),
            _stdout=output,
            _stderr=errors,
        )

    assert streamed.consumed_chunks == 0
    assert output.getvalue() == b""
    assert errors.getvalue() == "error: invalid image generation response\n"
    assert len(calls) == 1


def test_image_generation_command_completes_short_writes_and_flushes() -> None:
    output, errors, calls = _ShortWriteOutput([1, 2, 3]), io.StringIO(), []

    image_generation_command.main(
        ["a fox"],
        _client_factory=lambda **kwargs: _Client(_Response([_png()]), calls),
        _stdout=output,
        _stderr=errors,
    )

    assert bytes(output.value) == _png()
    assert output.flushes == 1
    assert errors.getvalue() == ""
    assert len(calls) == 1


def test_image_generation_command_does_not_retry_after_prefix_write_failure() -> None:
    output, errors, calls = _PrefixThenFailureOutput([3]), io.StringIO(), []

    with pytest.raises(SystemExit) as raised:
        image_generation_command.main(
            ["a fox"],
            _client_factory=lambda **kwargs: _Client(_Response([_png()]), calls),
            _stdout=output,
            _stderr=errors,
        )

    assert raised.value.code == 1
    assert bytes(output.value) == _png()[:3]
    assert errors.getvalue() == "error: image generation stdout write failed\n"
    assert len(calls) == 1


def test_image_generation_command_reports_flush_failure_without_retry() -> None:
    output, errors, calls = _ShortWriteOutput([], fail_flush=True), io.StringIO(), []

    with pytest.raises(SystemExit) as raised:
        image_generation_command.main(
            ["a fox"],
            _client_factory=lambda **kwargs: _Client(_Response([_png()]), calls),
            _stdout=output,
            _stderr=errors,
        )

    assert raised.value.code == 1
    assert bytes(output.value) == _png()
    assert output.flushes == 1
    assert errors.getvalue() == "error: image generation stdout write failed\n"
    assert len(calls) == 1


@pytest.mark.parametrize(
    ("argv", "outcome", "expected_requests"),
    [
        (["a fox", "extra"], None, 0),
        (["a fox", "--timeout-seconds", "00"], None, 0),
        (["a fox"], httpx.ConnectError("down"), 1),
        (["a fox"], httpx.ReadTimeout("late"), 1),
        (["a fox"], httpx.RequestError("failed"), 1),
        (["a fox"], _Response([], status_code=422), 1),
        (["a fox"], _Response([], status_code=404), 1),
        (["a fox"], _Response([], status_code=409), 1),
        (["a fox"], _Response([], status_code=503), 1),
        (["a fox"], _Response([], status_code=500), 1),
        (["a fox"], _Response([_png()], content_type="application/json"), 1),
        (["a fox"], _Response([b"not a png"]), 1),
    ],
)
def test_image_generation_command_pre_emission_failures_leave_stdout_empty(
    argv: list[str], outcome: object, expected_requests: int
) -> None:
    output, errors, requests = io.BytesIO(), io.StringIO(), []

    def factory(**kwargs: object) -> _Client:
        assert isinstance(outcome, (_Response, Exception))
        return _Client(outcome, requests)

    with pytest.raises(SystemExit):
        image_generation_command.main(
            argv, _client_factory=factory, _stdout=output, _stderr=errors
        )

    assert output.getvalue() == b""
    assert errors.getvalue().startswith("error: ")
    assert len(requests) == expected_requests


class _TTYOutput(io.BytesIO):
    def isatty(self) -> bool:
        return True


def test_image_generation_command_refuses_tty_before_client_creation() -> None:
    output, errors = _TTYOutput(), io.StringIO()
    with pytest.raises(SystemExit):
        image_generation_command.main(
            ["a fox"],
            _client_factory=lambda **kwargs: pytest.fail("client must not be created"),
            _stdout=output,
            _stderr=errors,
        )
    assert output.getvalue() == b""
    assert errors.getvalue() == "error: image generation requires non-TTY stdout\n"
