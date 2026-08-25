# RFC-0087: Bounded Ephemeral Interactive Chat

Status: Accepted

Date: 2026-08-25

Author: frian

## Summary

This RFC proposes one minimal foreground interactive mode for the existing
native Chat command. With no positional message and no `--message`, an
ordinary terminal invocation may enter one process-owned conversation:

```text
hac chat
```

Every submitted user turn sends one ordinary existing `capability=chat`
request containing all earlier successful user/assistant messages and the new
user message. A valid textual result becomes the next retained assistant
message. The conversation is held only in the foreground CLI process and
disappears when that process ends.

Existing one-shot forms remain exactly one request followed by termination:

```text
hac chat "Hello"
hac chat --message "Hello"
```

The proposal adds no server session, persistence, stdin message protocol,
sticky routing, retry, streaming, tools, agent behavior, or generic
conversation framework. It authorizes no implementation in this RFC PR.

## Problem

RFC-0045 and RFC-0053 deliberately define Chat as a one-shot ordinary native
client. The current implementation confirms that exactly one non-blank
positional message or one `--message` value is required, then one request is
sent and the command exits. That remains right for scripts and isolated
questions, but contextual terminal follow-up currently requires an operator to
reconstruct and resubmit prior context.

An interactive lifecycle changes input, state, failure, and termination
semantics. It must therefore be an explicit Chat CLI decision, rather than an
implementation convenience or an unstated extension of RFC-0045.

## Goals

This RFC proposes to:

* add one ordinary `hac chat` foreground interactive path only when it is safe
  to prompt an operator at a terminal;
* preserve positional and `--message` one-shot forms exactly;
* keep complete successful conversation context process-local and ephemeral;
* issue exactly one ordinary native Chat request for each submitted turn;
* preserve independent capability-centered routing for every turn;
* establish a fixed local aggregate message-content bound of 65,536 UTF-8
  bytes for interactive candidate requests;
* preserve privacy-first behavior by retaining no conversation outside process
  memory; and
* keep the later implementation command-owned and small.

## Non-goals

This RFC does not authorize stdin-as-message mode, piped conversation input,
prompt files, arbitrary message input, or an `--interactive` flag.

It does not authorize persistent conversations, saved history, server sessions,
databases, conversation identifiers, cookies, localStorage, browser storage,
multi-process recovery, synchronization, daemons, or background services.

It does not authorize sticky node, model, runtime, or adapter selection; tools
or function calling; agents; planning loops; retries; correction requests;
automatic summarization, pruning, truncation, token counting, or context-window
discovery.

It does not authorize slash commands such as `/clear`, `/save`, `/history`,
`/model`, or `/node`; terminal UI frameworks, color systems, Markdown
rendering, streaming, dashboards, or interactive editors.

Interactive Code, `code-file`, Aider, browser changes, OpenAI-compatible
changes, filesystem authority, shell execution, routing changes, transport
changes, and new dependencies are also outside this RFC.

## Proposal

### Exact invocation distinction

After a separate implementation, these remain ordinary one-shot native Chat
invocations:

```text
hac chat MESSAGE
hac chat --message MESSAGE
home-ai-cluster chat MESSAGE
home-ai-cluster chat --message MESSAGE
home-ai-cluster-chat MESSAGE
home-ai-cluster-chat --message MESSAGE
```

They retain their current parsing, request, timeout, output, error, privacy,
routing, transport, persistence, and lifecycle contracts. Each validates one
message, sends exactly one ordinary `POST /v1/chat` request with one `user`
message and `capability=chat`, then terminates. They must never enter
interactive mode.

Only an invocation with neither positional `MESSAGE` nor `--message` is a
candidate for the new lifecycle:

```text
hac chat
```

Under RFC-0050 and RFC-0052, root command aliases continue to forward their
remaining arguments unchanged to the existing Chat command owner. The
standalone Chat executable uses that same owner and has the same distinction.

### Existing option behavior

The existing timeout option is valid with no message:

