# Real-Tool Cluster-Routing Investigation

Status: Investigation only

Date: 2026-07-18

## Question and conclusion

This investigation answers:

> Which one real developer tool is the strongest candidate for proving that the
> user continues an ordinary workflow while Home AI Cluster performs real
> ordinary static-cluster routing?

**Aider is the strongest candidate.** It is the only candidate considered here
that has retained evidence of fitting the accepted narrow compatibility request
subset. That is client-compatibility evidence, not static-cluster-routing
evidence.

No evaluated tool can use unchanged accepted surfaces to make the desired proof.
The dedicated compatibility process is currently local-only; making it an edge
over an ordinary explicit static cluster would require a narrow RFC before any
implementation. This investigation does not create that RFC, a runbook, code,
or an architectural contract.

## Current accepted access and routing surfaces

The ordinary caller exposes the native loopback endpoint:

```text
POST http://127.0.0.1:8000/v1/chat
```

Its request is Home-AI-Cluster-native: `messages` plus a capability, with a
normalized `ClusterResult` response. `home-ai-cluster-chat` is the installed,
one-shot client of this endpoint. It is intentionally a project command, not a
general developer-tool protocol. An external tool capable of arbitrary HTTP is
not thereby an ordinary native integration: it would need to know the native
JSON envelope and result shape, and this investigation must not change either
to accommodate a tool.

The separate compatibility process provides only this loopback edge:

```text
POST http://127.0.0.1:8001/v1/chat/completions
```

[RFC-0031](../RFC/RFC-0031-minimal-openai-compatible-chat-access.md) limits it
to the fixed `home-ai-cluster` endpoint identifier, non-streaming plain-text
`system`, `user`, and `assistant` messages, and `n: 1`. It rejects unknown
fields, streaming, generation controls, tools, model discovery, aliases, and
request-level infrastructure selection. An absent authorization header or a
syntactically valid placeholder bearer value is accepted and ignored on this
loopback edge.

The ordinary `home-ai-cluster-static-cluster` process, separately, constructs
one local composition plus explicitly declared remote wiring. It owns local-first
capability routing, accepted pre-execution fallback, transport, result
validation, and declared-node attribution. The retained
[end-to-end ordinary remote request proof](end-to-end-ordinary-remote-request-proof.md)
demonstrates this path with `home-ai-cluster-chat` across two physical machines.

Current implementation confirms that these process constructions do not compose.
`create_openai_compatibility_app()` calls `create_app()` with no local
composition, static remote wiring, static remote collection wiring, declaration,
or composition-selection input. The compatibility route consequently follows
the existing local-only fallback wiring. In contrast,
`home-ai-cluster-static-cluster` parses its operator-owned declaration, creates
the static remote wiring, and passes it to `create_app()`. The compatibility
command also has no command-line surface for a declaration or ordinary local
runtime composition.

## Exact desired proof

The eventual proof should establish one bounded developer workflow:

```text
ordinary developer tool
  -> caller-local compatibility endpoint
  -> ordinary explicit static-cluster composition
  -> local-first capability routing
  -> unavailable caller-local runtime before request transmission
  -> accepted bounded fallback
  -> declared receiver on one trusted LAN
  -> normalized result with declared remote attribution
```

The tool may know only its own local endpoint settings and the fixed
compatibility endpoint identifier. It must not receive a node, runtime, adapter,
concrete runtime model, declaration, remote URL, candidate order, fallback
setting, or lifecycle control. One successful response must be attributable to
the declared remote node by the caller-owned normalized result; a direct call to
the receiver is not a substitute.

## Candidate selection method

The selected candidates are deliberately limited to two.

- **Aider** is mandatory and evidence-backed: the repository retains a real
  Aider proof against the current strict compatibility process.
- **Cline** is included as one current documented OpenAI-compatible developer
  tool with a configurable base URL. It is a useful negative control because
  its documented agent and model-configuration expectations expose why broad
  agentic tools must not define the next contract.

