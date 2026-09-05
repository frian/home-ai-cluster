# RFCs

RFC stands for Request for Comments.

In Home AI Cluster, RFCs are used to document important decisions before they become architecture, protocol, or long-term project rules.

An RFC is not a blog post.

An RFC is not a TODO list.

An RFC is not documentation for users.

An RFC explains a problem, proposes a decision, records the reasoning, and makes trade-offs visible.

---

## When to write an RFC

Write an RFC when a decision may affect the long-term direction of the project.

Examples:

* core architecture;
* agent/orchestrator responsibilities;
* node discovery;
* capability model;
* runtime adapter design;
* privacy boundaries;
* security model;
* configuration format;
* protocol design;
* breaking changes;
* project governance.

Do not write an RFC for small implementation details, typos, trivial refactors, or temporary experiments.

---

## RFC status

Each RFC must have one status:

* `Draft`
* `Accepted`
* `Rejected`
* `Superseded`

A draft RFC is a proposal.

An accepted RFC becomes part of the project’s architectural memory.

A rejected RFC remains useful because it explains what was considered and why it was not chosen.

A superseded RFC has been replaced by a newer RFC.

The displayed RFC lists below are intentionally selective navigation aids. They
highlight architecturally important or currently useful decisions. The `RFC/`
directory is the complete canonical archive; omission from this selective index
does not invalidate or supersede an RFC.

## Rejected RFCs

- [RFC-0064: Bounded Public URL Summarization](RFC-0064-bounded-public-url-summarization.md)
  — considered caller-local bounded URL summarization; hostname safety could
  not be guaranteed with the existing high-level stack, and the literal-IP-only
  narrowing was not useful enough. No implementation was authorized.

## Current Draft RFCs

- [RFC-0106: Retained Local HAC Execution Limit](RFC-0106-retained-local-hac-execution-limit.md)
  — proposes one optional retained local HAC execution limit through `config
  local`; it remains receiver-owned HAC policy rather than caller-side remote
  topology or runtime capacity, and absence preserves effective limit `1`.
- [RFC-0105: Bounded HAC Execution Concurrency Limit](RFC-0105-bounded-hac-execution-concurrency-limit.md)
  — proposes one finite positive, process-local limit over active HAC-owned
  execution intervals; it is HAC policy, not runtime capacity, and `1`
  preserves the current first proof.
- [RFC-0104: Remote Pre-Execution Permission Refusal](RFC-0104-remote-pre-execution-permission-refusal.md)
  — proposes receiver-side use of the first HAC execution-permission policy,
  an explicit validated pre-execution refusal for ordered remote continuation,
  and terminal reuse of `execution-permission-denied`, without availability
  observation, runtime-capacity claims, or implementation changes.
- [RFC-0103: Local Execution Permission Failure Contract](RFC-0103-local-execution-permission-failure-contract.md)
  — proposes one distinct cluster-owned no-alternative local execution-permission
  failure, native HTTP 409 mapping, ordinary CLI exit 1, a later RFC-0034
  structured-failure extension, and truthful routing explanation without
  changing fallback or remote protocol behavior.
- [RFC-0102: Local Execution Permission Policy](RFC-0102-local-execution-permission-policy.md)
  — proposes a fixed originating-process local permission rule: zero active
  RFC-0101 intervals permits local execution; otherwise HAC may continue in
  existing static order before any attempt, or fails immediately if none remains.
- [RFC-0101: Process-Local Execution Interval Representation](RFC-0101-process-local-execution-interval-representation.md)
  — proposes one process-local quantity for the cardinality of active
  HAC-owned execution intervals in one ordinary composed HAC application
  process; it defines neither capacity nor execution policy.
- [RFC-0100: Execution Availability First-Proof Scope](RFC-0100-execution-availability-first-proof-scope.md)
  — proposes the existing local adapter-dispatch seam and one ordinary composed
  HAC application process as the first bounded execution-availability proof
  scope, without a representation or policy.
- [RFC-0099: Execution Availability Authority Boundary](RFC-0099-execution-availability-authority-boundary.md)
  — proposes HAC-owned authority over whether HAC begins a new independent
  execution, without claiming runtime-internal capacity.
- [RFC-0098: Execution Availability Semantics](RFC-0098-execution-availability-semantics.md)
  — proposes execution availability as distinct from static eligibility,
  health, status, reachability, and fallback safety.

## Selected accepted RFCs

