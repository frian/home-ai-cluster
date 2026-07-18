# Phase 17 Closeout

Status: Complete

Date: 2026-07-18

## Purpose

This document records completion of Phase 17:

> One operator can understand ordinary preflight, health, and status results
> directly in a terminal while one explicit stable machine-readable
> representation remains available.

## Phase outcome

The ordinary command surfaces are now human-readable by default:

```sh
uv run home-ai-cluster-preflight
uv run home-ai-cluster-health
uv run home-ai-cluster-status --declaration <DECLARATION_PATH>
```

Their explicit machine-readable forms are:

```sh
uv run home-ai-cluster-preflight --json
uv run home-ai-cluster-health --json
uv run home-ai-cluster-status --declaration <DECLARATION_PATH> --json
```

Output selection is explicit. There is no TTY detection, and piping or
redirection does not change the selected representation. Each command formats
one completed result at its CLI edge; no domain result or observation semantics
changed.

## Architectural result

Accepted [RFC-0048](../RFC/RFC-0048-human-readable-inspection-output.md)
established human-readable plain text as the default for exactly preflight,
health, and status, with explicit `--json` preserving the prior successful
compact JSON stdout contract byte-for-byte. Field names, ordering,
vocabularies, null values, empty arrays, trailing newline, stdout/stderr
allocation, and exit-status semantics remain unchanged.

The decision adds no TTY-dependent selection, generic renderer hierarchy, or
third-party formatting dependency. Command-specific pure formatters run at the
CLI boundary after one completed result exists. The implementation remains
local-first, privacy-first, engine-independent, capability-centered, explicit,
finite, boring, and small. Human output is not a stable parseable machine
contract.

## Completed sequence

### Investigation

[The investigation](human-readable-operator-output-investigation.md) recorded
compact-JSON readability friction in the retained daily operator exercise for
the finite preflight, health, and status commands. It rejected widening this
work to chat, history, explanations, server output, long-running commands, or a
global CLI framework.

### Accepted decision

