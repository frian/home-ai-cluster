# RFC-0086: Positional Bounded Code Command Messages

Status: Accepted

Date: 2026-08-25

Author: frian

## Summary

This RFC proposes one additive input ergonomics decision for the existing
bounded code-oriented commands. Each command would accept exactly one message
through either one positional argument or its existing `--message` option:

```text
hac code "Write a small Python function"
hac code-file --file path/to/file.py "Add input validation"
hac aider --file path/to/file.py "Refactor this function"
```

The existing explicit `--message` forms remain fully supported and equal:

```text
hac code --message "Write a small Python function"
hac code-file --file path/to/file.py --message "Add input validation"
hac aider --file path/to/file.py --message "Refactor this function"
```

This changes only the local command input boundary. It adds no interactive
mode, stdin, joining, request source, filesystem authority, runtime behavior,
or lifecycle behavior.

## Problem

RFC-0053 intentionally limited positional-message ergonomics to ordinary
Chat. Later RFC-0067, RFC-0068, and RFC-0080 established distinct bounded
`code`, `aider`, and `code-file` surfaces with an explicit `--message` option.
Those commands now require the longer spelling even when the operator supplies
one ordinary shell argument.

The resulting inconsistency is a small operator ergonomics gap. It should be
resolved explicitly rather than silently treating RFC-0053 as if it had
already amended later, independently accepted command surfaces.

## Goals

- Accept exactly one positional message or exactly one `--message` value for
  each affected command.
- Keep `--message` fully supported, non-legacy, and non-deprecated.
- Normalize equal accepted values into the existing identical internal request
  or Aider child invocation behavior.
- Preserve one-message boundaries, current `--file` semantics, and all
  existing bounded code-command contracts.
- Keep root-command argument forwarding unchanged.

## Non-goals

This RFC does not add interactive mode, stdin, a REPL, prompting, session or
conversation state, automatic message acquisition, message files, shell
completion, or an argument-joining grammar.

It does not make `--file` positional, change target creation or validation,
alter Aider ownership, add a generic CLI parser abstraction, add executable
aliases, or change root or standalone command ownership.

It does not change code capability admission, request or result formats,
output, timeout, failure, privacy, routing, transport, runtime, fallback,
persistence, lifecycle, dependency, or bounded-request contracts. It creates
no roadmap phase and authorizes no implementation in this RFC PR.

## Proposal

### Affected command surfaces

After a separate implementation, each command accepts exactly one of the
following forms:

```text
hac code MESSAGE [--timeout-seconds SECONDS] [-v | --verbose | --json]
hac code --message MESSAGE [--timeout-seconds SECONDS] [-v | --verbose | --json]

hac code-file --file PATH MESSAGE [--timeout-seconds SECONDS]
hac code-file --file PATH --message MESSAGE [--timeout-seconds SECONDS]

hac aider --file PATH MESSAGE [--timeout-seconds SECONDS]
hac aider --file PATH --message MESSAGE [--timeout-seconds SECONDS]
```

`MESSAGE` is exactly one shell argument. Multi-word positional messages use
ordinary shell quoting. For example:

```text
hac code "Explain this function"
```

The existing `--message` forms remain equal, supported alternatives. No
deprecation, warning, migration, or precedence rule is introduced.

`--file` remains exactly the existing one required option for `code-file` and
`aider`; it is not positional. Existing timeout and Code output options retain
their current parsing and meaning. Under RFC-0050 and RFC-0052, the root
commands continue forwarding all remaining arguments unchanged to the existing
command owners.

### Exact validation

Exactly one non-blank message source is required. The following are valid:

- one non-blank positional `MESSAGE` and no `--message`;
- exactly one non-blank `--message MESSAGE` and no positional message.

The following are invalid local input and must retain the existing command
failure behavior before child or native request construction:

- neither a positional message nor `--message`;
- blank or whitespace-only positional or `--message` values;
- repeated `--message`;
- both a positional message and `--message`;
- more than one positional token; and
- unknown arguments.

There is no precedence when both forms are supplied. Implementations must not
use `nargs="+"` or `nargs="*"`, or implicitly join trailing shell arguments.
Thus `hac code Write a function` is invalid rather than a request whose words
are joined by HAC.

### Normalization and unchanged behavior

For equal values, the `code` and `code-file` forms normalize to the same
existing message string and construct the same existing native `capability=code`
request. The `aider` forms normalize to the same existing message string and
produce the same fixed Aider child invocation. The message value is preserved
after non-blank validation.

