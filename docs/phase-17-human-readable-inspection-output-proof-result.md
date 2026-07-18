# Phase 17 Human-Readable Inspection Output Proof Result

Date: 2026-07-18

Status: Passed

## Environment

The proof ran from the ordinary repository checkout at revision:

```text
c31184b
```

It used the installed `uv run` preflight, health, and status commands. Status
used one temporary, uncommitted declaration with the synthetic remote identity
`receiver-a`. No runtime or remote service was started, stopped, repaired, or
reconfigured for this proof.

## Privacy review

The temporary declaration endpoint was reviewed and redacted as
`<REDACTED_TEMPORARY_ENDPOINT>`. Temporary declaration and capture files were
not retained. The live health observation included a low-level connection
diagnostic in its reason; that value is redacted below as
`<REDACTED_LOW_LEVEL_CONNECTION_DIAGNOSTIC>`. No private address, URL, hostname,
absolute path, credential, prompt, response, raw exception trace, username, or
machine detail is retained.

## Evidence model

This result distinguishes:

- **Live operator evidence:** installed-command invocations for supported
  ordinary inputs.
- **Automated contract evidence:** existing focused CLI tests for the completed
  incoherent-preflight contract, which cannot be configured through accepted
  ordinary inputs.

## Live execution summary

| Case | Representation | Exit | Stderr |
| --- | --- | ---: | --- |
| Coherent preflight | human | 0 | empty |
| Coherent preflight | `--json` | 0 | empty |
| Local health | human | 0 | empty |
| Local health | `--json` | 0 | empty |
| Static-cluster status | human | 0 | empty |
| Static-cluster status | `--json` | 0 | empty |

## Preflight live evidence

### Human

```text
Preflight: coherent
Operating mode: local-only

Nodes:
- local
  Capabilities: chat
  Declared adapters: ollama

Registered adapters: ollama
Issues: none
```

The default result was directly readable, showed the complete coherent report,
and exited 0 with empty stderr.

### JSON

```json
{"status":"coherent","operating_mode":"local-only","nodes":[{"node_id":"local","capabilities":["chat"],"declared_adapters":["ollama"]}],"registered_adapters":["ollama"],"issues":[]}
```

The explicit JSON invocation exited 0 with empty stderr and emitted one compact
JSON value with one trailing newline and no human heading. It represented the
same status, operating mode, node order, capability, declared-adapter,
registered-adapter, and empty-issues facts as the human result.

## Preflight automated incoherent evidence

The following targeted command passed 2 tests:

```sh
uv run pytest \
  tests/test_static_preflight.py::test_main_human_emits_incoherent_report_and_exits_nonzero \
  tests/test_static_preflight.py::test_main_json_emits_incoherent_report_and_exits_nonzero
```

`test_main_human_emits_incoherent_report_and_exits_nonzero` asserts complete
human stdout, empty stderr, and exit 1. Its automated expected-output assertion
includes this privacy-safe excerpt:

```text
Preflight: incoherent
...
Issues:
- Status: missing-adapter
  Node: local
  Adapter: missing-adapter
  Reason: declared adapter is not present in the inspected registry
```

`test_main_json_emits_incoherent_report_and_exits_nonzero` asserts the exact
compact JSON serialization plus one trailing newline, complete issue fields,
empty stderr, and non-zero (specifically 1) exit behavior. This is automated
contract evidence, not observed installed-command terminal output.

## Health live evidence

### Human

```text
Local health

Nodes:
- local
  Name: Local node

  Declared state:
    Availability: available
    Healthy: true
    Reason: none
    Capabilities: chat
    Adapters: ollama

  Adapter observations:
  - Adapter: ollama
    Status: unavailable
    Reason: <REDACTED_LOW_LEVEL_CONNECTION_DIAGNOSTIC>
```

The default health output was directly readable and exited 0 with empty stderr.
Declared availability and health remained visibly separate from the direct
adapter observation. No synthetic overall-health value appeared.

### JSON

The explicit JSON invocation exited 0 with empty stderr and emitted one compact
JSON object with no human prose. It contained the same local node/name, declared
availability `available`, declared health `true`, null declared reason,
capability and adapter order, adapter `unavailable` status, and the same
redacted reason field as the human result.

