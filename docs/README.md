# Documentation Index

Status: Current

This index provides a human-readable path through Home AI Cluster documentation.
It separates current operator guidance from chronological project records without
renaming or moving existing files.

Architectural decisions remain indexed separately in
[the RFC index](../RFC/README.md). Accepted RFCs, not this index, define the
architecture.

## Start here

- [Project README](../README.md) — current project shape and basic commands.
- [Command reference](command-reference.md) — current lookup reference for
  ordinary installed commands, common forms, options, and boundaries.
- [Roadmap](../ROADMAP.md) — completed phases and future direction.
- [Canonical operator workflow](operator-workflow.md) — shortest supported
  operator path.
- [RFC index](../RFC/README.md) — proposed and accepted architectural decisions.

## Release and distribution

- [1.0 CLI contract candidate investigation](v1.0-cli-contract-candidate-investigation.md)
  — inventories the current ordinary CLI and retained compatibility surfaces as
  a 1.0 candidate; it distinguishes candidate stable contracts from private or
  flexible behaviour and records unresolved compatibility questions without
  making a policy decision.
- [v0.9 privacy and authority boundaries investigation](v0.9-privacy-authority-boundaries-investigation.md)
  — inventories current persistence, network, filesystem, process, plugin, and
  observation authority against accepted contracts; it changes no behavior and
  identifies only focused evidence gaps.
- [Release direction to 1.0](release-direction-to-1.0.md)
  — records the non-binding product-maturity direction from `0.5` through
  `1.0.0`; it is not a roadmap, backlog, implementation authorization, or
  architectural decision.
- [v0.3.0 release-readiness investigation](v0.3.0-release-readiness-investigation.md)
  — documents the current-main comparison with `v0.2.0`; one small Ruff
  formatting follow-up is required before a `0.3.0` preparation PR.
- [Future PyPI release process investigation](future-pypi-release-process-investigation.md)
  — documents the smallest recommended future stable-release process; it
  authorizes no workflow, version, tag, publication, or external change.
- [PyPI release-readiness investigation](pypi-release-readiness-investigation.md)
  — documentation-only evidence that the historical `v0.2.0` artifacts build
  and install cleanly, while a small protected Trusted Publishing preparation
  change is needed before first publication; it authorizes no publication.

## Operator entry points

- [HAC-owned proxy environment boundary investigation](hac-owned-proxy-environment-boundary-investigation.md)
  — documentation-only HTTPX inventory and controlled proxy evidence for a
  possible future explicit boundary; it authorizes no RFC or implementation.
- [Command reference](command-reference.md) — current lookup reference for
  ordinary installed commands, common forms, options, and boundaries.
- [Canonical operator workflow](operator-workflow.md) — current ordinary
  local-only and explicit static-cluster operation, including human-readable
  inspection defaults and explicit structured `--json` forms.
- [Loopback web client proof](loopback-web-client-proof.md) — retained
  privacy-safe evidence and current boundary for the accepted minimal browser
  surface.
- [Explicit Ollama model selection investigation](explicit-ollama-model-selection-investigation.md)
  — documents the adapter-owned, capability-centered seam for a possible
  per-node Ollama model argument; it authorizes no implementation or RFC.
- [Explicit Ollama model selection proof](explicit-ollama-model-selection-proof.md)
  — retains one real-local RFC-0071 observation that an already-installed
  explicitly selected Ollama model handled one native model-free `code` request.
- [Explicit Ollama thinking disable proof](explicit-ollama-thinking-disable-proof.md)
  — retains one privacy-safe real-local RFC-0073 observation that explicit
  Ollama thinking disable let a bounded Aider workflow complete in roughly one
  to two minutes after comparable default-thinking runs exceeded finite waits.
- [Explicit local runtime composition file proof](explicit-local-runtime-composition-file-proof.md)
  — retains one privacy-safe real-local RFC-0074 observation that an explicitly
  selected runtime-composition file reached an already-installed local Ollama
  path and rejected an explicit second composition source before startup.
- [Runtime reasoning control investigation](runtime-reasoning-control-investigation.md)
  — evaluates whether one narrowly scoped Ollama process-local reasoning control
  needs an RFC while preserving model-independent requests, routing, and privacy.
