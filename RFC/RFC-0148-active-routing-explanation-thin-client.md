# RFC-0148: Active Routing Explanation Thin Client

Status: Accepted

Date: 2026-10-06

Author: frian

## Summary

Home AI Cluster should provide one thin local operator command for the accepted and implemented RFC-0147 static-routing explanation carrier.

The command should be available through the canonical root CLI as:

```text
hac explain-active-routing
```

with the equivalent long-form root invocation:

```text
home-ai-cluster explain-active-routing
```

The command is a client of the already-running ordinary loopback process.

It sends exactly one bounded request to:

```text
POST http://127.0.0.1:25042/diagnostics/static-routing-explanation
```

It accepts only:

- one accepted HAC capability; and
- optional `--local-only`.

It validates one RFC-0147 response, writes one bounded JSON result to standard output on success, otherwise writes one stable safe error line to standard error, and exits.

The command does not:

- construct routing state;
- read retained Configuration;
- inspect topology;
- create local or remote candidates;
- run routing selection;
- probe runtimes or remotes;
- execute a business request;
- start or supervise HAC;
- discover processes;
- expose trusted-LAN or remote administration; or
- alter RFC-0027.

The historical standalone command:

```text
home-ai-cluster-explain-routing
```

remains unchanged and continues to explain only its explicitly constructed synthetic composition.

RFC-0148 therefore adds a distinct active-caller client rather than silently reinterpreting the RFC-0027 launcher.

## Context

RFC-0146 accepts one bounded semantic authority for static routing explanation of the effective ordinary caller composition.

RFC-0147 selects one bounded loopback carrier for that authority.

The implemented carrier is:

```text
POST /diagnostics/static-routing-explanation
```

on the ordinary loopback process.

Its request contains only:

- one accepted capability;
- Boolean `local_only`.

Every successful response contains:

- `capability`;
- `local_only`;
- `local_eligible`;
- ordered `eligible_remote_node_ids`;
- `remotes_excluded_by_local_only`;
- `initial_selection`.

The endpoint is deliberately:

- payload-free;
- non-effectful;
- loopback-only;
- absent from trusted-LAN;
- absent from receiver authority;
- absent from OpenAI compatibility;
- independent of retained Configuration;
- free from public no-selection reasons.

The carrier is already sufficient as a machine-readable HTTP contract.

However, direct operator use currently requires manual construction of:

- the fixed loopback URL;
- the HTTP method;
- the JSON request body;
- the accepted capability value;
- the `local_only` Boolean;
- HTTP error interpretation; and
- response validation.

RFC-0045 already establishes the relevant client pattern for an ordinary running process: one thin local command may remove manual transport construction while keeping the process as the sole authority for topology, routing, execution, and result truth.

### Historical RFC-0027 command

RFC-0027 accepts:

```text
home-ai-cluster-explain-routing
```

That command answers a different question.

It receives synthetic routing facts from its own invocation, including explicit local and declared-remote presence, constructs its own explanation-only composition, and applies the historical automatic selection semantics to that synthetic state.

Its lifecycle and authority are therefore:

```text
operator describes synthetic candidates
        |
        v
standalone finite process
        |
        v
synthetic routing explanation
```

RFC-0146 explicitly narrows that command's authority to the composition it constructs.

The modern RFC-0147 question is instead:

```text
already-running ordinary caller
        |
        v
active in-memory composition
        |
        v
RFC-0147 static routing explanation
```

These contracts differ in:

- lifecycle;
- inputs;
- authority;
- output;
- compatibility expectations.

The repository continues to install and test the RFC-0027 launcher, including its exact synthetic output behavior.

RFC-0148 must therefore not silently reuse that launcher name or reinterpret its meaning.

## Problem

RFC-0147 now provides the correct public process-owned carrier, but the normal interactive operator path is still raw HTTP.

That is acceptable as protocol access, but it leaves a small repeated transport task for a diagnostic intended for interactive operator use.

The client problem is narrow:

> Given one accepted capability and optional local-only intent, ask the already-running ordinary HAC process for its accepted RFC-0147 static routing explanation without making the operator construct HTTP manually.

The solution must not move any RFC-0146 or RFC-0147 authority into the command.

The command must remain a client.

It must not become:

- another router;
- another composition owner;
- a retained-configuration interpreter;
- a topology client;
- a runtime client;
- a fallback engine;
- a process manager;
- a generic diagnostics CLI.

## Goals

