"""Bounded, direct public-HTTPS HTML retrieval for future caller-local use.

This private module deliberately has no caller integration.  It resolves a
hostname once, rejects any non-public answer, and connects to that selected
numeric address while presenting the original hostname to TLS.  Consequently
DNS cannot select a different destination between validation and connection.
"""

from __future__ import annotations

import asyncio
import ipaddress
import socket
import ssl
from dataclasses import dataclass
from enum import StrEnum
from urllib.parse import urlsplit

from home_ai_cluster._document_passages import MAX_HTML_BYTES

MAX_RESPONSE_HEADER_BYTES = 16_384
MAX_ENCODED_HTML_BYTES = MAX_HTML_BYTES
CONNECT_TIMEOUT_SECONDS = 5.0
HEADER_TIMEOUT_SECONDS = 5.0
BODY_READ_TIMEOUT_SECONDS = 5.0
DOCUMENT_TIMEOUT_SECONDS = 15.0


class DocumentRetrievalFailureCode(StrEnum):
    """Finite outcomes a future caller may safely interpret per document."""

    INELIGIBLE_URL = "ineligible-url"
    DNS_REJECTED = "dns-rejected"
    CONNECTION_FAILED = "connection-failed"
    TLS_FAILED = "tls-failed"
    MALFORMED_RESPONSE = "malformed-response"
    REDIRECT = "redirect"
    UNSUPPORTED_CONTENT_TYPE = "unsupported-content-type"
    UNSUPPORTED_CONTENT_ENCODING = "unsupported-content-encoding"
    RESPONSE_TOO_LARGE = "response-too-large"
    TIMEOUT = "timeout"


class DocumentRetrievalFailure(Exception):
    """An expected, privacy-safe document retrieval rejection."""

    def __init__(self, code: DocumentRetrievalFailureCode) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class _Destination:
    hostname: str
    host_header: str
    port: int
    target: str


@dataclass(frozen=True)
class _ResolvedAddress:
    family: socket.AddressFamily
    sockaddr: tuple[str, int] | tuple[str, int, int, int]


async def retrieve_html(url: str) -> str:
    """Retrieve one bounded UTF-8 HTML document or raise a typed failure.

    All I/O is awaited directly by this coroutine.  Cancellation closes the
    owned stream in ``finally`` and is deliberately propagated, so no detached
    retrieval survives a cancelled foreground task.
    """
    destination = _parse_destination(url)
    addresses = await _resolve_public_addresses(destination)
    # One selected answer means no retry or alternate-destination behavior.
    address = addresses[0]
    writer: asyncio.StreamWriter | None = None
    try:
        async with asyncio.timeout(DOCUMENT_TIMEOUT_SECONDS):
            reader, writer = await _connect(destination, address)
            await _send_request(writer, destination)
            headers = await _read_headers(reader)
            _validate_response_headers(headers)
            body = await _read_body(reader, headers)
            try:
                return body.decode("utf-8")
            except UnicodeDecodeError as error:
                raise DocumentRetrievalFailure(
                    DocumentRetrievalFailureCode.MALFORMED_RESPONSE
                ) from error
    except asyncio.CancelledError:
        raise
    except TimeoutError as error:
        raise DocumentRetrievalFailure(DocumentRetrievalFailureCode.TIMEOUT) from error
    except ssl.SSLCertVerificationError as error:
        raise DocumentRetrievalFailure(
            DocumentRetrievalFailureCode.TLS_FAILED
        ) from error
    except ssl.SSLError as error:
        raise DocumentRetrievalFailure(
            DocumentRetrievalFailureCode.TLS_FAILED
        ) from error
    except (ConnectionError, OSError) as error:
        raise DocumentRetrievalFailure(
            DocumentRetrievalFailureCode.CONNECTION_FAILED
        ) from error
    finally:
        if writer is not None:
            writer.close()
            try:
                await writer.wait_closed()
            except (ConnectionError, OSError):
                pass


def _parse_destination(url: str) -> _Destination:
    if not isinstance(url, str):
        raise DocumentRetrievalFailure(DocumentRetrievalFailureCode.INELIGIBLE_URL)
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError as error:
        raise DocumentRetrievalFailure(
            DocumentRetrievalFailureCode.INELIGIBLE_URL
        ) from error
    if (
        parsed.scheme.lower() != "https"
        or not parsed.netloc
        or parsed.username is not None
        or parsed.password is not None
        or parsed.hostname is None
    ):
        raise DocumentRetrievalFailure(DocumentRetrievalFailureCode.INELIGIBLE_URL)
    try:
        hostname = parsed.hostname.encode("idna").decode("ascii").lower()
    except UnicodeError as error:
        raise DocumentRetrievalFailure(
            DocumentRetrievalFailureCode.INELIGIBLE_URL
        ) from error
    if not hostname or any(character in hostname for character in "\r\n"):
        raise DocumentRetrievalFailure(DocumentRetrievalFailureCode.INELIGIBLE_URL)
    actual_port = 443 if port is None else port
    if not 1 <= actual_port <= 65_535:
        raise DocumentRetrievalFailure(DocumentRetrievalFailureCode.INELIGIBLE_URL)
    host = f"[{hostname}]" if ":" in hostname else hostname
    host_header = host if actual_port == 443 else f"{host}:{actual_port}"
    target = parsed.path or "/"
    if parsed.query:
        target = f"{target}?{parsed.query}"
    return _Destination(hostname, host_header, actual_port, target)


