import asyncio
import struct
import zlib

import httpx
import pytest
from pydantic import ValidationError

from home_ai_cluster.adapters.base import RuntimeAdapterUnavailableError
from home_ai_cluster.api.wiring import LocalAppComposition
from home_ai_cluster.core.local_capability_binding import (
    LocalCapabilityBinding,
    LocalCapabilityBindings,
)
from home_ai_cluster.core.models import (
    INTERNAL_CLUSTER_REQUEST_ADAPTER,
    AdapterHealth,
    Capability,
    ImageGenerationRequest,
    NodeDescription,
    NodeHealth,
    RequestConstraints,
)
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_node import RemoteNodeDeclaration
from home_ai_cluster.core.remote_transport import (
    HttpRemoteTransport,
    RemoteExecutionPermissionDeniedError,
    RemoteTransportError,
    internal_cluster_request_body,
)
from home_ai_cluster.main import create_receiver_app


def _chunk(kind: bytes, payload: bytes) -> bytes:
    return b"".join(
        [
            struct.pack(">I", len(payload)),
            kind,
            payload,
            struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF),
        ]
    )


def _png(width: int = 1, height: int = 1) -> bytes:
    raw = b"".join(b"\0" + bytes(width * 3) for _ in range(height))
    return b"".join(
        [
            b"\x89PNG\r\n\x1a\n",
            _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)),
            _chunk(b"IDAT", zlib.compress(raw)),
            _chunk(b"IEND", b""),
        ]
    )


class _ImageAdapter:
    name = "image"

    def __init__(self) -> None:
        self.requests: list[ImageGenerationRequest] = []

    def health(self) -> AdapterHealth:
        return AdapterHealth(available=True)

    def capabilities(self) -> list[Capability]:
        return [Capability(name="image-generation")]

    async def generate_image(self, request: ImageGenerationRequest) -> bytes:
        self.requests.append(request)
        return _png(request.width or 1, request.height or 1)


def _composition(adapter: _ImageAdapter) -> LocalAppComposition:
    node = NodeDescription(
        id="receiver-local",
        name="Receiver local",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[Capability(name="image-generation")],
        adapters=[adapter.name],
    )
    return LocalAppComposition(
        node_registry=NodeRegistry([node]),
        adapter_registry=AdapterRegistry(
            [adapter],
            local_capability_bindings=LocalCapabilityBindings(
                [LocalCapabilityBinding(frozenset({"image-generation"}), adapter)]
            ),
        ),
    )


def _declaration() -> RemoteNodeDeclaration:
    return RemoteNodeDeclaration(
        node=NodeDescription(
            id="declared-remote",
            name="Declared remote",
            availability="available",
            health=NodeHealth(healthy=True),
            capabilities=[Capability(name="chat")],
            adapters=["unknown"],
        ),
        transport_address="http://remote.test",
    )


def _request(**values: object) -> ImageGenerationRequest:
    return ImageGenerationRequest(instruction="draw a fox", **values)


def _post_receiver(app, payload: dict[str, object]) -> httpx.Response:
    async def send() -> httpx.Response:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://receiver"
        ) as client:
            return await client.post("/internal/cluster/request", json=payload)

    return asyncio.run(send())


def test_internal_image_envelope_round_trips_exact_dimensions_and_constraints() -> None:
    request = _request(
        width=64,
        height=65,
        constraints=RequestConstraints(local_only=False, min_context_size=9),
    )
    body = internal_cluster_request_body(request)

    assert body == {
        "kind": "image-generation",
        "request": {
            "instruction": "draw a fox",
            "width": 64,
            "height": 65,
            "constraints": {
                "local_only": False,
                "prefer_fast_response": False,
                "min_context_size": 9,
            },
        },
    }
    assert (
        INTERNAL_CLUSTER_REQUEST_ADAPTER.validate_python(
            body
        ).request.normalized_request()
        == request
    )


def test_internal_image_envelope_accepts_instruction_only_shape() -> None:
    envelope = INTERNAL_CLUSTER_REQUEST_ADAPTER.validate_python(
        {"kind": "image-generation", "request": {"instruction": "fox"}}
    )

    assert envelope.request.normalized_request() == ImageGenerationRequest(
        instruction="fox"
    )


