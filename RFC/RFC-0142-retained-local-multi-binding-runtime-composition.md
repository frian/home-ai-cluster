# RFC-0142: Retained Local Multi-Binding Runtime Composition

Status: Accepted

Date: 2026-09-26

Author: frian

## Summary

Home AI Cluster should allow its existing HAC-managed retained local configuration to retain one complete RFC-0110-style local capability-binding composition as an alternative to the existing singular textual runtime composition.

Conceptually, retained local runtime composition becomes:

```text
exactly one complete local runtime composition

either

    singular textual runtime composition

or

    multi-binding runtime composition
```

A retained multi-binding composition contains explicit, pairwise-disjoint local capability ownership and the accepted runtime-specific construction facts required to reconstruct each concrete adapter.

The first retained multi-binding form intentionally excludes `image-generation`. RFC-0128 remains the sole retained owner of the optional local stable-diffusion.cpp Image Generation companion.

The intended operator workflow is:

```text
explicit RFC-0110 runtime-config document
        ↓
hac config local mutation
        ↓
validate complete composition now
        ↓
retain semantic binding facts
        ↓
source document loses authority
        ↓
ordinary later `hac local`
reconstructs retained bindings
```

This RFC does not retain a runtime-config path, does not introduce incremental binding CRUD, does not make the retained storage representation public, and does not add runtime discovery, lifecycle management, observation, routing policy, or generic provider abstractions.

## Context

RFC-0094 establishes one HAC-managed retained configuration surface.

Its retained local domain includes process-local runtime composition together with distinct HAC policy facts such as caller-local static routing capability permission and the retained HAC execution limit.

The retained runtime composition historically represents one singular textual runtime.

RFC-0108 later accepts explicit process-local capability-to-concrete-adapter ownership.

RFC-0110 provides an explicit `--runtime-config PATH` document for one or more pairwise-disjoint capability bindings.

That document is deliberately self-contained and remains separate from RFC-0094 retained runtime composition.

RFC-0126 extends RFC-0110 with the specialized stable-diffusion.cpp Image Generation adapter.

RFC-0128 then accepts one optional retained Image Generation companion rather than introducing general retained bindings. At that stage, a generalized retained binding model was not yet justified by multiple concrete specialized-runtime needs.

RFC-0140 accepts the classification-only Ollaya adapter.

RFC-0141 adds Ollaya to RFC-0110's explicit multi-binding runtime configuration.

The resulting ordinary process-local composition can now truthfully be:

```text
chat / summarize / code
    -> Ollama

classify
    -> Ollaya
```

and that composition has been implemented and proven through RFC-0110 configuration.

However, it cannot be retained as the ordinary HAC startup baseline.

The operator must continue to remember:

- that an external runtime-config file exists;
- where that file is located; and
- that `--runtime-config PATH` must be supplied on every applicable startup.

This is now a demonstrated operator gap rather than a hypothetical persistence feature.

## Problem

HAC currently has two relevant truths:

```text
RFC-0110
    can represent and construct a complete multi-binding local composition

RFC-0094
    can retain an ordinary local runtime-composition baseline
```

but these truths do not meet.

A composition such as:

```toml
[[bindings]]
capabilities = ["chat", "summarize", "code"]
runtime = "ollama"
model = "llama3.2"

[[bindings]]
capabilities = ["classify"]
runtime = "ollaya"
base_url = "http://127.0.0.1:11435"
model = "laya"
```

can be selected explicitly for one invocation:

```text
hac local --runtime-config PATH
```

but ordinary later:

```text
hac local
```

cannot reconstruct that composition from HAC-managed retained configuration.

Retaining only the source file path would not solve the ownership problem.

The retained behavior would then remain dependent on an externally mutable file whose contents could change, move, or disappear without a retained HAC mutation.

The retained configuration should own semantic configuration facts, not a durable pointer to an unmanaged source document.

## Goals

This RFC aims to:

