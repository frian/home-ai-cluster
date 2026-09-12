import asyncio
import struct
import zlib

import pytest
from pydantic import ValidationError

from home_ai_cluster.api.wiring import LocalAppComposition
from home_ai_cluster.core.adapter_execution_contracts import (
    AdapterExecutionContractError,
)
from home_ai_cluster.core.executor import execute_local_routing_decision
from home_ai_cluster.core.local_capability_binding import (
    LocalCapabilityBinding,
    LocalCapabilityBindings,
)
from home_ai_cluster.core.models import (
    INTERNAL_CLUSTER_REQUEST_ADAPTER,
    AdapterHealth,
    Capability,
    ImageGenerationRequest,
    ImageGenerationResult,
    NodeDescription,
    NodeHealth,
)
from home_ai_cluster.core.png_validation import (
    ImageGenerationResultValidationError,
    validate_still_png,
)
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_transport import internal_cluster_request_body
from home_ai_cluster.core.router import route_request
from home_ai_cluster.core.static_capabilities import (
    DEFAULT_STATIC_CAPABILITY_NAMES,
    validate_static_capabilities,
)


def chunk(kind: bytes, payload: bytes, *, valid_crc: bool = True) -> bytes:
    crc = zlib.crc32(kind + payload) & 0xFFFFFFFF
    if not valid_crc:
        crc ^= 1
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", crc)


def png(
    *,
    width: int = 1,
    height: int = 1,
    bit_depth: int = 8,
    color_type: int = 2,
    intent: int = 0,
    filters: list[int] | None = None,
    extra_chunks: list[bytes] | None = None,
    idat_parts: int = 1,
    compressed: bytes | None = None,
) -> bytes:
    channels = 3 if color_type == 2 else 4
    row_bytes = width * channels * (bit_depth // 8)
    raw = b"".join(
        bytes([(filters or [0] * height)[row]]) + bytes(row_bytes)
        for row in range(height)
    )
    compressed = zlib.compress(raw) if compressed is None else compressed
    parts = [
        b"\x89PNG\r\n\x1a\n",
        chunk(
            b"IHDR",
            struct.pack(">IIBBBBB", width, height, bit_depth, color_type, 0, 0, 0),
        ),
        chunk(b"sRGB", bytes([intent])),
    ]
    if extra_chunks:
        parts.extend(extra_chunks)
    split = max(1, len(compressed) // idat_parts)
    parts.extend(
        chunk(b"IDAT", compressed[index : index + split])
        for index in range(0, len(compressed), split)
    )
    parts.append(chunk(b"IEND", b""))
    return b"".join(parts)


def assembled_png(chunks: list[bytes]) -> bytes:
    return b"\x89PNG\r\n\x1a\n" + b"".join(chunks)


def ihdr() -> bytes:
    return chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))


def valid_raw_scanline() -> bytes:
    return b"\0\0\0\0"


class ImageAdapter:
    def __init__(self, capabilities: set[str], result: bytes | None = None) -> None:
        self._capabilities = capabilities
        self.result = result or png()
        self.requests: list[ImageGenerationRequest] = []

    @property
    def name(self) -> str:
        return "image-test"

    def health(self) -> AdapterHealth:
        return AdapterHealth(available=True)

    def capabilities(self) -> list[Capability]:
        return [Capability(name=name) for name in self._capabilities]

    async def generate_image(self, request: ImageGenerationRequest) -> bytes:
        self.requests.append(request)
        return self.result


class MissingImageOperationAdapter(ImageAdapter):
    generate_image = None  # type: ignore[assignment]


def composition(adapter: ImageAdapter) -> tuple[NodeRegistry, AdapterRegistry]:
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
    nodes, adapters = (
        NodeRegistry([node]),
        AdapterRegistry([adapter], local_capability_bindings=bindings),
    )
    LocalAppComposition(node_registry=nodes, adapter_registry=adapters)
    return nodes, adapters


def test_image_request_and_result_are_dedicated_local_models() -> None:
    request = ImageGenerationRequest(instruction="draw a fox")
    result = ImageGenerationResult(image_bytes=b"png", node_id="node")
    assert request.capability.name == "image-generation"
    assert result.image_bytes == b"png" and result.node_id == "node"
    with pytest.raises(ValidationError):
        ImageGenerationRequest(instruction="  ")
    ImageGenerationRequest(instruction="x" * 65_536)
    with pytest.raises(ValidationError):
        ImageGenerationRequest(instruction="x" * 65_537)
    ImageGenerationRequest(instruction="é" * 32_768)
    with pytest.raises(ValidationError):
        ImageGenerationRequest(instruction="é" * 32_768 + "x")


def test_image_only_adapter_is_admitted_and_routed_locally() -> None:
    adapter = ImageAdapter({"image-generation"})
    nodes, adapters = composition(adapter)
    request = ImageGenerationRequest(instruction="one tree")
    decision = route_request(request, nodes, adapters)
    result = asyncio.run(execute_local_routing_decision(request, decision))
    assert adapter.requests == [request]
    assert result.image_bytes == adapter.result
    assert result.node_id == "image-node"


def test_positive_image_claim_requires_image_execution_contract() -> None:
    adapter = MissingImageOperationAdapter({"image-generation"})
    with pytest.raises(AdapterExecutionContractError, match="Image Generation"):
        LocalAppComposition(
            node_registry=NodeRegistry(), adapter_registry=AdapterRegistry([adapter])
        )


