# RFC-0071: Explicit Ollama Model Selection

Status: Accepted

Date: 2026-08-16

Author: frian

## Summary

Home AI Cluster should permit one optional, runtime-specific ordinary startup
value, `--ollama-model MODEL`, when `--runtime ollama` is selected.  It chooses
the model identifier of that process's local `OllamaAdapter`; omission preserves
the existing effective model, `llama3.2`.

The value is neither a cluster request field nor routing information.  Nodes
continue to advertise independently declared capabilities, and routing remains
capability-based.  This RFC adds no Ollama lifecycle, discovery, base-URL,
browser, compatibility, Aider, static-declaration, or generic runtime
configuration behavior.

## Problem

The ordinary Ollama composition currently constructs an `OllamaAdapter` using
its `llama3.2` default.  An operator cannot truthfully select a different
already-installed Ollama model for one ordinary HAC process/node without
changing code or using a proof-only path.

This matters when one node is deliberately declared for `code` and another for
`chat`, `summarize`, and `classify`.  The project needs the smallest explicit
operator boundary for choosing the local Ollama adapter's model while
preserving the accepted separation between capability eligibility and runtime
model identity.

## Goals

- Add one optional `--ollama-model MODEL` value for ordinary
  `--runtime ollama` composition.
- Preserve `llama3.2` as the effective model when the option is omitted.
- Keep model selection process-local and adapter-owned.
- Preserve model-independent cluster requests and capability-centered routing.
- Reuse RFC-0042's shared ordinary local-runtime configuration boundary.
- Keep validation local, deterministic, and free of runtime/model discovery.

## Non-goals

This RFC does not authorize request-level model selection; a generic `--model`;
model discovery or inventory; capability inference from model identity; model
quality ranking, recommendations, benchmarking, fallback, or pools; multiple
simultaneous Ollama adapters or per-capability models in one process; runtime
scheduling; automatic pulls, downloads, or model/runtime lifecycle management.

It also does not authorize ordinary Ollama base-URL configuration; generic
runtime-option dictionaries, adapter factories, plugins, retained runtime
configuration files, or environment-variable model selection; model fields in
static TOML declarations; model selectors in browser, compatibility, or Aider
surfaces; new endpoints; or new capabilities.

## Proposal

### Ordinary Ollama model value

The ordinary local-runtime configuration boundary accepts one optional,
non-empty, Ollama-specific value:

```text
--runtime ollama --ollama-model MODEL
```

Its semantics are:

```text
--runtime ollama
  -> effective model remains llama3.2

--runtime ollama --ollama-model qwen2.5-coder:3b
  -> effective model is qwen2.5-coder:3b
```

The selected effective value is passed only to the process-local
`OllamaAdapter(model=...)`.  That adapter continues to supply its configured
model identifier in its existing Ollama `/api/chat` requests.  This RFC decides
the behavior, not whether an implementation represents the default in argparse
or another local construction detail.

An explicitly supplied empty value is invalid.  `--ollama-model` is invalid
with `--runtime llama-server`.  Invalid runtime/argument combinations fail
locally before application startup, without a network request, model inventory
query, pull, generation, or runtime discovery.  Existing llama-server-specific
arguments and their validation remain unchanged.

### Per-process ownership and capabilities

The configured model is a property of one HAC process's local runtime adapter:

```text
operator
  -> starts HAC node with runtime=ollama
  -> optionally selects an Ollama model
  -> HAC constructs OllamaAdapter(model=...)
  -> node advertises operator-declared capabilities
  -> routing selects by capability
  -> the selected adapter uses its configured model
```

For example, an operator may configure one node with `llama3.2` and declared
`chat`, `summarize`, and `classify`, and another with `qwen2.5-coder:3b` and
declared `code`.  HAC does not encode or infer either `qwen2.5-coder:3b =>
code` or `llama3.2 => chat`.  Model identity is not a statement of suitability;
the operator independently declares capabilities.

