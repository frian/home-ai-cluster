# Remote Summarize File Proof Runbook

Status: Ready to run

Date: 2026-07-28

## Purpose

This runbook prepares one standalone composition of accepted behavior: a local regular-file source; ordinary installed `hac summarize`; the caller-local native loopback endpoint; ordinary static-cluster routing; controlled caller-local pre-request runtime unavailability; one declared real remote receiver; remote `summarize` execution; and caller-owned declared-node attribution.

It is not Phase 19, a new capability, a new CLI feature, a routing or fallback rule, a file-upload feature, remote filesystem access, or a production-readiness claim.

> One ordinary `hac summarize --file` invocation can read a bounded local UTF-8 regular file on the caller machine, send only its decoded text to the caller-local Home AI Cluster process, follow accepted local-first pre-request fallback to one real declared remote receiver, execute `summarize` there, and return a normalized result attributed to the caller-declared remote node.

The live proof observes one caller native request, one receiver internal request, successful remote attribution, and controlled local-runtime unavailability. Exact retry and fallback-classification guarantees remain established by focused automated tests, not by new live telemetry.

Do not create the retained result, `docs/remote-summarize-file-proof.md`, until a later physical execution has actually succeeded.

## Topology and placeholders

Use exactly two physical machines on one trusted LAN.

| Role | Runs |
| --- | --- |
| Caller machine | installed `hac`; ordinary `hac static-cluster`; caller-local external runtime, initially available then deliberately stopped; temporary source file |
| Receiver machine | supported, operator-owned external runtime; ordinary trusted-LAN `hac local` process |

Use only these placeholders in working notes and retained evidence:

```text
<CALLER_MACHINE>
<RECEIVER_MACHINE>
<RECEIVER_LAN_ADDRESS>
<RECEIVER_HAC_PORT>
<CALLER_HAC_PORT>
<DECLARATION_PATH>
<DECLARED_REMOTE_NODE_ID>
<TEMP_SOURCE_PATH>
<MODEL_IDENTIFIER>
```

Current ordinary static-cluster startup owns fixed caller loopback port `8000`; `<CALLER_HAC_PORT>` means that fixed value here and is not a client option. Do not retain real addresses, hostnames, usernames, or paths.

## Preconditions

Both machines need the same current repository revision or installed package snapshot, Python and `uv` where a checkout is used, a supported runtime already installed and operator-owned, and the required model already present. The LAN must be trusted; limit any firewall allowance to it. Declarations contain no credentials.

For a checkout on each machine, confirm revision and clean tree, then prepare it:

```sh
git rev-parse HEAD
git status --short
uv sync
```

Refresh an intentionally stale installed snapshot only when needed:

```sh
uv tool install --force --no-cache .
hash -r
hac --help
```

Home AI Cluster does not install, download, start, stop, repair, or supervise external runtimes. Stop if revisions differ, worktree state is not understood, the LAN is not trusted, or evidence cannot be sanitized.

## 1. Create a temporary public source file on the caller

Create one temporary, regular, non-empty UTF-8 file below 65,536 bytes. It must contain no personal or private content and must be deleted during cleanup:

```sh
cat > <TEMP_SOURCE_PATH> <<'EOF'
Home AI Cluster routes capability-centered requests across explicitly declared personal machines. This temporary text exists only for a bounded remote summarization proof.
EOF
```

The path is interpreted and read only by the caller CLI. Strict UTF-8 decoding happens before its HTTP client is constructed; only decoded text enters the normalized summarize request. Do not retain the actual path or source text.

## 2. Prepare the receiver

On `<RECEIVER_MACHINE>`, start the chosen supported runtime through its own operator procedure and ensure `<MODEL_IDENTIFIER>` is already available. Prefer the default Ollama composition unless an existing environment makes llama-server simpler. For default composition, one finite local observation may confirm runtime availability:

```sh
hac health
```

Observe it only locally and transiently; it does not prove LAN reachability. Start the ordinary receiver in the foreground, exposed only to the trusted LAN:

```sh
hac local --host 0.0.0.0 --port <RECEIVER_HAC_PORT>
```

For the accepted explicit llama-server composition, use:

```sh
hac local \
  --runtime llama-server \
  --llama-server-base-url http://127.0.0.1:<LLAMA_SERVER_PORT> \
  --llama-server-model <MODEL_IDENTIFIER> \
  --host 0.0.0.0 \
  --port <RECEIVER_HAC_PORT>
```

`<LLAMA_SERVER_PORT>` is an invocation-local runtime placeholder; do not retain its real value. Keep receiver output transient. The receiver executes locally; it does not know the caller declaration or forward this request.

## 3. Create and validate the caller declaration

On `<CALLER_MACHINE>`, create one temporary operator-owned declaration at `<DECLARATION_PATH>` with exactly one remote node:

```toml
[[remote_nodes]]
node_id = "<DECLARED_REMOTE_NODE_ID>"
base_url = "http://<RECEIVER_LAN_ADDRESS>:<RECEIVER_HAC_PORT>"
```

The caller-local fixed node is implicit. The declaration contains topology only: do not add runtime, adapter, model, capability, credential, secret, or lifecycle fields. Ordinary static construction supplies the accepted remote capability set; the declaration does not target execution or configure a model.

Validate before startup:

```sh
hac preflight --declaration <DECLARATION_PATH>
```

Continue only if coherent. It is a local static check, not network or runtime evidence. An optional finite status check can establish current receiver reachability and runtime observations:

```sh
hac status --declaration <DECLARATION_PATH>
```

Treat an unexpected status as a stop condition and do not retain raw output.

## 4. Prepare and start the caller

