# RFC-0143: File-Free Incremental Retained Configuration

Status: Proposed

Date: 2026-09-26

Author: frian

## Summary

Home AI Cluster should allow an operator to construct and maintain its ordinary retained local and static-cluster configuration entirely through `hac config`, without requiring an external runtime-config document.

This RFC adds bounded incremental mutation over configuration domains that HAC already owns.

Conceptually:

```text
hac config
    |
    +-- local runtime bindings
    |      add
    |      replace
    |      remove
    |
    +-- caller-local routing capability set
    |      add
    |      remove
    |      clear
    |
    +-- existing execution-limit configuration
    |
    +-- existing Image Generation companion configuration
    |
    +-- remote node declarations
           add/replace
           remove
           capability add
           capability remove
```

Local bindings do not gain persistent IDs.

A capability currently owned by a binding is sufficient to identify that binding because RFC-0108 requires pairwise-disjoint local capability ownership.

The capability is only a lookup key. It does not become persistent identity.

Mutation operates on complete bindings:

```text
add complete binding

replace complete binding owning CAPABILITY

remove complete binding owning CAPABILITY
```

This RFC does not introduce generic configuration CRUD, arbitrary field editing, runtime identities, binding IDs, browser binding editing, runtime discovery, lifecycle management, or a public retained-storage schema.

A guided interactive CLI mode may collect the same complete mutation facts when standard input is an interactive terminal.

Interactive operation does not create a second configuration model or authority.

## Context

RFC-0094 established HAC-managed retained configuration so an operator could configure ordinary runtime and topology facts once and reuse them through later ordinary invocations.

RFC-0108 established explicit local capability ownership through pairwise-disjoint bindings:

```text
capability set
    ->
one concrete local adapter instance
```

RFC-0110 introduced an explicit multi-binding runtime-config document.

RFC-0128 added a separately retained stable-diffusion.cpp Image Generation companion.

RFC-0140 and RFC-0141 added the classification-only Ollaya adapter and allowed it in RFC-0110 multi-binding composition.

RFC-0142 then allowed one complete RFC-0110-style multi-binding composition to become HAC-managed retained local runtime state.

An operator can therefore currently perform:

```text
hac config local --runtime-config PATH
```

and later:

```text
hac local
```

without the source document remaining authoritative.

RFC-0142 solves retained persistence.

However, creation of a retained multi-binding composition still requires an external RFC-0110 document as mutation input.

HAC can now validate, retain, show, reconstruct, and consume that state, but cannot directly build and maintain the same state through its normal configuration CLI.

This RFC closes that operator gap.

## Problem

An ordinary useful HAC configuration may include:

```text
local execution ownership:
    chat, summarize, code -> Ollama
    classify              -> Ollaya

caller-local routing permission:
    chat
    summarize
    classify
    code

execution limit:
    2

Image Generation companion:
    image-generation -> stable-diffusion.cpp

remote topology:
    receiver
        base URL: ...
        capabilities:
            summarize
```

HAC already owns all of these retained semantic facts.

Yet from a clean installation, constructing the local multi-binding portion still requires manually authoring an RFC-0110 document before giving it to `hac config local --runtime-config PATH`.

The source document is no longer retained authority after RFC-0142, but it remains a required intermediate representation for ordinary configuration.

That is inconsistent with the HAC-managed retained configuration experience established by RFC-0094.

The operator should be able to construct the same accepted semantic state directly.

## Goals

This RFC aims to:

- make ordinary retained HAC configuration possible without external files;
- preserve all existing semantic owners;
- add bounded incremental mutation to retained local bindings;
- avoid persistent binding IDs;
- use current capability ownership as the natural lookup mechanism for existing bindings;
- mutate bindings only as complete validated objects;
- add bounded caller-local routing capability set mutations;
- add bounded remote-node capability set mutations;
- preserve remote node ID as remote identity;
- preserve existing Image Generation retained ownership;
- preserve existing execution-limit configuration;
- preserve `config show` as retained-state inspection;
- preserve `--runtime-config PATH` as complete batch replacement;
- allow a guided interactive CLI projection over the same mutations;
- keep every mutation fully validated before retained state changes.

## Non-goals

This RFC does not add:

- runtime discovery;
- model discovery;
- runtime health;
- model health;
- lifecycle management;
- installation;
- model pulling;
- scheduler policy;
- routing changes;
- dynamic node discovery;
- remote runtime metadata;
- remote model metadata;
- configuration synchronization;
- profiles;
- inheritance;
- environment configuration selection;
- reload or file watching;
- database persistence;
- generic resource CRUD;
- generic key/value mutation;
- generic runtime configuration;
- generic provider configuration;
- arbitrary options maps;
- persistent binding IDs;
- runtime IDs;
- runtime-name-based binding identity;
- binding priorities;
- binding capability-level structural CRUD;
- automatic browser support for bindings;
- Image Generation migration into generic bindings;
- a public retained-storage schema.

## Existing Semantic Owners Remain Authoritative

This RFC does not merge existing configuration domains.

The owners remain:

```text
local runtime composition
    -> RFC-0094 / RFC-0142

local execution ownership
    -> RFC-0108 bindings

caller-local routing permission
    -> RFC-0059 local_capabilities

execution limit
    -> RFC-0106

Image Generation companion
    -> RFC-0128

remote node identity/topology
    -> RFC-0094 retained node declarations

remote allowed capabilities
    -> explicit property of each retained remote-node declaration
```

Incremental mutation changes how the operator modifies those facts. It does not transfer their ownership.

In particular:

```text
local binding ownership
!=
caller-local routing permission
```

Adding `classify -> Ollaya` must not implicitly authorize caller-local routing of `classify`.

Likewise, adding caller-local `classify` permission must not construct an Ollaya binding.

## Binding Model

A retained local binding continues to mean:

```text
explicit non-empty capability set
+
one accepted concrete runtime
+
that runtime's accepted construction facts
```

Bindings remain pairwise-disjoint in capability ownership.

Runtime name is not binding identity.

Multiple bindings may use the same runtime type where existing architecture permits it.

For example:

```text
chat      -> Ollama model A
summarize -> Ollama model B
classify  -> Ollaya
```

Therefore `runtime = ollama` cannot safely identify one binding.

## Binding Lookup by Owned Capability

A retained binding does not gain a persistent ID.

To identify an existing binding for replacement or removal, the operator provides one capability currently owned by that binding.

Conceptually:

```text
replace binding owning classify

remove binding owning summarize
```

Because RFC-0108 requires pairwise-disjoint ownership, one capability identifies at most one retained binding.

If the capability is not currently owned, the mutation fails.

The supplied capability is a lookup key only.

It is not stored as a binding ID and does not become privileged relative to the other capabilities owned by the binding.

For example:

```text
chat, summarize, code -> Ollama
```

may be looked up through any of:

```text
chat
summarize
code
```

and all identify the same binding.

## Complete Binding Mutation

Incremental configuration does not introduce field-level or capability-level structural editing inside a binding.

The accepted primitives are:

```text
add complete binding

replace complete binding owning CAPABILITY

remove complete binding owning CAPABILITY
```

### Add

Adding a binding supplies its complete semantic shape:

```text
capabilities
runtime
runtime-specific construction facts
```

The resulting entire multi-binding composition is validated before mutation.

Addition fails if ownership overlaps any existing binding.

### Replace

Replacing a binding first resolves exactly one current binding through an owned capability.

The operator then supplies the complete replacement binding.

The old binding is removed conceptually, the replacement is inserted, and the resulting complete composition is validated before mutation.

Replacement may change capability ownership, runtime type, model, base URL, or other currently accepted runtime-specific construction facts.

Replacement does not patch arbitrary fields into a binding.

### Remove

Removing a binding resolves exactly one current binding through an owned capability and removes that complete binding.

Removal is not equivalent to removing only the lookup capability.

If the resulting retained multi-binding collection would violate existing non-empty composition requirements, the mutation fails.

Clearing or replacing the entire runtime-composition domain remains an explicit operation under existing retained configuration semantics.

## No Binding Capability CRUD

This RFC does not introduce:

```text
binding capability add
binding capability remove
```

as separate structural primitives.

For example, changing:

```text
chat, summarize, code -> Ollama
```

into:

```text
chat, code -> Ollama
```

is expressed by replacing the complete binding.

This avoids hidden rules such as:

```text
remove final capability
    ->
silently delete binding
```