- extend the existing retained local runtime-composition domain with one alternative complete multi-binding shape;
- reuse accepted RFC-0108 and RFC-0110 binding semantics;
- retain semantic adapter-construction facts rather than a runtime-config path;
- allow ordinary later `hac local` startup to reconstruct the retained multi-binding composition;
- preserve one semantic owner for local runtime composition;
- preserve legacy singular retained runtime configuration unchanged;
- preserve explicit complete-replacement semantics;
- preserve RFC-0059 caller-local routing permission as a distinct fact;
- preserve RFC-0106 HAC execution policy as a distinct fact;
- preserve RFC-0128 as the retained owner of local Image Generation for this first stage;
- preserve browser fail-closed behavior where browser mutation cannot represent the new local state;
- preserve explicit `--runtime-config PATH` as a self-contained invocation-time alternative;
- avoid a new incremental binding-editing language.

## Non-goals

This RFC does not add:

- runtime discovery;
- model discovery;
- runtime health observation;
- model observation;
- runtime lifecycle management;
- runtime installation;
- model downloading or pulling;
- remote runtime or model facts;
- configuration synchronization;
- runtime-config path retention;
- runtime-config file watching;
- reload;
- profiles;
- inheritance;
- environment-variable configuration selection;
- binding priorities;
- binding IDs;
- incremental binding CRUD;
- generic provider configuration;
- generic runtime factories;
- arbitrary runtime options maps;
- a public retained-storage schema;
- database-backed configuration;
- routing changes;
- model-aware routing;
- runtime-aware routing;
- browser editing of multi-binding composition;
- multi-binding status semantics;
- health aggregation;
- migration of RFC-0128 Image Generation into retained generic bindings.

## One Retained Local Runtime-Composition Owner

The retained local domain continues to own exactly one local runtime composition.

Its semantic shape becomes:

```text
retained local runtime composition
    =
one complete alternative

either:

    singular textual runtime composition

or:

    multi-binding runtime composition
```

The two forms are not layers.

They do not merge.

They do not partially override one another.

They do not coexist as two independently authoritative retained runtime-composition sources.

A successful retained mutation selecting one complete form replaces the previously retained local runtime composition.

Other retained local HAC policy facts remain independently owned under their accepted semantics.

In particular:

```text
local_capabilities
```

remains RFC-0059 caller-local routing permission.

It is not execution ownership and must not be derived from, merged with, or rewritten from the retained binding collection.

Likewise:

```text
execution_limit
```

remains RFC-0106 HAC execution policy rather than runtime or binding capacity.

## Retained Multi-Binding Semantics

A retained multi-binding composition represents one complete collection of explicit RFC-0108 local capability bindings.

Each binding contains:

```text
explicit capability ownership
+
one accepted concrete runtime
+
that runtime's accepted construction facts
```

The retained semantics reuse the RFC-0110 rules:

- the collection is finite and non-empty;
- every binding owns a non-empty explicit capability set;
- capability names are from the accepted vocabulary for this retained form;
- capability values do not duplicate within a binding;
- capability ownership is pairwise-disjoint across bindings;
- one binding constructs exactly one concrete adapter instance;
- binding ownership must be a subset of the adapter's positive capability support;
- RFC-0119 execution-contract coherence remains required;
- declaration order has no adapter-selection priority meaning;
- adapter name is not adapter-instance identity.

The retained composition stores no routing priority, scheduler state, health state, observed model state, or runtime availability.

## Initial Capability Boundary

For this first retained multi-binding stage, `image-generation` is not an accepted capability within the retained binding collection.

The retained multi-binding capability domain is therefore restricted to the existing non-Image-Generation local binding capabilities accepted for this purpose, including:

```text
chat
summarize
classify
code
```

This restriction is intentional.

RFC-0128 already defines a separate retained local Image Generation companion:

```text
stable-diffusion.cpp
    -> image-generation
```

Permitting retained RFC-0110 bindings to own `image-generation` simultaneously would create two retained semantic owners for the same local execution capability.

This RFC does not introduce that ambiguity.

Therefore:

```text
retained multi-binding local composition
    -> chat / summarize / classify / code

RFC-0128 retained companion
    -> image-generation
```

remain separate and non-overlapping.

A future RFC may evaluate whether the RFC-0128 companion should be migrated or normalized into a unified retained binding representation.

That migration is not required to solve the current operator problem.

## Runtime-Specific Binding Facts

A retained binding may contain only construction facts already accepted for its runtime by RFC-0110 and subsequent accepted extensions.

No new runtime configuration vocabulary is introduced here.

Current relevant closed cases include:

```text
ollama
llama-server
vllm
ollaya
```

