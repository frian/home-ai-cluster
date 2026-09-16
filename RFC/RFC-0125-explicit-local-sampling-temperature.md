# RFC-0125: Explicit Local Sampling Temperature

Status: Draft

Date: 2026-09-14

Author: frian

## Summary

Home AI Cluster should accept one optional finite non-negative sampling
temperature through one common local textual-runtime spelling for Ollama,
llama-server, and vLLM:

```text
--temperature VALUE
```

The shared meaning is only: request this explicit numeric value through the
selected local textual runtime's native sampling-temperature mechanism. It is
common operator control, not portable behavioral meaning. HAC promises neither
equivalent distributions, reliability, determinism, nor behavioral effects
across runtime/model-artifact compositions.

When omitted, HAC preserves the selected composition's native ordinary
free-text omission/default behavior. A retained value belongs to the currently
selected runtime-composition domain. Selecting a different runtime does not
carry the old value into that new domain.

This applies to local Chat, Summarize, and Code, including workspace-aware Code
through ordinary `capability=code` inference. It excludes Classify under
RFC-0061. It adds no request, capability, routing, transport, remote-node,
workspace-authority, model-selection, or generic-options semantics.

## Problem

The retained repeated workspace-Code experiment records valid `qwen3.5:9b`
results of ordinary/default settings: 0/4 strict PASS, and temperature=0: 5/5
strict PASS. Source model, thinking setting, ordinary 120-second timeout, HAC
contract/parser, workflow, filesystem authority, and production code were held
constant. The first invalid control attempt began while `hac local` was
stopped; it did not exercise the model and remains excluded from
model-behavior interpretation. This is bounded evidence in one local
composition, not a model recommendation or statistical result.

A later separate llama-server follow-up prevents treating that favorable Ollama
direction as engine-independent. The tested llama-server build could not load
the exact Ollama GGUF, so a compatible but different Qwen3.5-9B GGUF artifact
was used; this was not a byte-identical or runtime-only comparison.
Native/default was 3/5 strict; explicit temperature=0 was 0/5 strict; and a
later explicit temperature=1 condition was 2/5 strict. This does not establish
that llama-server caused a reversal or rank runtimes or models.

The bounded architectural lesson is only that generation temperature can
materially affect protocol behavior, and that its useful direction or value is
composition-dependent in the retained evidence. Equal numeric values have no
demonstrated portable reliability meaning across engine/model-artifact
compositions. The small problem is therefore visible, explicit operator control
and inspectable composition ownership for one fact, without making it a
cluster-facing policy.

## Goals

- Retain one explicit operator-controlled local sampling-temperature fact in
  one selected runtime-composition domain.
- Preserve native omission/default behavior when it is absent.
- Translate one narrow shared operator semantic through the existing Ollama,
  llama-server, and vLLM adapters.
- Keep local runtime composition distinct from capabilities, requests, routing,
  transport, remote ownership, and workspace authority.
- Extend the accepted closed retained-local and explicit runtime-file domains
  without creating a configuration subsystem.

## Non-goals

This RFC does not authorize `top_p`, `top_k`, `min_p`, seed, penalties, stop
tokens, max-token or context-size controls, mirostat, engine-specific modes,
arbitrary options, generic inference settings, per-capability or per-request
temperature, reliability mode, model qualification tables, automatic tuning,
temperature recommendations, runtime recommendations, default temperature,
discovery, profiles, per-runtime stored histories, multiple retained runtime
compositions, remote negotiation, transport/version changes, retries, parser
relaxation, or workspace-Code redesign. Image-generation composition is outside
this RFC.

It does not add dynamic runtime discovery, current runtime observation,
inference-options schemas, generic thinking/reasoning control, or vLLM
thinking configuration. RFC-0073's accepted Ollama-specific thinking-disable
choice remains separate: empirical usefulness of thinking changes elsewhere
does not itself establish shared semantics.

## Proposal

### Shared value and omission semantics

