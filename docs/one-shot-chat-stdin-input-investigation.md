# One-shot Chat Standard-Input Investigation

## Status

Investigation only. This document establishes no accepted command behavior,
does not amend RFC-0045 or RFC-0049, and authorizes neither an implementation
nor a test change. It records the current repository state and the retained
operator evidence relevant to one possible input source.

## Question and current evidence

Should `home-ai-cluster-chat` accept exactly one user message from standard
input without changing its request, execution, output, failure, routing,
topology, runtime, lifecycle, or persistence boundaries?

The answer is not selected in advance. The repository already contains the
closely related Phase 16 ordinary operator request access investigation. It
found a real limitation of command arguments, but no concrete operator workflow
sufficient to choose stdin over the accepted argument contract. The later
RFC-0049 work changed successful output presentation only; its accepted
non-goals expressly exclude input modes. Its proof covers the existing
`--message` client in its three output modes, not standard input. No later
retained proof or README workflow supplies a new stdin-specific operator need.

## Current accepted contract

RFC-0045 remains authoritative for command input. One invocation accepts
exactly one required `--message <MESSAGE>` value. It must contain
non-whitespace content and is otherwise preserved as supplied. There is no
positional message, standard input, prompt file, interactive prompting,
multiple messages, arbitrary role, system message, or session input.

The command constructs exactly one `user` message and fixed `chat` capability,
then makes exactly one `POST http://127.0.0.1:8000/v1/chat` request to an
already running ordinary process. The endpoint is fixed loopback-native; there
is no host, port, topology, node, runtime, adapter, model, capability,
configuration, discovery, startup, retry, or client-side fallback option. It
retains no state or persistence.

RFC-0049 replaces only the successful-output presentation rules originally
defined by RFC-0045. It does not alter the input contract: default success
writes content with the specified terminal-newline rule, `-v`/`--verbose`
writes content and truthful attribution, and `--json` preserves the historical
complete compact
`ClusterResult` representation. Selection is explicit and output options are
mutually exclusive. It does not alter request construction, one-request
execution, response validation, failure streams, exit statuses, or the stable
failure categories. Invalid local input still writes only
`error: invalid request input` to stderr and exits 2; operational and response
failures still write no stdout and use their existing prompt-free safe stderr
line with non-zero exit.

Thus RFC-0045 is the original one-shot input/execution contract and RFC-0049 is
a later, output-only amendment. Neither accepts stdin.

## Observed friction and its ownership

The accepted command shape is easy to understand and never waits for input:

```sh
home-ai-cluster-chat --message "<MESSAGE>"
```

Its documented limitations are concrete. Message text can be retained in shell
history and can be visible through local process inspection while it is an
argument. Multiline content and Markdown can require awkward shell quoting.
Quotes, code, `$`, backticks, and newlines are governed by the selected shell's
escaping rules. Generated or repeated local text can require command
substitution, a shell variable, or a wrapper before it can become one argument.
Ordinary pipelines are also less direct than sending a finite producer's output
to a consumer.

These are mostly shell and operating-system limitations, not evidence of a
cluster, routing, adapter, or HTTP problem. The retained Phase 16 proof and
later remote-request proof show the one-shot client functioning through its
ordinary process boundary; neither records an input-source failure. The
repository has no retained, privacy-safe report that a specific pipeline,
multiline workflow, or generated-input workflow cannot reasonably use the
current command.

Stdin would remove the message from the receiving command's ordinary argument
list and naturally carry EOF-delimited multiline output from a finite local
producer. It would not make input secure: the producer, shell history or
substitution, terminal scrollback or recording, clipboard manager, pipe,
redirection, file, operating system, auditing software, and other local tools
may still expose or retain it. It is neither authentication, encryption, a
protected secret-entry mechanism, nor a guarantee of non-retention. It is best
understood as potential shell ergonomics plus a limited reduction in one
argument-exposure path.

## Current implementation seam

`chat_command.py` parses `--message` with a private `argparse` subclass so all
parser failures reach the stable invalid-input category. It requires one value,
rejects empty or whitespace-only text, and preserves a valid value. It then
builds the existing `ClusterRequest` containing one `ChatMessage(role="user",
content=message)` and `Capability(name="chat")`, projects the native request,
and makes one `httpx.Client` request with the existing fixed URL, timeout, and
redirect policy. It maps transport and HTTP failures before validating a 2xx
JSON body as the authoritative `ClusterResult`; RFC-0049 formatting occurs only
after that validation.

