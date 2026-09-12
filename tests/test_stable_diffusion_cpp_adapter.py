import asyncio
import base64
import json
import struct
import zlib

import httpx
import pytest

from home_ai_cluster.adapters.base import (
    ImageGenerationExecutionAdapter,
    RuntimeAdapterUnavailableError,
    RuntimeConnectionUnavailableBeforeRequestError,
)
from home_ai_cluster.adapters.stable_diffusion_cpp import (
    _MAX_ENCODED_RESULT_BASE64_BYTES,
    StableDiffusionCppAdapter,
    _normalize_runtime_png,
)
from home_ai_cluster.api.wiring import LocalAppComposition
from home_ai_cluster.core.executor import execute_local_routing_decision
from home_ai_cluster.core.local_capability_binding import (
    LocalCapabilityBinding,
    LocalCapabilityBindings,
)
from home_ai_cluster.core.models import (
    Capability,
    ImageGenerationRequest,
    NodeDescription,
    NodeHealth,
)
from home_ai_cluster.core.png_validation import validate_still_png
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.router import route_request


def png_chunk(kind: bytes, payload: bytes, *, valid_crc: bool = True) -> bytes:
    crc = zlib.crc32(kind + payload) & 0xFFFFFFFF
    if not valid_crc:
        crc ^= 1
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", crc)


def runtime_png(
    *,
    include_srgb: bool = True,
    color_type: int = 2,
    width: int = 1,
    height: int = 1,
    interlace: int = 0,
    extra_chunks: list[bytes] | None = None,
) -> bytes:
    channels = 3 if color_type == 2 else 4
    raw = b"".join(b"\0" + bytes(width * channels) for _ in range(height))
    chunks = [
        png_chunk(
            b"IHDR",
            struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, interlace),
        )
    ]
    if include_srgb:
        chunks.append(png_chunk(b"sRGB", b"\0"))
    if extra_chunks:
        chunks.extend(extra_chunks)
    chunks.extend([png_chunk(b"IDAT", zlib.compress(raw)), png_chunk(b"IEND", b"")])
    return b"\x89PNG\r\n\x1a\n" + b"".join(chunks)


def completed_body(image: bytes, *, images: int = 1) -> dict[str, object]:
    encoded = base64.b64encode(image).decode("ascii")
    return {
        "id": "job_1",
        "status": "completed",
        "result": {
            "output_format": "png",
            "images": [
                {"index": index, "b64_json": encoded} for index in range(images)
            ],
        },
    }


def successful_transport(
    captured: list[httpx.Request], image: bytes, *, queued: bool = False
) -> httpx.MockTransport:
    poll_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal poll_count
        captured.append(request)
        if request.url.path == "/sdcpp/v1/img_gen":
            return httpx.Response(202, json={"id": "job_1", "status": "queued"})
        assert request.url.path == "/sdcpp/v1/jobs/job_1"
        poll_count += 1
        if queued and poll_count == 1:
            return httpx.Response(200, json={"id": "job_1", "status": "generating"})
        return httpx.Response(200, json=completed_body(image))

    return httpx.MockTransport(handler)


def test_image_only_identity_and_contract() -> None:
    adapter = StableDiffusionCppAdapter(base_url="http://127.0.0.1:7860")
    assert adapter.name == "stable-diffusion-cpp"
    assert adapter.capabilities() == [Capability(name="image-generation")]
    assert isinstance(adapter, ImageGenerationExecutionAdapter)
    assert not any(hasattr(adapter, name) for name in ("chat", "summarize", "classify"))


@pytest.mark.parametrize(
    "url",
    [
        "https://127.0.0.1:7860",
        "http://192.168.1.2:7860",
        "http://example.com:7860",
        "http://127.0.0.1:7860/path",
        "http://127.0.0.1:7860?query=x",
        "http://user@127.0.0.1:7860",
    ],
)
def test_runtime_origin_rejects_non_origin_or_non_loopback_urls(url: str) -> None:
    with pytest.raises(Exception, match="absolute loopback http"):
        StableDiffusionCppAdapter(base_url=url)