No third candidate was added. A market survey would not improve the decision:
the repository already establishes that a candidate must fit a narrow,
non-streaming chat-completions subset and that the missing issue is process
composition, not popularity. `home-ai-cluster-chat`, curl, and generic HTTP
clients are excluded because they are not independent ordinary developer-tool
integrations.

External documentation below was inspected on 2026-07-18. The Aider latest
release displayed by its official GitHub releases page was v0.86.0; its official
OpenAI-compatible, options, and model-settings documentation was inspected at
that state. Cline's official OpenAI-compatible and telemetry documentation was
inspected at its current published documentation state; those pages do not state
one extension version.

## Candidate 1 — Aider v0.86.0

### Evidence and accepted-surface compatibility

Aider is a local terminal coding assistant. Its official documentation says it
can use an OpenAI-compatible endpoint with an `openai/<model>` client model
name, configurable OpenAI base URL, and API key. The retained
[Aider access proof](phase-6-aider-access-proof.md) already observed one real
v0.86.0 request to the accepted process. It recorded exactly one
`POST /v1/chat/completions` request, a wire model of `home-ai-cluster`, only
`messages` and `model` top-level fields, no preliminary model-list request,
and no streaming, temperature, tools, tool choice, maximum-token, response-format,
or user field.

That retained result establishes client compatibility with the existing
compatibility edge. It does **not** establish ordinary static-cluster routing:
the process in that proof used the current local-only compatibility construction.
Repeating the proof without changing the process construction would be a
compatibility repetition, not new cluster evidence.

### Minimal client-only proof configuration

The existing Phase 6 investigation identifies an opt-in, bounded configuration:

- client model `openai/home-ai-cluster`, which presents the accepted fixed
  endpoint identifier rather than choosing a Home AI Cluster runtime model;
- caller-local base URL for the dedicated compatibility process;
- a non-secret placeholder key, which the loopback process accepts
  syntactically and ignores;
- `--no-stream` because Aider otherwise defaults to streaming;
- a temporary model-settings file that sets `use_temperature: false` and the
  non-function `whole` edit format; and
- dry-run, no-git, no-auto-commits, no analytics, no update check, and
  non-retained input/chat history settings for proof hygiene.

The current Aider options documentation confirms that streaming can be disabled,
prompt caching defaults off, and one-shot `--message` mode exists. It also
documents important local defaults that a proof must override or avoid: input
and chat history file paths, automatic commits, automatic linting, analytics
controls, and update checks. The proof must not enable LLM-history logging,
prompt caching, attached source files, tool/function modes, tests, linting,
file watching, or browser features.

### Required distinctions and boundary assessment

| Question | Assessment |
| --- | --- |
| Client compatibility with an accepted surface | Demonstrated by the retained Aider proof for one strict non-streaming chat-completions request. |
| Can that surface reach ordinary static routing now? | No. The compatibility process is local-only and accepts no static composition input. |
| Is the Aider setup client-only? | Yes, for the existing local-only compatibility proof. It is not sufficient to select a static cluster. |
| Does Aider require protocol expansion? | No for the retained bounded mode. Streaming, tools, generation controls, aliases, discovery, or broader edit modes remain outside the accepted subset. |
| Does Aider violate topology blindness? | Not in the bounded mode: it receives no topology setting and sends only to its caller-local compatibility URL. |

Aider can remain local-first: the tool and compatibility edge run locally, and
the actual static receiver is limited to the operator's trusted LAN. It requires
no cloud account for the proposed proof, although the tool itself must be
installed by the operator. The placeholder key must not be a real credential.

The significant privacy boundary is client-side source context. Aider can read
a codebase and normally has local history, git, analytics, update, cache, and
editing features. Those are not Home AI Cluster retention, but they matter to a
privacy-safe proof. The proof should use a harmless temporary or empty working
context, no attached files, no retained histories, analytics disabled, and no
network feature other than the caller-local compatibility endpoint and the
already accepted caller-to-receiver transport. No source, prompt, response, or
credential belongs in retained evidence.

