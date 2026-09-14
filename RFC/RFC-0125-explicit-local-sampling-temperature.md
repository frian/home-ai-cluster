# RFC-0125: Explicit Local Sampling Temperature

Status: Draft

Date: 2026-09-14

Author: frian

## Summary

Home AI Cluster should accept one optional finite non-negative **sampling
temperature** as a common local textual-runtime-composition fact for Ollama,
llama-server, and vLLM. When omitted, HAC preserves each selected
runtime/model's current native/default sampling behavior and sends no ordinary
free-text temperature override. When explicit, the adapter translates the exact
value to its native ordinary free-text request mechanism.

This applies to local Chat, Summarize, and Code, including workspace-aware Code
through its ordinary `capability=code` inference. It excludes Classify, which
retains RFC-0061's adapter-private generation shaping. It adds no request,
capability, routing, transport, remote-node, workspace-authority, model-
selection, or generic-options semantics.

## Problem

The retained repeated workspace-Code experiment records valid `qwen3.5:9b`
results of ordinary settings: 0/4 strict PASS, and temperature=0: 5/5 strict
PASS. Source model, thinking, the ordinary 120-second request timeout, HAC
contract/parser, human workflow, filesystem authority, and production code
were held constant. The first raw control attempt began while `hac local` was
stopped; it did not exercise the model and is not causal/model-behavior
evidence. This is a strong bounded repeatability signal in one local
model/environment, not a model recommendation or statistical result.

A generation fact that can materially affect reliable execution can therefore
remain outside retained HAC composition and invisible to HAC inspection. The
small problem is ownership and inspectability of that one fact, without making
it a cluster-facing policy.

## Goals

- Retain one explicit operator-controlled local sampling-temperature fact.
- Preserve native omission/default behavior when it is absent.
- Translate one shared narrow semantic through the existing Ollama,
  llama-server, and vLLM adapters.
- Keep local runtime composition distinct from capabilities, requests,
  routing, transport, remote ownership, and workspace authority.
- Extend the accepted closed retained-local and explicit runtime-file domains
  without creating a configuration subsystem.

## Non-goals

This RFC does not authorize `top_p`, `top_k`, `min_p`, seed, repeat penalty,
frequency/presence penalties, stop tokens, max-token or context-size controls,
mirostat or engine-specific modes, arbitrary Ollama options, arbitrary
OpenAI-compatible parameters, generic runtime option dictionaries, generic
inference settings, per-capability or per-request temperature, model-specific
tables, automatic tuning, qualification databases, discovery, capability-based
defaults, hidden heuristics, forcing Code to temperature=0, any runtime default
change, remote temperature negotiation, transport/version changes, retries,
parser relaxation, or workspace-Code redesign. Image-generation composition is
outside this RFC.

## Proposal

### Shared value and omission semantics

The accepted semantic domain is one finite number `>= 0`. Negative values,
NaN, and positive or negative infinity fail local validation; an explicit zero
is valid and distinguishable from absence. HAC imposes no arbitrary universal
upper bound. Greater temperature permits or increases sampling randomness as
implemented by the selected runtime/model; zero requests the common
greedy/no-randomness endpoint. HAC does not normalize runtime defaults or claim
that equal non-zero values give identical distributions across engines, models,
tokenizers, templates, or sampling pipelines.

The common compatible local-composition spelling is:

```text
--temperature VALUE
```

It is valid only for the covered local textual runtimes. Blank/non-numeric,
NaN, infinite, and negative input fails before runtime execution. Omission
preserves today's ordinary free-text request shape: HAC sends no temperature
override and does not synthesize 0, 0.7, 0.8, 1.0, or another HAC default.

### Covered execution and Classify exclusion

An explicit value applies uniformly to ordinary free-text Chat, Summarize, and
Code through the selected local adapter. Workspace-aware Code remains ordinary,
independently routed `capability=code`; sampling temperature is neither
workspace authority nor workspace interaction state. The selected execution
node uses its own local composition. No caller value travels in workspace
history, action outcomes, remote requests, or receiver envelopes.

Classify is explicitly excluded. RFC-0061 permits adapter-private prompts,
grammar, JSON mode, constrained decoding, and equivalent result shaping.
Current behavior remains unchanged: Ollama Classify explicitly uses
temperature=0; llama-server Classify explicitly uses temperature=0; and vLLM
Classify has no explicit classification temperature. This RFC neither overrides
nor normalizes that behavior, creates a Classify operator temperature, nor
changes RFC-0061.

### Concrete adapter translation

For covered ordinary free-text inference, omission means omission of the native
field exactly as today. An explicit value translates to Ollama's native
request-level temperature mechanism, or to the native chat-completion
`temperature` field for llama-server and vLLM. This is one accepted HAC fact,
not a shared adapter options object or sampling-policy object. A runtime/model
that rejects an otherwise HAC-valid value produces an ordinary runtime execution
failure; HAC performs no support probe during configuration.

