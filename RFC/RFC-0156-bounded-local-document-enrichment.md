# RFC-0156: Bounded Local Document Enrichment for External Information

Status: Draft

Date: 2026-10-15

Author: frian

## Summary

This Draft proposes one bounded extension to the existing External Information
caller path. After an already authorized, exactly selected Search plugin returns
up to five untrusted candidates, a HAC-owned caller-local document-enrichment
component may attempt, in provider result order, to retrieve and locally extract
HTML from up to five corresponding public HTTPS URLs. It selects bounded
passages before constructing fresh `SourceEvidence` values, which then enter
the existing Source-Grounded Chat path.

The component belongs to the main `home-ai-cluster` Python distribution. It is
an internal module conceptually named `hac-extract`; that is a working name,
not an accepted public CLI, package, distribution, entry point, service, or
capability. It is neither a plugin nor provider-specific. This Draft authorizes
no implementation, dependency, configuration, or accepted architectural change.

The proposal works independently with either the RFC-0079 SearXNG Search plugin
or the RFC-0093 Tavily Search plugin. SearXNG requires neither Tavily nor an
account or key; Tavily Search requires neither Tavily Extract nor any
cross-provider composition. It changes no routing, runtime adapter, capability,
or Source-Grounded Chat execution behavior.

## Existing boundaries and evidence

[RFC-0077](RFC-0077-bounded-source-grounded-chat.md) owns the complete
provider-neutral `SourceEvidence` contract. A URL in evidence is provenance,
not an action target: the core, runtime adapter, and selected execution node
must not follow it. [RFC-0078](RFC-0078-optional-external-information-acquisition-plugin-boundary.md)
defines an explicit caller-selected Search-plugin invocation before fresh
evidence construction and validation. RFC-0079 and RFC-0093 each make one
provider-specific Search request; [RFC-0095](RFC-0095-retained-external-information-plugin-choice.md)
retains plugin selection but grants no disclosure authority. [RFC-0096](RFC-0096-bounded-operator-authorized-chat-external-information-fallback.md),
[RFC-0133](RFC-0133-bounded-explicit-loopback-browser-external-information.md), and
[RFC-0134](RFC-0134-bounded-automatic-conversational-external-information.md)
define separate explicit and automatic Search surfaces. [RFC-0154](RFC-0154-bounded-external-information-source-expansion.md)
preserves at most five sources, 2,048 UTF-8 bytes per content field, 20,480
aggregate evidence bytes, a 65,536-byte canonical projection bound, and
complete validation before routing.

Rejected [RFC-0064](RFC-0064-bounded-public-url-summarization.md) established
that URL retrieval authority and its transport safety cannot be inferred from a
provenance URL. Its rejection remains in force; this Draft does not authorize a
generic fetch or URL-summarization feature.

The local feasibility record at
`/tmp/hac-searxng-local-document-feasibility-q4ZeFF/` demonstrated, in mocked
offline urllib3 2.6.3 tests, a plausible resolve-once, public-address-filtered,
IP-pinned HTTPS path that preserves the origin hostname for SNI, `Host`, and
certificate-name parameters, and a direct-pool configuration without a proxy.
It did not demonstrate real DNS, TCP, TLS, CA-root validation, or certificate
verification. It does not establish complete SSRF protection or a hard overall
deadline; `Timeout.total` does not bound a response that continues slowly
streaming. The document-evidence investigation also found that deterministic
selection can sometimes help, but that cleaning and neighboring passages can
lose useful material or add noise. No cleaning rule is generally superior.

## Problem

Search snippets can be too short for useful documentary answers. HAC needs a
small, explicit way to enrich the existing selected Search candidates without
making result URLs generally actionable, building a Web-research system, or
granting URL authority to an execution node.

## Goals

- Preserve Search-only behavior and the unchanged plugin contract:
  `async acquire(query: str) -> list[dict[str, str]]`.
- Keep authorization, enrichment invocation, lifecycle, and final validation
  in the acquisition caller.
- Attempt in original provider order no more than five eligible returned URLs,
  sequentially, with no additional Search request, discovered URL, retry, or
  provider fallback.
- Preserve RFC-0077/RFC-0154 evidence validation and all of its bounds before
  routing.
- Keep document retrieval local to the authorized caller process; the selected
  Chat node receives only the validated question and evidence.

## Non-goals

This Draft does not authorize a new plugin, distribution, repository, service,
public command, capability, browser, crawler, JavaScript, redirect, proxy,
cookie, ambient credential, HTTP, retry, concurrency, worker pool, queue,
document-acquisition framework, model-generated URL selection, Tavily Extract,
RAG, embeddings, vector search, persistence, cache, runtime-adapter change,
routing change, or production implementation.

## Alternatives and ownership

