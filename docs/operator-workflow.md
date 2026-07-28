# Canonical Operator Workflow

Status: Canonical

Date: 2026-07-17

This document is the shortest supported operator path for the current Home AI
Cluster architecture. It defines three distinct modes:

1. ordinary local-only operation;
2. ordinary explicit static multi-node operation;
3. explicit historical two-machine proof operation.

Use the [command reference](command-reference.md) for current syntax and option
lookup; this document remains the procedural sequence.

Local-only is the default, shortest, and least operationally complex path.
All external runtimes remain operator-owned. Home AI Cluster does not start,
stop, supervise, repair, or discover runtimes or remote machines.

## Daily-use overview

The ordinary process is started once and can serve repeated requests. `chat` and
`summarize` are finite clients of that already-running process; they do not
start it.

**Local-only (the shortest default path):**

```text
external runtime
  -> hac local
  -> repeated hac chat / hac summarize requests
  -> stop hac local
```

**Explicit static cluster:**

```text
receiver runtime + receiver hac local
  -> caller preflight/status when useful
  -> caller hac static-cluster
  -> repeated caller hac chat / hac summarize requests
  -> stop caller, then receiver
```

The second path adds an explicit caller, receiver, and retained declaration;
it does not replace the local-only default. A declared remote does not guarantee
remote execution because ordinary routing is local-first.

Inspection commands are finite observations, not mandatory prerequisites for
every startup or request:

- `hac preflight --declaration <DECLARATION_PATH>` checks static declaration
  coherence, not runtime or network availability.
- `hac health` observes the selected machine's local runtime composition, not
  declared remote nodes.
- `hac status --declaration <DECLARATION_PATH>` makes one bounded observation
  of the caller's local node and its declared remotes.

None starts, supervises, repairs, or guarantees later request success.
Historical proof runbooks and retained proof records are supporting evidence,
not required steps in either ordinary daily path.

## Mode 1: Ordinary local-only operation

### 1. Prepare the external local runtime

Install and start the runtime using its own supported procedure. Ensure its
required model is locally available. Home AI Cluster does not own this process.

### 2. Run local-only preflight

```sh
uv run home-ai-cluster-preflight
```

This checks only that every adapter declared by an ordinary local node resolves
in the ordinary local adapter registry. A coherent report does not prove that a
runtime, model, or application is available.

Preflight, health, and status results are human-readable by default. Automation
that needs their structured reports must request them explicitly:

```sh
uv run home-ai-cluster-preflight --json
uv run home-ai-cluster-health --json
uv run home-ai-cluster-status --declaration <DECLARATION_PATH> --json
```

This incremental output change applies to preflight, health, and status. Their
plain-text output is for ordinary operators; the explicit `--json` form retains
the compact structured output for automation.

### 3. Run local health

```sh
uv run home-ai-cluster-health
```

This observes the configured local runtime adapter. If it is not usable, repair
or start the external runtime, confirm the required model, then rerun health.

The default health report keeps declared state separate from adapter
observations. A completed snapshot may show an `unavailable`, `missing`, or
`probe-failed` adapter observation while the command itself still completes
successfully. Use `uv run home-ai-cluster-health --json` when automation needs
the existing compact structured snapshot.

### 4. Start the ordinary local-only application

```sh
uv run home-ai-cluster-local
```

The native endpoint is:

```text
http://127.0.0.1:8000/v1/chat
```

The same process also exposes the native bounded summarize endpoint:

```text
http://127.0.0.1:8000/v1/summarize
```

### 5. Send one native request

Replace `<OPERATOR_SUPPLIED_MESSAGE>` at invocation time. Do not retain the
supplied prompt or generated response in documentation or proof records.

```sh
uv run home-ai-cluster-chat --message "<OPERATOR_SUPPLIED_MESSAGE>"
```

This is the ordinary one-shot native client of the already running process. A
successful result includes cluster-owned node attribution. The native endpoint
remains `POST /v1/chat` for lower-level use when needed.

To summarize one bounded supplied text through that same process, use the
ordinary root client:

```sh
uv run home-ai-cluster summarize --text "<OPERATOR_SUPPLIED_TEXT>"
```

After installation, `hac summarize --text "<OPERATOR_SUPPLIED_TEXT>"` is the
short equivalent. The client also accepts one bounded UTF-8 source from stdin
when no explicit source is supplied, or one bounded strict-UTF-8 regular file
through `--file <PATH>`. `--text` and `--file` are mutually exclusive; either
explicit source ignores stdin. The client does not start or inspect the process.

### 6. Stop manually

Stop the ordinary application with normal process interruption. Leave the
external runtime running or stop it manually according to operator policy.

## Mode 2: Ordinary explicit static multi-node operation

Roles:

- **receiving machine or machines**: each runs an ordinary Home AI Cluster
  application plus an externally owned local runtime;
- **calling machine**: ordinary static multi-node process with one local node
  and one or more explicitly declared remote nodes.

The calling machine and every receiving machine must use compatible repository
revisions and remain on the same trusted LAN for the first reproduction. The
existing one-receiving-machine path remains the simple supported special case.