### Later repository impact and proof complexity

No Aider-specific core code should be added. If a narrow composition RFC is
accepted, later work would affect the compatibility process construction,
focused tests, operator documentation, and one privacy-safe proof record. It
would remain architectural because it determines which existing ordinary
topology and local composition the separate public edge may construct and how
the operator selects it. The proof itself is manageable because Aider's
request-shape compatibility has already been observed, but its client defaults
must be controlled precisely so one request does not become history, telemetry,
source exposure, a retry, or a tool call.

The support-promise risk is controlled only by naming this one Aider version and
one configured non-streaming plain-text workflow. It must not promise every
Aider mode, automatic commits, repository editing, or future Aider versions.

## Candidate 2 — Cline (current documentation state)

### Evidence and accepted-surface compatibility

Cline's current official OpenAI-compatible-provider documentation supports a
custom base URL, API key, and model ID. It therefore has a superficially similar
configuration shape: the fixed compatibility identifier could be entered as a
model ID, and a caller-local base URL could be configured.

The documentation does not establish a compatible bounded request for this
repository. It treats the API key as a provider secret, expects a selected
model ID and model configuration such as output-token and context-window
values, and offers a connection-verification action without documenting the
exact request sequence. It does not demonstrate that no model-list, metadata,
or other preliminary request occurs. It also exposes computer-use/tool-call
capability, and Cline's documented agent tooling reads files, searches a
workspace, runs commands, edits files, and sends tool definitions and results
through its agent flow.

The required narrow compatibility process neither supports those fields nor
permits tool calling. Current evidence does not identify a documented Cline mode
that performs exactly one non-streaming, plain-text chat-completions request
with no tool definitions, no extra metadata request, no source context, and no
retry. The candidate is therefore unsuitable for the current proof; it is not
a reason to expand Home AI Cluster.

### Required distinctions and boundary assessment

| Question | Assessment |
| --- | --- |
| Client compatibility with an accepted surface | Not demonstrated. Base URL, key, and model configuration are necessary but do not prove RFC-0031 request compatibility. |
| Can that surface reach ordinary static routing now? | No, for the same compatibility-process composition gap as Aider. |
| Is configuration client-only? | The provider settings are client-side, but their request and agent semantics are unverified against the accepted subset. |
| Does Cline require protocol expansion? | Its documented agentic capability would require unsupported tools, and its model/metadata expectations could pressure model discovery or generation metadata. Those expansions are rejected. |
| Does it preserve the proof's privacy and topology boundary? | Not credibly for the current next step: normal agent tools can read source and execute commands, and the exact request sequence is unknown. |

Cline can be configured for a local provider, but its broader product supports
accounts, cloud providers, telemetry controls, hosted configuration, and agentic
workspace operations. Its telemetry documentation says telemetry is optional and
can be disabled, but that does not make the unproven agent request shape
suitable. No account, hosted service, telemetry, prompt storage, remote
configuration, model catalogue, or tool execution should enter the Home AI
Cluster proof.

Even if a future investigation finds a strictly compatible Cline mode, the
existing compatibility/static-composition gap would remain. For now, validating
the tool would require a larger tool-specific request inspection effort before
it could produce cluster value. That is more complex than the Aider path and
would risk making an agentic tool's needs a Home AI Cluster support promise.

## Direct comparison

