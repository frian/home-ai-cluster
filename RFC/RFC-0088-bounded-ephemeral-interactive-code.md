# RFC-0088: Bounded Ephemeral Interactive Code

Status: Draft

Date: 2026-08-25

Author: frian

## Summary

This RFC proposes one minimal foreground interactive mode for the existing
native Code command. With neither a positional message nor `--message`, an
ordinary terminal invocation could enter one process-owned, ephemeral Code
conversation:

```text
hac code
```

Every submitted user turn would send all earlier successful user/assistant
messages plus the new user message in exactly one ordinary existing
`capability=code` request. A successful representable textual result would
become the next retained assistant message. The conversation would exist only
in the foreground CLI process and disappear when it exits.

Explicit-message forms remain one-shot:

```text
hac code "Write a Python script"
hac code --message "Write a Python script"
```

This proposal adds no server session, persistence, file access, execution,
shell authority, tools, agents, retries, or generic conversation framework. It
does not extend `code-file` or `aider`. It authorizes no implementation.

## Problem

RFC-0067 and RFC-0086 deliberately provide bounded, one-shot native Code
requests. They work for an isolated generation or transformation, but a later
correction such as “remove the Markdown” needs both the original instruction
and the prior free-form result to be meaningful. Requiring an operator to
reconstruct that context manually is possible but needlessly repetitive.

RFC-0083 establishes the same complete-context, ephemeral pattern for the
fixed loopback browser Code view, and RFC-0087 establishes a TTY-only
process-owned conversation for native Chat. A native Code lifecycle changes
input, retention, failure, and termination semantics, so it requires its own
explicit decision rather than being inferred from either prior RFC.

## Goals

This RFC proposes to:

* add one TTY-only `hac code` foreground conversation while preserving every
  explicit-message Code form;
* retain complete successful Code context only in ordinary process memory;
* send one ordinary independently routed native Code request per submitted
  turn, containing complete successful context;
* reuse RFC-0067's existing aggregate Code message-content bound;
* preserve text-only Code authority and existing safe native failures; and
* keep the lifecycle command-owned, small, local-first, privacy-first, and
  engine-independent.

## Non-goals

This RFC does not authorize an `--interactive` flag, stdin Code protocol,
prompt files, arbitrary roles, slash commands, a REPL framework, generic
interactive-capability framework, shared session framework, persistence, saved
transcripts/history, server sessions, conversation identifiers, background
services, or cross-process recovery.

It does not authorize interactive `code-file` or interactive `aider`. Those
commands have distinct file and subprocess authority and would require separate
consideration; this RFC does not pre-design their interaction shape.

It does not authorize sticky node/model/runtime/adapter affinity, model or
runtime selection, automatic execution, filesystem or repository access,
shell/Git/test/build invocation, tools or function calling, agents, planning
loops, retries, automatic result cleanup, Markdown stripping, code-fence
extraction, instruction removal, summarization, pruning, truncation, token
counting, context-window discovery, browser changes, OpenAI-compatible changes,
streaming, colors, spinners, progress bars, or a terminal UI framework.

## Proposal

### Invocation distinction

After a separate implementation, these remain ordinary one-shot native Code
invocations:

```text
hac code MESSAGE
hac code --message MESSAGE
home-ai-cluster code MESSAGE
home-ai-cluster code --message MESSAGE
```

They retain their existing parsing, 65,536-byte RFC-0067 bound, timeout,
presentation, error, privacy, routing, transport, and authority contracts.
Each validates one non-blank message, sends exactly one `capability=code`
request with one `user` message, and terminates. They must never enter
interactive mode.

Only an invocation with neither message form is a candidate for the new
lifecycle:

```text
hac code
```

Under RFC-0050 and RFC-0052, the root commands continue to forward their
remaining arguments unchanged to the existing Code command owner. No new
standalone executable, root parser behavior, or `--interactive` flag is added.

### TTY and existing options

No-message interactive entry requires exactly:

```python
sys.stdin.isatty() and sys.stdout.isatty()
```

If either condition is false, the command fails locally, returns non-zero, does
not read stdin, and does not construct or send a native request. `stderr` does
not determine eligibility and retains its ordinary error and foreground
presentation role. This does not create a piped or redirected stdin protocol.