The accepted domain is one finite number `>= 0`. Negative values, NaN, and
positive or negative infinity fail local validation; explicit zero is valid and
distinct from absence. HAC imposes no arbitrary universal upper bound. A
runtime may still reject an otherwise HAC-valid value during ordinary execution;
HAC performs no support probe at configuration time.

`--temperature VALUE` requests that exact numeric value through the selected
runtime's native ordinary free-text temperature mechanism. Explicit zero is
forwarded as explicit zero. HAC does not promise determinism, absence of all
stochastic behavior, or equal behavioral meaning for zero across complete
runtime/model compositions. It does not normalize runtime defaults or promise
equivalent distributions or effects for any equal values across runtimes, model
artifacts, templates, tokenizers, quantizations, or sampling pipelines.

Blank/non-numeric, NaN, infinite, and negative input fails before runtime
execution. Omission preserves today's ordinary free-text request shape: HAC
sends no temperature override and does not synthesize any HAC default.

### Covered execution and Classify exclusion

An explicit value applies to ordinary free-text Chat, Summarize, and Code
through the selected local adapter. Workspace-aware Code remains ordinary,
independently routed `capability=code` inference. The motivating experiment was
workspace Code, but applying this composition fact across Chat/Summarize/Code
follows adapter-composition ownership, not a claim of demonstrated equivalent
reliability effects for every capability.

Classify remains excluded. RFC-0061 permits adapter-private prompts, grammar,
JSON mode, constrained decoding, and equivalent result shaping. Current
Classify behavior remains unchanged: Ollama and llama-server explicitly use
temperature=0, while vLLM has no explicit classification temperature. This RFC
does not create a Classify operator temperature or normalize that behavior.

### Concrete adapter translation

For covered ordinary free-text inference, omission means omission of the native
field exactly as today. An explicit value translates to Ollama's native
request-level temperature mechanism, or to the native chat-completion
`temperature` field for llama-server and vLLM. This is one common operator
control, not a shared adapter-options or sampling-policy object. It does not
generalize to hypothetical engines or promise portable stochastic behavior.

### Runtime-scoped composition and retained configuration

Sampling temperature is one local textual runtime-composition fact:

```text
operator -> selected local HAC runtime composition -> concrete adapter -> native request
```

The common spelling and operator concept do not imply cross-runtime retained
value carryover. This restores and preserves RFC-0094 runtime-domain
replacement; it is not an exception to it.

Within one retained runtime domain, a retained value is an ordinary baseline.
For example, retained `runtime = ollama` and `temperature = X` may supply `X`
to an ordinary invocation in that same domain. An explicitly supplied
compatible `--temperature Y` temporarily overrides `X` for that invocation
without mutating retained state, under RFC-0094 suppliedness semantics.

An invocation explicitly selecting a different runtime replaces the effective
runtime-composition domain. Thus, retained `runtime = ollama` and
`temperature = X` followed by `--runtime llama-server` must not apply `X` to
llama-server. Unless temperature is explicitly supplied for that effective new
domain, it is unset and native omission/default behavior applies.

`hac config local` retains one complete local runtime composition only. When it
replaces that composition with a different runtime, the old runtime's
temperature must not silently become the new runtime's temperature. A value for
the new retained runtime domain exists only when explicitly part of that new
complete composition. This creates neither profiles, dormant preferences,
per-runtime history, nor multiple saved temperatures. `hac config show` must
truthfully display the temperature of the currently retained local runtime
composition, or absence, without observation or network activity.

This RFC permits RFC-0074's explicit runtime-composition file to accept one
temperature field for each covered textual runtime composition. The file
already selects its runtime and is self-contained; its value is scoped by that
selected runtime. The physical schema may use one top-level common field where
that remains the smallest coherent representation. There is no sampling table,
cross-source merging, or inheritance from retained temperature. Selecting
`--runtime-config PATH` continues to bypass the retained local runtime baseline
under RFC-0094.

