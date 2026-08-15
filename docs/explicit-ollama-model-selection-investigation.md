# Explicit Ollama Model Selection Investigation

Status: Current investigation

## Context

One HAC node should be able to select the model used by its local Ollama
adapter at startup.  This is an operator/runtime concern: a node declared with
`code` may use `qwen2.5-coder:3b`, while another node declared with `chat`,
`summarize`, and `classify` may use `llama3.2`.  The request remains a request
for a capability, never a request for a model.

This document investigates that boundary only.  It authorizes no code,
configuration, protocol, browser, compatibility, or operator-workflow change.

## Current accepted architecture

RFC-0003 puts runtime-specific requests, models, options, and responses behind
the runtime adapter.  It explicitly rejects making model names the primary
routing abstraction; the core owns normalized requests and routing decisions,
while the adapter translates them to its runtime.  Its `RuntimeResult` permits
runtime attribution, including a model, after execution without putting a
model on the request.

RFC-0002 selects Ollama as the first Phase 1 runtime but requires that it not
shape the core.  RFC-0030's second-runtime proof further distinguishes
runtime-specific model selection, health, lifecycle, and failure behavior from
the unchanged cluster API; its real runtime process and model are external
prerequisites, not HAC-managed lifecycle.

The later composition decisions make this concrete.  RFC-0042 accepts a
closed ordinary local runtime choice and runtime-specific arguments, with one
concrete local composition.  RFC-0043 carries that same local composition into
the static-cluster caller.  RFC-0044 reuses it for local runtime health during
status without exposing runtime URL or model in normalized status.  RFC-0038
and RFC-0039 define ordinary static topology as explicit node identity,
capabilities, and address, rather than runtime-model discovery.  RFC-0058 and
RFC-0059 preserve operator-declared remote and caller-local capabilities as
the eligibility inputs.  They do not make runtime or model identity a remote
declaration or routing field.

The core matches this architecture: `ClusterRequest` contains ordered messages,
a `Capability`, and constraints, but no model.  `Capability` is explicitly
independent of model and runtime names.  The router selects eligible
node/adapter/capability combinations; model attribution appears only on a
result.

## Current implementation

`OllamaAdapter` has two constructor defaults:

```python
OllamaAdapter(
    base_url="http://localhost:11434",
    model="llama3.2",
)
```

`chat` and `code` `ClusterRequest` execution use `OllamaAdapter.chat()`, while
summarize and classify use their existing adapter methods; all post that
adapter instance's configured `self.model` to Ollama's existing `/api/chat`
endpoint.  A non-2xx response, including one caused by an unavailable
configured model, is translated to the existing `RuntimeAdapterUnavailableError`;
connection failure before request transmission has its existing distinct error.
The adapter neither starts Ollama nor pulls, loads, keeps loaded, or unloads
models.

Ordinary `create_ollama_local_app_composition()` constructs `OllamaAdapter()`.
Consequently `llama3.2` is presently an adapter hard-coded default inherited
by ordinary composition, not an ordinary CLI selection.  Tests already verify
alternative adapter model values such as `configured-model` are sent in the
Ollama payload.  The RFC-0030 proof command separately exposes
`--ollama-base-url` and `--ollama-model`, both with defaults; it is proof-only,
not an ordinary composition contract.

Other production uses of the default are deliberately separate: legacy
`api.wiring` compatibility/default wiring, the declaration-backed OpenAI
compatibility process's local composition, and the fallback proof's unavailable
adapter.  They must not silently acquire a new ordinary operator contract.

## Construction and startup paths

The shared local-runtime argument and composition boundary is used by:

- `home-ai-cluster-local`, which is both ordinary local-only serving and, at
  the default loopback host, the loopback-browser launcher;
- `home-ai-cluster-static-cluster`, for both inline and declaration-backed
  caller/local-node composition; and
- `home-ai-cluster-status`, which constructs the same local adapter only to
  observe its health alongside declared remotes.

A receiving or remote node is an independently started ordinary local process,
so it owns its own local runtime selection through the local launcher.  The
static-cluster caller needs only its remote node ID, declared capabilities, and
transport address.  Its remote declaration has no model field, and it should
not gain one.

