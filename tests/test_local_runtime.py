import argparse
import asyncio
import signal
from pathlib import Path

import pytest
from fastapi import FastAPI

from home_ai_cluster import local_runtime
from home_ai_cluster.adapters.ollama import OllamaAdapter


def test_parse_args_defaults_to_ollama() -> None:
    args = local_runtime.parse_args([])

    assert args.runtime == "ollama"
    assert args.llama_server_base_url is None
    assert args.llama_server_model is None
    assert args.ollama_model is None
    assert args.ollama_disable_thinking is False
    assert args.host == "127.0.0.1"
    assert args.port == 25042
    assert args.receiver_host is None
    assert args.receiver_port is None


def test_parse_args_accepts_explicit_ollama() -> None:
    args = local_runtime.parse_args(["--runtime", "ollama"])

    assert args.runtime == "ollama"


def test_parse_args_accepts_ollama_disable_thinking() -> None:
    args = local_runtime.parse_args(
        ["--runtime", "ollama", "--ollama-disable-thinking"]
    )

    assert args.ollama_disable_thinking is True


def test_parse_args_rejects_unsupported_runtime() -> None:
    with pytest.raises(SystemExit):
        local_runtime.parse_args(["--runtime", "unsupported"])


@pytest.mark.parametrize(
    ("argv", "error"),
    [
        (
            ["--runtime", "llama-server", "--ollama-model", "configured-model"],
            "ollama arguments require --runtime ollama",
        ),
        (
            ["--runtime", "llama-server", "--ollama-disable-thinking"],
            "ollama arguments require --runtime ollama",
        ),
        (
            ["--runtime", "ollama", "--ollama-model", ""],
            "argument --ollama-model: value must not be empty",
        ),
        (
            [
                "--runtime",
                "ollama",
                "--llama-server-base-url",
                "http://127.0.0.1:8080",
            ],
            "llama-server arguments require --runtime llama-server",
        ),
        (
            ["--runtime", "llama-server"],
            "--llama-server-base-url is required for llama-server",
        ),
        (
            [
                "--runtime",
                "llama-server",
                "--llama-server-base-url",
                "http://127.0.0.1:8080",
            ],
            "--llama-server-model is required for llama-server",
        ),
        (
            [
                "--runtime",
                "llama-server",
                "--llama-server-base-url",
                "https://127.0.0.1:8080",
                "--llama-server-model",
                "local-model",
            ],
            "argument --llama-server-base-url: "
            "runtime URL must be an absolute loopback http:// URL",
        ),
        (
            [
                "--runtime",
                "llama-server",
                "--llama-server-base-url",
                "http://user@127.0.0.1:8080",
                "--llama-server-model",
                "local-model",
            ],
            "argument --llama-server-base-url: "
            "runtime URL must be an absolute loopback http:// URL",
        ),
        (
            [
                "--runtime",
                "llama-server",
                "--llama-server-base-url",
                "http://user:secret@127.0.0.1:8080",
                "--llama-server-model",
                "local-model",
            ],
            "argument --llama-server-base-url: "
            "runtime URL must be an absolute loopback http:// URL",
        ),
        (
            [
                "--runtime",
                "llama-server",
                "--llama-server-base-url",
                "http://127.0.0.1:8080/base",
                "--llama-server-model",
                "local-model",
            ],
            "argument --llama-server-base-url: "
            "runtime URL must be an absolute loopback http:// URL",
        ),
        (
            [
                "--runtime",
                "llama-server",
                "--llama-server-base-url",
                "http://127.0.0.1:8080?token=x",
                "--llama-server-model",
                "local-model",
            ],
            "argument --llama-server-base-url: "
            "runtime URL must be an absolute loopback http:// URL",
        ),
        (
            [
                "--runtime",
                "llama-server",
                "--llama-server-base-url",
                "http://127.0.0.1:8080#fragment",
                "--llama-server-model",
                "local-model",
            ],
            "argument --llama-server-base-url: "
            "runtime URL must be an absolute loopback http:// URL",
        ),
        (
            [
                "--runtime",
                "llama-server",
                "--llama-server-base-url",
                "http://127.0.0.1:8080?",
                "--llama-server-model",
                "local-model",
            ],
            "argument --llama-server-base-url: "
            "runtime URL must be an absolute loopback http:// URL",
        ),
        (
            [
                "--runtime",
                "llama-server",
                "--llama-server-base-url",
                "http://127.0.0.1:8080#",
                "--llama-server-model",
                "local-model",
            ],
            "argument --llama-server-base-url: "
            "runtime URL must be an absolute loopback http:// URL",
        ),
        (
            [
                "--runtime",
                "llama-server",
                "--llama-server-base-url",
                "http://127.0.0.1:",
                "--llama-server-model",
                "local-model",
            ],
            "argument --llama-server-base-url: "
            "runtime URL must be an absolute loopback http:// URL",
        ),
        (
            [
                "--runtime",
                "llama-server",
                "--llama-server-base-url",
                "http://127.0.0.1:/",
                "--llama-server-model",
                "local-model",
            ],
            "argument --llama-server-base-url: "
            "runtime URL must be an absolute loopback http:// URL",
        ),
        (
            [
                "--runtime",
                "llama-server",
                "--llama-server-base-url",
                "http://127.0.0.1:invalid",
                "--llama-server-model",
                "local-model",
            ],
            "argument --llama-server-base-url: "
            "runtime URL must be an absolute loopback http:// URL",
        ),
        (
            [
                "--runtime",
                "llama-server",
                "--llama-server-base-url",
                "http://127.0.0.1:8080",
                "--llama-server-model",
                "",
            ],
            "argument --llama-server-model: value must not be empty",
        ),
    ],
)
def test_parse_args_preserves_runtime_validation_error_wording(
    argv: list[str],
    error: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit):
        local_runtime.parse_args(argv)

    assert f"home-ai-cluster-local: error: {error}\n" in capsys.readouterr().err