This RFC should:

- provide one thin local operator client for RFC-0147;
- use the canonical `hac` / `home-ai-cluster` root CLI;
- give the command a name semantically distinct from RFC-0027;
- require an already-running ordinary process;
- target only the established fixed loopback RFC-0147 endpoint;
- accept only the current RFC-0147 semantic inputs;
- validate the RFC-0147 success response before printing it;
- preserve the full bounded RFC-0147 semantic result;
- define stable stdout, stderr, and exit behavior;
- fail safely without leaking response bodies or private details;
- preserve RFC-0027 unchanged; and
- remain small enough to implement without new architecture.

## Non-goals

This RFC does not define or authorize:

- modification of `home-ai-cluster-explain-routing`;
- deprecation of RFC-0027;
- retirement of RFC-0027;
- aliasing RFC-0027 to RFC-0147;
- a synthetic mode in the new client;
- multiple explanation modes in one command;
- trusted-LAN diagnostics;
- remote diagnostics;
- receiver diagnostics;
- OpenAI-compatible diagnostics;
- browser UI;
- process startup;
- process discovery;
- configurable host or port;
- configuration files;
- environment-variable target configuration;
- retained Configuration loading;
- topology discovery;
- node selection;
- adapter selection;
- runtime or model selection;
- request execution;
- remote probing;
- health or readiness probing;
- retry;
- client-side fallback;
- polling;
- monitoring;
- history;
- persistence;
- interactive mode;
- a generic HTTP client;
- a generic diagnostics framework;
- a diagnostics registry;
- authentication;
- TLS management;
- dashboard;
- database;
- Docker;
- Kubernetes.

## Decision

### One distinct active-caller command

HAC will provide:

```text
hac explain-active-routing
```

The equivalent long-form root invocation is:

```text
home-ai-cluster explain-active-routing
```

This is one root-subcommand contract, not a new standalone historical-style executable.

RFC-0148 does not add:

```text
home-ai-cluster-explain-active-routing
```

as a separate installed script.

This keeps new operator functionality on the current canonical root CLI and avoids adding another legacy-style console-script surface.

The wording `active` is deliberate.

It distinguishes:

```text
explain-active-routing
    -> explain the already-running ordinary caller

home-ai-cluster-explain-routing
    -> explain an explicitly constructed synthetic composition
```

The new command must not accept an alias that silently collides with the historical RFC-0027 launcher semantics.

### Running ordinary process is a precondition

The command requires an already-running ordinary HAC process exposing RFC-0147 on the established loopback listener.

The command must not:

- start `hac local`;
- start `hac static-cluster`;
- construct a temporary application;
- load retained Configuration;
- infer a composition;
- inspect process tables;
- discover ports;
- search the network.

If no ordinary process is available at the fixed target, the command fails with its bounded client-unavailable behavior.

This lifecycle difference from RFC-0027 is part of the public contract.

### Fixed target

The command sends exactly one request to:

```text
POST http://127.0.0.1:25042/diagnostics/static-routing-explanation
```

The target is fixed.

The command must not accept:

- host;
- port;
- base URL;
- remote node;
- receiver address;
- trusted-LAN address;
- environment-variable target;
- configuration-file target.

This follows the established ordinary loopback thin-client precedent.

A future need for configurable or remote diagnostics requires separate architecture.

### Capability input

The command must accept exactly one required capability option:

```text
--capability <CAPABILITY>
```

The value must belong to the accepted HAC capability vocabulary.

The client may validate the accepted vocabulary locally for immediate operator feedback.

That local validation does not become routing authority.

The running RFC-0147 process remains authoritative for the explanation.

The command must not derive accepted capabilities from:

- adapters;
- runtimes;
- models;
- remote declarations;
- retained Configuration.

### Local-only input

The command accepts one optional flag:

```text
--local-only
```

Absence means:

```text
local_only = false
```

Presence means:

```text
local_only = true
```

The command exposes no generic constraint map and no arbitrary request fields.

A future routing constraint requires separate accepted architecture before entering this command contract.

### Request contract

One invocation constructs exactly one RFC-0147 request equivalent to:

```json
{
  "capability": "<accepted capability>",
  "local_only": false
}
```

or, with `--local-only`:

```json
{
  "capability": "<accepted capability>",
  "local_only": true
}
```

The command must not send:

- candidate declarations;
- local-presence flags;
- remote-presence flags;
- node IDs;
- URLs;
- prompts;
- source text;
- labels;
- code instructions;
- image instructions;
- workspace content;
- execution controls.

### One request only

One invocation must:

1. parse and validate its bounded local arguments;
2. construct one RFC-0147 request;
3. perform one HTTP request;
4. validate one success response or map one failure;
5. write one result or one safe error;
6. exit.

The command must not:

- retry;
- poll;
- perform client-side fallback;
- make a status request first;
- probe health first;
- discover capabilities first;
- contact multiple endpoints.

### Success validation

HTTP success alone is insufficient.

Before writing output, the command must validate that the response conforms to the implemented RFC-0147 public success contract.

The validated semantic categories are:

- `capability`;
- `local_only`;
- `local_eligible`;
- ordered `eligible_remote_node_ids`;
- `remotes_excluded_by_local_only`;
- `initial_selection`.

`initial_selection` must be one of:

```text
null
```

```json
{"kind":"local"}
```

or:

```json
{"kind":"declared_remote","node_id":"<caller-owned node ID>"}
```

The client must reject malformed or semantically invalid successful responses rather than printing arbitrary server JSON.

Implementation may reuse an existing authoritative response model if one exists or introduce the smallest client-side validation model that mirrors the accepted public HTTP contract.

It must not import or expose internal routing objects as the client contract.

### Success output

On one valid RFC-0147 success, the command must write exactly one compact JSON object to standard output representing the complete validated RFC-0147 response.

Standard error must remain empty.

Exit status must be:

```text
0
```

The command must preserve all six mandatory RFC-0147 semantic categories.

It must not:

- pretty-print by default;
- add prose;
- add colors;
- add timestamps;
- add client metadata;
- add a wrapper object;
- omit false/empty/null categories;
- expose internal no-selection reasons.

The client must not reinterpret the response into synthetic RFC-0027 output.

### Failure and exit contract

On failure, standard output must be empty.

Standard error must contain exactly one stable safe category line.

The first contract is:

| Condition | Standard error | Exit |
| --- | --- | --- |
| Invalid local CLI input | `error: invalid routing explanation input` | 2 |
| Connection failure or timeout | `error: ordinary cluster unavailable` | 1 |
| HTTP 422 diagnostic rejection | `error: routing explanation rejected` | 1 |
| HTTP 503 explanation unavailable | `error: routing explanation unavailable` | 1 |
| Unexpected HTTP status | `error: routing explanation failed` | 1 |
| Malformed or invalid success response | `error: invalid routing explanation response` | 1 |
| Other client failure | `error: routing explanation failed` | 1 |

The command must not print:

- raw exceptions;
- tracebacks;
- raw HTTP response bodies;
- URLs other than documentation of the fixed public target;
- transport addresses;
- private node addresses;
- retained configuration;
- adapter names;
- runtime names;
- model names;
- credentials;
- internal no-selection reasons.

Remote node IDs contained in a valid successful RFC-0147 result are allowed because RFC-0147 already accepts them as part of the public diagnostic contract.

### Timeout

The command must use one finite implementation-owned request timeout.

Timeout maps to:

```text
error: ordinary cluster unavailable
```

The command must not expose:

- a timeout flag;
- timeout environment variable;
- retry count;
- retry delay;
- fallback behavior.

The exact numeric timeout is an implementation detail.

### No routing authority in the client

The client must not determine:

- local eligibility;
- remote eligibility;
- remote ordering;
- `local_only` exclusion;
- initial selection;
- no-selection reasons.

Those facts belong to the running process.

The client only:

- supplies capability;
- supplies `local_only`;
- validates the returned public representation.

The command must not import core routing helpers in order to recompute the answer.

Local capability-name validation is input validation, not routing computation.

### No retained Configuration

The command must not load retained Configuration for any purpose.

In particular, it must not use retained state to:

- determine the process target;
- infer local eligibility;
- infer remote nodes;
- format a synthetic explanation;
- decide whether the process should exist.

The ordinary running process remains the only owner of active caller truth.

### No process discovery

The client targets the fixed ordinary loopback contract.

It must not discover:

- running HAC PIDs;
- listening ports;
- LAN listeners;
- receiver listeners;
- compatibility listeners;
- remote nodes.

The absence of the expected process is a normal bounded client failure.

### No remote authority

RFC-0148 is local operator access only.

The command must not:

- accept a remote host;
- target trusted-LAN;
- target a receiver;
- target remote RFC-0147 carriers;
- tunnel requests;
- forward diagnostics through HAC-to-HAC transport.

This RFC creates no remote diagnostic protocol.

### Relationship to RFC-0027

RFC-0027 remains unchanged.

The existing installed launcher:

```text
home-ai-cluster-explain-routing
```

continues to mean:

> Explain the synthetic routing composition explicitly constructed by this invocation.

RFC-0148 does not:

- change that launcher's arguments;
- change its output;
- change its exit behavior;
- make it contact a running ordinary process;
- deprecate it;
- rename it;
- alias it;
- make it a mode of `hac explain-active-routing`.

Conversely, `hac explain-active-routing` must not accept RFC-0027 synthetic candidate inputs.

The two commands intentionally coexist because they answer different questions.

A future decision may reconsider RFC-0027 compatibility, naming, deprecation, or retirement.

That decision is outside RFC-0148.

### Relationship to RFC-0147

RFC-0147 remains authoritative for:

- target process ownership;
- request semantics;
- response semantics;
- privacy boundary;
- static routing truth.

RFC-0148 does not extend the endpoint.

It merely consumes it.

If RFC-0147 returns a valid successful response, the CLI presents that same bounded semantic response.

If the server returns malformed data, the CLI fails safely rather than inventing routing truth.

### Relationship to RFC-0145

RFC-0145 remains actual-request lifecycle explanation.

`hac explain-active-routing` is non-effectful and pre-execution.

It must not execute an actual request to obtain richer explanation.

It must not be presented as evidence of:

- execution permission;
- runtime engagement;
- consumed fallback;
- final node;
- success;
- terminal failure.

### Relationship to RFC-0045

RFC-0045 is the thin-client precedent.

The same process/client ownership split applies:

```text
thin local CLI
    |
    v
one bounded loopback HTTP exchange
    |
    v
already-running ordinary HAC process
```

RFC-0148 does not create a generic abstraction shared by all thin clients.

Small implementation reuse is allowed when it does not merge public contracts or create a generic client framework.

### Canonical CLI placement

The command belongs to the current root CLI's finite-command set.

It should appear in root help as a bounded finite operator command.

RFC-0148 intentionally does not add another `[project.scripts]` historical-style executable because:

- `hac` / `home-ai-cluster` is the current canonical command facade;
- RFC-0027 already occupies the historical generic standalone launcher name;
- another standalone alias would increase compatibility surface without adding capability.

The root aliases:

```text
hac
home-ai-cluster
```

therefore expose the same subcommand behavior.

### Documentation

The implementation must document:

- the active-process prerequisite;
- the fixed loopback nature;
- accepted capability input;
- optional `--local-only`;
- one-shot behavior;
- output as RFC-0147 JSON;
- bounded failure categories;
- distinction from `home-ai-cluster-explain-routing`.

Documentation must not imply:

- remote use;
- trusted-LAN use;
- process startup;
- retained Configuration interpretation;
- execution prediction;
- RFC-0027 deprecation.

## Privacy and security

The command submits no business payload.

Its request contains only:

- accepted capability name;
- Boolean `local_only`.

The success response contains only facts already accepted by RFC-0147.

The command must not persist request or response data.

It must not write history.

It must not log private state.

The surrounding shell or terminal may retain command invocation and output outside HAC's control.

Because the client uses fixed loopback HTTP, RFC-0148 introduces no new network trust boundary.

Loopback access must not be generalized into remote administration by implementation convenience.

## Compatibility

RFC-0148 is additive.

Existing commands remain unchanged.

In particular:

- `home-ai-cluster-explain-routing` remains unchanged;
- `home-ai-cluster-explain-request` remains unchanged;
- existing `hac` finite commands remain unchanged;
- RFC-0147 HTTP behavior remains unchanged;
- RFC-0144 browser projection remains unchanged;
- trusted-LAN remains unchanged;
- receiver authority remains unchanged;
- OpenAI compatibility remains unchanged.

The new root subcommand name becomes a public command contract once accepted and implemented.

Its argument names, stdout/stderr contract, and exit semantics therefore require explicit compatibility treatment in future changes.

## Rationale

The RFC-0147 endpoint establishes the correct process-owned authority, but direct curl usage leaves operators to repeatedly construct transport details.

A thin root-CLI client removes that friction without moving authority.

A distinct active-caller name is necessary because the historical RFC-0027 launcher has materially different semantics and remains a tested installed compatibility surface.

