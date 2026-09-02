# Phase 17 Ordinary Request Input Investigation

Status: Complete

## Question

What is the smallest privacy-bounded ordinary request input contract that avoids
requiring the operator message to appear in the command-line argument list while
preserving the one-shot ordinary request boundary?

## Scope

This is an investigation of possible future input contracts for one ordinary
request. It does not accept an input source, change `home-ai-cluster-chat`, or
change [RFC-0045](../RFC/RFC-0045-one-shot-ordinary-request-command.md).

The technical objective remains:

> Fake in distribution, but not fake in architecture.

The ordinary running process remains the sole owner of routing, fallback,
topology, runtime selection, node attribution, and cluster failures. An input
mechanism can only acquire one operator message locally, validate it, and pass
the existing request to that process. It must not become a client-side router,
fallback mechanism, process manager, or general input framework.

## Current accepted contract

Phase 16 accepted and implemented this command:

```sh
home-ai-cluster-chat --message "<MESSAGE>"
```

It accepts exactly one required `--message` option, rejects empty or
whitespace-only input, and preserves an otherwise valid value. It constructs
exactly one `user` message with the fixed `chat` capability and performs exactly
one request to the fixed native endpoint:

```text
POST http://127.0.0.1:8000/v1/chat
```

The client does not start or inspect the cluster, and remains topology-blind. It
validates a complete `ClusterResult`, writes compact JSON on success, writes
stable safe errors to standard error on failure, and exits after one request. It
has no retry, client fallback, session, or history. The implementation and its
focused tests confirm that boundary in
[`chat_command.py`](../src/home_ai_cluster/commands/chat_command.py) and
[`test_chat_command.py`](../tests/test_chat_command.py).

RFC-0045 explicitly excludes standard input, prompt files, and interactive
prompting. Its accepted contract therefore remains authoritative unless a later
RFC changes it. The Phase 16 investigation, proof, and closeout provide the
operator and privacy context for this investigation: [investigation](phase-16-ordinary-operator-request-access-investigation.md),
[proof](phase-16-ordinary-request-access-proof.md), and
[closeout](phase-16-closeout.md).

## Concrete privacy limitation

`--message` is not a secure secret-input mechanism. Its concrete limitation is
that command arguments can be retained in shell history and can be visible
through local process inspection. This is a meaningful reason to investigate a
narrow alternative, but it is not evidence that any particular alternative is
secure.

The ownership boundary matters:

| Surface | Ownership and implication |
| --- | --- |
| Home AI Cluster | The command must not log or persist the message or response. It can control that it creates no request history or input file. |
| Shell history | A shell may retain command arguments or constructs used to produce input. This is outside the client’s control. |
| Process arguments | Local users, processes, or operating-system tooling may observe an argument while the process runs. Removing the content from `argv` reduces this particular exposure. |
| Terminal capture | Scrollback, recording, terminal multiplexers, clipboard managers, or remote-terminal services may retain visible input or output. |
| Redirection and pipelines | A shell, producing command, pipe endpoint, redirection target, or wrapper can retain or expose content. |
| Operating system or third parties | Auditing, endpoint tools, backup systems, malware, or other local observers may see data independently of the chosen client source. |

Consequently, an alternative source can improve a specific exposure path without
being a universal confidentiality guarantee. It must not imply secure secret
handling that Home AI Cluster does not provide.

## Evaluation criteria

The options below are assessed against a small common set of criteria:

- realistic privacy improvement and its limits;
- clarity of exactly-one-message, one-shot semantics;
- ordinary terminal, script, pipeline, and multiline usability;
- accidental-blocking and persistence risk;
- portability, testability, and bounded implementation complexity;
- compatibility cost and the amount of new project authority; and
- preservation of the existing success output and process-owned failure
  boundary.

## Options investigated

### Keep `--message`

Keeping the accepted option is the simplest and most explicit contract. It is
easy to invoke, script, test, and explain; it preserves exact compatibility,
requires no new source selection or decoding policy, and adds no contract
authority. It already supports multiline values when the shell can pass one
argument, although shell quoting then becomes operator-owned.

