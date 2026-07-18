# Human-Readable Operator Output Investigation

Status: Investigation

This document investigates presentation of existing operator command results in
an interactive terminal. It records current repository evidence and questions
for a later decision; it is not an output contract, proposal, implementation
plan, RFC, or roadmap change.

## Context and question

One real daily operator exercise used `home-ai-cluster-preflight`,
`home-ai-cluster-health`, and `home-ai-cluster-status`. Those finite commands
returned useful compact JSON, but the JSON was difficult to scan during normal
interactive operation. The canonical workflow likewise places preflight and
status before starting an ordinary static-cluster caller, and identifies health
as a distinct local observation.

The question is therefore narrow:

> What is the smallest coherent way to make existing finite operator results
> easier to read in a terminal while preserving explicit, stable machine use?

This investigation considers only projections of results already produced. It
does not add observations, change any result vocabulary, alter routing or
health, or assume that every installed command needs one presentation policy.

## Evidence reviewed

The inventory is based on the current `main` branch's `pyproject.toml`, command
implementations, result models, and command tests. It also considered the
canonical operator workflow and the daily-workflow investigation and evidence
records. Relevant accepted RFCs are RFC-0027, RFC-0032 through RFC-0039, and
RFC-0040 through RFC-0047, together with the earlier accepted routing,
health, result-attribution, remote-declaration, and compatibility boundaries
they reuse.

The following distinction matters throughout this document:

- Repository tests directly parse JSON and, for many commands, assert the exact
  raw stdout string including compact separators and one trailing newline.
- The repository contains no evidence of an external script consumer. It would
  be unsupported to claim that one exists; nevertheless, an installed command's
  current stdout is a compatibility-sensitive interface for possible operators
  and for the repository's own tests.

## Installed command inventory and scope

`pyproject.toml` installs fifteen commands. The eight finite commands below are
the detailed investigation set. They do not all have the same purpose or
output-risk profile.

| Command | Classification | Scope for this investigation |
| --- | --- | --- |
| `home-ai-cluster-preflight` | finite, read-only declaration/coherence inspection | In scope. It is part of the canonical operator path and has repeated node and issue data. |
| `home-ai-cluster-health` | finite, read-only local snapshot | In scope. It is a one-time local observation with nested declared and observed data. |
| `home-ai-cluster-status` | finite, read-only bounded cluster observation | In scope. It is part of the canonical path and has ordered repeated node data. |
| `home-ai-cluster-chat` | finite one-shot request client | In scope for analysis, but not automatically the same presentation as inspection. It displays a real response. |
| `home-ai-cluster-history` | finite, read-only local-history inspection | In scope for analysis. It returns repeated privacy-filtered records. |
| `home-ai-cluster-clear-history` | finite one-shot mutation | In scope for inventory only. Its small acknowledgement is unlike a multi-field inspection result. |
| `home-ai-cluster-explain-routing` | finite, read-only synthetic routing explanation | In scope for analysis. It has a stable structured explanation contract. |
| `home-ai-cluster-explain-request` | finite one-shot request, optionally records history | In scope for analysis, but its nested account and explicit response content require different privacy and compatibility care. |
| `home-ai-cluster-static-proof` | long-running, proof-scoped HTTP process | Out of a shared finite-result proposal. It starts Uvicorn rather than returning one result. |
| `home-ai-cluster-automatic-proof` | long-running, proof-scoped HTTP process | Out of scope for the same reason; it is a historical proof entry point. |
| `home-ai-cluster-fallback-proof` | long-running, proof-scoped HTTP process | Out of scope; it proves fallback behavior rather than completing one inspection. |
| `home-ai-cluster-phase-12-heterogeneous-receiver` | long-running, proof-scoped receiving process | Out of scope; its arguments and process are specific to the Phase 12 proof. |
| `home-ai-cluster-local` | long-running ordinary local application process | Out of a finite-result proposal. Startup/server logging is not a completed operator result. |
| `home-ai-cluster-static-cluster` | long-running ordinary static-cluster application process | Out of a finite-result proposal. It owns an application lifecycle and accepts topology input. |
| `home-ai-cluster-openai-compatibility` | long-running compatibility application process | Out of scope. It serves a separate compatibility HTTP contract and is not a terminal-result command. |

