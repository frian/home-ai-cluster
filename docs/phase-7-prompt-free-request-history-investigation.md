# Phase 7 Prompt-Free Request History Investigation

Status: Investigation

Date: 2026-07-16

## Purpose

This document investigates the remaining Phase 7 roadmap outcome:

> request history without prompt logging by default

The question is:

> What is the smallest truthful request-history capability Home AI Cluster could
> add without retaining prompts or responses, introducing a database, or creating a
> premature lifecycle, event, tracing, or monitoring architecture?

This investigation does not select a storage mechanism, retention period, request
identifier format, public endpoint, or implementation.

Any architectural decision requires a later RFC.

## Current evidence

Home AI Cluster now has three request-scoped operator facts:

1. one actual request can be automatically selected and executed while preserving
   the routing explanation from that same selection;
2. one actual request can produce one structured successful or failed account;
3. the structured account can omit prompt content, raw exceptions, runtime URLs,
   transport details, authorization values, and private machine details.

The structured actual-request account currently contains:

- top-level status;
- eight routing fields;
- a normalized successful result projection or a small failed-outcome projection.

The command is explicit, local-only, process-scoped, and non-retained.

Home AI Cluster also has a separate local node and adapter health snapshot, but that
snapshot is configuration and direct observation data. It is not request history and
must not be treated as one.

## What “history” could mean

The roadmap phrase is broad. At least four different capabilities could be called
request history:

1. retaining the last few structured operator-command accounts;
2. retaining metadata for ordinary `/v1/chat` requests;
3. retaining metadata for both native and OpenAI-compatible request surfaces;
4. retaining a generalized lifecycle of selection, execution, fallback, and health
   events.

These are not equivalent.

The first is a narrow operator aid. The latter options require progressively more
ownership of request identity, concurrent writes, process boundaries, compatibility
edges, distributed behavior, retention, access control, and lifecycle semantics.

## Privacy boundary

A first request-history capability should retain no user or generated content.

It should not retain:

- prompt text;
- message arrays;
- generated response content;
- tool arguments or outputs;
- raw request or response payloads;
- raw exception messages;
- exception types or stack traces;
- runtime URLs or transport addresses;
- authorization values;
- private machine details.

Even prompt-free metadata can still reveal behavior. Capability names, selected node
ids, model names, failure categories, and timing information may disclose usage
patterns. Therefore “prompt-free” does not mean “privacy-neutral”.

A later RFC must explicitly decide every retained field rather than copying the full
actual-request account by default.

## Facts the repository can retain truthfully today

For the explicit local actual-request command, the repository can currently produce
and therefore potentially retain:

- whether the request succeeded or failed;
- requested capability;
- matched, selectable, excluded, and selected candidate families;
- selected node id when selection succeeded;
- routing outcome rule;
- routing failure reason when no candidate was selectable;
- successful result node id;
- successful adapter name;
- successful model name when provided by the adapter;
- one of the three accepted failed statuses;
- one accepted safe failure reason.

The architecture does not currently own:

- a stable request identifier;
- a timestamp or duration contract;
- a sequence number across processes;
- ordinary HTTP request-history interception;
- a shared lifecycle across native and compatibility processes;
- fallback-path attribution in the accepted actual-request command;
- remote-node failure history;
- a durable persistence contract;
- a stable access-control model for retained request facts.

## Candidate outcomes

### Candidate A: Documentation only

Document the privacy risks and current request-scoped facts without retaining
anything.

Advantages:

- no architectural or privacy risk;
- clarifies that prompt-free metadata remains sensitive;
- keeps Phase 7 honest.

Limitations:

- does not satisfy the roadmap history outcome;
- provides no way to inspect a previous request after its command exits.

Assessment:

Useful investigation work, but not a meaningful implementation increment.

### Candidate B: Explicit bounded in-memory history for the operator command

Add one purpose-specific process-local bounded store used only by explicit operator
request execution in a long-running owner process.

Advantages:

- small conceptual scope;
- no database;
- bounded retention;
- can retain only approved prompt-free metadata;
- can prove history before durable storage.

Limitations:

- the existing operator command is a short-lived process, so process-local memory
  disappears immediately;
- creating a long-running owner process solely for history would be a significant
  architectural change;
- it would not cover ordinary application requests.

Assessment:

Not recommended as stated. A short-lived CLI cannot provide useful in-memory history,
and introducing a daemon only to retain it is not a boring first step.

### Candidate C: Explicit bounded local file history for the operator command

Allow `home-ai-cluster-explain-request` to append a deliberately small prompt-free
record to one local file, with a separate command to inspect recent records.

Advantages:

- local-first;
- no database;
- survives process exit;
- easy to inspect and delete;
- can be bounded by a simple record count;
- isolates the first proof from ordinary HTTP contracts;
- uses boring line-oriented file storage.

Limitations:

- requires decisions about record identity, ordering, file location, permissions,
  concurrent writes, corruption handling, retention, and explicit activation;
- risks coupling one operator proof command to the first persistence contract;
- does not automatically represent ordinary cluster traffic;
- model and node attribution remain potentially sensitive metadata.

Assessment:

Plausible, but still larger than it first appears. It should not be implemented
without a focused RFC.

### Candidate D: Prompt-free history for the native application process

Have the ordinary native application retain bounded metadata for `/v1/chat`
requests and expose a local operator inspection command or endpoint.

Advantages:

- history describes ordinary application behavior rather than a proof command;
- one long-running process already exists;
- bounded in-memory history could avoid persistence initially;
- could advance the roadmap outcome directly.

Limitations:

- requires deciding whether request history is core orchestration responsibility,
  application-edge responsibility, or an outer operator concern;
