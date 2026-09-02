# Summarize stdin input investigation

## Status

Investigation only. This document proposes no accepted contract and makes no
production-code change. A later RFC is required before stdin becomes an
ordinary `summarize` input source.

## Scope

This investigates bounded standard-input support for the existing ordinary
native summarize clients:

```sh
hac summarize --text "Text"
home-ai-cluster summarize --text "Text"
```

The possible additional forms are `cat README.md | hac summarize`,
`hac summarize < README.md`, and `git diff | hac summarize`. This is not an
investigation of positional text, `--file`, document ingestion, parsing,
streaming summaries, or a new roadmap phase.

## Current behavior

Observed repository facts:

* Both root names dispatch through `home_ai_cluster.command.main`, whose
  `summarize` entry delegates to `home_ai_cluster.commands.summarize_command.main`.
* `summarize_command._parse_input()` owns an `argparse` parser. It records
  `--text` with `action="append"` and requires exactly one resulting value.
  Therefore omitted, repeated, positional, and unknown input forms currently
  fail locally.
* `_parse_input()` constructs `SummarizeRequest` before
  `_post_native_request()` constructs an `httpx.Client`. Invalid input produces
  empty stdout, exactly `error: invalid request input` on stderr, and exit 2.
* `SummarizeRequest` preserves accepted whitespace, rejects `text.strip()` that
  is empty, and rejects UTF-8 encodings longer than 65,536 bytes. It is the
  existing semantic and byte-limit validation authority.
* A validated request is serialized as only `{"text": <text>}` and posted once
  to the fixed loopback `/v1/summarize` endpoint. No client routing, topology,
  runtime, or fallback behavior is involved.
* The command imports the existing chat command's success formatter. Its
  explicit modes are content by default, `-v`/`--verbose`, and `--json`; their
  selection is not TTY-dependent. `--verbose` with `--json` is invalid locally.
* Current tests already prove invalid input happens before HTTP-client creation,
  preserves whitespace in a valid request, shares the 120.0-second native
  timeout, preserves all three output forms, and keeps safe failures separate
  from stdout.
* `summarize_command` deliberately shares narrow presentation and error seams
  with `chat_command`; it is not coupled to chat request construction,
  capability selection, or chat transport.

RFC-0051 establishes the `SummarizeRequest` 65,536 UTF-8-byte and non-blank
boundary before routing or network activity. RFC-0054 establishes the ordinary
root client, its local-before-HTTP validation order, fixed endpoint, output
modes, and safe failure behavior. RFC-0055 establishes the shared finite native
client timeout. Their accepted current input contract is text-only `--text`;
stdin would deliberately amend that client contract rather than merely fill an
implementation gap.

## Current implementation ownership

The smallest future implementation can keep the existing ownership visible:

1. The summarize CLI chooses one source and, for stdin only, converts bounded
   raw bytes to one Unicode string.
2. The CLI constructs one `SummarizeRequest` from that final string.
3. Existing `SummarizeRequest` validation remains authoritative for blank text
   and the semantic UTF-8 byte maximum.
4. Only after that succeeds does existing HTTP-client construction and the
   one-request path run.

This does not justify a generic input-source, document, stream, or
request-loader abstraction.

## Experiments

Disposable local experiments used the repository virtual environment and no
production code or repository test was changed.

| Experiment | Observation | Conclusion |
| --- | --- | --- |
| `home-ai-cluster summarize < /dev/null` | Exit 2, zero stdout, and the existing stable invalid-input line. | The current implementation requires `--text`; it does not yet read stdin. |
| `sys.stdin.buffer.read(65537)` with `abc` redirected from a here document | Four bytes, including the here-document newline; `sys.stdin.isatty()` was `False`. | A redirected byte stream supplies exact bytes and is not a terminal. |
| A piped UTF-8 `é` | Two bytes decoded strictly to one Unicode character. | UTF-8 byte count and character count differ. |
| A piped byte `0xff` | Strict UTF-8 decoding raised `UnicodeDecodeError`. | Reading raw bytes can detect invalid UTF-8 without replacement text. |
| `--text argument` with stdin redirected from `/dev/null` | The current command attempts its ordinary request; it does not inspect the inherited stdin. | Connected stdin and supplied stdin content are different facts. |

