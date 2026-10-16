from __future__ import annotations

import asyncio
import socket
import ssl

import pytest

from home_ai_cluster import _document_retrieval as retrieval


class _Writer:
    def __init__(self) -> None:
        self.written = bytearray()
        self.closed = False

    def write(self, data: bytes) -> None:
        self.written.extend(data)

    async def drain(self) -> None:
        return None

    def close(self) -> None:
        self.closed = True

    async def wait_closed(self) -> None:
        return None


def _reader(response: bytes) -> asyncio.StreamReader:
    reader = asyncio.StreamReader(limit=retrieval.MAX_RESPONSE_HEADER_BYTES)
    reader.feed_data(response)
    reader.feed_eof()
    return reader


def _response(
    headers: str = "Content-Type: text/html",
    body: bytes = b"<p>ok</p>",
    status: str = "200 OK",
) -> bytes:
    return f"HTTP/1.1 {status}\r\n{headers}\r\n\r\n".encode() + body


async def _public_destination(
    _: retrieval._Destination,
) -> list[retrieval._ResolvedAddress]:
    return [
        retrieval._ResolvedAddress(
            socket.AF_INET,
            ("93.184.216.34", 443),
        )
    ]


def test_url_eligibility_rejects_non_https_credentials_and_malformed_ports() -> None:
    for value in (
        "http://example.com/",
        "file:///etc/passwd",
        "https://user:secret@example.com/",
        "https://example.com:99999/",
        "not a URL",
    ):
        with pytest.raises(retrieval.DocumentRetrievalFailure) as error:
            retrieval._parse_destination(value)
        assert error.value.code is retrieval.DocumentRetrievalFailureCode.INELIGIBLE_URL


def test_url_target_excludes_fragment_and_never_contains_credentials() -> None:
    destination = retrieval._parse_destination("https://example.com/a?q=x#ignored")

    assert destination.target == "/a?q=x"
    assert destination.host_header == "example.com"