This is not premature engine-independent abstraction: all three currently
supported textual runtimes expose this fundamental concept, zero has the common
endpoint meaning, HAC has concrete adapters for all three, and retained evidence
shows an operational need. It does not generalize to hypothetical engines or
promise portable stochastic behavior.

### Composition and retained configuration

Sampling temperature is one common local textual-runtime-composition fact:

```text
operator -> local HAC runtime composition -> concrete adapter -> native request
```

It is analogous to RFC-0071/RFC-0073 only in ownership. Ollama thinking-disable
remains independently optional and Ollama-specific; neither fact implies the
other, and no combined inference-settings object is created.

This RFC narrowly amends RFC-0074's closed explicit composition-file schema to
allow one top-level common field, for example `temperature = 0.0`, for each of
the three supported textual runtime compositions. It adds no nested sampling
table, options dictionary, or cross-source merging; that file remains a
self-contained alternative source.

This RFC also extends RFC-0094's closed retained local-composition domain with
the optional common fact. `hac config local` may retain it and `hac config
show` must truthfully display absence/unset or the explicit numeric value,
without network activity. It remains a retained baseline; explicitly supplied
compatible CLI input is a temporary suppliedness-aware override and does not
mutate retained state. Because it is common rather than runtime-specific, it
may remain retained when selecting among Ollama, llama-server, and vLLM;
runtime-specific facts continue to follow their existing domain replacement
rules. This is a field-domain extension, not a new merge rule.

RFC-0112's existing complete-replacement loopback facade may represent this
newly accepted retained field through its shared retained-local semantic
authority. This RFC amends that accepted field domain only: Host/exact-Origin
authority, loopback scope, complete replacement, retained-versus-current
process separation, receiver isolation, and exclusions for observation,
discovery, and dynamic schema remain unchanged. No browser API or settings
subsystem is authorized.

### Unchanged cluster boundaries

Sampling temperature is not part of ClusterRequest; Chat, Summarize, Code, or
Classify request semantics; internal remote envelopes; receiver protocol;
remote-node declarations; capability declarations; routing/fallback;
explanations; status; health; result objects; or request history. It is not
model selection. A receiver uses only its own local composition. RFC-0116,
RFC-0123, and RFC-0124 retain caller-local workspace roots/grants and no sticky
model/runtime/session behavior.

## Alternatives considered

1. **No HAC change / external aliases only.** Rejected: the demonstrated fact
   remains invisible to retained composition and inspection.
2. **Ollama-only temperature.** Rejected: the three current textual adapters
   already expose the same narrow concept.
3. **Per-capability Code temperature.** Rejected: capability is requested work,
   not runtime sampling policy.
4. **Per-request temperature.** Rejected: it expands request and transport
   semantics without demonstrated need.
5. **Force temperature=0 for Code.** Rejected: evidence does not justify a
   universal default.
6. **Generic inference/sampling options.** Rejected as premature open-domain
   configuration.
7. **Runtime files only.** Rejected: inspectable ordinary retained composition
   is part of the demonstrated problem.
8. **Apply the value to Classify.** Rejected: RFC-0061 deliberately preserves
   private, currently differing adapter shaping.

## Trade-offs

This adds one shared local composition fact, one retained fact, one operator
input, three adapter translations, validation, and documentation burden. It
improves operator control, inspectability, repeatability, and parity across the
current textual engines, while intentionally not making inference behavior
strongly portable or behavior-identical.

## Impact and proof expectations

A later implementation must prove: omission preserves covered request shapes;
explicit zero reaches ordinary free-text Ollama, llama-server, and vLLM; a
non-zero finite value forwards unchanged; invalid values fail locally; and zero
is distinct from omission. It must prove retained `config local`/`config show`
and temporary CLI override semantics without network activity; RFC-0074 file
self-containment; unchanged remote envelopes, routing/capability semantics,
and node-local workspace-Code composition; unchanged three-adapter Classify
behavior; unchanged independent Ollama thinking behavior; and no
image-generation field. It need not repeat the model experiment or establish a
multi-model benchmark.

## Decision

Draft. Home AI Cluster accepts one optional finite non-negative sampling-
temperature value as a common local textual-runtime-composition fact for
Ollama, llama-server, and vLLM. When omitted, HAC preserves the selected
runtime/model's native sampling behavior and sends no ordinary free-text
temperature override. When explicit, HAC translates the exact value for local
ordinary free-text Chat, Summarize, and Code, including workspace-aware Code.

The fact remains local and adapter-owned. It is not part of capability
semantics, ClusterRequest, routing, remote transport, remote-node
configuration, result contracts, or generic inference configuration.
Classification retains its RFC-0061 adapter-private shaping and is unchanged.
No other sampling or inference parameter is authorized.
