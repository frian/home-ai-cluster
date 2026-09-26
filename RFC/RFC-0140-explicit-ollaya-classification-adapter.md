# RFC-0140: Explicit Ollaya Classification Adapter

Status: Accepted

Date: 2026-09-26

Author: frian

## Summary

Home AI Cluster should add one concrete `ollaya` runtime adapter that supports exactly the existing `classify` capability.

The adapter should connect to one explicitly configured local Ollaya HTTP runtime, translate one normalized `ClassifyRequest` into one native Ollaya choice decision, return one proposed label, and leave exact label-membership validation to the existing HAC Classify boundary.

The first accepted integration should be deliberately narrow:

```text
existing HAC classify semantics
    ->
one concrete Ollaya adapter
    ->
explicit local base URL + model construction facts
    ->
one programmatic RFC-0108 local capability binding
    ->
real inference proof
```

The adapter should not add a new capability, new routing policy, generic decision abstraction, model discovery, runtime discovery, retained configuration, browser configuration, remote protocol, confidence semantics, or RFC-0110 runtime vocabulary.

The first real-machine proof may use Ollaya's `laya` model, but `laya` is not a HAC default, recommendation, capability fact, routing fact, or architectural dependency.

## Context

Accepted RFC-0061 defines `classify` as a first-class bounded HAC capability.

Its core semantic boundary is already sufficient for a specialized classification runtime:

```text
ClassifyRequest
    text
    exact ordered labels

adapter
    proposes one label

HAC
    validates exact membership

ClassifyResult
    selected_label
    node_id
```

The adapter is permitted to use runtime-private prompting, grammars, JSON modes, constrained decoding, or equivalent native machinery. Those mechanics do not become part of the HAC capability contract.

Accepted RFC-0066 keeps semantic capabilities independent of runtimes and models. A runtime or model being specialized for classification does not create a new capability and must not become a routing criterion.

Accepted RFC-0108 defines explicit process-local capability-to-adapter ownership.

Accepted RFC-0110 permits explicit local runtime composition while retaining a closed operator-facing runtime vocabulary.

Accepted RFC-0119 separates:

```text
common adapter concerns

from

distinct execution contracts
```

and permits an adapter to support only the execution contracts required by the capabilities it positively claims.

Therefore an adapter supporting only:

```text
classify
```

is a valid use of the accepted architecture.

A previous real-machine exploration provides concrete motivation for this adapter. On one bounded 24-case corpus, Ollaya with Laya substantially outperformed the tested general-purpose local models for that classification workload while also completing decisions quickly.

Those measurements motivate investigating a concrete adapter. They do not establish a universal benchmark, preferred model, automatic selection policy, or new architectural abstraction.

## Problem

HAC currently supports Classify through general-purpose textual runtime adapters.

Ollaya exposes a runtime specifically suited to bounded choice decisions. HAC cannot use that runtime without a concrete adapter translating the existing normalized Classify contract into Ollaya's native protocol.

The architectural question is narrow:

> Can HAC add one classification-only concrete adapter without changing Classify semantics, routing semantics, capability ownership, or ordinary runtime configuration?

The answer should preserve these existing boundaries:

```text
Classify semantics
    owned by HAC

adapter-native request translation
    owned by the Ollaya adapter

model selection
    explicit process-local adapter construction fact

capability ownership
    explicit RFC-0108 binding

routing
    capability-centered and runtime-independent

result validity
    cluster-owned exact-label validation
```

The integration must not turn Ollaya's broader native decision concepts into a generic HAC decision capability.

## Goals

This RFC aims to:

- add one concrete `ollaya` adapter;
- support exactly the existing `classify` capability;
- reuse the accepted RFC-0061 Classify request and result semantics unchanged;
- use the existing RFC-0119 Classify execution contract;
- permit explicit programmatic RFC-0108 binding of `classify` to one Ollaya adapter instance;
- connect only to one explicitly supplied loopback HTTP Ollaya origin;
- make model selection explicit and process-local;
- keep Ollaya's native protocol adapter-private;
- preserve cluster-owned exact label validation;
- preserve existing failure semantics;
- perform one bounded real-machine proof using actual Ollaya inference;
- avoid expanding ordinary operator configuration until concrete evidence justifies that next step.

## Non-goals

This RFC does not authorize:

- a new HAC capability;
- a generic `decision`, `choose`, `route`, `score`, or structured-decision capability;
- changes to RFC-0061 Classify semantics;
- automatic label generation;
- label descriptions, aliases, examples, weights, or hidden metadata;
- confidence scores, probabilities, thresholds, rationales, or alternative labels;
- semantic repair, fuzzy matching, trimming, case folding, or label normalization;
- model-based or runtime-based routing;
- automatic runtime selection;
- model discovery;
- runtime discovery;
- Ollaya lifecycle management;
- model installation or download;
- retained Ollaya configuration;
- browser Ollaya configuration;
- `hac config` support;
- `runtime = "ollaya"` in RFC-0110;
- an `--runtime ollaya` ordinary CLI form;
- changes to the remote HAC protocol;
- remote Ollaya discovery or negotiation;
- runtime-specific capability probing;
- LAN Ollaya access;
- HTTPS or authentication configuration;
- a generic OpenAI-compatible adapter;
- a generic decision-model adapter framework;
- a plugin system;
- changes to scheduling, fallback, execution permission, or execution accounting;
- a new public HTTP capability contract; or
- benchmark-based automatic policy.

## Proposal

### Concrete adapter identity

HAC should gain one concrete adapter with stable identity:

```text
ollaya
```

The adapter should participate in the existing common adapter surface and positively advertise exactly:

```text
classify
```

It must not advertise:

```text
chat
summarize
code
image-generation
```

or any future capability merely because Ollaya or its selected model may be mechanically capable of broader behavior.

Capability support remains explicit semantic truth.

It must not be inferred from:

- adapter class;
- runtime identity;
- model identity;
- endpoint behavior;
- model metadata;
- successful probing; or
- native Ollaya feature availability.

### Execution contract

The adapter should implement the existing RFC-0119 Classify execution contract.

Conceptually:

```text
classify(ClassifyRequest) -> proposed label
```

No Ollaya-specific request or result type should cross into the HAC core.

The normalized request remains the existing RFC-0061 request:

```text
ClassifyRequest
    text
    exact ordered labels
    existing request constraints
```

The normalized successful result remains the existing HAC Classify result.

No change to RFC-0061 is required.

### Explicit construction facts

The first adapter construction should require explicit programmatic facts equivalent to:

```text
base_url
model
```

Both are process-local runtime construction facts.

They are not request data.

They are not capability data.

They are not routing data.

They are not remote-node declaration data.

They are not dynamically discovered.

#### Base URL ownership

`base_url` identifies one explicit operator-provided Ollaya HTTP origin.

For this first boundary it must be a loopback HTTP origin.

Conceptually acceptable forms are equivalent to:

```text
http://127.0.0.1:<port>
http://[::1]:<port>
```

subject to existing HAC loopback-origin validation conventions.

The adapter must not:

- resolve a hostname to discover Ollaya;
- scan ports;
- search the LAN;
- select an endpoint automatically;
- accept credentials embedded in the URL;
- treat URL path, query, or fragment as configuration;
- use ambient proxy configuration.

HTTP clients used for this adapter must preserve HAC's existing local-runtime network posture, including `trust_env = false` where applicable.

Ollaya process lifecycle remains operator-owned.

HAC does not start, stop, supervise, install, repair, or update Ollaya.

#### Model ownership

`model` is an explicit process-local, adapter-owned runtime configuration fact.

It identifies the model that the Ollaya adapter requests from the configured Ollaya runtime.

The adapter must actually use that explicit construction fact when forming the native Ollaya request.

It must not treat `model` as:

- merely descriptive metadata;
- a value discovered after execution;
- an implicit runtime default;
- a capability selector;
- a routing selector;
- request data; or
- cluster topology.

HAC does not interpret the semantic meaning of the model identifier.

The model does not affect Classify eligibility.

The model does not create a capability.

The model does not influence candidate priority.

The first real-machine proof may explicitly construct the adapter with:

```text
model = "laya"
```

but `laya` is not accepted as a HAC default or recommendation.

No model is implied when this construction fact is absent; the first adapter construction requires it explicitly.

### Native Classify mapping

The Ollaya adapter should translate one `ClassifyRequest` into one native Ollaya choice decision.

The semantic inputs to that mapping must be limited to:

```text
request.text
request.labels in exact supplied order
fixed adapter-private translation mechanics
explicit adapter construction facts needed to address runtime/model
```

The adapter may choose private native details such as:

- endpoint path;
- question identifier;
- fixed instruction text;
- field names;
- native request envelope;
- native response extraction.

Those mechanics remain implementation-private unless future evidence requires architectural standardization.

The mapping must preserve the exact supplied label strings and their order.

The adapter must not:

- invent a label;
- remove a label;
- add an implicit `unknown`;
- add a fallback choice;
- rename labels;
- attach semantic descriptions to labels;
- infer aliases;
- reorder labels for policy reasons;
- introduce weights;
- introduce confidence thresholds; or
- silently reinterpret one HAC label as another.

### No hidden external classification policy

The semantic meaning of one adapter execution must be determined by:

```text
ClassifyRequest.text
+
the exact ordered request.labels
+
fixed adapter-private mapping
```

The integration must not depend on hidden mutable Ollaya-side configuration that enriches or changes the HAC classification contract.

In particular, adapter correctness must not require an external Ollaya preset or configuration that silently introduces:

- label descriptions;
- alternate label names;
- aliases;
- examples carrying label-specific semantics;
- an unknown class;
- a none class;
- thresholds;
- score-based acceptance;
- fallback policy;
- label weighting;
- label suppression; or
- other classification policy not represented by the HAC request.

This does not prohibit ordinary runtime/model configuration owned by Ollaya.

It does prohibit treating external hidden classification policy as though it were part of the normalized HAC Classify request.

Two conforming HAC Ollaya adapter instances receiving the same normalized request should therefore differ only through their explicitly constructed runtime/model and native model behavior, not through undisclosed HAC label semantics.

### Native response normalization

The adapter should extract exactly one proposed label string from Ollaya's successful native response.

Ollaya-native confidence values, probabilities, scores, rationales, explanations, alternatives, or other decision metadata must not enter the normalized HAC result.

They may be ignored.

The adapter must not use confidence or probability as a second success policy.

For example, it must not reject a requested label because a native confidence value is below an adapter-owned threshold unless a future RFC changes Classify semantics.

Under RFC-0061, the relevant structural question remains only:

```text
did the adapter propose one usable string?
```

followed by the cluster-owned question:

```text
is that string exactly one supplied label?
```

### Cluster-owned exact-label validation

The adapter must not become the final authority on result membership.

Conceptually:

```text
Ollaya native response
    ↓
adapter extracts proposed string
    ↓
HAC Classify core
    ↓
exact proposal in request.labels?
```

The existing RFC-0061 result rule remains authoritative.

HAC performs:

- no trimming;
- no case folding;
- no Unicode normalization;
- no fuzzy matching;
- no prefix extraction;
- no prose parsing;
- no alias mapping;
- no conversion such as `"Label: invoice"` to `"invoice"`.

A syntactically usable string that is not exactly one member of the original label set must reach the existing cluster-owned invalid-classification-result boundary.

The adapter must not silently repair it.

### Failure semantics

This adapter introduces no new public failure category.

Existing HAC failure semantics remain authoritative.

The implementation must preserve the distinction between:

```text
runtime / transport unavailable

and

runtime responded but no usable classification proposal could be normalized

and

usable proposed string fails cluster-owned exact-label membership validation
```

#### Runtime or transport unavailability

A genuine failure to reach or communicate with the configured Ollaya runtime should use the existing runtime/transport availability semantics appropriate to the exact failure point.

The adapter must not broaden those semantics to cover malformed successful native responses.

#### Unusable successful native response

If Ollaya successfully responds but the response contains no structurally usable proposed classification string, including cases equivalent to:

- expected choice field absent;
- choice value missing;
- choice value non-string;
- response structure otherwise unable to yield one proposal;

the adapter must treat this as an invalid classification result / execution failure according to the existing Classify failure boundary.

It must not report the runtime as unavailable merely because normalization failed after a response was received.

This preserves the failure distinction already required by existing Classify semantics.

#### Proposed string outside the requested labels

If the adapter successfully extracts a string but that string is not exactly present in `request.labels`, the adapter should return the proposal to the existing cluster-owned Classify validation boundary.

The adapter must not convert that case into runtime unavailability.

The adapter must not invent its own failure taxonomy for membership.

HAC's existing exact-label validation remains the authority.

### Health

The adapter should expose ordinary adapter-wide health through the existing common adapter health boundary.

Health remains descriptive and bounded.

It must not become:

- model discovery;
- capability discovery;
- a claim of future classification success;
- runtime capacity;
- execution permission;
- scheduler input;
- model quality measurement; or
- a benchmark.

The exact minimal health interaction may remain an implementation detail consistent with existing runtime-adapter conventions.

### Programmatic local binding

The first accepted composition should use the existing RFC-0108 programmatic binding mechanism.

Conceptually:

```text
OllayaAdapter(
    base_url = explicit loopback origin,
    model = explicit model identifier,
)

LocalCapabilityBinding(
    adapter = ollaya_adapter,
    capabilities = ["classify"],
)
```

The binding must own exactly:

```text
classify
```

for the proof composition.

No new binding type is introduced.

No adapter-selection rule is introduced.

No routing branch may inspect `adapter == ollaya`, `model == laya`, or equivalent runtime/model identity.

Once local capability ownership is established, ordinary capability-centered routing remains authoritative.

### Executable admission

RFC-0119 remains authoritative.

An Ollaya adapter claiming:

```text
classify
```

must satisfy the Classify execution contract before entering request-executable use.

A contradictory state such as:

```text
adapter claims classify
but lacks valid Classify execution support
```

is invalid executable composition.

It is not:

- runtime unavailable;
- no matching candidate;
- execution-permission denial;
- request-time unsupported operation.

Conversely, the existence of a mechanically callable method must not create support for any additional capability.

### Routing

This RFC changes no routing semantics.

Routing continues to depend on capabilities and existing ownership/permission rules.

HAC must not prefer Ollaya because it is:

- specialized;
- faster in one benchmark;
- using Laya;
- classification-specific;
- locally reachable;
- healthier than another runtime; or
- believed to be more accurate.

No quality scoring or model-aware routing is introduced.

For the same request:

```text
capability = classify
```

the routing layer should not need to know whether the bound adapter is:

```text
ollama
llama-server
vllm
ollaya
```

Runtime identity remains below the capability-routing boundary.

### Remote execution

This RFC does not change HAC's remote protocol.

A receiver may execute `classify` through an Ollaya adapter if that receiver's local composition explicitly owns `classify` through such an adapter.

The caller does not need to know this.

Remote declarations continue to contain only caller-owned topology and capability facts.

They must not gain:

- `runtime = ollaya`;
- `model = laya`;
- Ollaya endpoint;
- native protocol information; or
- specialized classifier metadata.

The existing Classify remote request/result contract remains unchanged.

### RFC-0110 operator runtime configuration

This RFC does not add:

```text
runtime = "ollaya"
```

to RFC-0110.

It also does not add:

```text
--runtime ollaya
```

to ordinary runtime CLI configuration.

The first proof requires only programmatic RFC-0108 composition.

This preserves the closed operator-facing runtime vocabulary until there is concrete evidence that Ollaya should become an ordinary configurable HAC runtime.

If that later need is accepted, it should be handled by a separate RFC focused only on operator configuration, analogous in structure to the later configuration step taken for stable-diffusion.cpp.

That future RFC would need to decide the exact retained/runtime-config representation and interaction with existing composition rules.

This RFC does not pre-decide it.

### Retained and browser configuration

No retained Ollaya configuration is added.

No browser configuration is added.

No configuration UI should infer Ollaya support from the presence of an installed adapter.

No retained model default is introduced.

No migration is required.

### Privacy and network boundary

The adapter must preserve HAC's local-first and privacy-first posture.

The first boundary is explicitly local:

```text
HAC process
    ->
explicit loopback HTTP Ollaya runtime
```

No prompt, source text, or label set should be transmitted anywhere other than the explicitly configured loopback Ollaya runtime as part of this adapter.

Ambient proxy configuration must not redirect that traffic.

Native failure responses must not be surfaced verbatim when doing so would leak runtime-specific or request-specific details through existing HAC failure boundaries.

No credentials, cloud service, discovery mechanism, telemetry requirement, or external network dependency is introduced.

## Real-machine proof

Implementation should include one bounded real-machine proof after focused automated validation.

The proof should use:

- one explicit local Ollaya runtime;
- one explicitly selected Ollaya model;
- one programmatically constructed Ollaya adapter;
- one explicit programmatic `classify` binding;
- one real normalized Classify request;
- actual Ollaya inference;
- one successful HAC `ClassifyResult`.

The first proof may use:

```text
model = laya
```

The proof should establish only that the accepted adapter path is real:

```text
HAC ClassifyRequest
    ->
Ollaya adapter
    ->
Ollaya native choice inference
    ->
proposed string
    ->
HAC exact-label validation
    ->
ClassifyResult
```

It should not be presented as:

- a universal accuracy benchmark;
- a performance guarantee;
- a model recommendation;
- a default-selection proof;
- evidence for model-aware routing.

A small comparison corpus may be retained as motivation or evidence of practical usefulness, but it is not part of the adapter's semantic contract.

## Validation expectations

A later implementation should include focused tests sufficient to prove the accepted boundary.

At minimum, validation should cover:

- adapter identity is stable;
- adapter positively supports exactly `classify`;
- executable admission accepts its Classify execution contract;
- explicit base URL validation preserves the accepted loopback-only network boundary;
- explicit model construction is used in native requests;
- request text reaches the native mapping unchanged;
- labels reach the native mapping in exact supplied order;
- labels are not invented, removed, renamed, trimmed, or reordered;
- a successful native choice exactly matching a requested label can become a normal Classify success;
- a syntactically usable choice outside the label set reaches cluster-owned exact-label rejection;
- absent native choice does not become runtime unavailable;
- non-string native choice does not become runtime unavailable;
- malformed successful native response does not become runtime unavailable;
- genuine connection failure preserves existing availability semantics;
- native confidence/probability metadata does not enter HAC result semantics;
- programmatic binding may own exactly `classify`;
- Ollaya identity or model identity does not enter routing policy.

Tests should remain focused on this adapter and existing boundaries.

This RFC does not justify a generic adapter test framework.

## Alternatives considered

### Use ordinary Chat prompting instead

Rejected.

Classification already has a first-class HAC capability with exact request and result semantics.

Returning to Chat prompting would weaken that boundary.

### Add a generic decision capability

Rejected.

The concrete requirement is already represented by `classify`.

Ollaya's native vocabulary does not justify importing a more general abstraction into HAC.

### Add a new `ollaya-classify` capability

Rejected.

Capabilities describe semantic needs, not runtimes or implementation choices.

The semantic need remains `classify`.

### Require Ollaya to support all textual execution contracts

Rejected.

RFC-0119 explicitly permits adapters with only the execution contracts required by their positive capability claims.

Fake Chat, Summarize, or Code methods would make the architecture less truthful.

### Add `runtime = "ollaya"` immediately

Rejected for this RFC.

The first proof can be composed through existing programmatic binding.

Expanding RFC-0110 is an operator-facing decision that can be evaluated separately after the adapter proves useful.

### Add retained configuration immediately

Rejected.

Persistence is unnecessary for proving the adapter boundary.

### Add browser configuration immediately

Rejected.

The adapter execution contract does not require a new browser authority.

### Make the model runtime-owned and implicit

Rejected for this proposal.

The first integration should make model selection explicit as a process-local adapter construction fact.

This avoids silently depending on whichever model Ollaya happens to choose as a default.

### Use a hidden Ollaya preset with richer classification semantics

Rejected.

That would allow external mutable configuration to redefine the meaning of a normalized HAC Classify request.

The exact labels belong to the caller's HAC request.

### Expose confidence or probability

Rejected.

RFC-0061 deliberately does not make them part of Classify success semantics.

### Apply a confidence threshold internally

Rejected.

That would introduce a new result policy not represented by RFC-0061.

### Validate label membership entirely inside the adapter

Rejected.

The adapter proposes.

HAC validates exact membership.

Moving final membership authority into the adapter would weaken the engine-independent Classify boundary.

### Treat malformed successful Ollaya responses as runtime unavailable

Rejected.

A runtime that responded is not made unavailable merely because its result cannot be normalized into a usable classification proposal.

Existing failure semantics must remain truthful.

### Freeze one native Ollaya endpoint in architecture

Rejected.

The adapter must have one concrete implementation, but the exact native path does not need to become a HAC architectural contract unless later evidence requires it.

### Add remote Ollaya-specific protocol fields

Rejected.

Remote execution remains capability-centered and runtime-independent.

## Trade-offs

The first integration is intentionally less convenient than a normal `--runtime ollaya` operator configuration.

That is accepted.

It proves the smallest architectural seam first:

```text
concrete adapter
+
existing Classify contract
+
existing binding
```

before expanding operator-facing configuration.