@pytest.mark.parametrize(
    "body",
    [
        {
            "kind": "image-generation",
            "request": {"instruction": "fox", "width": 64},
        },
        {
            "kind": "image-generation",
            "request": {"instruction": "fox", "height": 64},
        },
        {
            "kind": "image-generation",
            "request": {"instruction": "fox", "width": None, "height": 64},
        },
        {
            "kind": "image-generation",
            "request": {"instruction": "fox", "width": 64, "height": None},
        },
        {
            "kind": "image-generation",
            "request": {"instruction": "fox", "width": None, "height": None},
        },
        {
            "kind": "image-generation",
            "request": {
                "instruction": "fox",
                "width": 64,
                "height": 64,
                "constraints": {"local_only": True, "unknown": True},
            },
        },
    ],
)
def test_internal_image_envelope_rejects_invalid_or_unknown_data(
    body: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        INTERNAL_CLUSTER_REQUEST_ADAPTER.validate_python(body)


def test_receiver_executes_internal_image_locally_and_returns_raw_png() -> None:
    adapter = _ImageAdapter()
    request = _request(
        width=64, height=64, constraints=RequestConstraints(local_only=False)
    )
    response = _post_receiver(
        create_receiver_app(local_app_composition=_composition(adapter)),
        internal_cluster_request_body(request),
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content == _png(64, 64)
    assert adapter.requests == [request]


def test_receiver_rejects_asymmetric_internal_geometry_before_adapter_execution() -> (
    None
):
    adapter = _ImageAdapter()
    response = _post_receiver(
        create_receiver_app(local_app_composition=_composition(adapter)),
        {
            "kind": "image-generation",
            "request": {"instruction": "fox", "height": 64},
        },
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid internal cluster request"}
    assert adapter.requests == []


async def _send_image(response: httpx.Response, request: ImageGenerationRequest):
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: response)
    ) as client:
        return await HttpRemoteTransport(client).send(request, _declaration())


def test_remote_image_transport_requires_exact_png_success_and_attributes() -> None:
    result = asyncio.run(
        _send_image(
            httpx.Response(200, content=_png(), headers={"content-type": "image/png"}),
            _request(),
        )
    )

    assert result.image_bytes == _png()
    assert result.node_id == "declared-remote"


@pytest.mark.parametrize("status", [201, 202, 204, 206])
def test_remote_image_transport_rejects_non_200_even_with_valid_png(
    status: int,
) -> None:
    with pytest.raises(RemoteTransportError):
        asyncio.run(
            _send_image(
                httpx.Response(
                    status, content=_png(), headers={"content-type": "image/png"}
                ),
                _request(),
            )
        )


@pytest.mark.parametrize("media_type", ["application/json", "text/plain", ""])
def test_remote_image_transport_requires_image_png_media_type(media_type: str) -> None:
    with pytest.raises(RemoteTransportError):
        asyncio.run(
            _send_image(
                httpx.Response(
                    200, content=_png(), headers={"content-type": media_type}
                ),
                _request(),
            )
        )


@pytest.mark.parametrize("candidate", [b"not png", _png() + b"trailing"])
def test_remote_image_transport_revalidates_complete_png(candidate: bytes) -> None:
    with pytest.raises(RemoteTransportError):
        asyncio.run(
            _send_image(
                httpx.Response(
                    200, content=candidate, headers={"content-type": "image/png"}
                ),
                _request(),
            )
        )


def test_remote_image_transport_rejects_wrong_requested_geometry() -> None:
    with pytest.raises(RemoteTransportError):
        asyncio.run(
            _send_image(
                httpx.Response(
                    200, content=_png(65, 64), headers={"content-type": "image/png"}
                ),
                _request(width=64, height=64),
            )
        )


@pytest.mark.parametrize(
    ("body", "recognized"),
    [
        (b'{"detail":"execution-permission-denied"}', True),
        (b'{"detail":"other"}', False),
        (b'{"detail":"x","detail":"execution-permission-denied"}', False),
    ],
)
def test_remote_image_transport_recognizes_only_exact_bounded_permission_refusal(
    body: bytes, recognized: bool
) -> None:
    response = httpx.Response(409, content=body)
    if recognized:
        with pytest.raises(RemoteExecutionPermissionDeniedError):
            asyncio.run(_send_image(response, _request()))
    else:
        with pytest.raises(RemoteTransportError):
            asyncio.run(_send_image(response, _request()))


def test_remote_image_transport_rejects_refusal_beyond_its_bounded_envelope() -> None:
    body = b" " * 1_024 + b'{"detail":"execution-permission-denied"}'
    with pytest.raises(RemoteTransportError):
        asyncio.run(_send_image(httpx.Response(409, content=body), _request()))


def test_remote_image_transport_preserves_503_without_reading_diagnostics() -> None:
    with pytest.raises(
        RuntimeAdapterUnavailableError, match="Runtime adapter unavailable"
    ):
        asyncio.run(
            _send_image(httpx.Response(503, content=b"private diagnostic"), _request())
        )
