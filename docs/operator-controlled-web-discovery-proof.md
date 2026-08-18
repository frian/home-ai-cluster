# Operator-Controlled Web Discovery Proof

Status: Retained

Date: 2026-08-18

## Purpose

This record retains privacy-safe evidence from one operator-run, disposable
proof performed entirely outside Home AI Cluster (HAC) implementation. Its
purpose was to test two empirical questions left open by the
[operator-controlled Web discovery investigation](operator-controlled-web-discovery-investigation.md):

1. Can a private operator-run SearXNG instance provide useful current-information
   title, URL, and snippet evidence without HAC following result URLs?
2. Can the existing local HAC Chat path make useful use of manually supplied
   snippets, and what grounding limitations appear?

The proof used a temporary private SearXNG checkout and Python virtual
environment outside this repository. No HAC source, dependency, runtime
configuration, service lifecycle, request/result contract, routing behavior, or
architectural decision changed. This proof does not authorize integration.

## Disposable SearXNG observation

The proof successfully created a dedicated Python 3.14.4 virtual environment
and installed the current SearXNG checkout and its Python dependencies into it.
The disposable instance was configured for loopback-only access, JSON search
output, disabled limiter, and disabled public-instance mode.

No Valkey, Docker, reverse proxy, systemd service, or HAC-owned lifecycle was
introduced. The first attempted loopback port was already occupied, so the
operator used another loopback port; the port value is incidental and is not a
proposed contract.

Startup reported several non-fatal observations: `ahmia` and `torch` could not
register, and SearXNG warned that `limiter.toml` was absent. The service still
accepted local searches. During later searches, Startpage was reported as
suspended following a CAPTCHA while the aggregate search still returned
results.

This is not a reliability guarantee. It demonstrates only that partial
upstream-engine failure can coexist with a usable aggregate result and that a
future boundary must normalize failures without treating any one engine as
guaranteed.

## Current-information discovery observation

One explicit current-information query about OpenAI was sent to the local
SearXNG JSON endpoint. Its results mixed generic or stale pages, including an
encyclopedia-style entry and a homepage, with same-day news from multiple news
organizations. The useful entries carried title, provenance URL, and informative
snippet text.

The structured `publishedDate` field was generally null, including for clearly
current results. A one-day time range increased the presence of current results
but did not behave as a strict freshness filter: generic pages could still rank
above same-day news. No returned result URL was fetched during this proof.

This observation supports three limited facts:

- private SearXNG discovery can surface useful current evidence;
- a time range is not strict currentness validation; and
- structured publication date and result rank cannot be treated as truth or
  freshness evidence.

## Technical-currentness discovery observation

A separate explicit query about the latest Ollama release returned official
Ollama/GitHub-oriented results, secondary release trackers, generic pages, and
stale or contradictory version claims. One official GitHub-oriented result
showed a recent release while secondary results in the same set asserted older
or conflicting versions. `publishedDate` was again generally null.

The observation shows that useful current information can be present while the
same bounded result set is still untrusted evidence rather than a normalized
factual database. Multiple snippets can disagree, and rank does not imply
authority. A future source-grounded Chat contract must not equate supplied
evidence with verified truth.

## Contested-information discovery observation

A third explicit query concerned a contested current market-analysis question.
The exact operator query is deliberately not retained. With a one-month time
range, the result set included evidence suggesting a bear market might be
nearing its end, evidence that another lower point could occur, conditional or
inconclusive analysis, and duplicated social/video variants or lower-quality
noise.

The result set showed useful viewpoint diversity, not factual convergence.
`publishedDate` was usually unavailable, freshness sometimes appeared only in
title or snippet text, and rank was not a reliability measure.

## Manual existing-HAC Chat observations

No source-grounded HAC request or result contract exists. For this proof only,
a small selection of SearXNG result snippets was manually formatted into one
ordinary existing `hac chat --message` request. This manual prompt
concatenation was experimental proof plumbing, not proposed architecture.

### Favorable evidence case

