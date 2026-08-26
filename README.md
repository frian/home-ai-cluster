# Home AI Cluster

Local-first orchestration for personal AI runtimes.

Project maturity: early prototype.

Home AI Cluster is an orchestration layer, not an LLM or inference engine. It
presents multiple personal machines and replaceable AI runtimes as one
capability-centered local system:

> Many machines. One AI.

The user addresses the cluster rather than selecting a machine or runtime
brand for an ordinary request. Ordinary operation remains intentionally small,
local-first, and explicit.

## What works today

| Area | Current support |
| ---- | --------------- |
| Local runtime | Run one operator-managed local Ollama or llama-server composition. |
| Static cluster | Run one explicit local-plus-remote cluster from operator-declared, ordered remote nodes. Routing is capability-centered and local-first; declared remote order is the only remote priority. |
| Native capabilities | Chat, Summarize, Classify, and Code. A narrow fallback applies only when an eligible candidate is unavailable before request transmission; results carry cluster-owned node attribution. |
| Ordinary interfaces | Use the `hac` command, cluster-native HTTP endpoints, or the fixed loopback browser for Chat, Summarize, Classify, and Code. The browser is not a dashboard, LAN interface, persistent server-side conversation store, filesystem authority, or execution environment. |
| Optional bounded integrations | Use the narrow loopback OpenAI-compatible Chat process, bounded Aider and code caller edges, or explicit separately installed external-information acquisition. |
| Historical evidence | Retained investigations, runbooks, proofs, and closeouts are indexed separately; they are not required for ordinary operation. |

Topology declarations and runtime lifecycle remain operator-owned.

## Deliberate boundaries

Home AI Cluster remains local-first, privacy-first, engine-independent,
capability-centered, and architecture-before-implementation. Topology is
explicit and static; operators own runtimes, models, remote processes, and
declarations.

The project does not provide automatic discovery, scheduling or ranking,
dynamic topology mutation, process supervision, a dashboard architecture,
Kubernetes deployment, a model catalogue, broad OpenAI API emulation, bundled
Web acquisition, a generic plugin system, or a general production security
model. See the [vision](https://github.com/frian/home-ai-cluster/blob/main/VISION.md),
[foundations](https://github.com/frian/home-ai-cluster/blob/main/FOUNDATIONS.md),
[principles](https://github.com/frian/home-ai-cluster/blob/main/PRINCIPLES.md),
and [non-goals](https://github.com/frian/home-ai-cluster/blob/main/NON_GOALS.md)
for the project rationale.

## Install and first use

For a complete first-use walkthrough, including `uv`, Python, Ollama, the default
model, browser use, and first commands, see the
[Getting Started guide](docs/getting-started.md).

### Installed package

The supported installed-package path uses the current published package release:

```sh
uv tool install home-ai-cluster
```

A repository checkout may contain unreleased development work. See the
[PyPI project](https://pypi.org/project/home-ai-cluster/) for published package
information.

The default path requires Python 3.13 or 3.14, `uv`, and an
operator-managed local Ollama runtime with the default `llama3.2` model
available. Home AI Cluster does not install, download, start, stop, or manage
the runtime or model.

Start the ordinary local process in the foreground:

```sh
hac local
```

From another terminal on the same machine, send one request:

```sh
hac chat "Hello"
```

The same fixed loopback process serves the browser at
`http://127.0.0.1:8000/`.

### Repository checkout

For development from a checkout, prepare the locked environment:

```sh
uv sync --locked
uv run home-ai-cluster-local
```

Then, from another terminal, send one request:

```sh
uv run home-ai-cluster-chat "Hello"
```

See [Contributing](https://github.com/frian/home-ai-cluster/blob/main/CONTRIBUTING.md)
for development and validation guidance.

## Optional bounded integrations

The separate `hac compatibility` process offers deliberately incomplete,
loopback-only OpenAI-compatible Chat access. `hac aider` is a bounded caller
edge and does not imply support for every Aider version or mode. `hac code`
returns textual code assistance, while `hac code-file` performs one bounded
whole-file replacement; generated code is never automatically executed and
these commands grant no general repository, shell, Git, testing, agent, or
execution authority.

`hac external-information` explicitly uses one separately installed compatible
acquisition plugin for one source-grounded Chat request. No provider is bundled,
and the ordinary HAC server does not acquire external information by itself.

Use the [command reference](https://github.com/frian/home-ai-cluster/blob/main/docs/command-reference.md)
for exact syntax and boundaries, and the [documentation index](https://github.com/frian/home-ai-cluster/blob/main/docs/README.md)
for retained integration evidence and proofs.

## Documentation

For a first installation and local run, use the
[Getting Started guide](https://github.com/frian/home-ai-cluster/blob/main/docs/getting-started.md).

For operating Home AI Cluster, use the [canonical operator workflow](https://github.com/frian/home-ai-cluster/blob/main/docs/operator-workflow.md),
[command reference](https://github.com/frian/home-ai-cluster/blob/main/docs/command-reference.md),
and [configuration examples](https://github.com/frian/home-ai-cluster/blob/main/examples/README.md).

For architecture and project history, use the [documentation and historical evidence index](https://github.com/frian/home-ai-cluster/blob/main/docs/README.md),
[RFC index](https://github.com/frian/home-ai-cluster/tree/main/RFC), and
[completed roadmap](https://github.com/frian/home-ai-cluster/blob/main/ROADMAP.md).

For project direction and participation, see the [vision](https://github.com/frian/home-ai-cluster/blob/main/VISION.md),
[foundations](https://github.com/frian/home-ai-cluster/blob/main/FOUNDATIONS.md),
[principles](https://github.com/frian/home-ai-cluster/blob/main/PRINCIPLES.md),
[non-goals](https://github.com/frian/home-ai-cluster/blob/main/NON_GOALS.md),
and [contribution guide](https://github.com/frian/home-ai-cluster/blob/main/CONTRIBUTING.md).

## Founding milestone, contributing, and license

> One endpoint. Two machines. One routed request.

This founding milestone established the core abstraction: multiple personal
machines can participate in one capability-centered local system without
becoming an infrastructure platform. Retained evidence is available through the
[documentation index](https://github.com/frian/home-ai-cluster/blob/main/docs/README.md).

Contributions follow the [contribution guide](https://github.com/frian/home-ai-cluster/blob/main/CONTRIBUTING.md).
Home AI Cluster is licensed under [AGPL-3.0-or-later](https://github.com/frian/home-ai-cluster/blob/main/LICENSE);
see the [notice](https://github.com/frian/home-ai-cluster/blob/main/NOTICE) for
associated notices.