within the non-Image-Generation retained multi-binding domain accepted by this RFC.

Each retains its existing runtime-specific meanings.

For example, Ollaya remains:

```text
capabilities
runtime = "ollaya"
base_url
model
```

with current valid positive ownership restricted by the adapter to:

```text
classify
```

The retained representation does not make similarly named fields generic.

A `model` field may retain different runtime-specific meanings where already accepted.

`base_url` remains subject to the accepted runtime-specific local HTTP boundaries.

`temperature` and `disable_thinking` remain valid only where already accepted.

No runtime-specific field becomes valid merely because it appears in another runtime's binding shape.

## Retained Semantic Facts, Not Source Documents

The retained state must contain the validated semantic facts necessary to reconstruct the composition.

It must not retain the runtime-config source document as future authority.

In particular, retained state does not semantically contain:

```text
runtime_config_path
original TOML text
source document ownership
source document mtime
source document hash as configuration authority
```

After a successful retained mutation from a supplied document:

```text
the document was input to the mutation
```

not:

```text
the document remains the retained source of truth
```

Future ordinary startup does not require that source document to exist.

Editing or deleting the original file after successful mutation does not change retained HAC behavior.

## Mutation Model

The retained local domain preserves RFC-0094's complete replacement model.

This RFC does not add incremental commands such as:

```text
add-binding
remove-binding
edit-binding
move-binding
enable-binding
disable-binding
```

No binding ID is required.

The smallest accepted mutation is one complete replacement operation using an explicitly supplied RFC-0110-style runtime-config document as input.

Conceptually:

```text
operator selects document
        ↓
HAC parses document
        ↓
HAC validates complete multi-binding composition
        ↓
HAC converts it to retained semantic facts
        ↓
retained local runtime-composition alternative is replaced
```

The exact CLI spelling is an implementation-level projection of this accepted semantic operation.

A spelling compatible with the existing owner may be conceptually equivalent to:

```text
hac config local --runtime-config PATH
```

provided it unambiguously means:

> validate this complete composition now and retain the resulting semantic facts.

The command must not retain the path as future authority.

## Validation Before Retained Mutation

A multi-binding document supplied for retained mutation must satisfy its complete accepted semantics before retained state changes.

Failure must leave the previous retained state unchanged.

Validation includes at minimum:

- valid RFC-0110 document shape;
- non-empty binding collection;
- closed runtime vocabulary;
- closed runtime-specific keys;
- required runtime-specific fields;
- non-empty capability ownership;
- accepted retained capability names;
- no duplicate capability values;
- pairwise-disjoint ownership;
- adapter capability subset validity;
- RFC-0119 execution-contract coherence;
- valid runtime-specific local URLs;
- valid non-blank runtime-specific string facts;
- this RFC's rejection of retained `image-generation` bindings.

No runtime network contact is required for mutation.

Validation does not prove runtime health, model presence, runtime availability, or inference quality.

## Legacy Singular Retained Composition

Existing retained singular textual runtime composition remains valid and unchanged.

This RFC requires no migration of existing retained configuration.

An operator who has retained one accepted singular textual runtime retains exactly the existing behavior.

The singular and multi-binding forms are complete alternatives.

Retaining a multi-binding composition replaces the singular runtime-composition alternative.

Retaining a singular runtime composition replaces the multi-binding alternative.

No field-level merge occurs between them.

## Invocation-Time Explicit Runtime Configuration

Existing explicit:

```text
--runtime-config PATH
```

remains self-contained and invocation-local.

When explicitly selected for an invocation, it replaces the retained runtime-composition baseline for that invocation under the existing RFC-0094/RFC-0110 boundary.

It does not mutate retained state.

It does not merge with retained bindings.

It does not inherit missing binding facts from retained configuration.

It does not rewrite the retained multi-binding composition.

The explicitly selected file remains authoritative only for that invocation.

## Legacy Runtime CLI Interaction

Legacy runtime-composition CLI flags must not become a field-patching language for retained multi-binding state.

For a retained singular textual composition, existing compatible field override semantics remain unchanged.

For a retained multi-binding composition, options such as:

```text
--ollama-model
--temperature
--ollama-disable-thinking
```

must not implicitly locate and mutate or patch one binding inside the retained collection.

That would require an unresolved binding-selection rule and create hidden precedence semantics.

