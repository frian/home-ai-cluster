# RFC-0096: Bounded Operator-Authorized Chat External-Information Fallback

Status: Accepted

Date: 2026-08-31

Author: frian

## Summary

This RFC proposes one optional, retained, Chat-specific operator authorization
for a bounded external-information fallback in one-shot `hac chat QUESTION`.
It is separate from RFC-0095's retained acquisition-plugin selection.  Its
absence preserves ordinary Chat exactly.

When the authorization is present, a retained exact acquisition-plugin choice
is present, and `QUESTION` is within RFC-0078's 4,096 UTF-8-byte query bound,
the caller makes exactly one caller-local Classify decision with two fixed
labels.  The decision asks only whether this one question should be attempted
with external evidence under the already authorized policy.  A local decision
makes one ordinary Chat request.  An external-evidence decision invokes the
one retained RFC-0078 plugin once with the exact question as its query, then
makes one RFC-0077 source-grounded Chat request, and finishes.

```text
authorization absent / retained plugin absent / question too long
        -> ordinary Chat

otherwise
        -> one caller-local Classify decision
           |- ordinary         -> one ordinary Chat request
           `- external-evidence -> one selected plugin invocation
                                -> one source-grounded Chat request
                                -> finish
```

This is not a truth, freshness, or model-knowledge oracle.  It is a closed
model judgement made before any external disclosure.  The caller owns the
finite branching and all plugin work; the ordinary HAC server remains
acquisition-neutral.  No implementation is authorized by this Draft RFC.

## Context

RFC-0077 establishes an acquisition-neutral, bounded source-grounded Chat
contract.  RFC-0078 places one plugin acquisition before that contract in a
separate explicit caller operation: it discovers and lazily loads exactly one
operator-selected plugin, invokes it once, validates fresh RFC-0077 evidence,
and sends one source-grounded request.  It deliberately gives neither the
ordinary server nor ordinary Chat plugin, credential, provider, or network
authority.

RFC-0095 permits retaining one exact RFC-0078 plugin name, but only as
selection for an explicit `external-information` operation.  It expressly
does not authorize ordinary Chat acquisition.  Installation is availability;
plugin credentials and service configuration are plugin/operator-owned
readiness; neither is consent to disclose a Chat question.

The retained bounded Chat external-information fallback investigation found a
smaller viable shape than server-side orchestration, a new capability, or a
hidden Chat prompt: one distinct Chat disclosure authority plus a caller-owned
use of the existing closed `classify` capability.  That investigation is
evidence only.  This RFC selects the bounded architecture it identified.

## Problem

Ordinary Chat is intentionally local-first and does not acquire external
information, even when an acquisition plugin is installed, selected, and ready.
An operator who wants a one-shot Chat question to use external evidence when
appropriate must currently choose a separate explicit acquisition command and
provide a distinct query and question.

That explicit path remains the correct general mechanism, especially when the
operator wants a different query.  It does not provide the requested limited
one-shot experience: one operator-authorized Chat question may either obtain
one ordinary answer or one answer grounded in one bounded acquired source set.

Treating a retained plugin, installation, or a present credential as that
authority would silently turn selection or readiness into disclosure consent.
Moving acquisition to the server would make the server own plugin discovery,
credentials, provider connections, and acquisition state.  Neither preserves
the established authority boundary.

## Goals

- Add one optional retained operator fact that explicitly authorizes this
  particular one-shot Chat fallback.
- Preserve ordinary Chat exactly when that fact is absent.
- Keep RFC-0095 retained plugin selection separate from Chat disclosure
  authorization.
- Use one existing closed Classify operation for one caller-local, two-label
  decision before a question may reach a selected acquisition plugin.
- Keep all acquisition discovery, loading, invocation, credentials, and
  provider/service behavior on the caller/plugin side of RFC-0078.
- Make the external branch deterministic: the exact question is the plugin
  query, one selected plugin is invoked once, then one RFC-0077 request occurs.
- Preserve source provenance and accurately expose the selected branch for an
  authorized invocation without changing legacy ordinary-Chat JSON when this
  authorization is absent.
- Keep the decision engine-independent, bounded, non-persistent, and free of
  provider, model, runtime, node, or query-planning policy.

## Non-goals

This RFC does not authorize:

- automatic fallback in interactive/no-message Chat, browser Chat,
  OpenAI-compatible Chat, Aider, Code, Summarize, Classify generally, or any
  caller surface other than native one-shot `hac chat` and its existing root
  alias;
- a general external-network permission, provider permission, policy language,
  profile, ACL, provider list, provider ranking, health system, generic plugin
  framework, generic configuration framework, or secrets manager;
- treating installation, a retained plugin, a credential, provider health, or
  a classifier result as authority to do anything beyond this finite flow;
- server-side plugin discovery/loading/invocation, provider configuration,
  credential handling, acquisition endpoint, provider HTTP client, or provider
  lifecycle ownership;
- a new executable capability, answerability capability, model self-knowledge
  claim, confidence score, rationale, question rewriting, query generation,
  truncation, extraction, summarization, or model-directed retrieval;
- retry, repeated classification, alternate-plugin/provider fallback, local
  answer substitution after acquisition begins, URL following, crawling,
  browsing, tools, agents, research loops, caching, persistence, history, or
  background work; or
- implementation, tests, configuration spelling, documentation changes, or an
  update to RFC-0095 or the RFC index in this RFC pull request.

## Decision / accepted architecture

### One orthogonal retained authorization

HAC may retain one optional boolean-like Chat-specific fact, conceptually:

```text
chat_external_information_fallback: bool = false
```

`false` or an absent value means that this fallback is not authorized.  `true`
means only:

> For an eligible one-shot Chat invocation, HAC may make the bounded local
> decision defined here and, only if that decision selects external evidence,
> disclose the exact one-shot question to the already retained selected
> RFC-0078 acquisition plugin.

It is not a general permission to use a network, a statement that an installed
plugin is ready, a grant to inspect credentials, or a provider-specific
authorization.  It is independent of RFC-0095's optional retained plugin
name.  Both facts are necessary for the automatic external branch, but neither
changes the meaning of the other.

The fact may be set, cleared, and shown through a later finite retained
configuration action consistent with RFC-0094.  Its physical stored field and
CLI spelling are deliberately not frozen here.  Configuration is syntactic and
read-only where applicable: setting, clearing, and showing it must not inspect
entry points, import a plugin, read credentials, contact a provider or service,
classify a question, or probe health.

`hac config show` may conceptually show only the configured authorization, for
example:

```text
Chat external information
  fallback: enabled