This leaves a theoretical narrow CLI-edge seam: an input source could acquire
one text string before the existing validation and request construction path,
then use the unchanged string as the existing message. That observation is not
permission to do so. The parser's required `--message`, its no-positional
behavior, the invalid-input tests, and RFC-0045's explicit stdin exclusion are
accepted operator behavior.

The implementation risks are correspondingly local but material: changing a
required parser option can change no-option behavior; reading `sys.stdin` can
block; decoding and read errors need safe local classification; any trimming
could mutate content; mixed sources need conflict rules; and an unbounded read
can impose a new resource policy. None should leak into the HTTP, result,
formatter, output-mode, routing, topology, runtime, lifecycle, or persistence
boundaries.

Focused tests currently protect missing, duplicate, empty, whitespace-only, and
unknown arguments; no HTTP for invalid input; one exact native request with
preserved message whitespace; all RFC-0049 success modes; output-option
exclusivity; and stable failure mappings. `pyproject.toml` declares the command
as the `home_ai_cluster.chat_command:main` console script. README guidance also
shows only `--message`.

## Candidate input contracts

| Candidate | Assessment |
| --- | --- |
| Keep required `--message` only | Explicit, immediately failing when omitted, compatible, discoverable, portable, and lowest-maintenance. Shell quoting and argument exposure remain operator-owned. |
| Read stdin when `--message` is absent | Convenient in a pipe, but ambiguous for a terminal and can accidentally block. TTY detection would add hidden environment-dependent behavior. It changes the required-option contract and has poor discoverability. |
| Add explicit `--stdin` | Clear source selection and compatible with retaining `--message` if mutually exclusive. It avoids implicit terminal reads and makes pipeline use discoverable, but adds a durable option, decoding/EOF/error policy, and test surface. |
| Treat `--message -` as stdin | Compact for users familiar with some Unix tools, but overloads a valid literal message, is less discoverable, and creates escaping and cross-platform ambiguity. It also makes a future literal `-` compatibility concern. |
| Add a positional message | More concise in some shells but violates the accepted no-positional contract, conflicts with option parsing and multiline ergonomics, and does not improve argument exposure. |
| Add `--file` | Explicit and scriptable, but makes prompt-file handling a durable contract with persistence, permissions, path, special-file, cleanup, and backup implications. It is a separate question, not a companion feature for stdin. |
| Shell substitution, aliases, functions, or external one-off wrappers | Keeps the public command contract small and lets operators choose local ergonomics. Substitution still has shell exposure and quoting considerations; a wrapper must not be represented as project-supported secure input. |

Feature count is not a benefit here. The current contract is the only candidate
already accepted. If new evidence later justifies stdin, explicit selection is
clearer than an implicit fallback, but choosing it would still require an RFC
decision rather than implementation discretion.

## Input ownership and blocking semantics

Implicitly reading stdin when `--message` is absent can wait forever or until a
terminal EOF gesture when an operator expected an argument error. A pipe can
also wait when a producer remains open. Detecting a TTY and changing behavior
would conceal this distinction in the environment: pipes, redirection, CI, and
terminals would invoke different command semantics. That conflicts with the
project preference for explicit, non-magical boundaries.

For a deliberately selected stdin mode, EOF is the only simple one-message
boundary for a finite stream. It preserves one complete message without
inventing line, sentinel, or conversational semantics. Interactive prompting is
excluded: it needs terminal availability, cancellation, visible-versus-hidden
input, and multiline rules, and would change the non-interactive one-shot
shape. Terminal input and piped input therefore should not be silently treated
as interchangeable. Under the current accepted command, no-option invocation
must fail immediately; it must not attempt stdin.

## Validation and fidelity

If a future RFC selected one stdin-derived message, acquisition would need to
produce exactly one Python text string before the existing one-message
validation. The contract would have to choose explicit UTF-8 decoding behavior
or otherwise state Python text-stream semantics; it must not accidentally make
platform defaults the public contract. Invalid decoding and read failures would
need prompt-free local failures with no HTTP request and no raw exception.

Empty input and whitespace-only input should be considered against the existing
whole-string non-whitespace rule. Multiline text, Unicode, leading whitespace,
trailing whitespace, and a final newline supplied by a pipe or redirection are
content, not formatting noise. Removing one structural trailing newline would
be a content mutation, not validation, unless a future accepted contract says
otherwise. The current `--message` contract preserves otherwise valid input,
which weighs against invented normalization.

