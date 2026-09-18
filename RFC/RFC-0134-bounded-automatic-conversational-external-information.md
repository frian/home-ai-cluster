# RFC-0134: Bounded Automatic Conversational External Information

Status: Draft

Date: 2026-09-18

Author: frian

## Summary

This RFC proposes bounded automatic External Information for two conversational
Chat surfaces, each with its own explicit, ephemeral authorization:

- ordinary/native loopback browser Chat, while a clearly visible current-page
  `Allow automatic External Information` control is enabled; and
- RFC-0087 native interactive Chat, only when its foreground invocation starts
  as `hac chat --external-information`.

The automation may decide whether to acquire external evidence. It must never
generate, rewrite, derive, summarize, expand, resolve, or plan an acquisition
`QUERY`. When an authorized conversational turn takes the external branch,
`QUERY` is exactly the newest operator-supplied user turn, byte-for-byte. No
earlier conversation content reaches acquisition. A turn such as `And
tomorrow?` must remain ordinary if it is not useful unchanged as a standalone
query.

This proposal reuses the retained exact RFC-0095 plugin choice as selection,
not authorization; the fixed caller-local RFC-0096 decision; RFC-0078's
single-plugin acquisition boundary; and RFC-0077's source-grounded Chat
boundary. It narrowly extends RFC-0077 with optional validated
`prior_messages`, allowing a successful external turn to preserve ordinary
conversation context without making evidence hidden future conversation state.

It does not extend the retained RFC-0096 one-shot authorization to browser or
interactive conversations, turn `/v1/chat` into an acquisition operation, or
introduce query planning, a research capability, provider selection, source
memory, or background work.

## Context

RFC-0096 accepts one bounded automatic External Information fallback for
native one-shot Chat only. It deliberately excludes RFC-0087 interactive Chat
and browser Chat. Its retained `chat_external_information_fallback` fact is
therefore a narrow authorization with an existing compatibility meaning.

RFC-0077 accepts bounded source-grounded Chat from already supplied normalized
evidence, but grants no acquisition authority. RFC-0078 places acquisition at
the explicit CLI caller edge, selecting one exact plugin, loading it lazily,
invoking it once, reconstructing fresh evidence, and then making a
source-grounded Chat request. RFC-0095 permits retaining only the exact plugin
selection. RFC-0079 and RFC-0093 establish separate SearXNG and Tavily plugin
contracts.

RFC-0133 adds one separately visible, explicitly submitted External Information
operation to the ordinary/native loopback browser. It narrowly permits trusted
plugin execution in that long-lived process only for that operation, subject to
the accepted native Host/Origin/JSON authority and RFC-0082 disconnect
ownership. It retains an operator-supplied distinct `QUERY` and `QUESTION`.

RFC-0087 keeps interactive Chat as a foreground process with in-memory,
successful user/assistant conversation only, bounded candidate turns,
rollback on failed turns, and no persistence. RFC-0062 establishes the
ordinary native loopback browser; its Chat history is current-page state.
RFC-0130 is a distinct trusted-LAN capability-only browser authority, not a
widening of loopback authority. RFC-0132 permits retained Configuration
management but correctly gives it no automatic acquisition effect.

The current implementation has seams for the one-shot fallback, interactive
conversation, browser current-page history, source-grounded request/result and
remote transport, the fixed decision operation, and RFC-0133's explicit
browser acquisition operation. Those implementation facts help describe the
existing boundary; accepted RFCs, rather than implementation convenience,
remain architectural authority.

## Problem

Conversational Chat can benefit from current external evidence, but a
conversation-aware automatic branch can easily become a hidden research or
query-planning system. Reusing a previously retained one-shot authorization
would silently widen disclosure after an upgrade. Sending context to a
provider, generating a search query from references, or retaining sources
would make the actual disclosure and future conversation state harder to see.

The project needs to decide whether browser and interactive conversational
surfaces can receive bounded automatic acquisition while preserving explicit
per-surface authority, an operator-authored deterministic query, conversational
context for the final answer, and the existing local-first privacy boundaries.

## Goals

This RFC proposes to:

- authorize automatic External Information only through one explicit
  current-page browser control or one explicit interactive CLI flag;
- preserve the exact newest user turn as the only possible acquisition query;
- preserve successful conversation context for source-grounded Chat through a
  small validated RFC-0077 extension;
- keep prior conversation out of decision and acquisition stages;
- retain only user text and generated assistant text after a successful
  external turn;
