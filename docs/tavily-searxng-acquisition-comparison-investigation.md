# Tavily Advanced vs SearXNG Acquisition Comparison Investigation

Status: Operator investigation (documentation only)

Date: 2026-10-14

## Question

For five public technical questions, what differences are observable between
one direct Tavily Advanced Search call and one direct query to the operator's
local SearXNG service, **before** any HAC model execution?

This is a small, one-shot comparison of acquired source candidates. It is not
a statistical benchmark, a general provider ranking, a test of model answer
quality, a production configuration change, or an architectural decision.

## Accepted boundaries and scope

- [RFC-0077](../RFC/RFC-0077-bounded-source-grounded-chat.md) defines
  provider-neutral bounded source evidence. Its provenance does not certify
  factual truth or claim-level support.
- [RFC-0078](../RFC/RFC-0078-optional-external-information-acquisition-plugin-boundary.md)
  fixes the optional, exact, operator-selected acquisition-plugin caller edge.
- [RFC-0079](../RFC/RFC-0079-fixed-loopback-searxng-acquisition-plugin.md)
  selects a fixed loopback SearXNG plugin contract.
- [RFC-0093](../RFC/RFC-0093-bounded-tavily-acquisition-plugin.md)
  selects the fixed Tavily plugin request contract.
- [RFC-0154](../RFC/RFC-0154-bounded-external-information-source-expansion.md)
  raises the accepted content limit to **2,048 UTF-8 bytes per source** and
  Tavily's fixed chunk count to two, without authorizing Advanced mode.

**The shipping Tavily plugin uses `search_depth="basic"`.** The direct
Advanced calls here are experimental, outside that plugin, and must not be
presented as measured production Tavily-plugin behavior. The production
SearXNG plugin was also not invoked: the script emulated its fixed
loopback request and candidate normalization.

No repository, plugin, RFC, configuration, routing, adapter, server, or
model behavior was changed. No generated answers were requested.

## Operator setup and reproducible method

The operator ran a disposable Python script from the local HAC Python
environment, one case at a time, and shared its console output. The script
made at most one provider request per case, sequentially: SearXNG first,
then Tavily. All five cases completed with one successful provider response
per provider (ten acquisition requests in total); there were no retries.

- **SearXNG:** form POST to `http://127.0.0.1:8888/search` with the exact
  `q` and `format=json`. The operator-owned service was already running.
  The enabled engines marked `general` in the observed `/config` output
  included Wikipedia, Currency, Wikidata, DuckDuckGo, Google CSE, Lingva,
  Startpage, Dictzone, MyMemory Translated, and Brave. This does **not**
  establish which engines were actually queried or returned results.
- **Tavily:** HTTPS POST to `https://api.tavily.com/search` with the same
  query, `search_depth="advanced"`, `max_results=5`,
  `chunks_per_source=2`, `include_answer=false`,
  `include_raw_content=false`, `include_images=false`,
  `include_image_descriptions=false`, and `auto_parameters=false`.
  No domain preference or exclusion filter was applied.
- **Common experiment bounds:** 30-second total deadline per request;
  1 MiB decoded-response ceiling; disabled HTTP redirects and environment
  proxies; one HTTP connection; no pagination or URL following. Tavily TLS
  verification remained enabled.
- **Selection and validation:** retain the first five ordered provider
  `results[]` objects with nonblank string `title`, `url`, `content`;
  preserve those field values without truncation, summarization, reranking,
  or deduplication. Reconstruct fresh `SourceEvidence` objects and the
  complete `SourceGroundedChatRequest` using the exact case question,
  entirely offline. The result is the actual HAC structural validation result.
- **Measurements:** acquisition wall time, ordered URLs, total UTF-8
  `content` bytes, size per selected source, a 12-hex-character prefix
  of SHA-256(content), and matches to a small *predeclared hostname hint
  list*. Hostname matching is not an authority or accuracy assessment.
  Console previews showed only the start of source content.
- **Privacy:** all queries concerned public technical documentation.
  The Tavily credential was supplied from an environment variable and
  was not printed. No raw provider responses, result-URL fetches, model
  requests, or experiment disk writes occurred. This document retains
  selected **public URLs, titles, and numeric measurements** from the
  operator's shared console output, not the full provider snippets.
  Although SearXNG's first hop was loopback, its configured upstream
  engines may have received the public query text.

The operator ran these fixed cases:

| Case | Exact query | Question asked for offline validation |
| --- | --- | --- |
| Python | `Python 3.14 free threading PEP 659 adaptive interpreter PEP 779 changes` | What changed in Python 3.14 free-threaded mode compared with 3.13, especially PEP 659 and the support status? |
| Rust | `Rust 2024 edition unsafe attributes no_mangle export_name link_section` | How must no_mangle, export_name and link_section attributes be written in Rust edition 2024, and why? |
| Linux | `Linux io_uring submission completion queue io_uring_setup io_uring_enter` | What are the roles of the io_uring submission and completion queues, and what do io_uring_setup and io_uring_enter do? |
| CUDA | `CUDA C++ programming guide global shared local memory scope` | How do CUDA global, shared, and local memory differ in scope and accessibility? |
| SQLite | `SQLite WAL write ahead logging readers writer checkpoint` | How does SQLite WAL mode permit concurrent readers and a writer, and what is a checkpoint? |

## Measurements

All five source sets from SearXNG passed current HAC request validation.
Four Tavily Advanced sets passed; its Linux set failed.

| Case | SearXNG time | Tavily time | SearXNG content bytes | Tavily content bytes | SearXNG / Tavily matching reference-host candidates | SearXNG / Tavily HAC validation |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Python | 1.42 s | 3.81 s | 807 | 5,792 | 1 / 1 | PASS / PASS |
| Rust | 0.64 s | 6.13 s | 789 | 3,959 | 1 / 2 | PASS / PASS |
| Linux | 0.86 s | 5.21 s | 814 | 11,780 | 2 / 1 | PASS / **FAIL** |
| CUDA | 0.66 s | 3.54 s | 782 | 5,475 | 2 / 2 | PASS / PASS |
| SQLite | 0.65 s | 3.11 s | 792 | 5,412 | 1 / 1 | PASS / PASS |
| **Total / mean** | **0.85 s mean** | **4.36 s mean** | **3,984 total** | **32,418 total** | **7 / 7 summed hints** | **5/5 / 4/5 PASS** |

Both returned five selected sources for every case: 25 selected source
records from each provider. Across these observations, Tavily supplied
about 8.1 times as many source-content bytes. These are **not** comparable
full-page sizes or measures of unique, useful facts. The latency measurements
are individual wall times, not distributions or speed guarantees. Provider
billed credits were not verified.

## Per-case source evidence

Only provider-selected titles/URLs and displayed preview excerpts were
available for this analysis; no one fetched or independently examined the
full source pages during these five runs. The following rank observations
are grounded in the shared console output.

### Python 3.14 free-threading