- [RFC-0097: Supported Windows Installation Path](RFC-0097-supported-windows-installation-path.md)
  — accepts one native Windows 11 x86_64 PowerShell installation route for
  1.0: WinGet to upstream `uv`, then the ordinary HAC PyPI package and `uv`'s
  supported shell-discovery step; it adds no HAC installer or lifecycle
  ownership.
- [RFC-0096: Bounded Operator-Authorized Chat External-Information Fallback](RFC-0096-bounded-operator-authorized-chat-external-information-fallback.md)
  — accepts one separate retained Chat disclosure authorization for native
  one-shot Chat, one caller-local bounded Classify decision, and at most one
  selected RFC-0078 acquisition followed by one RFC-0077 source-grounded
  Chat request, with exact-question disclosure and no provider fallback,
  query rewriting, or interactive automatic acquisition.
- [RFC-0095: Retained External-Information Plugin Choice](RFC-0095-retained-external-information-plugin-choice.md)
  — accepts one optional retained exact RFC-0078 acquisition-plugin name as
  the baseline selection for explicit external-information operations, with
  one-invocation `--plugin` override, provider-owned credentials and
  configuration, and no startup or ordinary Chat network authority.
- [RFC-0094: Retained HAC Configuration](RFC-0094-retained-hac-configuration.md)
  — accepts one HAC-managed retained configuration for local runtime composition,
  RFC-0059 caller-local static routing capabilities, and caller-owned static
  remote topology, with explicit temporary CLI overrides and no general
  configuration framework.
- [RFC-0093: Bounded Tavily Acquisition Plugin](RFC-0093-bounded-tavily-acquisition-plugin.md)
  — accepts one separately installed Tavily acquisition plugin under unchanged
  RFC-0078, with a fixed public HTTPS destination, plugin-owned
  `TAVILY_API_KEY`, one bounded provider request, deterministic candidate
  normalization, and no automatic network authority or generic provider
  framework.
- [RFC-0092: Ordinary CLI Short Options](RFC-0092-ordinary-cli-short-options.md)
  — accepts one finite additive ordinary short-option vocabulary: root `-h`,
  `-f/--file`, `-d/--declaration`, `-l/--label`, and `-j/--json`, while
  preserving existing `-v`, all long forms, semantic behavior, and explicit
  authority-sensitive options.
- [RFC-0091: Shorter External-Information Command](RFC-0091-shorter-external-information-command.md)
  — accepts one additive --plugin NAME QUERY QUESTION spelling for explicit
  external-information use while retaining the existing
  --plugin/--query/--question form, named per-operation plugin selection,
  distinct query/question semantics, and unchanged acquisition/privacy
  boundaries.
- [RFC-0090: Ordinary Loopback Port 25042](RFC-0090-ordinary-loopback-port-25042.md)
  — moves the fixed ordinary HAC loopback convention from port 8000 to 25042
  before 0.5 while preserving loopback exposure, fixed native paths, explicit
  remote URLs, compatibility port 8001, and SearXNG port 8888.
- [RFC-0089: Explicit HTTP Base URL Shape](RFC-0089-explicit-http-base-url-shape.md)
  — accepts origin-only semantics for existing explicit remote Home AI Cluster
  and loopback llama-server HTTP base URLs while preserving their accepted
  scheme, trust, endpoint, and lifecycle boundaries.
- [RFC-0088: Bounded Ephemeral Interactive Code](RFC-0088-bounded-ephemeral-interactive-code.md)
  — accepts one TTY-only, process-owned, bounded ephemeral conversation for
  no-message native Code invocation while preserving explicit-message Code,
  RFC-0067's bound, and text-only authority.
- [RFC-0087: Bounded Ephemeral Interactive Chat](RFC-0087-bounded-ephemeral-interactive-chat.md)
  — accepts one TTY-only, process-owned, bounded ephemeral conversation for
  no-message native Chat invocation while preserving every existing one-shot
  Chat form.
- [RFC-0086: Positional Bounded Code Command Messages](RFC-0086-positional-bounded-code-command-messages.md)
  — accepts one additive positional-message alternative for bounded `code`,
  `code-file`, and `aider` commands while preserving their existing explicit
  `--message`, file-target, request, and lifecycle boundaries.