- [Local runtime composition configuration investigation](local-runtime-composition-config-investigation.md)
  — evaluates whether one explicit retained process-local runtime-composition
  file now warrants an RFC; it authorizes no implementation or configuration
  contract.
- [Aider whole-file edit reliability investigation](aider-whole-file-edit-reliability-investigation.md)
  — records the Aider 0.86.2 source-level explanation for an unchanged-target
  observation; it authorizes no caller-edge, model, or filesystem change.
- [Aider single-target boundary investigation](aider-single-target-boundary-investigation.md)
  — finds that Aider 0.86.2 treats the supplied file as its initial editable
  set and can default-confirm a model-named extra path; its original
  `yes-always: false` enforcement analysis is corrected by the follow-up.
- [Aider single-target fail-closed corrective investigation](aider-single-target-fail-closed-corrective-investigation.md)
  — corrects the ConfigArgParse analysis after PR #499 and establishes a
  model-free Aider 0.86.2 stdin-based fail-closed repair direction; it
  supersedes the earlier document only on that failed enforcement analysis and
  authorizes no implementation.
- [Aider single-target fail-closed proof](aider-single-target-fail-closed-proof.md)
  — retains model-free real-Aider 0.86.2 evidence that the implemented private
  continuous-No child input preserves the selected edit while rejecting
  unselected existing and missing paths.
- [Aider post-edit summarization investigation](aider-post-edit-summarization-investigation.md)
  — documents model-free Aider 0.86.2 lifecycle evidence after PR #501:
  automatic post-edit summary can race one-shot shutdown and exceed the
  two-request edge; no deterministic compliant suppression guardrail is known.
- [Aider upstream post-0.86.2 lifecycle investigation](aider-upstream-post-0862-lifecycle-investigation.md)
  — finds Outcome D: the latest published release remains 0.86.2 and pinned
  upstream main preserves the same summary lifecycle, duplicate fallback, and
  lack of a supported disable switch; it authorizes no version or implementation
  change.
- [Single-file code caller investigation](single-file-code-caller-investigation.md)
  — finds Outcome B: a content-only, one-request whole-file caller is smaller
  than Aider for one selected small script; it authorizes no replacement and
  recommends an RFC before any change.
- [Bounded web retrieval investigation](bounded-web-retrieval-investigation.md)
  — evaluates the smallest explicit caller-local public-URL retrieval boundary;
  it authorizes no network access, capability, endpoint, or browser change.
- [Post-RFC-0064 external information access investigation](post-rfc-0064-external-information-access-investigation.md)
  — records Outcome C: a fixed-provider boundary is a focused future
  investigation candidate, but current evidence authorizes neither an RFC nor
  implementation; operator-owned retrieval remains the supported baseline and
  automatic/model-directed retrieval remains deferred.
- [Fixed-provider Chat information investigation](fixed-provider-chat-information-investigation.md)
  — finds that one explicit fixed-provider acquisition plus a bounded
  source-grounded ordinary Chat contract warrants a narrow RFC before any
  implementation; it selects no provider and adds no network authority.
- [Source-grounded Chat proof](source-grounded-chat-proof.md)
  — retains two privacy-safe real-local observations of implemented RFC-0077:
  useful bounded evidence use and one favorable but non-generalizable
  instruction-like hostile-source result, with supplied-source provenance kept
  distinct from claim-level correctness.
- [RFC-0078 installed-plugin boundary proof runbook](external-information-plugin-boundary-proof-runbook.md)
  — repeatable privacy-safe procedure for observing one temporary separately
  installed acquisition-plugin entry point without bundling or publishing a
  provider.
- [RFC-0078 installed-plugin boundary proof](external-information-plugin-boundary-proof.md)
  — retains real metadata, lazy-load, exact-query, and cleanup observations;
  no live HAC server was available, so it records no successful end-to-end
  source-grounded result.
- [RFC-0079 SearXNG acquisition plugin live-proof runbook](searxng-acquisition-plugin-proof-runbook.md)
  — repeatable privacy-safe procedure for the separately installed fixed
  loopback SearXNG plugin through the real RFC-0078/RFC-0077/ordinary Chat path;
  it does not claim that the live proof has occurred.
- [RFC-0079 SearXNG acquisition plugin proof](searxng-acquisition-plugin-proof.md)
  — retains privacy-safe structural evidence that the real separately installed
  plugin completed the fixed-loopback acquisition path through ordinary Chat;
  it does not establish provider, source, or answer correctness.
