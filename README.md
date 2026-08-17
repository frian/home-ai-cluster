# Home AI Cluster

Local-first orchestration for personal AI runtimes.

Status: early prototype with formal roadmap phases complete through Phase 18;
later bounded integration proofs are retained separately.

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
explicit static multi-node operation, with historical proof records kept
separate from current installation guidance.

Operators can find retained topology and local runtime-composition TOML examples
in [examples/README.md](examples/README.md).

For current ordinary command syntax, options, and boundaries, use the
[command reference](docs/command-reference.md).

## Unified ordinary command

`home-ai-cluster` is the preferred discoverable namespace for ordinary
operations. It is additive: every existing standalone command remains
supported with its current behavior.

```text
home-ai-cluster local
home-ai-cluster static-cluster
home-ai-cluster compatibility
home-ai-cluster chat
home-ai-cluster code
home-ai-cluster summarize
home-ai-cluster classify
home-ai-cluster preflight
home-ai-cluster health
home-ai-cluster status
```

`local`, `static-cluster`, and `compatibility` remain foreground processes.
The root command dispatches one selected operation only: it does not start
multiple services and provides no start, stop, restart, daemon, or supervision
behavior.

After ordinary package installation, `hac status` is a short equivalent of
`home-ai-cluster status`. `home-ai-cluster` remains the canonical, fully
supported command.

## Installed and checkout command usage

### Installed operator usage

For ordinary operator use, install the package with:

```sh
uv tool install .
```

After installation, use the short `hac` command for ordinary operations:

```sh
hac preflight
hac health
hac status --declaration <path>
hac local
hac static-cluster --declaration <path>
hac compatibility
hac chat "Hello"
hac code --message "<OPERATOR_SUPPLIED_CODE_REQUEST>"
hac summarize --text "Long text to summarize"
hac classify --text "The invoice is due tomorrow." --label invoice --label personal
```

The long namespace remains canonical and fully supported:

```sh
home-ai-cluster status --declaration <path>
home-ai-cluster code --message "<OPERATOR_SUPPLIED_CODE_REQUEST>"
home-ai-cluster summarize --text "Long text to summarize"
home-ai-cluster classify --text "The invoice is due tomorrow." --label invoice --label personal
```

After changing checked-out source, rebuild and refresh the installed tool
snapshot without reusing cached build artifacts:

```sh
uv tool install --force --no-cache .
```

`--force` replaces the installed tool environment. `--no-cache` ensures the
refresh does not reuse cached build artifacts from an earlier checkout state.

### Repository-checkout and development usage

Contributors and operators running directly from a repository checkout can
prepare it with `uv sync` and run the standalone installed-script names through
`uv run`:

```sh
uv sync
uv run home-ai-cluster-preflight
uv run home-ai-cluster-health
uv run home-ai-cluster-status --declaration <path>
uv run home-ai-cluster-local
uv run home-ai-cluster-static-cluster --declaration <path>
uv run home-ai-cluster-openai-compatibility
uv run home-ai-cluster-chat "Hello"
```

Development-only commands remain repository-checkout usage:

```sh
uv run uvicorn home_ai_cluster.main:app --reload
```

Historical proofs and repository-specific procedures may likewise retain their
established `uv run` commands.

## Current shape

The normal FastAPI application:

* runs as one local process;
* exposes the cluster-native `POST /v1/chat`, `POST /v1/summarize`, and
  `POST /v1/classify` endpoints;
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

The accepted ordinary capability vocabulary is `chat`, `summarize`, `classify`,
and `code`. `code` is explicit bounded textual code assistance: it shares the
ordered-message `ClusterRequest` representation and free-form textual result,
uses `POST /v1/chat` with `capability=code`, and introduces no `/v1/code`.
Both ordinary local Ollama and llama-server compositions advertise and execute
it through their existing Chat-like execution path. OpenAI-compatible access
remains Chat-only, and the fixed browser page remains Chat, Summarize, and
Classify only. The root command has the ten subcommands shown above, including
the ordinary native `summarize`, `classify`, and `code` clients.

