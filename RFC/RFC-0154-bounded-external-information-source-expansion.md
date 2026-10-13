# RFC-0154: Bounded External Information Source Expansion

Status: Draft

Date: 2026-10-13

Author: frian

## Summary

This proposal makes two coordinated, narrow amendments to the accepted
External Information architecture:

1. amend RFC-0077 so `SourceEvidence.content` accepts at most 2,048 UTF-8
   bytes rather than 1,024; and
2. amend RFC-0093 so its fixed Tavily Search request uses
   `chunks_per_source=2` rather than `1`.

The proposal preserves the five-source maximum, title and URL limits, the
20,480-byte combined evidence-field limit, the 65,536-byte canonical source
projection limit, complete validation before routing, and all existing
authority, privacy, acquisition, and failure boundaries. It neither guarantees
better answers nor authorizes implementation.

## Existing authority and evidence

[RFC-0077](RFC-0077-bounded-source-grounded-chat.md) owns the
provider-neutral `SourceEvidence` acceptance contract, deterministic
source-grounded Chat projection, and complete pre-routing validation.
[RFC-0078](RFC-0078-optional-external-information-acquisition-plugin-boundary.md)
owns the optional caller-edge acquisition-plugin boundary: a selected plugin
returns candidate title, URL, and content fields, while HAC reconstructs and
validates the complete RFC-0077 request. [RFC-0093](RFC-0093-bounded-tavily-acquisition-plugin.md)
owns Tavily's fixed request shape.

The retained [Tavily source-content comparison proof](../docs/tavily-source-content-comparison-proof.md)
made one authorized public Search call at each of one, two, and three chunks
per source. It measured five usable sources in every response. One chunk
returned 1,956 total content bytes (largest source 501 bytes); two returned
3,922 (largest 965); and three returned 6,407 (largest 1,472). The one- and
two-chunk sets passed the current RFC-0077 request validation. All five
three-chunk sources exceeded its present 1,024-byte individual-content limit,
so the complete request failed before routing.

That is one provider measurement, not a statistical sample or an
answer-quality evaluation. Provider result sets varied between calls;
`chunks_per_source` is a maximum, not a guaranteed content amount; and Tavily
does not promise a strict UTF-8 byte ceiling. Operator-run local-model
observations suggest that a more complete official-documentation passage can
improve a particular explanation, but no corresponding retained proof
establishes that observation, and both observed answers contained unsupported
claims. More evidence therefore does not establish more accurate, useful, or
source-supported generated answers.

The retained [source-content size investigation](../docs/tavily-source-content-size-investigation.md)
also records that the plugin copies selected nonblank title, URL, and content
unchanged. It does not truncate source content, and HAC validation is the
authoritative boundary.

## Problem

The current fixed Tavily one-chunk request and 1,024-byte provider-neutral
content envelope can leave ordinary source-grounded Chat with less evidence
than is useful for information-intensive questions. The completed measurement
shows that two chunks can nearly double available source text while remaining
within the current envelope in that one observation.

The project needs to examine a small increase in useful evidence without
turning External Information into configurable retrieval, accepting unbounded
provider output, or weakening validation, privacy, or routing boundaries.

## Goals

- Permit moderately larger provider-neutral source snippets, bounded at 2,048
  UTF-8 bytes per source.
- Request at most two Tavily chunks per source in RFC-0093's otherwise fixed
  Search request.
- Preserve independent per-field, aggregate, and canonical-projection
  validation before routing or model execution.
- Keep the acquisition-plugin boundary and ordinary `chat` routing unchanged.
- Make compatibility and safe rollout implications explicit.

## Non-goals

This RFC does not authorize configurable chunks or source-size limits, domain
inclusion/exclusion or YouTube filtering, result reranking, source credibility
or verification, other Tavily endpoints or request options, another request,
retry, provider fallback, raw-page extraction, URL crawling, RAG, embeddings,
storage, caching, a new capability, routing rule, model-adapter contract, or
generic search abstraction.

It does not change RFC-0077's system framing, source selection, source order,
normalization, or complete-request semantics. It does not address observed
model interpretation of the untrusted-source framing. It does not add logging,
persistence, telemetry, or any new network authority.

## Proposal

This RFC amends only the provisions stated below in RFC-0077 and RFC-0093.
All other accepted provisions of those RFCs, and all of RFC-0078, remain in
force. It does not supersede either RFC as a whole.

### RFC-0077 content bound amendment

`SourceEvidence.content` remains a nonblank string, but its maximum accepted
UTF-8 length becomes **2,048 bytes**. This is a general RFC-0077 contract
change, not a Tavily-specific rule: every current or future acquisition path
that constructs `SourceEvidence` uses the same limit.

