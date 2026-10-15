# RFC-0156: Bounded Local Document Enrichment for External Information

Status: Draft

Date: 2026-10-15

Author: frian

## Summary

This Draft proposes one bounded extension to the existing External Information
path: after an already authorized, exactly selected Search plugin returns its
untrusted results, that plugin may, with separate explicit authorization,
retrieve and locally extract HTML from at most one selected public HTTPS result
URL. A deterministic local passage-selection step may then construct ordinary
RFC-0077 `SourceEvidence` for the existing Source-Grounded Chat path.

It works independently with the RFC-0079 SearXNG Search plugin or the
RFC-0093 Tavily Search plugin. It neither requires both plugins nor requires
Tavily Extract. It adds no capability, routing rule, runtime-adapter behavior,
provider fallback, external extraction service, persistence, or general Web
research system. This Draft authorizes no implementation or dependency change.

## Established architecture and observed evidence

RFC-0077 makes `SourceEvidence.url` provenance only: neither HAC core, a
runtime adapter, nor a selected execution node may follow it. RFC-0078 places
one selected acquisition plugin before complete RFC-0077 validation and does
not authorize ordinary server-side acquisition. RFC-0079 and RFC-0093 each
make one provider-specific Search request and return untrusted ordered
title/URL/content candidates. RFC-0095 selects a plugin as retained state; it
is not disclosure authority. RFC-0096, RFC-0133, and RFC-0134 define distinct
explicit and automatic Search authorization surfaces. RFC-0154 preserves the
2,048-byte per-source-content, five-source, 20,480-byte aggregate, and
65,536-byte canonical-projection limits, with complete validation before
routing.

RFC-0064 was rejected because its evidence did not establish a safe useful
project-owned retrieval boundary. Its rejection remains in force; this Draft
does not revive generic URL summarization.

The local feasibility record at
`/tmp/hac-searxng-local-document-feasibility-q4ZeFF/` is narrower than a
production proof. Offline mocked tests with urllib3 2.6.3 demonstrated a
plausible resolve-once, public-address filter, IP-pinned HTTPS connection path
while preserving the origin hostname for SNI, `Host`, and certificate-name
parameters. They also showed direct-pool configuration need not use a proxy.
They did not demonstrate real DNS, TCP, TLS, CA-root validation, or certificate
verification, and they did not establish complete SSRF protection or an
effective hard overall deadline. `Timeout.total` alone is not such a deadline
for a peer that slowly continues to stream.

The offline document-evidence investigation found that simple selection and
boundary-aware extraction can sometimes improve a particular answer, but that
cleaning and neighboring passages can discard useful information or add noise.
It does not establish a universally superior cleaning rule.

## Problem

Search snippets can be too short for an ordinary documentary answer. Manually
copying a public page into an existing source-grounded request remains possible,
but is not an ordinary useful Search-assisted workflow. HAC needs the smallest
explicitly authorized way to turn one already returned result URL into bounded
local documentary evidence without making returned provenance URLs generally
actionable.

## Goals

- Permit at most one local HTML document retrieval per authorized turn, after
  one selected existing Search plugin has returned results.
- Keep Search-only behavior byte-for-byte and authority-wise unchanged.
- Preserve provider independence and all RFC-0077/RFC-0154 evidence bounds.
- Define finite, cancellable retrieval lifecycle ownership before Chat routing.
- Keep retrieval local to the acquisition side; selected Chat nodes receive
  only validated evidence under existing Source-Grounded Chat rules.

## Non-goals

This Draft does not authorize a browser, crawling, JavaScript, redirects,
cookies, authentication, HTTP, proxies, retries, multiple URLs, model-selected
URLs, provider fallback, Tavily Extract, RAG, embeddings, vector storage,
document cache, persistent service, worker pool, subprocess, new executable
capability, generic plugin framework, runtime-adapter change, routing change,
or implementation.

## Alternatives and ownership

Two credible locations exist:

| Placement | Benefit | Cost and compatibility |
| --- | --- | --- |
| Caller-local stage after RFC-0078 plugin acquisition | One provider-neutral caller implementation | RFC-0078 currently says the caller invokes the selected plugin once, reconstructs candidates, validates, and sends them; it expressly treats result URLs as non-actionable. This alternative requires an explicit RFC-0078 amendment authorizing one separately permissioned retrieval/selection stage between plugin return and RFC-0077 reconstruction, with its dependency and cancellation ownership. |
| Small shared local utility used by each selected acquisition plugin | Retains provider HTTP and result handling on the acquisition side; the RFC-0078 caller contract and Source-Grounded Chat entry stay unchanged | Requires a narrow RFC-0078 amendment allowing a selected plugin to invoke one fixed local enrichment helper after Search, while keeping the helper private to this category and preserving the three-field return contract. |

This Draft recommends the second placement. `hac-extract` is only a working
component name, not an accepted CLI, distribution, package, entry point, or
public API. It is a small shared utility, not HAC core: it receives a selected
untrusted result and returns bounded candidate evidence or a normalized
enrichment failure to the already selected plugin. It must not discover
plugins, select providers, call Chat, retain documents, or expose a service.

An acceptance must amend RFC-0078 narrowly: a selected acquisition plugin may
use this helper only within a separately authorized enrichment turn; it still
invokes its provider once, returns only `title`/`url`/`content` dictionaries,
and leaves fresh RFC-0077 reconstruction and complete validation to the caller.
No ordinary server process gains result-URL authority. This amendment is needed
even for the recommended design because RFC-0078 currently excludes arbitrary
result-URL retrieval; it must not be inferred from Search selection.

## Proposed authorization and flow

Search authority and document-retrieval authority remain separate. An existing
explicit or automatic Search authorization permits exactly the behavior already
accepted. It never permits a result URL to be contacted.

For the first automatic Chat surface, this Draft proposes one additional,
non-retained, current-surface `Allow local document enrichment` control. It
defaults off, is intelligible as disclosure of one selected result URL to its
public website, and is necessary in addition to RFC-0134's automatic External
Information authority and a valid RFC-0095 plugin selection. An enabled Search
control without this second control remains Search-only. The matching
interactive automatic surface would require a separate explicit
`--document-enrichment` foreground flag, valid only with its existing
`--external-information` authorization; it is not retained.

The explicit RFC-0078 `hac external-information` surface likewise needs one
new explicit per-operation document-enrichment option. It must not infer
consent from `--plugin`, `--query`, or `--question`. Browser, native explicit,
and automatic interactive authorizations remain independent. A later RFC may
choose exact spelling and presentation, but may not silently broaden any of
these existing authorities.

For one eligible authorized turn the proposed shape is:

```text
authorized Search -> one selected Search plugin -> untrusted results
  -> exactly one deterministic eligible URL selection
  -> one local HTTPS HTML retrieval and passage selection
  -> fresh bounded SourceEvidence -> existing Source-Grounded Chat
```

The selected plugin remains SearXNG *or* Tavily. SearXNG has no Tavily account,
key, endpoint, or dependency; Tavily Search has no Tavily Extract request or
dependency. Neither provider is coupled to the other. No runtime adapter or
routing decision sees retrieval authority or a URL destination.

## Retrieval and evidence boundary

The first policy is deliberately closed:

- HTTPS only; absolute URLs with no credentials and public destinations only.
- Resolve before connecting, reject any private, loopback, link-local,
  multicast, unspecified, reserved, or special answer, and connect only to a
  validated resolved address while preserving the origin hostname for TLS
  identity verification.
- Normal CA and hostname TLS verification; no redirect, proxy, retry, cookie,
  ambient credential, or JavaScript execution.
- One selected document URL maximum per turn; no second URL if selection or
  retrieval fails.
- Finite independently owned DNS/connection/header/read/body limits and finite
  encoded, decoded, extracted-text, and selected-passage limits.
- HTML only initially; reject non-HTML and do not persist raw HTML, extracted
  text, or documents.

IP-pinned HTTPS using urllib3 is a candidate mechanism, not a selected
implementation. The mocked feasibility proof supports that the candidate can
direct a connection to a validated numeric address while passing the hostname
to TLS-name configuration and keeping a direct pool proxy-free. It does not
prove real certificate verification, platform behavior, DNS correctness, or
complete SSRF resistance. Production implementation must validate all resolved
answers and preserve the validated-destination-to-connected-peer invariant;
this narrows risk but is not a claim of complete SSRF protection.