```text
hac chat --timeout-seconds 300
```

RFC-0060 remains authoritative for validation and scalar timeout semantics. In
interactive mode, the selected timeout applies independently to each ordinary
native Chat request sent for a submitted user turn. It does not apply while the
foreground process waits for terminal user input and does not create a
session-wide deadline.

If one submitted turn times out, it follows the failed-turn rule in this RFC:
all earlier successful conversation state remains retained, the failed user
turn is not retained, no assistant message is appended, and no retry occurs.
The foreground interactive session continues unless the operator terminates it.

No-message interactive mode supports only ordinary content presentation. These
no-message forms are invalid local input:

```text
hac chat --json
hac chat --verbose
hac chat -v
```

They fail before any request. This RFC defines no interactive JSON, verbose
multi-turn output, event stream, JSON Lines, transcript envelope, or other
machine-readable interactive protocol. Keeping structured and verbose
presentation one-shot avoids creating a new interactive presentation or
automation contract.

The existing output options remain unchanged for one-shot invocations with one
positional message or exactly one `--message`; for example:

```text
hac chat "Hello" --json
hac chat --message "Hello" --json
hac chat "Hello" --verbose
```

### TTY and non-TTY behavior

No-message interactive entry requires both of these precise conditions:

```python
sys.stdin.isatty() and sys.stdout.isatty()
```

This is the smallest understandable testable condition: stdin must be an
ordinary terminal for operator input, and stdout must be an ordinary terminal
for the conversation presentation. `stderr` does not determine eligibility;
it retains its existing error role.

If either condition is false, no-message invocation fails locally before an
HTTP client is constructed or a request is sent. It must not block, read or
consume stdin, or infer a second input protocol. This includes piped or
redirected stdin and piped or redirected stdout. The exact safe error text and
implementation-level test seam are left to the implementation PR, but the
failure must be unambiguous, prompt-free, and non-zero.

No `--interactive` flag is introduced. The no-message terminal form is the
ordinary UX; scripts retain the explicit one-message forms.

### Process-owned ephemeral state

One foreground CLI process owns one ordered sequence of successful Chat
exchanges in ordinary process memory:

```text
user turn 1
assistant result 1
user turn 2
assistant result 2
```

The sequence contains only successful user messages and their corresponding
valid assistant textual results. It is not a cluster-wide conversation and is
not owned by the selected node, runtime, adapter, server, or transport.

The command creates no file, database, server-side session, cookie, browser
storage, persistent history, conversation identifier, cross-process state,
daemon, or background service. Process termination naturally discards the
conversation. RFC-0035's explicit, prompt-free request history remains separate
and must not gain user prompts, assistant results, or automatic interactive
records.

### Complete-context request behavior

For every submitted turn, the CLI constructs one ordinary existing
`ClusterRequest` with `capability=chat`. Its ordered `messages` list
contains:

1. every retained successful user message;
2. every corresponding retained successful assistant textual result; and
3. the new user message.

It sends exactly one ordinary native Chat request. The command must not send
only the latest prompt, invent a system message, transform prior content, or
issue retries, correction requests, planning turns, tools, function calls, or
agent loops. A valid `ClusterResult.content` becomes the next retained
assistant message and remains ordinary text.

An empty `ClusterResult.content` remains a valid ordinary one-shot Chat result
and retains its existing one-shot success and output behavior. Interactive
state has the stricter representability requirement that a retained assistant
turn must be an existing non-empty `ChatMessage`. Therefore, an otherwise
validated interactive result with empty content cannot become retained state:
the CLI treats that submitted turn as a local interactive-conversation failure,
reports the existing safe invalid-cluster-response classification, retains
neither the submitted user turn nor an assistant turn, preserves earlier
successful exchanges, performs no retry, and keeps the foreground session
running. This narrow rule does not change `ClusterResult`, `ChatMessage`, a
server response schema, or one-shot Chat behavior.

### Blank interactive turns

