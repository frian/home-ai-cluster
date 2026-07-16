# Canonical Operator Workflow

Status: Canonical

Date: 2026-07-16

This document is the shortest supported operator path for the current Home AI
Cluster architecture.

It defines two separate modes:

1. ordinary local-only operation;
2. explicit two-machine proof operation.

It orders existing commands and process boundaries. It does not add lifecycle
ownership, automatic repair, discovery, supervision, remote control, or a new
configuration format.

## Read this boundary first

Home AI Cluster does not start, supervise, repair, or stop external AI runtimes.
Those runtimes remain operator-owned.

`home-ai-cluster-preflight` checks only ordinary local static node and adapter
registry coherence. It does not perform runtime or network checks.

The explicit two-machine path remains a proof-only path. It does not activate
ordinary distributed operation.

## Supported requirements

Use a supported Python version and `uv`.

From the repository root:

```sh
uv sync
```

The default local path currently requires an externally owned Ollama runtime and
the adapter's required local model.

## Mode 1: Ordinary local-only operation

This mode uses the ordinary local static registries, one externally owned local
runtime, the ordinary FastAPI application, and the native `/v1/chat` endpoint.

### 1. Prepare the runtime

Install and start the external local runtime using its own supported procedure.
Ensure the required model is locally available.

Home AI Cluster does not own this process.

### 2. Check static coherence

Run:

```sh
uv run home-ai-cluster-preflight
```

A coherent report means that every adapter name declared by an ordinary local
node resolves in the ordinary local adapter registry.

It does not mean that the runtime, model, or application is available.

If the report is `incoherent`, correct the repository-owned static declarations
before continuing.

### 3. Observe local runtime health

Run:

```sh
uv run home-ai-cluster-health
```

This command performs direct local adapter health observation. It answers a
different question from preflight.

If health is not usable, repair or start the external runtime, confirm the
required model, then rerun health.

### 4. Start the ordinary application

Run:

```sh
uv run uvicorn home_ai_cluster.main:app --reload
```

The ordinary native endpoint is:

```text
http://127.0.0.1:8000/v1/chat
```

### 5. Send one native request

From another terminal:

```sh
curl -s http://127.0.0.1:8000/v1/chat \
  -H 'content-type: application/json' \
  -d '{
    "messages": [{"role": "user", "content": "Hello"}],
    "capability": "chat"
  }'
```

A successful response should include cluster-owned node attribution.

### 6. Optional inspection surfaces

Use these only when their accepted purpose is needed:

```text
home-ai-cluster-explain-routing
home-ai-cluster-explain-request
home-ai-cluster-history
home-ai-cluster-clear-history
```

Request history remains opt-in. Clear it only when the operator explicitly wants
to remove retained optional history.

The separate OpenAI-compatible process is an optional access path, not part of
this canonical native workflow.

### 7. Stop

Stop the ordinary application with normal process interruption, usually
`Ctrl-C`.

Leave the external runtime running or stop it manually according to the
operator's runtime policy.

## Mode 2: Explicit two-machine proof operation

This mode reproduces the accepted trusted-LAN proof:

> One endpoint. Two machines. One routed request.

Roles:

- **receiving machine**: ordinary application plus externally owned local runtime;
- **calling machine**: explicit static proof process.

Both machines must use the same repository revision and remain on the same
trusted LAN.

### 1. Prepare both machines

On both machines:

```sh
uv sync
```

Confirm that both checkouts use the same repository revision.

On the receiving machine, install and start the external runtime and ensure the
required model is locally available.

### 2. Check the receiving machine

On the receiving machine, run:

```sh
uv run home-ai-cluster-preflight
uv run home-ai-cluster-health
```

Important limitation: this preflight validates only the receiving machine's
ordinary local static registries. It does not validate the proof-specific remote
node declaration, supplied URL, LAN route, receiving machine, runtime, model, or
remote execution.

### 3. Determine the receiving LAN address

Determine the receiving machine's current trusted-LAN address.

Use a placeholder such as:

```text
<receiving-lan-address>
```

Do not commit a real private address to repository documentation or proof
records.

### 4. Start the receiving application

On the receiving machine:

```sh
uv run uvicorn home_ai_cluster.main:app --host 0.0.0.0 --port 8000
```

If a host firewall is enabled, allow TCP port `8000` only from the trusted LAN
and only for the duration of the proof.

### 5. Verify receiving reachability

From the calling machine:

```sh
curl -s http://<receiving-lan-address>:8000/v1/chat \
  -H 'content-type: application/json' \
  -d '{
    "messages": [{"role": "user", "content": "Hello"}],
    "capability": "chat"
  }'
```

This checks the ordinary receiving endpoint and trusted-LAN path. It is not a
static preflight check.

### 6. Start the calling proof process

On the calling machine:

```sh
uv run home-ai-cluster-static-proof http://<receiving-lan-address>:8000
```

The proof process binds to its accepted loopback endpoint:

```text
http://127.0.0.1:8000/v1/chat
```

### 7. Send one routed request

From another terminal on the calling machine:

```sh
curl -s http://127.0.0.1:8000/v1/chat \
  -H 'content-type: application/json' \
  -d '{
    "messages": [{"role": "user", "content": "Hello"}],
    "capability": "chat"
  }'
```

Confirm the expected cluster-owned remote node attribution and visible failure
behavior.

### 8. Stop in canonical order

1. stop the calling proof process with normal process interruption;
2. stop the receiving ordinary application;
3. remove any temporary firewall allowance created for the proof;
4. leave or stop the external runtime manually according to operator policy.

## Failure-layer lookup

| Layer | Owning surface |
| --- | --- |
| Ordinary local static declaration coherence | `home-ai-cluster-preflight` |
| Ordinary local adapter health observation | `home-ai-cluster-health` |
| Process startup and fixed-port conflict | Invoked process and operating system |
| Receiving-machine reachability | Explicit trusted-LAN request |
| Routing and request execution | Existing request and explanation surfaces |
| Optional retained request history | History inspection and clearing commands |

Do not reinterpret one layer's failure as another layer's result.

## Process and port ownership

| Process | Purpose | Accepted exposure | Ownership |
| --- | --- | --- | --- |
| External AI runtime | Model execution | Runtime-specific | Operator-owned |
| Ordinary Home AI Cluster application | Native local or receiving endpoint | Loopback by default; trusted-LAN bind only for explicit proof | Home AI Cluster process, manually started |
| Static proof process | Calling-machine proof endpoint | Loopback only on accepted proof port | Home AI Cluster proof process, manually started |
| OpenAI-compatible process | Optional compatibility access | Loopback only on its accepted port | Separate optional Home AI Cluster process |

This table does not imply supervision or automatic lifecycle management.

## Recovery guidance

Use only supported manual recovery actions:

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

Do not retain in repository documentation or proof records:

- real private LAN addresses;
- prompts or generated responses;
- authorization values or runtime credentials;
- real filesystem paths;
- raw exceptions;
- machine names or hardware details;
- personal account details or secrets.

Use placeholders for operator-specific values.

## Detailed references

- `README.md`
- `docs/static-two-machine-proof.md`
- `RFC/RFC-0036-static-operator-preflight.md`
- `RFC/RFC-0037-canonical-operator-workflow.md`

These documents provide detail and retained history. This document remains the
canonical shortest operator sequence.