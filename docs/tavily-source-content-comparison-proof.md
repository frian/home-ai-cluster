# Tavily Source Content Comparison Proof

Status: Operator Proof

Date: 2026-10-13

## Objective

Measure the source content returned by one explicitly authorized Tavily Search
call at each supported `chunks_per_source` value (1, 2, and 3), and compare
the resulting candidate sets with the current [RFC-0077](../RFC/RFC-0077-bounded-source-grounded-chat.md)
validation contract. This is a provider measurement, not a model-answer-quality
evaluation or a production change.

## Authorization and scope

The operator explicitly authorized the exact public query category used for
this proof, use of the environment-provided Tavily credential, and exactly
three Tavily Search calls: one each with `chunks_per_source` 1, 2, and 3. This
document records the three calls made under that fresh retry authorization; it
does not rely on the prior discarded run.

The credential was read only for the provider requests. It was not displayed,
logged, or persisted. No result URL was fetched, no HAC server was started,
and no routing or model execution occurred. No source titles, URLs, content,
or raw provider response was retained.

## Verified baseline

The base branch `post-1.1-development` was fetched and verified at
`c6b850c044d55c1fe2b332f4ce81a6e374ea4d49`, the expected merge of the prior
[source-content-size investigation](tavily-source-content-size-investigation.md).
No equivalent open pull request was found before this proof began.

The experiment used a clean dedicated worktree at that baseline. It made no
HAC production, plugin, configuration, or accepted-RFC changes.

## Experimental method

A disposable harness outside the production source tree used the fixed Tavily
Search endpoint and the transport posture specified by
[RFC-0093](../RFC/RFC-0093-bounded-tavily-acquisition-plugin.md): TLS
verification, disabled redirects and environment proxies, finite connect/read/
write/pool timeouts, one connection, a 30-second total deadline, and bounded
incremental reading with a 1 MiB decoded-response ceiling.

For each response, the harness applied the existing Tavily plugin's
normalization: up to five provider-order entries having nonblank string
`title`, `url`, and `content` fields. It then reconstructed the current
`SourceEvidence` values and a `SourceGroundedChatRequest` offline. Therefore,
the reported validation outcome is the current HAC validation result before
routing, rather than a hypothetical truncation policy.

Only sanitized numeric measurements and aggregate overlap counts were emitted.
All byte counts use actual UTF-8 encoding.

## Provider request configurations

Each of the three requests used the same operator-authorized public query,
`search_depth="basic"`, `max_results=5`, `include_answer=false`,
`include_raw_content=false`, `include_images=false`,
`include_image_descriptions=false`, and `auto_parameters=false`. The sole
changed setting was `chunks_per_source`.

| Configuration | Chunks per source | HTTP | Returned / usable candidates | Elapsed | Decoded response bytes | Provider-reported credits |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| A | 1 | 200 | 5 / 5 | 628 ms | 3,154 | Not available |
| B | 2 | 200 | 5 / 5 | 571 ms | 5,140 | Not available |
| C | 3 | 200 | 5 / 5 | 438 ms | 7,877 | Not available |

Exactly three provider calls were attempted; all three returned usable
candidates. No other provider endpoint was contacted.

## Sanitized measurements

Content measurements remain in provider order within each configuration. They
are not source identities, rankings, titles, URLs, or retained content.

| Configuration | Content characters per selected candidate | Content UTF-8 bytes per selected candidate | Maximum content bytes | Total content bytes | Aggregate title + URL + content bytes | Sources over 1,024 content bytes |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| A (1) | 380, 499, 430, 313, 320 | 382, 501, 432, 317, 324 | 501 | 1,956 | 2,490 | 0 |
| B (2) | 904, 858, 320, 865, 965 | 906, 860, 324, 867, 965 | 965 | 3,922 | 4,423 | 0 |
| C (3) | 1,313, 1,472, 1,357, 1,024, 1,201 | 1,323, 1,472, 1,373, 1,030, 1,209 | 1,472 | 6,407 | 7,191 | 5 |