and avoids implicit splitting or merging of bindings.

The architecture remains:

> capability finds the binding; replacement defines the binding.

## Runtime-Specific Closed Facts

Binding creation and replacement reuse the existing accepted closed runtime-specific configuration shapes.

No generic `set FIELD VALUE` mechanism is introduced.

For example, Ollaya remains represented through its accepted facts:

```text
runtime = ollaya
capabilities = ...
base_url = ...
model = ...
```

An operator changing only the model may conceptually ask to replace the binding while the CLI pre-populates or explicitly reuses the current remaining binding facts.

The committed mutation remains a complete validated binding replacement.

Interactive convenience must not turn this into generic partial-field persistence semantics.

## Transition from Singular Retained Composition

RFC-0142 defines singular textual composition and multi-binding composition as complete alternatives.

That remains true.

Incremental local binding mutation is valid only when the retained local runtime-composition alternative is already multi-binding, or when no retained local runtime composition exists yet and the first complete binding creates one.

If a retained singular runtime composition currently exists, any incremental local binding add, replace, or remove operation must fail closed.

HAC must not automatically convert the singular runtime composition into a multi-binding composition.

The operator must first explicitly replace or reset the retained singular runtime composition through an existing complete runtime-composition mutation, after which incremental binding mutation may proceed against the resulting multi-binding state.

This rule exists because the historical singular runtime composition does not itself contain explicit RFC-0108 capability ownership. HAC therefore has no accepted authority from which to infer the capability set of a synthetic binding.

This RFC does not authorize hidden inference of capability ownership from runtime type, routing permission, adapter support, or default capabilities.

## Incremental Mutation from Clean State

No retained local configuration is required before the first local binding is added.

A first complete binding may create the retained multi-binding runtime-composition alternative while leaving independent facts unset:

```text
local_capabilities = None
execution_limit = None
```

No caller-local routing permission is inferred.

No execution limit is invented.

## Caller-Local Routing Capability Mutation

RFC-0059 caller-local routing capabilities remain a separate retained set.

This RFC accepts bounded set mutation:

```text
add capability
remove capability
clear explicit retained set
```

The distinction between `local_capabilities = None` and an explicit capability set remains preserved.

`None` means no explicit retained set and therefore retains existing default semantics.

It is not an empty set.

The first `add` when the retained value is `None` creates a new explicit set containing the added capability.

Removing one capability from an explicit set produces the remaining explicit non-empty set.

Removing the last capability is rejected.

Returning to `None` requires an explicit clear/reset operation.

No capability mutation changes local execution bindings.

## Execution Limit

Execution-limit configuration remains under existing RFC-0106 semantics.

No new architecture is required.

The file-free configuration experience may continue to use the existing retained `config local` execution-limit mutation surface or an equivalent bounded CLI projection.

Execution limit remains independent from bindings and routing capability permission.

## Image Generation

RFC-0128 remains unchanged.

The file-free workflow uses the existing retained Image Generation configuration domain.

Conceptually:

```text
hac config image-generation ...
```

continues to configure:

```text
image-generation
    -> stable-diffusion.cpp
```

This RFC does not migrate Image Generation into local bindings, duplicate its retained facts, allow generic retained bindings to own `image-generation`, or change RFC-0128 ownership.

## Remote Nodes

Remote node identity remains the retained `node_id`.

No new remote identifier is introduced.

Existing complete node add/replace and node removal semantics remain valid.

This RFC additionally accepts bounded mutation of a remote node's explicit capability set.

Conceptually:

```text
remote capability add NODE CAPABILITY

remote capability remove NODE CAPABILITY
```

The node is located by its existing node ID.

The capability set remains explicit and non-empty.

Adding an already present capability may either be idempotent or fail according to existing CLI mutation conventions, but must not duplicate the fact.

Removing an absent capability must fail clearly or be explicitly defined as idempotent by implementation convention.

Removing the final capability must not silently remove the node.

The mutation fails instead.

Removing the node remains an explicit node-removal operation.

Remote capability mutation does not add runtime or model facts.

## Existing Remote Node Replacement

This RFC does not require introducing a new semantic `node update` operation.

Existing retained node mutation already uses node ID as identity and complete declaration replacement.

Implementation may preserve existing command spelling where it already expresses this operation truthfully.