Changing the RFC-0027 launcher would combine:

- a standalone synthetic lifecycle;
- an already-running-process lifecycle;
- different input models;
- different output models;
- different authority meanings.

Explicit modes could technically preserve both, but would add avoidable complexity.

Two honest surfaces are simpler:

```text
home-ai-cluster-explain-routing
    synthetic historical explanation

hac explain-active-routing
    active ordinary caller explanation
```

Keeping the new command only on the canonical root CLI also avoids growing the legacy standalone script namespace.

## Alternatives considered

### No CLI

Rejected for the first operator workflow.

The HTTP carrier remains fully supported and machine-readable, but interactive diagnosis otherwise requires manual method, URL, JSON, and error construction.

The project already accepts the thin-client pattern for analogous ordinary-process access.

### Reuse `home-ai-cluster-explain-routing`

Rejected.

That would silently change:

- lifecycle;
- inputs;
- authority;
- output;
- compatibility expectations.

Keeping a name while changing the question it answers would be misleading.

### Add explicit synthetic/active modes to RFC-0027 launcher

Rejected as larger than necessary.

It would combine two distinct authority models in one command and require mode-specific argument and output behavior.

### Retire RFC-0027 first

Rejected.

The modern client does not require retirement of the historical synthetic command.

Deprecation or removal would be a separate compatibility decision.

### Add a new standalone `home-ai-cluster-explain-active-routing` script

Rejected.

The canonical root CLI already provides the appropriate modern extension point.

Adding another installed standalone script would increase compatibility surface without increasing capability.

### Configurable target

Rejected.

The accepted need is local access to the established ordinary loopback process.

Configurable targets would introduce process discovery and remote/admin semantics not justified here.

### Human-formatted output

Rejected for the first contract.

Compact JSON preserves the existing RFC-0147 semantic contract exactly and is useful both interactively and for shell tooling.

A future demonstrated need for human formatting can be evaluated separately.

### Client-side interpretation of routing facts

Rejected.

The process owns routing truth.

The client must not transform ordered candidates and selection facts into a new explanation policy.

## Implementation boundaries

A future implementation may decide:

- module/function names;
- internal request/response validation model placement;
- exact numeric timeout;
- exact `httpx` call structure;
- whether a very small existing one-shot HTTP helper can be reused safely;
- test organization;
- command help wording consistent with this RFC.

Implementation must not decide without further architecture:

- RFC-0027 deprecation or migration;
- standalone aliases;
- additional routing constraints;
- alternative output modes;
- configurable target;
- remote diagnostics;
- trusted-LAN diagnostics;
- retries;
- process discovery;
- generic client abstractions.

If implementation cannot add this command without introducing one of those decisions, it should stop and return to architecture.

## Proof requirements

A future implementation should prove at least:

1. `hac explain-active-routing --capability chat` makes exactly one request to the fixed RFC-0147 endpoint;
2. absence of `--local-only` sends `local_only=false`;
3. presence of `--local-only` sends `local_only=true`;
4. accepted capability validation is bounded;
5. invalid local input emits only the accepted local-input error and exit 2;
6. connection failure and timeout emit only the bounded unavailable error;
7. RFC-0147 HTTP 422 maps to the accepted rejection error;
8. RFC-0147 HTTP 503 maps to the accepted unavailable-explanation error;
9. unexpected HTTP status is safely normalized;
10. malformed success data is rejected;
11. one valid success response is emitted as one compact JSON object containing all six RFC-0147 semantic categories;
12. false, empty, and null categories remain present;
13. no internal no-selection reason is emitted;
14. no retained Configuration is loaded;
15. no routing helper is invoked by the client to recompute the explanation;
16. no process is started;
17. no retry or second request occurs;
18. no remote/trusted-LAN target option exists;
19. root `hac` and `home-ai-cluster` expose the same subcommand behavior;
20. `home-ai-cluster-explain-routing` behavior and exact historical tests remain unchanged.

## Open questions

The following remain intentionally deferred:

- Should RFC-0027 ever be deprecated, renamed, or retired?
- Is a human-oriented rendering ever useful in addition to compact JSON?
- Will a future accepted routing constraint need CLI exposure?
- Is there ever a justified remote or trusted-LAN diagnostic client?
- Is there later value in a shared internal one-shot HTTP helper without creating a generic client framework?

These questions do not affect the bounded thin-client decision in this RFC.

## Decision

Accepted.
