# RFC-0053: Positional chat message

Status: Draft

Date: 2026-07-24

Author: frian

## Summary

The ordinary one-shot chat command should accept one message through either a
single positional argument or the existing `--message` option:

```sh
hac chat "Hello"
hac chat --message "Hello"
```

The positional form is additive. `--message` remains fully supported and is
not deprecated. Exactly one message source is required; a positional message
and `--message` are mutually exclusive. This changes only the local input
boundary of the existing one-shot command. It preserves the request, output,
failure, privacy, routing, topology, transport, runtime, fallback,
persistence, and lifecycle contracts accepted by RFC-0045, RFC-0049,
RFC-0050, and RFC-0052.

## Problem

The existing ordinary command requires an explicit option for its only input:

```sh
hac chat --message "Hello"
```

That is clear and remains useful for scripts, but creates repeated typing
friction in the ordinary one-shot terminal case. The unified `hac chat` form
makes the command easy to find, yet the message itself still requires a longer
spelling than the one-value interaction needs.

The project needs a small ergonomic improvement without breaking existing
automation or turning a one-shot client into an interactive, multi-source, or
stateful chat interface.

## Goals

This RFC should:

* accept exactly one message through either one positional argument or exactly
  one `--message` option;
* preserve `--message` as a fully supported, non-deprecated equal alternative;
* make equal values from either form produce one identical internal message and
  identical native request body;
* preserve the existing local invalid-input error,
  `error: invalid request input`, and exit status 2;
* preserve the existing `-v`, `--verbose`, and `--json` output selections;
* apply the same input behavior through `home-ai-cluster-chat`,
  `home-ai-cluster chat`, and `hac chat`; and
* keep executable identity out of parsing and behavior.

## Non-goals

This RFC does not remove, deprecate, warn on, or migrate away from
`--message`. It does not add interactive chat, multi-turn sessions, REPL
behavior, automatic stdin input, file input, prompt history, conversation
state, multiple user messages, or system-message input.

It does not add model, node, or capability selection; output modes; shell
completion; API changes; a second parser; a wrapper command; another CLI
library or framework; or executable-name-dependent behavior.

It does not change routing, topology, transport, runtime, fallback, privacy,
persistence, or lifecycle behavior. It creates no roadmap phase or Phase 19.

## Proposal

### One additive input contract

The ordinary one-shot chat parser will accept precisely one of these forms:

```sh
home-ai-cluster-chat "Hello"
home-ai-cluster-chat --message "Hello"

home-ai-cluster chat "Hello"
home-ai-cluster chat --message "Hello"

hac chat "Hello"
hac chat --message "Hello"
```

The standalone command remains the owner of chat parsing. RFC-0050's root
continues to forward the remaining arguments unchanged, and RFC-0052's two
installed root executable names continue to invoke the same root function.
Executable identity must not affect accepted input, output, errors, or exit
status.

The positional form is additive. `--message` remains fully supported, is not
legacy or compatibility-only, and must remain documented as an equal
alternative. No deprecation, warning, migration timeline, or automatic command
rewriting is introduced.

### Exact validation rules

Exactly one message source is required. One non-blank positional message with
no `--message` is valid. Exactly one non-blank `--message` value with no
positional message is valid. The value is preserved after validation.

The following are invalid local input:

* missing both forms;
* a blank or whitespace-only positional value;
* a blank or whitespace-only `--message` value;
* repeated `--message`;
* supplying both a positional message and `--message`;
* more than one positional token; and
* unknown arguments.

Each invalid form performs no request, writes no stdout, writes the existing
stable error line to stderr, and exits 2. There is no precedence rule when both
sources are supplied.

Multi-word positional input requires ordinary shell quoting:

```sh
hac chat "Explain local-first design"
```

Unquoted trailing tokens are not joined into one message. For example,
`hac chat Explain local-first` is invalid because it supplies more than one
positional token. This retains one explicit message boundary instead of
inventing a variable-length prompt grammar.

### Normalization and unchanged execution

Both accepted forms normalize to one identical internal message string. For
equal input values, they must construct identical existing native request
bodies: one `user` message containing that preserved value and the fixed
`chat` capability. The command still sends one request to the same fixed
ordinary loopback target and validates the same normalized result.

`-v`, `--verbose`, and `--json` retain their current meaning and mutual
exclusion. They neither choose an input source nor alter validation.

All accepted RFC-0045 and RFC-0049 behavior otherwise remains unchanged:
request target, timeout, response validation, failure mapping, stdout, stderr,
exit status, output presentation, and privacy remain command-owned as before.
The change grants no routing, topology, transport, runtime, model, node,
fallback, persistence, or lifecycle authority.