Title remains limited to 512 UTF-8 bytes. URL remains limited to 2,048 UTF-8
bytes and remains an absolute HTTP(S) provenance string with an authority and
without user information. The one-through-five ordered-source constraint,
unchanged field preservation, and no-deduplication/no-ranking rules remain
unchanged.

An over-2,048-byte content field invalidates the entire source-grounded
request. HAC and acquisition callers must not truncate, rewrite, drop, or
selectively preserve a source to fit this bound.

### Preserved aggregate and projection bounds

The combined UTF-8 length of all accepted title, URL, and content fields
remains at most **20,480 bytes**. The canonical source-data projection remains
at most **65,536 UTF-8 bytes**. Both checks remain independent and complete
before routing.

With five sources at all individual maxima, the old theoretical field total was
`5 × (512 + 2,048 + 1,024) = 17,920` bytes. Under this proposal it is
`5 × (512 + 2,048 + 2,048) = 23,040` bytes. Thus individually valid sources
may now fail the unchanged aggregate limit. This is intentional: the aggregate
budget continues to bound the total evidence supplied to one execution rather
than silently expanding with one per-field amendment. Increasing it is not
needed to examine the operator's two-chunk objective and would be a separate
architectural decision.

Passing the aggregate check also does not ensure that canonical projection
passes. JSON escaping can enlarge serialized text, so the 65,536-byte
projection validation remains an independent protection. These values are byte
and serialized-message bounds, not model-token or context guarantees.

### RFC-0093 two-chunk amendment

RFC-0093's one fixed Tavily Search request changes only this field:

```json
"chunks_per_source": 2
```

All other fixed request fields remain exactly as accepted: `search_depth` is
`"basic"`; `max_results` is `5`; and `include_answer`,
`include_raw_content`, `include_images`, `include_image_descriptions`, and
`auto_parameters` are `false`.

The fixed HTTPS Search destination, exact operator query, one request, no
retries or pagination, no result-URL fetching, no provider-generated answer or
raw page content, plugin-owned credential, disabled ambient proxies, TLS
verification, disabled redirects, existing timeouts, 30-second deadline, one
simultaneous provider connection, 1 MiB decoded-response ceiling, unchanged
normalization, and privacy-safe failures remain unchanged. The plugin continues
to return its selected title, URL, and content fields unchanged; RFC-0077
validation remains caller/core owned.

Two chunks are a maximum provider request, not a promised number of chunks,
source size, or increase in relevant information.

### Validation and failure semantics

UTF-8 bytes, rather than character counts, remain authoritative. Multibyte
text can exceed the limit with fewer characters, and a provider can return a
longer-than-target two-chunk snippet. Title, URL, aggregate, and canonical
projection checks remain independently applicable.

Any invalid candidate makes the complete source-grounded request fail before
routing, remote transport, or model execution. It must not cause truncation,
source dropping, a retry with fewer chunks, an alternate provider request, or
implicit ordinary-Chat fallback. Acquisition/validation failures remain
distinct from the established routing or execution failures that can occur only
after a valid request enters ordinary Chat routing.

Larger accepted evidence can increase request memory, transport size, and model
context use. It does not remove tokenization or context constraints, and source
evidence remains untrusted private request content with the existing privacy
consequences.

### Provider-neutral behavior

The amended RFC-0077 maximum applies equally to Tavily, the RFC-0079 SearXNG
path, explicit External Information, RFC-0096 operator-authorized Chat
acquisition, RFC-0133 browser-triggered acquisition, RFC-0134 automatic
conversational acquisition, and local or trusted-remote source-grounded Chat.
It authorizes none of them to acquire more sources or alter how they acquire,
normalize, select, or route evidence. SearXNG and other plugins need not
return larger snippets. No provider gains source-size-specific normalization,
selection, routing, or network authority.

### Local and remote compatibility

`SourceGroundedChatRequest` is validated at the caller edge, public route, and
internal remote receiver. A newer caller can therefore form a request whose
content is 1,025 through 2,048 bytes, while an older public route or receiving
node still rejects it under the former 1,024-byte contract. Already-valid
sources at or below 1,024 bytes remain compatible in both directions.

This RFC introduces no version negotiation, transport version, downgrade,
fallback, or partial-success behavior. A newer request sent to an older
receiver fails validation before its local routing/execution, under that
receiver's established invalid-request handling.

If accepted, the safe order is: first implement and validate the enlarged
RFC-0077 contract in HAC core; then ensure every participating source-grounded
caller, public route, and trusted remote receiver uses that compatible contract
before relying on larger evidence across a boundary; only then independently
release or deploy the Tavily plugin change. This is rollout guidance, not
authorization to implement or deploy.