- [RFC-0085: Explicit HAC-Owned HTTP Environment Boundary](RFC-0085-explicit-hac-owned-http-environment-boundary.md)
  — isolates all HAC-owned HTTPX clients from ambient proxy and certificate
  environment configuration while preserving declared destinations and
  verifying HTTPS; excludes plugin/provider and subprocess ownership and adds
  no proxy or private-CA configuration.
- [RFC-0084: Persistent Loopback Theme Preference](RFC-0084-persistent-loopback-theme-preference.md)
  — accepts exactly one browser-local presentation preference: a System default
  plus a persisted Light or Dark override in `home-ai-cluster.theme`, without
  content, cookie, server, API, routing, capability, or exposure changes.
- [RFC-0083: Bounded Ephemeral Browser Code Conversation](RFC-0083-bounded-ephemeral-browser-code-conversation.md)
  — accepts one current-page-only ordered Code conversation in the fixed
  loopback browser, preserving one existing native `code` request per turn and
  RFC-0067's aggregate bound without persistence or new authority.
- [RFC-0082: Client-Disconnect Cancellation for Ordinary Requests](RFC-0082-client-disconnect-cancellation-for-ordinary-requests.md)
  — accepts confirmed client-disconnect cancellation of HAC-owned pending
  ordinary request work, discarding late results without guaranteeing runtime
  or transport termination.
- [RFC-0081: Explicit Code-File Target Creation](RFC-0081-explicit-code-file-target-creation.md)
  — accepts one caller-edge amendment to RFC-0080: after non-mutating
  validation, create one explicitly named missing leaf exclusively when its
  parent already exists, then retain RFC-0080's one-request replacement flow.
- [RFC-0080: One-Shot Whole-File Code Caller Edge](RFC-0080-one-shot-whole-file-code-caller-edge.md)
  — proposes one optional existing-target caller edge that sends one native
  `code` request, validates one closed content-only envelope, and atomically
  replaces only the selected file; it does not change or replace Aider.
- [RFC-0079: Fixed-Loopback SearXNG Acquisition Plugin](RFC-0079-fixed-loopback-searxng-acquisition-plugin.md)
  — accepts the first separately installed `searxng` provider plugin contract:
  one fixed loopback SearXNG JSON request with finite plugin-owned bounds before
  RFC-0078/RFC-0077 validation and unchanged ordinary `chat` routing.
- [RFC-0078: Optional External-Information Acquisition Plugin Boundary](RFC-0078-optional-external-information-acquisition-plugin-boundary.md)
  — accepts one optional explicitly selected, separately installed Python
  acquisition-plugin boundary at the one-shot caller edge before RFC-0077
  evidence validation and ordinary `chat` routing; it selects no provider and
  this acceptance change adds no implementation.
- [RFC-0077: Bounded Source-Grounded Chat](RFC-0077-bounded-source-grounded-chat.md)
  — proposes a bounded, provider-neutral evidence/request/result seam for
  ordinary `chat`, with source provenance distinct from generated citation
  correctness; it authorizes no acquisition or implementation.
- [RFC-0075: Retire Historical Proof Launchers](RFC-0075-retire-historical-proof-launchers.md)
  — retires four installed historical proof-only launchers while preserving
  ordinary architecture and retained historical evidence.
- [RFC-0074: Explicit Local Runtime Composition File](RFC-0074-explicit-local-runtime-composition-file.md)
  — accepts one optional explicitly selected, closed TOML file for local
  runtime-adapter construction while preserving CLI-only startup and all
  cluster-facing behavior.
- [RFC-0073: Explicit Ollama Thinking Disable](RFC-0073-explicit-ollama-thinking-disable.md)
  — accepts one optional Ollama-only process-local startup flag that requests
  `think: false` while leaving requests, routing, and result privacy unchanged.
- [RFC-0072: Bounded Aider Follow-Up Request](RFC-0072-bounded-aider-follow-up-request.md)
  — accepts one optional Aider-owned qualifying follow-up after a successful
  first translated result, while keeping the caller edge to at most two native
  `capability=code` requests per invocation.
- [RFC-0071: Explicit Ollama Model Selection](RFC-0071-explicit-ollama-model-selection.md)
  — accepts one optional ordinary Ollama model value that remains process-local
  and adapter-owned, while requests, routing, and declarations stay
  capability-centered and model-independent.
- [RFC-0070: Minimal Loopback Code View](RFC-0070-minimal-loopback-code-view.md)
  — accepts one fourth fixed loopback browser view for the existing bounded
  textual `code` capability, reusing native `/v1/chat` without adding a new
  endpoint, authority, or compatibility surface.