The excluded commands still have normal argparse diagnostics and server-runner
output, but treating those as a shared result renderer would mix startup,
Uvicorn logging, proof behavior, and compatibility behavior with finite command
presentation. This investigation has no evidence for doing that.

## Detailed finite command contracts

### `home-ai-cluster-preflight`

- **Purpose and duration:** one read-only static coherence inspection, finite.
- **Stdout:** one compact JSON report with `status`, `operating_mode`, ordered
  `nodes`, `registered_adapters`, and `issues`.
- **Stderr and exit status:** argparse/declaration-input failures use argparse
  stderr and non-zero status. A safe construction failure writes
  `error: unable to construct static preflight report` to stderr and exits 1.
  A coherent report exits 0; an incoherent report is still written to stdout
  and then exits non-zero.
- **Compact JSON and structural shape:** yes. Nodes and issues are repeated
  nested objects; node capabilities and declared adapters are arrays.
- **Compatibility evidence:** tests assert compact separators, a newline, an
  empty stderr on projected reports, and the stdout report even for
  incoherence. The repository proves test consumption, not external scripts.
- **Human-use and default-change sensitivity:** a readable projection could
  materially improve a multi-node or issue-bearing report. Replacing default
  stdout would be compatibility-sensitive because RFC-0036 and tests make the
  structured report and its output/exit boundary observable.

### `home-ai-cluster-health`

- **Purpose and duration:** one finite, read-only local node declaration and
  direct adapter-health snapshot.
- **Stdout:** one compact JSON object containing `nodes`. Each node contains
  `node_id`, `name`, nested `declared` facts, and repeated
  `adapter_observations`.
- **Stderr and exit status:** a completed snapshot exits 0 with no stderr. A
  whole-snapshot construction failure writes
  `error: unable to construct local health snapshot` to stderr and exits 1;
  the command does not expose raw failure details.
- **Compact JSON and structural shape:** yes. The result is nested and includes
  repeated adapter observations, though ordinary current composition is local.
- **Compatibility evidence:** tests assert exactly one compact JSON object and
  one trailing newline, plus safe empty-stdout failure behavior. RFC-0033
  defines the snapshot's declared-versus-observed separation. No external
  consumer is demonstrated in the repository.
- **Human-use and default-change sensitivity:** the declared and observed
  sections are difficult to scan in compact JSON, so a projection could be
  materially useful. A default change is compatibility-sensitive because the
  current structured stdout is tested and RFC-defined.

### `home-ai-cluster-status`

- **Purpose and duration:** one finite, read-only, bounded live observation of
  the validated static cluster.
- **Stdout:** one compact JSON `ClusterStatusResult` with
  `declaration_status` and ordered `nodes`; each node has `node_id`,
  `application_status`, and `runtime_status`.
- **Stderr and exit status:** required declaration and invalid composition
  arguments use argparse stderr and non-zero status. An unexpected collection
  failure writes `error: unable to construct cluster status result` to stderr
  and exits 1. Normalized unavailable, unreachable, request-failed, invalid
  response, or unknown node observations remain successful structured status
  results with exit 0.
- **Compact JSON and structural shape:** yes. The ordered node list is repeated
  data, and tests preserve the declaration's remote-node order.
- **Compatibility evidence:** tests parse the output, assert its exact compact
  serialization and newline, and assert status order. RFC-0041 and RFC-0044
  define a privacy-safe engine-independent result without runtime URLs or
  model identity. No external consumer is evidenced.
- **Human-use and default-change sensitivity:** this is the strongest directly
  observed friction: a status table makes repeated node states easier to scan.
  Replacing default JSON is compatibility-sensitive for the same RFC and test
  reasons.

### `home-ai-cluster-chat`

- **Purpose and duration:** one finite request to an already-running ordinary
  loopback cluster; it has the side effect of sending the supplied request.
- **Stdout:** on success, one compact JSON `ClusterResult` with `content`,
  `adapter`, `model`, and `node_id`.
- **Stderr and exit status:** invalid input prints the stable safe
  `error: invalid request input` and exits 2. Connection, HTTP, and invalid
  response failures print one safe stderr message, produce no stdout, and exit
  1. A successful result exits 0.
