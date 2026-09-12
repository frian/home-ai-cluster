"""Private native stable-diffusion.cpp image-generation adapter."""

import asyncio
import base64
import binascii
import struct
import zlib
from typing import Any

import httpx

from home_ai_cluster.adapters.base import (
    RuntimeAdapterUnavailableError,
    RuntimeConnectionUnavailableBeforeRequestError,
)
from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ImageGenerationRequest,
)
from home_ai_cluster.core.png_validation import MAX_ENCODED_PNG_BYTES, PNG_SIGNATURE
from home_ai_cluster.local_http import local_http_url

_POLL_INTERVAL_SECONDS = 0.05
_MAX_ENCODED_RESULT_BASE64_BYTES = 4 * ((MAX_ENCODED_PNG_BYTES + 2) // 3)
_JOB_ID_CHARACTERS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
)


class StableDiffusionCppAdapter:
    """One explicitly supplied operator-managed local ``sd-server`` origin."""

    def __init__(
        self,
        *,
        base_url: str,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = local_http_url(base_url)
        self._transport = transport

    @property
    def name(self) -> str:
        return "stable-diffusion-cpp"

    def capabilities(self) -> list[Capability]:
        return [Capability(name="image-generation")]

    def health(self) -> AdapterHealth:
        try:
            with httpx.Client(
                base_url=self.base_url,
                transport=self._transport,
                trust_env=False,
            ) as client:
                response = client.get("/sdcpp/v1/capabilities")
                response.raise_for_status()
        except httpx.HTTPError as exc:
            return AdapterHealth(available=False, reason=str(exc))
        return AdapterHealth(available=True)

    async def generate_image(self, request: ImageGenerationRequest) -> bytes:
        """Submit, await, and normalize exactly one native image-generation job."""
        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                transport=self._transport,
                timeout=None,
                trust_env=False,
            ) as client:
                job_id = await self._submit_image_generation(client, request)
                native_image = await self._await_image_result(client, job_id)
        except RuntimeAdapterUnavailableError:
            raise
        except httpx.ConnectError as exc:
            raise RuntimeAdapterUnavailableError("Runtime adapter unavailable") from exc
        except httpx.HTTPError as exc:
            raise RuntimeAdapterUnavailableError("Runtime adapter unavailable") from exc

        try:
            return _normalize_runtime_png(native_image)
        except ValueError as exc:
            raise RuntimeAdapterUnavailableError("Runtime adapter unavailable") from exc

    async def _submit_image_generation(
        self,
        client: httpx.AsyncClient,
        request: ImageGenerationRequest,
    ) -> str:
        try:
            response = await client.post(
                "/sdcpp/v1/img_gen",
                json={
                    "prompt": request.instruction,
                    "batch_count": 1,
                    "embed_image_metadata": False,
                    "output_format": "png",
                },
            )
            response.raise_for_status()
        except httpx.ConnectError as exc:
            raise RuntimeConnectionUnavailableBeforeRequestError(
                "Runtime connection unavailable before request transmission",
            ) from exc
        except httpx.HTTPError as exc:
            raise RuntimeAdapterUnavailableError("Runtime adapter unavailable") from exc

        try:
            body = response.json()
            job_id = body["id"]
            if (
                not isinstance(job_id, str)
                or not job_id
                or not set(job_id) <= _JOB_ID_CHARACTERS
            ):
                raise ValueError("invalid native job id")
            return job_id
        except (TypeError, ValueError, KeyError) as exc:
            raise RuntimeAdapterUnavailableError("Runtime adapter unavailable") from exc

    async def _await_image_result(
        self, client: httpx.AsyncClient, job_id: str
    ) -> bytes:
        while True:
            try:
                response = await client.get(f"/sdcpp/v1/jobs/{job_id}")
                response.raise_for_status()
                body = response.json()
                status = body["status"]
            except (httpx.HTTPError, TypeError, ValueError, KeyError) as exc:
                raise RuntimeAdapterUnavailableError(
                    "Runtime adapter unavailable"
                ) from exc

            if status in {"queued", "generating"}:
                await asyncio.sleep(_POLL_INTERVAL_SECONDS)
                continue
            if status == "completed":
                return _completed_native_image(body)
            if status in {"failed", "cancelled"}:
                raise RuntimeAdapterUnavailableError("Runtime adapter unavailable")
            raise RuntimeAdapterUnavailableError("Runtime adapter unavailable")


