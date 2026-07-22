# RFC-0050: Additive Unified Operator Command

Status: Accepted

Date: 2026-07-22

Author: frian

## Summary

Home AI Cluster should add one installed root command:

```text
home-ai-cluster
```

It is an additive facade over seven existing ordinary operator surfaces. It
recognizes exact subcommands, passes their remaining arguments to the existing
command implementation, and otherwise adds only static root help, a package
version display, and safe root-parser errors. Existing installed
commands remain unchanged and supported.

The facade is not a lifecycle manager, configuration system, general CLI
framework, dispatcher for every installed script, or another orchestration
layer. It changes no request, output, failure, routing, runtime, topology,
network, history, or privacy behavior.

## Problem

The completed post-roadmap system has several accepted ordinary commands with
separate, accurate purposes: foreground local, static-cluster, and
compatibility processes; one-shot chat; and finite preflight, health, and
status operations. The README and canonical workflow document their sequence,
but operators must discover and remember independent executable names.

The repository previously retained limited evidence of command-selection
mistakes. The project's technical first user has now reported that this
fragmentation is a concrete usability gap and selected one coherent ordinary
operator command as the next priority. The report concerns command discovery
and naming coherence only. It does not identify missing runtime, routing,
topology, lifecycle, or configuration behavior.

Doing nothing preserves all current behavior but leaves that supported
ordinary-surface discovery problem unresolved. Treating every installed script
as an ordinary root subcommand would instead make retained proof scaffolding
look like product operation and blur accepted boundaries.

## Goals

This RFC proposes to:

- provide one discoverable namespace for a selected set of ordinary commands;
- preserve each delegated command's arguments, output, failures, exit status,
  foreground process behavior, signals, and privacy contract;
- keep process, runtime, topology, and terminal ownership with the operator;
- use explicit names and a small standard-library parsing boundary; and
- retain all existing standalone entry points without warning, preference, or
  deprecation behavior.

## Non-goals

This RFC does not add or change:

- a capability, endpoint, request format, result format, or output format;
- runtime composition, routing, fallback, retry, topology, or network access;
- process supervision, daemonization, implicit or multi-process startup,
  shutdown, process discovery, PID files, restart behavior, or a lifecycle
  manager;
- discovery, scheduling, automatic topology mutation, configuration,
  authentication, internet exposure, or history behavior;
- proof command exposure, shell completion, interactive prompting, a TUI,
  dashboard, plugin framework, database, Docker, or Kubernetes; or
- removal, renaming, deprecation, aliases, compatibility warnings, or a
  migration timeline for existing commands.

## Proposal

### Root command and selected scope

Add exactly one new project script named `home-ai-cluster`. Its first contract
has exactly these ordinary subcommand concepts:

```text
home-ai-cluster local
home-ai-cluster static-cluster
home-ai-cluster compatibility
home-ai-cluster chat
home-ai-cluster preflight
home-ai-cluster health
home-ai-cluster status
```

They delegate respectively to the accepted implementations behind:

```text
home-ai-cluster-local
home-ai-cluster-static-cluster
home-ai-cluster-openai-compatibility
home-ai-cluster-chat
home-ai-cluster-preflight
home-ai-cluster-health
home-ai-cluster-status
```

`static-cluster` is preferred to ambiguous `cluster`: the accepted ordinary
mode is explicitly static and uses operator-owned declarations. `compatibility`
is preferred to `openai`: RFC-0031 defines only a narrow compatibility edge,
not general OpenAI API ownership. `start`, `run`, and `serve` are excluded
because they can imply daemonization, supervision, start/stop authority, or
process ownership that the project does not have.

Proof utilities are excluded because their retained architecture-evidence role
is not ordinary product operation. History and explanation commands are also
excluded: history is an opt-in bounded record tied to the explicit
actual-request account, and explanation surfaces have their own narrow
diagnostic meanings. Their inclusion needs separate evidence and a later
decision.

### Exact grammar