```

It reports configuration, not live plugin, credential, provider, network, or
classifier status.  It must not show secrets, secret presence, installed or
missing plugins, endpoints, health, quota, cost, or source data.

### Scope and entry conditions

This RFC applies only to a non-interactive native one-shot Chat invocation with
one supplied message: the existing positional-message and `--message` forms of
`hac chat`, and the equivalent existing root alias.  It excludes RFC-0087's
no-message foreground interactive conversation.  A later proposal would need
to define what conversation context is classified, what becomes an acquisition
query, and how source provenance survives turns; this RFC does none of that.

RFC-0096 eligibility is evaluated only after retained configuration has passed
the existing RFC-0094 load and validation boundary and can resolve both the
Chat-specific authorization and RFC-0095 retained plugin selection. Malformed
or semantically invalid retained state remains RFC-0094's visible local failure:

```text
retained configuration is malformed or semantically invalid
        -> existing RFC-0094 visible configuration failure
        -> no ordinary Chat, decision, plugin discovery, credential read,
           acquisition, or retained-state repair/rewrite
```

RFC-0096 defines no new public error vocabulary for this case. It must not
infer authorization, infer a plugin from installed distributions, repair or
rewrite retained state, or expose retained-file contents, secrets, or
unnecessary path details beyond existing RFC-0094 behavior. Configuration-
owning surfaces, including `hac config show`, retain their existing
responsibility for invalid retained configuration.

After successful retained-state validation, the caller evaluates these local facts, without the
decision, plugin discovery, import, credential access, provider/service access,
or network work:

```text
Chat fallback authorization absent                 -> ordinary Chat
no retained RFC-0095 plugin selection              -> ordinary Chat
QUESTION exceeds 4,096 UTF-8 bytes                 -> ordinary Chat
otherwise                                          -> one local decision
```

The normal one-shot Chat message validity bound remains authoritative.  The
4,096-byte condition is only the RFC-0078 plugin-query eligibility condition;
it does not narrow ordinary Chat's accepted question bound.  The question is
never truncated, rewritten, summarized, or otherwise transformed.  An operator
who needs external information for a larger or differently phrased query uses
the explicit RFC-0078/RFC-0091 operation with a separately supplied query.

The no-retained-plugin case intentionally remains ordinary Chat.  No external
operation can begin because the Chat authority selects no provider/plugin.  HAC
must not enumerate installed plugins, infer a sole plugin, invent a name, or
emit an incomplete-configuration error for this pre-disclosure case.

### Dedicated caller-local decision surface

The ordinary public `/v1/classify` client boundary is not this decision
surface: it reconstructs constraints and may permit declared-remote routing in
a static cluster. A later implementation may therefore add one dedicated
bounded loopback HAC decision surface, with its exact URI/name left open by
this RFC.

The native `hac chat` caller may send one bounded Chat external-information
decision request to that surface. The surface constructs the fixed RFC-0096
Classify projection below with `local_only=true` and executes it only against
the caller-local Classify candidate. It is server-executed but caller-initiated
and performs only this bounded decision. It must honor existing caller-local
static `classify` eligibility and must never route the decision to a declared
remote.

This dedicated surface performs no plugin discovery or acquisition. It accepts
no plugin name, provider configuration, credential, arbitrary labels,
caller-controlled routing policy, or `RequestConstraints` control. It is not a
new executable capability, a general local-only Classify API, or an ordinary
native-client API for `/internal/cluster/request`. The server owns local
decision execution only; the caller still owns branching and all plugin/provider
work.

### Fixed HAC-owned Classify projection

Conceptually, the decision surface accepts only:

```text
ChatExternalInformationDecision
  question: exact one-shot operator question
