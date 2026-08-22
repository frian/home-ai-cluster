# RFC-0080: One-Shot Whole-File Code Caller Edge

Status: Accepted

Date: 2026-08-22

Author: frian

## Summary

Home AI Cluster should add one optional, finite caller-edge command:

```text
hac code-file --file PATH --message TEXT [--timeout-seconds SECONDS]
home-ai-cluster code-file --file PATH --message TEXT [--timeout-seconds SECONDS]
```

It would let an operator replace one already-existing, explicitly selected UTF-8
text file from one existing native `capability=code` result, without manual
copy/paste. It is neither a new capability nor endpoint: it sends one existing
native `POST /v1/chat` request, validates a closed content-only response
envelope, and atomically replaces only the selected target.

This RFC is deliberately narrower than the broader small-script use case.
Missing targets, patches, agents, retries, model-selected paths, and all
execution/tool authority remain out of scope. Existing `hac code` and
`hac aider` remain unchanged.

## Problem

RFC-0067 provides bounded textual code assistance but leaves an operator to
copy result text into a file. RFC-0068 through RFC-0072 prove that Aider can
perform an edit through explicit `code`, but it necessarily carries an
external coding-agent/editor lifecycle: response parsing, confirmation input,
up to two translated requests, chat history, post-edit summary, weak-model
fallback, and LiteLLM retry behavior.

The retained single-file caller investigation found that this stated one-file
use case does not require that wider lifecycle. It needs a smaller, explicit,
operator-selected file boundary that is reliable at the transport, authority,
and lifecycle levels without judging generated code quality.

## Goals

This RFC proposes to:

* preserve explicit operator authority over exactly one existing target;
* reuse the existing native `code` capability, routing, result, and finite
  native timeout contract;
* send exactly one bounded native request with no retry or continuation;
* use one closed, syntactically validated whole-file response representation;
* replace only the selected target atomically on the ordinary process boundary;
* fail closed before replacement; and
* add no caller history, agent loop, execution authority, or external caller
  dependency.

## Non-goals

This RFC does not authorize:

* missing-target, parent-directory, sibling project-file, multiple-file,
  directory, file-discovery, or model-selected path/filename creation;
* symbolic-link targets, repository awareness, Git, conflict detection,
  locking, concurrent-edit resolution, patches, diffs, or search/replace;
* model quality, syntax, safety, usefulness, compilation, execution,
  formatting, linting, testing, shell, browser, URL, tool, function, or agent
  behavior;
* retry, corrective prompt, reflection, summary, conversation history,
  weak-model fallback, model cache, daemon, persistence, database, plugin, or
  external coding-agent framework;
* a new capability, native endpoint, routing rule, runtime operation,
  model/runtime selector, compatibility model, or OpenAI-compatible `code`
  semantics; or
* any change, deprecation, replacement, or supersession of RFC-0068,
  RFC-0069, RFC-0072, `hac aider`, or `hac code`.

This RFC PR authorizes no implementation, tests, dependency, lockfile, or
production-code change.

## Proposal

### Public caller surface

After a separate implementation, the additive caller surface is exactly:

```text
hac code-file --file PATH --message TEXT [--timeout-seconds SECONDS]
home-ai-cluster code-file --file PATH --message TEXT [--timeout-seconds SECONDS]
```

It accepts exactly one `--file` and one non-blank `--message`. Omitted
`--timeout-seconds` and a supplied value use RFC-0060's existing native
client parsing, bounds, default, ownership, and failure semantics. No other
option, stdin, message file, configuration, selector, or standalone executable
is added.

`hac code` remains bounded textual assistance. `hac aider` remains the
existing separate Aider caller edge. This command is a caller-edge convenience,
not a replacement decision or HAC core file authority.

### Exact existing-target authority

The single supplied target must already exist and be a regular file. The
selected path itself must not be a symbolic link; directories, missing paths,
and every other file type fail before any native request. The caller may read
only this target and may replace only this target. It never reads a repository,
parent, sibling, or inferred file.

The operator path is the only write authority. The model receives no target
path, filename, or basename and its output contains no path field. It cannot
expand file authority. RFC-0069's Aider-specific missing-target creation does
not apply: creating a missing `code-file` target needs a later architectural
decision.

