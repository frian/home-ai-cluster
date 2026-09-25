# Home AI Cluster

Local-first orchestration for personal AI infrastructure.

**User documentation:** [frian.github.io/home-ai-cluster](https://frian.github.io/home-ai-cluster/)

Home AI Cluster (HAC) is an orchestration layer, not an LLM or inference
engine. It lets you request capabilities from one local AI system instead of
choosing a machine, runtime, or model brand for each ordinary request.

> Many machines. One AI.

## Architecture at a glance

![Home AI Cluster architecture at a glance](docs/assets/architecture-at-a-glance.svg)

Requests name capabilities, and HAC routes them among explicitly eligible
nodes with local-first precedence. Runtimes, models, and processes remain
operator-owned. HAC does not discover machines or dynamically schedule work.

## What you can do

HAC provides these ordinary user-facing capabilities:

- Chat
- Code
- Image Generation
- Summarize
- Classify

Use them through `hac` or the fixed loopback browser interface. Local-only operation is
the default and simplest path; an explicit static cluster is available when you
want declared remote nodes. Image Generation requires an explicitly configured
Image Generation binding or companion. Code is textual by default, with
separate bounded file and workspace caller edges.

An operator may explicitly enable the capability-only trusted-LAN browser for
trusted peers and network paths. It uses plain HTTP; see the
[Command Reference](docs/command-reference.md) for its exact boundary.

Optional bounded integrations include External Information, Aider, and a
narrow OpenAI-compatible Chat edge. Their exact behavior and authority
boundaries are documented in the [Command Reference](docs/command-reference.md).

## Quick start

For prerequisites, Windows instructions, runtime setup, and the complete
first-use path, see [Getting Started](docs/getting-started.md).

Install the published package and start HAC:

```sh
uv tool install home-ai-cluster
hac local
```

From another terminal, send a request:

```sh
hac chat "Hello"
```

Then open:

```text
http://127.0.0.1:25042/
```

The fixed local browser offers an ordinary way to use HAC.

![Home AI Cluster browser interface](docs/assets/browser-interface.png)

## Deliberate boundaries

HAC is local-first, privacy-first, capability-centered, and engine-independent.
Its topology is explicit and static, while runtimes and models remain
operator-owned. It has no automatic discovery or scheduler, runtime or model
lifecycle management, general dashboard or control plane, broad
OpenAI-compatible API, or Docker, Kubernetes, or database architecture.

Read the [Vision](VISION.md), [Foundations](FOUNDATIONS.md),
[Principles](PRINCIPLES.md), and [Non-goals](NON_GOALS.md) for the complete
rationale.

## Go deeper

- [Getting Started](docs/getting-started.md) — complete installation and first use.
- [Command Reference](docs/command-reference.md) — exact command syntax and behavior.
- [Canonical Operator Workflow](docs/operator-workflow.md) — local and static-cluster operation.
- [Documentation index](docs/README.md) — retained investigations, proofs, and historical evidence.
- [RFC index](RFC/README.md) — architectural decisions.

## Contributing and license

Contributions follow [CONTRIBUTING.md](CONTRIBUTING.md). Home AI Cluster is
licensed under [AGPL-3.0-or-later](LICENSE); see [NOTICE](NOTICE) for associated
notices.
