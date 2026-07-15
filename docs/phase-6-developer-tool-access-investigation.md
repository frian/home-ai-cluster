# Phase 6 Developer Tool Access Investigation

Status: Investigation only

Date: 2026-07-15

## Purpose and scope

This investigation asks whether one real local developer tool can use the
completed RFC-0031 compatibility endpoint without broadening its contract. It
does not install or run Aider, start a runtime, change Home AI Cluster code,
create configuration in this repository, or define a new RFC.

The representative is Aider. The question is not whether every Aider mode can
work with the endpoint; it is whether a small, explicit, non-streaming Aider
proof can do so truthfully.

## Current RFC-0031 boundary

RFC-0031 provides only `POST /v1/chat/completions` on the dedicated loopback
process at `http://127.0.0.1:8001/v1`. It accepts exactly the endpoint
identifier `home-ai-cluster`, non-empty plain-text `system`, `user`, and
`assistant` messages, optional `stream: false`, and optional `n: 1`.

It rejects unknown fields and, in particular, `stream: true`, `temperature`,
`max_tokens`, `tools`, `tool_choice`, `response_format`, and `user`. The
identifier is not a runtime-model, adapter, node, or routing selector. The
compatibility process accepts an absent authorization header or a syntactically
valid placeholder bearer header, then ignores the bearer value.

The current implementation matches that boundary: it is a public-edge
translation to `ClusterRequest(..., Capability(name="chat"))`, uses the
existing cluster flow, and binds the dedicated process only to `127.0.0.1`.
The RFC-0031 implementation and its recorded real proof are both present on
`main` at investigation start (`6c06d39` and `43e62c0`, respectively).

## Representative tool

The representative is Aider v0.86.0, the current Aider GitHub release examined
on 2026-07-15. The current official Aider documentation was also examined on
that date, together with the v0.86.0 source and the current configuration
reference.

Aider documents support for any OpenAI-compatible API endpoint. Its documented
provider form is `openai/<model-name>`, so the client-side Aider model value
for this endpoint is `openai/home-ai-cluster`. The `openai/` prefix selects
Aider's OpenAI-compatible provider; `home-ai-cluster` remains the endpoint
identifier supplied to the compatibility service. It does not select a Home AI
Cluster runtime model.

## Aider configuration surface

Aider supports all inputs needed for an opt-in proof without changes to Home AI
Cluster:

| Need | Aider client-side setting | Finding |
| --- | --- | --- |
| Model | `--model openai/home-ai-cluster` or `AIDER_MODEL` | Required by Aider; uses RFC-0031's fixed identifier. |
| Custom base URL | `--openai-api-base http://127.0.0.1:8001/v1` or `AIDER_OPENAI_API_BASE` | Supported. Aider's OpenAI-compatible guide also documents `OPENAI_API_BASE`. |
| API key | `--openai-api-key <placeholder>` or `AIDER_OPENAI_API_KEY` | Required by Aider's documented OpenAI-compatible setup. Use a non-secret placeholder only. |
| Non-streaming | `--no-stream` or `AIDER_STREAM=false` | Required because Aider defaults to streaming. |
| Suppress `temperature` | A temporary `--model-settings-file` entry with `use_temperature: false` | Required for an unknown `openai/home-ai-cluster` model. |
| Avoid writes and retained history | `--dry-run`, `--no-git`, `--no-auto-commits`, temporary or null history paths | Client-side proof hygiene, not an endpoint requirement. |

The Aider configuration reference says an unknown model's default settings are
`edit_format: whole`, `use_temperature: true`, and `streaming: true`. Its
source constructs completion arguments with `model` and `stream`, adds
`temperature` unless `use_temperature` is false, and adds `tools` and
`tool_choice` only when its coder supplies functions. The base coder has
`functions = None`; retaining the `whole` edit format for this proof therefore
avoids the function/tool-calling path. No Aider setting should add
`max_tokens`, `response_format`, or `user` for this proof.

The temporary model-settings file is an Aider-owned client override, for
example:

```yaml
- name: openai/home-ai-cluster
  edit_format: whole
  use_temperature: false
```

It is not Home AI Cluster configuration and must not be added to this
repository. Aider documents a `--model-settings-file` option specifically for
such per-model overrides.

## Observed request behavior

This is a source-and-documentation investigation, not a live Aider execution.
The following describes the current Aider v0.86.0 behavior relevant to the
proposed proof.

