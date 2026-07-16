# RFC-0035: Bounded Local Request History

Status: Draft

Date: 2026-07-16

Author: frian

## Summary

Home AI Cluster should add one explicit, bounded, prompt-free local history for
accounts produced by:

```text
home-ai-cluster-explain-request
```

History recording should be disabled by default and enabled for one invocation
with:

```text
--record-history
```

Approved history records should be stored as compact JSON Lines in one local
state file. The file should retain at most 50 records, ordered oldest to newest.

The first record must contain only a strict cluster-owned metadata allowlist. It
must not contain prompts, responses, timestamps, request identifiers, node ids,
adapter names, model names, raw exceptions, runtime addresses, or private
machine details.

Two separate local operator commands should be added:

```text
home-ai-cluster-history
home-ai-cluster-clear-history
```

The first should print the retained records as one JSON array. The second should
remove all retained records.

This RFC does not add a database, daemon, public HTTP endpoint, shared
cross-process history, lifecycle model, event log, metrics, tracing, or automatic
history for ordinary request surfaces.

## Context

Phase 7 requires request history without prompt logging by default.

RFC-0032 introduced one request-scoped explanation for a successful actual
request. RFC-0034 extended that explicit operator command with one structured
account for successful and supported failed requests.

Those accounts remain process-scoped and disappear when the command exits.

The Phase 7 prompt-free request history investigation found that:

- a short-lived CLI cannot provide useful in-memory history;
- creating a daemon only for history would be disproportionate;
- adding automatic history to `/v1/chat` would require unresolved ownership and
  concurrency decisions;
- shared history across native and OpenAI-compatible processes would introduce
  premature cross-process coordination;
- a bounded local line-oriented file is the smallest plausible durable proof.

## Goals

This RFC should:

- prove that a small amount of request evidence can survive process exit;
- keep recording explicit and disabled by default;
- retain no prompt or generated content;
- retain only a strict metadata allowlist;
- use one ordinary local file rather than a database;
- use a small fixed retention bound;
- provide obvious local inspection and clearing commands;
- preserve the RFC-0034 request account and exit semantics;
- keep history secondary to request routing and execution;
- avoid new lifecycle, event, monitoring, or tracing abstractions;
- keep `/v1/chat` and `/v1/chat/completions` unchanged.

## Non-goals

This RFC does not define or authorize:

- automatic history recording by default;
- prompt logging;
- response logging;
- timestamps or durations;
- request identifiers or sequence identifiers;
- node-id retention;
- adapter-name retention;
- model-name retention;
- raw routing-account retention;
- raw exception retention;
- request search or filtering;
- configurable retention;
- indefinite retention;
- a database;
- a daemon;
- a dashboard;
- metrics;
- tracing;
- an event bus;
- a generalized request lifecycle;
- concurrent-writer guarantees;
- remote-node history;
- fallback-path history;
- automatic `/v1/chat` history;
- automatic `/v1/chat/completions` history;
- a public or private HTTP history endpoint;
- shared history across application processes;
- multi-user access control;
- schema migration infrastructure.

## Proposal

### Explicit recording

The existing command should accept one optional flag:

```text
--record-history
```

Without this flag, behavior must remain non-retained.

With this flag, the command should:

1. construct the RFC-0034 request account normally;
2. derive one approved history record from that account;
3. attempt to retain the record locally;
4. emit the original RFC-0034 account unchanged;
5. preserve the original request-account exit semantics.

Recording must not change candidate selection, execution, fallback, routing, or
failure classification.

### History ownership

The first history belongs only to explicit invocations of
`home-ai-cluster-explain-request --record-history`.

It is not cluster-wide traffic history.

It does not represent requests entering through `/v1/chat` or
`/v1/chat/completions`.

The history implementation should remain an operator-command concern rather than
becoming a core orchestration service.

### State location

The first implementation should use the XDG state directory.

The history path should be resolved as:

```text
${XDG_STATE_HOME}/home-ai-cluster/request-history.jsonl
```

When `XDG_STATE_HOME` is unset, use:

```text
${HOME}/.local/state/home-ai-cluster/request-history.jsonl
```

The implementation must not print the resolved path in ordinary command output
or safe error messages.

Tests should inject or override the state location and must not touch the user's
real state directory.

### File format

The file should use UTF-8 JSON Lines.

Each non-empty line should contain exactly one compact JSON object followed by
one newline.

Records should be stored oldest to newest.

The file is an implementation-owned local state format, not a public API or a
cross-version interchange format.

No schema-version field is required for the first proof.

### Retention bound

The file should retain at most 50 records.

After adding one record, the implementation should keep only the newest 50
valid records.

The bound should be fixed in the first contract. No command-line or environment
configuration should be added.

### Record allowlist

Every retained record should contain exactly:

```json
{
  "status": "succeeded",
  "requested_capability": "chat",
  "selected_candidate_family": "local",
  "outcome_rule": "local-only",
  "failure_status": null
}
```

The fields are:

- `status`: exactly `succeeded` or `failed`;
- `requested_capability`: copied from the routing projection;
- `selected_candidate_family`: copied from the routing projection or `null`;
- `outcome_rule`: copied from the routing projection;
- `failure_status`: copied from `failure.status` or `null`.

No additional fields should be retained.

In particular, the record must omit:

- matched candidate families;
- selectable candidate families;
- excluded candidate families;
- selected node id;
- routing failure reason;
- result node id;
- adapter name;
- model name;
- generated content;
- stable failure reason text.

The smaller allowlist is intentional. History should retain less information
than the one-request account.

### Successful record example

```json
{
  "status": "succeeded",
  "requested_capability": "chat",
  "selected_candidate_family": "local",
  "outcome_rule": "local-only",
  "failure_status": null
}
```

### Failed record example

```json
{
  "status": "failed",
  "requested_capability": "vision",
  "selected_candidate_family": null,
  "outcome_rule": "no-selectable-candidate",
  "failure_status": "no-selectable-candidate"
}
```

### Inspection command

Add:

```text
home-ai-cluster-history
```

The command should accept no options for the first proof.

It should emit exactly one compact JSON array followed by one newline.

Records should appear newest first for operator convenience.

When the file does not exist or contains no records, output:

```json
[]
```

and exit zero.

The command should expose only valid allowlisted records.

It must not print the state-file path.

### Clear command

Add:

```text
home-ai-cluster-clear-history
```

The command should accept no options for the first proof.

It should remove all retained records by removing the history file when present.

When clearing succeeds, or when no history file exists, it should emit exactly:

```json
{"cleared":true}
```

followed by one newline and exit zero.

It must not print the state-file path.

### File creation and permissions

The implementation should create the parent state directory when recording is
explicitly requested.

New history files should be owner-readable and owner-writable only.

The first proof should target ordinary single-user local operation.

It should not add user, group, or role management.

### Safe malformed-data behavior

The history reader should validate every line against the exact record allowlist.

Malformed lines and records with unexpected fields or values should not be
returned to the operator.

The first implementation may ignore invalid lines while returning valid records.

It should not print raw malformed content, parser errors, file paths, or stack
traces.

When recording, invalid existing lines should not be copied into the rewritten
bounded file.

This is recovery behavior for a small local state file, not schema migration.

### Update strategy

A recording operation should:

1. read existing valid records when the file exists;
2. append the new record in memory;
3. retain the newest 50 records;
4. write the complete compact JSON Lines content to a temporary file in the same
   directory;
5. set owner-only file permissions;
6. atomically replace the history file.

This boring rewrite strategy is preferred over append-plus-truncate complexity.

### Concurrent writers

The first proof does not guarantee correct merging of concurrent writers.

No lock service, lock file protocol, database transaction, or cross-process
coordination should be introduced.

Documentation should state that simultaneous recording invocations may race and
that the first proof targets ordinary sequential operator use.

A later RFC may add a boring local locking rule if real evidence requires it.

### Recording failure behavior

History is secondary evidence.

Failure to read, create, validate, write, chmod, or replace the history file must
not:

- retry the request;
- reselect a candidate;
- invoke fallback;
- alter the structured RFC-0034 account;
- change a successful request account into a failed request account.

When explicit recording fails, the command should emit one stable safe warning
to stderr:

```text
warning: unable to record request history
```

The original RFC-0034 account should still be written to stdout.

The process exit code should remain determined by the actual request account:

- zero for `status: succeeded`;
- non-zero for `status: failed`.

The warning must not include raw filesystem exceptions, paths, permissions,
usernames, or private machine details.

### Inspection and clear failures

If the inspection command cannot safely read history because of an ordinary file
operation failure, it should:

- write no JSON to stdout;
- emit exactly `error: unable to read request history` to stderr;
- exit non-zero.

If the clear command cannot remove existing history, it should:

- write no JSON to stdout;
- emit exactly `error: unable to clear request history` to stderr;
- exit non-zero.

Raw filesystem errors and resolved paths must remain hidden.

### Privacy boundary

Neither the file nor any command output introduced by this RFC may retain or
expose:

- prompt text;
- message arrays;
- generated response content;
- tool arguments or outputs;
- raw requests or responses;
- raw exception messages;
- exception types or stack traces;
- runtime URLs;
- transport addresses;
- authorization values;
- private machine details;
- selected node ids;
- adapter names;
- model names;
- timestamps;
- durations;
- request identifiers.

Capability names and routing outcome metadata still reveal usage patterns.
Recording is therefore explicit and disabled by default.

### Ordinary contracts remain unchanged

This RFC must not change:

- `POST /v1/chat`;
- the dedicated OpenAI-compatible process;
- `POST /v1/chat/completions`;
- routing policy;
- fallback behavior;
- health semantics;
- `ClusterRequest`;
- `ClusterResult`;
- adapter interfaces.

## First implementation proof

A later implementation satisfies this RFC only if it demonstrates:

1. recording is disabled without `--record-history`;
2. one explicit invocation can create one retained record;
3. the record has exactly the five approved fields;
4. prompt and generated content are absent;
5. node, adapter, and model attribution are absent;
6. timestamps and identifiers are absent;
7. successful and failed accounts can both be recorded;
8. at most 50 newest records are retained;
9. storage order is oldest to newest;
10. inspection output is newest first;
11. inspection of missing or empty history returns `[]` and exits zero;
12. malformed lines are omitted without leaking their contents;
13. recording rewrites only valid retained records;
14. clearing existing history succeeds;
15. clearing missing history also succeeds;
16. new files use owner-only permissions;
17. recording failure emits only the stable warning;
18. recording failure does not alter the account or its exit status;
19. inspection and clear failures use their exact safe errors;
20. no raw paths or filesystem exceptions leak;
21. no database, daemon, lock protocol, HTTP endpoint, event model, metrics, or
    tracing is introduced;
22. automated tests use an isolated temporary state directory;
23. one explicit local proof records, inspects, and clears history without retaining
    sensitive evidence.

## Rationale

An explicit opt-in flag preserves privacy-first default behavior.

A local JSON Lines file is understandable, inspectable, deletable, and requires
no database or service.

A fixed count of 50 keeps retention visibly bounded without configuration or
policy machinery.

Omitting timestamps and identifiers avoids creating lifecycle and usage-time
contracts before they are necessary.

Omitting node, adapter, and model attribution accepts less diagnostic detail in
exchange for a safer first privacy boundary.

Separate inspection and clearing commands make local state visible and removable
without adding an HTTP endpoint or dashboard.

Atomic full-file replacement is simple enough for 50 tiny records and avoids
partial append/truncation logic.

## Alternatives considered

### In-memory history in the operator CLI

Rejected because the short-lived process loses history immediately.

### A long-running history daemon

Rejected because it introduces a service solely to retain a tiny operator aid.

### Automatic native API history

Deferred because ownership, concurrent access, read surfaces, and privacy defaults
remain unresolved.

### Shared native and OpenAI-compatible history

Deferred because it requires cross-process coordination or shared persistence.

### SQLite

Rejected for the first proof because the bounded fixed record set does not need a
database.

### Append-only indefinite JSON Lines

Rejected because privacy-first history must be bounded and obviously clearable.

### Retain the full RFC-0034 account

Rejected because it includes generated content and more routing and runtime
attribution than history needs.

### Include timestamps

Rejected for the first proof because file order is enough to prove recent history
and timestamps reveal usage patterns.

### Include node, adapter, and model fields

Rejected because the first history proof can remain useful without retaining
machine and runtime attribution.

### Make history recording best-effort without warning

Rejected because explicit recording failure should be visible even though it must
not alter request execution semantics.

### Make history failure change the request exit code

Rejected because request success and history retention are separate outcomes. The
first proof should not turn an AI request failure model into a compound storage
status model.

## Trade-offs

The history is intentionally limited. It cannot answer when a request occurred,
which node or model handled it, or correlate a record with external activity.

The first proof is not safe for concurrent writers. Simultaneous recording may
lose one writer's update.

Malformed records are ignored rather than repaired or reported individually.

The local state file is durable across process restarts but is not a stable public
storage API.

These limitations are acceptable for a first bounded, explicit, local, privacy-
conscious history proof.

## Impact

Implementation should add one small purpose-specific history module and focused
CLI entry points.

`home_ai_cluster.actual_request_explanation` should only gain the optional
recording flag and a call to the history boundary after the account is built.

The history module must not become a generic event store, persistence repository,
or request lifecycle service.

Tests should require no live runtime and use temporary directories.

## Deferred questions

Future RFCs may separately consider:

- automatic bounded in-memory history for the native application;
- automatic history for the OpenAI-compatible process;
- shared cross-process history;
- boring local file locking if concurrent use becomes real;
- timestamps or durations;
- request identifiers;
- node, adapter, or model attribution;
- configurable retention;
- filtering and search;
- aggregate statistics;
- remote and fallback history;
- durable database-backed storage;
- multi-user access control.

## Open questions

The following remain open during review:

- Is 50 the right fixed first bound?
- Should `home-ai-cluster-history` return newest-first records directly or wrap
  them in a top-level object?
- Should malformed-line omission remain completely silent?
- Should the recording warning be emitted for both successful and failed request
  accounts?

These questions must not broaden this RFC into automatic request interception,
shared history, timestamps, identifiers, a database, or a general observability
architecture.

## Decision

Pending.
