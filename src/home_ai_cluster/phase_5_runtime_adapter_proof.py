"""Explicit real-local proof for the RFC-0030 runtime adapter boundary."""

import argparse
import asyncio
import json
from collections.abc import Callable, Sequence
from urllib.parse import urlsplit

from home_ai_cluster.adapters.base import RuntimeAdapter, RuntimeAdapterUnavailableError
from home_ai_cluster.adapters.llama_server import LlamaServerAdapter
from home_ai_cluster.adapters.ollama import OllamaAdapter
from home_ai_cluster.core.models import (
    Capability,
    ChatMessage,
    ClusterRequest,
    RuntimeResult,
)

LOCAL_HOSTS = {"127.0.0.1", "::1", "localhost"}


def local_http_url(value: str) -> str:
    """Validate one explicit loopback HTTP URL for this local-only proof."""
    parsed = urlsplit(value)
    if parsed.scheme != "http" or parsed.hostname not in LOCAL_HOSTS:
        raise argparse.ArgumentTypeError(
            "runtime URL must be an absolute loopback http:// URL"
        )
    return value.rstrip("/")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse explicit local runtime choices for the proof command."""
    parser = argparse.ArgumentParser(
        prog="home-ai-cluster-runtime-adapter-proof",
        description="Run the explicit RFC-0030 local runtime adapter proof.",
    )
    parser.add_argument(
        "--adapter",
        action="append",
        choices=["ollama", "llama-server"],
        help="Run only the named adapter; repeat to run both explicitly.",
    )
    parser.add_argument(
        "--ollama-base-url",
        type=local_http_url,
        default="http://127.0.0.1:11434",
    )
    parser.add_argument("--ollama-model", default="llama3.2")
    parser.add_argument(
        "--llama-server-base-url",
        type=local_http_url,
        default="http://127.0.0.1:8080",
    )
    parser.add_argument("--llama-server-model", default="phase-5-gemma")
    return parser.parse_args(argv)


def create_request() -> ClusterRequest:
    """Create the one small cluster-owned chat request for the proof."""
    return ClusterRequest(
        messages=[
            ChatMessage(role="system", content="Reply with one word."),
            ChatMessage(role="user", content="Ready?"),
        ],
        capability=Capability(name="chat"),
    )


def create_adapters(args: argparse.Namespace) -> dict[str, RuntimeAdapter]:
    """Construct both concrete adapters explicitly, without runtime discovery."""
    return {
        "ollama": OllamaAdapter(
            base_url=args.ollama_base_url,
            model=args.ollama_model,
        ),
        "llama-server": LlamaServerAdapter(
            base_url=args.llama_server_base_url,
            model=args.llama_server_model,
        ),
    }


def selected_adapters(
    adapters: dict[str, RuntimeAdapter],
    selected_names: list[str] | None,
) -> list[RuntimeAdapter]:
    """Return the explicitly requested adapters, or both proof adapters."""
    names = selected_names or ["ollama", "llama-server"]
    return [adapters[name] for name in names]


def result_summary(result: RuntimeResult) -> dict[str, str | int | None]:
    """Return proof output without printing the prompt or generated content."""
    return {
        "adapter": result.adapter,
        "model": result.model,
        "content_length": len(result.content),
    }


async def run_proof(
    adapters: list[RuntimeAdapter],
    request: ClusterRequest,
    *,
    output: Callable[[str], None] = print,
) -> int:
    """Execute each explicitly selected adapter through RuntimeAdapter."""
    for adapter in adapters:
        try:
            result = await adapter.chat(request)
        except RuntimeAdapterUnavailableError as exc:
            output(
                json.dumps(
                    {"adapter": adapter.name, "error": type(exc).__name__},
                    sort_keys=True,
                )
            )
            return 1

        output(json.dumps(result_summary(result), sort_keys=True))

    return 0


def main(argv: Sequence[str] | None = None) -> None:
    """Run the opt-in proof; runtimes must already be running on loopback."""
    args = parse_args(argv)
    adapters = selected_adapters(create_adapters(args), args.adapter)
    exit_code = asyncio.run(run_proof(adapters, create_request()))
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
