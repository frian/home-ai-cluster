# Single-file code caller investigation

Status: Current

Date: 2026-08-22

## Operator problem

The narrow requirement is to create or modify one explicitly selected small
administration or maintenance script without manually copying generated code.
This investigation concerns file-edit transport, target authority, and caller
lifecycle—not model quality. It does not implement or replace `hac aider`.

## Current boundary

RFC-0067's native `POST /v1/chat` accepts explicit `capability=code` and
returns free-form textual `ClusterResult`; HAC has no filesystem, repository,
shell, Git, test, tool, or execution authority. RFC-0068/0069/0072 separately
add one Aider `0.86.2` caller: Aider owns target read/edit, while HAC translates
at most two qualifying Aider requests into native `code` requests. Only an
explicit missing leaf may be created.

Current `aider_command.py` validates one target, creates only that missing leaf,
starts an Aider subprocess and translator, and constructs `capability=code`.
`code_command.py` already makes one native `code` request. The public
OpenAI-compatible route is Chat-only and cannot become the dependency of a new
code caller.

The Aider proofs establish a selected-file edit, but Aider also owns whole-file
parsing, confirmation behavior, a private translator, corrective interaction,
history, post-edit summary, weak-model fallback and LiteLLM retries. PR #502
and #503 found no compliant deterministic suppression of that lifecycle. This
is not a criticism of model quality; it is unnecessary machinery for one file.

## Minimum caller responsibilities

An irreducible caller must:

1. validate exactly one operator-selected target; existing targets are files,
   and a missing target has an already-existing parent directory;
2. create only the named missing leaf, if that authority is accepted;
3. read only the existing selected target when its literal content is required;
4. send one bounded native `POST /v1/chat` request with `capability=code` and
   one finite timeout, with no caller retry;
5. validate one bounded, non-semantic response envelope before any write;
6. replace exactly the selected target or return non-zero without a write; and
7. clean up and avoid default prompt/generated-content retention.

It must never trust a model path, infer a target, inspect source semantics,
execute generated content, or produce a corrective prompt.

## Candidate comparison

| Candidate | Useful responsibility | Cost/finding |
| --- | --- | --- |
| A. Retain Aider 0.86.2 | target read/edit and whole-file interpretation | Baseline; requires agent/editor lifecycle and at most two native requests |
| B. HAC-owned whole-file caller | exact target, one request, envelope validation, replacement | Technically sufficient and materially smaller |
| C. Structured patch caller | potential large-file efficiency | Premature: adds parser, ambiguity and partial-application rules |
| D. Maintained external caller | external provider/editor integration | No candidate retained |

### A. Retain Aider

Aider usefully reads the target, interprets an edit result, writes it, and
reports its own failure. A replacement still needs exact-target validation,
response representation, write transaction, and truthful failure handling. It
does not need conversation/history, summary, weak model, LLM retry,
confirmation stream, Git orientation, repository behavior, or an agent loop.

### B. Whole-file response contract

The smallest deterministic candidate is not plain output or a fence parser. It
is a closed structured envelope carried in HAC's existing textual result:

```json
{"version": 1, "content": "complete file content as a string"}
```

`content` is the complete target text; `version` closes the representation.
There is no filename, path, language, patch base, or success flag. The CLI path
is the only write destination, and an empty file is `{"version":1,"content":""}`.
An RFC would need to set a finite encoded-response limit, UTF-8 encoding for
writing validated content to disk, and existing/new-file permission policy.

Free-form content is ambiguous because prose and source are both text. Fenced
extraction is likewise ambiguous (multiple fences, prose, language labels, or
empty files) and recreates an Aider-like parser. The JSON envelope is syntactic,
not semantic: missing/unknown fields, wrong type/version, decoding failure, or
oversized content fail before writing. It does not claim the script is correct.

One native request is sufficient only when malformed output, unavailable HAC,
or timeout is an invocation failure—not an invitation to retry or correct. A
modification request may include literal existing selected-file content; an
absent target supplies no invented context. A target beyond the existing input
bound must fail rather than truncate or expand authority.

