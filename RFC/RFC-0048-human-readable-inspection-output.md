# RFC-0048: Human-Readable Inspection Output

Status: Accepted

Date: 2026-07-18

Author: frian

## Summary

This RFC proposes a bounded presentation contract for these existing finite
inspection commands:

```text
home-ai-cluster-preflight
home-ai-cluster-health
home-ai-cluster-status
```

Their default successful result presentation becomes plain, human-readable
text. Each command accepts `--json`, which preserves its current compact JSON
stdout contract byte-for-byte. Output selection is explicit: it does not depend
on TTY detection, pipes, redirection, environment variables, configuration
files, terminal capabilities, terminal width, or color support.

Human output projects one already completed result. This RFC changes neither
domain models nor result vocabulary, observation, routing, declaration, health,
privacy, or lifecycle behavior.

## Problem

The three commands currently write compact JSON directly to an ordinary
terminal. That representation is structured, privacy-safe, and useful to
machines. It is also dense to scan during interactive operation.

One retained real daily operator exercise observed this friction while using
preflight, local health, and static-cluster status. These are ordinary finite
inspection commands in the canonical operator workflow: preflight establishes
static coherence, health observes the local node, and status reports one
bounded local-plus-declared-remote observation. They expose no prompt or
generated response.

Repository tests parse and assert current structured stdout, including compact
serialization and newline behavior. That establishes a real compatibility
concern within the repository. The repository does not prove that external
scripts consume these commands, and this RFC does not claim that they do.

Documentation using `jq` is an immediate useful workaround, but it requires an
external tool and leaves raw technical structure exposed. It cannot provide a
semantic product-level presentation for ordinary operators. Doing nothing keeps
the workflow functional but unnecessarily difficult to understand at the
terminal.

## Goals

- Make no-option interactive use of preflight, health, and status directly
  readable.
- Preserve one explicit stable machine-readable representation for each command.
- Keep output selection deterministic and explicit.
- Preserve all current result semantics, result fields, vocabularies, ordering,
  and privacy boundaries.
- Preserve privacy-safe failures and meaningful exit statuses.
- Use the smallest understandable presentation boundary.
- Avoid requiring external presentation tools or dependencies.

## Non-goals

This RFC does not include:

- `home-ai-cluster-chat`, request history or history clearing, routing
  explanation, or actual-request explanation;
- long-running commands, proof-scoped commands, OpenAI-compatible responses,
  Uvicorn output, or server logging;
- changing result models, field vocabularies, observations, remediation actions,
  or preflight, health, or status semantics;
- routing, fallback, declaration, health, privacy, or lifecycle changes;
- retries, polling, watch mode, progress bars, spinners, required color, or
  icons as semantic information;
- curses or another interactive terminal UI, terminal-width-dependent semantic
  omission, or localization;
- output configuration files, environment-variable output selection, automatic
  TTY detection, or a global CLI framework;
- a generic plugin or renderer system, dashboard work, lifecycle automation,
  database, Docker, or Kubernetes work.

## Proposal

### Included command contract

The included commands are exactly:

```text
home-ai-cluster-preflight
home-ai-cluster-health
home-ai-cluster-status
```

They remain finite inspection operations with their present evaluation and
observation behavior. The only new command behavior is selection of terminal
presentation after one completed result is available.

### Default mode

Without an output-selection flag, each included command writes its completed
result as human-readable plain text to stdout. For example:

```sh
uv run home-ai-cluster-preflight --declaration <DECLARATION_PATH>
uv run home-ai-cluster-health
uv run home-ai-cluster-status --declaration <DECLARATION_PATH>
```

Human output is not a parseable machine contract.

### Machine-readable mode

Each included command accepts the explicit boolean flag:

```text
--json
```

For example:

```sh
uv run home-ai-cluster-preflight --declaration <DECLARATION_PATH> --json
uv run home-ai-cluster-health --json
uv run home-ai-cluster-status --declaration <DECLARATION_PATH> --json
```