- [SearXNG acquisition plugin investigation](searxng-acquisition-plugin-investigation.md)
  — finds Outcome C: an operator-owned private SearXNG service has a small
  enough provider-specific shape to justify a dedicated RFC, while authorizing
  no provider implementation, service lifecycle, network authority, or
  architectural decision.
- [Operator-controlled Web discovery investigation](operator-controlled-web-discovery-investigation.md)
  — finds Outcome B: an independently operated private SearXNG service is a
  credible future RFC candidate for bounded discovery, but HAC must not own its
  lifecycle; operator-owned retrieval remains supported and no implementation
  or search-service abstraction is authorized.
- [Operator-controlled Web discovery proof](operator-controlled-web-discovery-proof.md)
  — retains one privacy-safe operator observation that private SearXNG can
  return useful but untrusted current-information snippets without URL fetching;
  it records imperfect model source attribution and authorizes no integration.
- [Optional external integration plugin investigation](optional-external-integration-plugin-investigation.md)
  — finds Outcome B: one explicit, entry-point-discovered acquisition plug-in
  category is credible for a future RFC feeding RFC-0077, while no plug-in
  system, provider selection, acquisition, or implementation is authorized.
- [Bounded local PDF text extraction investigation](bounded-local-pdf-text-extraction-investigation.md)
  — finds current operator-owned extraction sufficient for the existing bounded
  Summarize and Classify text-input paths; it authorizes no PDF feature or
  document-ingestion contract.
- [Browser-local PDF extraction investigation](browser-local-pdf-extraction-investigation.md)
  — identifies a narrowly vendored PDF.js main/worker pair as a credible future
  browser-only preprocessing seam; it authorizes no implementation or RFC.
- [Classify local text-file input investigation](classify-local-text-file-investigation.md)
  — evaluates a narrowly bounded browser-local text-file convenience for
  Classify; it does not authorize an implementation or alter RFC-0062.
- [Minimal local web client investigation](minimal-local-web-client-investigation.md)
  — documentation-only investigation of a browser surface for the existing
  native capabilities; it does not authorize a UI or architectural change.
- [Daily operator workflow investigation](daily-operator-workflow-investigation.md)
  — bounded investigation of repeatable local role operation; not a proposal or
  accepted workflow change.
- [Ordinary daily-use friction investigation](ordinary-daily-use-friction-investigation.md)
  — documentation-only evaluation of ordinary local and one-receiver static
  operation after the retained remote summarize-file proof.
- [Daily operator workflow evidence protocol](daily-operator-workflow-evidence-protocol.md)
  — privacy-safe protocol for gathering operator workflow evidence; not a
  proof, accepted workflow, or Phase 17 plan.
- [Daily operator workflow evidence result](daily-operator-workflow-evidence-result.md)
  — retained privacy-safe evidence from one native two-machine daily workflow
  exercise; not an accepted workflow change or Phase 17 plan.
- [Human-readable operator output investigation](human-readable-operator-output-investigation.md)
  — investigated the bounded presentation need for existing finite operator
  commands that led to RFC-0048; it is not itself the architectural decision.
- [Static two-machine proof runbook](static-two-machine-proof.md) — retained
  historical LAN procedure; its launcher was retired by RFC-0075 and exact
  reproduction requires the historical repository revision.
- [First two-machine proof result](first-two-machine-proof-result.md) — retained
  result of the founding real two-machine proof.

The canonical operator workflow is the current supported path. The other entries
in this section are historical proof references. They describe what was
established at a specific stage and do not replace the current workflow.

## Project history

### RFC-0064 — Bounded public URL summarization

- [RFC-0064 HTTP client boundaries investigation](rfc-0064-http-client-boundaries-investigation.md)
  — preserves the HTTPX, Python, and controlled-transport evidence that led to
  RFC-0064's rejection: the hostname-safe contract was not established, and
  the literal-IP-only narrowing was not useful enough. It authorizes no
  retrieval implementation.

### Phase 1 — Single-machine orchestrator

- [Phase 1 current state](phase-1-current-state.md) — descriptive snapshot of the
  first ordinary single-machine shape.

### Phase 2 — Agent and node model