- make failure, cancellation, maximum work, and provider execution location
  explicit; and
- preserve ordinary Chat, explicit External Information, trusted-LAN, remote
  execution, plugin, provider, and retained-configuration boundaries.

## Non-goals

This RFC does not propose automatic External Information in trusted-LAN browser
Chat, receiver authority, OpenAI-compatible Chat, Code, Summarize, Classify,
Image Generation, Aider, or workspace coding. It does not add a new
`external-information`, `web`, `search`, `browse`, `retrieve`, or `research`
capability.

It does not add model-generated queries, query rewriting, pronoun or reference
resolution for acquisition, whole-conversation classification, plugin/provider
ranking, provider-health selection, alternate-provider fallback, URL retrieval
or following, crawling, retry/research loops, agents, tools, function calling,
server conversation sessions, source memory, a plugin manager, a provider
registry, a secrets UI or credential framework, persistence, a database,
workers, queues, schedulers, process-global serialization, or dependencies.

## Proposal / accepted architecture candidate

If accepted, this RFC adds only the following two conversational authorization
surfaces:

```text
ordinary/native loopback browser Chat + current-page control ON
RFC-0087 interactive `hac chat --external-information`
```

They are independent of the existing retained RFC-0096 authorization. In both
cases, a retained exact RFC-0095 plugin selection is a necessary selection fact
for the automatic branch, but is never itself disclosure authority.

### Authorization model

Three scopes remain distinct:

| Scope | Authority | Applies to |
| --- | --- | --- |
| RFC-0096 | retained `chat_external_information_fallback` | native one-shot Chat only |
| This RFC browser | visible, current-page browser control | native loopback browser Chat only |
| This RFC CLI | `hac chat --external-information` process flag | that foreground interactive session only |

RFC-0096 continues to authorize only its existing one-shot Chat path. A user
who previously set that retained fact must not gain automatic browser or
interactive disclosure after an upgrade. Existing one-shot behavior otherwise
remains unchanged; this RFC's CLI flag does not change `hac chat MESSAGE`.

#### Browser authorization

The ordinary/native loopback Chat page may offer one clearly visible checkbox
or toggle meaning conceptually `Allow automatic External Information`. Its
final wording is an implementation detail, but it must make clear that the
current user turn may be disclosed to the retained selected acquisition
plugin/provider if the bounded decision chooses the external branch.

It defaults OFF on every page load. It is visible and current-page only; it
does not mutate retained Configuration and uses no cookie, localStorage,
sessionStorage, database, or server session. Reloading or closing the page
naturally clears it. An operator may leave it enabled for later turns in that
page. With it OFF, browser Chat is exactly existing ordinary `/v1/chat`:
zero decision, discovery, import, credential, provider, or acquisition work.

#### Interactive CLI authorization

RFC-0087 gains the no-message form:

```text
hac chat --external-information
```

Existing executable/root aliases forward it under their normal rules. No short
option is introduced. The flag is not retained and authorizes only this
foreground interactive process. It is invalid with a positional one-shot Chat
message, `--message`, and output forms already incompatible with RFC-0087
interactive Chat. Plain `hac chat` remains ordinary interactive Chat even when
the RFC-0096 retained one-shot authorization is enabled.

### Retained plugin selection and retained-state failure

Both new surfaces reuse one exact RFC-0095 retained plugin name; they add no
plugin picker, enumeration, inferred/default provider, health or credential
inference, or per-turn provider selection. The retained RFC-0096 boolean is
irrelevant to them.

For a browser turn, retained configuration is resolved and validated per
explicitly authorized turn, consistent with the long-lived browser process and
RFC-0133. For an eligible interactive invocation, existing TTY/input
eligibility is established first; retained configuration is then loaded and
validated once. The exact plugin name, or absence, is a process-local session
snapshot. Later configuration changes cannot mutate the running session.

Malformed or semantically invalid retained configuration is a visible retained
configuration failure. On an explicitly authorized conversational surface it
fails safely before decision, plugin discovery/import, credential access,
provider activity, acquisition, or Chat execution. HAC must not repair, ignore,
or infer around it.

A valid configuration with no retained plugin does not fail ordinary
conversational Chat. It makes the automatic branch ineligible: no decision,
discovery, import, credential inspection, provider access, or acquisition;
exactly one ordinary full-context Chat turn follows.

### Per-turn eligibility

