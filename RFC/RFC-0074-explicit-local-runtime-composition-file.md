# RFC-0074: Explicit Local Runtime Composition File

Status: Draft

Date: 2026-08-17

Author: frian

## Summary

Home AI Cluster should accept one optional, explicitly selected TOML file for
constructing the one ordinary local runtime adapter owned by a process. The
file has a closed schema for the existing `ollama` and `llama-server` runtime
composition facts. It is selected only by `--runtime-config PATH` and is
mutually exclusive only with equivalent runtime-composition CLI arguments
explicitly supplied by the operator.

Omitting the option preserves existing CLI-only and zero-argument Ollama
behavior. The file does not configure requests, topology, routing, listener
exposure, credentials, lifecycle, or any cluster-facing surface.

## Problem

RFC-0042 deliberately chose a closed CLI-first local-composition contract and
rejected a retained file before evidence justified schema, selection,
precedence, validation, retention, reload, and permissions decisions. RFC-0043
and RFC-0044 reuse that boundary for ordinary static-cluster and status
operation. RFC-0071 and RFC-0073 then added optional process-local Ollama model
selection and thinking disable.

The shared composition now has five related CLI facts: runtime; optional Ollama
model; optional Ollama thinking disable; and required llama-server loopback HTTP
base URL and model. These facts are reused by ordinary `local`, caller-local
`static-cluster`, and `status`. The merged composition investigation records
that this is concrete repeated operator friction, not merely a first-proof
choice.

The existing static-cluster TOML declaration cannot solve this problem: it
describes caller-owned topology and capability eligibility, whereas this RFC
concerns how one process constructs its own local adapter.

## Goals

- Retain exactly the existing local runtime-composition facts in one small,
  closed, operator-selected document.
- Keep configuration process-local and adapter-owned.
- Preserve all CLI-only behavior, including zero-argument Ollama.
- Avoid precedence by making file mode and equivalent runtime CLI arguments
  explicitly supplied by the operator mutually exclusive.
- Reuse deterministic local validation without runtime, model, or network
  discovery.
- Make the contract available to ordinary local, caller-local static-cluster,
  and static-cluster status construction.
- Keep static topology declarations separate from local runtime composition.

## Non-goals

This RFC does not add general Home AI Cluster configuration, automatic config
search, default locations, environment-variable selection, reload or watch
behavior, profiles, includes, inheritance, aliases, arrays, version fields,
extension sections, generic provider/adapter options, plugins, or arbitrary
pass-through data.

It does not add `ClusterRequest` or request options; capabilities; routing,
candidate selection, local-first behavior, or fallback changes; remote-node
declaration fields; topology or remote addresses; local/remote capabilities;
Aider settings; native-client timeouts; prompts; browser or compatibility
settings; history or persistence; secrets, credentials, headers, passwords, or
tokens; model/runtime discovery or inventory; lifecycle, supervision,
cancellation, retries, databases, Docker, Kubernetes, or dashboard behavior.

It does not add listener `host` or `port`, browser settings, thinking levels or
budgets, model metadata, or an adapter-interface change.

## Proposal

### Explicit selection and compatibility

Ordinary startup gains one optional runtime-composition selection argument:

```text
--runtime-config PATH
```

The file is loaded only when this explicit path is supplied. There is no
current-directory, home-directory, XDG, or other default-location search; no
environment-variable selection; no automatic discovery; and no reload or watch
behavior.

When `--runtime-config` is absent, all existing runtime CLI behavior remains
unchanged. In particular, zero-argument ordinary local composition remains
Ollama-backed; omitted `--ollama-model` preserves the effective existing Ollama
model; omitted `--ollama-disable-thinking` preserves omission of native `think`;
and existing llama-server CLI validation remains unchanged. The retained file
is never required.

### TOML document and closed schema

The file format is TOML. Python provides `tomllib`, and the repository already
has a small strict TOML loader for static topology declarations. TOML is
readable for this tiny operator-owned document. This does not create a general
TOML configuration framework or couple this file to the topology declaration.

