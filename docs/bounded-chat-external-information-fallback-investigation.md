# Bounded Chat External-Information Fallback Investigation

Status: Investigation

Date: 2026-08-31

## Question

What is the smallest additional operator-owned authority and caller-side decision
seam that could let one-shot hac chat QUESTION choose either one ordinary Chat
answer or one RFC-0078 acquisition followed by one RFC-0077
source-grounded Chat request, without converting RFC-0095's retained plugin
selection into ambient network authority?

This is an architectural investigation only. It changes no runtime behavior,
configuration, command syntax, plugin, endpoint, model, test, or accepted
decision. It does not make a model self-assessment a proof of truth, freshness,
or knowledge.

## Existing accepted boundaries

The current architecture separates four facts:

    installed plugin                         -> availability only
    retained exact plugin name               -> selection for explicit acquisition only
    plugin credential/service configuration  -> plugin/operator-owned readiness
    new Chat-specific authorization          -> required before Chat may disclose a question

RFC-0095 is explicit: even a retained tavily, an installed plugin, and a
present TAVILY_API_KEY leave ordinary Chat unchanged. Retention selects one
plugin only after an explicit external-information operation; it does not
authorize ordinary Chat acquisition, plugin discovery, import, credential reads,
provider contact, or startup work. RFC-0094 retained configuration is local,
inspectable configuration of closed operator facts, not a generic policy or
provider system.

RFC-0078 owns one explicit caller edge: select exactly one plugin, discover and
load it lazily for that operation only, invoke it once, reconstruct bounded
RFC-0077 evidence, and make one source-grounded request. It supplies no provider
fallback, retry, server plugin authority, or model-directed retrieval. RFC-0091
preserves separate explicit QUERY and QUESTION values. RFC-0093 keeps Tavily
credentials in the plugin caller-process environment; RFC-0079 keeps its fixed
loopback SearXNG service operator-owned. Neither is HAC authority to use a
provider.

RFC-0077 keeps acquisition outside the cluster. Its dedicated source-grounded
Chat request accepts one question and one-to-five bounded sources, projects
them deterministically into ordinary chat execution, and returns supplied
sources as provenance. Source URLs are data, never action targets. Evidence
cannot gain configuration, routing, capability, network, file, tool, or
execution authority.

RFC-0087 preserves one-shot Chat forms as exactly one ordinary request. Its
no-message interactive mode instead holds chronological successful messages only
in the foreground process. RFC-0049 freezes one-shot Chat JSON as compact
ClusterResult content, adapter, model, and node_id fields.

## Current implementation seams

The current code confirms the ownership boundaries.

- [chat_command.py](../src/home_ai_cluster/chat_command.py) is a caller-edge
  client. A one-shot message creates a chat ClusterRequest and makes one fixed
  loopback request; it does not import acquisition code. Its output helpers
  validate and format only ClusterResult.
- [external_information_command.py](../src/home_ai_cluster/external_information_command.py)
  is separately caller-owned. It loads exactly one selected entry point after
  input parsing, invokes it once with a separately validated QUERY of at most
  4,096 UTF-8 bytes, reconstructs SourceGroundedChatRequest, and posts it once
  to the source-grounded route.
- [api/routes.py](../src/home_ai_cluster/api/routes.py) makes the
  source-grounded route acquisition-neutral. The server receives no plugin name,
  credential, query, or provider state. It also exposes a reuse limitation: in
  a static composition public Chat, source-grounded Chat, and Classify routes
  construct RequestConstraints with local_only false, so routing may select a
  declared remote.
- [core/models.py](../src/home_ai_cluster/core/models.py) defines closed
  ClassifyRequest text and labels, with two through 32 exact-unique labels. It
  defines RequestConstraints.local_only, default true. SourceGroundedChatRequest
  has one question, sources, and constraints; its result carries original
  ordered sources separately.
- [core/routing_candidates.py](../src/home_ai_cluster/core/routing_candidates.py)
  makes locality precise: local_only true excludes declared remotes; false
  permits local-precedence then declared-remote selection. Contacting a local
  server alone does not guarantee caller-local inference.
