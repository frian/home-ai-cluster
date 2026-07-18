# Home AI Cluster

Local-first orchestration for personal AI runtimes.

Status: early prototype with completed roadmap phases through Phase 16.

Home AI Cluster explores how multiple personal machines and AI runtimes can be
presented as one capability-centered local system:

> Many machines. One AI.

The current implementation remains intentionally small. The ordinary
application is local and static by default. An operator can also start an
explicit static cluster from a TOML declaration containing one or more ordered
remote nodes. Routing remains local-first and capability-centered, with a narrow,
bounded fallback when an eligible candidate is unavailable before request
transmission.

## Project context

Start with:

* `VISION.md`
* `FOUNDATIONS.md`
* `PRINCIPLES.md`
* `NON_GOALS.md`
* `ROADMAP.md`
* `RFC/`

Use the [documentation index](docs/README.md) to find current operator guidance
and chronological investigation, runbook, proof, and closeout records.

The [canonical operator workflow](docs/operator-workflow.md) is the shortest
supported operator sequence. It covers ordinary local-only operation, ordinary
explicit static multi-node operation, and historical proof-only operation.

## Current shape

The normal FastAPI application:

* runs as one local process;
* exposes the cluster-native `POST /v1/chat` endpoint;
* uses a static local node registry by default;
* routes by capability, not by machine, adapter, or runtime-model name;
* keeps runtime-specific behavior behind adapters;
* returns cluster-owned node attribution;
* does not enable distributed wiring automatically.

The repository currently contains Ollama and llama-server runtime adapters. The
ordinary `home-ai-cluster-local` entry point can start exactly one explicit local
runtime composition through the closed choices `ollama` and `llama-server`.
Runtime choice is consumed only at process startup and does not enter requests,
routing, remote declarations, attribution, or normalized status.

The explicit `home-ai-cluster-static-cluster` entry point can start an ordinary
small static cluster from an operator-owned declaration. Its one local
composition can be explicitly selected as `ollama` or `llama-server`; the
default remains Ollama. That declaration may contain multiple remote nodes whose
order is the only remote priority. The calling endpoint remains loopback-only,
topology remains explicit and static, and the project does not introduce
discovery, scheduling, supervision, dynamic topology mutation, or a general
retry policy.

An operator can inspect one explicitly declared static cluster with the default
Ollama local composition:

```sh
uv run home-ai-cluster-status --declaration <path>
```

Or inspect an explicit llama-server local composition with:

```sh
uv run home-ai-cluster-status \
  --declaration <path> \
  --runtime llama-server \
  --llama-server-base-url http://127.0.0.1:<LLAMA_SERVER_PORT> \
  --llama-server-model <MODEL_IDENTIFIER>
```

The command validates the declaration before runtime composition construction,
observes the fixed local node and declared remotes sequentially in declaration
order, and emits one compact normalized JSON result. Runtime identity remains
outside that result. The command is read-only and informational: it does not
change routing, fallback, topology, or runtime lifecycle. See the
[canonical operator workflow](docs/operator-workflow.md) for the supported path.

Separate proof commands remain available for historical architecture
reproduction and focused verification. They do not turn the ordinary application
into a general distributed deployment. The Phase 12 heterogeneous receiver
remains proof-only historical evidence; ordinary llama-server operation uses
`home-ai-cluster-local`.

## One-shot ordinary request access

With an ordinary local-only or explicit static-cluster process already running,
an operator can send one ordinary request without manually constructing HTTP
details:

```sh
uv run home-ai-cluster-chat --message "Hello"
```

The command is a topology-blind client of the already running ordinary process;
it does not start, configure, inspect, or manage that process. The same command
works for local-only and explicit static-cluster operation and returns one
normalized result with cluster-owned `node_id` attribution. See the
[Phase 16 closeout](docs/phase-16-closeout.md) and the
[canonical operator workflow](docs/operator-workflow.md) for the bounded
operator contract and process preparation.

## Phase 16 records

- [Ordinary operator request access investigation](docs/phase-16-ordinary-operator-request-access-investigation.md)
- [RFC-0045 one-shot ordinary request command](RFC/RFC-0045-one-shot-ordinary-request-command.md)
- [Ordinary request access proof runbook](docs/phase-16-ordinary-request-access-proof-runbook.md)
- [Ordinary request access retained proof](docs/phase-16-ordinary-request-access-proof.md)
- [Phase 16 closeout](docs/phase-16-closeout.md)

## Post-roadmap ordinary remote request proof