An explicit invocation that selects a complete singular runtime composition may replace the retained multi-binding runtime-composition baseline for that invocation, using the existing accepted singular runtime validation rules.

The exact argument compatibility matrix should preserve the existing principle:

```text
one explicit complete invocation-time runtime composition
replaces
one retained complete runtime composition
```

rather than merging arbitrary fields into retained bindings.

## Ordinary Startup

When a retained multi-binding composition exists and no explicit invocation-time runtime-composition source replaces it, ordinary:

```text
hac local
```

constructs the retained binding collection.

Each retained binding reconstructs its exact concrete adapter using the retained accepted construction facts.

The resulting local process continues to present one cluster-visible local node.

The union of the binding capability sets is local execution ownership under RFC-0108.

No binding creates a node.

No runtime or model identity becomes routing input.

## Static-Cluster Interaction

Where retained local runtime composition is consumed by ordinary `static-cluster`, the existing separation remains authoritative:

```text
retained/local RFC-0108 binding union
    =
physical local execution ownership

retained RFC-0059 local_capabilities
    =
caller-local routing permission
```

Neither is inferred from the other.

A retained Ollaya `classify` binding does not automatically add `classify` to caller-local routing permission.

Conversely, caller-local `classify` permission does not create an Ollaya binding.

Remote declarations remain capability-only.

No remote runtime or model fact is retained or transmitted.

## RFC-0128 Image Generation Companion

The existing retained Image Generation companion remains separately owned under RFC-0128.

It may continue to compose with either retained local runtime-composition alternative where current ordinary local composition rules already permit that companion.

For example:

```text
retained local multi-binding composition:
    chat / summarize / code -> Ollama
    classify               -> Ollaya

retained RFC-0128 companion:
    image-generation       -> stable-diffusion.cpp
```

is conceptually valid because the retained domains do not overlap.

This RFC does not normalize the companion into the multi-binding collection.

It does not duplicate its facts.

It does not permit a second retained `image-generation` owner.

## `config show`

`hac config show` must truthfully report the retained local runtime composition.

When the singular form is retained, existing behavior remains unchanged.

When the multi-binding form is retained, `config show` must make the retained capability ownership and the necessary retained runtime-construction facts visible enough for the operator to understand the retained baseline.

It must report retained facts only.

It must not imply:

- runtime availability;
- adapter health;
- model presence;
- currently loaded model identity;
- successful inference;
- active bindings in a currently running process;
- current routing eligibility.

Exact presentation wording is an implementation concern, provided the distinction between retained configuration and observed runtime truth remains clear.

## Browser Configuration Boundary

RFC-0112 and RFC-0132 define a bounded loopback browser facade for retained configuration.

Browser editing of retained multi-binding composition is not accepted by this RFC.

However, browser mutation must remain truthful.

If the browser's complete local-domain mutation shape cannot represent the currently retained multi-binding composition, it must not:

- silently delete it;
- convert it to singular configuration;
- preserve an unknown subset while replacing other parts;
- partially merge browser input into it.

Existing RFC-0132 fail-closed semantics therefore remain required.

A browser mutation that would replace a local domain containing unrepresented retained multi-binding state must fail locally until a later RFC explicitly accepts browser editing for that shape.

Browser read-only presentation may continue only where current authorization can truthfully represent retained facts.

This RFC does not require a multi-binding browser editor.

## Private Retained Storage

The physical retained storage representation remains internal.

This RFC accepts semantic retained facts, not public JSON field names.

Implementation may evolve the private representation as necessary while preserving:

- existing retained-state compatibility;
- atomic or otherwise safe mutation semantics already required by retained configuration;
- truthful decoding;
- fail-closed handling of unsupported or invalid retained state.

No public storage schema, migration API, or user-editable retained file is created.

## Privacy and Security

Retained multi-binding state contains only already accepted local runtime-construction facts needed to reproduce the composition.

This RFC adds no credentials, secrets, cloud configuration, network discovery, or remote machine administration.

Loopback runtime endpoints retain their existing validation.

No runtime is contacted merely because configuration is retained or shown.

No prompt, request content, response content, model inventory, or health information is retained by this decision.

## Compatibility

Existing retained singular local runtime compositions remain valid and unchanged.

Existing retained caller-local routing capabilities remain unchanged.