- **SearXNG:** rank 1 was the [official Python 3.14 What's New page](https://docs.python.org/3/whatsnew/3.14.html),
  with 158 content bytes. Its preview mentioned PEP 779 official support
  and the specializing adaptive interpreter, but offered little context.
  The remaining selected sources were secondary articles and an interview
  questions page.
- **Tavily Advanced:** rank 1 was a LinkedIn post; ranks 2 and 3 were
  a documentation mirror and a PEP 779 explanation; rank 4 was the
  [same official Python page](https://docs.python.org/3/whatsnew/3.14.html),
  with 1,388 content bytes. Its preview included more context on the
  Python 3.13 baseline and 3.14 implementation changes.
- The source sets shared one exact URL. Both passed HAC validation.

### Rust 2024 unsafe attributes

- **SearXNG:** rank 1 was the
  [Rust Edition Guide](https://doc.rust-lang.org/edition-guide/rust-2024/unsafe-attributes.html)
  (136 bytes); rank 2 was the project's
  [RFC 3325](https://rust-lang.github.io/rfcs/3325-unsafe-attributes.html)
  (160 bytes). The latter was **not counted** by the script's
  `doc.rust-lang.org`-only reference-domain heuristic, although it is an
  authoritative Rust-project RFC.
- **Tavily Advanced:** rank 1 was the same Edition Guide (1,507 bytes);
  rank 4 was the official
  [Rust Reference ABI page](https://doc.rust-lang.org/reference/abi.html)
  (1,528 bytes). The previews described symbol names, linking behavior,
  and safety conditions with more detail.
- The source sets shared one exact URL. Both passed HAC validation.

### Linux io_uring

- **SearXNG:** ranks 1 and 2 were the
  [`io_uring_setup(2)`](https://man7.org/linux/man-pages/man2/io_uring_setup.2.html)
  and [`io_uring_enter(2)`](https://man7.org/linux/man-pages/man2/io_uring_enter.2.html)
  Linux manual pages (166 and 163 bytes). Rank 3 was an Arch manual
  mirror for `io_uring_enter`; the selected documents covered both
  named syscalls.
- **Tavily Advanced:** ranks 1–4 were different URLs for
  `io_uring_setup(2)`: two Wayback snapshots, one `kernel.org` mirror
  and one `www.man7.org` page. All four had **2,260-byte contents with the same reported
  12-character SHA-256 prefix** (`df8ae60a5832`), strongly indicating
  duplicate text. Full digests were not retained in the console output. Rank 5 was an Ubuntu `io_uring_setup(2)` manual
  excerpt of 2,740 bytes. No selected Tavily result was a directly
  titled `io_uring_enter(2)` manual page.
- **All five** Tavily source contents exceeded the current **2,048-byte
  individual limit**, so fresh `SourceEvidence` / complete-request
  validation failed before any execution. The aggregate of 11,780
  content bytes was below the 20,480-byte combined field ceiling;
  the individual source bound was decisive in this observed data.
  No truncation or repair was performed.
- The two providers shared **zero exact URLs**.

### CUDA memory scopes

- **SearXNG:** rank 1 was NVIDIA's
  [CUDA C++ Programming Guide (Legacy)](https://docs.nvidia.com/cuda/cuda-c-programming-guide/)
  (162 bytes); rank 2 was its official PDF (129 bytes). The first
  preview stated that local memory is private to a thread and shared
  memory is visible to a thread block.
- **Tavily Advanced:** rank 1 was the corresponding NVIDIA
  [Programming Guide](https://docs.nvidia.com/cuda/cuda-c-programming-guide)
  (1,251 bytes); rank 3 was the official
  [Best Practices Guide](https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/index.html)
  (1,573 bytes). Other selected results included older PDF copies.
  A long passage on parent/child memory visibility was more specific
  than the operator's broad memory-scope question.
- Both passed HAC validation. The source sets shared one exact URL
  (an older university-hosted CUDA guide PDF); the near-identical NVIDIA
  paths with and without a trailing slash did not count as an exact match.

### SQLite WAL and checkpoints

- **Both providers:** rank 1 was the official
  [SQLite Write-Ahead Logging documentation](https://www.sqlite.org/wal.html).
  SearXNG supplied 165 bytes; Tavily supplied 1,569 bytes.
- The SearXNG preview identified checkpointing as moving WAL transactions
  back into the database; the Tavily preview added why a checkpoint may
  stop at an active reader's end mark. Tavily also selected a YouTube
  video and secondary explanations; SearXNG likewise selected secondary
  articles. These observations do not establish full-source accuracy.
- Both passed HAC validation and shared one exact URL.

## Findings and limitations

1. **Discovery was strong in this narrow sample.** SearXNG's first
   result was a directly relevant primary documentation reference in all
   five cases (with `man7.org` treated as an established Linux-manual
   reference, not mislabeled as `docs.kernel.org`). Tavily's first
   result was such a reference in three cases; on Python it started with
   LinkedIn, and on Linux with a Wayback copy.
2. **Passage depth differed substantially.** Tavily Advanced often
   supplied a longer relevant passage from an official reference.
   SearXNG supplied short search snippets, generally around 130–170
   content bytes per result. These behaviors reflect different
   acquisition products, not necessarily different raw discovery quality.
3. **Longer is not automatically better.** The Linux Advanced result
   contained four apparent duplicate excerpts, missed a directly titled
   reference for one of the two queried syscalls, and failed HAC
   validation for every individual source. More bytes neither imply
   unique coverage nor guarantee compatibility.
4. **Validation is not factual verification.** Passing
   `SourceGroundedChatRequest` means the source set satisfies the
   accepted structural bounds, not that the supplied facts are correct
   or sufficient, or that a future model will reason reliably.
5. **No general winner or failure rate is established.** Each case
   represents one run, with provider-specific ranking, fluctuating
   upstream indexes, different passage-production behavior, and no
   blind relevance rubric or full-document fact checking. The
   SearXNG `/config` observations do not identify actual upstream
   contributors. The current Tavily Basic production plugin was not
   part of the comparison. Timing and apparent authority must not
   be extrapolated beyond these ten requests.

These results highlight a potentially useful *analytical distinction*
between **document discovery** and **acquisition of sufficiently detailed
evidence**, but do not adopt a two-stage architecture or authorize any
extra network authority.

## Outcome and bounded possible follow-up

Retain these observations as evidence. Do **not** change provider selection,
plugins, the accepted source envelope, retries, URL following, content
extraction, ranking, deduplication, routing, or model behavior based on this
sample.

If a separate investigation is authorized, it could measure whether
carefully bounded content from **one explicitly operator-selected public
reference** provides materially more useful evidence than a search snippet,
independently of any model generation. Such an experiment must define its
own security, privacy, and acquisition limits. Making result URLs actionable
in HAC or its plugins is **not authorized** by RFC-0077/0078/0079/0093 and
would require an applicable new architectural decision through the RFC
process before implementation.

No production change or new RFC is proposed by this document.