- [core/executor.py](../src/home_ai_cluster/core/executor.py) validates that a
  classifier proposal is one supplied label. Its source-grounded path uses the
  existing adapter chat operation and returns provenance. The Ollama and
  llama-server adapters have bounded structured Classify projections, but
  ordinary Chat remains unstructured.

The native Classify client cannot be used unchanged as the decision call: it
sends only text and labels to a public route whose current static-cluster
behavior may be remote. Its public contract also says nothing about
answerability semantics.

## Authority analysis

The first new fact must authorize disclosure, not merely selection. The operator
must understand that an authorized fallback may send the exact one-shot question
to the selected acquisition plugin. That matters for a private question, even
though a selected SearXNG plugin might use an operator-owned loopback service:
HAC must remain provider-neutral.

| Candidate authority | Assessment |
| --- | --- |
| Keep explicit external-information | Current safest behavior. It preserves separate QUERY and QUESTION, but does not meet ordinary-Chat fallback. |
| Per-invocation Chat opt-in | Clear and privacy-visible, with no retained state. It repeats consent ceremony and is viable, but less suitable for a stable policy. Exact spelling should not be chosen here. |
| One retained Chat-specific authority | Smallest durable authority: one optional boolean-like fact whose absence means no automatic acquisition. It is orthogonal to runtime composition, topology, and retained plugin selection, and could be shown by config show. It needs an RFC because it authorizes ordinary-Chat disclosure. |
| Retained plugin choice as authority | Rejected by RFC-0095. It is selection only, expressly not ordinary-Chat network authority. |
| Installation or credential presence | Rejected. Installation is availability; an API key authenticates a plugin if invoked. Neither expresses permission to disclose a Chat question. |
| Separate command or mode | Cleanly preserves Chat, but adds another caller surface and is less natural for the stated 0.8 goal. It remains an alternative if the project rejects a Chat output union. |

If the project proceeds, the preferred candidate is one optional retained
Chat-specific authorization whose absence preserves current behavior exactly. It
is not a policy language, provider permission, profile, ACL, or generic
external-network toggle. Per-invocation authorization remains the smaller
non-retained alternative; an RFC must choose rather than implement both.

## Orchestration ownership

The only ownership-compatible candidate is caller-side finite orchestration:

    authorized one-shot Chat question
      -> one bounded decision request to HAC
      -> local              -> one ordinary Chat request
      -> external-evidence  -> caller invokes selected RFC-0078 plugin once
                             -> one source-grounded Chat request
      -> finish

The caller retains plugin discovery/loading, selection resolution, credential
visibility, and exactly one invocation. The server owns only a bounded decision
operation and normal Chat/source-grounded operations. It does not discover entry
points, import plugins, inspect credentials, acquire sources, or receive an
acquisition query. This preserves RFC-0078 and keeps provider knowledge out of
ordinary Chat routing and adapters.

Server-side orchestration would require server plugin discovery/import or an
acquisition endpoint, plugin configuration/credentials, a provider/network
call, and acquisition state. That inverts RFC-0078's caller boundary. A split
design, where the server returns only a closed decision and the caller performs
the selected acquisition, is the smallest seam, not a generic orchestrator.

## Answerability-decision alternatives

The truthful question is not whether the model knows something. A model cannot
prove its own factual correctness, freshness, or sufficiency. The smallest
honest semantic is:

> Under an explicitly authorized bounded external-evidence policy, should this
> one question be attempted with external evidence, or should HAC attempt one
> ordinary Chat answer?

This is a bounded model judgement, not a truth or currentness oracle. It may be
wrong, including confidently choosing local for a stale question.

### Existing Classify

ClassifyRequest can carry the one-shot question as bounded text and two labels
such as answer-locally and requires-external-evidence. The core already closes
the result to supplied labels. Both adapters have an explicit Classify
projection with structured output and temperature zero. This is materially
smaller than a new capability.

It is not already the needed contract. Current Classify means one bounded source
text classified against operator labels. Its generic adapter prompt has no
HAC-owned definition of proposed decision semantics. More importantly, public
Classify in a static cluster is not caller-local; the route sets local_only
false. A later RFC needs a narrow explicit way for this decision to require
caller-local execution, or must deliberately authorize and explain remote
decision disclosure. The latter is not recommended: the decision governs whether
the caller question crosses an external boundary.