It also retains the documented shell-history and process-argument limitation.
Documentation makes that limitation visible, but cannot remove it. It remains
appropriate when an operator has no demonstrated need beyond one ordinary,
non-secret command argument. Empty and whitespace-only values continue to fail
locally before HTTP. There is no accidental read blocking, file persistence, or
terminal-detection concern.

This option preserves RFC-0045 unchanged. It does not answer every possible
privacy concern, but it avoids treating a theoretical alternative as a new
default without a concrete operator workflow to justify it.

### Read one message from standard input

Standard input removes message content from the ordinary command arguments. It
is natural for shell scripts, generators, and pipelines, and it can carry
multiline text without shell argument quoting. A deliberately narrow contract
could define one complete message as the decoded bytes read until EOF, then make
one HTTP request or fail locally. EOF is clear for a finite pipe or redirected
file, but has different usability and blocking behavior for a terminal.

Piped and terminal stdin must not be treated as equivalent. A finite producing
command normally supplies EOF; a terminal may wait indefinitely for an EOF
gesture, and a pipe can also block if its producer does not close. This creates
a real accidental-blocking decision. A command that silently reads terminal
stdin when `--message` is absent could unexpectedly wait; requiring an explicit
source selection avoids that surprise but adds a new option and contract.

Trailing-newline handling is also visible semantics. Reading to EOF preserves
the bytes after decoding, including final newlines; stripping a final newline
would alter a message. A future RFC would need to state whether the existing
non-whitespace validation is applied to the whole decoded message without
normalization. It must also define the encoding and invalid-byte behavior rather
than letting platform defaults become the contract.

Stdin is not universally secure. `echo "secret" | ...`, command substitution,
shell variables, producing commands, terminal tools, pipe readers, and
redirection targets may still expose or retain content. It eliminates ordinary
argument visibility for the receiving client, not the wider surrounding-system
risks.

For scripts and pipelines, a finite EOF-delimited value is explainable and
testable. For an interactive terminal, it is less obvious than a prompt. A
future contract would also need an explicit policy for terminal versus
non-terminal stdin, empty input, whitespace-only input, decode failure, read
failure, and input that exceeds a fixed bound. It would be compatible with the
existing one-shot request and output contracts after local acquisition succeeds,
but it requires an RFC amendment or a new RFC because RFC-0045 prohibits it.

### Read one explicitly supplied file

An explicit file can avoid putting message content directly in the client
argument list, while leaving the path visible in arguments. It supports
multiline content and reproducible scripts, but turns prompt files into a
durable operator contract and makes the message persistent local state outside
Home AI Cluster until the operator removes it.

That persistence is substantial for a privacy-first default. Ownership,
permissions, backups, synchronization, filesystem encryption, and cleanup are
operator or operating-system concerns. A future contract would have to decide
how to handle unreadable files, ownership and permission checks, invalid text
encoding, read errors, file size, symbolic links, device files, named pipes,
directories, and other special files. Following a symlink or accepting a FIFO
can unexpectedly change both the data source and blocking behavior.

Automatic deletion, temporary-file creation, permission repair, or file
management would add new lifecycle and data-ownership responsibilities; none is
appropriate to infer here. An explicitly supplied path is testable and portable
only after those details are specified, and it adds failure modes that the
current command does not own.

File input can still represent exactly one message when the complete decoded
file content is the message, but a durable file format may invite multiple
messages or conversational transcripts. It must remain a plain, single-message
source if ever considered. This option requires a new RFC or RFC-0045 amendment
and has a higher persistence and long-term compatibility cost than the other
options.

### Read one message interactively

An interactive prompt can be pleasant for an ordinary terminal user and keeps
the message out of the command argument list. It is not a script or pipeline
interface, however, and it requires reliable terminal detection, cancellation,
EOF, non-interactive failure, and multiline termination rules. An ordinary
single-line prompt has simple termination but does not support natural multiline
input; a sentinel or editor-like interaction would create additional syntax and
state decisions.