- **Compact JSON and structural shape:** yes. It is a flat four-field object,
  but `content` is an operator-visible generated response rather than generic
  status metadata.
- **Compatibility evidence:** tests parse success JSON, check one newline, and
  assert exact privacy-safe failure messages. RFC-0045 preserves the native
  result fields. No repository evidence identifies downstream scripts.
- **Human-use and default-change sensitivity:** readable attribution around a
  response may help an operator, but response content already needs direct
  display and may be copied or redirected. Default replacement is therefore
  compatibility-sensitive and should not be assumed to match inspection output.

### `home-ai-cluster-history`

- **Purpose and duration:** one finite, read-only inspection of bounded,
  prompt-free local request records.
- **Stdout:** a compact JSON array of valid records, newest first. Each record
  contains only `status`, `requested_capability`,
  `selected_candidate_family`, `outcome_rule`, and `failure_status`.
- **Stderr and exit status:** a missing or wholly invalid history yields `[]`
  on stdout and exits 0. A read failure writes
  `error: unable to read request history` to stderr and exits 1. Unsupported
  options use argparse stderr and a non-zero status.
- **Compact JSON and structural shape:** yes. It is repeated structured data
  and may be empty; RFC-0035 bounds retention to fifty privacy-filtered records.
- **Compatibility evidence:** tests parse the array, assert compact output and
  newline, and assert safe error separation. The repository does not prove an
  external consumer.
- **Human-use and default-change sensitivity:** a list projection could make
  repeated records easier to scan, but it must not add timestamps, identifiers,
  prompt text, results, node identity, adapter, or model information. A default
  change is compatibility-sensitive because the current array is tested.

### `home-ai-cluster-clear-history`

- **Purpose and duration:** a finite explicit local-history deletion operation,
  not a read-only inspection.
- **Stdout:** the fixed compact JSON acknowledgement `{"cleared":true}`.
- **Stderr and exit status:** success exits 0 with no stderr. A clear failure
  writes `error: unable to clear request history` to stderr and exits 1;
  unsupported options use argparse stderr and a non-zero status.
- **Compact JSON and structural shape:** yes, but it is one flat acknowledgement
  with no nested or repeated data.
- **Compatibility evidence:** tests assert the exact acknowledgement on both an
  existing and already-missing state and safe empty stdout on failure. No
  external consumer is known from repository evidence.
- **Human-use and default-change sensitivity:** a human phrase would provide
  little material improvement over the existing acknowledgement. Replacing it
  would nevertheless be compatibility-sensitive; a future scope need not force
  it into a shared renderer merely for uniformity.

### `home-ai-cluster-explain-routing`

- **Purpose and duration:** a finite, read-only explanation of one synthetic
  routing decision; it does not execute a local adapter or remote transport.
- **Stdout:** one JSON object with the eight stable routing fields:
  `requested_capability`, matched/selectable/excluded candidate-family arrays,
  selected family and node, `outcome_rule`, and `failure_reason`.
- **Stderr and exit status:** invalid invocation uses argparse stderr and
  non-zero status. An evaluation failure writes a diagnostic to stderr and
  exits 1. A valid no-selection result remains data on stdout and exits 0.
- **Compact JSON and structural shape:** JSON is emitted, but not compact JSON:
  this implementation calls default `json.dumps`, and tests assert that exact
  single-line representation plus newline. It has repeated candidate-family
  arrays but no result content.
- **Compatibility evidence:** RFC-0027 defines exactly one structured stdout
  object, all eight fields, stdout/stderr separation, and the successful
  no-selection exit boundary; tests parse and compare it. No external consumer
  is proven.
- **Human-use and default-change sensitivity:** named routing facts may benefit
  from a projection, especially where arrays are empty, but the established
  structured explanation is a particularly explicit contract. A default change
  is compatibility-sensitive.

### `home-ai-cluster-explain-request`

- **Purpose and duration:** one finite actual routed request account. It may
  execute a request and, only with `--record-history`, write the approved local
  history record.
- **Stdout:** one compact JSON account with `status`, nested `routing`, a
  `result` object or `null`, and a `failure` object or `null`.
- **Stderr and exit status:** argparse input failures are non-zero with stderr.
  Internal account construction failure uses the safe
  `error: unable to construct actual request account` stderr message and exits
  1. Optional history-recording failure emits the safe warning
  `warning: unable to record request history` but preserves the account. A
  succeeded account exits 0; a failed account is still written to stdout then
  exits 1.
