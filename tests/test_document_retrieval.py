from __future__ import annotations

import asyncio
import concurrent.futures
import shutil
import socket
import ssl
import subprocess
import threading
from collections.abc import Awaitable, Callable
from pathlib import Path

import pytest

from home_ai_cluster import _document_retrieval as retrieval

_TLS_HOSTNAME = "document.example.test"


class _TlsMaterial:
    def __init__(
        self,
        trusted_ca: Path,
        matching_certificate: Path,
        matching_key: Path,
        mismatching_certificate: Path,
        mismatching_key: Path,
        untrusted_certificate: Path,
        untrusted_key: Path,
    ) -> None:
        self.trusted_ca = trusted_ca
        self.matching_certificate = matching_certificate
        self.matching_key = matching_key
        self.mismatching_certificate = mismatching_certificate
        self.mismatching_key = mismatching_key
        self.untrusted_certificate = untrusted_certificate
        self.untrusted_key = untrusted_key


def _openssl(*arguments: str) -> None:
    subprocess.run(
        ["openssl", *arguments],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _issue_certificate(
    directory: Path,
    name: str,
    common_name: str,
    ca_certificate: Path,
    ca_key: Path,
) -> tuple[Path, Path]:
    certificate = directory / f"{name}.pem"
    key = directory / f"{name}-key.pem"
    request = directory / f"{name}.csr"
    extensions = directory / f"{name}.ext"
    extensions.write_text(
        "basicConstraints=CA:FALSE\n"
        f"subjectAltName=DNS:{common_name}\n"
        "keyUsage=digitalSignature,keyEncipherment\n"
        "extendedKeyUsage=serverAuth\n",
        encoding="ascii",
    )
    _openssl(
        "req",
        "-new",
        "-newkey",
        "rsa:2048",
        "-nodes",
        "-keyout",
        str(key),
        "-out",
        str(request),
        "-subj",
        f"/CN={common_name}",
    )
    _openssl(
        "x509",
        "-req",
        "-in",
        str(request),
        "-CA",
        str(ca_certificate),
        "-CAkey",
        str(ca_key),
        "-CAcreateserial",
        "-out",
        str(certificate),
        "-days",
        "1",
        "-sha256",
        "-extfile",
        str(extensions),
    )
    return certificate, key


@pytest.fixture(scope="module")
def tls_material(tmp_path_factory: pytest.TempPathFactory) -> _TlsMaterial:
    """Generate ephemeral local CA material; no certificate fixture is retained."""
    if shutil.which("openssl") is None:
        pytest.skip("local TLS integration tests require the openssl executable")
    directory = tmp_path_factory.mktemp("document-retrieval-tls")
    trusted_ca = directory / "trusted-ca.pem"
    trusted_ca_key = directory / "trusted-ca-key.pem"
    untrusted_ca = directory / "untrusted-ca.pem"
    untrusted_ca_key = directory / "untrusted-ca-key.pem"
    _openssl(
        "req",
        "-x509",
        "-newkey",
        "rsa:2048",
        "-nodes",
        "-keyout",
        str(trusted_ca_key),
        "-out",
        str(trusted_ca),
        "-days",
        "1",
        "-subj",
        "/CN=HAC retrieval trusted test CA",
    )
    _openssl(
        "req",
        "-x509",
        "-newkey",
        "rsa:2048",
        "-nodes",
        "-keyout",
        str(untrusted_ca_key),
        "-out",
        str(untrusted_ca),
        "-days",
        "1",
        "-subj",
        "/CN=HAC retrieval untrusted test CA",
    )
    matching_certificate, matching_key = _issue_certificate(
        directory,
        "matching",
        _TLS_HOSTNAME,
        trusted_ca,
        trusted_ca_key,
    )
    mismatching_certificate, mismatching_key = _issue_certificate(
        directory,
        "mismatching",
        "other.example.test",
        trusted_ca,
        trusted_ca_key,
    )
    untrusted_certificate, untrusted_key = _issue_certificate(
        directory,
        "untrusted",
        _TLS_HOSTNAME,
        untrusted_ca,
        untrusted_ca_key,
    )
    return _TlsMaterial(
        trusted_ca,
        matching_certificate,
        matching_key,
        mismatching_certificate,
        mismatching_key,
        untrusted_certificate,
        untrusted_key,
    )


def _trusted_client_context_factory(
    ca_certificate: Path, contexts: list[ssl.SSLContext]
) -> Callable[[], ssl.SSLContext]:
    def create_context() -> ssl.SSLContext:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.load_verify_locations(cafile=str(ca_certificate))
        contexts.append(context)
        return context

    return create_context


async def _start_tls_server(
    certificate: Path,
    key: Path,
    handler: Callable[[asyncio.StreamReader, asyncio.StreamWriter], Awaitable[None]],
    sni_names: list[str | None],
) -> tuple[asyncio.AbstractServer, int]:
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certificate, key)
    context.set_servername_callback(
        lambda _ssl_object, name, _context: sni_names.append(name)
    )
    try:
        server = await asyncio.start_server(handler, "127.0.0.1", 0, ssl=context)
    except OSError as error:
        pytest.skip(f"local TLS integration tests require loopback sockets: {error}")
    socket_info = server.sockets[0].getsockname()
    return server, socket_info[1]


