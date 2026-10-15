# Document Evidence Selection Investigation

## Scope and research question

This October 2026 investigation asked whether supplying more documentary
evidence, selecting more relevant passages, or improving document boundaries
improves a local model's source-grounded answers. It was an exploratory,
offline document-acquisition and evidence-selection exercise, not a Home AI
Cluster feature or architectural proposal.

The experimental path was:

```text
HTML extraction -> text segmentation -> evidence selection -> local-model inference
```

It covered documentation about Python free-threading, Rust edition 2024, Linux
io_uring, CUDA memory spaces, and SQLite WAL. Full-page acquisition and
segmentation were experimental tooling, not existing HAC production behavior.

RFC-0077 keeps acquisition outside the source-grounded Chat contract and treats
source provenance as supplied data rather than truth or a model-use guarantee.
RFC-0078 keeps provider acquisition at an optional, explicit plugin boundary.
Nothing in this investigation changes those boundaries.

## Experimental setup

The frozen candidates compared naive document-order selection, lexical
selection, lexical selection with neighboring passages, boundary-aware
segmentation, and conservative navigation/table-of-contents cleaning. The
neighboring-passage hybrid sometimes introduced irrelevant material. No method
was shown to be universally superior.

| Subject | Comparison observation | Result |
| --- | --- | --- |
| SQLite WAL | Lexical versus cleaned 2048-byte candidates | Cleaning admitted checkpoint material without a larger budget. |
| Linux io_uring | Lexical versus boundary-aware 2048-byte candidates | A complete SQ/CQ explanation replaced a truncated passage; run accounting is contradictory. |
| Rust 2024 | Lexical versus cleaned 2048-byte candidates | Different useful details survived in each answer. |
| Python free-threading | Offline selection candidates | No retained fresh Qwen A/B answer comparison was found. |
| CUDA memory spaces | Offline selection candidates | No retained fresh Qwen A/B answer comparison was found. |

Nominal evidence budgets were upper bounds rather than equal inputs. For
example, lexical SQLite evidence was 1,694 UTF-8 bytes at the 2,048-byte budget,
whereas cleaned SQLite evidence was 1,641 bytes.

## Observations

### SQLite

The original lexical 2 KiB evidence was 1,694 UTF-8 bytes; the cleaned
candidate was 1,641 bytes. The cleaned selection replaced navigation and
table-of-contents material with checkpoint explanations, including checkpoint
transfer and the effect of active readers. Thus its favorable qualitative result
was not caused by an increased evidence budget.

The retained answer artifacts support a more complete checkpoint explanation in
the cleaned answer. A requested independent six-fact assessment of “3/6” for
the original answer and “5/6” for the cleaned answer was not found in the
retained artifacts: the contemporaneous human-evaluation files are explicitly
unscored. Those counts are therefore not reported here as verified results.

### Linux

Boundary-aware segmentation preserved the complete explanation that I/O
requests are placed on the submission queue and results are placed by the
kernel on the completion queue. The lexical evidence ended mid-word and the
boundary-aware answer consequently gave a better-grounded CQ description.
Conversely, the baseline retained more explicit shared-buffer context.

Both answer and raw-response artifacts are retained and their answer digests
were checked against the files. The execution record is not clean: the boundary
attempt has a durable intent followed by both `SUCCESS` and
`AMBIGUOUS_INTERRUPTED` terminal events. This is an exploratory comparison with
an execution-accounting limitation, not a clean comparative run.

### Rust

Cleaning removed the leading explicit list of unsafe attributes while retaining
relevant material elsewhere. Both conditions have successful terminal events
and matching retained answer/response artifacts. The cleaned answer included
complete syntax such as `#[unsafe(no_mangle)]` and mentioned that the compiler
cannot automatically verify correctness. The lexical answer instead made the
symbol-collision risk explicit. This is a mixed result, not evidence of a
general improvement or regression.

### Python and CUDA

Python and CUDA were included in the offline documentary-selection comparison.
No matching retained fresh Qwen A/B answer artifacts were found for these
selection candidates, so no inference-quality comparison is claimed for them.

## Negative results and counterexamples

More selected text did not establish a general answer-quality improvement. The
hybrid neighboring-passage method could add irrelevant material. Cleaning also
has an information-loss cost: in Rust it removed the explicit introductory
enumeration of the three unsafe attributes, while in SQLite it made useful
checkpoint explanations selectable. Boundary-aware segmentation repaired the
Linux truncation but did not retain every piece of shared-buffer context.

