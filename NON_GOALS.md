# Non-goals

Status: Current

This document records what Home AI Cluster deliberately does not try to be.

Non-goals protect the project from unnecessary complexity, unclear scope, and premature ambition.

A project becomes stronger when it knows what to refuse.

---

## Not an LLM

Home AI Cluster is not a language model.

It does not train models.

It does not define model architecture.

It does not compete with model providers or open model projects.

It orchestrates existing AI runtimes and capabilities.

---

## Not an inference engine

Home AI Cluster is not an inference engine.

It should not replace Ollama, llama.cpp, vLLM, MLX, or future runtimes.

Those tools execute models.

Home AI Cluster coordinates where and how AI workloads should run across personal machines.

The goal is integration, not replacement.

---

## Not a model format

Home AI Cluster does not define a model file format.

It should not care whether a model is GGUF, Safetensors, MLX, or something else unless a runtime adapter needs to know.

Model formats are runtime concerns.

They are not core architecture.

---

## Not a cloud platform

Home AI Cluster is not a cloud platform.

It should not require an account.

It should not require a hosted control plane.

It should not require external services for normal operation.

Optional cloud support may exist later, but it must never become the default assumption.

The project is local-first.

---

## Not Kubernetes for AI

Home AI Cluster should not become a general-purpose infrastructure orchestrator.

It should not require Kubernetes.

It should not copy enterprise complexity into a personal AI project.

It should not make local AI feel like managing a data center.

The first user is a technical individual, not an infrastructure team.

---

## Not enterprise-first

Home AI Cluster may eventually be useful to teams.

But it should not start by solving enterprise problems.

The project should not optimize first for:

* multi-tenant organizations;
* compliance departments;
* centralized administration;
* large-scale fleet management;
* enterprise billing;
* cloud-native deployment.

Personal usefulness comes first.

---

## Not magic

Home AI Cluster should automate decisions, but it should not hide reality.

The cluster may choose among allowed options.

It may recommend.

It may explain.

It may use the accepted bounded pre-transmission fallback.

But it must not silently expand its own authority.

Automatic behavior must remain understandable and inspectable.

Trust is more important than convenience.

---

## Not maximum performance at all costs

Performance matters.

But Home AI Cluster should not sacrifice clarity, privacy, or simplicity only to chase benchmarks.

The project should prefer boring, understandable solutions.

A slightly slower system that users trust is better than a clever system nobody can understand.

---

## Not distributed LLM execution first

Home AI Cluster does not begin by splitting one model across multiple machines.

Distributed tensor execution, expert placement, KV cache distribution, and low-level model parallelism are interesting ideas.

They are not the first goal.

The founding proof was achieved with the simpler shape:

> One endpoint. Two machines. One routed request.

That was enough to validate the core abstraction.

---

## Not a dashboard-first project

A dashboard may become useful.

But Home AI Cluster should not begin as a user interface.

The core idea must work without a dashboard.

The architecture, agent model, routing, and capability abstraction matter first.

A dashboard should reveal the system, not define it.

---

## Not a model manager first

Home AI Cluster may eventually help users understand which models are available where.

It may eventually help with downloads or placement.

But it should not begin as a model manager.

The first problem is orchestration.

Model management can come later.

---

## Not telemetry-first

Home AI Cluster should not collect usage data by default.

Prompts should not be logged by default.

Responses should not be logged by default.

Request contents should not leave the local cluster unless explicitly allowed.

The safest default is:

> Do not collect what is not needed.

---

## Scope rule

If a feature does not help multiple personal machines behave as one local AI system, it does not belong in the core.

It may belong later.

It may belong in an adapter.

It may belong behind a separately investigated and accepted bounded plugin
boundary.

It may belong in an idea file.

But it does not belong in the core.
