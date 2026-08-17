# Local Runtime Composition Configuration Investigation

Status: Investigation only

Date: 2026-08-17

## Question

Has ordinary local runtime composition reached the point where one small,
explicit retained configuration file is simpler and clearer than reconstructing
runtime-specific startup CLI arguments?

## Accepted current behavior

RFC-0042 deliberately selected a closed, CLI-first local-composition contract.
It rejected a retained file before evidence justified decisions about schema,
selection, precedence, validation, retention, migration, reload, and
permissions. RFC-0043 and RFC-0044 reuse that composition for ordinary
static-cluster and status operation. RFC-0071 added an optional process-local
Ollama model, and RFC-0073 added optional process-local Ollama thinking disable;
RFC-0073 explicitly leaves a composition file as a separate question.

The shared composition currently accepts these process-local adapter facts:

| Runtime | Current startup values |
| --- | --- |
| `ollama` | closed runtime choice; optional model; optional thinking disable |
| `llama-server` | closed runtime choice; required loopback HTTP base URL; required model |

The same local-runtime argument set appears in ordinary `local`, caller-local
`static-cluster`, and `status` startup. The first two construct the complete
selected composition. `status` also uses the shared parser and composition
builder for its local observation, but its present builder call passes runtime
and model values only; a future retained contract must explicitly decide its
relationship to status rather than infer it.

Omitting runtime inputs still constructs the existing zero-argument Ollama
composition. This compatibility behavior must remain exact if a later RFC is
accepted.

## Operator-friction evidence

The command reference now documents the same runtime-specific choices in the
ordinary local, static-cluster, and status command surfaces. A selected
llama-server composition requires reconstructing three values, and an explicit
Ollama composition can require runtime, model, and thinking-disable values.
Those facts are process-local and are reused by multiple ordinary paths; they
are no longer only a single first-proof runtime choice.

This is concrete retained-startup friction, not evidence for general project
configuration, runtime discovery, or hidden defaults.

## Separate topology ownership

The existing static-cluster declaration is a retained TOML topology document.
Its closed loader validates caller-owned remote node identity, remote transport
address, and local/remote capability eligibility. It rejects unknown keys and
parses deterministically; loading neither probes remotes nor starts processes.

That ownership is different from local runtime composition:

| Retained fact | Owner and meaning |
| --- | --- |
| Static declaration | Caller-owned static topology and capability eligibility |
| Possible runtime-composition file | How this one process constructs its local adapter |

Putting runtime, model, or thinking values in remote declarations would make a
topology file claim remote runtime internals and contradict RFC-0043 and
RFC-0073. Keeping separate files is simpler and more truthful than combining
topology with process-local adapter construction.

## Candidate boundary

The only credible retained values are the existing closed local-composition
facts: runtime; optional Ollama model; optional Ollama thinking disable; and
llama-server loopback base URL and model. A closed schema for the two supported
runtimes remains preferable to generic adapter options or arbitrary provider
pass-through.

TOML is a readable candidate because the repository already uses Python's
`tomllib` for a small, strict retained declaration. That is parser evidence,
not a reason to couple the two file roles or select TOML without an RFC. The
smallest illustrative shapes are only investigation material:

```toml
runtime = "ollama"

[ollama]
model = "..."
disable_thinking = true
```

```toml
runtime = "llama-server"

[llama_server]
base_url = "http://127.0.0.1:8080"
model = "..."
```

Server bind `host` and `port` are separate process-listener concerns: they
control endpoint exposure and fixed browser attachment, not local runtime
adapter construction. They should not enter this candidate merely because
`local` accepts them at startup.

The following remain outside: request options or `ClusterRequest`; capabilities;
routing; remote nodes, addresses, topology, or capability declarations; Aider;
native client timeouts; prompts; browser or compatibility settings; history or
persistence; secrets; runtime/model discovery or inventory; lifecycle,
supervision, database, environment-variable overrides, and generic
adapter/plugin options.