def _loopback_destination(
    port: int,
) -> Callable[[retrieval._Destination], Awaitable[list[retrieval._ResolvedAddress]]]:
    async def resolve(_: retrieval._Destination) -> list[retrieval._ResolvedAddress]:
        # This is controlled test policy setup only. Production validation still
        # rejects loopback answers before this transport receives an address.
        return [retrieval._ResolvedAddress(socket.AF_INET, ("127.0.0.1", port))]

    return resolve


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


class _PendingCloseWriter(_Writer):
    def __init__(self) -> None:
        super().__init__()
        self.wait_started = asyncio.Event()
        self.release = asyncio.Event()

    async def wait_closed(self) -> None:
        self.wait_started.set()
        await self.release.wait()


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
    "url",
    (
        "https://example.com/unicode-é",
        "https://example.com/?query=é",
        "https://example.com/with space",
        "https://example.com/line\r\nbreak",
        "https://example.com/%not-encoded",
    ),
)
def test_request_target_rejects_unsafe_or_non_ascii_values(url: str) -> None:
    with pytest.raises(retrieval.DocumentRetrievalFailure) as error:
        retrieval._parse_destination(url)
    assert error.value.code is retrieval.DocumentRetrievalFailureCode.INELIGIBLE_URL


def test_request_target_preserves_valid_percent_encoding() -> None:
    destination = retrieval._parse_destination(
        "https://example.com/a%2Fb?encoded=%C3%A9"
    )
    assert destination.target == "/a%2Fb?encoded=%C3%A9"


def test_send_request_turns_an_unexpected_encoding_error_into_typed_failure() -> None:
    writer = _Writer()
    destination = retrieval._Destination("example.com", "example.com", 443, "/é")
    with pytest.raises(retrieval.DocumentRetrievalFailure) as error:
        asyncio.run(retrieval._send_request(writer, destination))
    assert error.value.code is retrieval.DocumentRetrievalFailureCode.INELIGIBLE_URL


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


def test_document_deadline_covers_pending_dns_before_connection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    resolver_started = asyncio.Event()
    never = asyncio.Event()
    connection_started = False

    async def resolve(
        _: retrieval._Destination,
    ) -> list[retrieval._ResolvedAddress]:
        resolver_started.set()
        await never.wait()
        return await _public_destination(_)

    async def connect(*args: object) -> tuple[asyncio.StreamReader, _Writer]:
        nonlocal connection_started
        del args
        connection_started = True
        return _reader(_response()), _Writer()

    async def run() -> None:
        task = asyncio.create_task(retrieval.retrieve_html("https://example.com/"))
        await resolver_started.wait()
        with pytest.raises(retrieval.DocumentRetrievalFailure) as error:
            await task
        assert error.value.code is retrieval.DocumentRetrievalFailureCode.TIMEOUT

    monkeypatch.setattr(retrieval, "_resolve_public_addresses", resolve)
    monkeypatch.setattr(retrieval, "_connect", connect)
    monkeypatch.setattr(retrieval, "DOCUMENT_TIMEOUT_SECONDS", 0.001)
    asyncio.run(run())
    assert not connection_started