- [Phase 2 starting state](phase-2-starting-state.md) — historical starting
  snapshot.
- [Phase 2 current state](phase-2-current-state.md) — later descriptive snapshot
  of the accepted static node and agent boundaries.

### Founding multi-machine proof

- [Static two-machine proof runbook](static-two-machine-proof.md) — repeatable
  proof procedure.
- [First two-machine proof result](first-two-machine-proof-result.md) — retained
  successful real execution.
- [Retained proof scaffolding investigation](retained-proof-scaffolding-investigation.md)
  — documentation-only inventory of historical proof surfaces, their ordinary
  replacements, and the RFC boundary for any later retirement decision.

### Phase 6 — OpenAI-compatible access

- [OpenAI compatibility proof](phase-6-openai-compatibility-proof.md) — retained
  proof of the deliberately narrow compatibility endpoint.
- [Developer tool access investigation](phase-6-developer-tool-access-investigation.md)
  — investigation of ordinary tool access.
- [Aider access proof](phase-6-aider-access-proof.md) — retained real Aider
  integration evidence.
- [Aider static-cluster access investigation](aider-static-cluster-access-investigation.md)
  — concludes that the existing declaration-backed compatibility composition
  already supports the bounded Aider-to-declared-remote proof without a new
  contract or implementation.
- [Aider static-cluster compatibility proof](aider-static-cluster-proof.md) —
  retained privacy-safe evidence of one bounded two-machine Aider execution.

### Phase 8 — Operable local cluster

- [Phase 8 current state](phase-8-current-state.md) — descriptive state after the
  operability work.
- [Canonical operator workflow proof](phase-8-canonical-operator-workflow-proof.md)
  — retained workflow evidence.
- [Ordinary static multi-node proof](phase-8-ordinary-static-multi-node-proof.md)
  — retained ordinary-mode proof record.

### Phase 10 — Multiple explicit static remote nodes

- [Multiple static remote nodes proof](phase-10-multiple-static-remote-nodes-proof.md)
  — retained real multi-node evidence.
- [Phase 10 closeout](phase-10-closeout.md) — completion summary.

### Phase 11 — Explicit static cluster status

- [Explicit static cluster status proof](phase-11-explicit-static-cluster-status-proof.md)
  — retained normalized status evidence.
- [Phase 11 closeout](phase-11-closeout.md) — completion summary.

### Phase 12 — Heterogeneous runtime cluster proof

- [Heterogeneous runtime cluster proof](phase-12-heterogeneous-runtime-cluster-proof.md)
  — retained engine-independent cluster evidence; its historical launcher was
  retired by RFC-0075.
- [Phase 12 closeout](phase-12-closeout.md) — completion summary.

### Phase 13 — Explicit local runtime composition

- [Explicit local runtime composition proof](phase-13-explicit-local-runtime-composition-proof.md)
  — retained ordinary-node composition evidence.
- [Phase 13 closeout](phase-13-closeout.md) — completion summary.

### Phase 14 — Explicit static-cluster local composition

- [Static-cluster local composition proof](phase-14-static-cluster-local-composition-proof.md)
  — retained ordinary static-cluster evidence.
- [Phase 14 closeout](phase-14-closeout.md) — completion summary.

### Phase 15 — Explicit static-cluster status composition

- [Static-cluster status composition investigation](phase-15-static-cluster-status-composition-investigation.md)
  — evidence and recommendation before RFC-0044.
- [Static-cluster status composition proof](phase-15-static-cluster-status-composition-proof.md)
  — retained real status evidence.
- [Phase 15 closeout](phase-15-closeout.md) — completion summary.

### Phase 16 — Ordinary operator request access

- [Ordinary operator request access investigation](phase-16-ordinary-operator-request-access-investigation.md)
  — identified the smallest ordinary operator access path and established the
  need for RFC-0045.
- [Ordinary request access proof runbook](phase-16-ordinary-request-access-proof-runbook.md)
  — planned the real operator procedure and does not itself claim proof
  execution.
- [Ordinary request access retained proof](phase-16-ordinary-request-access-proof.md)
  — retains privacy-safe real observations of unavailable ordinary process,
  local-only success, runtime-unavailable failure, and explicit static-cluster
  success; the static-cluster observation selected `local`.
- [Phase 16 closeout](phase-16-closeout.md) — completion record for the bounded
  one-shot ordinary request access phase.