## Candidate semantics and validation

The boring candidate is one optional path supplied explicitly at startup. There
is no default-location search, implicit discovery, reload/watch behavior,
environment layer, network probe, runtime/model discovery, or secret support.
Loading would do only deterministic local parsing and the existing composition
validation before process startup.

It would need compact failures for a missing or unreadable file, malformed
syntax, unknown key, unsupported runtime, wrong-runtime key, empty required
value, and invalid llama-server URL. It would not check whether a runtime or
model exists or is reachable.

## Options compared

| Option | Assessment |
| --- | --- |
| A. Keep CLI-only | Still backward-compatible and usable through operator-owned scripts, aliases, or service units, but repeats the same retained process facts across three ordinary surfaces. |
| B. One explicit small file | Credible smallest next contract: a closed process-local schema selected by an explicit path, with deterministic validation and no topology coupling. |
| C. Automatically discovered default | Reject for a first contract: it hides startup inputs, adds location, portability, privacy, and precedence behavior, and makes zero-argument startup less legible. |
| D. Broader HAC configuration | Reject: combining topology, routing, caller settings, browser, Aider, timeouts, secrets, and runtime construction would erase accepted ownership boundaries. |
| E. Generic runtime/provider map | Reject: engine independence does not justify untyped pass-through or a plugin/options abstraction. |

For option B, the CLI relationship has four credible choices:

| Relationship | Assessment |
| --- | --- |
| File with CLI overrides | Convenient but creates a precedence stack, mixed-source error reporting, and uncertain visibility. |
| Explicit file and equivalent runtime CLI values mutually exclusive | Smallest and most predictable first contract; one visible source of composition facts per startup. |
| File as defaults beneath CLI | Preserves short overrides but has most of the same precedence and validation complexity. |
| No file | Preserves the present CLI-only contract and remains the option A baseline. |

Precedence is material complexity. If a file is later accepted, explicit path
selection plus mutual exclusion with equivalent CLI runtime values is the
simplest credible starting point. The existing CLI arguments should remain
available for backward compatibility and one-off operation. File omission must
preserve today's zero-argument Ollama behavior exactly.

## Ordinary consumers

A later accepted retained composition would need one shared interpretation for:

- ordinary local startup;
- caller-local static-cluster composition, in both inline and declaration-backed
  modes; and
- static-cluster status's caller-local observation.

It would not require a change to requests, routing, declarations, results,
status schema, browser, compatibility, Aider, adapter interfaces, or lifecycle
ownership. It would only change how each process constructs its already-accepted
local adapter before those surfaces run.

## Future field threshold

A later field needs concrete repeated process-local startup friction, a closed
meaning for one currently supported runtime, shared composition consumption, and
validation that remains local and deterministic. This does not justify thinking
levels or budgets, generic options, model inventory, runtime discovery, or a
cross-runtime policy now.

## Outcome

**Outcome B — a new RFC is justified for one narrowly bounded retained local-
runtime composition file.** The repeated, shared process-local composition
facts now present a concrete retained-operator need whose bounded contract is
smaller than further parallel runtime CLI reconstruction.

The RFC's one central question should be:

> Should HAC accept one optional, explicitly selected, closed retained file for
> constructing this process's ordinary local runtime adapter while preserving
> CLI-only startup and all cluster-facing behavior?

At minimum, that RFC must decide:

- exact closed schema and supported runtime-specific keys;
- explicit path selection and absence of automatic search;
- relationship to equivalent CLI runtime values, including whether they are
  mutually exclusive;
- deterministic parse/validation failures and privacy-safe diagnostics;
- the shared local, static-cluster, and status composition consumers; and
- compatibility: file omission retains zero-argument Ollama exactly.

It must defer file location discovery, environment overrides, reload, secrets,
generic options, topology, requests, routing, lifecycle, model/runtime
discovery, thinking levels or budgets, and all broader configuration questions.

This investigation authorizes no implementation or configuration contract.
