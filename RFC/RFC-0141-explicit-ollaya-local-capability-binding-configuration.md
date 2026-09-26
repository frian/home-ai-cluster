# RFC-0141: Explicit Ollaya Local Capability-Binding Configuration

Status: Accepted

Date: 2026-09-26

Author: frian

## Summary

Home AI Cluster should extend RFC-0110's explicitly selected multi-binding `--runtime-config PATH` vocabulary with one additional closed runtime:

```text
ollaya
```

The binding constructs the accepted RFC-0140 `OllayaAdapter` from exactly four explicit operator-owned configuration facts:

```text
capabilities
runtime
base_url
model
```

The adapter positively supports exactly `classify`. RFC-0108 therefore permits an Ollaya binding to own exactly that capability.

Conceptually:

```toml
[[bindings]]
capabilities = ["classify"]
runtime = "ollaya"
base_url = "http://127.0.0.1:11435"
model = "laya"
```

This RFC closes one operator-composition gap only.

It does not add Ollaya to the legacy single-runtime configuration shape, ordinary `--runtime`, retained configuration, browser configuration, status, preflight, discovery, lifecycle management, routing policy, remote protocol, or generic runtime abstractions.

## Context

RFC-0061 accepts `classify` as a bounded first-class semantic capability.

RFC-0108 accepts explicit process-local capability-to-concrete-adapter ownership.

RFC-0110 exposes those bindings through one explicit, self-contained, closed multi-binding `--runtime-config PATH` document.

RFC-0119 permits one adapter to implement only the execution contracts required by the capabilities it positively supports.

RFC-0140 then accepts one concrete classification-only adapter:

```text
OllayaAdapter
```

with:

```text
adapter identity:
    ollaya

positive capability support:
    classify only

construction facts:
    explicit loopback HTTP base_url
    explicit process-local model
```

RFC-0140 also accepts native `/api/decide` execution while preserving:

- exact RFC-0061 Classify semantics;
- exact ordered labels;
- cluster-owned membership validation;
- capability-centered routing;
- runtime/model independence above the adapter;
- explicit operator-managed runtime lifecycle;
- no hidden external classification policy.

PR #817 implemented that adapter and proved one real programmatic RFC-0108 binding against an already-running Ollaya runtime using an explicit `laya` model.

The architecture can therefore already represent and execute:

```text
ClassifyRequest
    ->
RFC-0108 binding
    ->
OllayaAdapter(base_url=..., model=...)
    ->
native Ollaya decision
    ->
existing HAC Classify result
```

The remaining gap is configuration.

RFC-0110's closed runtime vocabulary cannot yet construct the accepted Ollaya adapter.

## Problem

The current state is:

```text
accepted and implemented OllayaAdapter
    +
accepted RFC-0108 programmatic classify binding
    +
successful real-machine proof

but

RFC-0110 --runtime-config
    cannot construct that same accepted binding
```

This prevents an operator from expressing an already accepted local execution composition through the existing operator-facing binding configuration surface.

No new semantic capability, execution contract, routing rule, request format, or result format is needed.

The missing decision is only:

> Should RFC-0110 be able to construct the already accepted RFC-0140 Ollaya classification binding?

## Goals

This RFC aims to:

- add exactly one closed `ollaya` runtime case to RFC-0110 multi-binding configuration;
- preserve explicit RFC-0108 capability ownership;
- require explicit `base_url`;
- require explicit `model`;
- preserve RFC-0140's loopback-only runtime boundary;
- preserve `classify` as Ollaya's only positively supported capability;
- preserve existing RFC-0110 disjoint binding semantics;
- reject unrelated runtime-specific fields rather than silently ignoring them;
- preserve all existing routing, transport, retained configuration, and observation boundaries.

## Non-goals

This RFC does not add:

- a new capability;
- changes to Classify semantics;
- RFC-0074 single-runtime Ollaya configuration;
- ordinary `--runtime ollaya`;
- retained Ollaya configuration;
- `hac config local` Ollaya support;
- browser configuration;
- model defaults;
- model discovery;
- runtime discovery;
- Ollaya lifecycle management;
- Ollaya installation;
- automatic model downloading or pulling;
- configurable question IDs;
- Ollaya presets;
- confidence or probability semantics;
- classification thresholds;
- label descriptions;
- aliases;
- implicit labels;
- generic decision abstractions;
- generic runtime/provider factories;
- runtime-aware routing;
- model-aware routing;
- load balancing;
- scheduling;
- status expansion;
- preflight expansion;
- remote Ollaya-specific configuration;
- remote protocol changes.

## Proposal

### One additional closed RFC-0110 binding runtime

RFC-0110 gains exactly this additional runtime-specific binding form:

```toml
[[bindings]]
capabilities = ["classify"]
runtime = "ollaya"
base_url = "http://127.0.0.1:11435"
model = "laya"
```

For `runtime = "ollaya"`:

```text
required:
    capabilities
    runtime
    base_url
    model

optional:
    none
```

No other binding field is accepted.

In particular, the following must fail locally rather than be ignored:

```text
temperature
disable_thinking
preset
question
question_id
threshold
confidence
probabilities
options
api_key
credentials
any unknown key
```

This remains a concrete closed runtime-specific parser branch.

It does not introduce generic provider configuration.

## Capability ownership

The operator must explicitly write:

```toml
capabilities = ["classify"]
```

HAC must not infer this value from:

```text
runtime = "ollaya"
```

or from:

```text
OllayaAdapter.capabilities()
```

RFC-0108 remains authoritative:

```text
binding.capabilities ⊆ binding.adapter.capabilities()
```

RFC-0140's adapter positive support is exactly:

```text
classify
```

Therefore the only currently valid Ollaya binding capability set is:

```text
{"classify"}
```

The following assignments must fail under existing ownership and execution-coherence rules:

```text
chat
summarize
code
image-generation
```

No configuration rule should special-case routing based on runtime identity.

The explicit binding relation remains the sole local ownership fact.

## Runtime construction

A valid Ollaya binding constructs exactly one:

```text
OllayaAdapter(
    base_url = configured_base_url,
    model = configured_model,
)
```

No additional construction state is implied.

The parser must not contact Ollaya while reading or validating configuration.

It must not discover:

- models;
- capabilities;
- endpoint variants;
- presets;
- runtime health;
- runtime availability.

Configuration construction remains local and deterministic.

## Base URL

`base_url` retains the exact RFC-0140 local-runtime boundary.

It must be validated using the existing HAC loopback HTTP origin rules.

Valid configuration identifies one explicit absolute loopback HTTP origin.

It must not permit:

- HTTPS;
- LAN or Internet hosts;
- credentials or user information;
- URL path;
- query;
- fragment;
- runtime discovery;
- port scanning;
- environment-derived endpoint selection.

Conceptually:

```text
http://127.0.0.1:<port>
http://[::1]:<port>
http://localhost:<port>
```

subject to the existing accepted HAC validation rules.

The constructed adapter retains RFC-0085's `trust_env=False` boundary.

This RFC grants no new network authority.

## Model

`model` is required.

It must be an explicit non-empty model identifier suitable for passing to the accepted RFC-0140 adapter constructor.

Its meaning remains exactly the RFC-0140 meaning:

> the explicit process-local model identifier the adapter requests from Ollaya.

HAC does not:

- assign semantic meaning to the model name;
- infer capabilities from it;
- inspect model metadata;
- discover installed models;
- validate classification quality;
- choose a model automatically;
- provide a model default;
- treat the model as routing data.

For example:

```toml
model = "laya"
```

is one valid explicit operator choice.

It does not make `laya` a HAC default or recommendation.

## Closed-field semantics

Ollaya must not be treated as another member of an implicit generic textual-runtime family.

The existence of common-looking configuration facts such as:

```text
base_url
model
```

does not make runtime configuration semantics generic.

In particular:

```text
temperature
disable_thinking
```

remain unavailable for Ollaya unless a later RFC explicitly accepts them.

Likewise, textual capability support must not be inferred from Ollaya being HTTP-based or model-based.

RFC-0140 remains authoritative:

```text
OllayaAdapter
    -> classify only
```

This RFC adds no fake symmetry with Ollama, llama-server, or vLLM.

## RFC-0110 binding semantics

All ordinary RFC-0110 rules remain unchanged.

A valid document still contains one or more explicit `[[bindings]]` entries.

Each binding still requires:

- non-empty explicit capabilities;
- no duplicate capability value;
- accepted capability names;
- one known runtime;
- runtime-specific valid construction facts;
- capability ownership compatible with the constructed adapter;
- execution-contract coherence.

The complete binding collection still requires pairwise-disjoint capability ownership.

Binding order remains irrelevant to adapter selection.

Adapter names remain non-identifying.

No binding ID is introduced.

One HAC process remains one cluster-visible local node.

## Mixed bindings

An Ollaya binding may coexist with other pairwise-disjoint RFC-0110 bindings.

For example:

```toml
[[bindings]]
capabilities = ["chat", "summarize"]
runtime = "ollama"
model = "llama3.2"

[[bindings]]
capabilities = ["classify"]
runtime = "ollaya"
base_url = "http://127.0.0.1:11435"
model = "laya"

[[bindings]]
capabilities = ["code"]
runtime = "vllm"
base_url = "http://127.0.0.1:8000"
model = "Qwen/Qwen2.5-Coder"
```

This represents explicit process-local execution ownership only.

It does not establish runtime ranking or model ranking.

The cluster continues to route by semantic capability, not runtime identity.

For a `classify` request, the binding identifies the exact concrete adapter responsible for locally executing that already-selected capability.

## Existing single-runtime configuration

RFC-0074 remains unchanged.

This RFC does not add Ollaya to its single-runtime document shape.

The absence is deliberate.

RFC-0074 preserves historical general textual runtime composition semantics.

RFC-0140 accepts Ollaya as a classification-only adapter.

Adding Ollaya to the single-runtime compatibility surface would decide a separate operator-product question and may create misleading symmetry with general textual runtimes.

That decision is unnecessary for closing the current RFC-0110 composition gap.

## Ordinary runtime CLI

Existing ordinary runtime selection remains unchanged.

This RFC does not add:

```text
--runtime ollaya
```

The explicit RFC-0110 multi-binding file is sufficient for the first operator-facing Ollaya composition.

Any future convenience spelling requires separate evidence and decision.

## Retained configuration

RFC-0094 remains unchanged.

Selecting:

```text
--runtime-config PATH
```

continues to use one explicit self-contained process-local runtime-composition source.

This RFC adds no retained multi-binding state.

It does not extend:

```text
hac config local
```

with Ollaya fields.

It does not merge explicit Ollaya bindings with retained runtime composition.

Existing precedence and replacement behavior remain authoritative.

## Local and static-cluster behavior

A valid Ollaya binding participates only through existing RFC-0110 request-capable composition.

Ordinary `hac local --runtime-config PATH` may construct the binding.

Where RFC-0110 already permits the selected multi-binding source for `static-cluster`, the same existing separation remains:

```text
RFC-0108 binding
    = process-local execution ownership

RFC-0059 local capability declaration
    = caller-local routing permission
```

This RFC does not collapse those concepts.

It does not add any new static capability name because `classify` already exists.

It does not infer caller-local permission from the Ollaya binding.

## Remote behavior

No remote protocol changes are required.

Ollaya remains a private receiver/local execution implementation detail.

Remote declarations remain capability-only.

A caller must not gain remote facts such as:

```text
runtime = "ollaya"
model = "laya"
base_url = ...
```

Existing HAC-to-HAC Classify transport remains unchanged.

A receiver whose own process-local configuration constructs an Ollaya `classify` binding may execute the request through that local adapter without the caller knowing which runtime or model was used.

## Observation and status

RFC-0110's existing observation boundary remains authoritative.

This RFC does not add multi-binding status semantics.

An Ollaya binding does not require HAC to expose:

- adapter inventory;
- configured model;
- observed model;
- model availability;
- per-adapter health;
- endpoint details.

The configuration truth:

```text
configured model = X
```

must not be presented as:

```text
runtime currently serves model X
```

unless a separate accepted observation contract establishes that fact.

Existing RFC-0110 status rejection for multi-binding documents remains unchanged.

No preflight change is required.

## Health

RFC-0140 already defines ordinary adapter-wide Ollaya health.

This RFC does not extend or reinterpret it.

Configuration parsing must not call health.

A configured binding is a construction fact, not observed availability.

Health remains distinct from:

- capability truth;
- binding ownership;
- routing permission;
- execution permission;
- model availability;
- scheduling.

## Privacy and security

The binding preserves all accepted RFC-0140 privacy and network boundaries:

```text
HAC
    ->
explicit operator-configured loopback HTTP Ollaya origin
```

No cloud service, credential, remote endpoint, discovery process, model inventory, telemetry, or external configuration service is introduced.

HAC-owned HTTP retains the existing no-ambient-proxy behavior.

No prompt, source, label, or result logging is added.

## Compatibility

Existing valid RFC-0074 configuration remains unchanged.

Existing valid RFC-0110 bindings for:

```text
ollama
llama-server
vllm
stable-diffusion-cpp
```

remain unchanged.

Existing retained configuration remains unchanged.

Existing CLI-only composition remains unchanged.

Existing routing, static topology, remote protocol, request/result formats, status behavior, and browser surfaces remain unchanged.

The only newly valid configuration input is one RFC-0110 binding whose runtime is:

```text
ollaya
```

and whose closed fields satisfy this RFC.

No existing operator configuration requires migration.

## Rationale

The bounded sequence is now:

1. RFC-0061 accepted the `classify` semantic capability.
2. RFC-0108 accepted explicit capability-to-concrete-adapter ownership.
3. RFC-0110 accepted explicit serialized multi-binding construction.
4. RFC-0140 accepted one concrete classification-only Ollaya adapter.
5. PR #817 proved that adapter through a real RFC-0108 binding and real Ollaya inference.
6. RFC-0110's closed runtime vocabulary still cannot construct that accepted adapter.
7. This RFC closes only that composition gap.

This mirrors the structurally relevant part of RFC-0121 → RFC-0126:

```text
concrete adapter accepted
    ->
programmatic local binding proven
    ->
existing explicit binding configuration cannot construct it
    ->
add one closed runtime-specific configuration case
```

The runtime-specific construction facts differ, but the architectural gap is the same.

A concrete fifth runtime branch is preferable to introducing a generic runtime factory without concrete need.

Boring explicit configuration remains the simpler design.

## Alternatives considered

### Keep Ollaya programmatic only

Rejected.

The programmatic proof has completed its purpose.

The accepted adapter and binding now work in real execution.

Preventing the existing RFC-0110 operator surface from expressing that accepted composition leaves a concrete usability gap without protecting any unresolved architecture.

### Add Ollaya to RFC-0074 single-runtime configuration

Rejected for this step.

That surface preserves historical general textual runtime composition.

Ollaya currently supports only `classify`.

The explicit capability-binding form is a more truthful first operator surface.

### Add ordinary `--runtime ollaya`

Rejected.

This would add a convenience/product surface beyond the operator-composition gap being solved.

### Add retained Ollaya configuration

Rejected.

Persistence is independent of explicit process-local multi-binding construction.

RFC-0110 intentionally works without retained multi-binding state.

### Infer `classify` from `runtime = "ollaya"`

Rejected.

RFC-0108 requires explicit capability ownership.

Adapter support is an upper bound, not operator intent.

### Permit textual runtime options

Rejected.

`temperature`, `disable_thinking`, and similar fields have runtime-specific accepted meanings elsewhere.

Common spelling does not create generic semantics.

RFC-0140 accepts no such Ollaya construction facts.

### Add generic runtime/provider factory configuration

Rejected.

Five concrete runtime cases do not by themselves demonstrate the need for another abstraction.

The runtimes have distinct accepted construction facts.

A closed parser branch is smaller and clearer.

### Add Ollaya model discovery

Rejected.

RFC-0140 explicitly requires an operator-provided model and rejects discovery.

### Add status/model observation

Rejected.