The flag's position follows ordinary argparse behavior and is not separately
constrained. This RFC adds none of the following:

```text
--human
--format
--pretty
--color
```

### Explicit, non-TTY selection

The selected representation must not change based on:

- `isatty`;
- piping or redirection;
- CI environment;
- terminal type, width, or color support; or
- any environment variable or configuration file.

The same invocation produces the same representation regardless of how its
stdout is connected.

## Machine-readable compatibility

`--json` preserves each command's current JSON contract exactly. This RFC
intentionally requires byte-for-byte preservation of the current successful
stdout JSON representation because source and tests establish it today.

For a completed result, `--json` must preserve:

- the current top-level JSON value shape and field insertion order;
- field names, nested-object structure, `null` values, empty arrays, and all
  established value vocabularies;
- preflight node order, declared-adapter order, registered-adapter order, and
  issue order;
- status local-node-first order and declared-remote order;
- the current compact `json.dumps(..., separators=(",", ":"))` serialization;
- exactly one JSON value on stdout with exactly one trailing newline;
- no human prose mixed into stdout; and
- the existing privacy boundary, including omission of values excluded by the
  current result.

This includes output for valid normalized states that are not successful in an
ordinary-language sense. In particular, incoherent preflight remains a complete
stdout JSON report, and status results containing unavailable or failed
observations remain complete stdout JSON results.

`--json` also preserves current diagnostic streams, safe failure messages, and
exit statuses as specified below. Argument-parser usage text may necessarily
show the new `--json` option; its standard argparse stderr and non-zero failure
behavior remains unchanged.

The default no-option stdout deliberately changes from JSON to human text for
the three included installed commands. Existing automation therefore migrates
from:

```text
command ...
```

to:

```text
command ... --json
```

The implementation and canonical operator documentation must identify this
change prominently. This RFC creates no transition period, warning cycle,
environment override, or dual-output mode. It makes no semantic-versioning
claim beyond this explicit migration.

## Human-readable projection principles

Human presentation must:

- use only information already present in the completed result;
- preserve result ordering;
- distinguish declared facts from observed facts where the result does;
- make an empty collection explicit where it is needed to understand the
  result;
- represent established status values without replacing them with synonyms that
  hide the underlying vocabulary;
- omit raw exceptions, URLs, addresses, credentials, prompts, responses, and
  any new machine identity;
- write one completed result and one trailing newline to stdout;
- keep diagnostics and failures on stderr;
- contain no ANSI escape sequences; and
- remain understandable in a basic plain-text terminal without color or column
  alignment carrying semantic meaning.

Tables may be used where helpful, but labels and sections must make the output
understandable even when spacing is not aligned. No third-party rendering
dependency is required.

### Preflight projection

Human preflight output must represent, in result order:

1. overall `status`;
2. `operating_mode`;
3. every ordered node with its `node_id`, `capabilities`, and
   `declared_adapters`;
4. `registered_adapters`; and
5. every issue with its `status`, `node_id`, `adapter`, and `reason`.

It must explicitly say when there are no issues. A report with no nodes or no
registered adapters must make those empty collections explicit rather than
silently omitting their sections.

For an incoherent report, the human report remains stdout result data, preserves
all issue information and order, and exits non-zero exactly as the current
command does. No equivalent result information may be dropped.

**Illustrative presentation — exact spacing is not contractual**

```text
Preflight: coherent
Operating mode: static-multi-node

Nodes:
- local
  Capabilities: chat
  Declared adapters: ollama
- receiver
  Capabilities: chat
  Declared adapters: remote-http

Registered adapters: ollama
Issues: none
```

### Health projection

Human health output must preserve the current distinction between each node's:

- `node_id` and `name`;
- declared `availability`, `healthy`, and `reason`;
- declared `capabilities` and `adapters`; and
- ordered adapter observations, each with `adapter`, `status`, and `reason`.

It must present current observation statuses, including `available`,
`unavailable`, `missing`, and `probe-failed`, without creating a synthetic
combined "healthy" result. It must make empty declared collections and empty
adapter observations explicit.