RFC-0112's existing complete-replacement loopback retained-local facade may
represent this newly accepted retained field through its existing authority.
It must represent the complete selected runtime composition and must not hide
or preserve temperature when the runtime domain changes. It gains no runtime
discovery, generic settings, inference-options schema, per-capability
temperature, current-runtime observation, or automatic tuning.

Temperature is analogous to RFC-0073 only in bounded composition ownership.
Temperature has one narrow numeric operator control exposed by all three
selected textual runtimes; thinking-disable remains optional and
Ollama-specific. Neither fact implies the other or a combined inference-settings
object.

### Unchanged cluster boundaries

Temperature is not part of ClusterRequest; capability semantics; internal
remote envelopes; receiver protocol; remote-node declarations; routing,
fallback, explanations, status, health, result objects, history, model
selection, or workspace authority. A receiver uses only its own local
composition. RFC-0116, RFC-0123, and RFC-0124 retain caller-local workspace
roots/grants and no sticky model/runtime/session behavior.

## Alternatives considered

1. **No HAC change / external aliases only.** Rejected: the explicit fact
   remains invisible to retained composition and inspection.
2. **Ollama-only temperature.** Rejected: all three current textual adapters
   expose a sufficiently similar explicit numeric operator control, without
   claiming equivalent behavior.
3. **Carry one retained temperature across runtime switches.** Rejected: equal
   values have no demonstrated portable reliability semantics; RFC-0094 already
   conservatively replaces the runtime domain; a new composition receives a
   value only when the operator explicitly selects one for that domain.
4. **Per-capability or per-request temperature.** Rejected: this expands
   capability/request/transport semantics without demonstrated need.
5. **Force temperature=0 for Code.** Rejected: evidence does not justify a
   universal default or reliability policy.
6. **Generic inference/sampling options.** Rejected as premature open-domain
   configuration.
7. **Runtime files only.** Rejected: inspectable ordinary retained composition
   remains part of the problem.
8. **Apply the value to Classify.** Rejected: RFC-0061 deliberately preserves
   adapter-private, currently differing shaping.

## Trade-offs

This adds one common operator control, one runtime-scoped retained composition
fact, one operator input, three adapter translations, validation, and
documentation burden. It improves operator-control and
configuration/inspection parity across current textual engines, and
repeatability/inspectability of an explicitly selected composition. It does
not make model behavior portable, equivalent, or deterministic.

## Impact and proof expectations

A later implementation must prove at least:

- absence preserves today's native request shape;
- explicit zero reaches the native ordinary free-text temperature mechanism for
  Ollama, llama-server, and vLLM;
- finite non-zero values are forwarded unchanged, invalid HAC-domain values
  fail locally, and zero remains distinct from omission;
- same-runtime retained temperature is consumed as a baseline, and compatible
  explicit CLI temperature temporarily overrides it without mutation;
- explicit runtime switching does not carry retained temperature from the old
  domain, and replacing a retained domain does not preserve it unless the new
  complete composition explicitly supplies it;
- `--runtime-config` is self-contained and does not inherit retained
  temperature; `config show` truthfully reports the current retained
  composition's value or absence;
- no remote envelope, ClusterRequest, capability, routing, receiver, result,
  history, or workspace-authority semantics change; and
- Classify and independent Ollama thinking behavior remain unchanged.

The proof need not repeat model experiments or prove behavioral equivalence.

## Decision

Draft. Home AI Cluster proposes one optional finite non-negative,
operator-facing local textual-runtime sampling-temperature control for Ollama,
llama-server, and vLLM. It requests the explicit numeric value through the
selected runtime's native ordinary free-text mechanism; omission preserves
native behavior.

The retained value belongs to one selected runtime-composition domain. Changing
runtime does not automatically carry an old temperature into the new
composition. The fact remains local and adapter-owned: it is not a
ClusterRequest field, capability semantic, routing or transport field, remote
temperature negotiation, generic inference-settings object, Classify control,
or automatic/default temperature policy. No other sampling or inference
parameter is authorized.