- [RFC-0069: Explicit Aider Target Creation](RFC-0069-explicit-aider-target-creation.md)
  — accepts one narrowly bounded caller-edge authority to create the explicitly
  named missing Aider target as an empty non-overwriting file after prerequisites
  pass, while preserving Aider-owned content edits and HAC core text-only authority.
- [RFC-0068: One-Shot Aider Code Caller Edge](RFC-0068-one-shot-aider-code-caller-edge.md)
  — accepts one optional Aider-specific one-shot caller edge that coordinates
  external Aider with a private loopback translation to explicit native `code`,
  while keeping target edits caller-owned and RFC-0031 Chat-only.
- [RFC-0067: Bounded Textual Code Assistance](RFC-0067-bounded-textual-code-assistance.md)
  — accepts one explicit bounded textual `code` capability using the shared
  ordered-message representation and existing Chat-like execution mechanics,
  without tools or execution authority.
- [RFC-0066: Capability Admission Semantics](RFC-0066-capability-admission-semantics.md)
  — accepts a closed, explicit, model-independent admission rule for future
  capability proposals without authorizing a new capability or implementation.
- [RFC-0065: Browser-Local PDF Text Input for Summarize](RFC-0065-browser-local-pdf-text-input-for-summarize.md)
  — accepts one 8 MiB-bounded browser-local PDF.js preprocessing path for the
  existing Summarize textarea and unchanged text-only request.
- [RFC-0063: Classify Local Text File Input](RFC-0063-classify-local-text-file-input.md)
  — accepts one browser-local UTF-8 text-file convenience for Classify while
  preserving the existing JSON contract and exposure boundaries.
- [RFC-0062: Minimal Loopback Web Client](RFC-0062-minimal-loopback-web-client.md)
  — accepts one fixed same-origin browser client over existing native
  capabilities, without changing network exposure.
- [RFC-0061: Bounded Text Classification](RFC-0061-bounded-text-classification.md)
  — accepts one bounded `classify` capability with an exact operator-supplied
  selected-label result and explicit static eligibility.
- [RFC-0060: Explicit Native Client Timeout](RFC-0060-explicit-native-client-timeout.md)
  — accepts one shared finite per-invocation timeout for ordinary native clients
  while preserving the 120.0-second default and existing timeout ownership
  boundaries.
- [RFC-0059: Caller-local static capabilities](RFC-0059-caller-local-static-capabilities.md)
  — accepts bounded caller-local routing capabilities for ordinary static
  clusters while preserving local-first routing and receiver behavior.
- [RFC-0058: Explicit static remote capabilities](RFC-0058-explicit-static-remote-capabilities.md)
  — accepts bounded operator-declared capabilities for ordinary static remote
  nodes while preserving existing routing and compatibility boundaries.

---

## File naming

RFC files should use this format:

```text
RFC-0001-title.md
RFC-0002-title.md
RFC-0003-title.md
```

Use lowercase words separated by hyphens.

The number never changes.

---

## RFC template

```md
# RFC-0000: Title

Status: Draft

Date: YYYY-MM-DD

Author: Name or GitHub handle

## Summary

A short explanation of the proposal.

The summary should be understandable without reading the whole RFC.

## Problem

What problem are we trying to solve?

Why does this problem matter?

What happens if we do nothing?

## Goals

What should this RFC achieve?

## Non-goals

What is deliberately outside the scope of this RFC?

## Proposal

What are we proposing?

Describe the decision clearly.

Avoid implementation details unless they are essential to the decision.

## Rationale

Why this proposal?

Why is it better than the alternatives?

What project principles does it support?

## Alternatives considered

What other options were considered?

Why were they not chosen?

## Trade-offs

What does this proposal make easier?

What does it make harder?

What complexity does it introduce?

Why is that complexity acceptable?

## Impact

What documents, architecture, or future implementation work does this affect?

Does it affect users?

Does it affect developers?

Does it affect future compatibility?

## Open questions

What is still undecided?

What needs more research or discussion?

## Decision

For accepted or rejected RFCs, summarize the final decision here.

For drafts, leave this section empty or write:

Pending.
```

---

## Rules

RFCs should be clear, boring, and explicit.

A good RFC makes disagreement easier.

A good RFC explains trade-offs.

A good RFC can be understood months later by someone who was not part of the original discussion.

If an architectural decision cannot be explained in an RFC, it is not ready.