A terminal input containing no characters or only whitespace is not a submitted
Chat turn. The CLI rejects it locally, sends no native request, stores no input,
leaves the retained successful conversation unchanged, and keeps the
interactive session running for another terminal input. Exact prompt and error
wording remain implementation details.

### Routing remains stateless

Every interactive turn is an independent ordinary Chat request. Existing
routing may select a different eligible node for a later turn. There is no
sticky session, node affinity, conversation ownership by a node, model
affinity, runtime affinity, or server session state.

A later selected node receives earlier context only because the CLI includes the
complete retained successful message list in that new ordinary request. Existing
local-first selection, declared topology, capability eligibility, fallback,
transport, and result attribution remain unchanged.

### Failure behavior

Only a successful user/assistant exchange becomes retained state. If a
submitted turn fails locally, at transport, through an ordinary safe server
failure, or through invalid result validation, the command preserves all prior
successful exchanges, appends no synthetic assistant message, and sends no
automatic retry or correction request. The failed user text is not retained as
conversation state.

For this interactive lifecycle, an otherwise validated result with empty
content is also a failed turn because it cannot be represented as the retained
assistant `ChatMessage`. It uses the existing safe invalid-cluster-response
classification; it does not alter ordinary one-shot result validation or
presentation.

The implementation may leave exact prompt redisplay wording to its focused
terminal design, provided it remains foreground-owned and does not transform
the retained successful conversation or create persistence.

### Aggregate bound

Interactive Chat has one command-owned candidate-request bound:

```text
65,536 UTF-8 bytes aggregate message content
```

Before sending a new user turn, the CLI calculates the UTF-8 byte length of the
content of every retained successful user message, every retained successful
assistant result, and the new user message. If their aggregate exceeds 65,536
bytes, it rejects that new turn locally, sends no request, keeps the prior
successful conversation unchanged, and does not truncate, summarize, or
automatically prune any content.

This is an interactive CLI ownership bound, not a new general Chat capability
or one-shot Chat bound. It does not alter existing one-shot input validation. A
valid assistant response may leave retained conversation content too large for
any later candidate turn. That response remains retained unchanged; a later
turn is simply refused until the operator ends the process and begins a fresh
session. The proposal adds no token counting, context-window discovery, output
bound, rolling window, or hidden history policy.

### Termination and presentation

EOF (`Ctrl-D`) ends the interactive session normally. `Ctrl-C` ends the
foreground interactive session cleanly without persistence. Neither outcome
starts a daemon, leaves a reconnectable session, or attempts to preserve
conversation state.

The terminal presentation is deliberately small. A later implementation may use
simple operator and assistant prompts and ordinary content result text. It must
not introduce curses, Rich, a color system, Markdown rendering, streaming, a
dashboard, an interactive editor, or structured/verbose multi-turn output.
Exact prompts and spacing are implementation details unless they become an
explicit automation contract.

### Privacy and persistence boundary

Interactive text follows the existing ordinary native request path and does not
change where Chat requests are routed. The new CLI state exists only in memory
for the foreground process. It must not log, persist, export, or otherwise
retain prompt or result content because of this lifecycle. Ordinary terminal,
shell, operating-system, or redirection behavior remains outside the project's
persistence control; the TTY requirement prevents this lifecycle from creating
a piped transcript protocol.

### Relationship to prior RFCs

This RFC narrowly amends the no-message portion of RFC-0045 and RFC-0053.
Those RFCs deliberately establish one-shot Chat input; their accepted
positional and `--message` forms remain unchanged. The amendment is exactly
one TTY-only no-message foreground lifecycle, not a reinterpretation of either
message form.

RFC-0049 remains authoritative for one-shot Chat success presentation.
RFC-0050 and RFC-0052 remain authoritative for root and installed alias
ownership. RFC-0055 and RFC-0060 remain authoritative for the ordinary native
client timeout and timeout override; this RFC applies RFC-0060's selected
per-request timeout to each submitted interactive turn, not terminal input.
RFC-0062 remains browser-specific and is unchanged. RFC-0035 remains the
separate explicit prompt-free local history.

