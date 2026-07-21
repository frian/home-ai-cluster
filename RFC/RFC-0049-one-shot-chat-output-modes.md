# RFC-0049: One-shot chat output modes

Status: Draft

Date: 2026-07-21

Author: frian

## Summary

`home-ai-cluster-chat` should present a validated successful `ClusterResult` in
one of exactly three explicit modes: generated content by default,
human-readable content plus attribution with `-v`/`--verbose`, or the historical
compact complete JSON representation with `--json`. This changes only success
presentation at the command edge. It preserves the accepted RFC-0045 request,
transport, validation, failure, timeout, privacy, routing, fallback, topology,
and lifecycle contracts.

## Context

RFC-0045 established `home-ai-cluster-chat` as a thin client of the already
running ordinary cluster. It currently requires one compact complete
`ClusterResult` JSON object as its only successful output and explicitly rejects
content-only output, human-readable or pretty output, output selection, and
additional output options.

That compact result remains useful to machine consumers and retains cluster-owned
attribution. A real operator friction is nevertheless observed: the command's
primary ordinary use is to ask one question and read one answer, while its
default terminal result is raw JSON. The Phase 17 decision for preflight,
health, and status demonstrates a narrow presentation-at-the-CLI-edge pattern,
but deliberately did not include chat. Chat is a request-and-response command,
so its useful default may differ.

## Problem

Operators must visually extract generated content from a compact JSON object
when using one ordinary chat request interactively. Preserving JSON as the
no-option default retains existing scripts but does not address this observed
terminal friction. Changing the default without an explicit machine path would
break script consumers and discard normalized attribution.

## Goals

- Make the no-option successful chat result directly readable as its answer.
- Preserve an explicit byte-for-byte historical machine representation.
- Provide a deliberate human-readable attribution view without changing result
  semantics.
- Keep mode selection explicit and independent of terminal environment.
- Preserve every existing RFC-0045 execution, failure, privacy, and ownership
  boundary.
- Use one small command-specific presentation boundary with no dependency.

## Non-goals

This RFC does not add input modes, standard input, files, sessions, streaming,
tools, generation controls, selectors, configuration, retry, fallback,
discovery, supervision, persistence, history, a dashboard, database, Docker,
or Kubernetes. It does not change `/v1/chat`, `ClusterResult`, core or transport
models, runtime adapters, routing, topology, lifecycle, localization, color, or
TTY detection. It does not define a roadmap phase or reopen Phase 17.

## Decision

This RFC supersedes only the RFC-0045 successful-output presentation clauses
for `home-ai-cluster-chat`. All other RFC-0045 contracts remain authoritative.
Output mode selection occurs only after one successful HTTP response has been
validated as the authoritative `ClusterResult`.

### Default content mode

Without an output option:

```sh
home-ai-cluster-chat --message "Hello"
```

The command writes only `ClusterResult.content` to stdout. It must not strip,
indent, wrap, escape, Markdown-render, or normalize internal whitespace. It
therefore preserves multiline text, blank lines, Markdown, code fences, leading
whitespace, trailing whitespace, and Unicode.

The command writes content unchanged, then writes one final newline only when
the content does not end in `\n`. If it already ends in `\n`, it adds none.
This preserves textual content but is not byte-for-byte output when generated
content lacks a final newline. When `content` is empty, default content mode
writes exactly one newline. Stderr is empty and exit status is 0.

### Verbose human mode

`--verbose` and `-v` select the same mode:

```sh
home-ai-cluster-chat --message "Hello" --verbose
home-ai-cluster-chat --message "Hello" -v
```

The exact structure and field order are:

```text
Response:
<generated content>

Execution:
  Node: <ClusterResult.node_id>
  Adapter: <ClusterResult.adapter>
  Model: <ClusterResult.model>
```

`Response:`, generated content, `Execution:`, `Node`, `Adapter`, and optional
`Model` occur in that order. The formatter must not reindent or otherwise
transform generated content: it writes that content exactly once, never strips
it, and preserves every existing trailing newline. The formatter may add
structural newline characters outside the generated content. It must ensure that
`Execution:` starts on its own line and adds no more than one blank separator
line of its own. Existing trailing newlines in generated content remain
untouched and may therefore create additional visible blank lines; verbose mode
does not guarantee exactly one visible blank line before `Execution:`.

When `content` is empty, verbose mode writes the `Response:` heading, no
generated text or placeholder, the normal structural separation, and the
`Execution:` block.

`Node` projects `node_id`; `Adapter` projects `adapter`; `Model` projects
`model`. Omit the `Model` line when `model` is `None` or an empty string. Do not
invent `unknown`, `none`, `unavailable`, or another substitute value. Stderr is
empty and exit status is 0.

### JSON compatibility mode

`--json` selects the historical RFC-0045 successful output:

```sh
home-ai-cluster-chat --message "Hello" --json
```

It writes exactly one compact JSON object to stdout and preserves byte-for-byte
the prior successful representation: top-level fields `content`, `adapter`,
`model`, and `node_id` in that order; exact validated values; compact separators;
existing Unicode escaping behavior; and `null` for an absent model. It writes
exactly one final newline, no human framing or wrapper, empty stderr, and exits
0.

### Option exclusivity

`--verbose`/`-v` and `--json` are mutually exclusive. An invocation containing
both performs no HTTP request, writes no stdout, writes exactly:

```text
error: invalid request input
```

to stderr, and exits 2. There is no option-precedence rule.

Selection must not depend on TTY state, pipes, redirection, environment
variables, configuration, terminal width, or color support.

### Content and newline semantics

