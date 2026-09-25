# RFC-0126: Explicit stable-diffusion.cpp Local Capability-Binding Configuration

Status: Accepted

Date: 2026-09-16

Author: frian

## Summary

Home AI Cluster should amend RFC-0110's explicitly selected multi-binding
`--runtime-config PATH` document with one additional closed binding runtime:
`stable-diffusion-cpp`.

The binding constructs the RFC-0121 `StableDiffusionCppAdapter` from exactly
three explicit operator-owned facts: non-empty `capabilities`, `runtime`,
and a loopback HTTP `base_url`. The adapter positively supports exactly
`image-generation`; RFC-0108 therefore permits that binding to own only
`image-generation`.

This closes an operator-composition gap only. It does not decide how an Image
Generation request or PNG result later crosses an ordinary process-to-operator
boundary.

## Context

RFC-0120 accepted the semantic capability:

```text
one bounded caller-supplied textual instruction
    ->
exactly one bounded still image
```

RFC-0121 selected `stable-diffusion.cpp` via one operator-managed loopback
`sd-server`, with adapter identity `stable-diffusion-cpp`, an image-only
positive capability set, private native job mechanics, adapter normalization,
and cluster-owned final PNG validation. Its real proof establishes ordinary
programmatic local composition.

RFC-0108 defines explicit capability-to-concrete-adapter ownership in one HAC
process. RFC-0110 provides the explicit TOML construction path for one or more
pairwise-disjoint bindings, but its closed vocabulary constructs only
`ollama`, `llama-server`, and `vllm`. The core can represent and execute
the image binding, but an operator cannot express it in RFC-0110 configuration.

## Problem

The missing fact is neither Image Generation semantics, PNG behavior, runtime
protocol, nor routing. It is this composition gap:

```text
accepted image-generation -> StableDiffusionCppAdapter binding
    is constructible programmatically

accepted RFC-0110 --runtime-config document
    cannot yet construct that binding
```

Expanding a legacy single-runtime document or adding a convenience CLI spelling
would decide separate compatibility and product surfaces.

## Goals

- Extend only RFC-0110's closed multi-binding runtime vocabulary with
  `stable-diffusion-cpp`.
- Preserve explicit RFC-0108 ownership, subset validation, and disjointness.
- Require the adapter's explicit validated loopback HTTP `base_url`.
- Permit image-only one-binding and disjoint mixed binding documents.
- Preserve ordinary request-capable `local` and applicable `static-cluster`
  local-binding semantics.
- Preserve retained configuration, observation, routing, transport, and Image
  Generation request/result boundaries.

## Non-goals

This RFC does not change RFC-0120 request or result semantics; PNG validation
or normalization; the native `StableDiffusionCppAdapter` protocol; or model,
model-file, device, backend, runtime policy, or `sd-server` lifecycle
ownership.

It does not add `--runtime stable-diffusion-cpp`, runtime-specific startup
flags, an RFC-0074 single-runtime TOML form, retained Image Generation or
multi-binding state, `hac config local`, browser configuration, status,
health, preflight, routing explanation, history, an Image Generation CLI,
native HTTP route, browser UI, filesystem output, temporary files, result URLs,
base64 result encoding, or generic binary/media abstractions.

It does not add remote Image Generation, receiver Image Generation,
HAC-to-HAC protocol changes, scheduling, capacity, fallback, retries, or
execution-availability changes. The later binary process-to-operator edge,
including whether it is CLI, browser, native HTTP plus a thin client, or
another bounded surface, remains undecided.

## Proposal

### One additional closed RFC-0110 binding runtime

RFC-0110 gains exactly this runtime-specific binding form:

```toml
[[bindings]]
capabilities = ["image-generation"]
runtime = "stable-diffusion-cpp"
base_url = "http://127.0.0.1:<PORT>"
```

The port is an operator placeholder; this RFC establishes no
stable-diffusion.cpp port convention.

For this runtime, `capabilities`, `runtime`, and `base_url` are required.
No other runtime-specific field is accepted. In particular, these must fail
locally rather than be ignored:

```text
model                 temperature            disable_thinking
seed                  dimensions             steps
sampler               scheduler              guidance / CFG
negative prompt       arbitrary options      any unknown key
```

RFC-0125 temperature remains a textual-runtime composition fact; its shared
spelling neither makes it generic nor permits it for this runtime.