- **Compact JSON and structural shape:** yes. It is nested and contains routing
  arrays, a result that can include response `content`, and a failure section.
- **Compatibility evidence:** RFC-0032 and RFC-0034 establish the actual
  account/failure boundary; tests assert compact serialization, newline,
  stdout/stderr separation, and exit behavior for both account states. No
  external consumer is demonstrated.
- **Human-use and default-change sensitivity:** a readable account may improve
  troubleshooting, but its direct result content and side effects distinguish it
  from read-only inspections. Replacing default JSON is compatibility-sensitive
  and must retain the safe failure/history-warning boundary.

## Privacy-safe current output shapes

These synthetic examples show current result shapes only. They contain no real
addresses, paths, prompts, responses, hostnames, usernames, process IDs, or
logs.

```json
{"status":"coherent","operating_mode":"static-multi-node","nodes":[{"node_id":"local","capabilities":["chat"],"declared_adapters":["ollama"]},{"node_id":"receiver","capabilities":["chat"],"declared_adapters":["remote-http"]}],"registered_adapters":["ollama"],"issues":[]}
```

```json
{"nodes":[{"node_id":"local","name":"Local node","declared":{"availability":"available","healthy":true,"reason":null,"capabilities":["chat"],"adapters":["ollama"]},"adapter_observations":[{"adapter":"ollama","status":"unavailable","reason":"runtime unavailable"}]}]}
```

```json
{"declaration_status":"coherent","nodes":[{"node_id":"local","application_status":"local","runtime_status":"unavailable"},{"node_id":"receiver","application_status":"reachable","runtime_status":"available"}]}
```

```json
{"content":"<SYNTHETIC_RESPONSE_CONTENT>","adapter":"test-adapter","model":null,"node_id":"local"}
```

```json
[{"status":"failed","requested_capability":"chat","selected_candidate_family":null,"outcome_rule":"no-selectable-candidate","failure_status":"no-selectable-candidate"}]
```

```json
{"cleared":true}
```

```json
{"requested_capability":"chat","matched_candidate_families":["local"],"selectable_candidate_families":["local"],"excluded_candidate_families":[],"selected_candidate_family":"local","selected_node_id":"local","outcome_rule":"local-precedence","failure_reason":null}
```

```json
{"status":"failed","routing":{"requested_capability":"chat","matched_candidate_families":[],"selectable_candidate_families":[],"excluded_candidate_families":[],"selected_candidate_family":null,"selected_node_id":null,"outcome_rule":"no-selectable-candidate","failure_reason":"no-selectable-candidate"},"result":null,"failure":{"status":"no-selectable-candidate","reason":"no selectable routing candidate"}}
```

## Illustrative human-readable projections

These are non-normative presentations of fields that already exist. They do not
add observations, remediation, colors, icons, timestamps, or progress behavior.

**Illustrative only — not a decision**

```text
Cluster declaration: coherent

NODE      APPLICATION   RUNTIME
local     local         unavailable
receiver  reachable     available
```

**Illustrative only — not a decision**

```text
Preflight: coherent
Mode: static-multi-node

NODE      CAPABILITIES   ADAPTERS
local     chat           ollama
receiver  chat           remote-http

Issues: none
```

**Illustrative only — not a decision**

```text
Local health

Node: local
Declared availability: available
Declared healthy: true
Capabilities: chat
Adapters: ollama

ADAPTER   STATUS        REASON
ollama    unavailable   runtime unavailable
```

The health example shows only the current snapshot's declared facts and adapter
observations. In particular, it does not infer reachability, future routability,
remediation, timestamps, or continuous monitoring.

## Options to investigate, without selection

### Option A — human-readable default with explicit JSON

Conceptually, `command` would use a terminal-oriented projection and an explicit
machine option such as `command --json` would retain JSON. This offers the most
direct improvement to the ordinary operator path and makes the data format
discoverable as an opt-in. It also changes the current default stdout for every
affected command, so existing shell use, exact-output tests, examples, and any
unobserved external parsing would need migration consideration.