CLI symmetry alone is not sufficient reason to rename or duplicate an existing semantic operation.

## Complete Batch Replacement Remains

Existing:

```text
hac config local --runtime-config PATH
```

remains accepted.

It continues to mean:

```text
validate complete RFC-0110-style composition
        ↓
replace retained local runtime-composition alternative
```

It is a batch mutation surface.

Incremental CLI operations mutate the same retained semantic facts.

There is no dual authority.

After either form of successful mutation, retained semantic state remains authoritative.

The external file is never required for future ordinary startup.

## `config show`

`hac config show` remains the retained-state inspection surface.

Incremental configuration does not require health or observation architecture.

`config show` must continue to show only retained facts.

It must not imply runtime availability, runtime health, model presence, current execution state, remote node reachability, or routing success.

Its existing ability to expose retained binding composition, local routing capabilities, Image Generation configuration, and remote declarations is sufficient for this RFC.

## Guided Interactive Configuration

For commands requiring multiple related facts, HAC may provide a guided interactive mode.

Interactive mode is a user-interface projection over the same accepted semantic mutation.

It is not a second mutation model.

For example, conceptually:

```text
hac config local binding add
```

when invoked from an interactive terminal with no binding facts supplied may guide the operator through runtime, capabilities, runtime-specific construction facts, and final confirmation.

The resulting operation is exactly equivalent to supplying the complete accepted command arguments non-interactively.

Similarly, replacement may display or pre-populate the currently retained binding and collect a complete replacement.

### Interaction rules

The CLI follows these principles:

```text
complete explicit arguments
    -> execute non-interactively

command intentionally invoked without mutation facts
and interactive terminal available
    -> guided interaction may begin

non-interactive input
    -> never prompt unexpectedly

ambiguous or conflicting partial arguments
    -> fail clearly rather than guess
```

Interactive input must not change validation, relax required semantic facts, contact runtimes for discovery, infer models from runtime state, infer ownership, introduce additional retained fields, or mutate before final validation.

A simple terminal prompt implementation is sufficient.

No TUI framework is architecturally required.

## Validation Before Mutation

Every mutation is validated before retained state changes.

For local binding mutation, validation includes the resulting complete binding collection.

Existing rules remain authoritative, including:

- non-empty capability ownership;
- pairwise-disjoint ownership;
- accepted capability names;
- runtime capability support;
- closed runtime vocabulary;
- closed runtime-specific fields;
- required runtime-specific fields;
- valid loopback/local URLs where required;
- RFC-0119 execution-contract coherence;
- RFC-0142 exclusion of retained `image-generation`.

For local routing permission mutation, the resulting explicit set must satisfy existing RFC-0059 validation.

For remote node capability mutation, the resulting set must satisfy existing remote capability validation and remain non-empty.

Validation failure leaves previous retained state unchanged.

No runtime or remote node contact is required for mutation.

## Atomicity Boundary

Each individual `hac config` mutation is one validated retained-state change.

This RFC does not introduce multi-command transactions.

Moving one capability from one binding to another may therefore temporarily leave that capability unowned.

For example:

```text
replace old binding without summarize
add new summarize binding
```

is acceptable.

The reverse order would temporarily violate pairwise-disjoint ownership and must fail.

The operator remains responsible for mutation ordering across separate commands.

No transactional batch editor is justified by current evidence.

## Browser Configuration Boundary

This RFC grants no new browser mutation authority.

Existing browser behavior remains governed by RFC-0112 and RFC-0132.

Browser multi-binding editing remains deferred.

Existing fail-closed behavior for retained local shapes the browser cannot represent must remain intact.

CLI mutation does not imply browser parity.

## Private Retained Storage

The retained physical representation remains private.

Incremental commands operate through semantic retained configuration APIs.

They do not expose JSON field manipulation to the operator.

This RFC does not create generic retained-storage editing mechanisms such as `config set PATH VALUE`, `config get PATH`, or `config patch JSON`.

## Privacy and Security

All new mutation operations concern already accepted retained local or static topology facts.

They add no runtime observation, remote discovery, credentials, or prompt/response persistence.

Interactive mode must not contact runtimes merely to populate choices.

Supported runtimes, capabilities, and accepted field shapes come from HAC's existing accepted configuration vocabulary.

