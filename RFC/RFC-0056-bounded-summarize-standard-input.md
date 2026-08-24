# RFC-0056: Bounded summarize standard input

Status: Accepted

Date: 2026-07-27

Author: frian

## Summary

The ordinary native summarize command should retain its explicit text form and
add one bounded standard-input form:

```sh
hac summarize --text "Text"
cat README.md | hac summarize
hac summarize < README.md

home-ai-cluster summarize --text "Text"
cat README.md | home-ai-cluster summarize
```

Exactly one `--text` value remains valid. When it is present, it has explicit
precedence: the command uses it and does not read, probe, or otherwise inspect
stdin. When it is absent, the command reads at most 65,537 raw stdin bytes,
strictly decodes UTF-8, and passes the resulting text unchanged to the existing
`SummarizeRequest` before it constructs an HTTP client.

This is an input-boundary amendment to RFC-0054. It preserves the existing
65,536-byte request limit, native endpoint, one-request behavior, output modes,
timeout, safe errors, topology blindness, and all cluster-owned execution
behavior. It does not add files, positional text, document ingestion,
streaming, or a generic input abstraction.

## Problem

RFC-0054 made one bounded source text available through the ordinary native
summarize client, but limited that source to `--text <TEXT>`. That remains an
explicit, supported form, but it requires shell quoting and is inconvenient for
already-textual command output and redirected text.

An ordinary operator may already have one finite source text on standard input:

```sh
git diff | hac summarize
hac summarize < README.md
```

Adding stdin cannot be treated as a mechanical parser relaxation. It decides
which source wins, how unbounded streams are bounded, how invalid bytes are
handled, when a valid source is complete, and what may appear in errors. Those
are durable CLI and privacy boundaries. The merged
[`summarize stdin input investigation`](../docs/summarize-stdin-input-investigation.md)
provides evidence for this narrow decision.

## Goals

This RFC should:

* preserve exactly one explicit `--text <TEXT>` value as a supported source;
* accept standard input as the only source when `--text` is absent;
* give explicit `--text` precedence without inspecting unused stdin;
* bound stdin memory to at most 65,537 bytes while preserving the existing
  65,536 UTF-8-byte accepted-request limit;
* use strict, explicit UTF-8 decoding independent of locale text decoding;
* retain `SummarizeRequest` as the authority for accepted source-text
  validation;
* fail every invalid input locally before HTTP-client construction or network
  activity with the existing stable invalid-input outcome;
* preserve one existing native `POST /v1/summarize`, result validation, output
  formatting, and safe failure behavior; and
* retain the client as a topology-blind one-shot client of an already-running
  ordinary process.

## Non-goals

This RFC does not add or authorize:

* positional text such as `hac summarize "text"`;
* `--file`, multiple files, recursive input, URLs, clipboard input, PDF, DOCX,
  or HTML extraction, format detection, document parsing, or charset
  detection;
* automatic chunking, map/reduce summarization, truncation, streaming, partial
  summaries, retries, cancellation, or stdin timeout configuration;
* non-blocking pipe polling, readiness detection, terminal detection, or
  TTY-dependent source selection;
* runtime, model, node, capability, routing, topology, endpoint, transport,
  request-model, result-model, adapter, or fallback changes;
* a generic document, stream, loader, ingestion, or CLI-input abstraction;
* new client configuration, a new executable, a wrapper, or a second parser;
* prompt/source logging, persistence, history, or new error taxonomy; or
* a roadmap phase or Phase 19.

`--file` remains a possible later independent increment. It requires a separate
decision for path, filesystem, encoding, error, and privacy semantics.

## Decision

### Command scope and compatibility

The existing ordinary root forms remain supported through their shared command
implementation:

```sh
hac summarize --text "Text"
home-ai-cluster summarize --text "Text"
```

They retain exactly one `--text` value. Repeated `--text` values remain invalid.
Positional text remains invalid. The existing root forwarding and the canonical
long executable remain unchanged.

When `--text` is absent, standard input is the sole source text. Supported
examples include:

```sh
cat README.md | hac summarize
hac summarize < README.md
git diff | hac summarize
cat README.md | home-ai-cluster summarize
```

No `--file` source or positional spelling is added.

### Explicit-source precedence

When exactly one `--text` value is present, the command must use that value and
must not read stdin, probe stdin, call `isatty()`, or try to determine whether
stdin contains data. Thus each of these uses only `argument text`:

```sh
printf 'ignored stdin' | hac summarize --text 'argument text'
hac summarize --text 'argument text' < README.md
hac summarize --text 'argument text'
```

This is explicit-source precedence, not a mixed-input merge and not a claim
that the command can detect conflicting unused stdin data. File descriptor 0
may be inherited from a terminal, pipe, or redirection; its connection does not
establish that source content was supplied. Reliably determining whether it
contains data would require a read or probe and would introduce blocking, race,
or platform-specific behavior. The command deliberately does none of those.