This first version does not promise locking, conflict detection, or protection
against unrelated concurrent external writers. It does not invent repository
or filesystem concurrency policy.

### Input and one native request

The target is decoded as UTF-8 with strict error handling. Decode failure fails
before any native request; the caller does not replace bytes, guess an encoding,
truncate, normalize line endings, or rewrite source before sending it.

One invocation constructs exactly two ordered plain-text messages:

1. a fixed caller-owned system instruction requiring exactly the response
   envelope defined below; and
2. one deterministic serialized user JSON value with exactly
   `instruction` (the operator message) and `current_content` (the exact
   decoded target text).

The path is absent. The fixed system text and serialized user content are
counted as constructed request message content. Their aggregate UTF-8 size must
fit RFC-0067's existing 65,536-byte `code` bound. If it does not, the caller
fails before native request construction; it never truncates a component or
creates a larger caller-specific input allowance.

A valid invocation sends exactly one existing native request:

```text
POST /v1/chat
capability = code
```

It uses ordinary native validation, routing, local-first/static behavior, and
`ClusterResult` handling unchanged. It does not use RFC-0031 compatibility,
create an endpoint, select a node/runtime/model, or make a second request.
Timeout, unavailable cluster, non-success status, malformed native result, or
any other native failure is terminal and permits neither retry nor correction.

### Closed caller-local response envelope

The native response remains the existing `ClusterResult`. Only this caller
interprets `ClusterResult.content` as one JSON document with exactly:

```json
{"version":1,"content":"complete file content as a string"}
```

Leading/trailing JSON whitespace is permitted; there must otherwise be exactly
one JSON value and no prose or fenced Markdown. The top-level value must be an
object with exactly the keys `version` and `content`; duplicate keys are
rejected during parsing. `version` must be the JSON integer `1`; JSON `true`,
`1.0`, and `"1"` are rejected. `content` is a JSON string. Unknown keys,
filename/path, language, success, patch/diff metadata, wrong types/version,
duplicate keys, malformed JSON, or surrounding content fail before replacement.

An empty result is valid:

```json
{"version":1,"content":""}
```

Validation is syntactic only. The caller neither evaluates whether the text is
correct, safe, executable, idiomatic, complete, nor useful, nor does it inspect
the target after replacement to infer success.

### Output encoding and bound

Before any write, validated `content` must encode under strict UTF-8 and be at
most 65,536 UTF-8 bytes. This is a caller-local output/write bound; it does not
change `ClusterResult` generally or RFC-0067's input bound. Encoding failure
or an oversized value fails before target replacement.

The exact validated string, UTF-8 encoded, is the complete replacement. The
caller does not guess encoding, normalize line endings, or add/remove a final
newline.

### Atomic replacement and permissions

The caller must not truncate or rewrite the target in place. It may create
exactly one caller-selected private temporary sibling in the target's existing
parent directory, solely for a single replacement transaction. This file is not
an editable/model-visible target; it contains only the validated replacement,
and begins with restrictive private permissions. It is cleaned up on ordinary
pre-replacement failure. An abnormal process or host crash can leave it behind;
that bounded local privacy trade-off is explicit.

Before one same-directory atomic replacement, the future implementation must:

1. complete all input, native-result, envelope, UTF-8, and output-bound checks;
2. write the complete UTF-8 replacement to the private sibling and flush it;
3. make the temporary file durable enough for the ordinary process-crash
   boundary;
4. apply the selected target's preserved ordinary POSIX owner/group/other
   permission bits (`0o777`) to the temporary replacement; and
5. atomically replace the selected target once.

Successful replacement preserves only the selected target's ordinary POSIX
owner/group/other permission bits (`0o777`). It must not preserve or add setuid,
setgid, or sticky bits, and it must not add executable permission beyond a bit
already present in the preserved `0o777` mode. This first version deliberately
does not promise preservation of owner/group identity, ACLs, extended
attributes, inode identity, timestamps, or other filesystem-specific metadata,
nor power-loss/filesystem durability beyond the stated ordinary process-crash
boundary. It uses standard library filesystem primitives; no transaction
library is authorized.