For an explicitly authorized surface, HAC evaluates cheap local eligibility
before Classify or plugin activity. It requires valid retained state, an exact
retained RFC-0095 plugin name, a newest user turn of at most 4,096 UTF-8 bytes
(the RFC-0078 `QUERY` bound), and a contextual source-grounded representation
within the bound below. HAC must not truncate or rewrite a turn to make it
eligible.

If an otherwise valid ordinary Chat turn is ineligible, it makes one ordinary
full-context Chat request without decision, plugin discovery/import, credential
inspection, or provider contact. RFC-0087's existing 65,536-byte candidate
conversation bound remains authoritative: an over-bound interactive candidate
retains its local rejection and does not fall through to ordinary Chat.

For the new automatic browser branch only, a candidate whose successful prior
conversation plus newest question exceeds the contextual source-grounded bound
is ineligible and proceeds as ordinary browser Chat. This does not narrow
existing ordinary browser Chat.

### One fixed local decision

This RFC reuses RFC-0096's architectural decision shape: exactly one existing
caller-local `classify` inference, never routed to a declared remote, with only
the fixed HAC-owned labels `ordinary` and `external`. It has no confidence,
rationale, score, threshold, repeated decision, model-selected plugin, or
acquisition before decision.

The decision sees only the exact newest user turn, as untrusted subject data;
it never sees conversation history. This RFC narrowly clarifies the fixed
RFC-0096 semantics: `external` means both that external evidence is likely to
materially improve the answer under the already authorized bounded policy and
that the exact supplied question is sufficiently self-contained to use
unchanged as an acquisition `QUERY`, without prior conversation context.
Otherwise its result is `ordinary`. This remains conservative for existing
one-shot use and introduces no third label such as `rewrite`, `clarify`,
`search`, `needs-context`, or `unknown`.

Caller-local Classify unavailability, construction/request failure, or invalid
result produces exactly one ordinary full-context Chat turn. It does not
acquire, retry Classify, expose classifier details, or select a remote
classifier.

### Contextual RFC-0077 extension

This RFC proposes a narrow RFC-0077 amendment. `SourceGroundedChatRequest`
gains an optional public/native `prior_messages` field, defaulting to an empty
list. Existing one-shot callers that omit it retain their semantics.

`prior_messages` contains only complete successful prior conversational
exchanges as ordinary `ChatMessage` values:

- roles are only `user` and `assistant`;
- an empty list is valid;
- a nonempty list starts with `user`, alternates strictly, and ends with
  `assistant`; and
- it therefore contains complete previous user/assistant pairs only.

It contains neither the current user turn nor a system message, evidence,
plugin/provider/query/credential metadata. Current text remains the existing
separate `question`.

The aggregate UTF-8 length of every `prior_messages[*].content` plus `question`
must not exceed 65,536 bytes. This contextual source-grounded bound does not
replace RFC-0077 evidence bounds or reduce existing non-contextual behavior
when `prior_messages` is empty, except for the existing question bound. It adds
no token counting or runtime context-window discovery.

The conceptual projection is, in order:

```text
existing HAC-owned source-evidence system guard
ordered prior_messages
existing untrusted source-evidence data message
current exact question
```

With an empty list, RFC-0077's current three-message projection remains
unchanged. Conversation remains ordinary Chat context; source evidence remains
explicitly untrusted data. No prior message gains system authority.

The native `/v1/chat/sources` request may accept this additive field while
remaining acquisition-neutral: it still accepts only supplied normalized
evidence. The closed internal/remote source-grounded transport may carry the
same validated `prior_messages`; receiver reconstruction validates it again.
A trusted remote selected for ordinary `chat` may receive validated prior
messages, current question, sources, and routing constraints, but never a
separate acquisition query, plugin/provider identity, credentials, decision
state, or provider-response metadata. This is existing trusted Chat execution,
not remote acquisition.

### Browser flow and authority

With browser authorization OFF, the flow is unchanged:

```text
browser Chat -> existing /v1/chat
```

With it ON, the browser may call one separate, closed native-loopback browser
facade operation for that turn. It must not overload `/v1/chat` with hidden
acquisition. The exact URI and private JSON wrapper are implementation details;
this is not a stable general acquisition API. It receives only current-page
conversation sufficient to identify complete successful prior exchanges and
the newest turn. It accepts no plugin/provider/credential, distinct query,
arbitrary labels, or caller-controlled routing constraints. Its use represents
the page's explicit ephemeral authorization.

