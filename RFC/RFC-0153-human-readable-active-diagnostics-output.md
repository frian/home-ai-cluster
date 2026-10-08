# RFC-0153: Human-Readable Active Diagnostics Output

Status: Draft

Date: 2026-10-08

## Summary

This RFC proposes one bounded presentation change for exactly these existing
active-process diagnostic clients:

```text
hac explain-active-routing
hac explain-active-request
```

Each command would retain its current compact JSON stdout as its default and
would accept `--format text` for a deterministic, human-readable plain-text
projection of the one complete, validated response it already obtained. The
explicit `--format json` spelling would select the same current JSON output.

This is a CLI-edge proposal only. It neither changes the RFC-0147 or RFC-0149
HTTP carriers nor adds facts, endpoints, routing, execution, fallback, timing,
or lifecycle instrumentation. The active process remains the sole authority for
the facts being displayed.

## Problem

RFC-0148 and RFC-0150 deliberately require compact JSON stdout. That is useful
for scripts and is the correct current behavior. During operator dogfooding,
however, inspecting active routing and actual-request accounts repeatedly
required `jq` to find local eligibility, ordered declared remotes, selection,
permission, invocation, continuation, final attribution, failure, and result.

The problem is presentation, not a defect in the accepted JSON contracts. A
human-readable view can make one already completed public account easier to
inspect without making the CLI reconstruct routing or infer hidden events.

## Goals

- Add one explicit, deterministic human-readable presentation for each command.
- Preserve RFC-0148 and RFC-0150 JSON stdout byte-for-byte by default and when
  `--format json` is selected.
- Preserve carrier response shapes, client validation, request submission,
  timeout, retry, privacy, ordering, exit, and stderr contracts.
- Project only facts already present in the validated public response.
- Keep formatting local to these two command edges without a generic reporting
  or diagnostics framework.

## Non-goals

This RFC does not introduce:

- a new HTTP endpoint, carrier field, lifecycle fact, or public response shape;
- changes to RFC-0145, RFC-0146, RFC-0147, RFC-0148, RFC-0149, or RFC-0150
  server-side authority, routing, execution, permission, or continuation;
- a routing recomputation, health probe, retry, timeout change, progress view,
  event timeline, polling, color, TTY detection, interactive UI, or table
  framework;
- retained configuration migration, history, persistence, telemetry, web UI,
  process discovery, remote administration, or generic diagnostics machinery;
- an answer to OBS-01 or OBS-02. This proposal addresses OBS-03 only.

## Existing authority and invariants

RFC-0146 and RFC-0147 establish one bounded active-process static-routing
explanation. Its complete public response is:

```text
capability
local_only
local_eligible
eligible_remote_node_ids (ordered)
remotes_excluded_by_local_only
initial_selection (local, declared_remote with node_id, or null)
```

RFC-0145 and RFC-0149 establish one actual-request account from the same
ordinary execution. RFC-0150 validates and prints that account. Its response
contains `status`, `result`, `failure`, and an `explanation` containing
requested capability, local-only restriction, initial selection, ordered
candidate facts, ordered continuations, and final node attribution.

The following remain mandatory:

1. The CLI sends exactly its existing one request and performs its existing
   validation before formatting.
2. It must not recompute eligibility, selection, permission, invocation,
   continuation, fallback, or final attribution; it must not invent unknown or
   absent information.
3. Candidate-fact order and continuation order remain public order. A
   continuation describes the same request continuing after a named candidate;
   it is never displayed as a new request.
4. `execution-permission-denied` and
   `execution-permission-refused` remain permission facts. They are not runtime
   failures. `transport-invoked` means transport was invoked; it does not claim
   successful remote execution. `adapter-invoked` likewise is not a success
   claim.
5. A complete `status: "failed"` account remains a successfully obtained
   explanation. It remains stdout result data and exits zero under RFC-0150.
   Client/input/carrier/validation failures remain stderr-only failures.
6. No raw exception, URL, address, credential, retained configuration, hidden
   routing reason, private transport detail, prompt, or additional lifecycle
   detail may enter text output.

## Proposal

### Format selection

Both included commands accept:

```text
--format json
--format text
```

`json` is the default. `text` selects the human-readable projection. The
option follows normal argparse placement for each command: routing accepts it
with its existing root options; each active-request capability subcommand
accepts it with its existing options. It is not a global `hac` option and does
not alter the request body.

Only the two lowercase values above are accepted. `--format=text` is the
ordinary equivalent spelling of `--format text`. Missing option values,
unknown values, and repeated format options are invalid local input: the
existing safe invalid-input stderr line is emitted, no HTTP request occurs, and
the command exits 2. The exact parser mechanics remain an implementation detail
so long as one value is accepted and ambiguity is rejected.

