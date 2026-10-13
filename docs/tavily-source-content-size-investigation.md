# Tavily Source Content Size Investigation

Status: Investigation
Date: 2026-10-12

## Question and operator motivation

Can the optional Tavily acquisition plugin supply more useful source text to a local Chat model by requesting two or three chunks per source instead of one? The operator reports that some information-intensive questions receive too little evidence. This document investigates the existing limits and the smallest evidence needed for a decision. It authorizes no change to the accepted contracts or production behavior.

## Current accepted contracts

[RFC-0077](../RFC/RFC-0077-bounded-source-grounded-chat.md) defines an ordered set of one to five `SourceEvidence` values. Each nonblank title is at most 512 UTF-8 bytes; each nonblank absolute HTTP(S) provenance URL is at most 2,048 UTF-8 bytes and has no user information; each nonblank content value is at most 1,024 UTF-8 bytes. The combined title, URL, and content fields are at most 20,480 UTF-8 bytes. The fixed label plus canonical JSON source-data message is at most 65,536 UTF-8 bytes. Validation rejects the entire request before routing; it neither truncates nor drops a source. The question is separately bounded at 65,536 UTF-8 bytes. These are evidence and message bounds, not a model token or context guarantee.

The limits interact. With five sources at all three individual field maxima, raw fields total **17,920 bytes**, below the 20,480-byte aggregate bound. Thus the current aggregate bound cannot be the first failure for individually valid fields and at most five sources; it remains a distinct contract if field limits later change. Canonical JSON may enlarge fields through escaping, so its 65,536-byte limit is independently checked. For ordinary printable text it is far above the present field maxima, but it can matter for heavily escaped input (see synthetic example below).

[RFC-0078](../RFC/RFC-0078-optional-external-information-acquisition-plugin-boundary.md) places the selected, separately installed acquisition plugin at the caller edge. HAC reconstructs every candidate as `SourceEvidence`, then the complete `SourceGroundedChatRequest`, before sending anything to `/v1/chat/sources`. [RFC-0093](../RFC/RFC-0093-bounded-tavily-acquisition-plugin.md) fixes Tavily's request shape, including `chunks_per_source=1`, and explicitly leaves reconsideration of RFC-0077's 1,024-byte content limit for a separate investigation. Changing that fixed request value requires an architectural amendment to RFC-0093. Increasing accepted source content requires an amendment to RFC-0077; it may also require reconsidering the aggregate and projected-message bounds. This investigation makes neither decision.

The [loopback SearXNG plugin boundary](../RFC/RFC-0079-fixed-loopback-searxng-acquisition-plugin.md), [operator-authorized Chat fallback](../RFC/RFC-0096-bounded-operator-authorized-chat-external-information-fallback.md), [explicit browser acquisition](../RFC/RFC-0133-bounded-explicit-loopback-browser-external-information.md), and [automatic conversational acquisition](../RFC/RFC-0134-bounded-automatic-conversational-external-information.md) reuse the existing acquisition and source-grounded seams. They do not give Tavily or source content routing authority. External acquisition remains an authorized, selected operation, including the separately retained Chat disclosure authorization where applicable.

## Verified current implementation