The cross-document coverage reviews offer useful leads, but their AI-assisted
semantic classifications include disputed judgments and citation defects. Their
aggregate coverage totals are not independently established scientific results.

## Experimental reliability and limitations

The evaluation contains only five documents and one generation per condition.
Runtime sessions and resource conditions differed; temperature zero does not
guarantee identical outputs. Nominally equal budgets did not mean equal byte
counts, and documentary fact coverage does not guarantee answer quality.

The evidence-selection and cleaning rules were experimental. The investigations
also exposed experimental-runner defects: duplicate terminal-event accounting
and sandbox permissions affecting local Ollama access. A later synthetic,
offline runner prototype addressed the terminal-accounting class by separating
writer-owned terminal events from supervisor observations. These are
experimental-infrastructure observations, not defects attributed to HAC.

No production-readiness claim follows from this work.

## Conclusions

Improving relevance and coherence of supplied documentary evidence can improve
a local model's source-grounded answer without increasing the evidence budget.
Selection and cleaning can also discard useful information. The work does not
establish a generally superior strategy, justify an immediate HAC change, or
recommend a production implementation.

It does not authorize automatic full-Web-page fetching, changed network or
source-acquisition permissions, a larger production evidence budget, a
production document parser, a new retrieval architecture, embeddings, vector
databases, or additional model dependencies. Any future acquisition or
authorization change requires the normal RFC process and must preserve
local-first, privacy-first, engine-independent, capability-centered, and
boring-solutions-first principles.

## Open questions

- Can a broader, independently reviewed corpus reproduce the SQLite and Linux
  observations?
- Which selection rules preserve useful context while avoiding navigation,
  table-of-contents, and neighboring-passage noise?
- How should future experiments separate evidence coverage, factual support,
  answer usefulness, and execution reliability?

## Evidence provenance

The following local, read-only experiment archives are provenance records, not
durable public links. No archive was copied into this repository.

| Archive and retained identity | Verified detail |
| --- | --- |
| `/tmp/hac-generic-document-acquisition-investigation-v2/` | Five-source corrected replay; SQLite lexical 2048 evidence SHA-256 `d9dda39cae3e22f6b7654a1dad04daec012e9828d0f14435183815d9712989e9`. |
| `/tmp/hac-document-boundary-investigation-PhoeRy/` | Cleaned SQLite 2048 evidence: 1,641 bytes; SHA-256 `b9f62e79914657ff618e8363caebffcc9970c5c4ae2b8e33e2c0d62e98ea6e93`. |
| `/tmp/hac-sqlite-evidence-size-comparison-axBiZF/` and `/tmp/hac-sqlite-cleaned-2k-qwen-gDIw6k/` | Lexical attempt `sqlite-2048-29f39fd85acf`; cleaned attempt `440fa434-34c9-40ce-ae7c-a3c94b5f5444`; cleaned answer SHA-256 `815ed3d2fab54f65f40da191a5088f20ee44768f1790e132239141e748544b6a`. |
| `/tmp/hac-linux-boundary-qwen-comparison-1zjUkF/` | Boundary attempt `ffc7e1a6-b9e0-4011-b6e9-04a99a5b6568`; lexical/boundary answer SHA-256 `16f8df0280781f80597e9cf39ccbc400b0c647ad6fc4d035fbfc47ab538a4612` / `9352a2ce61ab727ae4260cb9c680d09fb1cb0fa5e92515d1c73ed398e928f1d1`. |
| `/tmp/hac-rust-cleaning-qwen-comparison-BsFEb3/` | Successful attempts `5740d3ea-f69d-46e2-bdd5-19a115de15f8` and `b8d58cb9-4371-4ee9-b0f1-76bed6012cdc`; answer SHA-256 `89bc9df3a0b019e8c0706bfb645e7d90042b0b79b6340ab306471294b9045fbc` / `82173c3f5d44fd73ad1b7fc8e11664b040ee878acd26282ab41db2fa2914cc15`. |
| `/tmp/hac-generic-hybrid-evidence-investigation-ma7sse/`, `/tmp/hac-experimental-runner-reliability-JiXYuQ/`, and the two `/tmp/hac-document-evidence-coverage-*` reviews | Hybrid, reliability, and coverage-review context; the latter reviews remain provisional and corrected rather than conclusive. |