**Illustrative presentation — exact spacing is not contractual**

```text
Local health

Node: local
Name: Local node
Declared availability: available
Declared healthy: true
Declared reason: none
Capabilities: chat
Declared adapters: ollama

Adapter observations:
- Adapter: ollama
  Status: unavailable
  Reason: runtime unavailable
```

`none` in this example represents an existing `null` reason; it does not add a
new status or health interpretation.

### Status projection

Human status output must represent:

1. `declaration_status`;
2. the fixed local node first;
3. every declared remote in the existing declaration order; and
4. each node's `node_id`, `application_status`, and `runtime_status`.

All current normalized application values (`local`, `reachable`, `unreachable`,
`request-failed`, and `invalid-response`) and runtime values (`available`,
`unavailable`, `observation-failed`, and `unknown`) must be representable with
their existing vocabulary. The projection must not invent a diagnosis or
remediation from one normalized value.

**Illustrative presentation — exact spacing is not contractual**

```text
Cluster declaration: coherent

Nodes:
- local
  Application status: local
  Runtime status: unavailable
- receiver
  Application status: reachable
  Runtime status: available
```

## Errors and exit statuses

Output selection does not affect evaluation, observation, error handling, or
exit status. For the same completed result, default human output and `--json`
have the same operation semantics and exit status.

### Preflight

- A coherent report writes its selected stdout result and exits 0.
- An incoherent report writes its selected stdout result and exits 1, as the
  current command does.
- Invalid arguments and invalid declarations remain argparse stderr failures
  with a non-zero exit status and no result stdout.
- An unexpected construction failure writes exactly
  `error: unable to construct static preflight report` plus newline to stderr,
  writes no result stdout, and exits 1.

### Health

- A completed snapshot writes its selected stdout result and exits 0.
- A whole-snapshot construction failure writes exactly
  `error: unable to construct local health snapshot` plus newline to stderr,
  writes no result stdout, and exits 1.

The current health command has no arguments. Adding the smallest argparse
parser necessary solely for `--json` is permitted, provided no-option
invocation remains valid and unsupported arguments retain ordinary argparse
stderr and non-zero exit behavior.

### Status

- A completed status result writes its selected stdout result and exits 0.
  Normalized node unavailability and observation-failure states remain result
  data; they do not by themselves become command failure.
- Invalid arguments, invalid declarations, and invalid runtime-composition
  combinations remain argparse stderr failures with a non-zero exit status and
  no result stdout.
- An unexpected result-construction failure writes exactly
  `error: unable to construct cluster status result` plus newline to stderr,
  writes no result stdout, and exits 1.

## Parser behavior

Each included command gains the same `--json` boolean option:

- its default is `False`;
- it accepts no argument value;
- repeated occurrences follow ordinary argparse `store_true` behavior;
- unknown output flags and supplied values remain argparse errors;
- it composes with every currently valid argument combination; and
- it does not change validation or observation ordering.

No general shared CLI framework is introduced.

## Presentation code boundary

Implementation should use command-specific pure formatting functions. They may
live in one small presentation module only if that clearly avoids duplication.
The implementation must not introduce a renderer class hierarchy, generic table
framework, plugin model, or dependency added solely for formatting.

The existing domain evaluation functions continue returning their current
structured results independently of terminal rendering. JSON serialization and
human presentation occur only at the CLI edge after result construction. A tiny
shared helper for trivial selected-output emission is permitted, but this RFC
does not require a general abstraction.

## Rationale

The accepted canonical workflow expects an operator to run these finite
inspection commands directly. Making their no-option presentation readable
serves user simplicity without expanding the cluster's authority or changing
what it knows. The explicit `--json` path keeps automation deliberate and
visible; it avoids the surprise and test ambiguity of output that changes when
redirected.

The scope stays with the three commands for which the daily exercise directly
observed friction. Their completed results already contain the information
needed for bounded projection and exclude prompt and response content. Keeping
formatting at the CLI edge preserves runtime independence, result semantics,
and privacy boundaries.