| Behavior | Default | Proof configuration | RFC-0031 fit |
| --- | --- | --- | --- |
| Request method and path | Aider delegates chat completion to its OpenAI-compatible provider. | `POST /v1/chat/completions` relative to the configured `/v1` base URL. | Supported. |
| Preliminary model request | The documented OpenAI-compatible invocation selects a model and starts chat directly. No Aider configuration requires `GET /v1/models`. | No model-listing request to Home AI Cluster is part of the proof. | Supported. |
| `stream` | `true` by default. | `--no-stream` produces `stream: false`. | Supported only with the override. |
| `temperature` | An unknown model defaults to `temperature: 0`. | `use_temperature: false` omits it. | Supported only with the override. |
| `tools`, `tool_choice` | Sent only when the selected coder supplies functions. | `whole` mode leaves the base coder's functions unset. | Supported. |
| `max_tokens`, `response_format`, `user` | Not default fields in Aider's completion construction. | Do not set related Aider options or extra parameters. | Supported. |
| Message roles and content | Aider builds a coding conversation, normally using plain-text system and user messages in this mode. | Do not attach files, use images, or enable tool/function modes. | Supported by the accepted plain-text role subset. |

The exact Aider request body must be captured only in a later opt-in execution
proof, with redaction and without retaining prompt or response content. This
investigation does not claim a live packet capture. The documented provider
form and source construction establish the minimum configuration; the actual
proof should verify that the wire `model` value is `home-ai-cluster` and that
the body contains only the allowed fields before reporting success.

## Compatibility matrix

| Observed requirement | Classification | Reason |
| --- | --- | --- |
| Custom OpenAI-compatible base URL | client-side configuration only | Aider provides an OpenAI-compatible base-URL setting. |
| Endpoint identifier `home-ai-cluster` | client-side configuration only | Aider's `openai/<model-name>` provider form can supply the fixed identifier without creating runtime-model selection. |
| Placeholder API key / bearer header | client-side configuration only | Aider's OpenAI-compatible setup expects a key; RFC-0031 explicitly tolerates a syntactically valid ignored placeholder on loopback. |
| `POST /v1/chat/completions` | already supported | This is RFC-0031's only compatibility route. |
| No `GET /v1/models` | already supported | The Aider documented direct model invocation needs no Home AI Cluster model-listing endpoint. |
| Disable streaming | client-side configuration only | Aider defaults to streaming but documents `--no-stream`; RFC-0031 correctly continues to reject streaming. |
| Omit `temperature` | client-side configuration only | An Aider temporary model setting can set `use_temperature: false`; accepting it server-side would contradict RFC-0031. |
| Plain text `system`/`user` messages | already supported | RFC-0031 accepts these roles and non-empty string content. |
| Tools/function calling | explicitly rejected by RFC-0031 | The small proof must remain in Aider's non-function `whole` mode. |
| `response_format`, `user`, arbitrary extra parameters | explicitly rejected by RFC-0031 | They must stay unset; neither should be accepted or ignored for Aider. |
| Model metadata, token limits, and pricing | client-side configuration only | Aider says unknown-model limits/costs may safely be ignored and are not enforced. Optional local metadata affects Aider only, not the cluster. |
| Model discovery or aliases | requires a new RFC | RFC-0031 explicitly excludes a model registry, aliases, and `GET /v1/models`. |
| Broad Aider edit formats or multimodal inputs | out of scope | They may introduce tools, unsupported fields, or unsupported message content. |

## Smallest possible proof

With the compatibility process and an already supported local runtime running
separately, one Aider command can make the minimal request after a temporary
client-only settings file has been prepared outside the repository:

```text
aider --model openai/home-ai-cluster \
  --openai-api-base http://127.0.0.1:8001/v1 \
  --openai-api-key ignored-loopback-placeholder \
  --model-settings-file /tmp/hac-aider-settings.yml \
  --no-stream --no-git --no-auto-commits --dry-run \
  --no-analytics --no-check-update --no-gitignore \
  --input-history-file /dev/null --chat-history-file /dev/null \
  --env-file /dev/null \
  --message "Reply with a short acknowledgement only."
```

This is a Unix-like proof command; the later proof should use platform-
appropriate temporary/null history paths where necessary. It deliberately uses
a non-secret placeholder, a generic non-sensitive message, no attached source
files, no model metadata, no model discovery, and no repository-local Aider
configuration. The settings file must contain the two-field YAML example above
and be removed after the opt-in proof.

The proof executor should additionally confirm, without retaining the body,
that the configured Aider version issues one non-streaming request to the
RFC-0031 route and that any local Aider metadata/update check is disabled or
kept off the network. Aider model metadata is not a Home AI Cluster endpoint
requirement; it is optional client-side presentation data.

## Gaps

There is no Home AI Cluster gap for the configured proof. The default Aider
experience is intentionally not compatible because it streams and sends
`temperature`; that is a client default, not an RFC-0031 implementation
defect.