The shell cases below were also evaluated from process semantics, not inferred
from argument parsing:

```sh
printf 'stdin text' | hac summarize --text 'argument text'
hac summarize --text 'argument text' < README.md
hac summarize --text 'argument text'
```

In the first two, file descriptor 0 is connected to a pipe or regular file;
in the last it is normally an inherited terminal. None establishes, without a
read, whether usable data was supplied. `isatty()` can distinguish a terminal
from the usual pipe/file cases, but cannot say whether a pipe contains data and
does not establish a portable non-blocking content check. Reading to find out
can block on a terminal or an open pipe.

## Findings

### Input-source semantics

The smallest deterministic rule is:

* with exactly one `--text <TEXT>`, use that value and do not read, probe, or
  otherwise inspect stdin;
* without `--text`, read stdin as the sole source.

This means `--text` has explicit precedence, rather than claiming that it is an
error to combine it with stdin. It is truthful for all three shell cases above:
the command cannot portably distinguish an inherited but unread stdin from
stdin that contains data without consuming or probing it. A conflict rule based
on "stdin was supplied" would either be false for some invocations or require
blocking reads, races, platform-specific polling, or TTY policy.

No `isatty()` rule is necessary for this first contract. With no `--text`,
ordinary terminal invocation waits for EOF just as an explicit request for
stdin input should; pipe and redirection behavior require no special detection.
That is deterministic and avoids treating pipeline use differently from file
redirection. It is a future RFC decision whether that waiting behavior is the
desired ordinary interactive ergonomics.

### Bounded-read findings

The future CLI can read at most 65,537 bytes from a binary stdin stream. If the
result is longer than 65,536 bytes, it rejects the input without truncation.
The extra byte is sufficient to classify the byte-limit violation: it proves
that the input has more bytes than the accepted maximum, while retaining at
most 65,537 bytes in memory. It never needs to read the remainder of an
oversized stream.

For a valid stream, `read(65537)` must observe EOF before it can know that no
additional byte exists; a pipe whose writer remains open can therefore keep the
command waiting. This is inherent in accepting one complete finite stdin value,
not streaming summarization. For an oversized stream that supplies at least the
extra byte, the command can reject without waiting for EOF. No truncation,
partial acceptance, chunking, or map/reduce behavior follows from this.

### UTF-8 findings

`sys.stdin` is a text wrapper whose decoding encoding and error behavior are
configured outside this command. It can therefore decode or replace bytes
before the command sees them, hiding information needed to apply a strict
invalid-UTF-8 contract. The future CLI should read `sys.stdin.buffer` (or an
injected binary stream in tests), then use explicit strict UTF-8 decoding.

After successful decoding, the resulting text should be passed unchanged to
`SummarizeRequest`. This preserves the existing Unicode-string behavior for
`--text` while keeping the model authoritative for blank and UTF-8-byte-limit
validation. It needs no charset detection, replacement decoding, locale policy,
BOM special case, or format detection.

### Empty and whitespace-only stdin

An empty byte stream decodes to `""`; whitespace-only UTF-8 bytes decode to a
whitespace-only string. Both should reach `SummarizeRequest`, which already
rejects them. They should therefore retain the existing public local-input
contract: exit 2, empty stdout, and exactly one `error: invalid request input`
stderr line, before HTTP-client construction.

## Error and exit behavior

For ordinary invalid source inputs—empty input, whitespace-only input, invalid
UTF-8, and more than 65,536 bytes—the evidence supports reusing the existing
safe invalid-input outcome. It exposes neither text, byte excerpts, paths from
shell redirection, decoding details, URLs, nor exceptions.

A synchronous stdin read can also fail independently of input validity (for
example an `OSError` from an injected or interrupted stream). The existing
contract has no stdin-read category. Mapping that case to invalid input is the
smallest privacy-safe possibility, but whether an operational read failure
deserves a distinct stable safe category is an architectural/CLI-contract
choice for the RFC. It must never reveal the raw exception, source path,
partial bytes, or stack trace.

Malformed command forms continue to be invalid local input. Under the
recommended precedence rule, `--text` plus a pipe, redirect, or terminal is not
a malformed form because stdin is intentionally unread.

## Privacy boundary