## Compatibility

Existing retained configurations remain valid.

Existing singular retained runtime composition remains valid.

Existing multi-binding retained composition remains valid.

Existing RFC-0128 Image Generation configuration remains valid.

Existing retained node declarations remain valid.

Existing `config local --runtime-config PATH` remains valid.

Existing ordinary startup behavior remains unchanged.

Existing browser Configuration authority remains unchanged.

Existing private retained-state representation remains non-public.

No migration is required merely because incremental mutation is accepted.

## Operator Experience

A clean-install workflow can now be expressed entirely through HAC.

Conceptually:

```text
add local binding:
    chat, summarize, code -> Ollama
    model = llama3.2

add local binding:
    classify -> Ollaya
    base_url = http://127.0.0.1:11435
    model = laya

add caller-local routing permission:
    chat
    summarize
    classify
    code

optionally set execution limit:
    2

optionally configure Image Generation companion:
    stable-diffusion.cpp
    base_url = ...

add remote node:
    receiver
    base_url = ...
    capabilities = summarize

optionally add remote capability:
    classify

inspect:
    hac config show

run:
    hac local
```

No TOML document is required.

A batch RFC-0110 document remains available when complete declarative replacement is preferable.

## Rationale

HAC already owns the semantic configuration facts involved here.

The missing capability is not a new configuration model.

It is direct operator mutation of the existing model.

The design remains small because it avoids introducing identities and abstractions that the current architecture does not need.

Pairwise-disjoint capability ownership provides an existing natural lookup mechanism for local bindings.

Remote node ID already provides identity for remote declarations.

Routing permissions and remote capability declarations are already explicit sets, making bounded set mutation natural.

Image Generation already has its own retained owner.

`config show` already provides retained inspection.

The result is a file-free workflow built entirely from existing semantic owners.

## Alternatives Considered

### Keep RFC-0142 file import as the only multi-binding mutation

Rejected.

It preserves architecture correctly but leaves ordinary HAC-managed configuration dependent on manual intermediate document authoring.

### Add repeated complete `--binding` arguments only

Not sufficient as the sole operator interface.

It could provide a useful complete batch CLI representation but would require re-declaring the entire composition for routine maintenance.

### Add persistent binding IDs

Rejected.

No demonstrated ambiguity requires them.

Capability ownership uniquely identifies current bindings.

### Identify bindings by runtime name

Rejected.

Multiple bindings may use the same runtime type.

Runtime is construction information, not identity.

### Add/remove individual capabilities inside bindings

Rejected for this stage.

Complete binding replacement expresses ownership changes without special split/merge/last-capability rules.

### Add runtime CRUD

Rejected.

A runtime without capability ownership is not an independent object in RFC-0108 local composition.

### Add generic field setters

Rejected.

Runtime-specific accepted configuration remains closed.

### Add generic config object CRUD

Rejected.

The required mutations operate over existing domain-specific semantic facts.

### Remove a remote node automatically when its final capability is removed

Rejected.

That would make capability mutation silently perform node-topology mutation.

Node removal remains explicit.

### Migrate Image Generation into bindings now

Rejected.

The current file-free objective does not require changing RFC-0128.

### Require interactive configuration

Rejected.

Interactive configuration is optional human-facing convenience.

Explicit non-interactive commands remain required for scripts, tests, reproducibility, and automation.

## Trade-offs

Complete binding replacement is slightly more verbose than field-level updates.

That verbosity is intentional.

It keeps binding state explicit and avoids patch semantics.

Using a capability as lookup means an operator must know one currently owned capability before replacing or removing a binding.

`config show` provides that retained information.

Moving a capability between bindings may require two commands and temporarily leave the capability unowned.

That is preferable to introducing transactions or hidden overlap resolution.

The CLI gains several domain-specific mutation operations.

This increases surface area, but each operation corresponds directly to an already accepted semantic owner rather than to a generic configuration framework.

Interactive mode adds CLI implementation complexity, but does not add architectural state or authority.

## Implementation Boundary

If accepted, implementation is authorized only to add bounded retained CLI mutation for:

- complete local binding addition;
- complete local binding replacement targeted by one currently owned capability;
- complete local binding removal targeted by one currently owned capability;
- caller-local routing capability add/remove/clear;
- remote-node capability add/remove;
- guided interactive collection of the same mutation facts where appropriate;
- documentation and tests for those operations.