The root accepts only this grammar:

```text
home-ai-cluster [--help]
home-ai-cluster [--version]
home-ai-cluster <subcommand> [subcommand arguments...]
```

Subcommands are exact full names. There are no aliases, abbreviations, fuzzy
matching, automatic correction, interactive selection, or TTY-dependent
behavior. Subcommand options appear only after the subcommand. The root has no
global runtime, topology, output, logging, verbosity, or configuration option.

### Root help and version

With no subcommand, or with `--help`, the root writes static help to stdout and
exits 0. It starts no process, inspects no environment, runtime, declaration,
or topology, and makes no network request. Help lists only the seven selected
ordinary subcommands and clearly classifies `local`, `static-cluster`, and
`compatibility` as foreground processes and the remaining four as finite
commands. It does not list proof utilities or private configuration.

The first contract includes `--version`. `pyproject.toml` is the existing
authoritative package-version declaration, so the root prints that installed
package version only, followed by one newline, to stdout and exits 0. It must
not derive version data from the environment, network, Git checkout, runtime,
or topology.

`home-ai-cluster <subcommand> --help` directly delegates the remaining argument
list to the current command implementation by default. Its usage identity may
therefore retain the standalone command's `prog` value, which is preferred over
adding an adapter. No adapter should be added unless focused implementation
evidence shows one is necessary to satisfy this accepted root-help contract.
Any such adapter must be command-specific and minimal, and must not become a
shared parser abstraction or generic framework.

### Root parser errors

An unknown subcommand is a root-local failure with this exact contract:

```text
stdout: empty
stderr: error: unknown command\n
exit status: 2
```

It must not echo the supplied token, expose Python exception text, print root
help, or delegate any command. It performs no environment, runtime, topology,
or network activity. Root help and version are the only root-level success
outputs.

### Delegation

The root parser recognizes one selected exact subcommand and passes the
remaining argument list unchanged to that implementation's existing `main()`.
It neither parses nor rewrites subcommand arguments, invokes a subprocess,
wraps standard streams, catches and translates `SystemExit`, nor alters signal
handling.

The current target `main()` functions accept explicit argument lists. They may
write directly to stdout or stderr, raise `SystemExit`, or run foreground
`uvicorn` processes. Those command-specific behaviors remain owned by their
existing implementations. Direct in-process delegation is the smallest clear
way to preserve them; the root dispatches one selected operation only.

### Output and failure compatibility

For every delegated operation, the root preserves existing request
construction; stdout and stderr; output and JSON formats; local validation;
HTTP behavior; exit codes; process foreground behavior; signal handling;
routing; fallback; runtime composition; topology; privacy; and history
behavior. It must not wrap, prefix, decorate, summarize, recolor, normalize,
or otherwise change delegated output or failures.

### Process, lifecycle, and privacy boundary

The facade preserves foreground execution, operator-owned terminals,
operator-owned runtime startup and shutdown, and operator-owned process
stopping. It adds no background or daemon mode, PID file, restart behavior,
process discovery, polling, `start`, `stop`, or `restart` subcommand, or
multi-process orchestration.

It adds no prompt or response logging, telemetry, usage analytics, hidden
files, command history, retained configuration, environment capture, runtime
or topology probing, or network access before delegation. Root help and parser
errors are static and privacy-safe.

### Packaging and implementation boundary

Later implementation adds one `[project.scripts]` entry named
`home-ai-cluster`; all existing entries remain unchanged. It introduces no
packaging migration, executable shim, installed shell alias, completion, or
generated wrapper.

`src/home_ai_cluster/command.py` is the probable narrow implementation module.
It should use the Python standard library and the repository's existing parser
style, with an explicit seven-entry dispatch table. It must not introduce a
generic CLI package, command registry, plugin mechanism, or large refactor.

## Rationale