Classify also creates a conditional dependency: a Chat-capable local node need
not declare classify, because RFC-0061 keeps it out of the omission default. The
external policy must not turn formerly valid ordinary Chat into failure merely
because local Classify is unavailable. The smallest safe rule is that an
unavailable or failed decision gives one ordinary Chat request, never
acquisition. This preserves local-first behavior but does not promise external
evidence for every question. The RFC must decide whether one extra inference on
every authorized one-shot request is proportionate. It is boring, finite, and
engine-independent.

### Private Chat-like decision request

A hidden first Chat prompt could return an answer or external-needed signal, but
would require a request/result representation, endpoint, structured parsing,
adapter semantics, and output/failure contract. Combining a local answer with
the signal saves one inference only by making ordinary Chat non-ordinary. It is
larger and less inspectable than Classify reuse; reject it unless Classify cannot
receive a small local-only decision seam.

### First ordinary answer plus uncertainty heuristic

Rejected. Searching generated prose for uncertainty is neither a closed result
nor evidence of factual uncertainty. Models can be confident and wrong,
uncertain and useful, or phrase uncertainty arbitrarily. It wastes an answer
inference before an external branch and makes fallback uninspectable.

### New answerability capability and deterministic rules

A new capability is disproportionate unless Classify reuse is impossible: it
requires a capability name, declaration/omission semantics, models, route,
remote envelope, adapter operation, and engine projections. Deterministic rules
can reject clearly oversized acquisition input but cannot determine factual
truth, freshness, model knowledge, or evidence value. They are guardrails, not
the decision.

## Query derivation and bounds

The candidate must use QUESTION exactly as selected plugin QUERY. It is
deterministic, reviewable, requires no model-generated disclosure or query
rewrite, and lets the operator know exactly what may leave HAC. It is the only
candidate compatible with RFC-0078 without a query-planning decision.

The limit is real: RFC-0078 bounds QUERY at 4,096 UTF-8 bytes, while ordinary
Chat and RFC-0077 questions allow up to 65,536. Automatic fallback must not
silently truncate, extract keywords, summarize, or rewrite. For a larger
question, the smallest candidate is to make the external branch unavailable
and perform one ordinary Chat request; the operator may use explicit
external-information with a separately chosen bounded query. The alternative,
visible failure rather than local Chat, is more explicit but harms local-first
utility. An RFC must select one; neither permits modified text.

Model-generated or rewritten queries are rejected. They give a model control
over external disclosure and retrieval semantics, approaching model-directed
retrieval. Deterministic truncation or extraction is likewise rejected.

## One-shot first; defer interactive Chat

First scope must be one-shot positional and message-option forms. Their request
is one question, matching RFC-0077. The interactive form retains chronological
user/assistant context, while source-grounded Chat accepts one question plus
evidence and no arbitrary message history. Automatic acquisition in an
interactive turn would require deciding what context is classified, what text
becomes disclosed query, how evidence/provenance persists, and whether later
turns remain grounded.

Those are a materially larger source-grounded conversation contract. Defer
interactive fallback; do not design a multi-turn source-grounded system.

## Output and provenance compatibility

An external branch produces SourceGroundedChatResult, not ClusterResult.
Dropping sources makes automatic execution insufficiently inspectable, while
silently adding occasionally present sources to RFC-0049 ordinary Chat JSON
changes a stable machine contract. Permissive model validation would not make
that product/API decision truthful.

Content mode can remain visually identical: print generated content after either
successful branch. An authorized new mode could make verbose output identify
local versus source-grounded path and, on external path, display supplied-source
provenance. Its JSON contract needs an explicit tagged stable result shape that
records branch and provenance, or the RFC must limit authorized mode initially
to content presentation. The latter is smaller but weaker in inspectability. The
RFC must decide explicitly and must not alter legacy ordinary Chat JSON when
authority is absent.

