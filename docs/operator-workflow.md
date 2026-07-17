# Canonical Operator Workflow

Status: Canonical

Date: 2026-07-17

This document is the shortest supported operator path for the current Home AI
Cluster architecture. It defines three distinct modes:

1. ordinary local-only operation;
2. ordinary explicit static multi-node operation;
3. explicit historical two-machine proof operation.

Local-only is the default, shortest, and least operationally complex path.
All external runtimes remain operator-owned. Home AI Cluster does not start,
stop, supervise, repair, or discover runtimes or remote machines.

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

### 3. Run local health

```sh
uv run home-ai-cluster-health
```

This observes the configured local runtime adapter. If it is not usable, repair
or start the external runtime, confirm the required model, then rerun health.

### 4. Start the ordinary local-only application

```sh
uv run uvicorn home_ai_cluster.main:app --reload
```

The native endpoint is:

```text
http://127.0.0.1:8000/v1/chat
```

### 5. Send one native request

Replace `<operator-supplied-message>` at invocation time. Do not retain the
supplied prompt or generated response in documentation or proof records.

```sh
curl -s http://127.0.0.1:8000/v1/chat \
  -H 'content-type: application/json' \
  -d '{
    "messages": [{"role": "user", "content": "<operator-supplied-message>"}],
    "capability": "chat"
  }'
```

A successful response includes cluster-owned node attribution.

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

### 3. Determine each receiving LAN address

For every receiving machine, use its current trusted-LAN address at invocation
time:

```text
<receiving-lan-address>
```

Do not commit a real private address to repository documentation or proof
records.

### 4. Start each receiving application

On every receiving machine represented by the declaration:

```sh
uv run uvicorn home_ai_cluster.main:app --host 0.0.0.0 --port 8000
```

Restrict any firewall allowance to the trusted LAN and remove it after use.

### 5. Run calling-machine multi-node preflight

On the calling machine:

```sh
uv run home-ai-cluster-preflight \
  --remote-node-id <remote-node-id> \
  --remote-base-url http://<receiving-lan-address>:8000
```

This validates one local declaration, one explicit remote declaration, and
adapter-name resolution against the inspected adapter registry. It is the
simple one-receiving-machine path; use the declaration in the next step to
inspect one or more declared remotes. It does not validate DNS, LAN
reachability, the receiving application, receiving runtime, receiving model,
remote execution, or fallback success. It performs no network request.

### 6. Inspect one declared static cluster

After preparing every receiving application represented by the declaration,
create one explicit declaration on the calling machine. Declaration order is
the remote observation order:

```toml
[[remote_nodes]]
node_id = "remote-a"
base_url = "http://<receiving-a-lan-address>:8000"

[[remote_nodes]]
node_id = "remote-b"
base_url = "http://<receiving-b-lan-address>:8000"
```

Run one finite, read-only inspection from the calling machine:

```sh
uv run home-ai-cluster-status \
  --declaration <path-to-static-cluster-declaration>
```

The command validates the declaration before local or network observation. Its
compact result has this shape:

```json
{
  "declaration_status": "coherent",
  "nodes": [
    {
      "node_id": "local",
      "application_status": "local",
      "runtime_status": "available"
    },
    {
      "node_id": "remote-a",
      "application_status": "reachable",
      "runtime_status": "available"
    },
    {
      "node_id": "remote-b",
      "application_status": "unreachable",
      "runtime_status": "unknown"
    }
  ]
}
```

`declaration_status = coherent` means static declaration validation succeeded;
it does not mean every application or runtime is available. The fixed local node
is always first. Each declared remote appears exactly once in declaration order.
Observations are sequential, each remote has the fixed implementation-owned
five-second timeout, and one failed remote does not stop later observations.
There are no retries.

Local `application_status` is `local`. Runtime statuses are `available`,
`unavailable`, `observation-failed`, and `unknown`; `unknown` is used only when
no valid remote runtime observation was obtained. Remote application statuses
are `reachable`, `unreachable`, `request-failed`, and `invalid-response`.
Node failures are reported as data. Once validation succeeds and observation
begins, unavailable or failed node observations do not by themselves make the
command exit unsuccessfully. The command exits unsuccessfully when it cannot
construct the operation, including invalid arguments or declarations, local
inspection construction failure, or unexpected collection failure.

Status complements rather than replaces the static, network-free preflight or
the current-machine-only local health command. Use each command for its own
observation boundary.

This operation does not start or stop runtimes, repair services, restart
machines, mutate declarations, change routing or fallback, persist observations,
poll, or watch. Its output excludes transport URLs, private addresses, machine
display names, adapter or model names, credentials, prompts, responses, and raw
exceptions.

### 7. Optionally observe the calling machine's local runtime

```sh
uv run home-ai-cluster-health
```

This remains local health only; it does not inspect the remote node. It matters
because ordinary routing is local-first, so a usable local path normally wins.

### 8. Start the ordinary static multi-node process

On the calling machine:

```sh
uv run home-ai-cluster-static-cluster \
  --remote-node-id <remote-node-id> \
  --remote-base-url http://<receiving-lan-address>:8000
```

It binds the calling machine's native endpoint to:

```text
http://127.0.0.1:8000/v1/chat
```

The supplied URL is held only in process memory and is not persisted. The
process owns only its HTTP client and application lifecycle; it does not start,
stop, supervise, repair, or discover the remote machine or runtime.

### 9. Send one ordinary request

```sh
curl -s http://127.0.0.1:8000/v1/chat \
  -H 'content-type: application/json' \
  -d '{
    "messages": [{"role": "user", "content": "<operator-supplied-message>"}],
    "capability": "chat"
  }'
```

A usable local candidate has precedence. The declared remote candidate is used
only through the accepted narrow fallback when the local runtime fails before
request execution with the accepted connection-unavailable condition. There is
no direct node targeting, retry loop, balancing, scoring, scheduling, or
discovery. A declared remote node does not guarantee that the first request uses
the remote path.

### 10. Reproduce remote fallback deliberately

To reproduce the accepted remote fallback manually, leave or make unavailable
the externally owned local runtime path on the calling machine before sending a
request, while keeping the receiving runtime and application available. Send one
request through the calling loopback endpoint and confirm that cluster-owned
attribution identifies `<remote-node-id>`. Do not introduce a direct
remote-targeting option or destructive recovery action.

### 11. Stop in canonical order

1. stop the calling static multi-node process;
2. stop the receiving ordinary application;
3. remove any temporary firewall allowance;
4. leave or stop external runtimes manually according to operator policy.

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

- correct repository-owned static declarations before rerunning preflight;
- start or repair the external runtime before rerunning health;
- ensure the required model is locally available;
- stop a conflicting process when an accepted fixed port is occupied;
- verify the trusted-LAN address and temporary firewall scope;
- rerun the failed inspection step before repeating a request;
- stop Home AI Cluster processes with normal process interruption;
- clear optional request history explicitly when desired.

Do not infer automatic repair, retries, service restart, remote shutdown,
configuration mutation, or process supervision from this workflow.

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

This document remains the canonical shortest operator sequence.