def test_health_uses_native_readiness_and_no_environment_trust(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options: list[dict[str, object]] = []
    original = httpx.Client

    def create_client(**kwargs: object) -> httpx.Client:
        options.append(kwargs)
        return original(**kwargs)

    monkeypatch.setattr(
        "home_ai_cluster.adapters.stable_diffusion_cpp.httpx.Client", create_client
    )
    adapter = StableDiffusionCppAdapter(
        base_url="http://127.0.0.1:7860",
        transport=httpx.MockTransport(lambda request: httpx.Response(200)),
    )
    assert adapter.health().available
    assert options == [
        {
            "base_url": "http://127.0.0.1:7860",
            "transport": adapter._transport,
            "trust_env": False,
        }
    ]


def test_native_submission_is_literal_private_and_exactly_one_image(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests: list[httpx.Request] = []
    options: list[dict[str, object]] = []
    original = httpx.AsyncClient

    def create_client(**kwargs: object) -> httpx.AsyncClient:
        options.append(kwargs)
        return original(**kwargs)

    monkeypatch.setattr(
        "home_ai_cluster.adapters.stable_diffusion_cpp.httpx.AsyncClient", create_client
    )
    instruction = 'draw <sd_cpp_extra_args>{"seed":2}</sd_cpp_extra_args>'
    image = runtime_png()
    adapter = StableDiffusionCppAdapter(
        base_url="http://127.0.0.1:7860",
        transport=successful_transport(requests, image),
    )
    assert asyncio.run(
        adapter.generate_image(ImageGenerationRequest(instruction=instruction))
    )
    assert requests[0].url.path == "/sdcpp/v1/img_gen"
    assert all(request.url.path != "/v1/images/generations" for request in requests)
    assert json.loads(requests[0].content) == {
        "prompt": instruction,
        "batch_count": 1,
        "embed_image_metadata": False,
        "output_format": "png",
    }
    assert options == [
        {
            "base_url": "http://127.0.0.1:7860",
            "transport": adapter._transport,
            "timeout": None,
            "trust_env": False,
        }
    ]


def test_native_job_polling_and_ordinary_local_vertical() -> None:
    requests: list[httpx.Request] = []
    adapter = StableDiffusionCppAdapter(
        base_url="http://127.0.0.1:7860",
        transport=successful_transport(
            requests,
            runtime_png(extra_chunks=[png_chunk(b"tEXt", b"model=private")]),
            queued=True,
        ),
    )
    bindings = LocalCapabilityBindings(
        [LocalCapabilityBinding(frozenset({"image-generation"}), adapter)]
    )
    node = NodeDescription(
        id="image-node",
        name="Image",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[Capability(name="image-generation")],
        adapters=[adapter.name],
    )
    nodes = NodeRegistry([node])
    adapters = AdapterRegistry([adapter], local_capability_bindings=bindings)
    LocalAppComposition(node_registry=nodes, adapter_registry=adapters)
    request = ImageGenerationRequest(instruction="a local tree")
    result = asyncio.run(
        execute_local_routing_decision(request, route_request(request, nodes, adapters))
    )
    assert result.node_id == "image-node"
    assert validate_still_png(result.image_bytes) == result.image_bytes
    assert b"tEXt" not in result.image_bytes
    assert [request.url.path for request in requests] == [
        "/sdcpp/v1/img_gen",
        "/sdcpp/v1/jobs/job_1",
        "/sdcpp/v1/jobs/job_1",
    ]


@pytest.mark.parametrize(
    "submission, poll, error",
    [
        ({}, None, RuntimeAdapterUnavailableError),
        ({"id": "bad/id"}, None, RuntimeAdapterUnavailableError),
        ({"id": "job_1"}, {"status": "mystery"}, RuntimeAdapterUnavailableError),
        ({"id": "job_1"}, {"status": "failed"}, RuntimeAdapterUnavailableError),
        (
            {"id": "job_1"},
            {"status": "completed", "result": {}},
            RuntimeAdapterUnavailableError,
        ),
    ],
)
def test_malformed_or_terminal_native_job_results_fail_closed(
    submission: dict[str, object],
    poll: dict[str, object] | None,
    error: type[Exception],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            202 if request.url.path.endswith("img_gen") else 200,
            json=submission if request.url.path.endswith("img_gen") else poll,
        )

    adapter = StableDiffusionCppAdapter(
        base_url="http://127.0.0.1:7860", transport=httpx.MockTransport(handler)
    )
    with pytest.raises(error):
        asyncio.run(adapter.generate_image(ImageGenerationRequest(instruction="x")))


def test_pre_submission_connection_error_is_distinct_from_post_submission_error() -> (
    None
):
    def initial_failure(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down", request=request)

    initial = StableDiffusionCppAdapter(
        base_url="http://127.0.0.1:7860", transport=httpx.MockTransport(initial_failure)
    )
    with pytest.raises(RuntimeConnectionUnavailableBeforeRequestError):
        asyncio.run(initial.generate_image(ImageGenerationRequest(instruction="x")))

    def polling_failure(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("img_gen"):
            return httpx.Response(202, json={"id": "job_1"})
        raise httpx.ConnectError("down", request=request)

    engaged = StableDiffusionCppAdapter(
        base_url="http://127.0.0.1:7860", transport=httpx.MockTransport(polling_failure)
    )
    with pytest.raises(RuntimeAdapterUnavailableError) as exc_info:
        asyncio.run(engaged.generate_image(ImageGenerationRequest(instruction="x")))
    assert not isinstance(
        exc_info.value, RuntimeConnectionUnavailableBeforeRequestError
    )


def test_non_success_native_response_is_an_adapter_unavailable_failure() -> None:
    adapter = StableDiffusionCppAdapter(
        base_url="http://127.0.0.1:7860",
        transport=httpx.MockTransport(lambda request: httpx.Response(429)),
    )
    with pytest.raises(RuntimeAdapterUnavailableError):
        asyncio.run(adapter.generate_image(ImageGenerationRequest(instruction="x")))


@pytest.mark.parametrize(
    "source",
    [
        runtime_png(include_srgb=False),
        runtime_png(color_type=0),
        runtime_png(interlace=1),
        runtime_png(width=2049),
        b"not a PNG",
    ],
)
def test_normalization_rejects_untagged_or_unsupported_runtime_pngs(
    source: bytes,
) -> None:
    with pytest.raises(ValueError):
        _normalize_runtime_png(source)


def test_normalization_rejects_source_crc_corruption_and_strips_metadata() -> None:
    source = runtime_png(extra_chunks=[png_chunk(b"tEXt", b"parameters=private")])
    candidate = _normalize_runtime_png(source)
    assert validate_still_png(candidate) == candidate
    assert b"tEXt" not in candidate and candidate.endswith(png_chunk(b"IEND", b""))
    corrupted = bytearray(source)
    corrupted[29] ^= 1
    with pytest.raises(ValueError):
        _normalize_runtime_png(bytes(corrupted))


def test_invalid_base64_oversized_and_multiple_runtime_results_fail_closed() -> None:
    malformed = {
        "id": "job_1",
        "status": "completed",
        "result": {"output_format": "png", "images": [{"b64_json": "*"}]},
    }
    oversized = {
        "id": "job_1",
        "status": "completed",
        "result": {
            "output_format": "png",
            "images": [{"b64_json": "A" * (_MAX_ENCODED_RESULT_BASE64_BYTES + 1)}],
        },
    }
    multiple = completed_body(runtime_png(), images=2)
    for body in (malformed, oversized, multiple):
        responses = iter([{"id": "job_1"}, body])

        def handler(
            request: httpx.Request, response_iterator: object = responses
        ) -> httpx.Response:
            return httpx.Response(
                202 if request.url.path.endswith("img_gen") else 200,
                json=next(response_iterator),  # type: ignore[arg-type]
            )

        adapter = StableDiffusionCppAdapter(
            base_url="http://127.0.0.1:7860", transport=httpx.MockTransport(handler)
        )
        with pytest.raises(RuntimeAdapterUnavailableError):
            asyncio.run(adapter.generate_image(ImageGenerationRequest(instruction="x")))