Reading to EOF also raises a very-large-input question before the existing core
model sees the message. The current message contract contains no visible size
limit. A fixed implementation-owned bound could prevent unbounded acquisition,
but it would newly reject content and needs justification; a configurable bound
would add configuration authority. There is no evidence here that either policy
is warranted. These are unresolved design details, not implementation choices
to hide in a read loop.

## Relationship with `--message`

`--message` and stdin cannot coexist safely without a selection rule. Reading
both and merging them violates the one complete message source model; preferring
one silently discards the other; concatenation invents content semantics. A
coherent future contract would normally require exactly one complete source and
reject a mixed invocation locally before any request. Whether `--message`
remains supported, whether a new source is explicit, and the exact error/exit
contract are compatibility decisions for an RFC. Today the rule is simpler:
exactly one `--message`; stdin is not an input source.

## Relationship with RFC-0049 output modes

An input-source change could theoretically end before request construction and
therefore leave default content-only success output, verbose output, JSON's
exact historical compatibility, successful-content newline behavior, failure
stream allocation, and output-mode mutual exclusion unchanged. RFC-0049
requires precisely that separation for output selection, but does not authorize
new input sources.

Later focused tests would need to prove one valid stdin-derived message yields
the same native request and one request in default, verbose, and JSON modes;
that output is unchanged; that empty, whitespace-only, read, decode, mixed
source, and blocked/no-source cases make no request and keep safe failure
streams; and that content, including final newlines and Unicode, is not mutated.
Those tests must follow an accepted contract, not choose one.

## Privacy assessment

The current client already must not log or persist the message, request,
response, or generated content. Stdin could reduce shell-history and receiving
argument-list exposure, but Home AI Cluster cannot control the data handling of
the surrounding producer, terminal, shell, operating system, or redirection.
It does not change the local-first request target, and it must not create a file,
history, telemetry, or a new retention path. The limited improvement is real
only for the receiving command's arguments; calling it secure secret input
would be inaccurate.

## Architecture and phase assessment

The native request, fixed capability and endpoint, cluster-owned routing and
fallback, result validation, runtime independence, topology blindness, and
process lifecycle could remain unchanged. But an accepted public input source
also defines CLI compatibility, local data handling, blocking/termination,
validation, error behavior, and privacy claims. RFC-0045 expressly rejected
stdin. It is consequently not already permitted as an implementation detail.

If concrete evidence later selects a narrow source, one focused RFC or a narrow
RFC-0045 amendment should decide it before implementation. This alone does not
justify Phase 18 or any new roadmap phase: it would be a bounded post-roadmap
refinement at most, with no need to bundle files, sessions, prompt management,
or generic input abstractions.

## Alternatives and recommendation

No change is a first-class outcome. Operators can continue using one explicit
argument, ordinary shell quoting, a local alias/function, command substitution,
or an operator-owned one-off wrapper. A future explicit stdin mode could be
investigated independently if a finite pipeline workflow is demonstrated.
Prompt files, sessions, interactive chat, and prompt libraries must remain
separate questions.

Recommended next step: collect one concrete, privacy-safe operator scenario
that the current command cannot meet, identifying whether it is a finite local
pipeline, a multiline shell workflow, or another bounded need. Until that
evidence exists, make no repository change: do not draft an RFC, amend
RFC-0045, implement stdin, define a new phase, or change documentation beyond
this investigation.

## Boundaries retained

This investigation proposes and authorizes none of interactive chat,
conversational sessions, multiple messages, roles, system prompts, prompt files,
prompt libraries, persistence, history, clipboard/editor integration, streaming,
tools, multimodal input, generation controls, request-level selectors,
configurable endpoints, discovery, routing/fallback changes, process lifecycle
changes, TTY-dependent output, a generic CLI/input framework, database,
dashboard, Docker, or Kubernetes.

## Files inspected

- Project guidance: `VISION.md`, `FOUNDATIONS.md`, `PRINCIPLES.md`,
  `NON_GOALS.md`, `ROADMAP.md`, `QUESTIONS.md`, `CONTRIBUTING.md`, `AGENTS.md`,
  and `RFC/README.md`.
- Accepted and retained command records: RFC-0045, RFC-0049, the Phase 16
  ordinary operator request access investigation, closeout, proof, and runbook;
  the RFC-0049 investigation and proof; and the end-to-end ordinary
  remote-request proof.
- Current surfaces: `src/home_ai_cluster/chat_command.py`,
  `tests/test_chat_command.py`, `pyproject.toml`, and README one-shot guidance.