Visible prompt text and password-style hidden input are different contracts.
Ordinary AI prompts are not automatically secrets, and hidden input can reduce
operator feedback while still not protecting against terminal recording or
operating-system observation. Choosing either behavior must be explicit, not
assumed from the word “privacy.”

An interactive prompt also changes the present non-interactive one-shot
character: it may wait for a terminal user and cannot be usefully consumed by
ordinary pipes and scripts. It is testable through injected terminal behavior,
but that increases portability and test complexity. It requires an RFC amendment
or new RFC and is not a small undisclosed implementation detail.

### Multiple input sources

A limited combination, such as retaining `--message` and adding one explicitly
selected alternative, is possible only if a future RFC defines mutual exclusion,
source selection, conflict errors, and one common validation boundary. Inference
such as “use stdin whenever `--message` is absent” is convenient but creates
ambiguity and accidental terminal blocking. Precedence rules such as “the
argument wins” can silently discard intended input.

Supporting every source for convenience would create a generic input abstraction
and accumulating compatibility obligations. That is outside this investigation.
Any combination should remain a deliberate, minimal operator contract rather
than a collection of loosely related ways to provide content.

## Comparison summary

| Option | One-message and ordinary use | Privacy and persistence | Validation, limits, and operational risk | Compatibility and testability |
| --- | --- | --- | --- | --- |
| `--message` only | One shell argument is explicit; shell quoting governs multiline values; it never waits for input. | The content can be in shell history and process arguments, but Home AI Cluster adds no file. | Existing local missing, duplicate, empty, and whitespace-only validation applies; decoding and size are ordinary argument/platform behavior. | Preserves RFC-0045 with the smallest, already focused test surface. |
| EOF-delimited stdin | Natural for finite scripts and pipelines; terminal stdin needs an EOF policy and can block. Preserving decoded content retains multiline and trailing newlines. | Removes content from the receiving command's arguments, but producers, pipes, shell constructs, terminal tools, and redirection may retain it; no file is required. | Needs explicit text decoding, read-failure, EOF, whitespace, and finite-size rules before HTTP. | Requires an RFC change; pipes and terminal/non-terminal cases are portable only with focused tests. |
| Explicit file | Complete decoded file content can be one multiline message; regular files are scriptable, while special files can wait. | The path is visible; content persists until the operator removes it and may be copied or backed up. Ownership, permissions, symlinks, and temporary files matter. | Needs regular-versus-special-file, decoding, unreadable-file, size, and cleanup-ownership rules. | Requires an RFC change and a durable file-input test matrix across supported platforms. |
| Interactive input | Convenient only for an operator at a terminal; multiline termination, cancellation, EOF, and non-terminal behavior need definition. | No message argument or required file, but visible input, hidden input, terminal capture, and operating-system observation remain distinct risks. | Needs terminal encoding, bounded input, cancellation, and unavailable-terminal errors before HTTP. | Requires an RFC change and terminal-aware tests; it is less portable for automation. |

## Pipes, scripts, and terminal behavior

The current argument option is predictable for a one-line shell invocation and
for scripts that can pass a string argument. It does not wait for external
input. It has ordinary argument exposure and shell-quoting limitations.

EOF-delimited stdin is strongest for a pipeline or redirected finite producer:
the producer supplies bytes, closes the stream, and the client has one complete
message. It must not turn a missing producer or a live terminal into an
unbounded wait without an explicitly accepted policy. It also does not remove
the risk created by the producer, shell constructs, or redirection used to
supply the text.

File input is scriptable and does not block for a regular, readable file, but
special files can behave like streams. Interactive input serves a terminal only;
it must fail safely rather than prompt when standard input is non-terminal. None
of these choices changes the existing output rule: once one valid message is
acquired, the command sends one request and emits one complete normalized result
or one safe error.

## Input validation, errors, and size limits

Input acquisition belongs before the HTTP request. No source-specific local
failure should cause a request, retry, topology inspection, or client fallback.
The existing command already establishes local rejection of missing, duplicate,
empty, and whitespace-only `--message` input. A future source contract would
need similarly small, stable categories for:

- no source selected;
- more than one source selected;
- empty or whitespace-only content;
- input exceeding a finite bound;
- stdin read or decoding failure;
- unreadable, invalid, or unsupported file input; and
- terminal cancellation, EOF, or unavailable terminal input.

The precise strings and exit mapping should be decided with the future contract,
not invented in this investigation. They should be prompt-free and should not
expose paths, raw decoder errors, or operating-system details.

The existing core message model requires non-empty content but has no visible
maximum-length field. Reading an unbounded pipe or file before constructing that
model can consume unbounded memory, so a new source creates a size-bound
question. Leaving the current behavior without a new explicit bound has the
lowest compatibility cost but does not protect acquisition from unexpectedly
large input. One fixed implementation-owned bound is easier to explain and
test than a configurable bound, but changes what previously valid large inputs
mean. A configurable bound adds configuration, precedence, and support
obligations with no demonstrated need. This is an RFC-level policy question if
an alternative source is pursued.

## Compatibility with RFC-0045

| Outcome | RFC-0045 compatibility |
| --- | --- |
| Keep `--message` only | Preserves RFC-0045 unchanged. |
| Accept stdin | Requires a new RFC or an amendment that changes the accepted message-input and privacy contract. |
| Accept an explicit file | Requires a new RFC or an amendment; it creates a durable prompt-file operator contract and file-boundary rules. |
| Accept interactive input | Requires a new RFC or an amendment; it changes non-interactive one-shot behavior and terminal ownership. |
| Accept multiple sources | Requires a new RFC or an amendment defining source selection, conflicts, and compatibility. |

The accepted RFC specifically requires exactly one `--message` option and
prohibits stdin, files, and interactive prompting. Implementing any of those
sources would therefore be an operator-contract and privacy-boundary change,
not an undocumented implementation detail.

## Architectural assessment

The request transport, fixed endpoint, fixed `chat` capability, normalized
result, output, and process ownership need not change for any option. The input
source nevertheless affects a durable ordinary-client interface, local data
handling, privacy claims, termination semantics, error compatibility, and
possibly resource limits. Those are architectural and long-term compatibility
decisions under the repository RFC process.

No option investigated justifies sessions, history, streaming, tools,
multimodal input, a new endpoint, client-side routing or fallback, a general
SDK, generic CLI/input abstraction, discovery, supervision, dashboard,
database, Docker, or Kubernetes. Runtime and topology remain outside the
ordinary client input boundary.

## Recommendation

Defer an input-contract change until a concrete operator need distinguishes the
privacy benefit and workflow from the already accepted `--message` command.
Keep `--message` as the only accepted source for now.

This is evidence-based rather than a judgment that argument exposure is
unimportant: Phase 16 documents the limitation clearly, while this investigation
shows that stdin, file, and interactive input each introduce material ownership
and compatibility decisions. No repository evidence establishes that one
alternative’s trade-offs are warranted yet. Documentation of the current
limitation should remain accurate; it does not make the current interface a
secret-entry mechanism.

If a demonstrated need later supports one alternative, investigate and accept a
small RFC before implementation. The RFC should state whether `--message`
remains supported; whether sources are mutually exclusive and explicitly
selected; the one-message termination rule; the realistic privacy improvement
and its limits; source-specific validation and bounded-size behavior; and the
continued exclusions below. It should not broaden into “support every source.”

## Proposed next step

Collect a concrete, privacy-safe operator scenario that the current command
cannot meet, including whether it is a finite script or pipeline workflow, an
ordinary terminal workflow, or an operator-managed durable file workflow. Then
write a focused RFC only if that scenario justifies a particular source and its
new authority. Until then, no implementation, CLI, roadmap, or RFC change is
needed.

## Non-goals retained

This investigation does not add or decide sessions, conversation history,
streaming, tools, multimodal input, arbitrary roles or message arrays, a new
endpoint, OpenAI-compatible expansion, a generic SDK, a generic CLI or input
abstraction, client routing or fallback, topology inspection, process startup
or supervision, discovery, dashboard, database, Docker, Kubernetes, automatic
file deletion, or secure-secret-input guarantees.