`--timeout-seconds N` is valid with no message on eligible TTY streams. It
retains RFC-0060's existing validation and scalar timeout semantics, applying
independently to each submitted native request rather than terminal input or a
session-wide deadline.

The current Code `--json`, `--verbose`, and `-v` modes remain unchanged for
explicit-message one-shot requests. With no message, each is invalid local
input before any request. This proposal defines only ordinary content
presentation for the foreground conversation; it creates no interactive JSON,
verbose transcript, JSON Lines, event stream, or other machine-readable
presentation contract.

### Process-owned ephemeral state

One foreground CLI process owns one ordered sequence of successful Code
exchanges in ordinary process memory:

```text
user request 1
assistant Code result 1
user correction 2
assistant Code result 2
```

The retained assistant content is the exact successful prior free-form Code
result, including Markdown, prose, code fences, or usage instructions. The
CLI must not insert a system message, rewrite prior content, extract code,
strip prose, or otherwise transform messages.

The state belongs neither to the selected node, runtime, adapter, server, nor
transport. It creates no file, database, cookie, storage, prompt/response log,
request-history record, server session, conversation ID, daemon, or
cross-process state. RFC-0035 remains separate prompt-free operator history.

### Complete-context requests and routing

`ClusterRequest.messages` is already the existing ordered-message
representation used by RFC-0067. For each non-blank submitted turn, the CLI
would construct one candidate list from every retained successful `user`
message, every corresponding retained `assistant` result, and the new `user`
message. It would validate that candidate, then send exactly one ordinary native
request:

```text
POST /v1/chat
capability = code
messages = complete ordered candidate list
```

The command must not send only the latest correction, automatically issue a
correction or planning call, retry, execute generated text, inspect files, run
a shell command, call a tool, or start an agent loop.

Each turn remains an independent ordinary `capability=code` request. Existing
capability eligibility, local-first selection, declared topology order,
fallback, transport, and result attribution remain unchanged. A later eligible
node may receive earlier Code content only because the CLI includes it in that
ordinary request; there is no sticky routing or session ownership.

### Code aggregate bound

RFC-0067's existing 65,536 UTF-8-byte aggregate message-content bound applies
to the complete candidate on every turn. It includes all retained successful
user messages, all retained successful assistant results, and the new user
message. This proposal adds no second interactive Code bound and does not reuse
RFC-0087's separately command-owned Chat bound.

If the candidate exceeds RFC-0067's bound, the CLI rejects the new turn locally
before transmission, does not retain it, preserves all earlier successful
context, and keeps the loop active. It must not truncate, summarize, prune, or
use a rolling context window. A successful result can leave retained context
too large for any subsequent candidate; that result remains intact and a later
turn is simply rejected until the process ends.

### Success, representability, and failed turns

Only a successful representable user/assistant exchange becomes retained state.
A valid non-empty `ClusterResult.content` is retained exactly as the next
assistant `ChatMessage`, then ordinary content is presented.

As with RFC-0087, a structurally valid one-shot `ClusterResult` with
`content=""` remains a valid one-shot Code result with its existing output
contract. Interactive retained assistant turns must be existing non-empty
`ChatMessage` values. Therefore, an otherwise validated empty interactive
result fails at the local conversation boundary using the existing safe
invalid-cluster-response classification. The submitted user turn and assistant
turn are not retained, earlier successful context remains unchanged, no retry
occurs, and the loop continues. This does not change `ClusterResult`,
`ChatMessage`, a server response schema, or one-shot behavior.

For any other failed submitted turn—including local rejection, timeout,
transport failure, safe server failure, capability/runtime failure, or invalid
response—the CLI retains neither the new user turn nor a synthetic assistant
message, preserves earlier successful context, emits the existing safe Code CLI
failure, makes no automatic retry, and continues the foreground session unless
the operator terminates it.

### Blank input, termination, and presentation

Empty or whitespace-only terminal input is not a submitted Code turn. It sends
no request, changes no retained state, stores nothing, and leaves the loop
active. EOF (`Ctrl-D`) ends the foreground session normally; `Ctrl-C` ends it
cleanly without a traceback or persistence.

Simple prompts and ordinary textual result presentation are sufficient. An
implementation may provide a small static foreground indication that a request
was submitted, written outside result stdout, but exact glyphs and spacing are
implementation details. It must not introduce animation, cursor manipulation,
spinners, timers, colors, progress frameworks, or streaming simulation.