Initially keep the caller external runtime available. For default composition, `hac health` observes the same default runtime composition that `hac static-cluster` will use, so it may confirm readiness before controlled shutdown. Do not use it to claim the state of a different explicit runtime composition.

Start the caller in the foreground:

```sh
hac static-cluster --declaration <DECLARATION_PATH>
```

It owns the fixed native caller endpoint:

```text
http://127.0.0.1:<CALLER_HAC_PORT>/v1/summarize
```

Do not send the request yet. If it cannot bind, stop; do not use another client target or a direct receiver request.

## 5. Establish the controlled local failure

After the caller process is running, stop only the caller-local external runtime. Leave the caller `hac static-cluster`, receiver `hac local`, and receiver runtime running. Do not change the declaration, disable the local node, modify capabilities, kill the caller, or manufacture a timeout or post-request failure.

This establishes the controlled precondition for the accepted local connection-unavailable-before-request outcome. The live CLI output alone does not expose the internal exception class. This procedure relies on that controlled precondition plus focused tests for exact classification and bounded traversal.

Do not run `hac health` after startup as evidence for an explicitly composed static caller: the standalone health command may not observe that composition.

## 6. Make one primary proof invocation

Invoke exactly once on the caller:

```sh
hac summarize --file <TEMP_SOURCE_PATH> --verbose
```

`--verbose` provides human-readable, cluster-owned attribution. Default content mode is insufficient; a second `--json` invocation is neither required nor permitted for this primary proof. Inspect output only transiently. Do not retain source text, generated summary text, or full verbose output.

## 7. Observe and record only sanitized live evidence

Observe transiently, without copying raw logs.

On the caller terminal, confirm one command invocation, successful exit, one caller process access observation for `POST /v1/summarize`, and verbose output with `Node: <DECLARED_REMOTE_NODE_ID>`.

On the receiver terminal, confirm one receiver process access observation for `POST /internal/cluster/request` and successful completion.

Retain only:

```text
Caller native summarize request observed once: yes
Receiver internal cluster request observed once: yes
Declared remote attribution observed: yes
Command exit status: success
```

Do not retain raw log lines, addresses, timestamps, payloads, generated content, or stack traces.

### Evidence limitation

The live proof does not independently establish a correlated request ID, exact internal exception class, durable local- or remote-attempt counter, or universal absence of retry.

It may combine controlled caller-runtime unavailability, one ordinary CLI invocation, one caller native request observation, one receiver internal request observation, and successful declared-node attribution with existing automated guarantees in:

- `tests/test_summarize_command.py` for file input and source-path absence from serialized requests;
- `tests/test_ordered_remote_fallback.py` for local-first traversal, accepted connection failure, no retry, and caller-owned summarize attribution;
- `tests/test_static_cluster.py` for ordinary static-cluster fallback; and
- `tests/test_routes.py` for the tagged summarize envelope and receiver-local execution.

## Failure handling

Stop the proof for every condition below. Do not reinterpret it as success or retry as part of the proof. Restore the environment, record only a sanitized failure category if useful, and investigate separately before any later attempt.

| Condition | Sanitized category |
| --- | --- |
| Caller command cannot reach `127.0.0.1:<CALLER_HAC_PORT>` | caller endpoint unavailable |
| Preflight rejects declaration | invalid declaration |
| Receiver unreachable | receiver unreachable |
| Receiver runtime unavailable | receiver runtime unavailable |
| Caller runtime remains available and result selects local | local runtime available |
| Request fails after transmission | post-transmission request failure |
| File invalid, non-regular, non-UTF-8, blank, or oversized | invalid local input |
| Verbose output lacks declared remote node | missing remote attribution |

One failed attempt means the retained proof has not succeeded.

## Success criteria

Accept a later retained proof only if one temporary valid regular UTF-8 file was read on the caller; exactly one ordinary CLI invocation was made; the caller observed one native summarize request; caller runtime was deliberately unavailable before invocation; receiver observed one internal cluster request; receiver runtime completed summarize; the CLI exited successfully; verbose output identified `<DECLARED_REMOTE_NODE_ID>`; no private data was retained; and cleanup completed. The focused tests above support exact-once routing internals in addition to the live observations.

## Cleanup

After the one invocation, perform these operator-owned steps in order:

1. Delete `<TEMP_SOURCE_PATH>`.
2. Stop the caller `hac static-cluster` process.
3. Restore or restart the caller external runtime.
4. Stop the receiver `hac local` process.
5. Remove `<DECLARATION_PATH>` if created only for this proof.
6. Remove any temporary trusted-LAN firewall allowance.
7. Confirm no proof process remains.
8. Confirm no raw logs or copied outputs were retained.
9. Confirm repository working trees remain clean.

Home AI Cluster must not automate these lifecycle actions.

## Later retained-proof template

Create `docs/remote-summarize-file-proof.md` only after a real successful run. It may use this privacy-safe template:

```markdown
# Remote Summarize File Proof

Status: Complete

Date: <DATE>

## Scope
## Environment
## Procedure
## Sanitized observations

Caller revision matched receiver revision: yes/no
Preflight coherent: yes/no
Caller runtime unavailable before request: yes/no
Caller native request observed once: yes/no
Receiver internal request observed once: yes/no
Declared remote attribution observed: yes/no
Command completed successfully: yes/no
Cleanup completed: yes/no

## Evidence limitation
## Result
## Cleanup
## Non-claims
```

## Non-claims

Even a successful run would not prove authentication, encryption, internet-safe exposure, production readiness, dynamic discovery, scheduling, load balancing, retries, supervision, automatic lifecycle, model selection, arbitrary document support, file upload, remote path access, multiple-file summarization, streaming, or Phase 19 completion.