def test_image_operation_without_positive_claim_does_not_gain_support() -> None:
    adapter = ImageAdapter(set())
    LocalAppComposition(
        node_registry=NodeRegistry(), adapter_registry=AdapterRegistry([adapter])
    )
    assert adapter.capabilities() == []


@pytest.mark.parametrize("bit_depth,color_type", [(8, 2), (8, 6), (16, 2), (16, 6)])
def test_validator_accepts_each_profile_layout(bit_depth: int, color_type: int) -> None:
    candidate = png(
        width=3,
        height=2,
        bit_depth=bit_depth,
        color_type=color_type,
        filters=[0, 4],
        idat_parts=2,
    )
    assert validate_still_png(candidate) == candidate


@pytest.mark.parametrize("intent", range(4))
def test_validator_accepts_each_srgb_intent(intent: int) -> None:
    assert validate_still_png(png(intent=intent))


@pytest.mark.parametrize(
    "candidate",
    [
        b"not png",
        png(width=0),
        png(height=0),
        png(width=2049),
        png(bit_depth=4),
        png(color_type=0),
        png(extra_chunks=[chunk(b"tEXt", b"x")]),
        png(extra_chunks=[chunk(b"abcd", b"")]),
        png(intent=4),
        png(filters=[5]),
    ],
)
def test_validator_rejects_closed_profile_violations(candidate: bytes) -> None:
    with pytest.raises(ImageGenerationResultValidationError):
        validate_still_png(candidate)


def test_validator_rejects_trailing_bytes_crc_and_unused_zlib_stream() -> None:
    valid = png()
    with pytest.raises(ImageGenerationResultValidationError):
        validate_still_png(valid + b"trailing")
    corrupt = bytearray(valid)
    corrupt[29] ^= 1
    with pytest.raises(ImageGenerationResultValidationError):
        validate_still_png(bytes(corrupt))
    raw = b"\0\0\0\0"
    with pytest.raises(ImageGenerationResultValidationError):
        validate_still_png(png(compressed=zlib.compress(raw) + zlib.compress(raw)))


def test_validator_rejects_truncated_and_wrong_scanline_extent() -> None:
    with pytest.raises(ImageGenerationResultValidationError):
        validate_still_png(png()[:-3])
    with pytest.raises(ImageGenerationResultValidationError):
        validate_still_png(png(compressed=zlib.compress(b"\0\0")))


def test_validator_rejects_truncated_zlib_stream_inside_valid_png_structure() -> None:
    truncated = zlib.compress(valid_raw_scanline())[:-2]
    with pytest.raises(ImageGenerationResultValidationError):
        validate_still_png(png(compressed=truncated))


def test_validator_rejects_excess_inflated_scanline_data() -> None:
    extra_scanline = valid_raw_scanline() + valid_raw_scanline()
    with pytest.raises(ImageGenerationResultValidationError):
        validate_still_png(png(compressed=zlib.compress(extra_scanline)))


@pytest.mark.parametrize(
    "chunks",
    [
        [
            ihdr(),
            chunk(b"sRGB", b"\0"),
            chunk(b"sRGB", b"\0"),
            chunk(b"IDAT", zlib.compress(valid_raw_scanline())),
            chunk(b"IEND", b""),
        ],
        [
            ihdr(),
            chunk(b"sRGB", b"\0\0"),
            chunk(b"IDAT", zlib.compress(valid_raw_scanline())),
            chunk(b"IEND", b""),
        ],
        [
            ihdr(),
            chunk(b"sRGB", b"\0"),
            chunk(b"IDAT", zlib.compress(valid_raw_scanline())),
            chunk(b"IEND", b"not-empty"),
        ],
    ],
)
def test_validator_rejects_duplicate_or_malformed_required_chunks(
    chunks: list[bytes],
) -> None:
    with pytest.raises(ImageGenerationResultValidationError):
        validate_still_png(assembled_png(chunks))


def test_validator_rejects_interrupted_idat_sequence() -> None:
    compressed = zlib.compress(valid_raw_scanline())
    candidate = assembled_png(
        [
            ihdr(),
            chunk(b"sRGB", b"\0"),
            chunk(b"IDAT", compressed[:2]),
            chunk(b"tEXt", b"interruption"),
            chunk(b"IDAT", compressed[2:]),
            chunk(b"IEND", b""),
        ]
    )
    with pytest.raises(ImageGenerationResultValidationError):
        validate_still_png(candidate)


def test_invalid_image_candidate_fails_after_adapter_invocation() -> None:
    adapter = ImageAdapter({"image-generation"}, b"invalid")
    nodes, adapters = composition(adapter)
    request = ImageGenerationRequest(instruction="bad fixture")
    with pytest.raises(ImageGenerationResultValidationError):
        asyncio.run(
            execute_local_routing_decision(
                request, route_request(request, nodes, adapters)
            )
        )
    assert adapter.requests == [request]


def test_image_generation_stays_outside_closed_remote_transport() -> None:
    request = ImageGenerationRequest(instruction="remote is not authorized")
    with pytest.raises(ValidationError):
        INTERNAL_CLUSTER_REQUEST_ADAPTER.validate_python(
            {
                "kind": "image-generation",
                "request": {"instruction": request.instruction},
            }
        )
    with pytest.raises(TypeError, match="Unsupported remote transport request"):
        internal_cluster_request_body(request)  # type: ignore[arg-type]
    assert "image-generation" not in DEFAULT_STATIC_CAPABILITY_NAMES
    with pytest.raises(ValueError, match="unknown test capability"):
        validate_static_capabilities(["image-generation"], subject="test")