The first manual Chat request supplied five OpenAI search results. It
deliberately placed two weak/generic entries before three useful same-day news
entries. The local Chat execution ignored the weak entries, identified the
common same-day event in the useful sources, produced a short materially
correct synthesis from their snippets, and identified the three useful source
numbers.

This establishes only that bounded snippets can be useful evidence for the
observed local Chat execution. It does not establish that source numbering is a
citation guarantee or that every model, query, result set, or ranking will
behave similarly.

### Adversarial and contradictory evidence case

A second manual request supplied five deliberately conflicting market-analysis
snippets. Its prompt instructed the model to use only the snippets, treat them
as untrusted reference data, recognize disagreement, avoid choosing a
conclusion merely because of rank, avoid unsupported facts, and identify the
sources supporting each side.

The response was broadly reasonable at the topic level: it characterized the
evidence as leaning toward an advanced bear-market phase that was not clearly
proven finished. Its source-level grounding was imperfect:

- a source that only asked whether a bottom had already occurred was treated as
  affirmative support for the position that the bear market was not over;
- another source's position was categorized inconsistently;
- a source that said the market might be nearing its end was rendered more
  categorically than its wording supported;
- one materially useful source was omitted from the source accounting; and
- the final synthesis generalized one source's conditional observation as
  collective support.

The exact financial query and generated answer are intentionally not retained.

## Bounded findings

The proof supports:

- an independently operated private SearXNG instance can return useful JSON
  search results for explicit current-information queries;
- useful title, URL, and snippet evidence can be obtained without following a
  result-page URL;
- result sets can contain current information even when structured publication
  dates are absent;
- result sets can be noisy, stale, contradictory, and subject to partial
  upstream-engine failure;
- the observed local HAC Chat execution can make useful high-level syntheses
  from manually supplied bounded snippets; and
- model source attribution can be wrong even when the overall synthesis is
  broadly reasonable.

The proof does not support:

- selecting SearXNG as an accepted HAC dependency or architecture;
- HAC ownership of SearXNG installation, configuration, lifecycle, or updates;
- treating a time range as strict freshness validation, a rank as reliability,
  or snippets as full source content;
- treating supplied sources as verified truth or model-generated source numbers
  as claim-by-claim citation correctness; or
- autonomous search, page fetching, model-selected queries, tools, agents, RAG,
  caching, or a Web capability.

## Provenance and citation observation

The proof provides empirical support for keeping two concepts distinct:

- **supplied-source provenance** — which normalized external sources were made
  available to a model execution; and
- **model-generated citation correctness** — whether a particular generated
  claim is actually supported by a particular supplied source.

The first could potentially be represented structurally if a future RFC decides
so. The second was imperfect in this proof and must not be assumed merely
because a model names source numbers. This is evidence, not a decision of a
future request/result shape; a future RFC remains responsible for those
semantics.

## Relation to the investigation and Draft RFC-0076

This proof materially strengthens Outcome B in the
[operator-controlled Web discovery investigation](operator-controlled-web-discovery-investigation.md):
an independently operated private SearXNG service has demonstrated practical
usefulness as a source of bounded current-information discovery evidence.

It does not authorize SearXNG integration or select SearXNG for HAC. Draft
RFC-0076 and its pull request remain non-governing and untouched. The proof
does not decide whether future RFC work should combine discovery and
source-grounded Chat or split them; that sequencing remains a review and RFC
decision.

## Privacy exclusions

This retained record contains no:

- exact personal market-analysis query;
- raw complete search response or exhaustive raw result list;
- operator username, home-directory path, process identifier, private hostname,
  private address, or private machine detail;
- model or runtime identifier;
- credential, API key, cookie, or other secret;
- personal financial data; or
- full generated model response.

Temporary proof material is not retained.

## Conclusion

The operator proof supports the investigation's claim that an independently
operated private SearXNG service can be a technically useful source of bounded
current-information discovery evidence. It also demonstrates that local Chat
can make useful use of such snippets while model-generated source attribution
is not reliable enough to treat as verified citation semantics. These
observations provide evidence for future RFC work but authorize no integration
or architectural change.