The loopback browser does not construct a runtime; it inherits the local
launcher composition.  The compatibility process has no local-runtime
arguments today and uses its intentionally fixed/default compositions.  The
fallback and RFC-0030 proof compositions are not ordinary operator startup
paths.  No other browser, native client, Aider, or request launcher constructs
an ordinary Ollama adapter.

## llama-server precedent

The accepted ordinary runtime boundary already provides a narrow precedent.
All shared ordinary parsers accept `--runtime` (`ollama` or `llama-server`),
`--llama-server-base-url`, and `--llama-server-model`.  The latter two are
validated as local HTTP URL and non-empty value, rejected for `ollama`, and
both required for `llama-server`.  `create_local_runtime_composition()`
validates them once and wires them to
`LlamaServerAdapter(base_url=..., model=...)`; `LlamaServerAdapter` has no
model default.

That precedent is sufficient for one additional runtime-specific value.  It
does not justify `--model`, runtime-option dictionaries, generic factories,
plugins, or dynamic runtime schemas.

## Candidate contract and per-node semantics

The smallest compatible candidate is:

```text
--runtime ollama --ollama-model MODEL
```

with `llama3.2` as the default, preserving today's ordinary behavior.  It
would be valid only for `--runtime ollama`, be non-empty, and flow through the
existing concrete composition to `OllamaAdapter(model=MODEL)`.  The shared
ordinary argument boundary should carry it where a local runtime is actually
constructed: local serving (and therefore its loopback browser), static-cluster
caller/local node, and status health composition.  A remote receiver selects
its model in its own local process.  Compatibility, proofs, and legacy/default
factories are outside this increment unless a later accepted decision gives
them an explicit ordinary configuration surface.

The resulting boundary is:

```text
operator starts a node with --runtime ollama --ollama-model qwen2.5-coder:3b
  -> local OllamaAdapter(model="qwen2.5-coder:3b")
  -> existing POST /api/chat includes that model
```

This is a property of one process/node's adapter.  A node may independently
declare `[code]` with `qwen2.5-coder:3b`; another may declare
`[chat, summarize, classify]` with `llama3.2`.  HAC need not, and must not,
infer that either model is suited to any capability.  Operators declare
capabilities; routing uses those declarations and eligibility; the selected
adapter always uses its configured model.

The existing Ollama base URL default can remain independent.  Nothing in the
ordinary model path makes a configurable base URL necessary.  Whether ordinary
Ollama base-URL configuration is desirable is a separate future question, not
a prerequisite or an implicit part of this proposal.

## Public boundaries and lifecycle

This candidate needs no model identity in static declarations, preflight,
status, routing explanations, or result contracts.  Current normalized status
reports application and runtime availability only; RFC-0044 expressly keeps
model and URL out.  Existing results may retain runtime-returned/configured
model attribution, but that does not require any new public field.

It also leaves native `/v1/chat` and internal request schemas, the loopback
browser (including Code), OpenAI compatibility, and Aider capability-centered.
No caller gets a model selector.  HAC continues to send the configured model
to an already managed Ollama HTTP service and relies on its existing safe
adapter error handling when that model is unavailable.

## Rejected scope

This increment must reject request-level model selection, model discovery,
model-to-capability inference, quality ranking, fallback, pools, multiple
simultaneous Ollama adapters per node, automatic pull/download, lifecycle
management, generic runtime configuration, plugins, new routing policy, and
model selectors in the browser, OpenAI compatibility, or Aider.

## RFC requirement and recommendation

**Outcome B — narrow RFC required.**  The proposal agrees with accepted
adapter ownership and capability-centered routing, but it adds a stable,
operator-visible runtime configuration contract across ordinary launchers.
`CONTRIBUTING.md` and `RFC/README.md` identify configuration format and
runtime-adapter decisions as RFC subjects; RFC-0042's closed runtime argument
set makes this more than a mechanical private refactor.

The next available number is **RFC-0071: Explicit Ollama Model Selection**.
Its decision boundary should be only: accept one optional, non-empty
`--ollama-model` for the existing ordinary `ollama` runtime, defaulting to
`llama3.2`, wired to the per-node adapter while retaining capability-only
requests, static declarations, routing, lifecycle, and public caller surfaces.