`chat` and `code` are existing `ClusterRequest` executions and use the
selected adapter's existing `chat(...)` path.  Therefore the configured Ollama
model naturally applies to both Chat and Code.  Summarize and Classify retain
their existing adapter methods, which use that same adapter's configured model.
This does not change RFC-0067's Code semantics or create a Code-specific
adapter method or model rule.

### Ordinary composition surfaces

RFC-0071 extends only the shared ordinary local-runtime configuration boundary
accepted by RFC-0042, RFC-0043, and RFC-0044.  After implementation, the value
must be carried through each ordinary surface that constructs the shared local
runtime composition:

- `home-ai-cluster-local`;
- the local-node composition of `home-ai-cluster-static-cluster`; and
- `home-ai-cluster-status`.

The loopback browser inherits the runtime of its owning local process and gains
no model selector.  A remote receiving node selects its own local model when
its own ordinary local process starts.  The intentionally separate compatibility
process receives no model configuration under this RFC, even where it currently
constructs an Ollama-backed composition.

### Requests, routing, declarations, status, and health

`ClusterRequest`, `SummarizeRequest`, and `ClassifyRequest` remain unchanged.
No cluster-owned request gains `model`, `preferred_model`, `runtime_model`, or
a model constraint.  Capability semantics, candidate eligibility, local-first
and remote selection, fallback, routing explanations, and request constraints
remain unchanged.  Model identity is not a routing-candidate attribute or
selection input.

Static remote declarations remain limited to accepted topology and routing
facts, including node identity, transport address, and declared capabilities.
They gain no runtime, adapter, or model field; in particular, no TOML model
field is added.  The receiving node owns those local execution details.

Normalized status and preflight gain no model identity, inventory, suitability
check, discovery, or routing-explanation field.  Ollama adapter health remains
a runtime/service availability observation and does not prove that a configured
model exists.  This RFC does not add a startup model-existence probe.  If a
configured model is unavailable, existing adapter/runtime execution and error
behavior remains authoritative; no new cluster-wide model-unavailable taxonomy
is introduced.  Existing normalized result model attribution remains unchanged
and does not become routing input.

### Lifecycle and base URL

HAC only supplies the configured model identifier to an already managed Ollama
service through the existing runtime request.  It does not start, stop, or
restart Ollama; run `ollama serve`; run `ollama pull`; download or discover
models; proactively load, keep resident, or unload models; manage VRAM/RAM; or
update Ollama.  Runtime and model lifecycle remain external and operator-owned.

The existing default Ollama base URL remains unchanged.  Ordinary Ollama
base-URL selection is a separate possible future decision and is not combined
with `--ollama-model` in this RFC.

### Compatibility boundary

This RFC adds no model configuration to native `/v1/chat`, `/v1/summarize`, or
`/v1/classify`; internal cluster request envelopes; the loopback browser or its
Code view; `hac chat`, `hac summarize`, `hac classify`, or `hac code`; Aider;
OpenAI compatibility requests; or static remote declarations.  These callers
continue to ask for semantic capabilities, not models.

## Rationale

RFC-0002 makes Ollama the first runtime without allowing it to shape the core.
RFC-0003 assigns runtime-specific model details to adapters and explicitly
rejects model names as the routing abstraction.  RFC-0030 further separates
runtime-specific selection, lifecycle, health, and failure details from the
cluster API.  This proposal follows those boundaries by carrying one value into
one concrete adapter, rather than into requests or routing.

RFC-0042 accepted a closed, CLI-first ordinary local-runtime composition with
runtime-specific validation, one local runtime adapter per process, and no
lifecycle ownership.  RFC-0043 and RFC-0044 reuse that boundary for ordinary
static-cluster local composition and status.  RFC-0071 answers only the
deferred Ollama-model question within that existing boundary; it does not
supersede RFC-0003, RFC-0042, RFC-0043, or RFC-0044.