### Capability and binding semantics

Binding ownership remains explicit operator input. HAC must not derive it from
`StableDiffusionCppAdapter.capabilities()`, adapter name, endpoint, model, or
runtime observation. RFC-0108 remains authoritative:

```text
binding.capabilities ⊆ binding.adapter.capabilities()
```

The adapter's positive capability set is exactly `image-generation`. A valid
current binding can therefore own only that capability. `chat`, `summarize`,
`classify`, and `code` fail under existing subset and execution-coherence
rules. Existing non-empty, duplicate-value, and pairwise-disjoint validation
remains unchanged.

A mixed document may include disjoint accepted textual bindings and an Image
Generation binding. It establishes no canonical mixed composition,
adapter-name selection, or declaration-order priority.

### Runtime-specific ownership

`base_url` is the one explicit operator-owned construction fact. It retains
RFC-0121 and existing HAC local-HTTP rules: it is an absolute loopback HTTP
origin/base URL, without path, query, fragment, user information, credentials,
LAN/Internet endpoint, TLS, or discovery. HAC-owned HTTP retains RFC-0085's
no-ambient-proxy boundary.

The value is not model selection or observed runtime truth. It grants no model
path, model discovery or installation, secret, filesystem, runtime-policy, or
lifecycle authority. Those remain runtime/operator-owned.

## Configuration shape

RFC-0110's collection remains one-or-more, so an image-only one-binding
document is permitted while RFC-0074's legacy single-runtime document remains
unchanged. Documents remain complete alternatives: `[[bindings]]` cannot mix
with RFC-0074 root `runtime` or runtime-specific tables; unknown root and
binding keys fail locally.

The RFC-0110 closed forms gain only:

```text
runtime = "stable-diffusion-cpp"
  required: capabilities, base_url
  optional: none
```

## Relationship to RFC-0074, RFC-0094, RFC-0110, RFC-0120/0121, and RFC-0125

RFC-0110 is the correct first path because it already expresses explicit
capability-to-concrete-adapter ownership, and its one-or-more collection covers
image-only composition. Image Generation is not historical text-runtime
default composition. Preserving RFC-0074 retains its compatibility meaning,
and no current need requires single-runtime convenience spelling. A later
convenience remains undecided.

RFC-0094 remains exact: selected `--runtime-config PATH` is self-contained
and bypasses retained runtime-composition baseline for that invocation. This
RFC adds no retained multi-binding state, persistence, precedence, or Image
Generation entry in `hac config local`.

RFC-0120 and RFC-0121 remain authoritative for semantics, execution,
normalization, final validation, identity, runtime boundary, and real proof.
This RFC only enables their accepted adapter through RFC-0110. RFC-0125
remains textual-runtime-only.

## Local/static-cluster boundary

The binding is available only through RFC-0110's explicitly selected
request-capable `--runtime-config PATH` path. Ordinary `local` may construct
it. Where RFC-0110 applies that path to request-capable `static-cluster`, the
existing local binding rule remains applicable, including its separation of
RFC-0108 execution ownership from RFC-0059 caller-local routing permission.

RFC-0126 does not expand RFC-0059 caller-local static capability permission.
The local binding therefore establishes local execution ownership, while
unchanged caller-local permission does not newly make `image-generation` an
eligible static-cluster local candidate. Implementation must not add
`image-generation` to a shared static capability vocabulary merely to route
this binding; whether RFC-0059 should permit it later is a separate decision.

This does not authorize remote Image Generation. In a static-cluster process:

- the binding is local process execution ownership only;
- no static remote declaration gains `image-generation`;
- no remote Image Generation candidate is created;
- no Image Generation request is serialized through HAC remote transport; and
- receiver routes remain unchanged.

Local binding ownership does not alter routing or transport semantics.

## Observation and retained-configuration boundaries

RFC-0110's observation boundary remains authoritative. A multi-binding document
using this runtime remains outside single-runtime status semantics and retains
the existing local rejection there. This RFC adds no multi-adapter status,
health, preflight, browser configuration, inspection, or routing explanation.

## Privacy and security boundary

The binding preserves loopback-only `sd-server` access, no external service or
hosted dependency, no secrets, no model path in HAC configuration, no ambient
proxy inheritance, no prompt/image retention, no filesystem authority, and no
runtime-lifecycle authority. The endpoint is explicit operator configuration,
not discovery or a claim about current runtime health.

