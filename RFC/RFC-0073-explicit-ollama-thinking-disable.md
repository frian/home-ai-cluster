# RFC-0073: Explicit Ollama Thinking Disable

Status: Accepted

Date: 2026-08-17

Author: frian

## Summary

Home AI Cluster should permit one optional Ollama-specific process-local startup flag, `--ollama-disable-thinking`. With `--runtime ollama`, it requests native Ollama `"think": false` for every inference through that process's adapter. Omission preserves today's request shape: HAC omits `think` and leaves Ollama's selected-model default intact. This adds no generic reasoning model.

## Problem

The current adapter leaves thinking unspecified. Privacy-safe real-local evidence recorded one bounded Aider workload exceeding finite 300-second and 600-second caller waits, while a direct diagnostic using the same captured Aider-shaped messages with native thinking disabled completed in approximately 91 seconds. This establishes an observed difference, not that reasoning alone caused every slow request or should always be disabled.

## Goals

- Add one explicit Ollama-only process-local disable choice.
- Preserve default native omission when the flag is absent.
- Keep requests, capabilities, routing, results, privacy, and Aider unchanged.

## Non-goals

This RFC does not authorize thinking levels, budgets, explicit enable behavior, generic reasoning modes, per-request/per-capability/per-model policy, model discovery, prompt switches, hidden heuristics, generic runtime options, a ClusterRequest field, capability/routing criterion, remote/TOML field, browser/compatibility/Aider option, environment/configuration file, llama-server setting, trace/result metadata, persistence, cancellation, lifecycle management, retry, or model download.

## Proposal

### Ordinary local Ollama composition

The shared ordinary local-runtime composition accepts the optional flag only with `--runtime ollama`:

```text
hac local --runtime ollama --ollama-disable-thinking
home-ai-cluster local --runtime ollama --ollama-disable-thinking
```

It also applies to ordinary static-cluster startup where shared composition constructs the caller-local Ollama adapter. It is not a remote declaration; independently started receiving processes own their local configuration. Use with `--runtime llama-server` fails through existing local argument validation before startup, without runtime/model discovery.

### Omission and explicit-disable semantics

When absent, `OllamaAdapter` continues to omit native `think`; Ollama and the selected model retain their current default behavior. HAC must not silently force thinking on or off.

When present, the composed adapter sends exactly `"think": false` in every native Ollama chat inference request. It applies uniformly to chat, summarize, classify, and code on that adapter, never by capability, Aider use, route, node, or model metadata. It requests Ollama behavior; HAC does not guarantee all models support disable semantics.

Official [Ollama Thinking documentation](https://docs.ollama.com/capabilities/thinking) states that thinking is enabled by default for supported models and describes model-dependent boolean/level restrictions and separate thinking/final fields.

### Unchanged boundaries

`RuntimeResult` and `ClusterResult` remain final textual content only. No trace, token count, mode attribution, history, status, health, routing explanation, browser output, log, or persistence is added.

RFC-0068/RFC-0072 remain unchanged: `hac aider` gains no flag or selection and uses the already-running runtime. RFC-0060 remains unchanged: the option affects request construction before inference and is not timeout, cancellation, supervision, lifecycle control, retry, or background-work control.

llama-server receives no equivalent. Its controls are not equivalent to Ollama's model-dependent `think` contract, so this RFC creates no shared enum, budget, format, or adapter method.

## Rationale

An explicit process-local Ollama-only flag is smaller and more honest than a hidden adapter policy. It is analogous to RFC-0071 only in ownership: one operator starts one process, composition configures one adapter, and requests/routing remain independent. It preserves current defaults while making the exceptional choice visible.

## Alternatives considered

No HAC change, hard-coded `think=false`, generic process-local abstraction, request-level control, capability-specific policy, Aider-specific control, Ollama levels, generic pass-through, configuration files, and cancellation work are rejected. They either leave the demonstrated explicit choice unavailable, silently change behavior, or broaden request/routing, caller-edge, generic configuration, or lifecycle authority. The explicit Ollama process-local disable flag is selected as the smallest justified option.

## Trade-offs

The flag adds one runtime-specific startup input. It intentionally offers no levels or automatic support detection, so a selected model may restrict the request. That visible runtime behavior is smaller than discovery or a policy system.

## Relationship to previous RFCs

RFC-0003 and RFC-0030 runtime independence remain intact. RFC-0042/RFC-0043 composition ownership extends only with this Ollama-specific startup choice. RFC-0060 timeout/cancellation, RFC-0067 capability semantics, RFC-0068/RFC-0072 Aider ownership, and RFC-0071 model selection remain unchanged. RFC-0073 does not supersede RFC-0071; it is analogous only in process-local ownership.

## Impact and proof expectations

A later implementation must prove omission has no `think` field; explicit disable adds exactly `think: false`; ordinary local and caller-local static-cluster composition reach Ollama; llama-server rejects the flag before startup; and schemas, eligibility, routing, Aider translation, browser, compatibility, remote declarations, and TOML remain unchanged. It must introduce no trace exposure/persistence, timeout/cancellation/lifecycle/retry, discovery, or download. A later privacy-safe proof may use an already-installed model but must not retain private content, execute code, or claim universal performance.

## Open questions

None within this contract. A composition configuration file is separate.

## Decision

Accepted. Home AI Cluster accepts one optional Ollama-specific process-local
startup flag, `--ollama-disable-thinking`. When omitted, HAC preserves the
existing Ollama request shape and sends no `think` field. When explicitly
supplied with `--runtime ollama`, the composed Ollama adapter sends native
`think: false` for every inference handled by that adapter.

The choice remains process-local and adapter-owned. It does not become a
`ClusterRequest` field, capability property, routing criterion, remote
declaration, Aider/browser/compatibility option, generic runtime abstraction,
reasoning-level/budget control, timeout/cancellation mechanism, lifecycle
authority, or configuration-file contract. llama-server behavior remains
unchanged.