Implementation may preserve and reuse:

- existing node add/replace/remove semantics;
- existing execution-limit configuration;
- existing Image Generation configuration;
- existing complete runtime-config import;
- existing retained serialization and validation helpers.

Implementation must not add binding IDs, runtime IDs, generic configuration resource APIs, generic field mutation, runtime discovery, model discovery, runtime lifecycle management, remote discovery, transactions across separate mutations, browser binding editing, Image Generation migration, or a public retained-storage schema.

## Proof Expectations

A later implementation must prove at minimum:

1. local binding add works from no retained local configuration;
2. adding a second disjoint binding preserves the first;
3. overlapping ownership is rejected without mutation;
4. complete binding replacement can be targeted by any capability currently owned by that binding;
5. replacement preserves unrelated bindings;
6. replacement can change runtime-specific construction facts;
7. replacement can change the owned capability set;
8. replacement revalidates the complete resulting composition;
9. removing a binding removes the whole binding, not only the lookup capability;
10. removing a binding preserves unrelated bindings;
11. removing the last remaining binding does not create invalid retained multi-binding state;
12. multiple instances of the same runtime type remain independently targetable through their owned capabilities;
13. no persistent binding ID is introduced;
14. local binding mutation does not modify caller-local routing permission;
15. caller-local routing capability add from `None` creates one explicit retained set;
16. caller-local routing capability add preserves existing explicit members;
17. caller-local routing capability remove preserves remaining explicit members;
18. removing the final explicit local routing capability is rejected;
19. explicit clear restores `None`;
20. local routing mutation does not alter local binding ownership;
21. execution-limit state remains independent;
22. RFC-0128 Image Generation configuration remains unchanged;
23. remote capability add targets the node by `node_id`;
24. remote capability remove preserves remaining capabilities;
25. removing the final remote capability is rejected;
26. remote capability mutation never implicitly removes the node;
27. existing remote node replacement/removal continues to work;
28. `config show` truthfully reflects all successful mutations;
29. no runtime or remote node is contacted during mutation;
30. `config local --runtime-config PATH` remains complete batch replacement;
31. incremental local binding mutation fails closed while a retained singular runtime composition exists;
32. existing retained singular configuration remains compatible;
33. existing retained multi-binding configuration remains compatible;
34. browser fail-closed behavior remains unchanged;
35. complete explicit CLI mutation works without prompts;
36. interactive mode, when used, produces the same semantic mutation as explicit arguments;
37. non-interactive invocation never unexpectedly prompts;
38. invalid or ambiguous interactive/partial input mutates nothing;
39. no external configuration file is required for a complete clean-install workflow.

## Open Questions

This RFC intentionally leaves for implementation-level CLI design:

- exact subcommand spelling;
- exact prompt wording;
- whether interactive selections use numbers, names, or both;
- whether explicit repeated `--capability` options or another simple closed syntax is clearest;
- whether duplicate set-add should be idempotent or report already-present state;
- whether removal of an absent set member should be idempotent or fail explicitly;
- exact confirmation wording for destructive mutations.

These choices must not change the accepted semantic model.

The following architectural questions remain deferred:

- browser editing of multi-binding composition;
- Image Generation migration into bindings;
- generic configuration import/export;
- transactional multi-command mutation;
- persistent binding identity beyond capability ownership.

## Decision

If accepted, HAC gains bounded file-free incremental retained configuration.

The core rules are:

```text
local binding:
    add complete binding
    replace complete binding owning CAPABILITY
    remove complete binding owning CAPABILITY

binding identity:
    no persistent ID
    capability ownership is lookup only

caller-local routing permission:
    add/remove/clear explicit retained capability set
    preserve None vs explicit non-empty semantics

remote node:
    node_id remains identity
    remote capability set may be incrementally mutated
    final capability cannot be removed implicitly

Image Generation:
    remains RFC-0128-owned

runtime-config file:
    remains optional complete batch replacement

interactive mode:
    optional guided input
    same semantic mutation
    never separate authority
```

The operator can therefore configure and maintain ordinary HAC retained state from a clean installation using `hac config` alone, without requiring any external configuration document.