```text
authorized browser turn
  -> validate conversation
  -> validate retained configuration
  -> no plugin / query or contextual ineligible
       -> one ordinary full-context Chat
  -> one caller-local fixed decision on exact newest turn
       -> unavailable/failure/ordinary -> one ordinary full-context Chat
       -> external -> exact retained plugin, invoked once with exact newest turn
          -> fresh RFC-0077 evidence
          -> contextual source-grounded Chat with prior successful conversation
```

No branch produces both an ordinary and source-grounded answer. Once acquisition
starts, failure does not fall back to ordinary Chat.

RFC-0133's ordinary-process plugin exception is narrowly extended only here:
after a valid explicitly authorized loopback turn reaches this operation, the
ordinary process may inspect RFC-0078 entry-point metadata, lazy-load the exact
retained plugin, invoke it once, and use plugin/provider-owned process state.
That authority does not arise from startup, installation, credentials, retained
selection, retained RFC-0096 authorization, ordinary Chat with control OFF,
Configuration access, or another capability.

The facade has RFC-0133's native authority discipline: exact accepted native
Host, independently listener-derived authority, exact same-origin Origin,
bounded `application/json` non-simple request, and no CORS. Attacker-controlled
Host and Origin must not authenticate each other. It is absent from trusted-LAN
and receiver authority. This does not add accounts, sessions, tokens, OAuth,
TLS, or generic browser authentication.

It is one HAC-owned foreground operation across decision, optional acquisition
and reconstruction, then ordinary or source-grounded Chat. Confirmed disconnect
uses RFC-0082/RFC-0133 ownership: abandon it, propagate best-effort
cancellation, discard late work, publish no late result, and create no
background continuation. HAC uses cancellation-win checkpoints between stages:
after disconnect wins it must not begin acquisition from a late decision, final
Chat from a late acquisition, or ordinary Chat from a later branch. This does
not promise forced termination or rollback of non-cooperative runtime/plugin
code or already disclosed provider requests. RFC-0082 terminal precedence is
unchanged.

Its success result is closed and distinguishes `ordinary` from
`source-grounded`, conceptually a tagged `branch` plus existing corresponding
result. Exact facade JSON is private. The page retains only user text and
generated assistant text; it displays ordered supplied sources separately for
the completed assistant turn, with inert plain-text URLs. It neither treats
sources as verified/current/sentence-level citations nor fetches, previews,
resolves, enriches, or follows them. Provenance display is current-page only.

### Interactive CLI flow

`hac chat --external-information` remains RFC-0087's foreground,
process-owned conversation: complete successful user/assistant text in memory,
one candidate at a time, independent ordinary routing per turn, the existing
65,536-byte candidate bound, failed-turn rollback, EOF/Ctrl-C termination, and
no persistence. At entry it validates existing TTY requirements, loads and
validates retained configuration once, snapshots the exact plugin or absence,
and performs no plugin discovery/import, credential inspection, or provider
contact. With no snapshot plugin, all turns are ordinary.

For each valid candidate turn:

```text
absent snapshotted plugin / newest turn > 4,096
  -> one ordinary full-context Chat
otherwise
  -> one caller-local fixed decision on exact newest turn
     -> unavailable/failure/ordinary -> one ordinary full-context Chat
     -> external -> invoke exact snapshotted plugin once with exact newest turn
        -> fresh evidence -> one contextual source-grounded Chat request
```

No history reaches the acquisition plugin and no query is generated from it.
Before acquisition, decision failure produces ordinary Chat. After acquisition
starts, missing/load/configuration/credential/provider/acquisition failure is
the existing privacy-safe External Information failure: no ordinary fallback,
retry, other plugin, or reclassification. A failed external or source-grounded
turn prints only safe failure, retains neither candidate user nor assistant
text, preserves earlier successful context, and keeps the session active unless
the operator ends it. A structurally valid source-grounded result with empty
generated content is RFC-0087's existing safe invalid-cluster-response failure
and follows the same rollback. One-shot empty-result semantics do not change.

For a successful source-grounded turn, interactive presentation may narrowly
add a human-readable ordered `Supplied sources` section after generated content,
containing existing bounded title, inert URL provenance string, and content.
Spacing is implementation detail. It does not add interactive JSON/JSON Lines,
verbose mode, event stream, clickable URL, terminal UI framework, or Markdown
renderer. Only generated assistant text continues into the next request.