## Failure-state analysis

    authority absent                         -> ordinary Chat only
    authorized, decision unavailable/fails   -> ordinary Chat only
    authorized, decision says local          -> ordinary Chat only
    authorized, decision says external,
      query too large                        -> ordinary Chat only (candidate)
    authorized, decision says external,
      no retained plugin choice              -> ordinary Chat only (recommended candidate)
    authorized, decision says external,
      selected plugin unusable               -> visible acquisition failure
    authorized, acquisition fails            -> visible acquisition failure
    authorized, source-grounded Chat fails   -> ordinary bounded failure

No decision failure may trigger external acquisition. Chat-specific authority
alone cannot select a plugin: RFC-0095's retained exact plugin name remains the
only candidate automatic selection fact. HAC must not inspect installation to
infer a plugin, invent a name, or select one automatically. When no retained
selection exists, no acquisition or disclosure has begun. The two smallest
candidate behaviors are one ordinary Chat request because the external branch
cannot be entered, or a visible incomplete-authorized-configuration failure.
The former is recommended as the smaller local-first candidate, but the later
RFC must decide it explicitly.

This is distinct from a retained name whose plugin distribution, credential,
service, or acquisition is unusable. Once that selected external operation
begins, surface the existing privacy-safe acquisition failure rather than
silently returning an ordinary answer; do not invent another plugin, retry, or
use an alternate provider. There is no second local answer, acquisition,
provider, or source-grounded request. A source-grounded execution failure
likewise has no retry or fallback.

The oversized-query and absent-retained-selection rules are the remaining
policy choices. Every other bound follows existing safe failure ownership or
preserves ordinary Chat before an external operation exists.

## Privacy, routing, and maximum work

The authorization must say what it means: when the decision selects external,
the exact one-shot question becomes plugin query. For Tavily that can disclose
the entire question to an external provider. Plugin responses, credentials, raw
provider data, and source content remain non-persistent; normalized sources
travel only through source-grounded path. For SearXNG the first receiver may be
operator service, but that cannot weaken provider-neutral authority.

The decision should be caller-local. local_only is a routing constraint, not a
conclusion implied by loopback transport. Current routes show why an RFC must
state locality and identify an implementation seam. Only the disclosure
decision needs new caller-local execution semantics. The ordinary Chat answer
branch retains existing Chat routing and may use an already authorized declared
remote under current rules. Neither evidence nor model may change
configuration, routing, plugin selection, credentials, files, tools, network
authority, or execution authority. Language-level prompt injection remains a
model limitation, as RFC-0077 states.

For the Classify-first candidate, maximum work is finite:

| Path | Local decision inferences | Ordinary Chat | Plugin acquisitions | Source-grounded Chat |
| --- | ---: | ---: | ---: | ---: |
| Authority absent | 0 | 1 | 0 | 0 |
| Decision unavailable/fails | 1 | 1 | 0 | 0 |
| Decision says local | 1 | 1 | 0 | 0 |
| Decision says external, no retained plugin choice | 1 | 1 | 0 | 0 |
| External path through usable selected plugin | 1 | 0 | 1 | 1 |
| Acquisition/source-grounded failure | 1 | 0 | 1 | at most 1 |

There is no loop, alternate provider, repeat classification, URL following,
background work, or recursive local fallback. The external decision inference
is a deliberate boring trade-off for a closed branch before disclosure, not a
performance optimization.

## Compatibility and invariants

With no new Chat-specific authorization, ordinary one-shot Chat retains its
current exact operation: one Chat request; no plugin discovery/import; no
provider credential read/request; no answerability inference; no Classify
dependency; and no new failure state. A retained selected plugin, installed
package, or present credential remains inert for ordinary Chat.

Startup is unaffected: it must not inspect acquisition entry points, load
plugins, read credentials, contact providers, perform decision work, or alter
routing. Even with authorization, automatic work belongs only within an
explicitly authorized one-shot caller operation.

The decision projection must remain engine-independent. Reusing Classify means
both adapters use their existing bounded classification operation; HAC must
define semantics above it, not branch on runtime, model, provider, node, or
prompt dialect. A static cluster cannot silently let a declared remote determine
whether the caller discloses its question unless a future RFC expressly changes
that privacy boundary.

## Alternatives considered