### 1. Prepare the calling machine and every receiving machine

On the calling machine and every receiving machine:

```sh
uv sync
```

Confirm compatible repository revisions. On every receiving machine, prepare
and start the external runtime and ensure the required model is locally
available. Home AI Cluster does not own that runtime.

### 2. Run static preflight and health on every receiving machine

On every receiving machine:

```sh
uv run home-ai-cluster-preflight
uv run home-ai-cluster-health
```

Preflight checks local static declaration coherence. Health observes each
receiving machine's configured local runtime adapter. Neither result proves LAN
reachability from the calling machine.

### 3. Start each receiving application

On every receiving machine represented by the declaration:

```sh
uv run home-ai-cluster-local --host 0.0.0.0 --port 8000
```

This explicit trusted-LAN exposure remains operator-owned. Restrict any firewall
allowance to the trusted LAN and remove it after use.

### 4. Select or create one retained declaration

On the calling machine, select or create one explicit, operator-owned
declaration at a stable local path:

```sh
DECLARATION="<DECLARATION_PATH>"
```

This shell variable is ordinary shell convenience, not a Home AI Cluster
contract. The project defines no default path, the CLI does not discover this
file, and the operator supplies its path explicitly. Do not treat the
declaration as disposable proof material, and do not commit private addresses
or machine-specific values.

For one remote, use these root keys:

```toml
remote_node_id = "<DECLARED_REMOTE_NODE_ID>"
remote_base_url = "http://<RECEIVER_ADDRESS>:8000"
```

For multiple remotes, use ordered tables:

```toml
[[remote_nodes]]
node_id = "<DECLARED_REMOTE_NODE_A_ID>"
base_url = "http://<RECEIVER_A_ADDRESS>:8000"

[[remote_nodes]]
node_id = "<DECLARED_REMOTE_NODE_B_ID>"
base_url = "http://<RECEIVER_B_ADDRESS>:8000"
```

Declaration order remains meaningful for the existing ordered remote behavior.
Do not add merging, include files, aliases, schema versions, environment
expansion, lookup precedence, or automatic discovery.

### 5. Run declaration-aware preflight

On the calling machine:

```sh
uv run home-ai-cluster-preflight --declaration "$DECLARATION"
```

This validates static declaration coherence and performs no remote network
observation. Run it before status or startup. An unknown key is an invalid
declaration; compare the retained file with the accepted single-remote or
multi-remote shape rather than reconstructing its schema from memory.

### 6. Inspect the declared static cluster

Run one finite, read-only inspection from the calling machine:

```sh
uv run home-ai-cluster-status --declaration "$DECLARATION"
```

The command validates the declaration before local or remote observation.
Coherent declaration validation does not prove live reachability. Status reports
separate local runtime status, remote application reachability, and remote
runtime availability. The fixed local node is first; each declared remote is
observed in declaration order. This operation does not start or stop runtimes,
repair services, mutate declarations, poll, or watch.

Status is human-readable by default. Use
`uv run home-ai-cluster-status --declaration "$DECLARATION" --json` when
automation needs the compact structured result. `unreachable`, `request-failed`,
`invalid-response`, `unavailable`, `observation-failed`, and `unknown` are
normalized result data in a completed status result, not whole-command failures.

If a receiver is unreachable, first check the retained declaration and receiving
process. Do not interpret that result automatically as a network fault. Correct
a wrong address or stale operator value in the retained declaration, rerun
preflight, then rerun status; do not delete and recreate the declaration merely
to repeat the workflow.

### 7. Optionally observe the calling machine's local runtime

```sh
uv run home-ai-cluster-health
```

This remains local health only; it does not inspect the remote node. It matters
because ordinary routing is local-first, so a usable local path normally wins.

### 8. Start the ordinary static multi-node process

On the calling machine:

```sh
uv run home-ai-cluster-static-cluster --declaration "$DECLARATION"
```

It binds the calling machine's native endpoint to:

```text
http://127.0.0.1:8000/v1/chat
```

The process owns only its HTTP client and application lifecycle; it does not
start, stop, supervise, repair, or discover the remote machine or runtime.

### 9. Send one ordinary request

```sh
uv run home-ai-cluster-chat --message "<OPERATOR_SUPPLIED_MESSAGE>"
```

A usable local candidate has precedence. The declared remote candidate is used
only through the accepted narrow fallback when the local runtime fails before
request execution with the accepted connection-unavailable condition. There is
no direct node targeting, retry loop, balancing, scoring, scheduling, or
discovery. A declared remote node does not guarantee that the first request uses
the remote path. Do not retain the supplied message or generated response in
proof records.

### 10. Stop in canonical order

1. stop the calling static multi-node process;
2. stop the receiving ordinary application;
3. remove any temporary firewall allowance;
4. leave or stop external runtimes manually according to operator policy.