The accepted explicit static capability names are `chat`, `summarize`,
`classify`, and `code`. Omitted local or remote capability declarations retain
exactly the compatibility default `chat` plus `summarize`; `classify` and
`code` eligibility must be declared explicitly. Capability membership controls
hard eligibility, not priority, model preference, or runtime preference;
declared remote order remains the only remote priority.

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
hac status --declaration <path>
```

For the compact normalized structured result used by automation, run:

```sh
hac status --declaration <path> --json
```

Or inspect an explicit llama-server local composition with:

```sh
hac status \
  --declaration <path> \
  --runtime llama-server \
  --llama-server-base-url http://127.0.0.1:<LLAMA_SERVER_PORT> \
  --llama-server-model <MODEL_IDENTIFIER>
```

The command validates the declaration before runtime composition construction,
observes the fixed local node and declared remotes sequentially in declaration
order, and emits a human-readable status report by default. Explicit `--json`
emits the compact normalized structured result. Declaration status, local-first
ordering, remote order, application statuses, and runtime statuses are the same
in both representations. Runtime identity remains outside that result. The
command is read-only and informational: it does not change routing, fallback,
topology, or runtime lifecycle. `--json` can be combined with the same valid
runtime-composition arguments shown above. See the
[canonical operator workflow](docs/operator-workflow.md) for the supported path.

## Current inspection commands

Preflight and health are also human-readable by default:

```sh
hac preflight
hac health
```

Automation uses their explicit compact structured forms:

```sh
hac preflight --json
hac health --json
```

See the [canonical operator workflow](docs/operator-workflow.md) and the
[Phase 17 closeout](docs/phase-17-closeout.md) for the bounded inspection
contract.

All four historical installed proof launchers were retired by accepted RFC-0075;
their records and Git history remain the archive. Ordinary llama-server
operation uses `home-ai-cluster-local`.

## One-shot ordinary request access

With an ordinary local-only or explicit static-cluster process already running,
an operator can send one ordinary request without manually constructing HTTP
details:

```sh
hac chat "Hello"
```

The explicit message option remains fully supported:

```sh
hac chat --message "Hello"
```

To summarize one bounded supplied text through the same already-running
ordinary process, use:

```sh
hac summarize --text "Long text to summarize"
```

For one explicit bounded textual code request, use the same native
ordered-message endpoint through the root command:

```sh
hac code --message "<OPERATOR_SUPPLIED_CODE_REQUEST>"
```

The long equivalent is `home-ai-cluster code --message
"<OPERATOR_SUPPLIED_CODE_REQUEST>"`. It accepts exactly one non-blank explicit
message and limits that message to 65,536 UTF-8 bytes; it never reads a file or
stdin and never truncates input. Generated code is response text only: it
grants no filesystem, repository, shell, Git, testing, tool, agent, or
execution authority.

The same one bounded UTF-8 source can come from standard input:

```sh
cat README.md | hac summarize
hac summarize < README.md
git diff | hac summarize
```

One bounded strict-UTF-8 regular file can also be selected explicitly:

```sh
hac summarize --file README.md
hac summarize --file docs/operator-workflow.md --verbose
```

When `--text` is present, it takes precedence and stdin is ignored. `--text`
and `--file` are mutually exclusive. When `--file` is present, stdin
is ignored. The 65,536-byte limit applies to every source; oversized input is
rejected rather than truncated.

The canonical equivalent is:

```sh
home-ai-cluster summarize --text "Long text to summarize"
```

This client accepts one source through `--text`, `--file`, or stdin when no
explicit source is supplied. `--text` and `--file` are mutually exclusive, and
an explicit source ignores stdin. It uses the existing native
`POST /v1/summarize` contract and the same topology-blind local-only or
explicit static-cluster process boundary as chat.

To choose one exact label from an operator-supplied ordered set, use the bounded
classification client:

```sh
hac classify --text "The invoice is due tomorrow." --label invoice --label personal
```

It accepts one bounded source through `--text`, `--file`, or stdin, and repeated
ordered `--label` options. A successful minimal result contains `selected_label`
and `node_id`; the selected label must exactly equal one supplied label. See the
[command reference](docs/command-reference.md) for complete syntax and bounds.

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

## Phase 17 records

- [Human-readable operator output investigation](docs/human-readable-operator-output-investigation.md)
- [RFC-0048 human-readable inspection output](RFC/RFC-0048-human-readable-inspection-output.md)
- [Human-readable inspection output proof runbook](docs/phase-17-human-readable-inspection-output-proof.md)
- [Human-readable inspection output retained proof result](docs/phase-17-human-readable-inspection-output-proof-result.md)
- [Phase 17 closeout](docs/phase-17-closeout.md)

## Phase 18 records

- [Second-capability investigation](docs/second-capability-investigation.md)
- [RFC-0051 bounded text summarization](RFC/RFC-0051-bounded-text-summarization.md)
- [Phase 18 retained two-machine summarize proof](docs/phase-18-two-machine-summarize-proof.md)
- [Phase 18 closeout](docs/phase-18-closeout.md)

## Post-roadmap ordinary remote request proof

This standalone post-roadmap integration proof does not reopen or extend Phase
16. It did not create, reopen, or extend a roadmap phase and remains separate
from the later completed Phase 17 presentation work. It composes existing
accepted behavior without implementation changes: the unchanged
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

## Run the cluster-native endpoints

For repository-checkout development, start the normal application with the
existing default Ollama composition:

```sh
uv run uvicorn home_ai_cluster.main:app --reload
```

Start the explicit ordinary local runtime path with its compatible Ollama
default:

```sh
hac local
```

Or start one ordinary llama-server-backed node whose runtime remains on local
loopback:

```sh
hac local \
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
hac compatibility
```

To expose that unchanged compatibility route over an explicit static cluster,
provide an accepted RFC-0039/RFC-0040 declaration:

```sh
hac compatibility --declaration <path>
```

This is the only compatibility static-cluster mode. It reuses the ordinary
static-cluster declaration validation and local-first routing while retaining
the same loopback-only listener and RFC-0031 compatibility contract.

For the separately executed static-cluster proof only, an operator may
explicitly enable the accepted bounded observation mode:

```sh
uv run home-ai-cluster-openai-compatibility \
  --declaration <path> \
  --proof-observation