For this option, a later proposal would need to say whether explicit JSON means
the current exact fields, vocabulary, ordering, compactness, and newline—not
merely JSON with approximately equivalent information. It would also need to
preserve stdout as data-only and leave diagnostics on stderr. The compatibility
cost is highest where an RFC already calls stdout JSON structured data.

### Option B — JSON default with explicit human format

Conceptually, `command --human` would select a readable projection while no
option preserves today's output. This has the smallest default compatibility
impact and could preserve current tests as the no-option path. It gives a weaker
improvement to the canonical daily workflow because operators who run the
documented commands without extra knowledge continue to see compact JSON.

Discoverability would need documentation, help text, and tests. The flag name
is illustrative only: this investigation does not choose `--human` or imply
that every command deserves the same option.

### Option C — explicit format selection

Conceptually, `--format human` and `--format json` make the choice visible and
could support argument validation consistently. They are extensible, but that
does not establish that more than two formats are justified. A general format
architecture risks being larger than this observed friction.

It would need an explicit default, invalid-value behavior, compatibility
decision, and command-by-command applicability. The smallest boring version
could remain a closed two-value choice, reuse existing JSON serialization, and
avoid a generic presentation framework; none of that is selected here.

### Option D — TTY-dependent behavior

This could emit human output on a terminal and JSON when piped or redirected.
It reduces typing but makes output implicit: capturing a command, running it
under a test harness, or changing shell redirection can change representation.
That complicates testability and can vary by shell and platform. It may also
surprise an operator who saves output and gets a different format.

The repository favors explicit, boring, understandable operator boundaries.
There is no evidence here that TTY detection is needed, so it should not be
selected merely because other CLIs use it.

### Option E — separate commands

Separate names such as `home-ai-cluster-status-json` would preserve existing
commands but proliferate installed surfaces and split documentation and help.
They make the relationship between one result and two presentations less
discoverable, especially across the eight finite commands. This option avoids a
flag parser change but does not avoid a compatibility contract for the new
command.

### Option F — documentation-only `jq`

Documented `jq` filters offer immediate utility with no project code, no output
contract change, and no new CLI surface. They add an external dependency,
expose raw technical structure, and cannot supply semantic terminal wording
without maintaining command-specific filters. They could be a temporary
workaround, but the observed status/preflight friction is not automatically
solved by merely exposing a JSON filter.

## Compatibility boundary

Current compatibility-sensitive properties differ slightly by command, but the
following are directly evidenced by source, accepted RFCs, and tests:

- field names, nesting, `null` values, enum/value vocabulary, and arrays are
  structured output contracts for the relevant commands;
- status node order follows local-first plus declaration order, and preflight
  projects node and issue order;
- preflight, health, status, chat, history, clear-history, and actual-request
  explanation use compact JSON separators; routing explanation currently does
  not, and its tests assert its default `json.dumps` representation;
- finite JSON outputs terminate with one newline in the current implementations
  and relevant tests;
- successful structured data is written to stdout, while safe diagnostic and
  argument failures are written to stderr;
- some valid domain failures remain stdout data with a non-zero status
  (`preflight` incoherence and failed actual-request accounts), whereas valid
  routing no-selection is a successful explanation with exit 0;
- tests assert raw output, JSON parseability, stdout/stderr separation, safe
  errors, and exit statuses; and
- the repository contains no evidence about downstream scripts beyond those
  tests, so compatibility uncertainty outside the repository remains explicit.

A future implementation must not conflate a human-success projection with a
machine-readable error protocol. Existing argparse usage failures, stable
privacy-safe stderr messages, non-zero exits, no raw exception exposure, and
success-data-on-stdout behavior are established boundaries. Whether structured
machine-readable errors are desirable is not answered by this investigation and
should remain unchanged absent a separately supported decision.

## Shared presentation boundary

The evidence supports considering, but does not require, a small presentation
boundary. Command-specific formatting functions are the baseline: they can
project existing result data while keeping domain models independent and leaving
the current JSON serialization path intact. A small shared output-format enum
or protocol could become justified only if several selected commands truly need
the same explicit selection and validation behavior.

One universal renderer is not established. Preflight and status have naturally
tabular repeated nodes; health has nested declared-versus-observed facts;
history is a bounded list; clear-history is one acknowledgement; chat and
actual-request explanation can contain operator-requested response content.
Introducing a generic formatting framework before deciding the command scope
would be premature abstraction.