### Bounded stdin read and decoding

When `--text` is absent, the command must read stdin as raw bytes and request at
most 65,537 bytes. It must reject the input if it observes more than 65,536
bytes. The 65,537th byte exists solely to prove that the retained limit was
exceeded.

The command must not truncate, transmit partial text, or continue reading only
to drain the remainder of an oversized stream. It must explicitly decode the
bounded bytes as strict UTF-8. It must not use locale-dependent text decoding,
replacement decoding, charset detection, or BOM-specific behavior. Invalid
UTF-8 is invalid request input.

Without `--text`, stdin represents one complete finite source document. For an
input within the limit, the command may wait for EOF before it can establish
that there is no additional byte. Consequently, a writer that keeps an
otherwise valid pipe open may keep the command waiting. Once the 65,537th byte
is observed, the command may reject without waiting for EOF. This is not a
streaming-summary, polling, timeout, cancellation, or partial-processing
contract.

### Validation and execution boundary

The CLI owns only source selection, the bounded raw stdin read, and strict
UTF-8 decoding. After a successful decode, it must pass the resulting string
unchanged to one existing `SummarizeRequest` construction.

`SummarizeRequest` remains authoritative for rejecting empty and
whitespace-only text, enforcing the maximum 65,536 UTF-8 bytes, and preserving
accepted whitespace and source content. The CLI must not duplicate its semantic
validation or create an input-source, document, stream, loader, or ingestion
abstraction.

The required ordering is:

1. select and obtain the one input source;
2. decode stdin when stdin is the source;
3. construct exactly one `SummarizeRequest`;
4. only after successful construction, create the HTTP client; and
5. send exactly one existing native summarize request.

Invalid stdin must construct no HTTP client and cause no network activity.
Valid text continues through the existing fixed `POST /v1/summarize` boundary.
The client does not gain routing, runtime, model, node, adapter, topology, or
process-lifecycle authority.

### Invalid input and privacy-safe failures

The following are invalid local input and must retain the existing public
outcome:

* omitted `--text` with empty stdin;
* whitespace-only stdin;
* invalid UTF-8 stdin;
* stdin longer than 65,536 bytes;
* an ordinary synchronous stdin read failure;
* repeated `--text`;
* mutually invalid output-mode options; and
* positional or otherwise unsupported input shapes.

Each writes no stdout, writes exactly one stderr line,
`error: invalid request input`, and exits 2. No separate public stdin-read
failure category is introduced. The error must not expose source text, partial
bytes, byte excerpts, decoding or read exceptions, redirection paths, runtime
URLs, machine details, or stack traces.

Existing connection, timeout, HTTP-status, response-validation, and other
request-error classifications remain unchanged. In particular, RFC-0055's
shared 120-second HTTPX timeout remains an HTTP-client boundary and does not
become an stdin timeout.

### Source-neutral output

After one valid request completes, the established summarize output behavior is
unchanged and does not vary by source:

* default mode emits validated `ClusterResult.content` with the existing final
  newline rule;
* `-v`/`--verbose` uses the existing response and attribution format; and
* `--json` uses the existing compact validated `ClusterResult` form.

The same native endpoint, result validation, stdout/stderr destinations, exit
behavior, and timeout apply to both explicit and stdin source text.

## Rationale

One explicit source plus one fallback stdin source is the smallest useful
extension for shell pipelines and redirection. The visible `--text` spelling
remains clear for direct input and scripts. Giving it precedence makes the
contract truthful: the command does not pretend it can distinguish an
inherited-but-unread descriptor from a descriptor that contains source data.

Raw bytes and strict UTF-8 retain the information needed to enforce one
engine-independent byte boundary without accepting locale-dependent or
replacement-decoded content. Reading the accepted maximum plus one byte creates
a simple finite memory limit and proves oversize input without reading the
remainder. Retaining `SummarizeRequest` after decoding keeps source semantics
in their existing normalized request model, rather than dividing them among
new parsing helpers.

The deliberately ordinary EOF behavior is simpler than special terminal or
pipe handling. It makes the command's ownership clear: it accepts one complete
text value, not an interactive or streaming protocol. Existing safe local
input errors protect privacy and avoid exposing shell, operating-system, or
decoder details.

## Alternatives considered

### Retain `--text` only

Rejected. It preserves the current smallest scope but does not serve the
observed finite pipeline and redirection use cases. The accepted bounded
contract adds those cases without changing the request or cluster boundary.

### Reject `--text` whenever stdin is non-terminal

Rejected. A non-terminal descriptor does not establish that useful source data
was supplied, and a terminal is also a connected stdin. This rule would make
behavior depend on environment state rather than the explicit source choice.

### Probe stdin for conflicting data