```

It writes one final, content-free structural line to standard error for each
strictly accepted request. It is disabled by default, does not change HTTP or
routing behavior, and does not retain request observations.

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

The earlier retained Phase 6 local compatibility proof established that Aider
v0.86.0 can use the loopback compatibility endpoint without changing Home AI
Cluster. The tested setup used only temporary client-side configuration:

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

That local proof observed exactly one `POST /v1/chat/completions` request
containing only `messages` and `model`, followed by HTTP 200 and successful
response parsing by Aider.

A later bounded two-machine static-cluster proof used Aider 0.86.2 for one
non-streaming request to the caller loopback compatibility endpoint. It
completed through one declared remote receiver without exposing routing topology
to Aider. It does not imply support for all Aider versions or modes.

See [the Phase 6 local Aider proof](docs/phase-6-aider-access-proof.md),
[the retained Aider static-cluster proof](docs/aider-static-cluster-proof.md),
and [its runbook](docs/aider-static-cluster-proof-runbook.md) for the bounded
scope and privacy constraints.

## Two-machine proofs

The historical founding two-machine proof is retained through [the RFC-0022
LAN-only runbook](docs/static-two-machine-proof.md) and [its retained
result](docs/first-two-machine-proof-result.md). Its retired launcher requires
the historical repository revision for exact reproduction.

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