## Rationale

The two amendments serve one bounded operator objective: request more useful
Tavily evidence while giving the provider-neutral evidence contract enough
headroom to accept moderately larger snippets. They remain distinct in
ownership. RFC-0077 owns general source acceptance; RFC-0093 owns the
provider-specific fixed request; RFC-0078 remains unchanged because its plugin
boundary, ownership, and complete HAC validation are sufficient.

Two chunks are the smallest measured increase that nearly doubled returned
content while still passing the current contract in one retained proof. Three
chunks supplied more text, but all five observed snippets exceeded the present
individual bound and the experiment did not establish additional answer-value.
This is not a finding that three chunks are inherently unsuitable; it supports
two chunks as the smaller first proposal. A 2,048-byte envelope gives a clear,
provider-neutral margin above the observed two-chunk maximum of 965 bytes,
without treating a single observation as a hard provider limit.

## Alternatives considered

### Keep one chunk and 1,024 bytes

This preserves the smallest envelope and current proven behavior, but retains
the observed completeness concern and no additional evidence capacity.

### Request two chunks while retaining 1,024 bytes

This changes only the provider request, but leaves a narrow margin and a higher
risk that a valid provider response rejects the complete operation. The
observed two-chunk sizes do not establish robust future fit at that limit.

### Increase to 2,048 bytes and request two chunks

This preferred proposal remains fixed, bounded, and provider-neutral while
admitting moderately larger snippets. Its costs are larger accepted payloads,
mixed-version rejection risk, and no answer-quality guarantee.

### Request three chunks with a larger envelope

Three chunks can provide substantially more text, but the retained proof did
not establish additional usefulness and showed substantially greater individual
content sizes. It would require separate justification for a broader envelope
and its aggregate/projection consequences.

### Increase the content limit without changing Tavily chunks

This would expand general acceptance capacity but would not directly request
more Tavily evidence for the stated operator objective.

### Make chunks or limits configurable

Configuration would enlarge policy and operator surfaces without enough
evidence that the flexibility is needed.

### Retry with fewer chunks or truncate/drop sources

These alternatives silently alter evidence and accepted complete-request
failure semantics. They are not authorized by this proposal.

## Trade-offs

The proposal permits more source text, which can be useful but can also be
irrelevant, repetitive, misleading, stale, or too large for a selected model's
effective context. It raises the possible evidence and trusted-remote payload
size without changing the existing disclosure/trust model. The preserved
aggregate and projection limits retain bounded total exposure, at the cost that
some individually valid sets reject. The proposal is deliberately not a claim
about truth, freshness, citations, or generated-answer quality.

## Implementation and rollout implications

No implementation is authorized by this Draft RFC. If it is accepted, the HAC
repository work should be separately reviewable: update the general
`SourceEvidence` validation and focused caller, public-route, internal-receiver,
aggregate, projection, full-rejection, and UTF-8 boundary tests. It should
demonstrate acceptance at 2,048 bytes and rejection at 2,049 bytes, including
multibyte boundaries, without unrelated refactoring.

The separate Tavily-plugin repository should then independently change its one
fixed `chunks_per_source` value and request-shape tests, while retaining its
transport bounds, unchanged candidate normalization, privacy-safe failures,
and one-request/no-retry behavior. Architectural acceptance and either
implementation must not be combined in this RFC pull request.

## Validation requirements

Before implementation, review must confirm that the retained proof supports
only its stated numeric measurement; that all arithmetic is correct; and that
the RFC preserves no truncation, no source dropping, complete pre-routing
rejection, the aggregate limit, and projection validation. It must also confirm
that the amendments are narrow, do not alter RFC-0078 ownership, and identify
mixed-version rejection and the safe deployment order.

## Open questions

- Does independent review find 2,048 bytes to be the smallest justified
  provider-neutral margin, given the limited measurement?
- Is the retained 20,480-byte aggregate ceiling the right conservative total
  budget once it becomes reachable, or should any change to it require a
  separate investigation and RFC?
- What controlled future evidence, if any, would be sufficient to assess
  answer usefulness without retaining private prompts, source text, or outputs?

## Proposed decision

If accepted, amend RFC-0077 only by raising the maximum
`SourceEvidence.content` size from 1,024 to 2,048 UTF-8 bytes while preserving
all other source, aggregate, projection, validation, authority, and failure
rules. Amend RFC-0093 only by changing its fixed Tavily Search
`chunks_per_source` value from 1 to 2 while preserving all other request,
transport, normalization, and privacy rules. RFC-0078 remains unchanged.