async def _resolve_public_addresses(
    destination: _Destination,
) -> list[_ResolvedAddress]:
    try:
        raw_answers = await asyncio.get_running_loop().getaddrinfo(
            destination.hostname,
            destination.port,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )
    except OSError as error:
        raise DocumentRetrievalFailure(
            DocumentRetrievalFailureCode.DNS_REJECTED
        ) from error
    answers: list[_ResolvedAddress] = []
    for family, _, _, _, sockaddr in raw_answers:
        try:
            address = ipaddress.ip_address(sockaddr[0])
        except ValueError as error:
            raise DocumentRetrievalFailure(
                DocumentRetrievalFailureCode.DNS_REJECTED
            ) from error
        if not _is_public_address(address):
            raise DocumentRetrievalFailure(DocumentRetrievalFailureCode.DNS_REJECTED)
        answers.append(_ResolvedAddress(family, sockaddr))
    if not answers:
        raise DocumentRetrievalFailure(DocumentRetrievalFailureCode.DNS_REJECTED)
    return answers


def _is_public_address(address: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Use explicit exclusions; ``is_global`` alone is not sufficient here."""
    return (
        address.is_global
        and not address.is_loopback
        and not address.is_private
        and not address.is_link_local
        and not address.is_multicast
        and not address.is_unspecified
        and not address.is_reserved
    )


async def _connect(
    destination: _Destination, address: _ResolvedAddress
) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
    context = ssl.create_default_context()
    # These remain explicit even if a future Python default changes.
    context.verify_mode = ssl.CERT_REQUIRED
    context.check_hostname = True
    try:
        async with asyncio.timeout(CONNECT_TIMEOUT_SECONDS):
            return await asyncio.open_connection(
                host=address.sockaddr[0],
                port=address.sockaddr[1],
                family=address.family,
                ssl=context,
                server_hostname=destination.hostname,
                limit=MAX_RESPONSE_HEADER_BYTES,
            )
    except TimeoutError as error:
        raise DocumentRetrievalFailure(DocumentRetrievalFailureCode.TIMEOUT) from error


async def _send_request(
    writer: asyncio.StreamWriter, destination: _Destination
) -> None:
    request = (
        f"GET {destination.target} HTTP/1.1\r\n"
        f"Host: {destination.host_header}\r\n"
        "User-Agent: home-ai-cluster/1.1\r\n"
        "Accept: text/html\r\n"
        "Accept-Encoding: identity\r\n"
        "Connection: close\r\n\r\n"
    )
    writer.write(request.encode("ascii"))
    await writer.drain()


async def _read_headers(reader: asyncio.StreamReader) -> dict[str, list[str]]:
    try:
        async with asyncio.timeout(HEADER_TIMEOUT_SECONDS):
            raw = await reader.readuntil(b"\r\n\r\n")
    except (asyncio.IncompleteReadError, asyncio.LimitOverrunError) as error:
        raise DocumentRetrievalFailure(
            DocumentRetrievalFailureCode.MALFORMED_RESPONSE
        ) from error
    if len(raw) > MAX_RESPONSE_HEADER_BYTES:
        raise DocumentRetrievalFailure(DocumentRetrievalFailureCode.RESPONSE_TOO_LARGE)
    try:
        lines = raw[:-4].decode("iso-8859-1").split("\r\n")
        version, status, _ = lines[0].split(" ", 2)
        if version not in {"HTTP/1.0", "HTTP/1.1"} or not status.isdecimal():
            raise ValueError
        headers: dict[str, list[str]] = {":status": [status]}
        for line in lines[1:]:
            name, value = line.split(":", 1)
            if not name or name != name.strip() or "\t" in name:
                raise ValueError
            headers.setdefault(name.lower(), []).append(value.strip())
        return headers
    except (IndexError, ValueError, UnicodeError) as error:
        raise DocumentRetrievalFailure(
            DocumentRetrievalFailureCode.MALFORMED_RESPONSE
        ) from error


def _validate_response_headers(headers: dict[str, list[str]]) -> None:
    status = int(headers[":status"][0])
    if 300 <= status < 400:
        raise DocumentRetrievalFailure(DocumentRetrievalFailureCode.REDIRECT)
    if not 200 <= status < 300:
        raise DocumentRetrievalFailure(DocumentRetrievalFailureCode.MALFORMED_RESPONSE)
    content_types = headers.get("content-type", [])
    is_html = (
        len(content_types) == 1
        and content_types[0].split(";", 1)[0].strip().lower() == "text/html"
    )
    if not is_html:
        raise DocumentRetrievalFailure(
            DocumentRetrievalFailureCode.UNSUPPORTED_CONTENT_TYPE
        )
    encodings = headers.get("content-encoding", [])
    if encodings and encodings != ["identity"]:
        raise DocumentRetrievalFailure(
            DocumentRetrievalFailureCode.UNSUPPORTED_CONTENT_ENCODING
        )
    transfer_encodings = headers.get("transfer-encoding", [])
    if transfer_encodings and transfer_encodings != ["chunked"]:
        raise DocumentRetrievalFailure(DocumentRetrievalFailureCode.MALFORMED_RESPONSE)
    lengths = headers.get("content-length", [])
    if len(lengths) > 1 or (transfer_encodings and lengths):
        raise DocumentRetrievalFailure(DocumentRetrievalFailureCode.MALFORMED_RESPONSE)
    if lengths:
        try:
            length = int(lengths[0])
        except ValueError as error:
            raise DocumentRetrievalFailure(
                DocumentRetrievalFailureCode.MALFORMED_RESPONSE
            ) from error
        if length < 0:
            raise DocumentRetrievalFailure(
                DocumentRetrievalFailureCode.MALFORMED_RESPONSE
            )
        if length > MAX_ENCODED_HTML_BYTES:
            raise DocumentRetrievalFailure(
                DocumentRetrievalFailureCode.RESPONSE_TOO_LARGE
            )


async def _read_body(
    reader: asyncio.StreamReader, headers: dict[str, list[str]]
) -> bytes:
    if headers.get("transfer-encoding") == ["chunked"]:
        return await _read_chunked_body(reader)
    length = headers.get("content-length")
    if length:
        return await _read_exactly_bounded(reader, int(length[0]))
    return await _read_to_eof_bounded(reader)


async def _read_exactly_bounded(reader: asyncio.StreamReader, length: int) -> bytes:
    try:
        async with asyncio.timeout(BODY_READ_TIMEOUT_SECONDS):
            return await reader.readexactly(length)
    except asyncio.IncompleteReadError as error:
        raise DocumentRetrievalFailure(
            DocumentRetrievalFailureCode.MALFORMED_RESPONSE
        ) from error


async def _read_chunked_body(reader: asyncio.StreamReader) -> bytes:
    body = bytearray()
    while True:
        try:
            async with asyncio.timeout(BODY_READ_TIMEOUT_SECONDS):
                line = await reader.readuntil(b"\r\n")
        except (asyncio.IncompleteReadError, asyncio.LimitOverrunError) as error:
            raise DocumentRetrievalFailure(
                DocumentRetrievalFailureCode.MALFORMED_RESPONSE
            ) from error
        try:
            size = int(line[:-2].split(b";", 1)[0], 16)
        except ValueError as error:
            raise DocumentRetrievalFailure(
                DocumentRetrievalFailureCode.MALFORMED_RESPONSE
            ) from error
        if size < 0 or len(body) + size > MAX_ENCODED_HTML_BYTES:
            raise DocumentRetrievalFailure(
                DocumentRetrievalFailureCode.RESPONSE_TOO_LARGE
            )
        if size == 0:
            # Trailer fields would add a second unbounded header grammar.
            try:
                async with asyncio.timeout(BODY_READ_TIMEOUT_SECONDS):
                    if await reader.readexactly(2) != b"\r\n":
                        raise ValueError
            except (asyncio.IncompleteReadError, ValueError) as error:
                raise DocumentRetrievalFailure(
                    DocumentRetrievalFailureCode.MALFORMED_RESPONSE
                ) from error
            return bytes(body)
        chunk = await _read_exactly_bounded(reader, size)
        try:
            async with asyncio.timeout(BODY_READ_TIMEOUT_SECONDS):
                if await reader.readexactly(2) != b"\r\n":
                    raise ValueError
        except (asyncio.IncompleteReadError, ValueError) as error:
            raise DocumentRetrievalFailure(
                DocumentRetrievalFailureCode.MALFORMED_RESPONSE
            ) from error
        body.extend(chunk)


async def _read_to_eof_bounded(reader: asyncio.StreamReader) -> bytes:
    body = bytearray()
    while True:
        async with asyncio.timeout(BODY_READ_TIMEOUT_SECONDS):
            chunk = await reader.read(min(16_384, MAX_ENCODED_HTML_BYTES + 1))
        if not chunk:
            return bytes(body)
        if len(body) + len(chunk) > MAX_ENCODED_HTML_BYTES:
            raise DocumentRetrievalFailure(
                DocumentRetrievalFailureCode.RESPONSE_TOO_LARGE
            )
        body.extend(chunk)