### Minimal parser boundary

The expected implementation can use one existing parser and one normalized
input path. Conceptually, its input declarations can be as small as:

```python
parser.add_argument("message_positional", nargs="?")
parser.add_argument("--message", action="append")
```

The source-count and non-blank checks remain local validation after parsing.
This example is explanatory, not a requirement to adopt particular names or
helper structure.

The implementation must not use `nargs="+"` or `nargs="*"`, join arbitrary
trailing tokens, choose one source by precedence when both are supplied, add a
second parser or wrapper, make behavior depend on the executable name, or add a
CLI library or framework.

## Rationale

One optional positional value is the smallest understandable spelling for the
ordinary one-message terminal interaction. It reduces repeated use friction
without broadening the chat client's authority or changing how the cluster
receives, routes, or executes a request.

Retaining `--message` avoids breaking scripts, automation, documentation, and
operator muscle memory. Its explicit name also remains useful where command
lines contain several values or are generated programmatically. The option is
not a legacy path: the two forms have equal support and normalize to exactly
the same request behavior.

Mutual exclusion is clearer and safer than a hidden precedence choice. A
quoted positional value preserves ordinary shell behavior for multi-word
messages. Rejecting surplus tokens makes the one-message boundary visible and
avoids reassembling a value that the shell deliberately split. This is a boring
local parser adjustment, not a second input mode or protocol change.

## Alternatives considered

### Keep `--message` only

This preserves the accepted input contract without change and remains the
lowest-risk choice. It does not address the specific repeated-use friction that
motivates the proposal.

### Replace `--message` with a positional value

Rejected. Removing the existing form breaks scripts, automation,
documentation, and operator muscle memory for no demonstrated benefit beyond
what the additive form supplies. It would also require a migration decision.

### Accept both sources with precedence

Rejected. Choosing positional or option input silently would make an accidental
extra argument capable of changing submitted content. Rejection is simpler,
safer, and immediately understandable.

### Use variable positional arguments or join trailing tokens

Rejected. `nargs="+"`, `nargs="*"`, or manual joining would make a
variable-length prompt grammar, lose the shell's supplied argument boundaries,
and need joining and whitespace rules. Normal shell quoting already expresses
one multi-word value.

### Add stdin or interactive behavior

Rejected. Stdin and interaction introduce source precedence, blocking, TTY,
empty-input, session, and lifecycle semantics beyond this one-shot input
decision.

### Add a wrapper, second parser, or CLI framework

Rejected. The existing command parser and root forwarding seam are sufficient.
Extra layers would duplicate parsing or conceal a small explicit contract
change.

## Trade-offs

The positional form makes ordinary terminal use shorter, while keeping the
explicit option stable for automation. It adds one durable input spelling and
requires operators to quote multi-word positional messages, as normal shell
usage already does.

Rejecting surplus tokens is stricter than accepting unquoted prose, but it
keeps exactly one message boundary and avoids ambiguous joining behavior.
Supporting two equal forms adds focused validation cases, but retaining one
normalization and request path bounds that cost.

## Impact

After acceptance, a separate small implementation PR may change only the
existing chat parser and focused chat/root forwarding tests. It may update
operator documentation where appropriate. It must not change Python package
dependencies, API models, request/response contracts, runtime adapters,
routing, topology, transport, persistence, privacy defaults, or process
lifecycle behavior.

The implementation must preserve the standalone chat command and the two
unified entry points. It must not use this RFC to authorize unrelated
refactoring.

## Later implementation proof

A separate implementation PR must provide focused evidence that:

1. positional input succeeds;
2. retained `--message` input succeeds;
3. equal input values produce identical normalized native requests;
4. both forms together are rejected before client construction;
5. missing input is rejected;
6. blank positional input is rejected;
7. blank option input is rejected;
8. repeated `--message` is rejected;
9. surplus positional tokens are rejected;
10. unknown arguments are rejected;
11. verbose and JSON modes remain unchanged;
12. forwarding is preserved through `home-ai-cluster chat`, `hac chat`, and
    `home-ai-cluster-chat`;
13. stdout, stderr, and exit status remain unchanged; and
14. no live runtime, network, model, or two-machine proof is required.

The proof should extend the focused chat-command and unified-command tests and
must not duplicate their full suite. Request capture at the existing client
seam is sufficient to establish equal normalization without a live cluster.

## Open questions

None for the proposed narrow contract. The implementation may select internal
variable names and helper arrangement, provided it preserves this RFC's one
parser, one normalized message, and unchanged execution boundary.

## Decision

Pending.