## Compatibility

Existing RFC-0074 documents, RFC-0110 textual multi-binding documents, textual
runtime behavior, RFC-0125 temperature behavior, and programmatic RFC-0121
Image Generation composition remain valid and unchanged. No migration is
required.

The only new valid input is this closed RFC-0110 binding. It adds neither
retained configuration, legacy single-runtime convenience, an operator
request/output surface, filesystem authority, nor remote Image Generation.

## Rationale

The bounded sequence is:

1. RFC-0120 accepted the semantic capability and normalized binary result.
2. RFC-0121 selected and programmatically proved one real local adapter.
3. RFC-0110 already owns explicit capability-to-concrete-adapter construction.
4. Its closed schema cannot construct that accepted adapter.
5. This form closes the independent composition gap.
6. Ordinary PNG result delivery remains a future decision.

The smallest truthful configuration is explicit capability ownership plus the
adapter's accepted `base_url`. Generation controls or generic factories would
expand authority without resolving the narrow gap.

## Alternatives considered

### Expand RFC-0074 or ordinary `--runtime`

Rejected for this first path. It changes legacy single-runtime compatibility
and presents Image Generation as historical text composition. RFC-0110 is
already explicit and capability-centered.

### Infer ownership from adapter support

Rejected. RFC-0108 requires explicit ownership; adapter support is an upper
bound, not implicit operator configuration.

### Add model or generation settings

Rejected. Those facts are runtime/operator-owned or future decisions. Accepting
them would create generic options or expand Image Generation authority.

### Add retained configuration or observation

Rejected. RFC-0094 persistence and RFC-0110 observation are separate contracts.
The selected explicit file is sufficient here.

### Add remote Image Generation

Rejected. A process-local binding does not provide a remote request/result
transport or receiver contract, especially for the PNG result.

## Trade-offs

Operators must explicitly state capability and loopback origin, and cannot use
a short single-runtime spelling or retain this composition. Those limits keep
ownership visible and defer persistence, observation, result delivery, and
transport. The parser gains one runtime-specific case, not a generic factory or
options abstraction.

## Implementation boundary

If accepted, implementation is authorized only to:

- extend RFC-0110's closed multi-binding parser/validation vocabulary;
- accept explicit valid `image-generation` ownership;
- validate this runtime's `base_url` under existing local HTTP rules;
- construct exactly one `StableDiffusionCppAdapter` per binding;
- integrate it into the existing RFC-0108 relation; and
- preserve ordinary local and applicable static-cluster local-binding behavior,
  with focused tests and accurate documentation/examples.

It must not refactor unrelated code, introduce a generic runtime factory, or
generalize binding values merely for symmetry. A broader abstraction requires
separate justification.

## Proof expectations

Later implementation must prove that:

1. RFC-0074 single-runtime and RFC-0110 textual documents remain unchanged;
2. an image-only one-binding file with valid loopback `base_url` parses and
   constructs a concrete adapter with that exact validated URL;
3. its RFC-0108 binding owns exactly `image-generation`;
4. disjoint textual and Image Generation bindings construct without adapter-name
   or declaration-order selection;
5. assigning `chat`, `summarize`, `classify`, or `code` to
   `stable-diffusion-cpp`, or assigning `image-generation` to `ollama`,
   `llama-server`, or `vllm`, fails under existing subset/coherence rules;
   duplicate/overlapping ownership, missing/invalid `base_url`, and
   non-loopback URLs also fail locally;
6. `model`, `temperature`, `disable_thinking`, and unknown keys fail rather
   than being ignored;
7. retained state neither completes nor is mutated by the selected file, and
   multi-binding status rejection remains unchanged; and
8. remote declarations, remote protocol, receiver routes, remote capability
   behavior, and Image Generation operator request/output surfaces remain
   unchanged.

A physical `sd-server` inference proof is not required for this configuration
decision because RFC-0121 already retains successful real local evidence. A
later small proof is justified only if implementation exposes a distinct
configuration-to-concrete-adapter uncertainty.

## Decision

Accepted. RFC-0110 gains exactly the closed
`stable-diffusion-cpp` multi-binding construction form defined here, and no
other Image Generation surface or authority.