All current `code-file` target handling, including RFC-0080 and RFC-0081
validation, creation, request construction, replacement, and failure rules,
remains unchanged. All current Aider target and subprocess rules, including
RFC-0068, RFC-0069, and RFC-0072, remain unchanged.

The proposal changes no timeout, output, failure, privacy, routing, transport,
runtime, fallback, persistence, lifecycle, capability, file-authority, or
bounded-request behavior. It adds no input source beyond the one explicitly
supplied command-line argument.

## Rationale

RFC-0053 supplies the primary precedent: one optional positional value is the
smallest ordinary shell spelling for a one-message command, while explicit
`--message` remains valuable for scripts and generated invocations. Applying
that same closed choice to the three existing bounded code-command surfaces
makes their ergonomics consistent without changing what the cluster or Aider
receives.

This must be a follow-up RFC rather than an unstated extension of RFC-0053.
RFC-0053 intentionally scoped positional input to Chat; later Code, Aider, and
Code File RFCs made their own explicit `--message` surfaces and preserve their
own distinct authority and lifecycle boundaries. A new decision makes the
narrow shared input change visible without revising accepted RFC history.

The approach is local-first and privacy-first because it neither acquires nor
retains new data. It is engine-independent and capability-centered because it
does not alter the existing `code` request or selection. It is a boring,
small, architecture-before-implementation decision: agents can later implement
the accepted local parser change, but do not own the decision.

## Alternatives considered

### Retain `--message` only

Rejected. It preserves current behavior but retains an unnecessary inconsistency
with accepted Chat ergonomics.

### Treat RFC-0053 as automatically applying

Rejected. Its accepted scope was Chat, and the later commands have separately
defined input surfaces. Silent extension would obscure the decision and blur
their distinct boundaries.

### Accept both sources with precedence

Rejected. Hidden selection can submit unintended content. Rejection is clear
and preserves one explicit source.

### Accept variable positional tokens and join them

Rejected. It loses the shell's argument boundary and requires joining and
whitespace rules. Normal shell quoting already expresses one multi-word value.

### Add stdin or interactive input

Rejected. It introduces source precedence, blocking, TTY, session, and
lifecycle decisions beyond this one-shot ergonomic refinement.

### Introduce a shared CLI parser abstraction

Rejected. A few parallel local declarations do not justify a framework or
refactor that could hide distinct command contracts.

## Trade-offs

The positional spelling reduces ordinary terminal friction and adds focused
validation cases. Operators must quote multi-word positional messages, and
unquoted surplus tokens fail. These small costs preserve a visible one-message
boundary, stable automation through `--message`, and the existing bounded
command behavior.

## Impact and implementation boundary

If accepted, a later separate implementation may make minimal localized
changes to the existing parsers in `code_command.py`, `code_file_command.py`,
and `aider_command.py`, with focused tests and any necessary operator
documentation. Root forwarding tests may demonstrate unchanged delegation.

It must not change core models, API routes, runtime adapters, routing,
capability admission, file semantics, Aider translation/lifecycle,
dependencies, executable aliases, or introduce a generic parser abstraction.

## Later implementation proof expectations

A later implementation PR must demonstrate for each affected command:

1. positional and retained `--message` input both succeed;
2. equal values normalize to the same existing native request or Aider child
   invocation;
3. missing, blank, repeated-option, both-source, surplus-positional, and
   unknown-argument input fails before child or native request construction;
4. `code-file` and `aider` retain exactly one existing `--file` target rule;
5. root commands forward positional and explicit forms unchanged; and
6. timeout, output, failure, target, privacy, routing, transport, runtime,
   fallback, persistence, lifecycle, and bounded-request behavior are
   unchanged.

No generated code may run, and no interactive, stdin, session, joining, or
automatic message-acquisition behavior may be added.

## Open questions

None within this narrow proposed decision.

## Decision

Accepted.

`hac code`, `hac code-file`, and `hac aider` may accept exactly one message
either positionally or through exactly one existing `--message`; the forms are
mutually exclusive, and `--message` remains fully supported and
non-deprecated. Existing `--file` semantics remain unchanged.

This decision authorizes no interactive mode, stdin, REPL, argument joining,
session state, or automatic message acquisition. Existing request,
bounded-input, target, timeout, output, failure, privacy, routing, transport,
runtime, fallback, persistence, and lifecycle behavior remains unchanged.
Implementation is authorized only in a later separate implementation PR.