Default content mode uses the rule above: unchanged text plus a final newline
only when one is absent, including exactly one newline for empty content.
Verbose mode writes generated text exactly once without stripping, reindenting,
or normalizing it, including its existing trailing newlines, and adds only
structural newline characters outside it. It ensures that `Execution:` starts on
its own line while adding no more than one blank separator line of its own;
existing content trailing newlines may create additional visible blank lines.
JSON mode retains its historical one-final-newline serialization. These rules
are presentation rules, not changes to the validated `ClusterResult.content`
value.

### Failure and exit behavior

Every existing RFC-0045 request and execution failure remains identical in every
valid mode. Without a validated successful `ClusterResult`, stdout remains
empty; stderr retains the same stable prompt-free safe line; and the existing
exit status and failure classification are preserved. Mode selection must not
alter failure classification.

### Execution boundary

Output selection must not affect message validation, native request construction,
fixed `chat` capability, fixed loopback target, HTTP method/body, timeout,
redirects, number of requests, response validation, routing, fallback, topology,
runtime/adapter/model/node selection, error translation, privacy, retention, or
process lifecycle. The command remains a thin client of the already running
ordinary cluster.

### Privacy

Formatting a completed result creates no retention. The command continues not to
log or persist messages, generated content, requests, or responses, and failure
output remains free of prompts, generated responses, URLs, private identities,
addresses, credentials, raw response bodies, and exceptions. Successful stdout
remains direct operator output that surrounding systems may retain outside the
project's control.

### Compatibility and migration

Changing no-option success output from compact JSON to generated content is a
breaking CLI-default change for callers that parse the current output. `--json`
is an explicit migration and compatibility path; it does not make the default
change backward-compatible and no automatic compatibility is claimed.

```text
Before:
  home-ai-cluster-chat --message "Hello"

After, for machine consumers:
  home-ai-cluster-chat --message "Hello" --json
```

## Rationale

Content-only default output fits the bounded command's ordinary purpose: show
one answer directly. Verbose mode retains deliberate access to truthful node,
adapter, and model attribution without forcing it into every response. Explicit
JSON preserves the complete historic representation for machines. Mutually
exclusive flags avoid an ambiguous mixture of prose and one machine contract.

This is the smallest presentation change because it formats one already
validated result at the command edge. It neither creates new request authority
nor gives the client runtime, routing, or topology knowledge.

## Alternatives considered

### Keep compact JSON as the default

This preserves current default compatibility and needs no RFC-0045 successor,
but leaves the observed ordinary-terminal friction unresolved.

### Human response plus attribution as the default

This keeps attribution always visible, but reduces answer readability and still
breaks JSON-default consumers. Attribution is better available deliberately in
verbose mode.

### Add only `--content-only` while retaining JSON default

This preserves the default, but makes the primary terminal use opt-in and does
not define a concise human attribution view.

### Use `--quiet`

Rejected: content is not merely a quieter version of a complete result; it is a
distinct presentation. `--quiet` also obscures what information is omitted.

### Omit verbose mode

Rejected: this would leave no direct readable presentation of truthful execution
attribution, pushing operators back to JSON for that purpose.

### Use TTY-dependent output

Rejected: pipes, redirection, CI, and terminal properties would silently change
the contract. Explicit mode selection follows the bounded Phase 17 precedent.

### Add a generic formatter

Rejected: one command does not justify a shared CLI-output framework, renderer
protocol, or abstraction. Command-specific helpers are smaller and clearer.

### Amend RFC-0045 instead of creating a focused successor RFC

Deferred in favor of this successor RFC. RFC-0045 is accepted project memory for
the original one-shot client. RFC-0049 narrowly supersedes its success-
presentation clauses for this command while preserving every other RFC-0045
contract, making the changed compatibility decision explicit without rewriting
history.

## Trade-offs

Default content is easier to read and copy, but it is a breaking default change
for JSON-parsing scripts. `--json` offers a deterministic migration rather than
automatic compatibility. A final newline improves normal terminal framing but
means no-final-newline content is not byte-for-byte stdout. Verbose attribution
improves transparency while adding a second human representation; exact labels
and ordering constrain future presentation changes intentionally.

## Impact

A future implementation changes only the successful CLI presentation of
`home-ai-cluster-chat`. It does not change the native HTTP API, result schema,
runtime behavior, cluster composition, routing, fallback, privacy policy, or
process ownership. Existing machine consumers must add `--json`.

## Implementation boundaries

A future implementation must format only an already validated `ClusterResult`,
use command-specific formatter functions or similarly narrow helpers, preserve
one request and one validation path, and add focused CLI tests for all three
successful modes and mutual exclusion.

It must not introduce a generic renderer, shared CLI-output framework,
formatter protocol, dependency, new core or transport model, `ClusterResult`
change, `/v1/chat` change, runtime-adapter change, routing/fallback change,
localization, colors, or TTY detection.

## Proof requirements

A later implementation proof must cover:

1. default content-only output;
2. default multiline and whitespace behavior;
3. final-newline behavior with and without an existing content newline;
4. verbose output and exact attribution order;
5. verbose output without model attribution;
6. `-v` alias behavior;
7. exact historical JSON preservation under `--json`;
8. representative Unicode JSON compatibility;
9. mutual exclusion before HTTP;
10. unchanged stable failures, stdout, stderr, and exit statuses;
11. one ordinary local live request; and
12. one ordinary explicit static-cluster live request.

The retained live evidence must contain no prompt, generated response, endpoint,
private address, raw exception, or credential. It may retain structural or
redacted response evidence only.
