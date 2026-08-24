"""Regression checks for RFC-0085's HAC-owned HTTPX environment boundary."""

import ast
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import httpx
import pytest

from home_ai_cluster import chat_command

_HTTPX_ENVIRONMENT_VARIABLES = (
    "HTTP_PROXY",
    "http_proxy",
    "HTTPS_PROXY",
    "https_proxy",
    "ALL_PROXY",
    "all_proxy",
    "NO_PROXY",
    "no_proxy",
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
)
_PRODUCTION_SOURCE = Path(__file__).parents[1] / "src" / "home_ai_cluster"
_SYNTHETIC_MARKER = "SYNTHETIC-HAC-PROXY-PROBE"


def _clear_httpx_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in _HTTPX_ENVIRONMENT_VARIABLES:
        monkeypatch.delenv(name, raising=False)


def _start_server(
    handler: type[BaseHTTPRequestHandler],
) -> tuple[ThreadingHTTPServer, threading.Thread]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    return server, thread


def _stop_server(server: ThreadingHTTPServer, thread: threading.Thread) -> None:
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)
    assert not thread.is_alive()


def _post_through_real_native_client(
    monkeypatch: pytest.MonkeyPatch, port: int
) -> httpx.Response:
    monkeypatch.setattr(
        chat_command,
        "_ORDINARY_CHAT_URL",
        f"http://127.0.0.1:{port}/v1/chat",
    )
    return chat_command._post_native_request(
        {"marker": _SYNTHETIC_MARKER},
        timeout_seconds=2.0,
        client_factory=httpx.Client,
    )


def test_hac_native_client_ignores_synthetic_http_proxy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    direct_requests: list[bytes] = []
    proxy_requests: list[bytes] = []

    class DirectHandler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            direct_requests.append(self.rfile.read(int(self.headers["Content-Length"])))
            self.send_response(200)
            self.end_headers()

        def log_message(self, *_: object) -> None:
            return None

    class ProxyHandler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            proxy_requests.append(self.rfile.read(int(self.headers["Content-Length"])))
            self.send_response(502)
            self.end_headers()

        def log_message(self, *_: object) -> None:
            return None

    direct_server, direct_thread = _start_server(DirectHandler)
    proxy_server, proxy_thread = _start_server(ProxyHandler)
    try:
        _clear_httpx_environment(monkeypatch)
        monkeypatch.setenv("HTTP_PROXY", f"http://127.0.0.1:{proxy_server.server_port}")
        monkeypatch.setenv("NO_PROXY", "")

        response = _post_through_real_native_client(
            monkeypatch, direct_server.server_port
        )

        assert response.status_code == 200
        assert direct_requests == [b'{"marker":"SYNTHETIC-HAC-PROXY-PROBE"}']
        assert proxy_requests == []
    finally:
        _stop_server(proxy_server, proxy_thread)
        _stop_server(direct_server, direct_thread)


def test_hac_native_client_ignores_synthetic_unsupported_socks_proxy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    direct_requests: list[bytes] = []

    class DirectHandler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            direct_requests.append(self.rfile.read(int(self.headers["Content-Length"])))
            self.send_response(200)
            self.end_headers()

        def log_message(self, *_: object) -> None:
            return None

    direct_server, direct_thread = _start_server(DirectHandler)
    try:
        _clear_httpx_environment(monkeypatch)
        monkeypatch.setenv("ALL_PROXY", "socks5://127.0.0.1:1")

        response = _post_through_real_native_client(
            monkeypatch, direct_server.server_port
        )

        assert response.status_code == 200
        assert direct_requests == [b'{"marker":"SYNTHETIC-HAC-PROXY-PROBE"}']
    finally:
        _stop_server(direct_server, direct_thread)


def test_all_production_httpx_constructors_disable_environment_trust() -> None:
    violations: list[str] = []

    for source_path in sorted(_PRODUCTION_SOURCE.rglob("*.py")):
        tree = ast.parse(
            source_path.read_text(encoding="utf-8"), filename=str(source_path)
        )
        for node in ast.walk(tree):
            if not (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "httpx"
                and node.func.attr in {"Client", "AsyncClient"}
            ):
                continue
            has_literal_false = any(
                keyword.arg == "trust_env"
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value is False
                for keyword in node.keywords
            )
            if not has_literal_false:
                violations.append(
                    f"{source_path.relative_to(_PRODUCTION_SOURCE)}:{node.lineno}"
                )

    assert not violations, "HTTPX constructors missing trust_env=False: " + ", ".join(
        violations
    )