## Testing implications for a future proposal

No tests are added by this investigation. A later implementation should retain
or add focused coverage for:

- default output and any explicit machine-readable output;
- exact field and value-vocabulary preservation for JSON;
- node ordering, empty issue lists, multiple nodes, unavailable and normalized
  failure states;
- nested routing/account and bounded history cases where included;
- stdout versus stderr separation and all existing exit-status categories;
- invalid format arguments, if a format argument is selected;
- absence of ANSI escape sequences unless explicitly requested; and
- privacy-safe failures with no raw prompts, responses, URLs, paths, tokens, or
  exception details.

Tests should be command-specific where the current contracts differ. In
particular, a readable status projection must not turn `unreachable` or
`unknown` into an invented diagnosis, and a readable health projection must not
claim a result beyond the one observed snapshot.

## Scope and architectural classification

### In scope for a possible future proposal

- finite read-only or one-shot operator-result presentation;
- projection of existing fields only;
- explicit preservation of machine-readable output;
- command-specific consistency where evidence supports it; and
- stdout, stderr, exit-status, compatibility, migration, and privacy questions.

### Out of scope

- domain-model or vocabulary changes; added observations; health, declaration,
  or routing changes; retries; polling or watch mode;
- dashboards, curses or interactive terminal UI, required colors, progress
  bars, spinners, logging changes, localization, shell completion, telemetry,
  database persistence, configuration files for output style, or a global CLI
  framework migration; and
- remote lifecycle behavior, process management, and compatibility API changes.

Documentation of `jq` is documentation-only. An opt-in presentation addition
that preserves the default could be a compatible presentation addition, but its
specific flag and exact output still need a decision. Changing default stdout is
a compatibility-sensitive CLI contract change. Selecting defaults, affected
commands, machine-output guarantees, or a shared abstraction shapes the
operator-facing command contract and therefore appears architectural under the
repository's decision rules; an RFC should precede implementation of such a
choice.

## Conclusions and evidence gaps

1. **Compact JSON is a real ordinary-operator friction.** One privacy-safe daily
   exercise directly observed it for preflight, health, and status; source and
   tests confirm those commands present dense structured data.
2. **Preflight, health, and status are materially affected.** History and the
   routing/account commands may also benefit in some cases, but their differing
   semantics mean that common formatting is not assumed. Clear-history gains
   little from a richer projection.
3. **Long-running startup, proof, and compatibility commands should remain
   outside a shared finite-output proposal.** Their server/process output is not
   one completed result and carries separate lifecycle or protocol boundaries.
4. **Documentation plus `jq` is immediately useful but not shown sufficient as
   a product response.** It retains raw structure, adds an external dependency,
   and cannot establish semantic operator wording.
5. **Changing default output would be compatibility-sensitive.** The current
   stdout, stderr, exit, serialization, and ordering properties are RFC- and
   test-visible.
6. **Machine-readable output can remain stable.** An explicit path could reuse
   the existing serializers and schemas, but this investigation does not choose
   how that path is named or whether it is default.
7. **One narrow candidate merits roadmap consideration.** The evidence does not
   justify lifecycle automation, additional observations, or broad terminal UI.
8. **An RFC appears necessary before implementation.** In particular, default
   representation, affected-command scope, and stable machine-output behavior
   are operator-facing compatibility decisions.
9. **The smallest plausible implementation boundary is presentation only for
   existing finite command results, beginning with the materially affected
   inspection commands.** It must preserve domain results and current privacy,
   stdout/stderr, and exit boundaries.
10. **Missing evidence includes external consumer use, how frequently each
    finite command is run interactively, which non-inspection commands operators
    want rendered, and whether a documentation-only workaround actually removes
    the observed friction.**

## Candidate roadmap framing

**Candidate only — not a roadmap decision**

**Human-readable operator command output**

Potential success statement:

> One operator can understand ordinary preflight, health, and status results
> directly in a terminal while an explicit stable machine-readable form remains
> available.

This candidate is deliberately unnumbered and does not add a phase. It neither
selects human-readable default output nor JSON default output, a flag name, TTY
behavior, command-specific coverage, or a shared abstraction. No implementation
should begin from this investigation alone.