RFC-0058 and RFC-0059 retain static declared capabilities as eligibility input,
while RFC-0067 makes `code` a semantic capability rather than a coding-model
quality label.  Keeping model selection local and capabilities explicit
preserves each of those decisions.

## Alternatives considered

### Keep hard-coded `llama3.2` only

Rejected.  It preserves the smallest status quo but prevents ordinary per-node
selection of an already-installed Ollama model.

### Generic `--model`

Rejected.  Model configuration is runtime-specific.  A generic name would make
an Ollama value appear to be a cluster-generic model-selection contract.

### Infer a model from a capability

For example, `code -> qwen2.5-coder`.  Rejected because capabilities and model
identity are independent operator choices.

### Add model identity to static declarations

Rejected.  Declarations describe topology and capability eligibility, not the
receiving runtime's private local configuration.

### Request-level model selection

Rejected.  It would place model identity in the cluster API and routing
contract, contrary to capability-centered architecture.

### Automatic model discovery

Rejected.  Supplying one explicit identifier requires neither inventory nor
lifecycle authority.

### Add ordinary Ollama base-URL selection at the same time

Rejected for now.  It is independent of explicit model selection and would
broaden this decision.

## Trade-offs

The project gains one runtime-specific operator value and conditional validation
rule.  That is more configuration than an unconditional adapter default, but it
is explicit, local to the concrete runtime boundary, and preserves existing
ordinary commands without requiring `--ollama-model llama3.2`.

The option intentionally does not verify that the model exists.  Operators may
still encounter the existing runtime execution failure for an unavailable
service or model, but HAC does not gain discovery, lifecycle, status, or
failure-taxonomy authority merely to avoid that runtime outcome.

## Impact and implementation boundary

After acceptance, a separate implementation may affect only shared ordinary
local-runtime argument parsing and validation, ordinary Ollama composition,
the local, static-cluster local-composition, and status composition paths that
use it, focused tests, operator documentation, and privacy-safe proof material.

It must not require a core, routing, protocol, remote-declaration, browser,
compatibility, Aider, lifecycle, or ordinary Ollama base-URL change.  A need
for any such change is a discrepancy that requires a separate decision, not an
expansion of this RFC.

## Proof expectations

Later implementation must prove that:

1. ordinary Ollama startup without `--ollama-model` still uses `llama3.2`;
2. an explicit non-empty value reaches the constructed `OllamaAdapter`;
3. the configured value is used in the existing Ollama `/api/chat` request;
4. Chat-like `ClusterRequest` execution, including `code`, uses that configured
   adapter model;
5. configuration works through each ordinary local-composition surface that
   constructs Ollama;
6. using the option with llama-server and supplying a blank value are rejected
   before startup;
7. no request schema, routing behavior, remote declaration, normalized status,
   browser, compatibility, Aider, discovery, lifecycle, or base-URL behavior
   changes.

Deterministic automated proof should cover exact configuration propagation.  A
later privacy-safe real-local proof may use one explicitly selected non-default
installed model, but must neither require model download nor add lifecycle
management.  Retained evidence must not contain prompts, generated code,
credentials, private addresses, machine names, or raw sensitive logs.

## Open questions

Whether ordinary Ollama base-URL configuration is useful is a separate future
question.  It is not a prerequisite for, or part of, this RFC.

## Decision

RFC-0071 accepts one optional, non-empty `--ollama-model MODEL` only with
ordinary `--runtime ollama`; omission preserves the effective `llama3.2`
model. The effective value is passed only to the process-local
`OllamaAdapter(model=...)` and must be carried through every ordinary surface
that constructs the shared local runtime composition.

Model identity remains outside requests, routing, capability semantics, remote
declarations, normalized status, preflight, browser, compatibility, and Aider
surfaces. Capabilities remain independently operator-declared and routing
capability-centered. This decision authorizes no model discovery or inference,
automatic pull/download, lifecycle management, model fallback or pools, or
ordinary Ollama base-URL configuration.