## Alternatives considered

### Keep JSON default and add `--human`

Rejected. It preserves the current no-option contract but does not improve the
ordinary no-option operator path that motivated Phase 17.

### Add `--format human|json`

Rejected. Exactly two representations are justified now, and a general format
selector adds premature extensibility and validation surface.

### TTY-dependent output

Rejected. It is implicit, harder to test, and changes the same command under
redirection or piping.

### Separate `-json` commands

Rejected. Separate commands multiply the command surface and weaken
discoverability of the relationship between human and machine presentation.

### Pretty JSON by default

Rejected. Indentation improves syntax visibility but does not provide semantic
human presentation.

### Documentation plus `jq`

Retained as an immediate workaround but rejected as the product-level solution.
It requires an external tool and still presents raw internal structure.

### Human output only

Rejected. It would discard the current machine-readable command contract.

### Apply the policy to all finite commands

Deferred. Evidence is strongest for preflight, health, and status. Chat and
the explanation surfaces have different content, side effects, privacy, and
compatibility concerns.

## Trade-offs

This proposal gives operators direct readability, an explicit automation
contract, deterministic behavior, no external formatting dependency, and
preserved domain semantics.

It intentionally changes no-option stdout compatibility for three installed
commands. Script users must add `--json`; implementation must add three sets of
human-projection tests and migrate documentation. Limited command-specific
formatting duplication is acceptable when the alternative is a premature
renderer abstraction.

## Impact

If accepted, this RFC authorizes a later small implementation for exactly the
three included command edges. That implementation must update the canonical
operator workflow, relevant command documentation, examples that present
compact JSON as default, Phase 17 proof or runbook material, and any normal RFC
references or documentation-index links.

This Draft RFC changes no command behavior and contains no implementation,
dependency, proof, or additional documentation artifact. `RFC/README.md`
defines RFC process and template but does not index individual RFCs, so it does
not change in this proposal.

## Testing requirements

A future implementation must test at least:

- default human output and one trailing newline for each command;
- exact `--json` compatibility, including compact serialization, for each
  command;
- no ANSI escape sequences and stdout/stderr separation;
- existing exit statuses and privacy-safe unexpected failures;
- preflight coherent and incoherent results, issue ordering, and empty issues
  and collections;
- health declared-versus-observed distinction and available, unavailable,
  missing, and probe-failed observations;
- status node ordering, all normalized application and runtime values, multiple
  remotes, and interaction with runtime-composition arguments;
- argparse treatment of invalid output-flag use where applicable; and
- no repeated observation or evaluation merely to render a second format.

## Privacy and security

Human projections must not expose information omitted by the structured
results. They must not add transport URLs, private addresses, executable or
filesystem paths, credentials, prompts, generated responses, raw exceptions,
or runtime-specific information excluded by the current result contracts.

No color or terminal escape sequence may be required to distinguish states.

## Open questions

- What exact whitespace and column widths, if any, should a future plain-text
  implementation use within the required information and ordering?
- Should command-specific functions remain colocated with their commands, or
  should a tiny common plain-text utility be introduced after duplication is
  demonstrated?

These are implementation details. This RFC resolves the default format,
`--json` name, non-TTY behavior, included commands, machine-readable
preservation, output streams, and exit-status semantics.

## Decision

Home AI Cluster accepts human-readable plain-text output by default for
`home-ai-cluster-preflight`, `home-ai-cluster-health`, and
`home-ai-cluster-status`.

Each command will provide explicit `--json`, preserving its current compact JSON
stdout contract byte-for-byte. Output remains deterministic and independent of
TTY state, pipes, redirection, environment variables, and configuration.

Implementation must preserve existing domain results, ordering, privacy
boundaries, diagnostics, and exit-status semantics. It will use command-specific
bounded formatting at the CLI edge, without a generic renderer architecture or
formatting dependency.

Implementation remains separate and must follow this accepted RFC.
