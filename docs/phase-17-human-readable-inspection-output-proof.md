# Phase 17 Human-Readable Inspection Output Proof

## Purpose

This runbook proves the accepted RFC-0048 presentation boundary for the three
finite inspection commands:

```text
home-ai-cluster-preflight
home-ai-cluster-health
home-ai-cluster-status
```

It proves their directly readable default output and explicit compact `--json`
output without changing their evaluation, ordering, normalized vocabularies,
stream boundaries, or exit semantics. It is a documentation-and-evidence
procedure, not a new operator workflow, diagnostic mechanism, or Phase 17
closeout.

## Evidence model

### Live operator evidence

Use the installed `uv run` commands for states reachable through accepted
ordinary inputs. Capture stdout, stderr, and exit status separately. Retain
only privacy-reviewed excerpts.

### Automated contract evidence

Use existing focused CLI tests where the current accepted command surface cannot
construct a completed state. Label that evidence as automated; do not describe it
as a live terminal exercise.

## Preconditions

- Run from one revision containing the three merged RFC-0048 command slices.
- Use the ordinary local repository checkout and `uv run` commands.
- Do not start, stop, repair, or reconfigure an external runtime or remote
  service to force a preferred observation.
- Use a temporary static declaration outside committed repository data for the
  status command.

## Privacy rules

Before retaining evidence, inspect every captured value. Do not retain private
addresses, URLs, hostnames, absolute paths, credentials, prompts, generated
responses, raw exceptions, terminal prompts, usernames, or machine details.
Use `receiver-a` for the temporary remote identity. Replace any unsafe completed
result value with a descriptive redaction without changing the demonstrated
status semantics.

## Why live incoherent preflight is not constructible

The ordinary local node declares `ollama`, and the ordinary local adapter
registry contains `ollama`. Inline and file-declared remotes use the accepted
`remote-http` boundary, while remote nodes are intentionally excluded from local
adapter-resolution checks. Therefore every supported ordinary installed-CLI
configuration in the current bounded product produces a coherent preflight
unless application wiring itself changes.

This is an architectural property of the current bounded system, not a proof
failure, missing feature, or request for a diagnostic mechanism. The completed
incoherent-report contract is proven through existing automated CLI tests.

## Temporary declaration

Create a temporary, uncommitted declaration equivalent to:

```toml
remote_node_id = "receiver-a"
remote_base_url = "http://127.0.0.1:<TEMPORARY_PORT>"
```

Review the actual endpoint before retaining evidence. Do not commit the
declaration or its endpoint.

## Exit-status capture method

For each command, capture streams before reading output and preserve the command
exit status without placing the command in an unchecked pipeline:

```sh
set +e
<COMMAND> > <TEMPORARY_STDOUT_FILE> 2> <TEMPORARY_STDERR_FILE>
status=$?
set -e
```

Record `status` and whether stderr is empty. Delete temporary captures after the
privacy review.

## Live proof steps

### Coherent preflight human

```sh
uv run home-ai-cluster-preflight
```

Confirm exit 0, empty stderr, `Preflight: coherent`, operating mode, ordered
nodes, capabilities, declared adapters, registered adapters, and `Issues: none`.

### Coherent preflight JSON

```sh
uv run home-ai-cluster-preflight --json
```

Confirm exit 0, empty stderr, one compact JSON object with one trailing newline,
no human heading, and the same status, node, adapter, and issue facts.

### Health human

```sh
uv run home-ai-cluster-health
```

Confirm exit 0, empty stderr, and visibly separate `Declared state` and `Adapter
observations` sections. Record declared availability, health, reason,
capabilities, adapters, and each observed status and safe reason.

### Health JSON

```sh
uv run home-ai-cluster-health --json
```

Confirm exit 0, empty stderr, one compact JSON object, no human prose, and the
same declared and observed facts in their existing order. Confirm that no
synthetic overall health value appears.

### Status human

```sh
uv run home-ai-cluster-status --declaration <TEMPORARY_DECLARATION>
```

Confirm exit 0, empty stderr, coherent declaration status, local node first,
`receiver-a` after local, and the application and runtime status values for both.
Any normalized non-happy-path value remains result data.

### Status JSON

```sh
uv run home-ai-cluster-status --declaration <TEMPORARY_DECLARATION> --json
```

Confirm exit 0, empty stderr, one compact JSON object, no human prose, local
first, remote declaration order, and the same completed status facts as the
human result.

### Redirected-output check

Redirect both preflight forms to temporary files:

```sh
uv run home-ai-cluster-preflight > <TEMPORARY_HUMAN_FILE>
uv run home-ai-cluster-preflight --json > <TEMPORARY_JSON_FILE>
```

Confirm the first remains human text headed `Preflight: coherent` and the
second remains one compact JSON object. Do not use or test TTY detection.

## Automated incoherent-preflight proof

Run the existing focused CLI-path tests:

```sh
uv run pytest \
  tests/test_static_preflight.py::test_main_human_emits_incoherent_report_and_exits_nonzero \
  tests/test_static_preflight.py::test_main_json_emits_incoherent_report_and_exits_nonzero
```

These tests call the same command `main` presentation and exit paths with a
completed injected incoherent report. They prove default human output and
explicit compact JSON output, complete stdout result data, empty stderr, exit
status 1, issue fields/order, and exact compact JSON serialization with one
trailing newline. They do not claim that an ordinary operator can configure an
incoherent adapter registry through supported inputs.

When no live non-happy-path health or status value occurs, run the narrowest
existing normalized-status contract test and label it automated evidence:

```sh
uv run pytest \
  tests/test_status_command.py::test_normalized_node_failures_exit_successfully
```

## Expected invariants

- No flag selects human plain text; `--json` selects compact JSON.
- Representation selection does not change completed semantic facts, ordering,
  stderr, or exit status.
- JSON output is one value with one trailing newline and contains no human prose.
- Health never combines declared facts and observations into a synthetic overall
  health state.
- Status preserves local-first and declared-remote order.
- Completed normalized unavailable or failed observations remain result data.
- The proof retains no unsafe operator-specific material.

## Cleanup

Delete the temporary declaration and all captured stdout/stderr files after the
privacy review. Do not commit temporary material.

## Pass criteria

The proof passes when live evidence covers coherent preflight, health, status,
both representations, redirected-output selection, and their successful exit
statuses; automated evidence covers the completed incoherent-preflight contract;
and all retained excerpts remain privacy-safe. Run the full repository suite and
normal validation before recording a passed result.

## Non-goals

This proof does not change application code, tests, RFCs, the roadmap, routing,
health, declarations, runtime ownership, service lifecycle, discovery,
monitoring, or Phase 17 completion status. It does not prove production
readiness or introduce a new operator diagnostic surface.