An additive facade answers the reported first-user usability problem while
keeping the accepted commands as the owners of their specific contracts. The
selected seven surfaces match the canonical ordinary workflow: three explicit
foreground process modes, one ordinary request, and three bounded inspection
operations. Explicit full subcommands make those modes discoverable without
pretending that they are one lifecycle system.

Direct delegation preserves the already tested parser, output, error, and
process seams. It is more transparent than subprocess orchestration and
smaller than shared parser refactoring. The scope is intentionally narrower
than the installed-script inventory so that proof and forensic concepts do not
become ordinary product vocabulary by accident.

## Alternatives considered

### No change

Rejected. Existing documentation remains useful, but the first-user report
establishes a concrete command-discovery gap that documentation alone does not
resolve.

### Finite commands only

Rejected. It groups useful finite actions but leaves ordinary process startup
outside the only discoverable ordinary namespace.

### Every installed command, including proof utilities

Rejected. It would turn retained proof scaffolding into apparent product
operation and make root help misleading.

### History and explanation in the first facade

Deferred. Their accepted purposes are secondary and deliberately narrow; no
evidence yet supports presenting them as ordinary root operations.

### Subprocess delegation

Rejected. It adds installation/PATH dependence, child signal forwarding, and
error complexity for no new operator value.

### Duplicated parsers or a generic CLI framework

Rejected. Duplicated parsing can drift from accepted command contracts; a
generic framework hides a small explicit mapping behind unneeded abstraction.

### `home-ai-cluster start ...`

Rejected. It suggests lifecycle authority, daemonization, or process management
that the project explicitly retains with the operator.

### Aliases and abbreviated subcommands

Rejected. They add durable namespace and ambiguity decisions without evidence.

### Removal or deprecation of standalone commands

Rejected. The facade is additive. Future deprecation needs separate evidence
and a separate accepted decision.

### Interactive menu, TUI, or lifecycle manager

Rejected. Each adds interaction or lifecycle authority beyond command discovery
and is disproportionate to the demonstrated problem.

## Trade-offs

The facade provides one discoverable ordinary namespace, reduces command-name
fragmentation, preserves current compatibility, and adds no runtime or routing
behavior or system authority.

It also adds a public root CLI contract. Root help and parser errors require
focused tests; selected names become durable; both root and standalone forms
must be maintained; and help identity can differ between root and standalone
invocation. These costs are acceptable because the implementation remains a
small explicit adapter over existing behavior.

## Impact

Later implementation affects package entry points, one small root-command
module, focused root and compatibility tests, README guidance, and possibly a
retained proof. It does not alter core orchestration, request/response models,
runtime adapters, topology declarations, routes, or existing command modules.

The change is a standalone post-roadmap refinement, not Phase 18. It requires
no roadmap phase, creates no new capability, and grants no authority beyond the
additive operator namespace.

## Implementation sequence

After acceptance, a bounded implementation should:

1. add one root-command module;
2. add the one project script entry point;
3. implement an explicit seven-subcommand dispatch table;
4. add focused root-parser tests;
5. add compatibility tests showing delegated behavior is unchanged;
6. update README guidance; and
7. retain a proof if needed.

It must not use this sequence to authorize unrelated refactoring.

## Open questions

- What exact static root-help wording best distinguishes foreground and finite
  operations while remaining concise?
- If focused implementation evidence shows an adapter is necessary for
  root-oriented help, what is the smallest command-specific seam that preserves
  direct delegation as the default?

These questions do not reopen the selected scope, exact names, delegation
model, or retained standalone contracts.

## Decision

Accepted.

Home AI Cluster will add one additive `home-ai-cluster` entry point with the
seven exact subcommands `local`, `static-cluster`, `compatibility`, `chat`,
`preflight`, `health`, and `status`. It will use direct in-process delegation,
static root help, the package-version-only `--version` contract, and the exact
unknown-command failure defined above.

All standalone commands remain unchanged and supported. The root facade adds no
lifecycle management and creates no Phase 18. This decision authorizes only
the bounded implementation sequence in this RFC; it does not authorize work
beyond that sequence.