RFC-0083 is the architectural precedent for client-owned ephemeral ordered
conversation, complete successful context on every independently routed turn,
failure rollback, and rejection rather than hidden truncation or summarization.
This RFC does not copy Code-specific browser semantics or RFC-0067's Code
bound; it defines one narrow Chat CLI contract with its own explicit
65,536-byte interactive bound.

## Rationale

One process-owned loop is the smallest truthful way to make a terminal Chat
follow-up meaningful without asking the operator to paste already available
context. Sending the complete retained list makes ownership visible: the CLI
owns short-lived context, while the existing ordinary request remains
responsible for validation, routing, execution, and results.

The two-stream TTY check prevents `hac chat` from ambiguously blocking in
automation or consuming data intended for another program. The fixed byte bound
preserves a finite operator-owned limit without pretending to know every
engine's tokenization or context window. Reusing the existing timeout only for
each native request preserves its ordinary client boundary without imposing a
deadline on operator thought or terminal input. Restricting interactive output
to ordinary content avoids turning a human foreground loop into a second
machine-readable protocol.

The existing models deliberately allow an empty normalized result while
requiring a non-empty retained `ChatMessage`. Widening that shared message model
for one CLI edge would alter a broader contract, while creating a second
retained-message representation would add needless lifecycle complexity. The
existing failed-turn rollback is the smallest consistent behavior: it adds no
fake assistant content, silent insertion, persistence, or schema change.

## Alternatives considered

### Keep Chat one-shot only

Rejected for this proposal. It remains valid for scripts and isolated requests,
but does not provide a minimal terminal follow-up path.

### Read no-message turns from stdin

Rejected. It creates blocking, pipe, delimiter, EOF, input-source, and
automation semantics beyond one ordinary terminal conversation.

### Add an `--interactive` flag

Rejected. No-message terminal invocation is understandable without a second
mode selector, while explicit message forms already preserve scripting intent.

### Use server-owned or persistent sessions

Rejected. They require identity, lifecycle, retention, privacy, recovery, and
concurrency decisions not needed for one foreground process.

### Send only the latest user message

Rejected. It would show a conversation without supplying earlier context to an
independently selected eligible node.

### Use sticky routing

Rejected. It would change stateless capability-centered routing and would not
remove the need for an explicit state ownership contract.

### Summarize, truncate, or prune old turns automatically

Rejected. Each silently changes operator content and introduces information-loss
and policy decisions. Clear local refusal is smaller.

### Generic conversation or REPL framework

Rejected. One command-owned loop and ordinary in-memory data are sufficient;
future symmetry is not evidence for a framework.

## Trade-offs

Later turns may grow more expensive and can reach the fixed aggregate bound. An
eligible later node receives prior Chat content as part of the newly sent
ordinary request. A successful large result can naturally end the session's
ability to accept another turn. The operator must start a new session rather
than receiving an automatic rolling history.

These costs remain bounded by one foreground process, one explicit local byte
calculation, one ordinary request per turn, no persistence, and unchanged
routing. They are smaller and clearer than server sessions, hidden context
management, or an agent loop.

## Impact and implementation boundary

Acceptance would authorize only a later separate implementation PR. It may make
small localized changes to `chat_command.py`, its focused tests, and necessary
operator documentation. It should use one command-owned loop and ordinary
in-memory ordered messages, not a generic session manager, conversation
abstraction, reusable interaction engine, storage layer, or CLI framework.

It must not change core models, API routes, native request/result schemas,
routing, topology, adapters, runtimes, transport, timeout semantics, output
contracts for existing one-shot forms, executable aliases, dependencies,
browser behavior, OpenAI compatibility, filesystem authority, or shell
authority.

## Later implementation proof expectations

A later implementation must demonstrate at minimum that:

1. positional and `--message` one-shot forms retain one request and terminate;
2. no-message invocation enters one interactive loop only when stdin and stdout
   are TTYs;
3. every non-TTY no-message form fails before reading stdin or sending a
   request;