The calling process and each receiving process remain foreground-bound. The
measured one-receiver exercise used a maximum of three simultaneously used
terminals: one receiver process, one caller process, and another available
caller terminal for finite inspection and the request. That is an observation,
not a universal terminal requirement. Normal process interruption is the
current stop mechanism; no PID file, detached mode, stop command, supervision,
or service manager is implied.

The retained [daily workflow evidence](daily-operator-workflow-evidence-result.md)
records one successful native two-machine exercise. Its only measured recovery
event was an invalid declaration; repeated same-day creation and deletion of
declarations was broader workflow friction. Foreground operation and normal
interruption were sufficient in that exercise, without establishing production
readiness or eliminating possible future lifecycle needs.

## Mode 3: Explicit historical two-machine proof operation

This preserves the historical distributed architecture proof. It is not the
ordinary static multi-node operating mode.

```sh
uv run home-ai-cluster-static-proof http://<receiving-lan-address>:8000
```

It uses explicit declared-remote-only selection for historical proof
reproduction. It remains documented until ordinary static multi-node operation
has been reproduced and its retained ordinary-mode proof record is complete.
For the detailed historical runbook, see `docs/static-two-machine-proof.md`.

## Mode comparison

| Mode | Calling process | Selection behavior | Preflight | Intended use |
| --- | --- | --- | --- | --- |
| Local-only | ordinary app | local only | local declarations | normal simplest use |
| Static multi-node | `home-ai-cluster-static-cluster` | local-first, narrow fallback | local + declared remote static declarations | ordinary explicit two-node operation |
| Historical proof | `home-ai-cluster-static-proof` | declared remote only | ordinary local preflight only unless separately invoked | historical architecture reproduction |

## Failure-layer lookup

Successful preflight does not imply runtime or network success.

| Layer | Owning surface |
| --- | --- |
| Static declaration coherence | `home-ai-cluster-preflight` |
| Local runtime health | `home-ai-cluster-health` |
| Declared local and remote live observations | `home-ai-cluster-status --declaration <path>` |
| Process startup and port conflict | Invoked process and operating system |
| Trusted-LAN reachability | Explicit trusted-LAN request |
| Receiving endpoint availability | Receiving application and explicit request |
| Routing and fallback execution | Existing request and explanation surfaces |
| Optional request history | History inspection and clearing commands |

Do not reinterpret one layer's failure as another layer's result.

## Process and port ownership

| Process | Purpose | Accepted port and exposure | Ownership |
| --- | --- | --- | --- |
| External AI runtime | Model execution | Runtime-specific | Operator-owned |
| Ordinary Home AI Cluster application | Native local or receiving endpoint | `8000`; loopback by default, trusted-LAN bind only when explicitly started that way | Home AI Cluster process, manually started |
| Static multi-node process | Calling-machine ordinary multi-node endpoint | `8000` on the calling machine loopback | Home AI Cluster process, manually started |
| Static proof process | Calling-machine historical proof endpoint | `8000` on the calling machine loopback | Home AI Cluster proof process, manually started |
| OpenAI-compatible process | Optional compatibility access | `8001`; loopback only | Separate optional Home AI Cluster process |

This table does not imply supervision or automatic lifecycle management.

## Recovery guidance

Use only supported manual actions:

- for an unknown declaration key, compare the retained file with the accepted
  single-remote or multi-remote shape before rerunning preflight;
- for a wrong address or stale operator value, correct the retained declaration,
  rerun preflight, then rerun status;
- do not delete and recreate a declaration merely to rerun the workflow;
- do not interpret an unreachable receiver as a network fault before checking
  the retained declaration and receiving process;
- start or repair the external runtime before rerunning health;
- ensure the required model is locally available;
- stop a conflicting process when an accepted fixed port is occupied;
- rerun the failed inspection step before repeating a request;
- stop Home AI Cluster processes with normal process interruption;
- clear optional request history explicitly when desired.

Do not infer automatic repair, retries, service restart, remote shutdown,
configuration mutation, or process supervision from this workflow.

## Declaration and lifecycle boundary

Declaration placement remains operator-owned. The CLI accepts an explicit path;
it does not automatically discover declarations, define a project default path,
apply lookup precedence, or merge configuration. Declarations must not contain
secret values. They do not grant remote lifecycle authority, and Home AI Cluster
does not own external runtimes. Any future project-defined declaration location,
automatic lookup behavior, or changed lifecycle surface requires an RFC.

## Privacy boundary

Do not retain in repository documentation or proof records real private LAN
addresses, prompts, generated responses, authorization values, credentials,
filesystem paths, raw exceptions, machine names, hardware details, personal
account details, or secrets. Use placeholders for operator-specific values.

## Detailed references

- `README.md`
- `docs/static-two-machine-proof.md`
- `docs/phase-8-ordinary-static-multi-node-proof.md`
- `RFC/RFC-0036-static-operator-preflight.md`
- `RFC/RFC-0037-canonical-operator-workflow.md`
- `RFC/RFC-0038-ordinary-static-multi-node-mode.md`
- `RFC/RFC-0041-explicit-static-cluster-status.md`
- `docs/daily-operator-workflow-evidence-result.md`

This document remains the canonical shortest operator sequence.