| Criterion | Aider v0.86.0 | Cline current documentation state |
| --- | --- | --- |
| First-user usefulness | Direct terminal coding-assistant workflow. | Familiar IDE agent workflow, but broader than the required proof. |
| Accepted chat-only fit | Retained real request evidence for the strict subset. | No evidence of a strict one-request, no-tool subset. |
| Caller-local endpoint | Documented custom base URL; retained proof used the dedicated loopback edge. | Documented custom base URL, but exact verification/request behavior is not established. |
| Fixed endpoint identifier | Retained wire value matches `home-ai-cluster`. | Configurable model ID, but model-selection and metadata behavior are unverified. |
| Streaming | Can be disabled explicitly. | Not established for the intended tool workflow. |
| Model list or extra requests | Retained proof observed none. | Not established; documentation describes verification and model settings. |
| Placeholder key | Retained proof used a non-secret placeholder accepted by the current edge. | Documentation expects a provider secret; placeholder behavior is not established. |
| Tool/function calls | Avoidable in the retained `whole`-format proof. | Central documented agent capability and outside the accepted edge. |
| Source and response retention | Bounded with explicit client options and no attached files. | Agent workspace access and retention behavior make the smallest proof less clear. |
| Static-cluster reachability now | No; missing process composition. | No; missing process composition plus unproven protocol fit. |
| Proof complexity and support risk | Lowest: an existing, privacy-bounded proof foundation. | Higher: would first need tool-specific compatibility and privacy evidence. |

## Why Aider is the strongest candidate

The previous Aider proof is the best foundation because it already proves the
hard client-side facts that must remain true: a real coding assistant can use
the fixed compatibility identifier, caller-local base URL, one accepted
non-streaming chat-completions request, and no model-list request. It also
documents the exact client-side controls needed to avoid unsupported fields and
client retention.

It is not sufficient evidence for the new goal because the previous endpoint
was local-only. The new value would come only from combining this known client
with one ordinary static-cluster composition and showing caller-owned declared
remote attribution. That makes Aider the strongest *foundation*, not evidence
that the desired integration already exists.

## Can any candidate use unchanged accepted surfaces?

No. Neither selected external developer tool can truthfully use the native
`/v1/chat` contract as an ordinary integration, and neither can cause the
current compatibility process to construct ordinary static-cluster wiring.

The accepted native process and the accepted static-cluster process already
compose, as proved by `home-ai-cluster-chat`. The accepted compatibility process
and the accepted static-cluster composition do not. Client configuration cannot
bridge a process-construction boundary. Therefore a runbook and proof alone
would claim a composition the current code and contracts do not provide.

## Exact missing architectural question

The missing decision is narrower than OpenAI-compatibility expansion:

> May the dedicated loopback-only OpenAI-compatible process construct the
> existing operator-selected ordinary local-only or explicit static-cluster
> composition, and what single operator-owned startup input and validation
> boundary selects that composition without duplicating topology, routing,
> runtime, lifecycle, or compatibility-protocol authority?

This wording follows the current code: the compatibility process currently
constructs no explicit composition, while ordinary local and static commands
have distinct accepted construction and validation paths. The question is not
whether a client selects topology; the client remains topology-blind. It is not
whether to add OpenAI fields, models, aliases, streaming, tools, a LAN-facing
compatibility listener, authentication, or lifecycle automation. Those remain
out of scope.

The selection and validation boundary is architectural: it determines process
responsibility, configuration ownership, topology authority, and future
compatibility. An RFC is required before implementation.

## Recommended next step

Create a **narrow RFC before implementation**, limited to the missing
process-composition decision above. It should decide whether and how the
separate loopback compatibility process may be started over existing ordinary
compositions while preserving their validation and ownership boundaries.

Do not write a runbook or execute a real tool proof first. A future runbook is
justified only if that RFC is accepted and implemented. If the RFC is rejected,
no real-tool routing proof should be attempted with Aider under the current
surface, because it would not test the requested path.

## Smallest eventual proof boundary

If a narrowly scoped RFC is accepted and implemented, the eventual Aider proof
should use exactly two physical machines on one trusted LAN, one caller-local
compatibility listener, one explicit declared remote, and one ordinary receiver.
The caller local runtime must be unavailable before the one tool submission;
the receiver's local runtime must remain available. The tool must make one
bounded non-streaming action with no retry, no direct receiver request, no
node/runtime/adapter/model/declaration/remote selector, and no tool/function
call.