Deterministic first-version HTML extraction should remove non-content elements
such as script and style, decode under explicit bounded rules, preserve stable
text order, and use simple deterministic passage segmentation and selection.
It must select a passage before constructing `SourceEvidence`; it must not
silently truncate an already constructed evidence object. The selected title,
provenance URL, and passage then undergo unchanged RFC-0077/RFC-0154 complete
validation: content is at most 2,048 UTF-8 bytes, no more than five evidence
objects, and existing aggregate and projection bounds apply. This Draft does
not claim a particular cleaning policy is generally best.

## Selection, failure, cancellation, and privacy

An acceptance must choose and specify one deterministic eligible-result policy
before implementation. The smallest candidates are first eligible result in
provider order, or first eligible result with nonblank Search content. The
former preserves provider order and avoids interpreting snippets; the latter
uses a small available quality signal but changes which URL is contacted. This
Draft prefers first eligible provider-ordered result, leaving the decision open
for review. Search results are untrusted in either case.

No eligible URL, retrieval failure, empty content, oversized document, no
selected useful passage, cancellation, or final RFC-0077/RFC-0154 validation
failure ends this enrichment branch safely. It must not attempt another URL,
retry, select another provider, call Tavily Extract, or fall back to ordinary
Chat. Source-Grounded Chat starts only after a complete valid evidence request
exists.

Retrieval owns its finite lifecycle from selection through evidence validation.
Cancellation or expiration must prevent later Source-Grounded Chat initiation,
including when an underlying blocking read completes after the awaiting task
has been cancelled. urllib3 total timeout is insufficient to establish this
requirement. This Draft selects no subprocess, worker pool, or execution
framework; evidence must justify any such mechanism.

Privacy boundaries remain explicit: the query is disclosed to the selected
Search provider under existing authorization; one selected URL is disclosed to
its public website; HTML is processed locally; only validated selected evidence
and the question reach a selected trusted Chat node under existing routing.
There is no mandatory external extraction service. Default logs, metrics,
traces, histories, and retained configuration must not receive queries, URLs,
HTML, selected passage text, credentials, or generated responses.

## Dependency and implementation proofs

The feasibility record found urllib3 2.6.3 in system Python, but not in the
relevant project virtual environments, which declare/use httpx. This Draft adds
no dependency. Before acceptance, the smallest responsible choice must be
shown: either add and lock a narrowly justified urllib3 dependency with its
supported pinned-IP/TLS behavior, or demonstrate that an already locked
library provides the same verified invariant. System installation is not a
project dependency contract.

Before any production implementation is considered ready, focused local,
falsifiable proofs must show:

- SearXNG and Tavily Search each participate independently, without the other
  plugin, account, or Tavily Extract.
- Search-only and unauthorized turns perform no result-URL retrieval.
- Exactly one eligible URL is selected; special/private destinations are
  rejected; destination pinning and TLS hostname identity are verified with
  controlled matching and non-matching TLS fixtures.
- Redirects, non-HTML, oversized encoded/decoded responses, empty extraction,
  and absent passages fail without another URL/provider/ordinary-Chat attempt.
- A narrowly scoped local slow-stream test demonstrates bounded lifecycle and
  that cancellation or expiry prevents late Source-Grounded Chat execution.
- Final evidence validation occurs before routing, and default logs contain no
  secret, query, URL, HTML, or source-content disclosure.

These are implementation proofs, not authorization to implement them in this
RFC change.

## Trade-offs

The recommended plugin-side helper preserves the established acquisition
boundary and keeps ordinary HAC server/routing behavior unchanged, but requires
a carefully scoped RFC-0078 amendment and dependency proof. Caller-local
retrieval would centralize implementation but more visibly changes the caller's
accepted authority and needs a larger RFC-0078 amendment. One URL and no
fallback reduce usefulness when a result fails, but make disclosure, resource
use, and failure behavior explainable.

## Decision

Draft. No implementation, dependency, configuration, public command, or
accepted architectural change is authorized.