[RFC-0048](../RFC/RFC-0048-human-readable-inspection-output.md), merged in PR
[#309](https://github.com/frian/home-ai-cluster/pull/309), accepted a human
default, explicit `--json`, no TTY detection, CLI-edge presentation only, exact
machine-readable compatibility, no semantic change, and no dependency or
generic rendering system.

### Preflight implementation

PR [#310](https://github.com/frian/home-ai-cluster/pull/310) updated
[preflight](../src/home_ai_cluster/static_preflight.py) and its [focused
tests](../tests/test_static_preflight.py). It provides a sectioned human report
by default and explicit compact JSON; coherent results exit 0, while completed
incoherent results remain ordered stdout data and exit 1. Nodes and issues stay
ordered, and empty collections are explicit.

### Health implementation

PR [#311](https://github.com/frian/home-ai-cluster/pull/311) updated [local
health](../src/home_ai_cluster/local_health_snapshot.py) and its [focused
tests](../tests/test_local_health_snapshot.py). It provides default human output
and explicit compact JSON while keeping declared state visibly separate from
adapter observations. `available`, `unavailable`, `missing`, and `probe-failed`
remain existing observation values; no synthetic overall health is created.
Completed snapshots exit 0, and rendering does not probe adapters again.

### Status implementation

PR [#312](https://github.com/frian/home-ai-cluster/pull/312) updated [status
command](../src/home_ai_cluster/status_command.py) and its [focused
tests](../tests/test_status_command.py). It provides default human output and
explicit compact JSON, preserves local-first and declaration/result order, and
retains existing application and runtime vocabularies. Normalized unavailable
and failure states remain completed result data with exit 0; rendering does not
recollect status or contact nodes again.

### Retained proof

PR [#313](https://github.com/frian/home-ai-cluster/pull/313) retained [the
proof runbook](phase-17-human-readable-inspection-output-proof.md) and [proof
result](phase-17-human-readable-inspection-output-proof-result.md). The proof
passed at revision `c31184b`.

Live evidence covered coherent preflight, health, and status in human and JSON
modes, plus redirected output. Each representation showed the same completed
facts and ordering. Health observed `unavailable`; status observed local
`unavailable`, remote `unreachable`, and runtime `unknown`. These normalized
non-happy-path values remained completed result data with exit 0 and empty
stderr.

Automated contract evidence proved that human incoherent preflight emits a
complete stdout report and exits 1, that JSON incoherent preflight emits exact
compact stdout and exits 1, and that normalized status failure states remain
successful completed results. The targeted tests passed, and the full suite
passed with 666 tests at proof time.

## Final command contracts

### Preflight

```text
default -> human-readable report
--json  -> compact structured report
```

- Coherent: stdout result, empty stderr, exit 0.
- Incoherent completed report: stdout result, empty stderr, exit 1.
- Invalid input or declaration: argparse stderr and no result stdout.
- Unexpected construction failure: `error: unable to construct static preflight report`
  on stderr, no stdout, exit 1.

### Health

```text
default -> human-readable snapshot
--json  -> compact structured snapshot
```

- Completed snapshot: stdout result, empty stderr, exit 0.
- `unavailable`, `missing`, and `probe-failed` observations remain result data.
- Whole-snapshot construction failure uses
  `error: unable to construct local health snapshot` on stderr and exits 1.
- Invalid parser input uses ordinary argparse behavior.

Declared health is not derived from adapter observation.

### Status

```text
default -> human-readable status result
--json  -> compact structured status result
```

- Completed result: stdout result, empty stderr, exit 0.
- `unreachable`, `request-failed`, `invalid-response`, `unavailable`,
  `observation-failed`, and `unknown` remain result data.
- Invalid declaration or runtime arguments use parser-mediated stderr failures.
- Unexpected construction failure uses
  `error: unable to construct cluster status result` on stderr and exits 1.

## Compatibility and migration

The no-option stdout contract changed for the three included commands.
Automation must now use `--json`. That output preserves the former compact JSON
representation byte-for-byte, including ordering and one trailing newline. This
makes no semantic-versioning claim and does not claim knowledge of external
consumers. Repository consumers and operator documentation were migrated
explicitly.

## Exit and stream behavior

| Command/result | stdout | stderr | Exit |
| --- | --- | --- | ---: |
| coherent preflight | selected complete result | empty | 0 |
| incoherent preflight | selected complete result | empty | 1 |
| completed health snapshot | selected complete result | empty | 0 |
| completed status result | selected complete result | empty | 0 |
| parser or declaration failure | empty | safe parser diagnostic | non-zero |
| unexpected construction failure | empty | fixed safe error | 1 |

Output format selection does not change the exit status.

## Privacy boundary

Human output uses only fields already present in completed results. It adds no
prompt or generated-response content, raw exceptions, credentials, topology or
identity, URL, declaration path, logging, retention, telemetry, or persistence.
The retained proof redacted `<REDACTED_TEMPORARY_ENDPOINT>` and
`<REDACTED_LOW_LEVEL_CONNECTION_DIAGNOSTIC>`; their original values are not
retained.

## Proof deviation

The original proof plan requested a live incoherent preflight. Accepted ordinary
CLI inputs cannot construct that state in the current bounded wiring: the fixed
local node declares registered `ollama`, while remotes use `remote-http` and
remain outside local adapter-resolution checks. Targeted tests therefore provide
the incoherent completed-result evidence. No wiring or production behavior was
modified merely to create a proof state.

This does not weaken the tested public completed-result presentation and exit
contract. It does mean the proof does not claim that an operator can configure an
incoherent adapter registry through supported ordinary inputs.

## What Phase 17 does not establish

Phase 17 does not establish a general output framework, stable parseable human
output, localization, color or terminal UI, TTY-dependent behavior, watch mode,
polling, background monitoring, progress indicators, chat/request-result human
formatting, history/explanation formatting, server-log changes, new
observations, health semantics, routing or fallback changes, declaration
changes, retries, discovery, lifecycle management, supervision, dashboard,
database, Docker, or Kubernetes. It does not expand RFC-0048 scope beyond
preflight, health, and status.

## Phase completion statement

Phase 17 is complete because retained operator evidence demonstrated the
readability need; the scope was investigated; RFC-0048 was accepted; all three
bounded implementations were merged; exact JSON compatibility and output
contracts are covered by tests; canonical operator documentation was migrated;
one privacy-safe retained proof passed; redirected output retained explicit
representation; live normalized non-happy-path states remained understandable
result data; and the architectural proof deviation was recorded without changing
production behavior.

> One operator can understand ordinary preflight, health, and status results
> directly in a terminal while one explicit stable machine-readable
> representation remains available.

## Follow-up

- Merge this closeout record.
- Then update `ROADMAP.md`, `README.md`, and any maintained public documentation
  index in one separate small documentation PR.
- Do not infer a Phase 18 scope from this closeout.
- Extending human-readable output to another command requires new observed need
  and investigation; architectural changes require an RFC.