@pytest.mark.parametrize(
    "address", ["127.0.0.1", "10.0.0.1", "::1", "224.0.0.1", "0.0.0.0", "2001:db8::1"]
)
def test_non_public_answers_are_rejected(
    address: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    class _Loop:
        async def getaddrinfo(
            self, *args: object, **kwargs: object
        ) -> list[tuple[object, ...]]:
            del args, kwargs
            family = socket.AF_INET6 if ":" in address else socket.AF_INET
            sockaddr = (address, 443, 0, 0) if ":" in address else (address, 443)
            return [(family, 0, 0, "", sockaddr)]

    monkeypatch.setattr(asyncio, "get_running_loop", lambda: _Loop())
    with pytest.raises(retrieval.DocumentRetrievalFailure) as error:
        asyncio.run(
            retrieval._resolve_public_addresses(
                retrieval._parse_destination("https://example.com/")
            )
        )
    assert error.value.code is retrieval.DocumentRetrievalFailureCode.DNS_REJECTED


def test_mixed_public_and_non_public_answers_are_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _Loop:
        async def getaddrinfo(
            self, *args: object, **kwargs: object
        ) -> list[tuple[object, ...]]:
            del args, kwargs
            return [
                (socket.AF_INET, 0, 0, "", ("93.184.216.34", 443)),
                (socket.AF_INET, 0, 0, "", ("127.0.0.1", 443)),
            ]

    monkeypatch.setattr(asyncio, "get_running_loop", lambda: _Loop())
    with pytest.raises(retrieval.DocumentRetrievalFailure) as error:
        asyncio.run(
            retrieval._resolve_public_addresses(
                retrieval._parse_destination("https://example.com/")
            )
        )
    assert error.value.code is retrieval.DocumentRetrievalFailureCode.DNS_REJECTED


def test_connection_is_pinned_to_validated_address_and_tls_keeps_hostname(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    async def open_connection(**kwargs: object) -> tuple[asyncio.StreamReader, _Writer]:
        captured.update(kwargs)
        return _reader(_response()), _Writer()

    monkeypatch.setattr(asyncio, "open_connection", open_connection)
    reader, writer = asyncio.run(
        retrieval._connect(
            retrieval._parse_destination("https://example.com/path"),
            retrieval._ResolvedAddress(socket.AF_INET, ("93.184.216.34", 443)),
        )
    )

    assert isinstance(reader, asyncio.StreamReader)
    assert isinstance(writer, _Writer)
    assert captured["host"] == "93.184.216.34"
    assert captured["server_hostname"] == "example.com"
    context = captured["ssl"]
    assert isinstance(context, ssl.SSLContext)
    assert context.check_hostname is True
    assert context.verify_mode is ssl.CERT_REQUIRED


def test_non_matching_tls_certificate_is_a_typed_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def connect(*args: object) -> tuple[asyncio.StreamReader, _Writer]:
        del args
        raise ssl.SSLCertVerificationError("hostname mismatch")

    monkeypatch.setattr(retrieval, "_resolve_public_addresses", _public_destination)
    monkeypatch.setattr(retrieval, "_connect", connect)
    with pytest.raises(retrieval.DocumentRetrievalFailure) as error:
        asyncio.run(retrieval.retrieve_html("https://example.com/"))

    assert error.value.code is retrieval.DocumentRetrievalFailureCode.TLS_FAILED


@pytest.mark.parametrize(
    ("headers", "code"),
    [
        (
            "Location: https://elsewhere/",
            retrieval.DocumentRetrievalFailureCode.REDIRECT,
        ),
        (
            "Content-Type: application/json",
            retrieval.DocumentRetrievalFailureCode.UNSUPPORTED_CONTENT_TYPE,
        ),
        (
            "Content-Type: text/html\r\nContent-Encoding: gzip",
            retrieval.DocumentRetrievalFailureCode.UNSUPPORTED_CONTENT_ENCODING,
        ),
    ],
)
def test_response_policy_rejections_use_actual_retrieval_path(
    monkeypatch: pytest.MonkeyPatch,
    headers: str,
    code: retrieval.DocumentRetrievalFailureCode,
) -> None:
    writer = _Writer()
    status = (
        "302 Found"
        if code is retrieval.DocumentRetrievalFailureCode.REDIRECT
        else "200 OK"
    )

    async def connect(*args: object) -> tuple[asyncio.StreamReader, _Writer]:
        del args
        return _reader(_response(headers, status=status)), writer

    monkeypatch.setattr(retrieval, "_resolve_public_addresses", _public_destination)
    monkeypatch.setattr(retrieval, "_connect", connect)
    with pytest.raises(retrieval.DocumentRetrievalFailure) as error:
        asyncio.run(retrieval.retrieve_html("https://example.com/"))

    assert error.value.code is code
    assert writer.closed


def test_encoded_limit_is_enforced_while_reading_not_just_from_content_length(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    writer = _Writer()
    oversized = b"x" * (retrieval.MAX_ENCODED_HTML_BYTES + 1)

    async def connect(*args: object) -> tuple[asyncio.StreamReader, _Writer]:
        del args
        return _reader(_response("Content-Type: text/html", oversized)), writer

    monkeypatch.setattr(retrieval, "_resolve_public_addresses", _public_destination)
    monkeypatch.setattr(retrieval, "_connect", connect)
    with pytest.raises(retrieval.DocumentRetrievalFailure) as error:
        asyncio.run(retrieval.retrieve_html("https://example.com/"))
    assert error.value.code is retrieval.DocumentRetrievalFailureCode.RESPONSE_TOO_LARGE
    assert writer.closed


def test_request_has_no_proxy_credentials_cookies_or_question_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    writer = _Writer()

    async def connect(*args: object) -> tuple[asyncio.StreamReader, _Writer]:
        del args
        return _reader(_response()), writer

    monkeypatch.setattr(retrieval, "_resolve_public_addresses", _public_destination)
    monkeypatch.setattr(retrieval, "_connect", connect)
    result = asyncio.run(retrieval.retrieve_html("https://example.com/"))

    assert result == "<p>ok</p>"
    wire = writer.written.decode("ascii")
    assert "Accept-Encoding: identity" in wire
    assert "Cookie:" not in wire
    assert "Authorization:" not in wire
    assert "Proxy-" not in wire
    assert "question" not in wire.lower()


def test_cancellation_closes_owned_connection_without_late_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    writer = _Writer()
    entered = asyncio.Event()

    async def connect(*args: object) -> tuple[asyncio.StreamReader, _Writer]:
        del args
        reader = asyncio.StreamReader()
        reader.feed_data(b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
        entered.set()
        return reader, writer

    async def run() -> None:
        task = asyncio.create_task(retrieval.retrieve_html("https://example.com/"))
        await entered.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    monkeypatch.setattr(retrieval, "_resolve_public_addresses", _public_destination)
    monkeypatch.setattr(retrieval, "_connect", connect)
    asyncio.run(run())
    assert writer.closed


def test_slow_body_read_hits_the_bounded_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    writer = _Writer()

    async def connect(*args: object) -> tuple[asyncio.StreamReader, _Writer]:
        del args
        reader = asyncio.StreamReader()
        reader.feed_data(
            b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: 10\r\n\r\n"
        )
        return reader, writer

    monkeypatch.setattr(retrieval, "_resolve_public_addresses", _public_destination)
    monkeypatch.setattr(retrieval, "_connect", connect)
    monkeypatch.setattr(retrieval, "BODY_READ_TIMEOUT_SECONDS", 0.001)
    with pytest.raises(retrieval.DocumentRetrievalFailure) as error:
        asyncio.run(retrieval.retrieve_html("https://example.com/"))

    assert error.value.code is retrieval.DocumentRetrievalFailureCode.TIMEOUT
    assert writer.closed


def test_pending_retrieval_does_not_block_the_event_loop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    writer = _Writer()
    entered = asyncio.Event()
    release = asyncio.Event()

    async def connect(*args: object) -> tuple[asyncio.StreamReader, _Writer]:
        del args
        entered.set()
        await release.wait()
        return _reader(_response()), writer

    async def run() -> None:
        task = asyncio.create_task(retrieval.retrieve_html("https://example.com/"))
        await entered.wait()
        # Reaching this scheduling point while connect is pending is the proof.
        release.set()
        assert await task == "<p>ok</p>"

    monkeypatch.setattr(retrieval, "_resolve_public_addresses", _public_destination)
    monkeypatch.setattr(retrieval, "_connect", connect)
    asyncio.run(run())
    assert writer.closed