def test_late_executor_backed_dns_completion_cannot_resume_cancelled_retrieval(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    resolver_started = asyncio.Event()
    resolver_finished = asyncio.Event()
    release_resolver = threading.Event()
    attempted_actions: list[str] = []

    async def connect(*args: object) -> tuple[asyncio.StreamReader, _Writer]:
        del args
        attempted_actions.append("tcp-tls-connection")
        return _reader(_response()), _Writer()

    async def send_request(*args: object) -> None:
        del args
        attempted_actions.append("http-request")

    async def read_headers(*args: object) -> dict[str, list[str]]:
        del args
        attempted_actions.append("html-processing")
        return {}

    async def run() -> None:
        loop = asyncio.get_running_loop()
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        resolver_future: concurrent.futures.Future[list[tuple[object, ...]]] | None = (
            None
        )

        def resolve_late() -> list[tuple[object, ...]]:
            loop.call_soon_threadsafe(resolver_started.set)
            assert release_resolver.wait(timeout=1)
            loop.call_soon_threadsafe(resolver_finished.set)
            return [(socket.AF_INET, 0, 0, "", ("93.184.216.34", 443))]

        def getaddrinfo(
            *args: object, **kwargs: object
        ) -> asyncio.Future[list[tuple[object, ...]]]:
            nonlocal resolver_future
            del args, kwargs
            resolver_future = executor.submit(resolve_late)
            return asyncio.wrap_future(resolver_future)

        monkeypatch.setattr(loop, "getaddrinfo", getaddrinfo)
        monkeypatch.setattr(retrieval, "_connect", connect)
        monkeypatch.setattr(retrieval, "_send_request", send_request)
        monkeypatch.setattr(retrieval, "_read_headers", read_headers)

        try:
            task = asyncio.create_task(retrieval.retrieve_html("https://example.com/"))
            await asyncio.wait_for(resolver_started.wait(), timeout=1)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

            assert resolver_future is not None
            assert not resolver_future.done()
            release_resolver.set()
            await asyncio.wait_for(resolver_finished.wait(), timeout=1)
            assert resolver_future.result(timeout=0) == [
                (socket.AF_INET, 0, 0, "", ("93.184.216.34", 443))
            ]
            assert attempted_actions == []
            assert [
                pending
                for pending in asyncio.all_tasks()
                if pending is not asyncio.current_task() and not pending.done()
            ] == []
        finally:
            release_resolver.set()
            executor.shutdown(wait=True, cancel_futures=True)

    asyncio.run(run())


def test_pending_normal_close_becomes_a_typed_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    writer = _PendingCloseWriter()

    async def connect(
        *args: object,
    ) -> tuple[asyncio.StreamReader, _PendingCloseWriter]:
        del args
        return _reader(_response()), writer

    monkeypatch.setattr(retrieval, "_resolve_public_addresses", _public_destination)
    monkeypatch.setattr(retrieval, "_connect", connect)
    monkeypatch.setattr(retrieval, "CLOSE_TIMEOUT_SECONDS", 0.001)
    with pytest.raises(retrieval.DocumentRetrievalFailure) as error:
        asyncio.run(retrieval.retrieve_html("https://example.com/"))
    assert error.value.code is retrieval.DocumentRetrievalFailureCode.TIMEOUT
    assert writer.closed
    assert writer.wait_started.is_set()


def test_cancellation_requests_close_without_waiting_for_a_stuck_shutdown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    writer = _PendingCloseWriter()
    entered = asyncio.Event()

    async def connect(
        *args: object,
    ) -> tuple[asyncio.StreamReader, _PendingCloseWriter]:
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
    assert not writer.wait_started.is_set()


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


def test_real_local_tls_uses_pinned_address_original_sni_and_verified_hostname(
    monkeypatch: pytest.MonkeyPatch, tls_material: _TlsMaterial
) -> None:
    """Exercise TCP and TLS; only the test's policy resolver is controlled."""

    async def run() -> None:
        sni_names: list[str | None] = []
        received_request = asyncio.Event()

        async def handler(
            reader: asyncio.StreamReader, writer: asyncio.StreamWriter
        ) -> None:
            request = await reader.readuntil(b"\r\n\r\n")
            assert b"Host: document.example.test\r\n" in request
            received_request.set()
            writer.write(_response(body=b"<p>local TLS</p>"))
            await writer.drain()
            writer.close()
            await writer.wait_closed()

        server, port = await _start_tls_server(
            tls_material.matching_certificate,
            tls_material.matching_key,
            handler,
            sni_names,
        )
        contexts: list[ssl.SSLContext] = []
        loop = asyncio.get_running_loop()

        async def unexpected_resolution(*_: object, **__: object) -> object:
            raise AssertionError(
                "the pinned numeric address must not be resolved again"
            )

        monkeypatch.setattr(
            retrieval,
            "_resolve_public_addresses",
            _loopback_destination(port),
        )
        monkeypatch.setattr(
            ssl,
            "create_default_context",
            _trusted_client_context_factory(tls_material.trusted_ca, contexts),
        )
        monkeypatch.setattr(loop, "getaddrinfo", unexpected_resolution)
        try:
            assert await retrieval.retrieve_html(f"https://{_TLS_HOSTNAME}/proof") == (
                "<p>local TLS</p>"
            )
            await asyncio.wait_for(received_request.wait(), timeout=1)
        finally:
            server.close()
            await server.wait_closed()

        assert sni_names == [_TLS_HOSTNAME]
        assert len(contexts) == 1
        assert contexts[0].check_hostname is True
        assert contexts[0].verify_mode is ssl.CERT_REQUIRED

    asyncio.run(run())


def test_real_local_tls_rejects_a_trusted_certificate_for_another_hostname(
    monkeypatch: pytest.MonkeyPatch, tls_material: _TlsMaterial
) -> None:
    async def run() -> None:
        sni_names: list[str | None] = []

        async def handler(
            _: asyncio.StreamReader, writer: asyncio.StreamWriter
        ) -> None:
            writer.close()
            await writer.wait_closed()

        server, port = await _start_tls_server(
            tls_material.mismatching_certificate,
            tls_material.mismatching_key,
            handler,
            sni_names,
        )
        contexts: list[ssl.SSLContext] = []
        monkeypatch.setattr(
            retrieval,
            "_resolve_public_addresses",
            _loopback_destination(port),
        )
        monkeypatch.setattr(
            ssl,
            "create_default_context",
            _trusted_client_context_factory(tls_material.trusted_ca, contexts),
        )
        try:
            with pytest.raises(retrieval.DocumentRetrievalFailure) as error:
                await retrieval.retrieve_html(f"https://{_TLS_HOSTNAME}/")
        finally:
            server.close()
            await server.wait_closed()

        assert error.value.code is retrieval.DocumentRetrievalFailureCode.TLS_FAILED
        assert sni_names == [_TLS_HOSTNAME]
        assert contexts[0].check_hostname is True
        assert contexts[0].verify_mode is ssl.CERT_REQUIRED

    asyncio.run(run())


def test_real_local_tls_rejects_an_untrusted_certificate_authority(
    monkeypatch: pytest.MonkeyPatch, tls_material: _TlsMaterial
) -> None:
    async def run() -> None:
        sni_names: list[str | None] = []

        async def handler(
            _: asyncio.StreamReader, writer: asyncio.StreamWriter
        ) -> None:
            writer.close()
            await writer.wait_closed()

        server, port = await _start_tls_server(
            tls_material.untrusted_certificate,
            tls_material.untrusted_key,
            handler,
            sni_names,
        )
        contexts: list[ssl.SSLContext] = []
        monkeypatch.setattr(
            retrieval,
            "_resolve_public_addresses",
            _loopback_destination(port),
        )
        monkeypatch.setattr(
            ssl,
            "create_default_context",
            _trusted_client_context_factory(tls_material.trusted_ca, contexts),
        )
        try:
            with pytest.raises(retrieval.DocumentRetrievalFailure) as error:
                await retrieval.retrieve_html(f"https://{_TLS_HOSTNAME}/")
        finally:
            server.close()
            await server.wait_closed()

        assert error.value.code is retrieval.DocumentRetrievalFailureCode.TLS_FAILED
        assert sni_names == [_TLS_HOSTNAME]
        assert contexts[0].check_hostname is True
        assert contexts[0].verify_mode is ssl.CERT_REQUIRED

    asyncio.run(run())


def test_real_local_tls_pending_network_io_keeps_the_event_loop_responsive(
    monkeypatch: pytest.MonkeyPatch, tls_material: _TlsMaterial
) -> None:
    async def run() -> None:
        sni_names: list[str | None] = []
        request_received = asyncio.Event()
        release_response = asyncio.Event()

        async def handler(
            reader: asyncio.StreamReader, writer: asyncio.StreamWriter
        ) -> None:
            await reader.readuntil(b"\r\n\r\n")
            request_received.set()
            await release_response.wait()
            writer.write(_response(body=b"<p>responsive</p>"))
            await writer.drain()
            writer.close()
            await writer.wait_closed()

        server, port = await _start_tls_server(
            tls_material.matching_certificate,
            tls_material.matching_key,
            handler,
            sni_names,
        )
        contexts: list[ssl.SSLContext] = []
        monkeypatch.setattr(
            retrieval,
            "_resolve_public_addresses",
            _loopback_destination(port),
        )
        monkeypatch.setattr(
            ssl,
            "create_default_context",
            _trusted_client_context_factory(tls_material.trusted_ca, contexts),
        )
        task = asyncio.create_task(retrieval.retrieve_html(f"https://{_TLS_HOSTNAME}/"))
        try:
            await asyncio.wait_for(request_received.wait(), timeout=1)
            # The task is waiting on real TLS/TCP input, yet this coroutine runs.
            await asyncio.sleep(0)
            assert not task.done()
            release_response.set()
            assert await task == "<p>responsive</p>"
        finally:
            release_response.set()
            server.close()
            await server.wait_closed()

    asyncio.run(run())


def test_real_local_tls_cancellation_closes_the_live_connection(
    monkeypatch: pytest.MonkeyPatch, tls_material: _TlsMaterial
) -> None:
    async def run() -> None:
        sni_names: list[str | None] = []
        request_received = asyncio.Event()
        client_disconnected = asyncio.Event()

        async def handler(
            reader: asyncio.StreamReader, writer: asyncio.StreamWriter
        ) -> None:
            await reader.readuntil(b"\r\n\r\n")
            writer.write(b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
            await writer.drain()
            request_received.set()
            await reader.read()
            client_disconnected.set()
            writer.close()
            await writer.wait_closed()

        server, port = await _start_tls_server(
            tls_material.matching_certificate,
            tls_material.matching_key,
            handler,
            sni_names,
        )
        contexts: list[ssl.SSLContext] = []
        monkeypatch.setattr(
            retrieval,
            "_resolve_public_addresses",
            _loopback_destination(port),
        )
        monkeypatch.setattr(
            ssl,
            "create_default_context",
            _trusted_client_context_factory(tls_material.trusted_ca, contexts),
        )
        task = asyncio.create_task(retrieval.retrieve_html(f"https://{_TLS_HOSTNAME}/"))
        try:
            await asyncio.wait_for(request_received.wait(), timeout=1)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            await asyncio.wait_for(client_disconnected.wait(), timeout=1)
        finally:
            server.close()
            await server.wait_closed()

    asyncio.run(run())