This standalone post-roadmap integration proof does not reopen or extend Phase
16, and it does not establish a formal Phase 17. It composes existing accepted
behavior without implementation changes: the unchanged
`home-ai-cluster-chat` client used only its fixed caller loopback endpoint and
successfully reached a real ordinary remote receiver through the caller-owned
static-cluster path. Exactly one client invocation returned a complete normalized
result attributed to the declared remote node ID. The client remained
topology-blind throughout.

See [the investigation](docs/phase-17-end-to-end-ordinary-remote-request-investigation.md),
[the runbook](docs/end-to-end-ordinary-remote-request-proof-runbook.md), and
[the retained proof](docs/end-to-end-ordinary-remote-request-proof.md).

## Requirements

* Python 3.13 or 3.14
* `uv`
* Ollama installed and running for the default local path
* the default Ollama model used by the adapter, currently `llama3.2`

Install dependencies:

```sh
uv sync
```

## Run the cluster-native endpoint

Start the normal application with the existing default Ollama composition:

```sh
uv run uvicorn home_ai_cluster.main:app --reload
```

Start the explicit ordinary local runtime path with its compatible Ollama
default:

```sh
uv run home-ai-cluster-local
```

Or start one ordinary llama-server-backed node whose runtime remains on local
loopback:

```sh
uv run home-ai-cluster-local \
  --runtime llama-server \
  --llama-server-base-url http://127.0.0.1:<LLAMA_SERVER_PORT> \
  --llama-server-model <MODEL_IDENTIFIER>
```

The llama-server base URL must use loopback HTTP. Runtime installation,
startup, shutdown, supervision, and model lifecycle remain operator-owned.

Send a chat request:

```sh
curl -s http://127.0.0.1:8000/v1/chat \
  -H 'content-type: application/json' \
  -d '{
    "messages": [{"role": "user", "content": "Hello"}],
    "capability": "chat"
  }'
```

Example response shape:

```json
{
  "content": "...",
  "adapter": "ollama",
  "model": "llama3.2",
  "node_id": "local"
}
```

If the selected runtime adapter is unavailable, `/v1/chat` returns HTTP 503
without exposing runtime URLs or raw adapter errors:

```json
{
  "detail": "Runtime adapter unavailable"
}
```

## Run the minimal OpenAI-compatible endpoint

RFC-0031 adds a dedicated compatibility process. It is separate from the normal
application and binds only to loopback:

```sh
uv run home-ai-cluster-openai-compatibility
```

Its base URL is:

```text
http://127.0.0.1:8001/v1
```

It accepts the fixed endpoint identifier:

```text
home-ai-cluster
```

Example request:

```sh
curl -s http://127.0.0.1:8001/v1/chat/completions \
  -H 'content-type: application/json' \
  -d '{
    "model": "home-ai-cluster",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

This is a deliberately small compatibility surface. It supports non-streaming
plain-text chat only. It does not provide general OpenAI API compatibility,
model discovery, request-level runtime-model selection, tools, multimodal
content, generation controls, LAN exposure, or real authentication.

## Use Aider

A real Aider v0.86.0 request has been proven against the compatibility endpoint
without changing Home AI Cluster. The tested setup used only temporary
client-side configuration:

```yaml
- name: openai/home-ai-cluster
  edit_format: whole
  use_temperature: false
```

With that model-settings file, Aider was configured with:

* model `openai/home-ai-cluster`;
* base URL `http://127.0.0.1:8001/v1`;
* a non-secret placeholder API key;
* streaming disabled.

The proof observed exactly one `POST /v1/chat/completions` request containing
only `messages` and `model`, followed by HTTP 200 and successful response
parsing by Aider.

See `docs/phase-6-aider-access-proof.md` for the exact tested scope and privacy
constraints. The proof does not imply support for every Aider mode.

## Two-machine proofs

The historical founding two-machine proof remains available through [the
RFC-0022 LAN-only runbook](docs/static-two-machine-proof.md) and [its retained
result](docs/first-two-machine-proof-result.md).

The newer [end-to-end ordinary remote request proof](docs/end-to-end-ordinary-remote-request-proof.md)
records one unchanged ordinary client invocation reaching a real remote ordinary
receiver through existing static-cluster fallback; [its runbook](docs/end-to-end-ordinary-remote-request-proof-runbook.md)
records the bounded operator procedure.

These proof paths are explicit and opt-in. They are not the default application
configuration.

## Project boundaries

Home AI Cluster remains:

* local-first;
* privacy-first;
* engine-independent;
* capability-centered;
* architecture-before-implementation.

The project does not currently provide a dashboard, automatic discovery,
Kubernetes deployment, a model catalogue, broad OpenAI API emulation, or a
general production security model.