@pytest.mark.parametrize(
    "argv",
    [
        [
            "--runtime",
            "ollama",
            "--llama-server-base-url",
            "http://127.0.0.1:8080",
        ],
        [
            "--runtime",
            "ollama",
            "--llama-server-model",
            "local-model",
        ],
    ],
)
def test_parse_args_rejects_llama_server_arguments_for_ollama(
    argv: list[str],
) -> None:
    with pytest.raises(SystemExit):
        local_runtime.parse_args(argv)


@pytest.mark.parametrize(
    "argv",
    [
        ["--runtime", "llama-server"],
        [
            "--runtime",
            "llama-server",
            "--llama-server-model",
            "local-model",
        ],
        [
            "--runtime",
            "llama-server",
            "--llama-server-base-url",
            "http://127.0.0.1:8080",
        ],
        [
            "--runtime",
            "llama-server",
            "--llama-server-base-url",
            "https://127.0.0.1:8080",
            "--llama-server-model",
            "local-model",
        ],
        [
            "--runtime",
            "llama-server",
            "--llama-server-base-url",
            "http://runtime.example:8080",
            "--llama-server-model",
            "local-model",
        ],
        [
            "--runtime",
            "llama-server",
            "--llama-server-base-url",
            "http://127.0.0.1:8080",
            "--llama-server-model",
            "",
        ],
    ],
)
def test_parse_args_rejects_invalid_llama_server_composition(
    argv: list[str],
) -> None:
    with pytest.raises(SystemExit):
        local_runtime.parse_args(argv)


def test_parse_args_accepts_explicit_llama_server() -> None:
    args = local_runtime.parse_args(
        [
            "--runtime",
            "llama-server",
            "--llama-server-base-url",
            "http://[::1]:8080/",
            "--llama-server-model",
            "local-model",
            "--port",
            "8123",
        ]
    )

    assert args.runtime == "llama-server"
    assert args.llama_server_base_url == "http://[::1]:8080"
    assert args.llama_server_model == "local-model"
    assert args.host == "127.0.0.1"
    assert args.port == 8123