4. `hac chat --timeout-seconds N` enters interactive mode on eligible TTY
   streams and applies the selected RFC-0060 timeout independently to each
   submitted native request, while waiting for user input is not governed by
   that timeout;
5. no-message `--json`, `--verbose`, and `-v` each fail locally before any
   request, while those output flags remain unchanged on one-shot message
   invocations;
6. blank and whitespace-only terminal input sends no request, changes no
   retained state, stores no input, and leaves the loop active;
7. the first and later successful turns send one ordinary `capability=chat`
   request each, with later lists containing complete successful context;
8. successful turns are retained in chronological user/assistant order;
9. every failed turn, including a timeout, retains neither its user text nor a
   synthetic assistant message, continues the foreground session unless the
   operator terminates it, and preserves earlier successful exchanges;
10. an interactive native response with a structurally valid `ClusterResult`
    and `content=""` reports the safe invalid-cluster-response failure, retains
    neither the submitted user turn nor an assistant turn, preserves earlier
    successful context, continues the loop, and sends no automatic retry;
    one-shot empty-result behavior remains unchanged;
11. independent routing remains non-sticky across turns;
12. the aggregate calculation includes retained assistant results and rejects an
   over-limit candidate before network transmission without modifying state;
13. a successful oversized assistant result remains intact even if it prevents a
   later turn;
14. EOF and Ctrl-C end the foreground session without persistence; and
15. no stdin protocol, file, database, session, conversation ID, daemon,
   history expansion, retry, summary, pruning, token counting, tools, agents,
   streaming, filesystem, shell, browser, or compatibility behavior appears.

Retained proof material must contain no real prompts, generated content,
private addresses, model/runtime details, credentials, or raw exceptions.

## Open questions

Exact prompt strings, blank-line spacing, safe non-TTY error wording, and the
small test seam for terminal streams are implementation details. They must not
expand this proposal into a second input protocol, terminal UI contract, or
session framework.

## Decision

Accepted.

RFC-0087 accepts one TTY-only foreground interactive lifecycle for native Chat
when neither a positional message nor --message is supplied. Existing
positional and --message forms remain unchanged one-shot commands. Interactive
eligibility requires both sys.stdin.isatty() and sys.stdout.isatty(); a
non-TTY no-message invocation fails locally without reading stdin or sending a
request.

--timeout-seconds N is valid in interactive mode and applies independently to
each submitted ordinary native request, never to terminal input waiting and
never as a session-wide deadline. No-message --json, --verbose, and -v are
invalid local input, while those output modes remain unchanged for one-shot
message forms. Blank or whitespace-only interactive input sends no request,
changes no retained state, is not stored, and leaves the session running.

Successful conversation state belongs only to the foreground CLI process and
exists only in memory. Each submitted turn sends one ordinary native
capability=chat request containing the complete retained successful
user/assistant context plus the new user message. Only successful
user/assistant exchanges are retained; failed turns are not retained or
automatically retried. Routing remains independent and stateless across turns,
with no sticky node, model, runtime, or session ownership.

An otherwise validated interactive `ClusterResult` with empty content is a
failed turn because the existing retained assistant `ChatMessage` contract is
non-empty. It reports the existing safe invalid-cluster-response classification,
retains neither turn, preserves earlier successful context, performs no retry,
and leaves the session active. This is interactive-only: one-shot empty-result
behavior remains unchanged, and this decision changes neither core model nor
server response schema.

The interactive candidate request is bounded to 65,536 aggregate UTF-8 bytes of
message content. Over-limit candidates are rejected locally without
truncation, summarization, pruning, or state mutation. EOF / Ctrl-D and Ctrl-C
terminate the foreground session without persistence.

This decision accepts no stdin message protocol, persistent conversation, saved
history, server session, database, conversation ID, slash commands, tools,
agent loop, streaming, generic conversation framework, browser change,
Code/Aider change, filesystem authority, or shell authority. Implementation is
authorized only in a later separate implementation PR.