The adapter also deliberately discards native Ollaya metadata that might appear useful, such as confidence or alternative scores.

That is accepted because HAC's existing Classify contract has a smaller and clearer truth boundary.

Requiring an explicit model adds one construction fact but avoids hidden dependence on Ollaya defaults.

Preventing hidden semantic presets may constrain some native Ollaya workflows, but preserves the property that the meaning of a HAC Classify request is visible in the normalized request itself.

## Relationship to existing RFCs

RFC-0061 remains authoritative for:

- Classify request semantics;
- label bounds and ordering;
- exact-label result validation;
- absence of confidence/threshold/rationale semantics.

RFC-0066 remains authoritative for capability identity independent of runtime and model identity.

RFC-0071 provides precedent for explicit process-local adapter-owned model configuration without making model identity request or routing data.

RFC-0085 and RFC-0089 remain relevant to explicit local runtime HTTP/network privacy boundaries.

RFC-0108 remains authoritative for local capability binding and ownership.

RFC-0110 remains unchanged. Its current operator-facing runtime vocabulary is not extended by this RFC.

RFC-0119 remains authoritative for capability-coherent execution contracts and permits a classification-only adapter.

RFC-0121 provides precedent for accepting one concrete specialized adapter and programmatic binding before accepting ordinary runtime configuration.

RFC-0126 demonstrates that operator-facing runtime configuration can be added later through a separate bounded RFC when justified.

No accepted RFC is superseded by this proposal.

## Impact

Acceptance of this RFC authorizes a bounded implementation that:

- adds one concrete `ollaya` adapter;
- positively supports exactly `classify`;
- implements the existing Classify execution contract;
- uses explicit loopback `base_url` and explicit process-local `model`;
- maps normalized Classify requests into one adapter-private Ollaya choice operation;
- prevents hidden external Ollaya classification policy from changing HAC label semantics;
- extracts one proposed string while discarding native decision metadata;
- preserves cluster-owned exact-label validation;
- preserves existing availability versus execution/result failure semantics;
- supports programmatic RFC-0108 binding;
- performs focused automated tests;
- performs one real-machine Ollaya inference proof.

Acceptance does not authorize:

- RFC-0110 Ollaya configuration;
- retained configuration;
- browser configuration;
- remote protocol changes;
- generic decision abstractions;
- confidence semantics;
- runtime/model-based routing;
- lifecycle management.

## Open questions

No architectural question is required to be resolved beyond this RFC before implementing the first bounded adapter proof.

Implementation may choose ordinary private mechanics such as:

- exact Ollaya HTTP endpoint path;
- exact native JSON field names;
- exact fixed question identifier;
- exact internal helper structure;
- exact HTTP client placement;
- exact adapter-private response extraction code.

Those choices must remain within the boundaries accepted here and must not introduce new semantic policy.

If implementation discovers that Ollaya cannot provide the proposed choice mapping without relying on hidden external classification semantics, that evidence should return to architecture review rather than being worked around implicitly.

## Decision

Accepted. Home AI Cluster will add one explicit concrete `ollaya` adapter supporting exactly the existing `classify` capability.

The adapter will connect only to one explicitly constructed loopback Ollaya HTTP runtime, with explicit process-local adapter-owned model selection. It will translate the existing normalized Classify request into one adapter-private Ollaya choice decision whose semantic inputs are limited to the request text, the exact ordered labels, fixed translation mechanics, and explicit runtime/model construction facts.

Hidden external Ollaya configuration must not enrich or transform HAC label semantics.

The adapter will return one structurally usable proposed string. Existing HAC Classify logic will remain responsible for exact membership in the original requested labels. Ollaya-native confidence, probabilities, rationales, alternatives, and other decision metadata will not enter HAC Classify semantics.

A successful Ollaya HTTP response that cannot yield one usable proposed string will remain an execution/result failure rather than being mislabeled as runtime unavailability. A usable proposed string outside the requested labels will reach the existing cluster-owned RFC-0061 membership validation.

The adapter may be bound programmatically to `classify` through the existing RFC-0108 mechanism. This RFC does not extend RFC-0110 with `runtime = "ollaya"`, does not add retained or browser configuration, does not change routing or remote protocol, and does not introduce a generic decision abstraction.

The first implementation should conclude with one real local Ollaya inference proof. The proof may use `laya` as its explicit model, but no HAC default, recommendation, routing preference, or architectural dependency on Laya is created.