| Placement | Benefit | Cost and compatibility |
| --- | --- | --- |
| HAC-owned caller-local enrichment after plugin acquisition | One provider-neutral implementation; the caller already owns the authorized operation, lifecycle, fresh evidence construction, and final validation | Requires a narrow RFC-0078 amendment because its current caller may not turn returned provenance URLs into retrieval destinations. |
| Helper invoked inside each Search plugin | Keeps retrieval beside provider request code | Gives two independently installed plugins common URL authority, duplicates a common concern, and obscures caller-owned authorization and lifecycle. It would require plugin imports/knowledge of enrichment and is not proposed. |

This Draft proposes the first placement. The internal HAC component receives
already returned candidate data only after the caller has established the
separate authorization for this turn. It does not own Search, plugin/provider
selection, routing, inference, Chat execution, persistence, or a listener.
Neither plugin imports it, receives an enrichment-permission argument, nor
knows whether enrichment is enabled. The plugin receives only its existing
Search query and returns its unchanged list of three-field dictionaries.

Acceptance would narrowly amend RFC-0078 to permit the authorized acquisition
caller, after its one selected plugin invocation and before fresh RFC-0077
evidence construction, to use this HAC-owned bounded component on returned
candidate URLs. The amendment must retain the one-plugin invocation, unchanged
plugin callable/return contract, caller-owned final validation, and ordinary
server's lack of global URL authority. It must not amend RFC-0078 itself in
this PR or create a generic retrieval/plugin framework.

## Authorization and process ownership

Existing Search authority remains Search-only. A retained plugin selection,
plugin installation, HAC startup, ordinary Chat, and RFC-0134 automatic Search
authority alone never permit contacting a result URL. An authorized Search turn
with enrichment disabled performs no document retrieval.

The caller owns one additional ephemeral document-enrichment authority for the
specific turn. For the existing surfaces, this Draft proposes:

| Surface | Search authority today | Proposed enrichment authority |
| --- | --- | --- |
| Explicit `hac external-information` | Explicit operation | An additional explicit per-operation document-enrichment flag; `--plugin`, query, and question are insufficient. |
| RFC-0133 explicit native loopback browser acquisition | Current-page explicit operation | A separate visible current-page document-enrichment control for that operation, default off and non-retained. |
| RFC-0134 automatic native loopback browser Chat | Current-page automatic External Information control | A separate visible `Allow local document enrichment` control, default off and non-retained; it is necessary in addition to automatic Search authority. |
| Foreground interactive Chat | Explicit `--external-information` process flag | An additional foreground `--document-enrichment` flag, valid only with the existing Search authority and not retained. |
| RFC-0096 retained one-shot Chat fallback | Retained one-shot Search authority | Search-only. This Draft proposes no separately authorized enrichment mechanism and does not extend retained RFC-0096 authority. |

The acquisition caller is not always a short-lived CLI. Under RFC-0133 and
RFC-0134 it can execute inside the already-running ordinary HAC process. That
process may execute enrichment only while handling the specifically authorized
turn; it does not gain a process-global or startup-time retrieval permission.
The source-grounded execution node never receives URL-retrieval authority, and
final evidence URLs remain provenance only.

For explicit CLI operations, Search `QUERY` and source-grounded Chat `QUESTION`
may differ. The component sends neither question as a URL parameter nor request
body to a document website.

## Proposed flow and up-to-five policy

```text
authorized acquisition caller
  -> one selected Search plugin: acquire(query)
  -> up to five returned candidates in provider order
  -> HAC-owned sequential local enrichment attempts for eligible candidates
  -> fresh complete SourceEvidence validation
  -> existing Source-Grounded Chat
```

The first-version selection policy is deterministic: inspect at most the first
five returned candidates in their original provider order; for each candidate,
attempt at most one retrieval when its URL is eligible. It neither ranks,
rewrites, nor lets a model choose URLs. An ineligible candidate consumes no
network attempt and never causes a replacement URL to be discovered. Retrieval
is sequential; no concurrency, worker, queue, or framework is proposed.

Three counts are deliberately separate: there can be up to five returned Search
candidates, up to five eligible document-retrieval attempts, and up to five
final `SourceEvidence` entries. They need not be equal: an ineligible URL has
no retrieval attempt, and a failed retrieval can retain its original snippet.
The caller constructs the final ordered evidence list only after all permitted
per-document work has ended and then applies complete RFC-0077/RFC-0154
validation before any routing.

## Retrieval, preparation, and evidence boundaries

Each attempt is limited to an absolute public HTTPS URL without credentials.
It resolves before connecting; all answers that are private, loopback,
link-local, multicast, unspecified, reserved, or otherwise special are
rejected. The chosen implementation must preserve the invariant that a
validated hostname cannot connect to a non-public destination, while retaining
normal CA and hostname certificate verification. It permits no redirect,
proxy, cookie, ambient credential, retry, JavaScript, or subresource request.
Only HTML is accepted; raw HTML, extracted text, and documents are not
persisted.