| Alternative | Result |
| --- | --- |
| Ordinary Chat plus explicit external-information | Retain as current behavior and fallback for absent authority. |
| Per-invocation authorization | Viable but repeated ceremony. |
| Retained Chat-specific authorization | Preferred durable candidate, subject to RFC. |
| Plugin selection as authority | Rejected by RFC-0095. |
| Existing Classify decision | Preferred only with an explicit local-decision seam and defined semantics. |
| Private Chat-like structured decision | Larger new contract; reject unless Classify fails evidence. |
| First answer plus prose heuristic | Rejected as unreliable and wasteful. |
| New answerability capability | Disproportionate capability expansion. |
| Exact QUESTION as QUERY | Preferred deterministic disclosure, subject to 4,096-byte policy. |
| Model-generated or rewritten query | Rejected as model-directed disclosure/retrieval. |
| Caller-side orchestration | Required to preserve plugin and credential ownership. |
| Server-side plugin orchestration | Rejected; gives server provider authority. |
| One-shot first | Required; interactive support is separate contract. |

## Outcome

**Outcome B — viable with one bounded architectural adjustment and a later RFC.**

The adjustment is a closed, operator-authorized one-shot Chat fallback contract:
one explicit Chat disclosure authority plus caller-owned finite branching that
obtains one HAC-owned, caller-local, closed two-label decision before it either
does ordinary Chat or invokes already selected RFC-0078 plugin once. This does
not reinterpret retained plugin selection as authority and does not add a new
executable capability if the project accepts a narrow Classify decision seam.

This outcome is conditional, not implementation authorization. It remains
proportionate only if a later RFC can keep decision local, define truthful
semantic and Classify projection, preserve zero-authority compatibility, and
give external branch a truthful output/provenance contract. If that requires a
general permission system, generic orchestration, a new capability, or
source-grounded multi-turn conversation, the correct later outcome is C.

## Exact later-RFC decision surface

A later RFC should decide only:

1. Whether authority is per-invocation or one retained Chat-specific fact, and
   how absence preserves ordinary Chat exactly.
2. One-shot-only scope; interactive Chat is deferred.
3. Caller-side ownership of finite state machine and prohibition on server
   plugin/provider authority.
4. Precise truthful two-label semantic and narrow caller-local use of existing
   Classify, including Classify-unavailable and decision-failure behavior.
5. Whether exact question is acquisition query, and visible behavior over its
   4,096-byte bound.
6. Behavior when Chat-specific authority exists but no retained
   acquisition-plugin selection exists, distinct from selected-plugin failure.
7. Exact operation counts and no-retry/no-alternate-provider failure behavior.
8. Authorized-mode output: branch indication and supplied-source provenance,
   especially JSON and verbose output.
9. If retained authority is selected, one inspectable retained-state concept and
   its relationship to retained plugin selection.

It should not choose final flag or field spelling, provider configuration,
credentials, provider options, profiles, ACLs, query rewriting, caching,
history, agents, tools, URL retrieval, or implementation abstractions.

## Explicit non-goals

This investigation does not propose an agent, research loop, repeated search,
query planning/refinement, URL following, crawling, browser, tools/function
calling, provider fallback, multiple providers, async work, queue, database,
cache, RAG, embeddings, generic permission/provider/plugin framework, secrets
manager, distributed acquisition, or interactive source-grounded conversation.

## Suggested proof expectations for a later implementation

If an RFC is accepted, implementation proof should demonstrate:

1. zero-authority, retained-plugin, installed-plugin, and credential-present
   cases all keep ordinary one-shot Chat at exactly one ordinary request;
2. authorized local and external branches meet maximum-work table;
3. decision execution is caller-local in a static cluster, including a remote
   Classify-capable declaration that must not receive decision;
4. Classify-unavailable and decision-failure behavior never triggers
   acquisition;
5. exact selected-plugin-only loading and invocation, with no startup discovery
   or credential read;
6. exact-question query transmission and visible over-limit behavior, with no
   truncation or rewrite;
7. plugin/acquisition/source-grounded failures have no retry, alternate
   provider, or local-answer substitution after acquisition starts;
8. source URLs are never followed and evidence cannot alter HAC authority;
9. content, verbose, and JSON preserve ordinary compatibility when authority is
   absent and accurately expose authorized external branch; and
10. retained evidence is prompt-, credential-, query-, source-content-, and
    provider-response-free.
