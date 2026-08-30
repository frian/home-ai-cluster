"""Additive root command for existing ordinary operator commands."""

import sys
from collections.abc import Callable, Sequence
from importlib.metadata import version

from home_ai_cluster import (
    aider_command,
    chat_command,
    classify_command,
    code_command,
    code_file_command,
    config_command,
    external_information_command,
    local_health_snapshot,
    local_runtime,
    openai_compatibility,
    static_cluster,
    static_preflight,
    status_command,
    summarize_command,
)

_HELP = """usage: home-ai-cluster <command> [arguments...]

Foreground process commands:
  local           Run one local runtime process.
  static-cluster  Run one static-cluster process.
  compatibility   Run one loopback compatibility process.

Finite commands:
  aider           Run one bounded Aider code edit.
  external-information  Acquire one bounded source-grounded chat request.
  chat            Send one ordinary chat request.
  code            Send one bounded textual code request.
  code-file       Replace one selected file from one bounded code request.
  classify        Send one ordinary classify request.
  summarize       Send one ordinary summarize request.
  preflight       Inspect static declaration coherence.
  health          Observe local runtime health.
  status          Inspect static-cluster status.
  config          Manage retained configuration.

Use 'home-ai-cluster <command> --help' for command-specific help.
"""

_COMMANDS: dict[str, Callable[[Sequence[str] | None], None]] = {
    "local": local_runtime.main,
    "static-cluster": static_cluster.main,
    "compatibility": openai_compatibility.main,
    "aider": aider_command.main,
    "external-information": external_information_command.main,
    "chat": chat_command.main,
    "code": code_command.main,
    "code-file": code_file_command.main,
    "classify": classify_command.main,
    "summarize": summarize_command.main,
    "preflight": static_preflight.main,
    "health": local_health_snapshot.main,
    "status": status_command.main,
    "config": config_command.main,
}


def _write_help() -> None:
    sys.stdout.write(_HELP)


def _unknown_command() -> None:
    print("error: unknown command", file=sys.stderr)
    raise SystemExit(2)


def main(argv: Sequence[str] | None = None) -> None:
    """Dispatch one accepted ordinary command without changing its behavior."""
    arguments = list(sys.argv[1:] if argv is None else argv)

    if not arguments or arguments in (["--help"], ["-h"]):
        _write_help()
        return

    if arguments == ["--version"]:
        print(version("home-ai-cluster"))
        return

    delegated_main = _COMMANDS.get(arguments[0])
    if delegated_main is None:
        _unknown_command()

    delegated_main(arguments[1:])
