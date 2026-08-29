# RFC-0092: Ordinary CLI Short Options

Status: Draft

Date: 2026-08-29

Author: frian

## Summary

This RFC proposes one finite, additive ordinary CLI vocabulary:

| Short | Long | Commands |
| --- | --- | --- |
| `-h` | `--help` | root `hac`, root `home-ai-cluster` |
| `-f` | `--file` | aider, code-file, summarize, classify |
| `-d` | `--declaration` | static-cluster, compatibility, preflight, status |
| `-l` | `--label` | classify |
| `-j` | `--json` | chat, code, external-information, summarize, classify, preflight, health, status |

Every long form remains supported, canonical, and non-deprecated. This Draft
authorizes no implementation.

Existing behavior is not newly proposed:

| Short | Long | Commands |
| --- | --- | --- |
| `-h` | `--help` | all argparse-backed subcommands |
| `-v` | `--verbose` | chat, code, external-information, summarize, classify |

## Problem

The completed CLI short-option investigation found a small amount of repeated
ordinary typing ceremony. The problem is not that every long option is verbose:
most remain clearer long-only. It is that a few recurring conventional concepts
lack a consistent short spelling while argparse-backed subcommands already
support `-h/--help` and several ordinary request commands already support
`-v/--verbose`.

A small set can improve ordinary daily comfort without creating a second command
language, hiding operator authority, or changing any request semantics. It is
worthwhile before 0.6 if accepted, but the current CLI satisfies the 0.6 exit
condition and this is not a release blocker.

## Goals

- Add only the five mappings in the proposed-new-vocabulary table.
- Preserve each existing parser option's value, validation, and behavior.
- Close the root `-h` inconsistency without changing general root parsing.
- Keep long and short spellings behaviorally equal and long forms explicit.
- Keep authority-sensitive and specialized choices visibly long-only.

## Non-goals

This RFC does not add automatic abbreviation, prefix matching, generated
aliases, an alias registry or allocation API, combined short flags, global
option parsing, shell completion, command aliases, renamed commands,
environment options, configuration, profiles, or parser replacement. It does
not establish a policy that every future option needs a short form.

It changes no runtime, capability, routing, request, API, network, privacy,
filesystem, persistence, history, lifecycle, output, or failure contract.

## Proposal

### Root help

Both root spellings will accept exactly `-h` as an additive spelling of their
existing root-only `--help` request:

```text
hac -h
home-ai-cluster -h
```

Each prints the same root help and succeeds exactly as the corresponding
`--help`. The custom root dispatcher recognizes this exact root request only;
it gains no generic global-option parser, combined flags, or `-V`/`-v` spelling
for `--version`. Existing `hac chat -h` and other subcommand help behavior
continues to be argparse-owned and unchanged.

### File

`-f` becomes an additional option string for the existing `--file` action on
`aider`, `code-file`, `summarize`, and `classify`, including equivalent long-root
and shared standalone-parser entry points. It is the identical parser
destination and action, not a generic file-option abstraction.

The respective existing contracts remain intact: Aider and Code-file retain
their exactly-one selected target validation; Summarize and Classify retain
their `--text` mutual exclusion; all retain their current file validation,
caller-local filesystem authority, request construction, and failure behavior.

### Declaration

`-d` becomes an additional option string for `--declaration` on
`static-cluster`, `compatibility`, `preflight`, and `status`, through both root
names and their shared parser entry points. Required versus optional use,
declaration/inline-topology mutual exclusion, parsing, validation, topology
ownership, routing, compatibility, and observation behavior remain unchanged.
No discovery, default path, retained configuration, or topology behavior is
introduced.

### Label

`-l` becomes an additional option string for Classify's existing repeatable,
ordered `--label` input. It preserves the order, validation, request shape,
exact selected-label semantics, and failures. No inferred, defaulted, aliased,
or normalized label behavior is introduced.

### JSON

`-j` becomes an additional option string for existing `--json` on exactly
`chat`, `code`, `external-information`, `summarize`, `classify`, `preflight`,
`health`, and `status`. It does not add JSON to another command. It joins the
existing mutually exclusive JSON/verbose output group where one exists and
preserves JSON schemas, serialization, stdout/stderr behavior, interactive
restrictions, exit status, request behavior, and failures.

### Equal spellings and long forms

For every accepted mapping, the short and long spellings bind to the same
existing parser option and destination. They introduce no special duplicate,
precedence, or mixed-spelling rule: existing parser action behavior remains the
behavior regardless of which accepted spelling is supplied.

Long forms remain supported, canonical, non-deprecated, documented after a
later implementation, and appropriate for explicit or generated commands. No
warning, migration, replacement terminology, schedule, or preference is added.

### Examples

The following pairs are equal forms, not preferred-versus-legacy forms:

```sh
hac summarize --file notes.txt
hac summarize -f notes.txt

hac classify --file message.txt --label personal --label work
hac classify -f message.txt -l personal -l work

hac preflight --declaration cluster.toml
hac preflight -d cluster.toml

hac status --declaration cluster.toml --json
hac status -d cluster.toml -j

hac chat "Hello" --json
hac chat "Hello" -j

hac --help
hac -h
```