- requires concurrent access and ordering semantics;
- requires a read surface;
- an HTTP history endpoint would expand the public contract and privacy surface;
- process restart loses in-memory history;
- it would not automatically include the separate OpenAI-compatible process.

Assessment:

Architecturally meaningful, but too many ownership decisions are unresolved for the
next immediate implementation.

### Candidate E: Shared history across native and OpenAI-compatible processes

Create a shared local history facility for both application processes.

Advantages:

- gives one user-facing history regardless of entry surface;
- aligns with the cluster abstraction.

Limitations:

- immediately introduces cross-process coordination or durable shared storage;
- requires common request identity and lifecycle ownership;
- risks introducing a database, event bus, tracing abstraction, or compatibility-led
  core design;
- broadens the first history step beyond the current evidence.

Assessment:

Deferred.

### Candidate F: General request lifecycle or event log

Represent selection, execution, fallback, failure, and result as retained events.

Advantages:

- could later support debugging, metrics, dashboards, and distributed reasoning.

Limitations:

- is exactly the premature observability abstraction the project has avoided;
- requires event vocabulary, ordering, identity, retention, schema evolution, and
  cross-process ownership;
- would turn a small history need into infrastructure.

Assessment:

Rejected for the first history increment.

## Key architectural decisions still required

A useful RFC cannot simply say “store recent requests”. It must decide:

1. Which execution surface owns the first history proof?
2. Is history opt-in or enabled by default?
3. Is retention in memory or in a local file?
4. If file-backed, where is the file located and who creates it?
5. What exact prompt-free fields are retained?
6. Are successful adapter and model names retained?
7. Is selected node id retained?
8. Is any timestamp necessary, and if so, what privacy cost is accepted?
9. Is a synthetic local sequence number necessary?
10. How many records are retained?
11. How are old records removed?
12. What happens on malformed or partially written data?
13. How are concurrent writers handled?
14. What command or local surface reads the history?
15. How is history explicitly cleared?
16. What file permissions or process-access boundary is required?
17. Does a history write failure affect the actual request result?
18. Is history best-effort or part of command success?

These are architectural decisions, not implementation details.

## Timestamp and identifier tension

A history without timestamps or identifiers can still be useful as an ordered list
of the most recent records. However:

- a timestamp helps an operator know when something happened;
- an identifier helps refer to a specific record;
- both create new stable metadata contracts;
- a timestamp reveals usage patterns;
- a globally meaningful identifier suggests lifecycle ownership not yet established.

A first proof could use file order alone and avoid identifiers. It could also omit
wall-clock time and describe records only as newest-to-oldest. This would be a very
small but limited history.

The investigation does not decide this question.

## Default-on versus explicit opt-in

The roadmap says “without prompt logging by default”, not necessarily “history on by
default”.

Privacy-first behavior favors one of these:

- history disabled unless explicitly enabled;
- a separate explicit operator command that records only its own invocation;
- a very small bounded history with an obvious clear operation and documented local
  storage.

Automatically retaining metadata for all ordinary requests should not be assumed.

## Write-failure semantics

History is secondary evidence. It should not silently change routing or execution.

A future RFC should strongly consider:

- request success or failure remains determined by request execution;
- inability to retain history does not trigger retry, reselection, or fallback;
- history-write failure is reported separately and safely;
- raw filesystem errors and paths are not leaked through ordinary request contracts.

Whether history-write failure should make an explicit recording command exit non-zero
remains open.

## Recommended next architectural question

The smallest useful question is:

> Should Home AI Cluster first prove prompt-free request history as an explicit,
> bounded, local, line-oriented record of actual-request operator accounts, with no
> database, no ordinary HTTP integration, no timestamps or request identifiers, and
> explicit inspection and clearing commands?

This candidate is intentionally narrow:

- local file rather than a database;
- explicit operator use rather than automatic interception;
- bounded records rather than indefinite retention;
- approved metadata projection rather than complete account copying;
- file order rather than a general lifecycle model;
- no cross-process or distributed coordination.

A later RFC should compare this against deferring history until the ordinary native
application can own a bounded in-memory view.

## Recommended boundaries for a later RFC

A later RFC should preserve:

- local-first and privacy-first operation;
- prompt and response content excluded from retained records;
- explicit small retained-field allowlist;
- bounded retention;
- no database;
- no dashboard;
- no metrics, tracing, or generic event abstraction;
- no changes to routing, fallback, or health semantics;
- no remote-node history;
- no OpenAI-compatible integration in the first proof;
- no public HTTP history endpoint in the first proof;
- no raw exception or private machine detail retention;
- safe behavior when history cannot be read or written;
- one obvious local clear operation;
- no claim that first history records form a complete request lifecycle.

## Deferred questions

The following remain deferred:

- automatic history for `/v1/chat`;
- history for `/v1/chat/completions`;
- shared history across processes;
- durable database-backed history;
- request ids;
- timestamps and durations;
- fallback-path records;
- remote-node records;
- history search and filtering;
- aggregate statistics;
- dashboards;
- metrics and tracing;
- retention configuration beyond one small fixed bound;
- schema migration infrastructure;
- multi-user access control.

## Conclusion

Home AI Cluster can now explain one actual request, expose structured failures, and
inspect local node and adapter health. The remaining Phase 7 gap is retaining a small
amount of trustworthy evidence after a request ends.

The difficult part is not writing records. It is deciding who owns history, what can
be retained safely, and how little persistence is enough.

The most boring plausible first proof is an explicit bounded local line-oriented
history for the operator request command, with a strict prompt-free allowlist and no
timestamps, request identifiers, database, HTTP endpoint, or cross-process sharing.

That direction is not yet accepted. It requires a focused RFC before implementation.
