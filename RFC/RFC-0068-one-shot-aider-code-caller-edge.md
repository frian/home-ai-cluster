# RFC-0068: One-Shot Aider Code Caller Edge

Status: Draft

Date: 2026-08-13

Author: frian

## Summary

Home AI Cluster should add one optional, Aider-specific, one-shot caller/access
edge:

```text
hac aider --file PATH --message TEXT
home-ai-cluster aider --file PATH --message TEXT
```

The edge would coordinate one already-installed Aider 0.86.2 invocation with
one ephemeral private loopback translator. The translator would accept at most
one strict Aider-shaped request, send exactly one existing native `POST
/v1/chat` request with explicit `capability=code`, project one minimal response,
and stop. Aider would retain target-file reading and editing authority.

This is not cluster core, general developer-tool support, OpenAI compatibility
expansion, a persistent bridge, or HAC filesystem or execution authority.

## Problem

The retained one-machine Aider proof established the narrow no-copy/paste
small-script outcome: one explicit native `code` request returned text and
Aider used it to edit one disposable caller-owned file. The temporary bridge
and Aider configuration were deliberately proof-only, however, leaving an
ordinary operator to reconstruct temporary configuration, listener lifecycle,
and cleanup for every use.

Existing `hac code` is the smallest native text-only interface, but it does not
own an external caller's file-edit action. Existing RFC-0031 compatibility is
deliberately Chat-only and cannot truthfully select `code`. The project needs a
small decision about whether and how to support the proven concrete caller
composition without creating a general developer agent.

## Goals

- Make the proven one-shot Aider composition practical for ordinary small-script
  work.
- Preserve explicit `code` semantics, engine-independent cluster routing, and
  existing native `POST /v1/chat` ownership.
- Keep Aider target-file authority outside HAC core.
- Keep translation private, ephemeral, loopback-only, strict, and finite.
- Make prerequisite failures, request failure, cleanup, and ownership clear.
- Avoid a generic developer-tool abstraction or compatibility expansion.

## Non-goals

This RFC does not authorize generic developer-tool integration, generic OpenAI
compatibility, a persistent bridge/server, multiple model requests, interactive
Aider, multiple targets, target creation, repository indexing or repo maps,
Git, shell, tests, lint execution, generated-code execution, tools/functions,
agents, autonomy, browser Code UI, a dashboard, plugin framework, SDK,
model/runtime/node selection or discovery, web retrieval, RAG/embeddings,
persistence/database, Docker/Kubernetes, or Aider installation/update
management.

It does not complete the physical two-machine RFC-0067 proof.

## Proposal

### Concrete optional caller edge

The supported edge is specifically Aider, not a generic provider, plugin, or
subprocess framework. It is project-owned caller/access mechanics, not HAC core
semantics. The core continues to own explicit `code` validation, eligibility,
routing, native `/v1/chat`, textual `ClusterResult`, and internal attribution.

The initial ordinary root surface is exactly `hac aider --file PATH --message
TEXT` and its `home-ai-cluster aider` equivalent. It adds no standalone
`home-ai-cluster-aider` script and no generic `code-edit` command.

The command accepts exactly one existing caller-selected target file and one
explicit non-blank message. It does not create targets, accept multiple files,
read target contents for semantic processing, modify the target, parse or apply
a patch, inspect repository semantics, read a message from stdin/files, or
conduct a conversation. An operator may create an empty target before invoking
the edge. Aider alone reads and edits the target under normal operator OS/user
authority; this operational scope is not a security sandbox.

### One-shot lifecycle and existing process ownership

One invocation has this bounded lifecycle:

```text
validate local prerequisites
  -> create private temporary integration configuration
  -> start one ephemeral 127.0.0.1 translator
  -> directly invoke external Aider once
  -> accept at most one qualifying request
  -> make exactly one native HAC request
  -> project one response and stop translator
  -> remove temporary integration material and exit
```

There is no daemon, background service, persistent bridge, session, project
retry, or fallback to Chat. Aider's second qualifying request is rejected and
fails the invocation.