The source remains request content. The future command must not log, persist,
echo on failure, cache, retain, or include stdin text in request history. It
may send only the fully validated final text through the existing native
request boundary. Existing content, verbose, and JSON success output remains
direct operator output and is not varied by source. Failed input produces no
stdout.

## Testability

The smallest later automated proof can remain local and deterministic:

* direct command-function tests with an injected `BinaryIO` for valid UTF-8,
  invalid UTF-8, empty, whitespace-only, exactly 65,536 bytes, and 65,537 bytes;
* an HTTP-client factory that fails if invoked, proving every invalid source
  stops before client construction;
* request-capture tests proving decoded valid text produces the unchanged one
  `{"text": ...}` request and all existing output modes are source-neutral;
* tests proving `--text` does not read an injected stdin stream; and
* small subprocess tests for pipe, redirected file, and `/dev/null` behavior.

Injected streams avoid live runtimes. Shell pipeline tests are useful
integration evidence, but they are not required to prove byte limits or error
mapping. `/dev/null`, shell redirection, and `isatty()` observations above are
POSIX/Linux experiments; the recommended contract intentionally does not rely
on POSIX-only readiness APIs or terminal detection. The exact availability of
`sys.stdin.buffer` for nonstandard embeddings would be an implementation
boundary to test or guard, not a reason to use locale-decoded text.

## Alternatives considered

* **Require `--text` and reject stdin.** This is the accepted current contract
  and remains the smallest scope, but it does not enable the investigated
  pipeline workflow.
* **Reject `--text` whenever stdin is connected.** Rejected: stdin is always
  connected; this would reject ordinary terminal use and says nothing about
  supplied content.
* **Reject `--text` only when stdin contains data.** Rejected: truthful,
  portable detection requires reading/probing and introduces blocking, races,
  or platform-specific behavior.
* **Use `isatty()` to decide whether to read.** Rejected for the first contract:
  it adds a hidden environment-dependent branch and does not answer whether a
  pipe contains data.
* **Read text-mode stdin.** Rejected: it cannot reliably preserve invalid-byte
  information for strict UTF-8 validation.
* **Read all stdin then validate.** Rejected: it permits unbounded memory use.
* **Truncate at 65,536 bytes.** Rejected: it silently changes source content.

## Recommended smallest contract

Subject to RFC acceptance:

1. `--text <TEXT>` remains accepted and takes precedence; stdin is not
   inspected when it is present.
2. With no `--text`, the command reads one stdin byte sequence, bounded at
   65,537 bytes.
3. It strictly decodes that bounded sequence as UTF-8 and constructs exactly
   one `SummarizeRequest` before creating an HTTP client or performing network
   activity.
4. Empty, whitespace-only, invalid-UTF-8, and over-limit input are rejected;
   they are never truncated or transmitted.
5. Existing content, verbose, and JSON success formats remain unchanged and
   source-neutral.
6. The contract uses no TTY detection, positional input, or file option.

## RFC-required decisions

The following are durable CLI and privacy-boundary decisions and need an RFC
before implementation:

* whether to amend RFC-0054's text-only input contract with the deterministic
  no-`--text` stdin rule;
* whether explicit `--text` precedence over unread stdin is accepted in place
  of an unenforceable conflict rule;
* the exact public classification of invalid UTF-8, over-limit bytes, and
  unexpected stdin read failure, including whether the last requires a new
  stable safe error category;
* acceptance of waiting for EOF for a valid stdin stream and rejecting an
  oversized stream after one extra byte; and
* the intended cross-platform support statement for raw binary stdin and any
  nonstandard-stdin fallback, if one is wanted.

## Deferred work

`--file` may be considered only as a separate future increment and decision.
It would introduce path, filesystem, encoding, and privacy/error semantics that
this stdin contract deliberately does not decide.

## Non-goals

This investigation does not add or decide:

* `hac summarize "positional text"` or `hac summarize --file README.md`;
* multiple files, recursion, URLs, clipboard input, PDF/DOCX/HTML extraction,
  format detection, or document parsing;
* automatic chunking, map/reduce, truncation, streaming, retries, timeout,
  model, runtime, node, topology, routing, endpoint, or request-model changes;
* a generic document or stream abstraction, a new roadmap phase, or Phase 19.