The sibling [Tavily plugin](https://github.com/frian/home-ai-cluster-plugin-tavily) is a separate Python package with an RFC-0078 `tavily` entry point (`pyproject.toml`, `README.md`). Its `plugin.py` fixes one HTTPS POST to `https://api.tavily.com/search` with the exact query, `search_depth="basic"`, `max_results=5`, `chunks_per_source=1`, and `include_answer`, `include_raw_content`, `include_images`, `include_image_descriptions`, and `auto_parameters` all `false`. It has no retry or redirect following, a 30-second total deadline, and a 1 MiB **decoded provider response** ceiling enforced while streaming. Those transport bounds do not imply that 1 MiB reaches the model. The existing plugin tests assert the request shape, decoded-body bound, one request, normalization, and preservation of oversized content.

The plugin accepts an HTTP 200 JSON object with a concrete `results` list, takes up to five usable entries in provider order, and copies their nonblank string `title`, `url`, and `content` values unchanged. It ignores extra provider fields and malformed entries, but does **not** enforce the RFC-0077 byte bounds or trim a long content value. A selected value that exceeds those bounds therefore reaches HAC caller validation and fails there. Its credential is plugin-owned; it is not part of source evidence.

In [`external_information_command.py`](../src/home_ai_cluster/commands/external_information_command.py), `_candidate_sources` requires one to five exact three-field dictionaries of strings and constructs `SourceEvidence` for all candidates; `_acquire_source_grounded_request_async` then constructs `SourceGroundedChatRequest`. In [`models.py`](../src/home_ai_cluster/core/models.py), those models enforce the per-field, aggregate, and projected-message limits above. The caller sends the validated body to `/v1/chat/sources` only after all validation succeeds ([command reference](command-reference.md)). The public route reconstructs and revalidates the request, returning a safe 422 on invalid input. None of these steps adds another independent content-size limit. The browser and authorized Chat fallback call the same acquisition/request construction path.

## Tavily parameter semantics

Official [Tavily Search API documentation](https://docs.tavily.com/documentation/api-reference/endpoint/search) and the [Python SDK Search reference](https://docs.tavily.com/sdk/python/reference) were checked on **2026-10-12**. For Search, `chunks_per_source` accepts **1 through 3** and is available with `search_depth="basic"` (also `fast` and `advanced`). Under `basic`, each relevant source snippet is **about 500 characters**. The parameter sets a maximum number of chunks per source, not a guaranteed count. Multiple chunks appear together in one `results[].content`, shown by Tavily as `<chunk 1> [...] <chunk 2> [...] <chunk 3>`; adjacent chunks may instead be joined into a longer passage. Tavily explicitly describes chunk length as a **target, not a hard limit**.

The Search API lists `basic` at one API credit and `advanced` at two. It does not document an additional credit charge for choosing two or three chunks within `basic`, nor a chunk-count-specific latency guarantee. Longer output may affect transfer or processing time; this is an untested inference, not a documented measured change. Tavily gives no guarantee that additional chunks are distinct, relevant to the operator's question, or useful to the model. The SDK page also describes a separate Extract parameter with a different 1–5 range; that is **not** the Search parameter used here.

The [historical Tavily acquisition investigation](tavily-acquisition-plugin-investigation.md) and RFC-0093 described a provider character maximum for one chunk. Today's official documentation instead says approximately 500 characters for `basic` and explicitly disclaims a hard chunk-length limit. Neither description establishes a UTF-8-byte maximum. The accepted RFC and implemented HAC byte validation remain authoritative.

## Comparison: 1, 2 and 3 chunks

The text estimates below use Tavily's approximate 500-character `basic` target, not measured provider output or guaranteed byte ceilings. The provider returns one `content` string per result, and HAC validates that entire string.

| Hypothetical Search setting | Approximate available text per source | Current RFC-0077 fit and likely first barrier | Potential model value and uncertainty |
| --- | --- | --- | --- |
| **1** (current) | About 500 characters; actual length may vary. ASCII around 500 B, accented or multibyte text more. | Usually fits in the 1,024 B content bound, but no guarantee. A large or multibyte content value fails the whole request. | Historical one-query proof shows successful use. Some questions lack detail; rejection frequency and quality remain unknown. |
| **2** | Up to two target-sized snippets, roughly 1,000 characters plus any separator or joined passage. ASCII near 1,000 B may fit narrowly; multibyte text and longer passages can exceed 1,024 B. | Per-source content is the immediate likely barrier. The five-source field aggregate cannot bind first while current individual maxima hold. Projection is still checked independently. | May supply more evidence only if a second relevant chunk exists and passes validation. No answer-quality evidence yet. |
| **3** | Up to three target-sized snippets, roughly 1,500 characters plus any separator or joined passage. ASCII near that size already exceeds 1,024 B. | Per-source content is even more likely to reject the entire operation. Aggregate and projection cannot rescue an invalid source. | May include useful additional details but may add noise or repetition; accepted text and answer quality are unmeasured. |

Two or three chunks could still fit today when Tavily returns short passages. Conversely, one chunk can fail because approximate character counts are neither byte limits nor strict length ceilings. The provider's 1 MiB response ceiling is much larger than the current model-facing evidence envelope; it is a transport-safety bound, not usable source capacity.

## UTF-8 and evidence-size boundaries

**Synthetic deterministic examples only.** These are local string calculations, not Tavily observations. Byte counts use `len(text.encode("utf-8"))`; no invalid evidence is truncated. The ` [...] ` separator in examples has seven ASCII bytes solely to illustrate one possible combined string, not Tavily's exact serialization promise.

| Synthetic content | Characters | UTF-8 bytes | Current result |
| --- | ---: | ---: | --- |
| `"A" * 1000` | 1,000 | 1,000 | Content fits. |
| `"A" * 1025` | 1,025 | 1,025 | Content fails by 1 B. |
| `"L'été est déjà là. " * 45` (French sentence) | 855 | 1,080 | Content fails despite fewer than 1,024 characters. |
| `"🙂" * 300` | 300 | 1,200 | Content fails with four-byte Unicode characters. |
| `"A" * 500 + " [...] " + "B" * 500` | 1,007 | 1,007 | Two synthetic ASCII snippets fit by 17 B. |
| `"A" * 500 + " [...] " + "B" * 500 + " [...] " + "C" * 500` | 1,514 | 1,514 | Three synthetic ASCII snippets fail by 490 B. |

For **five synthetic sources** with 512 ASCII title bytes, a valid 2,048-byte ASCII URL (`https://x/` plus 2,038 `a` characters), and 1,024 ASCII content bytes each, the fields total exactly `5 × (512 + 2,048 + 1,024) = 17,920` B. The actual canonical label plus compact JSON used by `source_data_message_content` is **18,123 B** for this example, below 65,536 B. At the same per-field maxima with 2,038 NUL characters instead of the URL's `a` characters, Python's current URL validation accepts the provenance string, while JSON escaping makes the canonical message **69,073 B**: projection validation then rejects it. This pathological control-character example shows why the projection check is independent; it does not describe plausible Tavily URLs. Any source content over 1,024 B would already fail at the earlier field check, regardless of aggregate or projection size.

## Complete acquisition-to-model path

1. An authorized External Information operation selects one plugin and gives it the exact bounded query. For authorized Chat or browser flows, the accepted caller authorization applies; the ordinary local Chat route has no implicit Tavily request ([RFC-0078](../RFC/RFC-0078-optional-external-information-acquisition-plugin-boundary.md), [RFC-0096](../RFC/RFC-0096-bounded-operator-authorized-chat-external-information-fallback.md), [RFC-0133](../RFC/RFC-0133-bounded-explicit-loopback-browser-external-information.md), [RFC-0134](../RFC/RFC-0134-bounded-automatic-conversational-external-information.md)).
2. The separately packaged Tavily plugin owns its fixed request, 1 MiB decoded-response ceiling, 30-second deadline, and candidate normalization. It never fetches result URLs; the query alone goes to Tavily. Returned `content` remains one unchanged string per selected result ([RFC-0093](../RFC/RFC-0093-bounded-tavily-acquisition-plugin.md), sibling plugin `plugin.py`).
3. The RFC-0078 caller owns exact candidate shape and complete RFC-0077 model reconstruction. `SourceEvidence` rejects an oversized content value immediately; `SourceGroundedChatRequest` checks count, combined fields, canonical projection, question, and any conversational context. One invalid selected source fails **all** acquisition before the HTTP request or any routing; no partial surviving set is sent (`external_information_command.py`, `models.py`).
4. The public `/v1/chat/sources` route revalidates the same contract. If a valid request selects a declared trusted remote, the internal receiver revalidates it as well. The normalized question and evidence may reach that remote; provider credentials and raw response do not ([routes.py](../src/home_ai_cluster/api/routes.py), [remote transport](../src/home_ai_cluster/core/remote_transport.py)).
5. Core-owned projection serializes the accepted evidence into a labeled canonical JSON `user` message, alongside a fixed untrusted-evidence `system` message and the operator question as a final `user` message; conversational prior messages may precede the evidence message. Ordinary `capability=chat` routing selects a node and runtime adapter. The selected adapter receives the projected Chat messages and supplies them to its model. Adapter-specific context windows or tokenization may constrain usefulness or execution, but they are not an additional accepted Tavily/source byte limit and are not measured here ([models.py](../src/home_ai_cluster/core/models.py), [executor.py](../src/home_ai_cluster/core/executor.py), [RFC-0077](../RFC/RFC-0077-bounded-source-grounded-chat.md)).

Source URLs remain provenance data, never destinations or instructions. The result's sources mean what HAC supplied to execution, not that the model used them or that generated citations are correct.

## Existing evidence and limitations

The [0.7 interchangeability checkpoint](0.7-interchangeability-checkpoint.md) retains one **2026-08-30** live Tavily acquisition for a nonsensitive public Python 3.14 free-threading query with `chunks_per_source=1`. It recorded five content lengths, in provider order: **501, 489, 481, 431, and 460 UTF-8 bytes**. The corresponding title sizes were 57, 59, 38, 65, and 20 B; URL sizes were 44, 91, 60, 58, and 34 B. All five selected candidates fit the then-current evidence limits. The record also demonstrates that the optional plugin used the RFC-0078 seam in that proof.

One successful query does not establish output sizes for two or three chunks, multilingual byte lengths, how often longer results would fail validation, the relevance or novelty of extra chunks, latency, or measurable downstream answer quality. No live Tavily request or source-grounded Chat execution was performed for this investigation.

## Alternatives and assessment

**A — retain current behavior and close.** The one-chunk proof shows a working boundary, and there is no measured improvement case. This avoids changing accepted limits, but leaves the operator's reported information gap unresolved.

**B — seek one bounded comparison before choosing limits.** The operator need is credible, while current documentation provides neither strict output sizes nor usefulness evidence. A small public-query comparison would reveal actual accepted/rejected byte sizes and whether additional chunks add distinct, question-relevant information. It could inform whether to amend RFC-0093 alone, RFC-0077 too, or neither. This is the smallest evidence-producing next step.

**C — draft future contract amendments now.** The accepted boundaries identify where changes would belong: RFC-0093 for the fixed request shape and RFC-0077 for any larger evidence fields and possibly aggregate/projection ceilings. Yet no present evidence establishes a safe useful size or whether two chunks outperform one. Drafting a specific new limit now would be arbitrary.

**Outcome: B.** Do not increase `chunks_per_source` under the current accepted RFC-0093 shape. Even if that shape were amended, simply changing it to two or three would leave RFC-0077's 1,024-byte content rejection in place and could make complete-operation failure more common. Neither provider byte sizes nor answer-quality gain are established. The comparison should precede any proposed RFC amendment or implementation. This investigation does not decide future limits.

## Recommended next step and privacy boundary

Seek separate operator authorization for one narrowly bounded proof using an identical, explicitly approved, nonsensitive **public** query under Search `basic`: one provider call each for `chunks_per_source=1`, `2`, and `3`, with the existing five-result maximum and other fixed flags. Use only sanitized aggregate measurements: result count, per-result content UTF-8 byte lengths and character lengths, whole-response decoded bytes, RFC-0077 pass/fail reasons without source text, observed elapsed time and provider-reported credits if available, plus a qualitative assessment of whether extra chunks add distinct question-relevant evidence without retaining private content. A downstream answer-quality comparison would require its own bounded protocol and explicit authorization; this proof should not claim one. Do not log credentials, queries, source URLs/content, prompts, or generated responses by default.

This task made **no** provider request, consumed no credits, did not inspect `TAVILY_API_KEY`, invoked no installed plugin, sent no operator query, and did not run source-grounded Chat. It changed no production code, tests, configuration, routing, or accepted contract.