The edge neither starts, stops, supervises, restarts, discovers, nor configures
HAC. It expects the same already-running ordinary native caller endpoint as
existing native one-shot commands. It works with either `hac local` or `hac
static-cluster`; Aider selects no node, remote, runtime, adapter, or concrete
model. Existing explicit capability eligibility, local-first behavior, remote
order, fallback, and attribution remain cluster-owned.

### Private strict ingress and native translation

The launcher privately selects an IPv4 loopback port and passes its base URL
only to its Aider subprocess. The translator is not `hac compatibility`, is not
separately startable, and is not LAN-accessible, public, persistent,
discoverable, or a general OpenAI API.

It accepts exactly one `POST /v1/chat/completions` request with top-level fields
exactly `model, messages`, optionally plus `stream`. The model is exactly
`home-ai-cluster`; stream is absent or `false`; messages are non-empty; and each
message has exactly non-empty plain-string `content` plus `system`, `user`, or
`assistant` `role`. An Authorization header may be absent or syntactically
Bearer-prefixed; it is neither authentication nor authorization and is never
retained or forwarded. Unknown fields, streaming, tools, functions, generation
parameters, multimodal content, model discovery, and a second request fail
closed rather than being discarded.

For the one accepted request, the translator preserves ordered messages and
makes exactly one native request equivalent to:

```text
POST /v1/chat
messages: <preserved ordered plain-text messages>
capability: code
```

It calls no runtime directly, duplicates no routing, selects no node/runtime/
model, never downgrades to Chat, and never infers a capability from content.
RFC-0067's existing aggregate 65,536-byte validation remains authoritative; no
second code-input limit is introduced.

The response is only the proven minimal non-streaming Aider-shaped projection:
opaque completion id, fixed `chat.completion`, caller-edge timestamp, fixed
`home-ai-cluster` endpoint identifier, exactly one assistant choice containing
HAC textual content, and `finish_reason: null`. It exposes no node, adapter,
runtime, concrete model, routing explanation, token accounting, usage, or extra
compatibility fields. This private projection does not change RFC-0031.

### External Aider and conservative execution

Aider is an optional external prerequisite, not a HAC Python dependency. The
initial supported version is exactly Aider 0.86.2. A missing executable or a
different reported version fails before a model or HAC request. Later compatible
versions may be added only after confirming the same bounded request shape and
guardrail behavior; a new RFC is required only when that changes this
architectural contract. A local version-only check may be used and contacts no
model or network service. The edge neither installs nor updates Aider.

The launcher invokes only the installed `aider` executable directly: no shell,
arbitrary executable path, or pass-through arguments. Its fixed invocation
enforces the proven conservative behavior: non-streaming; whole-file edit
representation; no temperature field; no Git or auto-commit; no automatic
lint/test; no file watching; no shell command suggestions/execution; no URL or
browser tooling; no GUI, analytics, update/release checks, notifications, or
prompt cache; no retained input/chat/LLM history; no project `.env` loading;
and one supplied target and message. These guardrails are not a sandbox.

### Authority, temporary files, privacy, and failures

Three authority domains remain distinct:

| Domain | May do | Must not do |
| --- | --- | --- |
| HAC core/execution | Validate `code`, route, invoke selected text adapter, return text | Access files/repositories; launch shell; run Git/tests/lint; execute code; invoke tools/functions |
| Project-owned caller edge | Check bounded prerequisites; create/remove its own temporary integration material; bind one private translator; launch fixed Aider; wait, report bounded outcome, and clean up | Read/write target as editor; inspect repository semantics; execute generated code; invoke arbitrary shell; run Git/tests/lint; select HAC execution; persist prompt/response |
| Aider | Read explicit target, interpret returned text, apply edit | Become HAC or cluster authority |

Temporary integration configuration is private, outside the target workspace
when practical, not project or operator configuration, not persistence, and is
removed on success and failure. No database or permanent configuration is
added.

By default the edge persists and logs no prompt, target content, generated
content, Authorization placeholder, raw HAC response, or private path beyond
what a live local process unavoidably receives. Explicit Aider terminal output
remains caller-visible process output, not HAC persistence. Small
operator-safe structural failures are allowed.