### Provider invocation locations

For browser automatic acquisition, the RFC-0079 SearXNG or RFC-0093 Tavily
plugin executes in the already-running ordinary HAC process only after the
authorized loopback turn takes the external branch. Existing provider contracts
remain unchanged. Tavily consequently reads its plugin-owned `TAVILY_API_KEY`,
if needed, from that process environment only.

For interactive acquisition, the selected plugin executes in the foreground CLI
process; Tavily consequently reads only that CLI process environment. HAC core
and browser protocol must never read, accept, transfer, retain, persist, log,
expose, or place a credential in evidence, routing, or forwarded environment.

RFC-0133's separate browser External Information view remains unchanged, as
does `hac external-information`. They remain appropriate when an operator wants
a distinct QUERY and QUESTION, an explicit plugin override, or direct
deliberate acquisition.

### State, privacy, concurrency, and maximum work

After any successful external turn, future conversation state contains only the
original user text and generated assistant text. Sources are completed-turn
presentation/provenance only: never silently inserted, cached, accumulated, or
reused as hidden research context. A later assistant message may mention facts
from them; that generated visible text is ordinary conversation content.

This proposal adds no HAC-owned persistence of conversation, queries,
questions, sources, provider results, decisions, or acquisition results. It
adds no browser content storage, cookie, server session, database, history
service, cache, analytics, or telemetry. Arbitrary trusted plugin module state
resident in the browser process remains the accepted RFC-0133 trusted-plugin
trade-off, not HAC-owned persistence.

Independent browser pages may submit independent authorized turns concurrently;
an existing page-local foreground gate may prevent deliberate overlap within a
page. Interactive CLI owns one foreground submitted turn. This RFC adds no
global mutex, queue, semaphore, scheduler, or thread-safety claim for arbitrary
trusted plugins.

Maximum work is finite:

| Turn outcome | Maximum work |
| --- | --- |
| authorization absent, or authorized but plugin/query/context ineligible | one ordinary Chat |
| decision unavailable, fails, or returns `ordinary` | one decision, one ordinary Chat |
| `external`, then acquisition fails | one decision, one plugin invocation, no Chat result |
| `external`, then acquisition succeeds | one decision, one plugin invocation, one source-grounded Chat |

There is never a second decision, second plugin, provider fallback, ordinary
answer after acquisition failure, recursive acquisition, repeated retrieval,
or background continuation.

## Relationship to prior RFCs

- **RFC-0062:** browser Chat gains one optional current-page authorization and
  dedicated loopback facade; ordinary browser Chat remains unchanged when OFF.
- **RFC-0077:** optional bounded `prior_messages` preserves successful
  conversation context. RFC-0077 remains acquisition-neutral.
- **RFC-0078:** its historical CLI caller rule remains; RFC-0133's browser
  exception remains; this RFC adds a second narrow browser invocation location
  only after authorization and an external decision.
- **RFC-0079 / RFC-0093:** provider contracts are unchanged; their accepted
  browser-process consequences also apply to this automatic browser operation.
- **RFC-0082:** disconnect ownership spans the complete browser automatic turn
  and requires cancellation-win checks before later HAC-owned phases.
- **RFC-0087:** interactive Chat gains one explicit flag and source provenance
  display for successful external turns, retaining only successful text context.
- **RFC-0095:** retained exact selection is reused unchanged and is not
  disclosure authorization.
- **RFC-0096:** retained authorization remains one-shot only. Its fixed
  decision is reused on newest-turn-only input and conservatively clarified to
  require unchanged standalone-query suitability for `external`.
- **RFC-0130:** trusted-LAN browser remains capability-only and gains no
  automatic acquisition authority.
- **RFC-0132:** Configuration gains no setting; RFC-0096 retained fallback
  does not control these new surfaces.
- **RFC-0133:** explicit browser External Information remains unchanged; its
  process-location and disconnect principles are narrowly extended here.

## Rationale

The project should permit useful automation only inside boundaries that an
operator can understand. An explicit browser control and process-local CLI flag
make authority visible at the place disclosure can occur. They avoid treating
retained one-shot consent as blanket conversational consent.

The newest-turn-only rule makes the potential disclosure inspectable: it is
the text the operator just supplied, unchanged. The fixed two-label decision
can choose whether evidence is worth obtaining, but cannot turn conversational
context into a concealed instruction for a provider. Preserving prior messages
only at the existing Chat boundary keeps a meaningful third turn possible
without making providers or later conversation inherit source material.