### Authority boundary

Interactive Code remains bounded textual generation, transformation, and
explanation under RFC-0067. It grants no authority to execute generated code,
read or write files, inspect a repository, run tests, invoke a shell, call
tools, modify a workspace, or act as an agent. Conversational presentation does
not expand that text-only authority.

## Rationale

One command-owned foreground loop is the smallest truthful way to make a Code
follow-up meaningful without claiming file-editing or agent authority. Sending
the complete retained list makes ownership explicit: short-lived CLI memory
owns context, while the existing native request continues to own validation,
routing, execution, and safe results.

RFC-0067 already supplies the capability-owned aggregate bound and shared
ordered-message representation, so a second model or interactive Code limit
would add artificial policy. Reusing failed-turn rollback for empty results
avoids widening shared models or creating a second retained-message
representation. Keeping free-form prior output exact lets the operator request
cleanup explicitly rather than introducing hidden transformations.

## Alternatives considered

### Keep native Code one-shot only

Rejected for this proposal. It remains correct for scripts and isolated work,
but requires operators to manually reconstruct context for small corrections.

### Use only the browser Code conversation

Rejected. RFC-0083 remains browser-only; it does not answer the bounded
foreground terminal workflow without a separate native lifecycle decision.

### Send only the latest correction

Rejected. It would present a conversation while withholding the prior request
and result needed to make the correction meaningful to an independently routed
node.

### Add execution, file editing, or Aider behavior

Rejected. Those introduce distinct filesystem, subprocess, and authority
boundaries. `code-file` and `aider` remain separate one-shot caller edges.

### Add a generic conversation framework

Rejected. One command-owned list and loop are sufficient evidence; future
symmetry is not justification for shared session infrastructure.

### Summarize, prune, strip Markdown, or extract code automatically

Rejected. Each silently changes operator or generated content and introduces
hidden policy, information loss, and output-shaping claims.

## Trade-offs

Later Code turns may be more expensive and can become non-sendable under the
existing bound. A later independently selected eligible node receives all
retained successful context. The operator must start a new process rather than
receiving automatic rolling history or cleanup. These costs are bounded by one
foreground process, ordinary memory, one request per turn, no persistence, and
unchanged text-only authority.

## Impact and implementation boundary

If accepted, a separate implementation PR may make small localized changes to
the existing Code command, focused tests, and concise operator documentation.
It must reuse existing native Code request/result, routing, transport, timeout,
and safe-error mechanics. It must not change core models, API routes, request
or result schemas, routing, topology, adapters, runtimes, transport, one-shot
Code output contracts, dependencies, browser behavior, OpenAI compatibility,
filesystem authority, shell authority, `code-file`, or `aider`.

## Later implementation proof expectations

A later implementation must demonstrate at minimum that:

1. positional and `--message` Code forms remain one-shot;
2. no-message interaction requires both stdin and stdout TTYs, while non-TTY
   invocation fails before reading or sending;
3. no-message JSON and verbose options fail locally while one-shot options are
   unchanged;
4. blank turns send nothing and keep the loop active;
5. the first valid turn sends one user message and a later successful turn sends
   complete successful user/assistant context plus the new correction;
6. prior assistant output is transmitted exactly, including prose or Markdown;
7. failed, timed-out, and empty-result turns roll back only their pending turn,
   preserve earlier context, send no retry, and leave the loop active;
8. RFC-0067's aggregate Code bound is enforced before transmission without
   modifying retained state, including when a prior valid result leaves a later
   candidate over-limit;
9. selected timeout applies independently per request, never to terminal input;
10. routing remains independent across turns;
11. EOF and Ctrl-C discard the ephemeral conversation; and
12. no execution, filesystem, shell, test, tool, agent, persistence,
    `code-file`, or `aider` authority appears.

Proof uses fake terminal and native HTTP seams only. Retained proof material
must contain no real prompts, generated code, private paths, addresses,
credentials, or runtime/model details.

## Open questions

Exact prompts, safe local error wording, blank-line spacing, and the narrow
test seam are implementation details. Whether simple static submission
indication is useful is a presentation choice, not a new protocol. No other
interactive capability, `code-file`, or `aider` behavior is proposed here.

## Decision

Pending.