The exact allowed shape is one top-level `runtime` key and, according to that
value, at most one matching runtime table.

An Ollama composition is:

```toml
runtime = "ollama"

[ollama]
model = "..."
disable_thinking = true
```

For `runtime = "ollama"`, `[ollama]` may be absent. Its only permitted keys
are `model` and `disable_thinking`. `model`, when present, must be a non-blank
string. `disable_thinking`, when present, must be a TOML boolean. Its omission
means `false`, preserving RFC-0073's existing adapter behavior: HAC sends no
native `think` field. `[llama_server]` is invalid.

A llama-server composition is:

```toml
runtime = "llama-server"

[llama_server]
base_url = "http://127.0.0.1:8080"
model = "..."
```

For `runtime = "llama-server"`, `[llama_server]` is required and its only
permitted keys are `base_url` and `model`. Both are required, must be non-blank
strings, and `base_url` must satisfy the existing absolute loopback `http` URL
boundary. `[ollama]` is invalid.

`runtime` is required, must be a string, and must be exactly `ollama` or
`llama-server`. Unknown top-level or table keys, unsupported runtime values,
wrong-runtime tables, wrong value types, missing required values, and blank
required strings fail validation.

### Validation and failure boundary

An explicitly selected file is parsed and validated locally before application
startup or status observation. Missing or unreadable files, malformed TOML, and
all schema or runtime-specific validation failures produce compact operator-
facing failure before endpoint binding or observation. Diagnostics may identify
the operator-supplied path when needed, but must not dump file contents.

Loading performs no runtime availability check, network request, model
existence check, runtime/model discovery, generation, download, start, stop,
supervision, or lifecycle action. The existing local composition validation and
construction boundaries remain authoritative.

### One source of local composition facts

When `--runtime-config PATH` is supplied, it is mutually exclusive with any
equivalent runtime-composition CLI argument explicitly supplied by the operator.
Implicit parser defaults used by the existing CLI-only path do not constitute a
second configuration source. Thus, file mode alone is valid even though the
existing parser internally defaults `--runtime` to `ollama`; supplying both
`--runtime-config PATH` and `--runtime ollama` is invalid.

The equivalent CLI arguments are:

```text
--runtime
--ollama-model
--ollama-disable-thinking
--llama-server-base-url
--llama-server-model
```

There is no CLI-over-file or file-over-CLI precedence, merged values, partial
override, or fallback between sources. An operator chooses either the existing
CLI composition or one explicit retained runtime-composition file. Existing CLI
arguments remain supported for backward compatibility and one-off operation.

### Ordinary consumers and topology separation

The same file contract constructs only the local adapter of the process that
selects it. It is available to ordinary local startup; caller-local
static-cluster startup in both inline and declaration-backed topology modes; and
static-cluster status's local composition for its finite observation.

Status does not expose runtime configuration or become a model/thinking
inspection API. A retained value such as `disable_thinking` has no new
cluster-facing status meaning merely because it constructed the local adapter.

Static-cluster declarations remain separate, topology-only documents for remote
node identity, remote transport addresses, and local/remote capability
eligibility. They do not gain runtime, model, thinking, adapter, or local
composition fields. A static-cluster invocation may intentionally use both:

```text
--declaration cluster.toml --runtime-config runtime.toml
```

The documents have different ownership and meaning even though both use TOML.

Listener `host` and `port` remain process-listener and exposure concerns, not
adapter construction facts. They, and browser settings, remain outside the
runtime-composition file.

### Privacy and cluster-facing boundaries

The document contains only accepted local runtime-composition facts. It does
not support secrets or credentials and its full contents are not logged by
default. Runtime-specific facts remain process-local and adapter-owned.

This proposal does not change requests, results, status schemas, routing,
declarations, attribution, browser request behavior, OpenAI compatibility,
Aider, native-client timeout semantics, adapter interfaces, or runtime
lifecycle ownership. Engine independence remains a boundary around concrete
adapter facts; it does not require an untyped generic option map.