def _completed_native_image(body: Any) -> bytes:
    """Extract one bounded PNG result from a completed native job response."""
    try:
        result = body["result"]
        images = result["images"]
        if (
            result["output_format"] != "png"
            or not isinstance(images, list)
            or len(images) != 1
        ):
            raise ValueError("invalid native image result")
        encoded = images[0]["b64_json"]
        if (
            not isinstance(encoded, str)
            or len(encoded) > _MAX_ENCODED_RESULT_BASE64_BYTES
        ):
            raise ValueError("invalid native image result")
        decoded = base64.b64decode(encoded.encode("ascii"), validate=True)
        if len(decoded) > MAX_ENCODED_PNG_BYTES:
            raise ValueError("native image result exceeds maximum size")
        return decoded
    except (
        IndexError,
        UnicodeEncodeError,
        binascii.Error,
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        raise RuntimeAdapterUnavailableError("Runtime adapter unavailable") from exc


def _normalize_runtime_png(source: bytes) -> bytes:
    """Keep one structurally compatible, truthfully identified PNG image only."""
    if len(source) > MAX_ENCODED_PNG_BYTES or not source.startswith(PNG_SIGNATURE):
        raise ValueError("invalid runtime PNG")

    offset = len(PNG_SIGNATURE)
    ihdr: bytes | None = None
    srgb: bytes | None = None
    idat_parts: list[bytes] = []
    seen_idat = False
    seen_iend = False

    while offset < len(source):
        if len(source) - offset < 12:
            raise ValueError("truncated runtime PNG chunk")
        length, kind = struct.unpack_from(">I4s", source, offset)
        offset += 8
        if length > len(source) - offset - 4:
            raise ValueError("truncated runtime PNG chunk body")
        payload = source[offset : offset + length]
        expected_crc = struct.unpack_from(">I", source, offset + length)[0]
        if zlib.crc32(kind + payload) & 0xFFFFFFFF != expected_crc:
            raise ValueError("invalid runtime PNG chunk CRC")
        offset += length + 4

        if kind == b"IHDR":
            if ihdr is not None or offset != len(PNG_SIGNATURE) + 25 or length != 13:
                raise ValueError("invalid runtime PNG IHDR")
            _validate_runtime_ihdr(payload)
            ihdr = payload
        elif kind == b"sRGB":
            if (
                ihdr is None
                or seen_idat
                or srgb is not None
                or length != 1
                or payload[0] > 3
            ):
                raise ValueError("invalid runtime PNG sRGB")
            srgb = payload
        elif kind == b"IDAT":
            if ihdr is None or srgb is None or seen_iend:
                raise ValueError("invalid runtime PNG IDAT")
            seen_idat = True
            idat_parts.append(payload)
        elif kind == b"IEND":
            if length != 0 or not seen_idat or seen_iend or offset != len(source):
                raise ValueError("invalid runtime PNG IEND")
            seen_iend = True
        elif kind[0] & 0x20 == 0:
            raise ValueError("unsupported runtime PNG critical chunk")

    if ihdr is None or srgb is None or not idat_parts or not seen_iend:
        raise ValueError("runtime PNG cannot be truthfully normalized")

    return b"".join(
        [
            PNG_SIGNATURE,
            _png_chunk(b"IHDR", ihdr),
            _png_chunk(b"sRGB", srgb),
            *(_png_chunk(b"IDAT", payload) for payload in idat_parts),
            _png_chunk(b"IEND", b""),
        ]
    )


def _validate_runtime_ihdr(payload: bytes) -> None:
    width, height, bit_depth, color_type, compression, filter_method, interlace = (
        struct.unpack(">IIBBBBB", payload)
    )
    if (
        not 1 <= width <= 2048
        or not 1 <= height <= 2048
        or bit_depth != 8
        or color_type not in {2, 6}
        or compression != 0
        or filter_method != 0
        or interlace != 0
    ):
        raise ValueError("unsupported runtime PNG layout")


def _png_chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    )