After the preserved `0o777` mode has been applied but before atomic replacement,
an abnormal process or host crash can leave the private temporary sibling with
those preserved ordinary target permissions rather than its initial restrictive
private permissions. Normal pre-replacement failures still clean it up. This
bounded crash-residue case does not authorize locking, a cleanup daemon,
recovery scan, or another filesystem mechanism.

Before final replacement, every failure—including target validation/decoding,
input bound, native failure/timeout, invalid result/envelope, output bound,
temporary creation/write/flush, durability preparation, or permission
preparation—leaves the selected target's contents unchanged. Once replacement
succeeds, no later fallible operation may cause a false failure result. Success
means the complete validated replacement became the selected target; failure
before replacement means its prior contents remain.

### Privacy

The caller creates no prompt, generated-response, conversation, retry, or audit
history; it creates no cache, database, daemon, or retained configuration.
Existing HAC server/request-history behavior is unchanged. Operator instruction
and selected-target text travel only in the one existing native request under
existing request constraints. The private temporary output exists only for the
atomic transaction and has the disclosed abnormal-crash residue risk.

## Rationale

Whole-file replacement is the smallest reliable first boundary for one small,
explicit file: one target, one request, one closed syntactic result, and one
replacement. It has no model path authority, agent lifecycle, or patch parser.

Aider remains valid for its accepted use case, but it is materially broader than
this one. The retained investigation also rejected OpenCode and Goose as
agent/tool frameworks, not smaller deterministic callers. A general patch
protocol solves no demonstrated problem here and would add parsing, ambiguity,
partial-application, and likely corrective-loop questions. Raw or fenced model
output cannot distinguish source from prose deterministically; the closed
content-only envelope can.

Private same-directory temporary material is the smallest portable path to
atomic visibility. It adds a narrow crash-residue trade-off, but makes it
visible and keeps the model from choosing a second target.

## Alternatives considered

### Retain Aider as the only editing edge

Rejected for this proposal. It remains supported, but its lifecycle and
dependency surface are broader than the narrow one-file need.

### Plain or fenced response text

Rejected. Neither provides an unambiguous empty-file, prose, multiple-block, or
single-document contract.

### Structured patch, diff, or search/replace protocol

Rejected. It introduces parser, context, ambiguity, partial-application and
conflict rules for an unproven problem.

### Allow missing target creation now

Rejected. RFC-0069 is Aider-specific. Portable non-overwriting creation adds a
separate filesystem decision that should not be mixed with this first boundary.

### In-place write

Rejected. A write/flush failure can expose a truncated selected target.

### External coding agent

Rejected. Aider, OpenCode, and Goose are broader lifecycle/tool dependencies;
the required caller responsibilities are smaller and explicit.

## Trade-offs

This command reads and replaces an operator-selected existing file, which is
new caller-edge authority. It also sends that file's text through the existing
native request and uses one private temporary sibling that can survive an
abnormal crash. The 65,536-byte input/output bounds can reject useful larger
files. There is no automatic repair for malformed model output.

These are deliberate costs: they retain explicit authority, local-first native
routing, fail-closed behavior, finite lifecycle, and a boundary explainable as
validate → request → validate → replace. An operator who needs broader editing
can continue to use the unchanged Aider edge.

## Impact

If accepted, this RFC authorizes only a later, separate implementation and
model-free proof of this exact optional caller edge. It must not change native
server/API/routing behavior, capability admission, `ClusterRequest`,
`ClusterResult`, compatibility, runtime adapters, Aider, or existing commands.

The later proof must cover exactly one existing regular non-symlink target,
strict UTF-8 input, one native `capability=code` request, aggregate input
bound, valid and empty response replacement, malformed/duplicate/unknown
envelope failures without write, output bound, native timeout without write,
temporary failure without target change, mode preservation, ordinary cleanup,
and no retry/history/tool/execution behavior. Generated code must not run.

## Open questions

The fixed system instruction wording and deterministic JSON serialization
details are implementation details, provided they preserve this RFC's exact
message roles, fields, bounds, and absence of path data. Cross-platform
directory durability and exceptional permission errors need focused
implementation evidence, but do not authorize stronger durability or metadata
promises than this RFC states.

## Decision

Accepted.