## Rationale

One explicit file is now smaller than repeatedly reconstructing the same shared
process-local composition across ordinary local, static-cluster, and status
surfaces. Explicit path selection keeps the source visible and avoids hidden
location behavior. A closed two-runtime schema makes validation clear and
prevents generic configuration from leaking into cluster-facing concerns.

Mutual exclusion is deliberately simpler than a precedence stack. It makes one
source authoritative for each invocation while retaining the existing CLI for
short-lived and backward-compatible operation. Keeping topology separate
preserves the distinction between caller-owned cluster facts and local adapter
construction.

## Alternatives considered

### Keep CLI-only composition forever

Rejected. CLI-only startup remains available, but shared repeated runtime facts
now justify optional retention.

### Automatically discovered default configuration

Rejected. Implicit discovery introduces hidden startup behavior, location and
portability questions, privacy concerns, and precedence complexity.

### CLI overrides file values or file overrides CLI values

Rejected for the first contract. Either policy requires mixed-source validation
and a precedence ladder. Mutual exclusion is more predictable.

### General HAC configuration file

Rejected. Combining topology, routing, caller settings, browser, Aider,
timeouts, secrets, and runtime composition collapses distinct ownership
boundaries.

### Runtime values in the static topology declaration

Rejected. A topology declaration must not claim local or remote runtime
internals. The two files intentionally describe different facts.

### Generic adapter/provider options

Rejected. Untyped pass-through weakens validation and is premature abstraction;
engine independence does not require it.

### Environment variables

Rejected. They would create a hidden input and another precedence layer.

### Listener settings in the same document

Rejected. `host` and `port` control listener exposure, not adapter construction.

### Profiles, includes, or multiple named configurations

Deferred. One explicitly selected file already chooses one process-local
composition; more selection mechanisms are not justified.

## Trade-offs

The proposal introduces one retained format, one explicit selection argument,
one strict parser and validation contract, a second TOML document during some
static-cluster operation, and mutual-exclusion rules with existing runtime CLI
arguments.

This is acceptable because runtime composition is now repeated across multiple
ordinary surfaces; the schema is tiny and closed; explicit selection prevents
hidden configuration; mutual exclusion avoids precedence complexity; topology
remains separate; and no cluster-facing meaning is added.

## Impact

After acceptance, a small implementation may add a retained runtime-config
value/loader, strict TOML parsing and validation, `--runtime-config PATH`,
mutual exclusion, reuse of existing composition construction, propagation to
ordinary local/static-cluster/status surfaces, focused tests, operator
documentation, and a privacy-safe proof if useful.

It must not introduce a generic configuration framework, dependency-injection
layer, plugin system, schema framework, or abstraction beyond this closed
document. It must not change any cluster-facing contract or the accepted
ownership of topology, runtime lifecycle, or external runtimes.

## Proof expectations

A later implementation must prove deterministically that:

1. no config path preserves zero-argument Ollama behavior;
2. existing CLI-only composition remains supported;
3. valid Ollama and llama-server files construct the corresponding existing
   local adapter compositions;
4. omitted optional Ollama keys preserve existing defaults and
   `disable_thinking = true` reaches existing RFC-0073 adapter behavior;
5. local, static-cluster caller-local, and status surfaces accept the same file
   contract;
6. file mode plus any equivalent runtime CLI argument fails before startup;
7. missing, unreadable, malformed, unknown, wrong-runtime, and invalid
   llama-server configurations fail locally;
8. loading performs no network/runtime/model discovery or lifecycle action; and
9. request, routing, declaration, result, status, browser, compatibility, and
   Aider contracts remain unchanged.

A retained real-local proof, if needed, must remain privacy-safe and exclude
private paths, machine identity, credentials, prompts, generated content, and
raw runtime traffic.

## Open questions

None within this proposed contract. Concrete implementation naming and small
helper placement remain implementation details.

## Decision

Pending.
