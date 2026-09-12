"""Closed RFC-0120 still-PNG validation for local image generation."""

import struct
import zlib

MAX_ENCODED_PNG_BYTES = 41_943_040
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


class ImageGenerationResultValidationError(ValueError):
    """Raised when candidate bytes are outside HAC's still-PNG profile."""


def validate_still_png(candidate: bytes) -> bytes:
    """Return only candidate bytes that satisfy the closed RFC-0120 PNG profile."""
    if len(candidate) > MAX_ENCODED_PNG_BYTES:
        _fail("encoded PNG exceeds 40 MiB")
    if not candidate.startswith(PNG_SIGNATURE):
        _fail("invalid PNG signature")

    # Establish finite geometry before parsing IDAT or decompressing any data.
    if len(candidate) < len(PNG_SIGNATURE) + 8 + 13 + 4:
        _fail("truncated IHDR")
    first_length, first_kind = struct.unpack_from(">I4s", candidate, len(PNG_SIGNATURE))
    if first_kind != b"IHDR" or first_length != 13:
        _fail("IHDR must be the first 13-byte chunk")
    ihdr = candidate[len(PNG_SIGNATURE) + 8 : len(PNG_SIGNATURE) + 21]
    width, height, bit_depth, color_type, compression, filter_method, interlace = (
        struct.unpack(">IIBBBBB", ihdr)
    )
    if not 1 <= width <= 2048 or not 1 <= height <= 2048:
        _fail("PNG geometry is outside the accepted bounds")
    if bit_depth not in {8, 16} or color_type not in {2, 6}:
        _fail("unsupported PNG pixel layout")
    if compression != 0 or filter_method != 0 or interlace != 0:
        _fail("unsupported PNG encoding method")

    channels = 3 if color_type == 2 else 4
    row_bytes = width * channels * (bit_depth // 8)
    expected_inflated_bytes = height * (1 + row_bytes)

    offset = len(PNG_SIGNATURE)
    state = "ihdr"
    idat_parts: list[bytes] = []
    while offset < len(candidate):
        if len(candidate) - offset < 12:
            _fail("truncated PNG chunk")
        length, kind = struct.unpack_from(">I4s", candidate, offset)
        offset += 8
        if length > len(candidate) - offset - 4:
            _fail("truncated PNG chunk body")
        payload = candidate[offset : offset + length]
        expected_crc = struct.unpack_from(">I", candidate, offset + length)[0]
        if zlib.crc32(kind + payload) & 0xFFFFFFFF != expected_crc:
            _fail("invalid PNG chunk CRC")
        offset += length + 4

        if state == "ihdr":
            if kind != b"IHDR" or length != 13:
                _fail("IHDR must occur exactly once and first")
            state = "srgb"
        elif state == "srgb":
            if kind != b"sRGB" or length != 1 or payload[0] > 3:
                _fail("invalid or missing sRGB chunk")
            state = "idat"
        elif state == "idat":
            if kind == b"IDAT":
                idat_parts.append(payload)
                continue
            if kind != b"IEND" or length != 0 or not idat_parts:
                _fail("IDAT chunks must be consecutive and followed by IEND")
            state = "done"
        else:
            _fail("bytes after IEND")

    if state != "done":
        _fail("missing IEND")

    compressed = b"".join(idat_parts)
    decompressor = zlib.decompressobj()
    try:
        inflated = decompressor.decompress(compressed, expected_inflated_bytes + 1)
    except zlib.error as exc:
        raise ImageGenerationResultValidationError("invalid PNG zlib stream") from exc
    if (
        not decompressor.eof
        or decompressor.unused_data
        or decompressor.unconsumed_tail
        or len(inflated) != expected_inflated_bytes
    ):
        _fail("incomplete, excess, or trailing PNG zlib data")

    stride = 1 + row_bytes
    if any(inflated[start] > 4 for start in range(0, len(inflated), stride)):
        _fail("invalid PNG scanline filter")
    return candidate


def _fail(message: str) -> None:
    raise ImageGenerationResultValidationError(message)