## Alternatives considered

### Reuse retained RFC-0096 authorization everywhere

Rejected. It would silently widen a previously granted one-shot disclosure
authority to browser and interactive conversations after upgrade.

### Generate a search query from conversation history

Rejected. It creates query-planning/model-directed disclosure authority and
makes disclosed text less obvious to the operator.

### Send entire history to the acquisition plugin, or classify it

Rejected. Only the newest exact turn may need disclosure. The decision remains
one bounded local question rather than a conversation resolver.

### Drop context on source-grounded turns

Rejected. A later answer could be disconnected from visible conversation.

### Retain sources in conversation history

Rejected. It would create hidden persistent/reused research context and alter
later ordinary Chat semantics.

### Add a search/research capability or generic orchestrator

Rejected. Acquisition remains a caller/browser edge before ordinary `chat`,
using existing bounded seams rather than a new routable capability or framework.

### Put automatic acquisition inside `/v1/chat`

Rejected. Ordinary Chat must remain acquisition-neutral unless the separate
explicitly authorized browser facade is invoked.

### Require retained RFC-0096 authorization as well

Rejected. The new browser control and CLI flag are independently sufficient
ephemeral authorization for their surfaces; retained plugin selection remains
separately necessary.

## Trade-offs

Follow-ups such as `And tomorrow?` may remain ordinary; an operator may need to
write a self-contained turn when external evidence is wanted. Contextual
source-grounded requests slightly enlarge RFC-0077 native and remote shapes.
Browser acquisition runs trusted plugin code in a long-lived process, retaining
RFC-0133's module-residency trade-off; browser and CLI can see different
provider-owned credential environments. Source evidence is deliberately not
reused. Per-surface explicit authorization is less convenient than implicit
retained consent, but makes privacy authority truthful and bounded.

## Impact

If accepted, later implementation would add a Draft-authorized browser facade,
an interactive flag and validation, bounded conversational source-grounded
models/projection/transport, turn-local provenance presentation, and focused
proofs. It would not change routing semantics, capabilities, provider contracts,
retained configuration format, explicit External Information, or ordinary Chat
when the new authority is absent.

## Proof expectations

A later implementation should demonstrate, without live provider/network tests:

1. RFC-0096 remains one-shot only; browser control defaults off/current-page
   only with no persisted setting/storage; interactive mode requires the flag
   and rejects one-shot forms.
2. The newest exact turn alone reaches both decision and acquisition; no prior
   content reaches plugins/providers and non-self-contained turns cannot rewrite.
3. Missing plugin or ineligibility produces ordinary Chat with no decision,
   discovery, provider, or credential work; decision is one caller-local
   Classify and decision failure produces ordinary Chat without disclosure.
4. `prior_messages` accepts only complete alternating successful pairs within
   the aggregate 65,536-byte bound; old empty/omitted requests retain the old
   projection, and remote transport carries context but no acquisition metadata.
5. Successful external turns retain only user/generated assistant text, with
   sources turn-local and not silently resent later.
6. Browser automatic operation exists only on native loopback with exact
   Host/Origin/JSON authority, not LAN/receiver; a disconnect during decision
   or acquisition cannot start a later HAC-owned phase after cancellation wins.
7. Browser plugin execution starts only after explicit authorization and
   `external`; browser/CLI provider credentials remain plugin-owned in their
   respective process environments and never traverse HAC protocol.
8. RFC-0133 explicit browser External Information, historical CLI External
   Information, browser Chat with control OFF, and interactive Chat without the
   flag remain unchanged. Acquisition failure never falls back to ordinary Chat;
   interactive failed external turns preserve earlier context only.
9. No global acquisition serialization, capability, query planner, provider
   framework, persistence, background work, retry/research loop, URL retrieval,
   or dependency is introduced.

Fake plugins, fake environment values, bounded request capture, and
deterministic seams should be sufficient.

## Open questions

Implementation-level details remain open: the precise browser control wording,
the private browser-facade URI and wrapper spelling, and human
spacing/punctuation for interactive source presentation. This RFC does not
leave open whether history becomes QUERY, query rewriting is allowed, retained
RFC-0096 authority widens, sources enter conversation history, trusted-LAN gets
acquisition, or acquisition becomes a capability.

## Decision

Pending.