Atomic replacement normally needs a caller-owned temporary file in the target
parent, `fsync`, then rename/replace. It protects the original target before
replacement, but it creates temporary sibling material. A portable atomic rule
therefore requires an RFC decision on that private, cleaned-up material rather
than assuming it fits the current no-sibling-creation boundary. A crash before
replacement leaves the old file; after replacement it leaves the complete new
file. Directory durability and metadata policy need explicit platform-aware
rules.

### C. Structured patch protocol

Whole-file replacement covers the stated small-script case without a patch
parser, model-selected path, context matching, partial apply, conflict handling,
or correction request. Diffs and search/replace blocks solve a different,
unproven large-file/surgical-edit problem and need grammar, one-target rejection,
unique matching and all-or-none behavior. A patch protocol is premature.

### D. External callers

No external candidate was retained. Aider `0.86.2` is the baseline but fails
the smallest/deterministic lifecycle test in prior investigations.

OpenCode current release [`v1.18.21`](https://github.com/anomalyco/opencode/releases/tag/v1.18.21)
supports custom OpenAI-compatible providers, but HAC compatibility is Chat-only,
not `code`. OpenCode documents a coding agent with built-in read, edit/write,
shell, task/subagent, web, and extensible MCP tools; permissions can constrain
them but its non-interactive `opencode run` does not create a one-target,
one-request protocol. It is rejected.

[Goose `v1.33.1`](https://github.com/aaif-goose/goose/releases/tag/v1.33.1)
(2026-04-29) describes an extensible agent that can install, execute, edit, and
test with MCP extensions. Its local-provider support cannot overcome the
no-agent/no-tool/no-execution boundary. It is rejected. These quick rejections
are not a coding-agent catalogue.

## Model-free protocol evidence

Two disposable `/tmp` probes used no HAC server, Ollama, model, generated-code
execution, repository file, or retained prompt/source. An envelope/atomicity
probe showed: valid content replaced the selected file; a valid empty envelope
produced a zero-byte file; malformed fenced text was rejected before writing;
an injected replacement failure preserved old selected content.

A second temporary-loopback fake native `/v1/chat` responder performed four
independent invocations. Each made exactly one `capability=code` request. Valid
and empty envelopes wrote; malformed envelope and timeout failed before write.
The final selected file was the deliberate valid empty result. This is evidence
only for controlled protocol mechanics, not output quality, production crash
durability, or an authorization to implement.

## Reliability comparison

| Question | Aider baseline | Whole-file candidate |
| --- | --- | --- |
| Target authority | Aider parses model filenames; HAC feeds continuous No | CLI target is sole destination; envelope has no path |
| Requests/lifecycle | up to two; Aider owns continuation/history/retry/summary | one request; no retry/history/reflection |
| Git, shell, tools, execution | disabled guardrails over Aider subsystems | absent |
| Missing/existing target | RFC-0069 leaf creation; Aider edit | exact leaf rule; RFC must decide write/create semantics |
| Malformed response/timeout | Aider interprets response and can continue | non-zero before write; no second request |
| Crash/write failure | Aider-owned behavior | atomic replace protects old file before replacement; RFC contract needed |
| Privacy/dependencies | Aider, LiteLLM, subprocess/config | existing native path and file primitives; no external agent |
| Explainability | Aider-specific, wider lifecycle | validate → request → validate → replace |

## Outcome and next step

**Outcome B — a HAC-owned whole-file caller edge is technically sufficient and
materially smaller/more deterministic than Aider.** This is an inference from
the native contract, controlled protocol evidence, and lack of a demonstrated
patch requirement. It is not authorization to replace Aider.

The smallest next step is a focused RFC deciding: one optional caller surface;
exact target read/create/write authority; the closed content-only envelope and
byte/encoding limit; temporary-file/atomic-replacement and permission policy;
failure/timeout status semantics; and privacy/no-retention behavior. Only then
could implementation be considered. The Aider edge remains unchanged.