Failures fail closed and exit non-zero: missing/unsupported Aider, invalid
arguments, listener-bind failure, unsupported/second request, unavailable or
timed-out HAC, no eligible `code`, native non-success or malformed success,
unsuccessful Aider exit, and cleanup failure. There is no automatic retry or
large public error taxonomy. The single HAC request uses RFC-0060's bounded
per-invocation timeout range and 120-second omission default; it is not an
Aider-process deadline or cancellation contract.

### Compatibility and physical-proof boundaries

RFC-0031 remains Chat-only. This RFC adds no `code` compatibility model,
endpoint, field, alias, prompt mapping, `/v1/code`, `/v1/models`, streaming, or
tools/functions. The Aider-shaped ingress is private one-shot caller-edge
mechanics, not a compatibility expansion.

The physical two-machine RFC-0067 `code` proof remains pending. This edge must
preserve ordinary static routing so a later physical proof can use the same
native `code` semantics, but the proof obligations are independent.

## Rationale

The real proof establishes that one request and one caller-owned edit are
sufficient for the stated small-script goal. A project-owned launcher removes
the remaining temporary-bridge lifecycle friction that a bridge alone leaves to
the operator, while keeping the only file action in Aider. A fixed concrete
caller is more honest and smaller than a generic developer-tool abstraction.

The private strict translation preserves the cluster's existing capability and
routing value: it can route to an eligible explicitly declared `code` node
without Aider selecting an execution detail. It is narrower than persistent
compatibility and does not turn a model-like field into a capability selector.

## Alternatives considered

### Keep the proof/runbook only

Rejected. It proves feasibility but leaves repeated temporary configuration and
lifecycle work that is disproportionate to the small-script use case.

### Document an operator-owned reusable helper

Rejected. It can help an individual operator, but it leaves a private and
unsupported protocol/lifecycle contract and only relocates much of the setup.

### Ship only a strict bridge

Rejected. The operator would still coordinate bridge, configuration, Aider, and
cleanup; that does not remove the proven operational friction.

### Persistent or multi-request bridge

Rejected. Current evidence needs one request only. Sessions would add lifetime,
state, retries, recovery, shutdown, privacy, and request-shape commitments.

### Expand RFC-0031 compatibility for `code`

Rejected. It would change the accepted Chat-only contract and risk model/prompt
capability mapping solely to remove a private caller edge.

### Generic developer-tool abstraction

Rejected. Aider is the only investigated and proven caller; abstraction would
create a framework before a second concrete need exists.

### Let HAC edit files

Rejected. RFC-0067 accepts text only. Moving Aider's authority into HAC would
expand filesystem, repository, process, and trust boundaries.

## Trade-offs

This introduces a maintained dependency boundary on one external tool, a small
subprocess lifecycle, private ephemeral protocol projection, temporary
caller-edge filesystem use, and maintenance when Aider's request shape changes.
Those costs are bounded by the exact version, one request, loopback-only
listener, and no-persistence contract. They are smaller than persistent
compatibility or granting HAC file/tool authority.

## Impact and proof expectations

After acceptance, a separate implementation PR may add only the command and
caller-edge mechanics needed by this contract, focused tests, documentation,
and privacy-safe proof material. It must leave RFC-0067 behavior, existing
native surfaces, routing, RFC-0031 compatibility, browser, and core authority
unchanged.

A later implementation/proof must establish missing/unsupported Aider failure
before a model/HAC request; one successful invocation; exactly one accepted
Aider-shaped and native `code` request; an Aider-owned selected-target edit with
no other workspace edit; no generated-code execution, Git/test/lint/shell
automation, second request, or prompt/response persistence; cleanup after
success and representative failure; loopback-only listener; ordinary local and
topology-blind static-cluster operation; and the still-pending physical
RFC-0067 proof as a separate obligation. Retained evidence remains privacy-safe.

## Open questions

None within the proposed first contract. Implementation details that do not
change this contract belong to a later implementation PR.

## Decision

Pending.