The later execution proof must verify the provider library's final wire model
value and request body. If the observed Aider version sends a model value other
than `home-ai-cluster`, it must be reported as an Aider/client configuration
incompatibility. It must not be fixed by accepting aliases, prefixes, or
arbitrary model values at the Home AI Cluster endpoint.

## Architectural classification

| Possible action | Classification |
| --- | --- |
| Temporary Aider settings that disable streaming and temperature | Client-side configuration only. |
| Starting the existing loopback compatibility entrypoint for an opt-in proof | Already authorized by RFC-0031. |
| Accepting `temperature`, streaming, tools, or unknown fields | Explicitly rejected by RFC-0031. |
| Correcting a mismatch between the implementation and RFC-0031's existing strict contract | A narrow implementation correction within accepted semantics; no such mismatch was found. |
| Adding aliases, a model catalogue, model selection, token accounting, or provider declarations | A new architectural decision requiring an RFC. |
| Making every Aider edit mode or client workflow work | Unsupported and deliberately out of scope. |

## Alternatives considered

### Change the endpoint to accommodate Aider defaults

Rejected. Accepting or silently dropping `temperature` or `stream: true` would
misrepresent generation and streaming semantics. The necessary Aider overrides
already exist, so no server change is justified.

### Add `GET /v1/models` or a model alias

Rejected. Aider's documented direct OpenAI-compatible invocation does not need
model discovery. A cluster catalogue or alias would decide ownership,
configuration, and model-selection semantics beyond RFC-0031.

### Select another developer tool

Rejected for this investigation. Aider can reach the endpoint with a small,
truthful client-side configuration, so a replacement representative is not
needed.

## Privacy and local-first considerations

The proof remains loopback-only and uses no cloud account, real token, or
repository-retained secret. RFC-0031 ignores the placeholder bearer value and
does not log, persist, forward, or route on it.

Aider itself has history, analytics, update-check, git, and optional LLM
history facilities. The proposed command disables the relevant optional
network/write behavior and directs input/chat history to a null device. It
must not enable `--llm-history-file`, `--cache-prompts`, attached files, or
tool/function modes. A later operator should review their shell history and
local Aider defaults as part of the opt-in proof; none of those client-local
choices authorize Home AI Cluster to retain data.

No prompt, response, bearer value, or machine-specific private detail is
recorded in this document.

## Recommendation

**Outcome A — proof can run unchanged.**

Run a separate opt-in local Aider execution proof using the existing
RFC-0031 process and only temporary Aider-side configuration. Use Aider's
`--no-stream` option plus an external model-settings file that disables
temperature; do not change Home AI Cluster code or its compatibility contract.

The proof report should record the exact Aider version, command shape without
secrets, loopback listener, successful response envelope, and the redacted
request-field check. It should not retain the bearer value, prompt, response,
or tool-specific secrets.

## Questions requiring an RFC

None block the recommended proof. The following would require a separate RFC
before any implementation:

* endpoint model aliases or a model catalogue;
* request-level concrete model, adapter, or node selection;
* streaming, tools, structured output, multimodal content, or generation
  controls;
* token accounting, pricing, or finish-reason provenance at the cluster edge;
* real authentication, stored credentials, LAN binding, or remote access; and
* a Home AI Cluster configuration format for any of those decisions.

## Evidence sources

Repository sources examined on 2026-07-15:

* [RFC-0031: Minimal OpenAI-Compatible Chat Access](../RFC/RFC-0031-minimal-openai-compatible-chat-access.md);
* [Phase 6 OpenAI-Compatible Access Investigation](phase-6-openai-compatibility-investigation.md);
* [Phase 6 OpenAI-Compatible Access Proof](phase-6-openai-compatibility-proof.md);
* `src/home_ai_cluster/api/openai_compatibility.py`,
  `src/home_ai_cluster/openai_compatibility.py`, `src/home_ai_cluster/main.py`,
  its entrypoint in `pyproject.toml`, and the compatibility tests; and
* accepted RFCs governing the system shape, runtime adapter and availability
  boundaries, routing, node attribution, the second adapter proof, and
  RFC-0031.

Current primary Aider sources examined on 2026-07-15:

* [Aider OpenAI-compatible API guide](https://aider.chat/docs/llms/openai-compat.html);
* [Aider options reference](https://aider.chat/docs/config/options.html);
* [Aider advanced model settings reference](https://aider.chat/docs/config/adv-model-settings.html);
* [Aider v0.86.0 release](https://github.com/Aider-AI/aider/releases/tag/v0.86.0);
* [Aider v0.86.0 completion construction](https://github.com/Aider-AI/aider/blob/v0.86.0/aider/models.py); and
* [Aider v0.86.0 coder stream/function boundary](https://github.com/Aider-AI/aider/blob/v0.86.0/aider/coders/base_coder.py).