@pytest.mark.parametrize("host", ["0.0.0.0", "localhost", "::1", "192.0.2.10"])
def test_parse_args_rejects_non_loopback_native_host(host: str) -> None:
    with pytest.raises(SystemExit):
        local_runtime.parse_args(["--host", host])


@pytest.mark.parametrize("receiver_host", ["192.0.2.10", "2001:db8::10"])
def test_parse_args_accepts_concrete_non_loopback_receiver_host(
    receiver_host: str,
) -> None:
    args = local_runtime.parse_args(["--receiver-host", receiver_host])

    assert args.receiver_host == receiver_host
    assert args.receiver_port == 25042


@pytest.mark.parametrize(
    "receiver_host",
    ["0.0.0.0", "::", "127.0.0.1", "::1", "localhost", "example.invalid", "bad"],
)
def test_parse_args_rejects_non_concrete_receiver_host(receiver_host: str) -> None:
    with pytest.raises(SystemExit):
        local_runtime.parse_args(["--receiver-host", receiver_host])


def test_parse_args_keeps_native_and_receiver_ports_independent() -> None:
    args = local_runtime.parse_args(
        [
            "--port",
            "25043",
            "--receiver-host",
            "192.0.2.10",
            "--receiver-port",
            "26000",
        ]
    )

    assert args.port == 25043
    assert args.receiver_port == 26000


def test_parse_args_rejects_receiver_port_without_receiver_host() -> None:
    with pytest.raises(SystemExit):
        local_runtime.parse_args(["--receiver-port", "26000"])


