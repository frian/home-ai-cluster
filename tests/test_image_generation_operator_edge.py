import asyncio
import io
import struct
import zlib

import httpx
import pytest

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
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_node import RemoteNodeDeclaration
from home_ai_cluster.core.routing_candidates import RoutingCandidateSelectionMode
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
    status_code = 200
    headers = {"content-type": "image/png"}

    def __init__(self, content: bytes) -> None:
        self.content = content


class _Client:
    def __init__(self, response: _Response, calls: list[tuple[str, object]]) -> None:
        self.response, self.calls = response, calls

    def __enter__(self):
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def post(self, url: str, *, json: object) -> _Response:
        self.calls.append((url, json))
        return self.response


def test_image_generation_command_writes_exact_png_to_non_tty_stdout() -> None:
    output, errors, calls = io.BytesIO(), io.StringIO(), []

    def factory(**kwargs: object) -> _Client:
        assert kwargs == {
            "timeout": 120.0,
            "follow_redirects": False,
            "trust_env": False,
        }
        return _Client(_Response(_png()), calls)

    image_generation_command.main(
        ["a fox"], _client_factory=factory, _stdout=output, _stderr=errors
    )
    assert output.getvalue() == _png()
    assert errors.getvalue() == ""
    assert calls == [
        (
            "http://127.0.0.1:25042/v1/image-generation",
            {"instruction": "a fox"},
        )
    ]


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