```

It projects that value deterministically into one existing `ClassifyRequest`:

```text
text: fixed HAC-owned decision policy + exact question as untrusted subject data
labels:
  - ordinary
  - external
constraints.local_only: true
```

HAC, not the operator or runtime adapter, owns the fixed policy. It asks whether
external evidence is likely to materially improve the response under this
already authorized bounded flow; it does not ask whether the model knows the
answer. It makes no claim of truth, freshness, confidence, completeness, or
correctness. The exact policy wording and its serialization/delimiting are
implementation details, but these semantic invariants are fixed.

The exact operator question is preserved as untrusted subject data. It is not
rewritten, truncated, summarized, normalized, or interpreted as policy, and it
cannot grant configuration, routing, capability, plugin-selection,
provider-selection, file, tool, network, or execution authority. Only the two
fixed HAC-owned labels are available. No confidence, rationale, explanation,
score, threshold, or alternative is returned. The projection remains runtime-
and engine-independent; existing runtime adapters continue to execute ordinary
Classify, and this introduces no generic prompt-template system.

Because automatic external eligibility already requires a question no larger
than 4,096 UTF-8 bytes, this fixed projection remains within RFC-0061's
existing 65,536-byte Classify text bound. It does not change RFC-0061's generic
operator-facing Classify semantics or add an `answerability` capability.

### One caller-local closed decision

For the remaining eligible invocation, the caller makes exactly one request to
the dedicated decision surface. That surface executes the fixed projection above
using the existing `classify` capability. The classifier's only HAC-defined
semantic is:

```text
ordinary  = attempt one ordinary Chat answer
external  = attempt one answer with external evidence under this authorization
```

It does not assert whether an answer would be correct, current, complete,
safe, useful, or known by the model.  It is not a factual or freshness oracle.
The existing Classify closed-result rule remains authoritative: a successful
result is exactly one supplied label, with no confidence, explanation,
alternative, or repair.

This one use of Classify executes caller-locally through the dedicated surface;
a loopback client connection alone is not evidence of local execution. The
ordinary and source-grounded Chat requests retain their existing routing
semantics, including existing operator-declared remote eligibility.

If caller-local Classify is unavailable, its request cannot be constructed or
sent, it fails before a valid result, or it returns an invalid result, the
caller makes exactly one ordinary Chat request.  It does not acquire external
information, retry Classify, select a remote classifier, report a classifier
detail, or make a second decision.  This preserves one-shot Chat utility and
ensures that decision failure cannot expand disclosure authority.

### Closed caller-side state machine

The complete operation is caller-owned and finite:

```text
eligible one-shot Chat
  -> one dedicated caller-local decision surface
  -> unavailable/failure/ordinary
       -> one ordinary Chat request -> finish
  -> external
       -> retained exact RFC-0095 plugin name
       -> discover/load that exact RFC-0078 entry point only
       -> invoke it once with exact QUESTION as QUERY
       -> reconstruct and validate RFC-0077 evidence
       -> one source-grounded Chat request -> finish