Serialized construction does not require new observation semantics.

RFC-0110 already deliberately excludes multi-binding status.

## Trade-offs

The operator must write:

```text
capabilities = ["classify"]
```

even though the adapter currently supports no other capability.

This repetition is intentional because capability support and binding ownership are distinct facts.

The operator must also explicitly provide both `base_url` and `model`.

This is less convenient than defaults or discovery but preserves visible runtime authority.

Ollaya remains unavailable through the shorter legacy runtime configuration forms.

That is acceptable because this RFC solves only the already demonstrated RFC-0110 composition gap.

The parser gains another runtime-specific branch instead of a generic runtime factory.

That duplication is accepted because runtime construction semantics remain different and the generic abstraction has not earned its complexity.

## Implementation boundary

If accepted, implementation is authorized only to:

- add `ollaya` to RFC-0110's closed multi-binding runtime vocabulary;
- accept exactly the closed Ollaya binding keys:
  - `capabilities`
  - `runtime`
  - `base_url`
  - `model`;
- require explicit non-empty `model`;
- validate `base_url` with the existing local HTTP rules;
- construct exactly one `OllayaAdapter` for each valid Ollaya binding;
- preserve explicit RFC-0108 ownership;
- preserve RFC-0119 execution-contract coherence;
- reject unsupported Ollaya capability assignments;
- reject textual-runtime and unknown Ollaya fields;
- preserve ordinary `local` and applicable `static-cluster` multi-binding behavior;
- add focused parser/construction tests;
- update only accurate configuration documentation/examples required by the new accepted form.

Implementation must not:

- add generic runtime factories;
- refactor unrelated adapters;
- modify routing policy;
- add retained state;
- add Ollaya to RFC-0074;
- add `--runtime ollaya`;
- change remote transport;
- change observation/status;
- change Classify semantics.

## Proof expectations

A later implementation must prove at minimum:

1. existing RFC-0074 single-runtime documents remain unchanged;
2. existing RFC-0110 runtime forms remain unchanged;
3. a valid Ollaya binding parses successfully;
4. the configured exact loopback `base_url` reaches the constructed `OllayaAdapter`;
5. the configured exact `model` reaches the constructed `OllayaAdapter`;
6. the binding owns exactly explicitly supplied `classify`;
7. `chat`, `summarize`, `code`, and `image-generation` ownership fail;
8. missing `base_url` fails locally;
9. invalid or non-loopback `base_url` fails locally;
10. missing or invalid `model` fails locally;
11. `temperature` fails rather than being ignored;
12. `disable_thinking` fails rather than being ignored;
13. unknown keys fail rather than being ignored;
14. mixed pairwise-disjoint bindings including Ollaya construct successfully;
15. overlapping ownership remains rejected;
16. declaration order does not acquire routing meaning;
17. no retained configuration is read or mutated to complete the binding;
18. multi-binding status behavior remains unchanged;
19. remote declaration and transport behavior remain unchanged.

A second real-machine Ollaya inference proof is not required for this configuration decision because RFC-0140 and PR #817 already retain successful real local evidence.

A small configuration-to-real-execution proof is justified only if implementation exposes uncertainty about constructing the accepted adapter from the serialized fields.

## Decision

Accepted. RFC-0110 gains exactly one additional closed multi-binding runtime:

```text
runtime = "ollaya"
```

with:

```text
required:
    capabilities
    base_url
    model

optional:
    none
```

The configured binding explicitly owns a subset of the constructed adapter's positive capability support. Under current RFC-0140 semantics, that means exactly:

```text
capabilities = ["classify"]
```

The binding constructs:

```text
OllayaAdapter(
    base_url = validated explicit loopback HTTP origin,
    model = explicit model identifier,
)
```

No capability ownership is inferred from runtime identity.

No textual-runtime options become valid.

No legacy single-runtime, ordinary runtime CLI, retained configuration, browser, status, preflight, discovery, lifecycle, routing, remote protocol, or generic provider abstraction is added.

The decision closes only the RFC-0110 operator-composition gap for the already accepted and proven RFC-0140 Ollaya adapter.