def test_create_local_runtime_app_passes_composition_to_create_app(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = FastAPI()
    captured: dict[str, object] = {}

    def create_app(*, local_app_composition):
        captured["composition"] = local_app_composition
        return app

    monkeypatch.setattr(local_runtime, "create_app", create_app)
    args = local_runtime.parse_args(
        [
            "--runtime",
            "llama-server",
            "--llama-server-base-url",
            "http://127.0.0.1:8080",
            "--llama-server-model",
            "local-model",
        ]
    )

    result = local_runtime.create_local_runtime_app(args)

    assert result is app
    node = captured["composition"].node_registry.list_nodes()[0]
    assert node.adapters == ["llama-server"]


def test_create_local_runtime_app_constructs_explicit_vllm_composition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = FastAPI()
    captured: dict[str, object] = {}

    def create_app(*, local_app_composition):
        captured["composition"] = local_app_composition
        return app

    monkeypatch.setattr(local_runtime, "create_app", create_app)

    result = local_runtime.create_local_runtime_app(
        local_runtime.parse_args(
            [
                "--runtime",
                "vllm",
                "--vllm-base-url",
                "http://127.0.0.1:8000",
                "--vllm-model",
                "served-name",
            ]
        )
    )

    assert result is app
    adapter = captured["composition"].adapter_registry.list_adapters()[0]
    assert adapter.name == "vllm"
    assert adapter.base_url == "http://127.0.0.1:8000"
    assert adapter.model == "served-name"


def test_create_local_runtime_app_defaults_to_ollama_composition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = FastAPI()
    captured: dict[str, object] = {}

    def create_app(*, local_app_composition):
        captured["composition"] = local_app_composition
        return app

    monkeypatch.setattr(local_runtime, "create_app", create_app)

    result = local_runtime.create_local_runtime_app(local_runtime.parse_args([]))

    assert result is app
    node = captured["composition"].node_registry.list_nodes()[0]
    assert node.adapters == ["ollama"]
    adapter = captured["composition"].adapter_registry.list_adapters()[0]
    assert isinstance(adapter, OllamaAdapter)
    assert adapter.model == "llama3.2"
    assert adapter.disable_thinking is False


def test_create_local_runtime_app_passes_explicit_ollama_model_to_composition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = FastAPI()
    captured: dict[str, object] = {}

    def create_app(*, local_app_composition):
        captured["composition"] = local_app_composition
        return app

    monkeypatch.setattr(local_runtime, "create_app", create_app)

    result = local_runtime.create_local_runtime_app(
        local_runtime.parse_args(
            ["--runtime", "ollama", "--ollama-model", "configured-model"]
        )
    )

    assert result is app
    adapter = captured["composition"].adapter_registry.list_adapters()[0]
    assert isinstance(adapter, OllamaAdapter)
    assert adapter.model == "configured-model"


def test_create_local_runtime_app_passes_thinking_disable_to_composition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = FastAPI()
    captured: dict[str, object] = {}

    def create_app(*, local_app_composition):
        captured["composition"] = local_app_composition
        return app

    monkeypatch.setattr(local_runtime, "create_app", create_app)
    result = local_runtime.create_local_runtime_app(
        local_runtime.parse_args(["--runtime", "ollama", "--ollama-disable-thinking"])
    )

    assert result is app
    adapter = captured["composition"].adapter_registry.list_adapters()[0]
    assert isinstance(adapter, OllamaAdapter)
    assert adapter.disable_thinking is True


def test_create_local_runtime_app_attaches_loopback_browser_routes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api_app = FastAPI()
    browser_app = FastAPI()
    calls: list[str] = []

    monkeypatch.setattr(
        local_runtime,
        "create_local_runtime_composition",
        lambda **_: object(),
    )
    monkeypatch.setattr(local_runtime, "create_app", lambda **_: api_app)
    monkeypatch.setattr(
        local_runtime,
        "add_loopback_browser_routes",
        lambda app: calls.append("browser") or browser_app,
    )

    result = local_runtime.create_local_runtime_app(local_runtime.parse_args([]))

    assert result is browser_app
    assert calls == ["browser"]


def test_invalid_input_does_not_start_server(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    started = False

    def run(*args: object, **kwargs: object) -> None:
        nonlocal started
        started = True

    monkeypatch.setattr(local_runtime.uvicorn, "run", run)

    with pytest.raises(SystemExit):
        local_runtime.main(["--runtime", "llama-server"])

    assert not started


def test_main_starts_default_ollama_composition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = FastAPI()
    recorded: dict[str, object] = {}

    def create_local_runtime_app(args: argparse.Namespace) -> FastAPI:
        recorded["runtime"] = args.runtime
        return app

    def run(run_app: FastAPI, *, host: str, port: int) -> None:
        recorded["app"] = run_app
        recorded["host"] = host
        recorded["port"] = port

    monkeypatch.setattr(
        local_runtime,
        "create_local_runtime_app",
        create_local_runtime_app,
    )
    monkeypatch.setattr(local_runtime.uvicorn, "run", run)

    local_runtime.main([])

    assert recorded == {
        "runtime": "ollama",
        "app": app,
        "host": "127.0.0.1",
        "port": 25042,
    }


def test_main_does_not_wrap_uvicorn_owned_startup_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = FastAPI()
    handed_to_uvicorn: dict[str, object] = {}
    failure = RuntimeError()

    monkeypatch.setattr(local_runtime, "create_local_runtime_app", lambda _: app)

    def run(run_app: FastAPI, *, host: str, port: int) -> None:
        handed_to_uvicorn.update(app=run_app, host=host, port=port)
        raise failure

    monkeypatch.setattr(local_runtime.uvicorn, "run", run)

    with pytest.raises(RuntimeError) as raised:
        local_runtime.main([])

    assert raised.value is failure
    assert handed_to_uvicorn == {
        "app": app,
        "host": "127.0.0.1",
        "port": 25042,
    }


def test_receiver_enabled_startup_uses_one_shared_composition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    native_app = FastAPI()
    composition = object()
    native_app.state.local_app_composition = composition
    receiver_app = FastAPI()
    received: dict[str, object] = {}

    monkeypatch.setattr(local_runtime, "create_local_runtime_app", lambda _: native_app)

    def create_receiver_app(*, local_app_composition: object) -> FastAPI:
        received["composition"] = local_app_composition
        receiver_app.state.local_app_composition = local_app_composition
        return receiver_app

    monkeypatch.setattr(local_runtime, "create_receiver_app", create_receiver_app)

    async def run_servers(
        native: FastAPI, receiver: FastAPI, args: argparse.Namespace
    ) -> None:
        received.update(native=native, receiver=receiver, args=args)

    monkeypatch.setattr(local_runtime, "_run_receiver_enabled_servers", run_servers)

    local_runtime.main(["--receiver-host", "192.0.2.10"])

    assert received["composition"] is composition
    assert receiver_app.state.local_app_composition is composition
    assert received["native"] is native_app
    assert received["receiver"] is receiver_app
    assert received["args"].receiver_port == 25042


def test_receiver_enabled_lifecycle_stops_both_servers() -> None:
    created: list[object] = []
    served: list[object] = []
    completed: list[object] = []

    class Server:
        def __init__(self, config: object) -> None:
            self.config = config
            self.should_exit = False
            self.pending_signals: tuple[int, ...] = ()
            created.append(self)

        async def serve(self) -> None:
            served.append(self)
            try:
                while not self.should_exit:
                    await asyncio.sleep(0)
            except asyncio.CancelledError as error:
                raise AssertionError(
                    "server must complete without cancellation"
                ) from error
            completed.append(self)

    original_server = local_runtime.uvicorn.Server
    original_native_server = local_runtime._NativeServer
    original_receiver_server = local_runtime._ReceiverServer
    local_runtime.uvicorn.Server = Server
    local_runtime._NativeServer = Server
    local_runtime._ReceiverServer = Server
    try:

        async def stop_native() -> None:
            while not served:
                await asyncio.sleep(0)
            created[0].should_exit = True

        async def run() -> None:
            async with asyncio.TaskGroup() as group:
                group.create_task(
                    local_runtime._run_receiver_enabled_servers(
                        FastAPI(),
                        FastAPI(),
                        argparse.Namespace(
                            port=25042,
                            receiver_host="192.0.2.10",
                            receiver_port=25042,
                        ),
                    )
                )
                group.create_task(stop_native())

        asyncio.run(run())
    finally:
        local_runtime.uvicorn.Server = original_server
        local_runtime._NativeServer = original_native_server
        local_runtime._ReceiverServer = original_receiver_server

    assert len(created) == 2
    assert served == created
    assert completed == created
    assert all(server.should_exit for server in created)
    assert created[0].config.host == "127.0.0.1"
    assert created[0].config.port == 25042
    assert created[1].config.host == "192.0.2.10"
    assert created[1].config.port == 25042


def test_receiver_enabled_lifecycle_stops_sibling_after_server_failure() -> None:
    created: list[object] = []

    class Server:
        def __init__(self, config: object) -> None:
            self.config = config
            self.should_exit = False
            self.pending_signals: tuple[int, ...] = ()
            created.append(self)

        async def serve(self) -> None:
            if self is created[0]:
                raise RuntimeError("startup failed")
            while not self.should_exit:
                await asyncio.sleep(0)

    original_server = local_runtime.uvicorn.Server
    original_native_server = local_runtime._NativeServer
    original_receiver_server = local_runtime._ReceiverServer
    local_runtime.uvicorn.Server = Server
    local_runtime._NativeServer = Server
    local_runtime._ReceiverServer = Server
    try:
        with pytest.raises(ExceptionGroup):
            asyncio.run(
                local_runtime._run_receiver_enabled_servers(
                    FastAPI(),
                    FastAPI(),
                    argparse.Namespace(
                        port=25042,
                        receiver_host="192.0.2.10",
                        receiver_port=25042,
                    ),
                )
            )
    finally:
        local_runtime.uvicorn.Server = original_server
        local_runtime._NativeServer = original_native_server
        local_runtime._ReceiverServer = original_receiver_server

    assert len(created) == 2
    assert created[1].should_exit is True


def test_receiver_enabled_lifecycle_uses_one_signal_owner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recorded: list[tuple[object, object]] = []

    async def serve_until(server: object, sibling: object) -> None:
        recorded.append((server, sibling))

    monkeypatch.setattr(local_runtime, "_serve_until_sibling_stops", serve_until)

    asyncio.run(
        local_runtime._run_receiver_enabled_servers(
            FastAPI(),
            FastAPI(),
            argparse.Namespace(
                port=25042,
                receiver_host="192.0.2.10",
                receiver_port=25042,
            ),
        )
    )

    native_server, receiver_server = recorded[0]
    assert isinstance(native_server, local_runtime._NativeServer)
    assert isinstance(receiver_server, local_runtime._ReceiverServer)


def test_native_server_delays_uvicorn_signal_reraise(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    signal_calls: list[tuple[int, object]] = []
    raised_signals: list[int] = []
    previous_handlers: dict[int, object] = {}

    def install_signal_handler(signal_number: int, handler: object) -> object | None:
        signal_calls.append((signal_number, handler))
        return previous_handlers.setdefault(signal_number, None)

    monkeypatch.setattr(signal, "signal", install_signal_handler)
    monkeypatch.setattr(signal, "raise_signal", raised_signals.append)
    server = local_runtime._NativeServer(local_runtime.uvicorn.Config(FastAPI()))

    with server.capture_signals():
        server.handle_exit(signal.SIGINT, None)

    assert server.should_exit is True
    assert any(handler == server.handle_exit for _, handler in signal_calls)
    signal_numbers = {signal_number for signal_number, _ in signal_calls}
    assert len(signal_calls) == 2 * len(signal_numbers)
    assert all(
        sum(1 for seen_signal, _ in signal_calls if seen_signal == signal_number) == 2
        for signal_number in signal_numbers
    )
    assert server.pending_signals == (signal.SIGINT,)
    assert raised_signals == []


def test_receiver_enabled_lifecycle_reraises_signal_after_both_servers_complete(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []

    class NativeServer:
        def __init__(self, _: object) -> None:
            self.should_exit = False
            self.pending_signals = (signal.SIGINT,)

        async def serve(self) -> None:
            events.append("native-complete")

    class ReceiverServer:
        def __init__(self, _: object) -> None:
            self.should_exit = False

        async def serve(self) -> None:
            while not self.should_exit:
                await asyncio.sleep(0)
            events.append("receiver-complete")

    monkeypatch.setattr(local_runtime, "_NativeServer", NativeServer)
    monkeypatch.setattr(local_runtime, "_ReceiverServer", ReceiverServer)
    monkeypatch.setattr(
        local_runtime.signal,
        "raise_signal",
        lambda captured_signal: events.append(f"signal-{captured_signal}"),
    )

    asyncio.run(
        local_runtime._run_receiver_enabled_servers(
            FastAPI(),
            FastAPI(),
            argparse.Namespace(
                port=25042,
                receiver_host="192.0.2.10",
                receiver_port=25042,
            ),
        )
    )

    assert events == ["native-complete", "receiver-complete", f"signal-{signal.SIGINT}"]


def test_receiver_server_signal_capture_is_inert(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    signal_calls: list[object] = []
    monkeypatch.setattr(signal, "signal", lambda *args: signal_calls.append(args))
    server = local_runtime._ReceiverServer(local_runtime.uvicorn.Config(FastAPI()))

    with server.capture_signals():
        pass

    assert signal_calls == []


@pytest.fixture(autouse=True)
def isolated_retained_configuration(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