## Preserved semantic boundaries

The aliases alter accepted local CLI spelling only. They do not change parser
destinations, validation, repeatability, mutual exclusion, defaults,
precedence, request models or bodies, endpoints, routing, capability or node
selection, runtime/model behavior, privacy, security, network or filesystem
authority, persistence, history, lifecycle ownership, output content, JSON
schema, exit codes, or failure normalization.

## Explicit non-aliases

- `-m` is not added for `--message`: Chat, Code, Code-file, and Aider already
  have accepted positional message forms; their existing long form is unchanged.
- `-q` is not added: external-information QUERY and QUESTION are distinct, and
  RFC-0091 already supplies their accepted positional form.
- `-t` is not added: `--text` and `--timeout-seconds` are distinct concepts and
  must not receive conflicting meanings across one product.
- `-p` is unassigned. It is not `--plugin`: RFC-0091 retains named per-operation
  plugin selection as a visible authority and network-disclosure decision. It
  is also not `--port`: RFC-0090 fixes ordinary HAC at 25042 and retains port as
  an exceptional server-only override that clients do not discover or receive.
  This RFC makes no permanent reservation for `-p`.
- `-r` is not added for `--runtime`: it is coherent but lacks sufficient
  repeated-use evidence for this first set and remains possible later work.

The following specialized, structural, exposure-sensitive, runtime-specific,
topology/network-sensitive, or authority-significant options remain long-only:
`--plugin`, `--host`, `--runtime-config`, `--ollama-model`,
`--ollama-disable-thinking`, `--llama-server-base-url`,
`--llama-server-model`, `--remote-node-id`, `--remote-base-url`,
`--local-capability`, `--remote-capability`, and `--proof-observation`. This is
the current bounded evidence, not a universal prohibition on later aliases.

## Accepted-contract amendments

RFC-0092 amends only CLI spelling, and leaves every non-spelling provision
unchanged, in these accepted contracts:

- RFC-0050 for the custom ordinary root command's exact `-h` help request;
- RFC-0068 for Aider's selected `--file` argument;
- RFC-0080 and RFC-0081 for Code-file's selected `--file` argument;
- RFC-0054 and RFC-0057 for Summarize's source/file and output forms;
- RFC-0061 for Classify's source, ordered label, and JSON output forms;
- RFC-0039 and RFC-0040 for static-cluster declaration selection;
- RFC-0046 for compatibility declaration selection;
- RFC-0036 and RFC-0048 for preflight declaration and presentation spelling;
- RFC-0041 and RFC-0048 for status declaration and presentation spelling;
- RFC-0033 and RFC-0048 for health presentation spelling;
- RFC-0049 for Chat and Summarize output-mode spelling;
- RFC-0067 for Code output-mode spelling; and
- RFC-0078 and RFC-0091 for external-information output-mode spelling while
  preserving its named plugin and positional query/question boundaries.

This does not supersede any whole RFC or retroactively edit accepted RFC files.

## Rationale

One memorable concept per letter is smaller than arbitrary per-command
abbreviations. File, declaration, label, and JSON are recurring conventional
inputs or presentation choices with direct ordinary-workflow evidence. Root
`-h` removes a concrete inconsistency with every argparse-backed subcommand.
Existing `-v/--verbose` demonstrates that additive equal spellings already fit
the ordinary CLI.

Retaining long forms protects clarity and scripts. Keeping plugin, topology,
runtime, and proof controls visually explicit preserves boundaries where the
evidence favors it. The proposal is local-first, privacy-first,
engine-independent, and capability-centered because it moves no behavior
behind the caller edge.

## Alternatives considered

Keeping all commands long-only leaves the observed small friction unresolved.
Aliasing every frequent long option creates a cryptic second vocabulary without
evidence. `-m`, `-q`, `-t`, `-p/--plugin`, `-p/--port`, and `-r/--runtime` are
rejected or deferred for the reasons above. Aliases for topology or
runtime-specific advanced controls lack ordinary-use value and can obscure
structural choices. Automatic abbreviation or a general alias framework is
premature abstraction for this finite mapping.

## Relationship to 0.6

If accepted, this is worthwhile before 0.6 because it addresses one concrete
ordinary CLI ergonomics observation. Current behavior nonetheless satisfies the
0.6 exit condition; this RFC is not evidence that 0.6 was previously unready
and is not a release blocker. Draft PR #575 remains a separate checkpoint and
is neither amended nor decided by this RFC.

## Implementation boundary

This Draft authorizes no implementation, tests, or user-documentation change.
If accepted, one later focused implementation PR may add only these option
strings, focused parser/help tests, and relevant current documentation/examples.
It must preserve every long form and semantic boundary and must introduce no
unrelated CLI cleanup.

## Open questions

None within this finite proposed mapping.

## Decision

Draft. No decision or implementation is authorized until review and acceptance.
