# OBS-01: Singular-to-Multi-Binding Configuration Investigation

Status: Investigation

Date: 2026-10-12

## Question

Does the tested transition from a retained singular runtime composition to an
explicit retained multi-binding composition respect accepted configuration
boundaries? This records the operator's completed dogfooding evidence against
verified `origin/post-1.1-development` at
`1726b0e00d06f60aa38d8a467b4116cc5e4fafc0`.

## Scope and environment

On 2026-10-12, the operator ran three manual configuration tests with an
isolated `XDG_CONFIG_HOME`. Every mutation used that isolated configuration,
leaving the normal retained configuration untouched. These are supplied
operator observations, not tests or runtime traces independently captured by
this investigation. No HAC serving process, runtime, or remote receiver was started
or changed for this investigation. In the commands below, `hac_obs01` denotes the
operator's wrapper that ran `uv run --locked hac` with that isolated
`XDG_CONFIG_HOME`; `$OBS01_DIR` denotes its temporary test directory.

## Accepted architectural contracts

- [RFC-0059](../RFC/RFC-0059-caller-local-static-capabilities.md) and
  [RFC-0094](../RFC/RFC-0094-retained-hac-configuration.md) keep caller-local
  routing permission separate from local runtime composition and remote-node
  declarations. [RFC-0108](../RFC/RFC-0108-local-capability-binding-semantics.md)
  gives each local capability exactly one explicit adapter owner within a
  composition; ownership is disjoint and is not inferred from routing permission.
- [RFC-0110](../RFC/RFC-0110-explicit-local-capability-binding-configuration.md)
  defines the complete `[[bindings]]` document shape.
  [RFC-0142](../RFC/RFC-0142-retained-local-multi-binding-runtime-composition.md)
  makes retained singular and multi-binding runtime compositions complete
  alternatives. Explicit `config local --runtime-config PATH` replaces the
  runtime-composition alternative while preserving independent retained facts.
- [RFC-0143](../RFC/RFC-0143-file-free-incremental-retained-configuration.md)
  permits complete binding mutations only from existing retained multi-binding
  state or an empty retained local runtime state. A singular composition must
  reject incremental binding mutation; HAC cannot invent binding ownership.
  `--owning` is a lookup by an already owned capability, never a persistent
  binding ID. Caller-local capability mutation is separate from binding mutation.
  The [RFC-0128 companion](../RFC/RFC-0128-retained-local-image-generation-companion-composition.md)
  remains a separate Image Generation configuration domain.

## Test 1 — Implicit migration refusal

The operator retained singular Ollama composition with `chat` and `summarize`
caller-local permission and HAC execution limit `2`:

```sh
hac_obs01 config local --runtime ollama --ollama-model qwen3.5:9b \
  --local-capability chat --local-capability summarize --execution-limit 2
```

The isolated configuration also held an Image Generation companion at a
loopback endpoint and one declared remote eligible for Chat and Summarize.
The operator attempted an incremental binding addition:

```sh
hac_obs01 config local binding add --capability code \
  --runtime ollama --model qwen2.5-coder:7b
```

It exited `2` with the following error line:

```text
home-ai-cluster config: error: local binding mutation requires retained multi-binding composition
```

Before and after `config show` displayed the same retained semantic state:
singular Ollama composition, caller-local `chat, summarize`, execution limit
`2`, the Image Generation companion, the remote declaration, unconfigured
External Information, and unauthorized Chat external-information fallback.
This supports refusal of this implicit transition and preservation of the
inspected state. It does not prove every failure path is atomic. The
[mutation implementation](../src/home_ai_cluster/retained_configuration.py)
checks for singular composition before saving; the
[CLI](../src/home_ai_cluster/commands/config_command.py) reports that error.

## Test 2 — Explicit multi-binding replacement

The operator supplied this complete isolated RFC-0110-style document:

```toml
[[bindings]]
capabilities = ["chat", "summarize"]
runtime = "ollama"
model = "qwen3.5:9b"

[[bindings]]
capabilities = ["code"]
runtime = "ollama"
model = "qwen2.5-coder:7b"
```

```sh
hac_obs01 config local --runtime-config "$OBS01_DIR/multi-binding.toml"
```

`config show` then reported multi-binding composition with those two disjoint
bindings. Caller-local permission remained `chat, summarize`; the HAC execution
limit remained `2`. The Image Generation companion, remote declaration,
External Information state, and Chat fallback authorization were unchanged.
The inspection supports explicit replacement and preservation of those
independent retained facts. It says nothing about loaded models, health, or
inference success. The [replacement implementation](../src/home_ai_cluster/retained_configuration.py)
preserves the existing caller-local capability and execution-limit values.

## Test 3 — Incremental mutations

Starting from the inspected multi-binding state, the operator ran:

```sh
hac_obs01 config local capability add code
hac_obs01 config local binding add --capability classify \
  --runtime ollama --model qwen3.5:9b
hac_obs01 config local binding remove --owning classify
```

The first command reported `local capability added`; caller-local permission
became `chat, summarize, code` while the two bindings stayed unchanged. The
second reported `local binding added`; it added an independent `classify`
binding using the same runtime type and model as the Chat/Summarize binding,
without adding `classify` to caller-local routing permission. The third
reported `local binding removed`; it removed the complete `classify` binding
by its owned capability. The original two bindings and caller-local permission
`chat, summarize, code` remained. The operator's final inspection also showed
the same execution limit, Image Generation companion, remote declaration,
External Information state, and Chat fallback authorization.

## Preserved configuration boundaries

`config show` reports retained facts, not live runtime state. In the tested
sequence, the multi-binding collection described local execution capability
ownership, while the separate caller-local set described routing permission.
The execution limit was HAC policy; the Image Generation companion and remote
declaration had separate owners. Adding a binding did not authorize routing to
it, and adding routing permission did not construct a binding. The
[command reference](command-reference.md#hac-config),
[configuration examples](configuration-examples.md#local-runtime-composition),
and [Incus runbook](incus-loopback-receiver-runbook.md#6-inspect-retained-caller-configuration-host-repository-shell)
describe these operator surfaces and retained-state distinctions.

## Operator-experience observation

The singular-state error accurately names the violated precondition. It does
not explain both explicit transition choices: replace the singular composition
with a complete multi-binding runtime-config document, or reset the singular
local configuration and construct bindings incrementally. The operator tested
the replacement path only. This is a minor, non-blocking wording observation;
the current evidence does not justify changing the accepted behavior, adding a
command, or opening a separate implementation task.

## Evidence limitations

The campaign inspected retained state after three selected workflows. It did
not test every failure path, configuration mutation, startup path, or runtime
combination. It did not test the reset-and-rebuild option, model loading,
runtime availability, remote reachability, or actual request execution.

## Assessment

All three reported scenarios are consistent with RFC-0142 and RFC-0143: the
singular state refused implicit binding mutation, complete replacement selected
the multi-binding alternative while preserving independent facts, and later
file-free mutations kept routing permission distinct from binding ownership.
No architectural violation or functional defect is demonstrated within the
tested transition workflow.

## Outcome

**A — The tested workflow is conformant.** No behavioral or architectural
correction is justified by this evidence.

## Recommended next step

Retain this investigation as the OBS-01 record and close the observation. The
error-message usability note can remain here without an additional task.