Selection is independent of TTY state, redirection, pipes, environment,
configuration, width, locale, color support, and terminal capabilities. There
is no `--json`, `--human`, `--pretty`, color mode, automatic terminal choice,
or third format in this proposal.

### JSON compatibility

No-option invocation and `--format json` must emit exactly the representation
already required by RFC-0148 and RFC-0150:

- one compact `json.dumps(..., separators=(",", ":"))` JSON object;
- current field names, field insertion order, object/array structure, nulls,
  vocabulary, and ordered arrays; and
- exactly one trailing newline, no prose on stdout, and existing stderr and
  exit behavior.

This is byte-for-byte compatibility for a given validated response, not merely
semantic JSON equivalence. It preserves existing scripts without migration.

The accepted carriers and clients currently reject undeclared response fields.
This proposal does not weaken that fail-closed boundary. A future optional
public field requires a separate accepted carrier/client compatibility decision.
That decision must specify both JSON behavior and whether text displays the
field; it must not silently omit a newly accepted meaningful field.

### Text presentation rules

`--format text` writes one complete report and one trailing newline to stdout.
Exact indentation and blank-line count are not contractual. Labels, section
order, public vocabulary, required facts, and source ordering are contractual.
No ANSI sequence, color, column alignment, or terminal capability carries
meaning.

Text is a projection, not a second data model. It must use only the validated
response and must make relevant empty collections and absent values explicit as
`none`. It must retain literal public status, fact, and reason vocabulary in
parentheses where prose would otherwise obscure it. It must not imply elapsed
time, an unreported event order, a causal detail, or a successful execution
beyond what the public account states.

Public node identifiers, adapters, models, labels, and text result content are
untrusted terminal data. Formatting must use a deterministic terminal-safe,
injective rendering for labels and scalar values: no control character or escape
sequence is written raw. For ordinary scalar fields, a quoted/escaped rendering
is permitted. This is presentation escaping, not added data.

For textual business result content, the report has a `Content:` block. Every
accepted content character is represented, in source order, without truncation,
summary, rewriting, or omission. Logical LF characters delimit displayed
content lines; all other control characters, including CR, ESC, and C0/C1
controls, are rendered as visible escapes. This preserves multiline content
while preventing content from changing terminal state or HAC-owned report
structure. An empty content value is explicitly shown as an empty block. No
business content is printed for a failed account because RFC-0149 supplies no
result in that case.

### Active routing report

The report must present, in this logical order:

1. requested `capability` and `local_only`;
2. local eligibility;
3. eligible declared remotes in their response order, or `none`;
4. whether those remotes were excluded by the local-only restriction;
5. initial selection as `local`, `declared remote <node_id>`, or `none`; and
6. an explicit `No selectable candidate: yes` when selection is absent.

It must distinguish `local` from every `declared remote`. It must not describe
an eligible remote as selected when local precedence selected local, nor infer
why an ineligible candidate was not eligible.

Illustrative local selection:

```text
Active routing explanation
Capability: chat
Local only: false
Local eligible: true
Eligible declared remotes: remote-a, remote-b
Remotes excluded by local-only: false
Initial selection: local
No selectable candidate: no
```

Illustrative remote selection:

```text
Active routing explanation
Capability: summarize
Local only: false
Local eligible: false
Eligible declared remotes: remote-a, remote-b
Remotes excluded by local-only: false
Initial selection: declared remote remote-a
No selectable candidate: no
```

### Actual-request report

The report must present, in this logical order:

1. requested capability, local-only restriction, and overall account status;
2. initial selection, or `none`;
3. `Candidate facts`, in their existing sequence, retaining each candidate's
   family (`local` or `declared remote`), node identifier, and exact fact;
4. `Continuations`, in their existing sequence, retaining node identifier and
   exact reason, or `none`;
5. final execution node, or `none`;
6. failure status, or `none`; and
7. result metadata and content for a succeeded account.

Candidate facts for one candidate may be visually grouped only when that
grouping preserves their contiguous public sequence. The report must not add an
attempt number, duration, success claim, runtime diagnosis, or unstated event.
The continuation section must say that it is continuation of the same request.

For text results, metadata is `Node`, `Adapter`, and `Model` (with absent model
shown as `none`), followed by the complete terminal-safe `Content:` block. For
classification, metadata is `Node` and `Selected label`; it has no synthetic
text content. A business failure has no result section and must show its exact
failure status.

Illustrative successful local request:

```text
Active request explanation
Capability: chat
Local only: false
Status: succeeded
Initial selection: local

Candidate facts:
- local local-1: execution-permission-granted
- local local-1: adapter-invoked
Continuations: none
Final execution node: local-1
Failure: none

Result:
Node: local-1
Adapter: adapter
Model: none
Content:
hello
```

Illustrative local permission denial followed by remote continuation:

```text
Active request explanation
Capability: chat
Local only: false
Status: succeeded
Initial selection: local

Candidate facts:
- local local-1: execution-permission-denied
- declared remote remote-a: transport-invoked
Continuations (same request):
- after local-1: local-execution-permission-denied
Final execution node: remote-a
Failure: none

Result:
Node: remote-a
Adapter: adapter
Model: none
Content:
remote answer
```

Illustrative explained business failure:

```text
Active request explanation
Capability: summarize
Local only: true
Status: failed
Initial selection: local

Candidate facts:
- local local-1: execution-permission-denied
Continuations: none
Final execution node: none
Failure: execution-permission-denied
Result: none
```

## Errors and exits

Format selection happens only after the existing complete response has been
validated. It must not change request count, request body, client timeout,
HTTP status mapping, safe stderr messages, retry behavior, or response
validation.

For either format:

- valid routing explanation, including no selection, writes stdout and exits 0;
- valid actual-request account, including `status: "failed"`, writes stdout and
  exits 0;
- invalid local invocation, including invalid format, writes the established
  command-specific safe invalid-input line to stderr, writes no stdout, and
  exits 2; and
- existing connection, timeout, carrier, malformed-response, and unexpected
  client failures remain stderr-only, use their established safe line, write no
  result stdout, and exit 1.

No new safe-error taxonomy is introduced. A formatter failure after successful
validation must be handled as the existing safe generic client failure; it must
not leak public content or an exception and must not produce a partial report.

## Alternatives considered

### Text default with explicit JSON

This follows RFC-0048's inspection-command decision and is attractive for
interactive use. It is rejected here because RFC-0148 and RFC-0150 make JSON
mandatory public stdout, these commands have newer compatibility-sensitive
contracts, and the actual-request command may emit business content. Changing
the no-option contract would require existing automation to migrate despite no
repository evidence that every operator wants that break.

### JSON default with `--human`

This is compatible but creates a second naming pattern beside the explicit
two-value format selection considered for this bounded pair. `--format text`
states the selected representation directly and leaves a symmetric explicit
JSON spelling without introducing a third form.

### TTY-dependent behavior

Rejected. The same invocation must not change merely because stdout is piped
or redirected.

### Pretty JSON, `jq`, or documentation only

These remain useful operator choices but do not supply a bounded semantic
presentation at the command edge.

### A shared renderer or all-diagnostics policy

Rejected as premature. RFC-0048 covers a distinct, accepted inspection scope;
these commands have active-process and business-content constraints. Two small
command-specific projections are sufficient evidence now.

## Compatibility and rollout

This is additive: existing invocations retain exact JSON stdout. `--format
text` is new syntax only. An accepted RFC would supersede only RFC-0148 and
RFC-0150's CLI presentation requirement to the narrow extent necessary to add
that explicit text alternative; it would not supersede either carrier,
authority, validation, or execution contract.

No transition warning, automatic migration, environment toggle, configuration,
or documentation rewrite of existing JSON examples is necessary. Future
documentation may demonstrate the opt-in text form after implementation.

## Implementation and testing consequences

No implementation is authorized by this Draft. If accepted, the smallest
implementation should add command-local pure formatting after existing response
validation and selected-output emission. It should not modify server code,
carrier models, or ordinary orchestration.

Tests must cover at least:

- both commands in default JSON, explicit JSON, and text modes;
- byte-for-byte JSON compatibility and one trailing newline;
- all required text facts, empty/absent values, local versus declared-remote
  distinction, candidate and continuation order, and no fabricated facts;
- local and remote routing selection and no-selectable routing;
- local success, permission-denial continuation, remote transport/refusal
  semantics, explained business failure, and classification result metadata;
- complete multiline content and terminal-control escaping without truncation;
- stdout/stderr separation, client failures, invalid format, and zero exit for
  a valid failed business account; and
- absence of raw exceptions, URLs, addresses, credentials, prompt data, and
  extra private lifecycle/configuration information.

## Open questions

The exact quote character, indentation, and blank-line layout are left to a
future implementation as long as the required labels, facts, ordering, safe
escaping, and complete content rules hold. No further format or scope decision
is needed to review this proposal.

## Decision requested

Accept an additive `--format text|json` contract, with JSON as the default,
for only `hac explain-active-routing` and `hac explain-active-request`, subject
to the compatibility, privacy, and thin-client boundaries above.

Implementation remains separate and requires acceptance first.