## Current RFC-0077 validation results

[RFC-0077](../RFC/RFC-0077-bounded-source-grounded-chat.md) allows one to five
sources, title fields through 512 UTF-8 bytes, URLs through 2,048 UTF-8 bytes,
content through 1,024 UTF-8 bytes, aggregate evidence fields through 20,480
UTF-8 bytes, and a canonical source projection through 65,536 UTF-8 bytes.
An invalid source rejects the complete request; HAC does not discard or shorten
that source.

| Configuration | Every selected candidate passes RFC-0077 | Complete `SourceGroundedChatRequest` passes before routing | First rejection boundary |
| --- | --- | --- | --- |
| A (1) | Yes | Yes | None |
| B (2) | Yes | Yes | None |
| C (3) | No | No | Per-source content: all 5 values exceed 1,024 UTF-8 bytes |

For C, the aggregate evidence measurement (7,191 bytes) remains below the
20,480-byte aggregate limit. The immediate and decisive boundary is instead
the individual content limit. The current acquisition path would fail before
routing or execution; it would not pass a partial four- or zero-source set.

## Comparison of 1, 2 and 3 chunks

Relative to A, B returned 1,966 additional content bytes (roughly twice the
observed source text) while retaining five valid sources. Relative to B, C
returned 2,485 additional content bytes, but none of C's selected sources fit
the existing per-source content contract.

Tavily search results can vary between calls. Sanitized identity comparison
found three overlapping sources between A and B; two had changed content and
were longer in B. There were no overlapping sources between B and C. These
counts show that larger settings can return distinguishably different source
text for overlapping results, but do not establish that a particular result
position is the same source or that more text improves an answer.

## Evidence usefulness observations

The run establishes a provider-content size difference, not a downstream
answer-quality result. The A-to-B overlap observation supports that two chunks
can provide additional, non-identical source material rather than only an
identical response replay. Because raw passages were intentionally neither
retained nor reported, this proof does not claim that the additional material
contained a specific relevant fact, was non-repetitive overall, or improved a
model answer. Those questions need separately authorized content or
answer-quality evaluation.

## Limitations

This is one public query and three provider calls, not a statistical sample.
The provider can vary results across calls, `chunks_per_source` is a maximum
rather than a guarantee, and neither source truth nor freshness was assessed.
The measurements do not establish a model context requirement, safe future
limit, provider credit count, or answer-quality improvement.

## Architectural implications

Configuration B demonstrates that two chunks can materially increase returned
source text while still fitting the current RFC-0077 validation bounds in this
single observation. It cannot be used in the accepted Tavily plugin today:
[RFC-0093](../RFC/RFC-0093-bounded-tavily-acquisition-plugin.md) fixes that
plugin at `chunks_per_source=1`. An RFC-0093 amendment would be required before
changing that production request shape.

Configuration C demonstrates a concrete incompatibility: any future proposal
to admit this observed three-chunk set would need a per-source content envelope
of at least the observed 1,472 UTF-8 bytes, with any safety margin separately
justified. It would require an amendment to RFC-0077 and reconsideration of its
related aggregate and projection bounds, as well as an RFC-0093 amendment for
the request shape. This proof selects no new limit and authorizes no such
change.

## Recommended next step

The smallest justified next step is a narrowly scoped architectural discussion
of whether RFC-0093 should permit **two** chunks while retaining the current
RFC-0077 limits. The observed B set is compatible, but this proof is too small
to establish a reliable upper bound or answer-quality benefit. Do not propose a
three-chunk change, raise RFC-0077 limits, or implement a production setting
from this evidence alone.

## Validation

- Exactly three authorized provider calls were made for this proof; no retries,
  pagination, or result-URL requests occurred.
- The report contains no credential, authorization header, raw response, source
  title, URL, or content.
- The candidate normalization and offline request validation followed the
  current accepted plugin and HAC model behavior.
- No HAC production behavior changed.
- Internal Markdown links were reviewed.
- `git diff --check` passed.