Success would require a complete normalized caller-owned result with the
sanitized declared remote node ID, rather than `local`, and evidence that the
tool received the translated compatibility response. The proof must not attempt
to demonstrate discovery, balancing, scheduling, retries, runtime lifecycle,
broader compatibility, general Aider support, or production security.

## Privacy-safe retained evidence

A later proof may retain only:

- the tool and Home AI Cluster versions or revision;
- sanitized process roles and command shapes;
- confirmation of the selected bounded client configuration and disabled
  retention/telemetry features;
- the fact that one tool action and one resulting cluster request occurred;
- whether standard success or failure conditions occurred; and
- a structural, redacted normalized result showing the declared remote node ID.

It must not retain prompt or generated-response content, source code or source
context, file names or paths, private address, hostname, username, credential,
token, declaration content, raw HTTP body, raw log, screenshot, or packet
capture. The tool's local files, history, analytics, update checks, and external
network behavior remain operator concerns and must be controlled before the
run; Home AI Cluster must not add persistence or logging.

## Explicit non-goals

This investigation does not introduce or recommend:

- implementation code, an RFC, a formal Phase 17, or a runbook;
- a generic integration framework or client SDK;
- broader OpenAI compatibility, streaming, tools, function calling, model
  discovery, aliases, generation controls, or request-level infrastructure
  selection;
- client-side routing, fallback, retries, topology input, or lifecycle control;
- discovery, scheduling, load balancing, supervision, Docker, Kubernetes,
  dashboards, or databases; or
- Aider- or Cline-specific behavior in the core.

The roadmap remains complete through Phase 16. The retained two-machine
ordinary remote request proof remains a standalone post-roadmap integration
proof.

## Open questions requiring André's decision

1. Is the precise narrow composition question above worth an RFC now, given that
   Aider is already the smallest credible client foundation?
2. If it is, should the RFC consider both existing ordinary local-only and
   explicit static-cluster compositions, or only the latter needed for the
   proof, while preserving existing default compatibility behavior?
3. Should a future proof be limited to Aider's one-shot dry-run workflow, or is
   a different bounded Aider interaction required to represent the intended
   developer workflow without exposing source context?

## Evidence

Repository evidence includes the current implementation in
`openai_compatibility.py`, `static_cluster.py`, `local_runtime.py`, API wiring
and routes; [RFC-0031](../RFC/RFC-0031-minimal-openai-compatible-chat-access.md),
[RFC-0038](../RFC/RFC-0038-ordinary-static-multi-node-mode.md),
[RFC-0040](../RFC/RFC-0040-multiple-explicit-static-remote-nodes.md), and
[RFC-0045](../RFC/RFC-0045-one-shot-ordinary-request-command.md); the
[Phase 6 Aider investigation](phase-6-developer-tool-access-investigation.md)
and [proof](phase-6-aider-access-proof.md); the Phase 16 records; and the
post-roadmap ordinary remote request records.

External evidence inspected on 2026-07-18:

- [Aider OpenAI-compatible APIs](https://aider.chat/docs/llms/openai-compat.html),
  [options reference](https://aider.chat/docs/config/options.html),
  [advanced model settings](https://aider.chat/docs/config/adv-model-settings.html),
  and [v0.86.0 release](https://github.com/Aider-AI/aider/releases/tag/v0.86.0).
- [Cline OpenAI-compatible provider documentation](https://docs.cline.bot/provider-config/openai-compatible),
  [tool documentation](https://docs.cline.bot/tools-reference/all-cline-tools),
  and [telemetry documentation](https://docs.cline.bot/enterprise-solutions/monitoring/telemetry).

No private addresses, prompts, responses, source contents, usernames, machine
names, credentials, tokens, or local filesystem paths are retained in this
document.