## Status live evidence

### Human

```text
Cluster status
Declaration: coherent

Nodes:
- local
  Application status: local
  Runtime status: unavailable
- receiver-a
  Application status: unreachable
  Runtime status: unknown
```

The completed status result exited 0 with empty stderr. It showed local first
and `receiver-a` second, preserving the temporary declaration order.

### JSON

```json
{"declaration_status":"coherent","nodes":[{"node_id":"local","application_status":"local","runtime_status":"unavailable"},{"node_id":"receiver-a","application_status":"unreachable","runtime_status":"unknown"}]}
```

The explicit JSON invocation exited 0 with empty stderr and emitted one compact
JSON object with one trailing newline and no human prose. It preserved the same
declaration status, local-first order, remote order, and normalized values as
the human result.

## Human-versus-JSON comparison

For each live command, no flag selected human text and `--json` selected one
compact JSON value. The paired invocations represented the same completed
semantic facts and ordering in the observed environment. The live proof confirms
the explicit compact JSON path; automated implementation tests establish the
byte-for-byte historical JSON compatibility contract.

## Redirected-output evidence

Preflight was run with stdout redirected to temporary files in both modes. The
no-flag capture remained headed `Preflight: coherent`; the `--json` capture
remained one compact JSON object. Both exited 0 with empty stderr. Representation
therefore remained explicit under redirection; no TTY behavior was used or
tested.

## Exit-status evidence

Coherent preflight, completed health, and completed status each exited 0 in both
representations. The automated incoherent-preflight tests prove that a completed
incoherent report is still written to stdout with empty stderr and exits 1 in
both representations. The live `unavailable`, `unreachable`, and `unknown`
values remained completed result data with exit 0.

## Ordering evidence

Live preflight preserved its one local node and adapter ordering in both forms.
Live health preserved its one adapter observation. Live status preserved fixed
`local` first followed by declared `receiver-a`; the same order appeared in
human and JSON output.

## Normalized-state evidence

Live evidence contained health `unavailable` and status `unavailable`,
`unreachable`, and `unknown`. These values remained ordinary completed output
data and did not produce stderr or a non-zero status exit.

The targeted command also included the automated parametrized test
`tests/test_status_command.py::test_normalized_node_failures_exit_successfully`.
It ran 3 cases and verified compact successful output for normalized
`observation-failed` plus `unreachable`, `request-failed`, and
`invalid-response` result states.

## Validation

The targeted automated evidence command passed 5 tests: 2 incoherent-preflight
CLI-path tests and 3 normalized-status parametrizations. The full repository
suite completed with 666 passed tests. `uv run ruff check .` passed and `git diff
--check` passed. `uv run ruff format --check .` reported only the repository's
known 17 pre-existing files; none were reformatted.

## Architectural observation

Live incoherent preflight is not constructible through the accepted ordinary CLI
surface: the local node declares `ollama`, the ordinary local registry contains
`ollama`, and declared remotes use `remote-http` while remaining outside local
adapter-resolution checks. This is an architectural property of the current
bounded system, not a request for a new diagnostic mechanism.

## Findings

The three default results were directly understandable as plain text. Explicit
JSON retained machine-readable compact shapes, status ordering remained stable,
and normalized non-happy-path values remained result data. The retained evidence
contains no indication that representation selection changed evaluation or
observation behavior.

## Deviations

The original proof plan requested a live incoherent preflight. Repository
inspection and a bounded live attempt established that this state is not
constructible through the accepted ordinary CLI surface. This proof therefore
uses existing targeted CLI tests for that contract. No application wiring or
production behavior was changed.

This deviation does not weaken proof of the public incoherent-result contract:
the tests execute the same CLI `main` presentation and exit paths with a
completed report. It does mean this proof does not claim that an ordinary
operator can currently configure an incoherent adapter registry through
supported inputs.

## Conclusion

The revised Phase 17 proof passed. It retains live privacy-safe evidence for all
reachable installed-command states and automated contract evidence for the
completed incoherent-preflight state, while keeping output selection explicit,
ordering stable, normalized failures non-fatal, and all retained material within
the privacy boundary. This record does not mark Phase 17 complete.