Rejected. Determining whether stdin has data requires consuming or probing it.
That can block, race with a writer, need platform-specific readiness behavior,
or create rules for data that has been partly inspected. It is less truthful
and more complex than leaving explicit stdin unread.

### Use `isatty()` for source selection

Rejected. TTY state neither proves that a pipe contains data nor expresses the
operator's chosen source. It would create a hidden terminal-dependent branch
and does not solve empty or open-pipe semantics.

### Read text-mode stdin

Rejected. The text wrapper's external encoding and error policy may decode or
replace raw bytes before validation. The command must instead classify strict
UTF-8 itself.

### Read all stdin before validating

Rejected. It permits unbounded memory use and cannot reject a large input as
soon as the retained limit is proven exceeded.

### Truncate oversized input

Rejected. It silently changes the source content and would transmit a partial
document as though it were complete.

### Add positional input

Rejected. It introduces a second durable source spelling and shell-token
questions distinct from the explicit source option and the one stdin fallback.

### Add `--file` in the same increment

Deferred. File paths introduce filesystem ownership, path disclosure,
encoding, size, and error rules that are independent of shell redirection.

### Create a generic input-source abstraction

Rejected. Two concrete sources do not justify a framework. One explicit parser
path and one bounded byte-read branch keep ownership visible.

### Give stdin read failures a separate public error

Rejected. A new category exposes an operational distinction without an
operator action that can safely be specified here. The existing invalid-input
line is stable, local, non-leaking, and sufficient for this increment.

## Trade-offs

Stdin lets operators compose an ordinary command with existing text-producing
tools, but a valid pipe whose writer remains open can wait for EOF. That is a
deliberate consequence of treating stdin as one complete input, and avoids
inventing timeout, polling, streaming, or partial-result semantics.

Explicit `--text` precedence means a user can connect stdin while providing an
argument without receiving a conflict error. This is intentional: the command
cannot truthfully detect whether unused stdin contains content without doing
the reads and probes the contract refuses. The trade-off is documented rather
than hidden.

Raw byte reading adds a small command-edge responsibility, but preserves strict
UTF-8 and bounded memory while leaving semantic validation and all execution
behavior in their established owners.

## Impact

After acceptance, a separate implementation PR may make the smallest
command-specific change to the ordinary summarize parser/input path and its
focused tests. It may update ordinary operator documentation only after the
behavior exists. It must preserve `SummarizeRequest`, the 65,536-byte limit,
the fixed native endpoint, exactly one POST, the existing output modes, the
shared 120-second timeout, error mappings, and all routing, runtime, topology,
and privacy boundaries.

No production behavior, test, README, canonical operator workflow, roadmap, or
Phase 19 changes are included in this RFC.

## Implementation proof

A later implementation PR must provide focused evidence that:

1. existing `--text` behavior remains supported;
2. repeated `--text` remains invalid;
3. valid piped UTF-8 input succeeds;
4. redirected-file input succeeds;
5. `/dev/null` is invalid input;
6. whitespace-only stdin is invalid;
7. invalid UTF-8 is invalid;
8. exactly 65,536 valid stdin bytes are accepted;
9. 65,537 stdin bytes are rejected without truncation;
10. stdin read failure uses the stable invalid-input outcome;
11. `--text` does not read or inspect stdin;
12. invalid stdin creates no HTTP client;
13. one valid stdin input constructs one `SummarizeRequest`;
14. one valid stdin input sends exactly one request to `/v1/summarize`;
15. content, verbose, and JSON output remain source-neutral;
16. automated input tests need no live runtime;
17. no generic input abstraction is introduced;
18. routing, runtime, timeout, endpoint, and topology behavior do not change;
19. no private input or raw local exception leaks; and
20. one explicit local pipeline proof succeeds.

Direct command-function tests with injected byte streams and an HTTP-client
factory that fails if constructed are sufficient for local invalid-input and
request-ordering evidence. Small subprocess tests may cover pipe, redirection,
and `/dev/null` behavior. The explicit local pipeline proof occurs only after
implementation and must retain no source text, generated text, raw exception,
or private machine detail.

## Privacy considerations

Source text read from stdin is request content. The command must not log,
persist, cache, retain, add history for, or echo it on failure. It must not
expose partial bytes, byte excerpts, decoder errors, read errors, redirection
paths, runtime URLs, private identities, credentials, or stack traces.

Only fully validated source text may cross the existing native summarize
request boundary. Successful stdout remains direct operator output under the
existing content, verbose, and JSON contracts; shell and operating-system
retention outside Home AI Cluster remains outside this RFC's authority.

## Open questions

None for this proposed narrow contract. The implementation may choose narrow
function and parameter names, byte-stream injection mechanics, and focused test
placement, provided it preserves this RFC's source, validation, execution,
privacy, and proof boundaries.

## Decision

Accepted.