The component owns finite per-document connection/header/read and encoded,
decoded, extracted-text, and selected-passage limits. It may obtain more HTML
bytes than the eventual evidence-content budget, but performs deterministic
bounded text preparation and passage selection before constructing evidence.
It must not silently truncate an already constructed `SourceEvidence` object.
The selected title, original provenance URL, and selected passage form fresh
evidence subject to the unchanged 2,048-byte content limit, five-source limit,
20,480-byte aggregate limit, and 65,536-byte projection limit.

IP-pinned urllib3 HTTPS remains a candidate mechanism, not an accepted HAC or
plugin dependency. Any selected dependency belongs to the main HAC distribution,
must be explicitly packaged, tested, and locked, and must not be placed in the
SearXNG or Tavily plugins merely for this shared functionality. System Python's
urllib3 installation is not a project dependency contract.

## Partial failure, global termination, and privacy

A normal per-document failure is evidence-level degradation within an already
authorized Search acquisition, not ordinary-Chat or provider fallback. The
proposed policy is to preserve the original Search snippet for an ineligible
URL, timeout, retrieval rejection, empty document, oversized document, or no
useful selected passage, provided the final complete evidence list validates.
Successful retrieval replaces that candidate's snippet with the selected
document passage. Original result order is always preserved; no extra URL,
Search request, provider, or Tavily Extract request compensates for failure.

For example, with five valid SearXNG candidates, successful retrievals for 1,
2, and 4 and failures for 3 and 5 produce evidence in this same order:
document passages for 1 and 2, the original snippet for 3, a document passage
for 4, and the original snippet for 5. The full list then undergoes final
RFC-0077/RFC-0154 validation. The alternative—dropping failed candidates—would
reduce untrusted snippet carry-through but needlessly loses existing authorized
Search evidence and can yield fewer sources; this Draft proposes preservation
instead, subject to review.

Per-document failure differs from global termination. The whole enrichment
operation has a finite overall lifecycle in addition to every per-document
bound. Global expiry, caller cancellation, client disconnect, or loss of the
specific turn's authorization prevents subsequent HAC-owned stages, including
new retrieval attempts, evidence construction, routing, and Source-Grounded
Chat. No late Source-Grounded Chat may start after cancellation or global
expiry, even if an underlying blocking read later returns. `urllib3`
`Timeout.total` does not itself meet this hard lifecycle requirement. This
Draft does not choose subprocesses, workers, or another execution framework.

Privacy remains explicit: the query goes to the selected Search provider under
its existing authorization; each eligible attempted document creates one
outbound HTTPS request, up to five, and its public website observes the
connection and requested URL; HTML processing and passage selection stay local;
the selected Chat node receives only validated question/context and bounded
evidence. There is no external extraction provider. Default logs, metrics,
traces, histories, and retained configuration must not retain query, question,
URL, HTML, selected passages, credentials, or generated responses.

## Required implementation proofs

Before production implementation is considered ready, focused local and
falsifiable proofs must show:

- Search-only behavior is unchanged and no retrieval occurs without the
  separate caller-owned authorization.
- Both Search plugins independently use the same HAC-owned component while
  retaining the exact `acquire(query)` contract.
- Up to five results are processed in provider order, sequentially, and never
  exceed the number of eligible candidates or five total attempts.
- The selected per-source policy preserves a failed/ineligible candidate's
  original snippet, while a successful passage fits the 2,048-byte limit.
- Failure never triggers a second URL, second Search provider, Tavily Extract,
  or ordinary-Chat fallback; complete evidence validation precedes all routing.
- Controlled matching/non-matching TLS and destination-pinning fixtures verify
  the chosen transport behavior, without claiming the current mocked proof did.
- A narrowly scoped local slow-stream proof establishes per-document and global
  bounds and confirms cancellation or expiry prevents late Source-Grounded Chat.
- Default logs expose no sensitive query, question, URL, HTML, source content,
  or credential.

These proofs do not authorize their implementation in this RFC change.

## Trade-offs and open questions

Caller-local ownership makes the additional authority, lifecycle, shared
dependency choice, and final validation visible in the component that already
owns the operation. It expands that caller's accepted responsibility and needs
a narrow RFC-0078 amendment, but avoids giving separate plugins hidden common
retrieval behavior. Up to five sequential attempts improve documentary coverage
while increasing bounded latency and website disclosures; the overall deadline
and no-compensation rule keep that cost finite and understandable.

Architectural review still must decide the exact public controls/flag spellings,
the numeric per-document and overall limits, the concrete dependency and
transport mechanism, and the final deterministic extraction/selection rules.
Those questions must not be resolved silently during implementation.

## Decision

Draft. No production implementation, dependency, accepted RFC amendment,
configuration, public command, or merge authorization is granted.