### Phase 17 — Human-readable operator inspection output

- [Human-readable operator output investigation](human-readable-operator-output-investigation.md)
  — investigation of the bounded presentation need that preceded the accepted
  decision.
- [Human-readable inspection output proof runbook](phase-17-human-readable-inspection-output-proof.md)
  — reusable procedure for collecting bounded presentation evidence.
- [Human-readable inspection output retained proof result](phase-17-human-readable-inspection-output-proof-result.md)
  — privacy-safe record of the completed live and automated proof evidence.
- [Phase 17 closeout](phase-17-closeout.md) — completion record for the bounded
  human-readable inspection output phase.

### Phase 18 — Bounded text summarization

- [Second capability investigation](second-capability-investigation.md) —
  investigated the smallest credible second executable capability before
  RFC-0051.
- [Remote summarize file proof investigation](remote-summarize-file-proof-investigation.md)
  — investigation of one standalone post-roadmap composition of regular-file
  input, ordinary static fallback, remote summarize execution, and
  caller-owned attribution; it does not run or retain that proof.
- [Remote summarize file proof runbook](remote-summarize-file-proof-runbook.md)
  — privacy-safe procedure for the standalone remote summarize-file integration
  proof.
- [Remote summarize file proof](remote-summarize-file-proof.md) — retained
  privacy-safe result of one real two-machine `hac summarize --file` execution
  through accepted local-first remote fallback.
- [Phase 18 two-machine summarize proof runbook](phase-18-two-machine-summarize-proof.md)
  — repeatable privacy-safe procedure for the bounded real two-machine
  summarize proof.
- [Phase 18 two-machine summarize retained proof result](phase-18-two-machine-summarize-proof-result.md)
  — retained privacy-safe evidence from the completed real two-machine remote
  and local-first summarize observations.
- [Phase 18 closeout](phase-18-closeout.md) — completion record for the bounded
  second executable capability phase.
- [Heterogeneous static capabilities investigation](heterogeneous-static-capabilities-investigation.md)
  — standalone documentation-only investigation that distinguishes capability
  eligibility from scheduling and records an Outcome C contract gap.
- [Heterogeneous static capabilities proof](heterogeneous-static-capabilities-proof.md)
  — retained ordinary process-and-HTTP proof that explicit remote capability
  declarations control eligibility without changing local-first routing.
- [Local capability ownership investigation](local-capability-ownership-investigation.md)
  — standalone documentation-only investigation of the contract gap for
  restricting fixed local-node routing capabilities.
- [Caller-local static capabilities proof](caller-local-static-capabilities-proof.md)
  — retained ordinary process-and-HTTP proof that a healthy chat-only caller-local
  candidate excludes summarize before selection and reaches a summarize-only
  declared remote.
- [Post-RFC-0059 next gap investigation](post-rfc-0059-next-gap-investigation.md)
  — standalone documentation-only investigation concluding Outcome A: no
  justified follow-up gap is currently established.
- [Explicit remote capabilities investigation](explicit-remote-capabilities-investigation.md)
  — documents the accepted RFC-0058 operator-declared remote capability
  contract and its relevance before any third executable capability.
- [Third executable capability investigation](third-executable-capability-investigation.md)
  — compares `rewrite`, `question-answer`, and `classify`; it selects
  `classify` as investigation guidance for a future RFC, not an accepted change.
- [Native client timeout configurability investigation](native-client-timeout-configurability-investigation.md)
  — standalone documentation-only investigation prompted by a sanitized
  repeated slow-remote request observation; it records Outcome C and requires
  an RFC before any timeout behavior can change.
- [Native client timeout override proof](native-client-timeout-override-proof.md)
  — retained privacy-safe evidence that one real slow-but-valid routed
  summarize request completed with the accepted per-invocation client override.

### RFC-0061 — Bounded text classification

- [Bounded classification proof](bounded-classification-proof.md) — retained
  privacy-safe evidence for accepted local, loopback static-remote, and
  physical-LAN bounded classification execution; it does not change RFC-0061
  or add distributed infrastructure.

### RFC-0067 — Bounded textual code assistance

- [Minimal loopback Code view proof](minimal-loopback-code-view-proof.md)
  — retains focused automated and implementation-inspection evidence for the
  accepted RFC-0070 fourth fixed text-only Code view; it records no live model
  or filesystem-authority exercise.