```

The client, not the ordinary HAC server, resolves the retained name and owns
plugin metadata discovery, lazy loading, one invocation, and RFC-0077
reconstruction. Apart from the dedicated local decision request, the server
receives neither a plugin name, acquisition query as a distinct field,
credential, provider configuration, nor acquisition state. It continues to
receive only that fixed decision request or one existing ordinary/source-
grounded Chat request.

When the classifier selects `external`, the exact UTF-8 question is the
RFC-0078 `QUERY` unchanged.  It is also the RFC-0077 question after acquisition.
There is no model-generated, derived, hidden, or provider-specific query.
Consequently, the operator can know the exact text that may be disclosed to the
selected plugin.  For a plugin such as Tavily, that may mean disclosure to its
fixed external provider; for SearXNG, the first recipient may be the
operator-owned service.  Those differences do not weaken the provider-neutral
authorization.

Once the selected acquisition path starts, RFC-0078 failure ownership applies.
If the selected plugin is missing, duplicate, incompatible, unable to load,
unconfigured, credential-invalid, unable to acquire, or returns invalid data,
the operation ends with the existing privacy-safe
`external-information-acquisition-failed` failure.  It must not return an
ordinary answer, retry the plugin, select another plugin/provider, mutate
retained state, or reclassify.  A source-grounded Chat failure likewise ends
under its existing bounded failure behavior, without a local-answer retry.

### Maximum work

Each invocation has these upper bounds.  “Decision” always means a
caller-local Classify inference.

| Path | Decisions | Ordinary Chat | Plugin acquisitions | Source-grounded Chat |
| --- | ---: | ---: | ---: | ---: |
| Invalid retained configuration | 0 | 0 | 0 | 0 |
| Authorization/plugin/query eligibility absent | 0 | 1 | 0 | 0 |
| Decision unavailable, invalid, or fails | 1 | 1 | 0 | 0 |
| Decision is `ordinary` | 1 | 1 | 0 | 0 |
| Decision is `external`, selected plugin fails | 1 | 0 | 1 | 0 |
| Decision is `external`, acquisition succeeds | 1 | 0 | 1 | 1 |
| Source-grounded Chat fails | 1 | 0 | 1 | 1 |

The invalid-retained-configuration row is a pre-operation RFC-0094 visible
configuration failure, not a successful Chat path.

There is no branch with more than one decision, ordinary Chat request, plugin
invocation, or source-grounded Chat request.  There is no loop, recursion,
background continuation, URL fetch, provider fallback, or second answer.

### Output and provenance

With valid retained configuration and absent Chat authorization, all existing
content, verbose, JSON, error, and exit-status behavior remains byte-for-byte
and structurally compatible with ordinary Chat. In particular, legacy ordinary
Chat JSON remains the RFC-0049 `ClusterResult` shape and does not gain optional
sources.

For an invocation made while the authorization is safely resolved as enabled,
content presentation prints only generated content after either successful
branch, as ordinary Chat does. Verbose and JSON output must use one closed
tagged authorized-Chat result, conceptually:

```text
branch: ordinary | source-grounded
result: existing ClusterResult | existing SourceGroundedChatResult
```

The active authorization always uses this authorized verbose/JSON shape, even
when deterministic eligibility or the decision ultimately selects ordinary
Chat. The `ordinary` path explicitly identifies that no external acquisition
occurred. The `source-grounded` path includes the ordered RFC-0077 supplied
sources as provenance and must not claim that they are true, used, current, or
sentence-level citations. The two result types must not be flattened into one
object with arbitrary optional fields, and source provenance must not be
discarded.

This narrowly scoped envelope is necessary because dropping provenance is
misleading, while adding sources to legacy ordinary Chat JSON changes an
existing contract. Its exact field spelling and human verbose formatting are
implementation details, but it must be closed and selected only when the
retained authorization was safely resolved as enabled. It must never expose a
query separately, credentials, provider payloads or metadata, endpoints, raw
Classify output, decision prompt, prompts, topology, or internal failure
details. When valid retained configuration has authorization absent, existing
RFC-0049 verbose/JSON remains exactly unchanged. Invalid retained configuration
fails before an RFC-0096 Chat result exists; RFC-0096 adds no result envelope
or presentation for that RFC-0094 failure.

## Privacy, authority, and compatibility invariants

Startup remains unchanged whether or not either retained fact is present.  It
must not inspect plugin entry points, import a plugin, read a credential,
contact a provider/service, run Classify, or alter topology, routing, adapters,
capabilities, history, or background work.

With the Chat authorization absent, including when a plugin is installed and
retained and its credentials are present, one-shot Chat performs exactly one
ordinary Chat request.  It makes no decision inference and no plugin or
provider activity.  This is the primary compatibility and privacy guarantee.

RFC-0096 does not weaken RFC-0094 retained-state validation. Malformed or
semantically invalid retained configuration fails visibly before RFC-0096
eligibility, Classify, plugin discovery, credential access, acquisition, or
Chat execution. It has no special recovery path.

With authorization present but no retained plugin selection or an oversized
question, one-shot Chat also performs exactly one ordinary Chat request with no
classification or plugin activity.  A local decision failure likewise never
discloses the question externally.  Only an `external` result from one
successful caller-local decision may cause the question to reach the exact
retained plugin.

Plugin credentials, provider configuration, raw provider responses, sources,
queries, decision prompts/results, generated content, and ordinary message
history remain non-persistent and must not enter retained configuration, default
logs, metrics, traces, or proof material.  RFC-0077 evidence remains data:
source URLs are provenance strings, never executable fetch targets, and sources
cannot influence configuration, routing, plugin choice, credentials, files,
tools, network authority, or execution authority.  Language-level prompt
injection is a model limitation, not authority.

This decision is engine-independent.  HAC defines the fixed labels, their
limited semantics, locality, and branching; no behavior may depend on model,
runtime, adapter prompt dialect, provider, plugin, node identity, confidence,
or model metadata.

## Relationship to existing RFCs

### RFC-0094

RFC-0094 remains the retained-configuration substrate and is authoritative for
retained-state parsing, validation, and failure. This RFC adds exactly one
orthogonal Chat authorization fact, no generic configuration framework, and no
special recovery path. Invalid retained state is never silently ignored merely
to preserve Chat availability. The physical retained field and path formats
remain private, and the exact CLI spelling for enabling or disabling this
authority remains outside this RFC.

### RFC-0095

RFC-0095 remains authoritative: the retained exact plugin name is selection,
not Chat authorization.  This RFC adds the separate conjunct required for an
automatic external branch.  It does not add a plugin list, fallback, provider
configuration, credential handling, or startup activity.

### RFC-0078 and RFC-0079/RFC-0093

RFC-0078 remains the complete acquisition boundary.  This RFC changes only the
bounded caller condition under which its existing selected-plugin operation may
occur.  Its exact-name discovery, lazy loading, one-call contract, evidence
revalidation, and privacy-safe acquisition failure remain unchanged.  RFC-0079
continues to own SearXNG lifecycle and RFC-0093 continues to keep
`TAVILY_API_KEY` entirely plugin/operator-owned.  HAC neither reads nor retains
either provider's configuration or credentials.

### RFC-0077

RFC-0077 remains the source-grounded request, evidence, projection, and
provenance authority.  This RFC supplies no acquisition API to the server and
does not loosen source bounds or source URL restrictions.  The external branch
constructs a fresh RFC-0077 request only after complete existing validation.

### RFC-0061

RFC-0061 remains the sole executable `classify` capability and closed
membership result contract.  This RFC adds no generic answerability capability;
it defines one caller-side semantic use with exactly two labels and requires a
narrow caller-local decision seam.  It does not make `classify` part of the
omission capability default or change ordinary classification behavior.

### RFC-0087 and RFC-0049

RFC-0087 interactive Chat is outside this proposal.  RFC-0049 ordinary Chat
JSON remains unchanged when this authorization is absent.  The explicitly
authorized presentation envelope is a distinct, closed result contract rather
than a permissive extension of legacy `ClusterResult` JSON.

## Alternatives considered

### Keep only explicit external-information

This remains available and is the safest current behavior, but does not supply
the intentionally bounded one-shot Chat fallback.

### Treat retained plugin selection, installation, or credentials as consent

Rejected.  These describe selection, availability, or readiness, not permission
to disclose a private Chat question.  It would contradict RFC-0095.

### Per-invocation Chat authorization

Viable, but rejected for this proposal.  One retained orthogonal fact is the
smaller durable policy for an operator who wants this bounded behavior, while
its absence keeps ordinary Chat exact.

### Server-side orchestration

Rejected.  It would grant the server plugin/provider authority and invert the
RFC-0078 caller boundary.

### New answerability capability or hidden Chat prompt

Rejected.  A new capability or private Chat protocol would require materially
more request, result, route, adapter, and semantic surface.  The existing
closed Classify result is sufficient with the narrow caller-local seam.

### Use a remote classifier

Rejected.  The decision governs whether an exact question crosses an external
acquisition boundary; sending it to a declared remote before that decision
would silently widen that privacy boundary.

### Rewrite, generate, or truncate a query

Rejected.  It would give a model or heuristic control over external disclosure
or alter operator text.  The exact question is the only bounded automatic
query; questions over RFC-0078's limit remain ordinary Chat.

### Fall back to local Chat after acquisition starts

Rejected.  A failed selected provider must not silently substitute an answer
without the requested external evidence, retry elsewhere, or hide a failed
disclosure attempt.  RFC-0078's existing privacy-safe failure is authoritative.

### Add interactive source-grounded Chat

Rejected as out of scope.  It would require a source-grounded conversation and
history/provenance contract beyond this one-shot decision.

## Rationale

One retained explicit authority makes the disclosure choice visible and durable
without confusing RFC-0095 selection with permission. Deterministic prechecks
preserve ordinary Chat before any decision or disclosure where the optional flow
is unavailable. The dedicated local decision surface keeps the decision local
while preserving caller-side plugin ownership. Reusing Classify is smaller than
a new capability, and its fixed HAC-owned projection gives the two labels
truthful, engine-independent meaning. Exact QUESTION-as-QUERY makes disclosure
inspectable. Finite work and the absence of server acquisition authority keep
the architecture bounded.

## Trade-offs

Benefits include a natural one-shot Chat experience after one-time operator
authorization, exact and inspectable disclosure, provider independence, no
model-generated retrieval query, no new executable capability, no server
plugin/provider authority, bounded maximum work, and unchanged ordinary
behavior without authorization.

Costs are one additional local Classify inference for eligible authorized
requests; a fallible model judgement; required caller-local `classify`
eligibility; changed verbose/JSON presentation while authorization is active;
no automatic acquisition for questions over 4,096 UTF-8 bytes; excluded
interactive Chat; visible rather than silent failures after acquisition begins;
and malformed retained configuration remaining a visible operator error rather
than silently degrading to ordinary Chat.

## Impact

If accepted, a later implementation may add only one retained authorization
fact, one dedicated bounded loopback decision surface, one fixed HAC-owned
Classify projection, the caller-side finite Chat state machine, and authorized
verbose/JSON presentation. It must not expand provider, capability, routing,
startup, credential, dependency, plugin, or network architecture.

### Proof expectations

A later implementation must provide focused proof that:

1. absent authorization preserves exactly one ordinary one-shot Chat request,
   including with retained/installed plugins and present credentials;
2. malformed or semantically invalid retained configuration produces the
   existing visible retained-configuration failure with zero Chat requests,
   decision requests, plugin discovery/invocation, credential reads, and
   acquisitions;
3. valid configuration with absent authorization takes one ordinary Chat request
   without Classify, plugin loading, or acquisition;
4. valid configuration with authorization but no retained plugin selection
   takes one ordinary Chat request without Classify, plugin loading, or
   acquisition;
5. valid configuration with authorization and a retained plugin selection but
   an over-4,096-byte question takes one ordinary Chat request without
   Classify, plugin loading, or acquisition;
6. the dedicated decision surface is caller-local, accepts only the fixed
   projection, and cannot reach a declared remote classifier;
7. unavailable, failed, and invalid Classify produce one ordinary Chat request
   and never acquisition;
8. `ordinary` and `external` decisions follow the exact maximum-work table;
9. the external branch uses the question unchanged as RFC-0078 query, without
   model-generated or deterministic rewriting, truncation, or extraction;
10. exactly one retained selected plugin is discovered, loaded, and invoked only
   after an `external` decision, with no startup plugin activity;
11. plugin, acquisition, and source-grounded failures have no retry, alternate
   provider, reclassification, or local-answer substitution;
12. all RFC-0077 validation precedes source-grounded routing and source URLs are
   never followed; and
13. enabled authorization always uses the closed tagged verbose/JSON result,
    truthfully distinguishes the branch and preserves supplied-source
    provenance, while valid configuration with absent authorization preserves
    legacy ordinary Chat output exactly.

## Open questions

- The exact `hac config` spelling for enabling and disabling the Chat automatic
  external-information authority.
- The exact private retained serialized field name.
- The exact URI/name of the dedicated local decision surface.
- The exact fixed decision-projection wording and serialization within the
  accepted semantic invariants.
- The exact human verbose formatting.
- The exact JSON field spellings within the accepted tagged-envelope contract.

## Decision

Accepted.

HAC may retain one separate Chat-specific authorization for bounded automatic
external-information use in native one-shot Chat. RFC-0095 retained
acquisition-plugin selection remains selection only and grants no Chat
authority by itself.

After valid RFC-0094 retained-state resolution, automatic fallback is
considered only when authorization is present, one retained RFC-0078 plugin is
selected, and the exact question fits RFC-0078's 4,096 UTF-8-byte query bound.
Otherwise the invocation remains ordinary Chat without a decision or
acquisition.

Eligible invocations may perform exactly one caller-local, HAC-owned two-label
decision using the existing `classify` capability through a dedicated bounded
local decision surface. The ordinary and source-grounded Chat branches retain
their existing routing semantics.

An external decision permits the caller to invoke exactly the retained
RFC-0078 plugin once with the exact Chat question as `QUERY`, followed by at
most one RFC-0077 source-grounded Chat request. There is no query rewriting,
truncation, retry, alternate provider, loop, or ordinary-Chat substitution
after acquisition begins.

Interactive Chat remains unchanged. Acquisition remains caller-owned, provider
credentials remain plugin/operator-owned, startup remains inert, and this
decision introduces no new executable capability, provider framework, generic
permission framework, or secrets manager.