Existing retained HAC execution limits remain unchanged.

Existing RFC-0128 retained Image Generation companion configuration remains valid and separately owned.

Existing retained remote topology remains unchanged.

Existing retained External Information and Chat configuration domains remain unchanged.

Existing explicit runtime-config files remain valid.

Existing invocation-time `--runtime-config` behavior remains self-contained.

Existing singular runtime CLI behavior remains unchanged except that it must not be interpreted as a patch language for retained multi-binding state.

No existing retained configuration requires operator migration merely because this RFC is accepted.

## Rationale

The original retained runtime-composition model solved a demonstrated operator need:

```text
configure once
    ->
ordinary later invocation
```

RFC-0110 deliberately left retained multi-binding out because the architecture had not yet demonstrated enough need.

RFC-0128 introduced one specialized retained Image Generation companion rather than generalizing prematurely.

That was the smallest decision at the time.

The situation has now changed.

HAC has a second independently justified specialized composition:

```text
classify -> Ollaya
```

combined with general textual execution on another adapter.

The useful composition is no longer naturally described by:

```text
one textual runtime
+
one exceptional image companion
```

Yet inventing another retained `classify` companion would repeat specialization by capability and create unnecessary configuration domains.

RFC-0108 and RFC-0110 already provide the correct capability-centered composition model.

The smallest next step is therefore to allow the existing retained local runtime-composition owner to retain that accepted model directly.

This remains narrower than redesigning all retained configuration around generic bindings.

Image Generation is deliberately left under RFC-0128 until migration itself becomes justified.

## Alternatives Considered

### Keep `--runtime-config PATH` as the permanent ordinary mechanism

Rejected.

The explicit file remains valuable for reproducible invocation-specific composition, but requiring the operator to remember its path on every ordinary startup does not provide the retained baseline experience already accepted by RFC-0094.

### Retain the runtime-config path

Rejected.

That would retain a pointer to externally mutable state rather than HAC-owned semantic configuration.

The retained startup behavior could change without a retained configuration mutation.

### Add a separate `config bindings` domain

Rejected.

Local runtime composition already has one retained semantic owner.

A second retained domain controlling the same composition would require precedence and merging semantics.

### Add a retained Ollaya/Classify companion

Rejected.

RFC-0128's image companion was deliberately specialized when only one such need existed.

Repeating that structure for every specialized capability would create capability-specific retained configuration silos.

The already accepted RFC-0108/RFC-0110 binding model is the more direct representation.

### Immediately migrate Image Generation into retained bindings

Rejected for this stage.

RFC-0128 remains valid and deployed architecture.

Supporting `image-generation` simultaneously in retained generic bindings would create overlapping retained ownership.

Migration or normalization should be evaluated separately.

### Add incremental binding CRUD

Rejected.

A complete RFC-0110-style document already expresses the entire composition.

RFC-0094 retained local configuration uses complete replacement semantics.

IDs and incremental mutation provide no demonstrated value for the current need.

### Apply legacy runtime flags as patches to retained bindings

Rejected.

A flag such as `--ollama-model` has no unambiguous binding target once a collection may contain multiple concrete runtime instances.

No hidden selection rule should be introduced.

### Introduce a generic runtime/provider persistence schema

Rejected.

Current runtime-specific binding shapes are closed and already accepted.

The private retained representation can preserve those facts directly without an arbitrary options map or provider abstraction.

## Trade-offs

Retained multi-binding configuration introduces another valid shape within the retained local domain.

This increases retained-state validation and presentation complexity.

Operators cannot initially edit this shape through the browser Configuration facade.

They must use the accepted CLI mutation input until browser editing independently earns justification.

Image Generation remains represented separately under RFC-0128, so the retained architecture is not yet fully normalized around bindings.

That temporary asymmetry is intentional.

It avoids migrating a working retained domain merely for conceptual symmetry.

Legacy per-runtime CLI override convenience is reduced when the retained baseline is multi-binding: those options cannot safely patch a binding collection without additional selection semantics.

Operators can instead select a complete explicit runtime composition for one invocation.

These limits preserve explicit ownership and avoid precedence ladders.

## Implementation Boundary

If accepted, implementation is authorized only to:

- extend retained local runtime composition with one multi-binding alternative;
- retain validated semantic RFC-0110-style binding facts rather than a source path;
- restrict retained multi-binding capabilities initially so `image-generation` remains RFC-0128-owned;
- add one complete retained mutation path using an explicitly supplied RFC-0110-style document as input;
- reconstruct retained bindings during ordinary applicable startup;
- preserve existing singular retained runtime composition;
- preserve RFC-0059 retained local routing permission separately;
- preserve RFC-0106 retained execution-limit semantics separately;
- preserve RFC-0128 Image Generation companion separately;
- make `config show` truthfully represent retained multi-binding facts;
- preserve or strengthen browser fail-closed behavior when the browser cannot represent the retained local shape;
- add focused compatibility, validation, startup, configuration, and browser-boundary tests;
- update accurate operator documentation.

Implementation must not:

- retain the source path as configuration authority;
- introduce incremental binding CRUD;
- migrate Image Generation;
- add browser multi-binding editing;
- add runtime discovery;
- add lifecycle management;
- add status/health aggregation;
- alter routing;
- expose remote runtime facts;
- publish the retained storage schema;
- introduce a generic runtime factory or provider abstraction.

## Proof Expectations

A later implementation must prove at minimum:

1. existing retained singular textual runtime configuration remains valid;
2. existing retained RFC-0059 local capability permission remains independent;
3. existing retained HAC execution-limit state remains independent;
4. existing RFC-0128 retained Image Generation companion remains valid;
5. a valid RFC-0110-style non-image multi-binding document can be supplied as retained mutation input;
6. successful mutation retains semantic composition rather than the source path;
7. deleting or modifying the original source document after mutation does not alter later retained startup;
8. ordinary later `hac local` reconstructs the retained binding collection without `--runtime-config`;
9. an Ollama + Ollaya retained composition reconstructs exact capability ownership and runtime construction facts;
10. invalid binding documents fail without mutating previous retained state;
11. overlapping capability ownership is rejected;
12. unsupported runtime-specific fields are rejected;
13. retained `image-generation` binding ownership is rejected;
14. explicit `--runtime-config PATH` continues to replace retained runtime composition for one invocation without mutation;
15. retained multi-binding does not merge with explicitly selected runtime-config;
16. legacy singular runtime CLI flags do not patch individual retained bindings;
17. complete explicit singular runtime replacement remains possible under existing invocation semantics;
18. `config show` truthfully represents retained multi-binding facts without runtime observation;
19. browser local mutation fails closed when retained multi-binding state cannot be represented;
20. browser mutation does not silently remove or convert retained multi-binding state;
21. remote retained topology remains unchanged;
22. no runtime is contacted during retained mutation or `config show`;
23. the retained physical format remains private;
24. existing retained configurations require no migration for continued use.

A real-machine inference proof is not required for this RFC.

RFC-0140 and RFC-0141 already prove Ollaya execution and serialized binding construction.

The proof required here is retained semantic persistence and faithful later reconstruction.

## Open Questions

This RFC intentionally leaves the following for later evidence:

- whether browser Configuration should edit retained multi-binding compositions;
- whether RFC-0128 Image Generation should eventually migrate into the binding model;
- whether retained multi-binding composition should eventually replace singular retained representation internally;
- whether additional specialized capabilities justify broader retained binding coverage;
- whether any future observation surface should present configured binding facts separately from running adapter facts.

None of these is required to solve the current operator problem.

## Decision

Accepted. HAC retained local runtime composition gains one additional complete alternative:

```text
multi-binding local runtime composition
```

using existing RFC-0108/RFC-0110 semantics.

The retained local runtime-composition domain remains singular in authority:

```text
one complete singular textual composition

OR

one complete multi-binding composition
```

never both as merged layers.

The retained state owns validated semantic binding facts rather than a runtime-config path.

A supplied RFC-0110-style document may serve as complete mutation input, after which the source document has no continuing authority.

For this first retained multi-binding stage, `image-generation` remains excluded from the retained binding collection and stays under RFC-0128's existing companion authority.

Browser editing of bindings remains deferred, with RFC-0132 fail-closed mutation behavior preserved.

Explicit `--runtime-config PATH` remains a self-contained invocation-time replacement.

Legacy runtime flags do not become binding patch operations.

No routing, remote protocol, runtime discovery, lifecycle, observation, public storage schema, or generic provider architecture is added.