- [Loopback browser Code view investigation](browser-code-view-investigation.md)
  — concludes that a text-only Code view can reuse the accepted native request
  path and browser mechanics, but RFC-0062 and RFC-0067 require a narrow
  follow-up RFC before the fixed browser surface can expand.
- [Bounded textual code assistance proof](bounded-textual-code-assistance-proof.md)
  — retains privacy-safe local positive, no-eligible-capability, and physical
  two-machine real-LAN evidence for accepted RFC-0067 bounded textual code
  assistance.
- [Code caller integration investigation](code-caller-integration-investigation.md)
  — finds a bounded external Aider caller-side proof justified for one
  caller-owned script edit through explicit native `code`; no Home AI Cluster
  implementation or RFC is recommended.
- [Aider code bridge proof runbook](aider-code-bridge-proof-runbook.md)
  — prepares one disposable, one-machine Aider caller-side bridge proof of an
  explicit native `code` request and caller-owned script edit; it is not an
  execution result, supported integration, or replacement for the physical
  two-machine RFC-0067 proof.
- [Aider code bridge proof](aider-code-bridge-proof.md) — retained privacy-safe
  evidence from one bounded one-machine caller-side execution through explicit
  native `code`; it is not a supported integration or replacement for the
  independent physical two-machine RFC-0067 proof.
- [Supported Aider code integration investigation](aider-code-supported-integration-investigation.md)
  — evaluates the smallest possible project-owned one-shot caller edge after
  the bounded proof; it recommends an RFC before any implementation and defers
  persistent Aider support and compatibility expansion.
- [Aider caller edge proof](aider-caller-edge-proof.md) — retains privacy-safe
  evidence that the accepted RFC-0068 and RFC-0069 one-machine caller edge
  completed one bounded Aider-owned edit through explicit native `code`; the
  independent physical two-machine RFC-0067 proof remains separate.

### RFC-0080 — One-shot whole-file Code caller edge

- [Code-file real-model proof](code-file-real-model-proof.md) — retains
  privacy-safe evidence that two real-model `hac code-file` invocations passed
  the accepted one-request, closed-envelope, atomic-replacement boundary while
  sampled generated-code quality remained outside the caller guarantee.

### RFC-0081 — Explicit Code-File target creation

- [Code-file target-creation real-model proof](code-file-target-creation-real-model-proof.md)
  — retains privacy-safe evidence that one explicitly selected absent target
  was created and atomically populated through the accepted RFC-0081/RFC-0080
  caller path without manual target preparation or generated-code execution.

### Code-file model interoperability observations

- [Code-file model interoperability observations](code-file-model-interoperability.md)
  — retains bounded local observations of runtime-edge model output behavior
  through the accepted `code-file` caller; it is not a support guarantee,
  model recommendation, or change to RFC-0080/RFC-0081 boundaries.
- [Code-file model interoperability procedure](code-file-model-interoperability-procedure.md)
  — canonical non-normative stable seven-scenario inputs and inspection-only
  manual procedure for future observations; distinct from dated results.
- [Code-file timeout cancellation investigation](code-file-timeout-cancellation-investigation.md)
  — documents the bounded distinction between a one-shot caller timeout and
  unproven server, transport, runtime, and model-cancellation behavior; it
  selects no implementation or architectural decision.

## Document roles

- **Current operator guidance** describes the supported way to use the repository
  now.
- **Investigation** records evidence and a recommendation. It does not authorize an
  architectural change.
- **Runbook** records a repeatable procedure.
- **Proof** retains privacy-safe evidence of an observed behavior.
- **Closeout** summarizes completion of one roadmap phase.
- **RFC** proposes or records an architectural decision and remains indexed under
  [`RFC/`](../RFC/README.md).

## Maintenance

When adding a documentation file:

1. link it from the relevant phase or operator section in this index;
2. identify its role clearly in the file and link description;
3. keep current operator guidance separate from historical proof records;
4. do not rename older files merely to impose chronology; and
5. keep architectural decisions in RFCs rather than in this index.

The index may be expanded when older historical records become useful to navigate.
It should remain concise enough to answer two questions quickly:

> What should an operator read now?

and:

> In what order did the project establish its current shape?
