# RFC-0057: Bounded summarize regular-file input

Status: Accepted

Date: 2026-07-27

Author: frian

## Summary

The ordinary native summarize CLI should add one explicit regular-file source:

```sh
hac summarize --file README.md
home-ai-cluster summarize --file README.md
```

The existing three source forms would be:

```sh
hac summarize --text "Text"
hac summarize --file README.md
cat README.md | hac summarize
```

`--text` and `--file` are mutually exclusive explicit options. With neither,
stdin remains the source under RFC-0056. A file source is restricted to an
opened regular file, read as bounded raw bytes and strict-decoded UTF-8 before
the existing `SummarizeRequest` is constructed. Existing endpoint, one-request,
output, timeout, privacy, routing, and error contracts remain unchanged.

This proposal does not add positional paths, multiple files, directories,
general streams, document parsing, or a generic source abstraction.

## Problem

RFC-0054 made one supplied source text available through the ordinary native
summarize client. RFC-0056 added bounded stdin while retaining explicit
`--text`. Operators may also have one already-existing local text file that
they want to summarize without shell command substitution or redirection:

```sh
hac summarize --file README.md
```

A file path is not merely another spelling for text. It introduces source
selection, path interpretation, special-file behavior, open/read races,
encoding, privacy, and filesystem-error decisions. The merged
[`summarize file input investigation`](../docs/summarize-file-input-investigation.md)
provides evidence for the deliberately narrow proposal below.

## Goals

This RFC should:

* preserve `--text` and RFC-0056 stdin behavior;
* add one explicit `--file <PATH>` source through both root executable names;
* make explicit source conflicts local invalid input;
* accept only an opened regular file, including a normal symlink whose opened
  target is regular;
* preserve the existing 65,536 UTF-8-byte source limit through a short-read-safe
  bounded read;
* use strict UTF-8 without source-changing decoding;
* retain `SummarizeRequest` as the source-text validation authority;
* complete every file failure before HTTP-client construction or network
  activity; and
* preserve all existing native client output, failure, privacy, topology, and
  execution boundaries.

## Non-goals

This RFC does not add or authorize:

* positional paths, multiple `--file` values, multiple files, directories,
  recursive traversal, globs, path search, or `--file -`;
* URLs, clipboard input, PDF/DOCX/HTML extraction, Markdown or source-code
  parsing, MIME or format detection, charset detection, compressed files, or
  archives;
* chunking, map/reduce, truncation, streaming, file watching, retries,
  locking, snapshots, checksums, or race-free filesystem guarantees;
* application-side `~`, environment-variable, glob, repository-relative, or
  configuration-path expansion;
* a generic source, document, stream, loader, ingestion, or CLI-input
  abstraction;
* runtime, model, node, routing, endpoint, request-model, result-model,
  adapter, topology, fallback, or timeout changes; or
* a roadmap phase or Phase 19.

## Decision

### Source forms and explicit conflicts

Both root executable names support the same forms:

```sh
hac summarize --text "Text"
hac summarize --file README.md
cat README.md | hac summarize

home-ai-cluster summarize --text "Text"
home-ai-cluster summarize --file README.md
cat README.md | home-ai-cluster summarize
```

`--text` and `--file` are mutually exclusive explicit options. Repeated
`--text`, repeated `--file`, their combination, positional tokens, and unknown
arguments are invalid local input. In particular, these are invalid:

```sh
hac summarize --text "Text" --file README.md
hac summarize --file first.txt --file second.txt
```

With neither explicit option, stdin remains the sole source according to
RFC-0056. When `--text` is supplied, the command uses it and does not inspect
stdin or open a file. When `--file` is supplied, the command uses only that
file and does not read, probe, or inspect stdin. Thus:

```sh
cat ignored.txt | hac summarize --file README.md
hac summarize --file README.md < ignored.txt
```

use only `README.md`. The command makes no claim that it can diagnose unused
stdin content.

### Path semantics

`--file` receives one ordinary operating-system path. Relative paths resolve
from the process working directory; absolute paths use ordinary operating-system
behavior. Home AI Cluster does not expand `~`, environment variables, globs,
repository-relative paths, or configuration paths. `--file -` has no stdin
meaning. Shell expansion performed before invocation remains outside this
contract.

Directories are invalid. Normal symbolic-link resolution is allowed only when
the opened target is a regular file. A link resolving to a directory, FIFO,
socket, device, or other non-regular object is invalid.

### Regular-file open and validation

The first `--file` contract accepts only regular files. It rejects directories,
FIFOs, sockets, device files, `/dev/null`, procfs/sysfs-style non-regular
objects, and symlinks whose opened target is non-regular. This prevents the
file option from becoming a second general stream interface.

The implementation must use this bounded strategy:

1. perform an ordinary pre-open check that the supplied path currently
   identifies a regular file;
2. open the path in binary read mode;
3. inspect the opened file descriptor with `os.fstat()`;
4. require `stat.S_ISREG()` on that opened descriptor; and
5. only then read content.

The descriptor check is authoritative for the object actually opened. The
pre-open check rejects ordinary known special paths before a potentially
blocking normal open. This is not race-free: a path can change between those
steps and a concurrent replacement can still affect or delay the invocation.
The explicit path and surrounding filesystem remain operator-owned.

This RFC deliberately adds no locking, snapshotting, checksums, retries,
descriptor-relative traversal, platform-specific non-blocking open API, or
race-free filesystem promise. It does not silently define a POSIX-only API
contract.

### Bounded source bytes and UTF-8

After validating the opened descriptor, the command reads raw bytes using a
short-read-safe loop. It retains at most 65,537 bytes, rejects when the 65,537th
byte is observed, never truncates, never transmits partial content, and does
not continue reading only to drain an oversized file.

Metadata size may be used only as an optional early rejection optimization. It
is not authoritative: it can be stale and cannot validate UTF-8. The bounded
read and later model validation remain authoritative.

The bounded bytes are decoded with strict UTF-8. The command must not use
locale-dependent decoding, replacement decoding, charset or format detection,
`utf-8-sig`, or BOM removal. A valid UTF-8 BOM remains the source character
`U+FEFF`, consistent with strict decoding and unchanged source content.

### Validation and execution boundary

The command owns source selection, path handling, regular-file validation,
bounded raw reading, and strict UTF-8 decoding. It then passes the decoded text
unchanged to exactly one existing `SummarizeRequest`.

`SummarizeRequest` remains authoritative for empty text, whitespace-only text,
the 65,536 UTF-8-byte maximum, and preservation of accepted whitespace and
text. No generic file, document, stream, loader, ingestion, or input
abstraction is introduced.

The required order is:

```text
source selection
  -> path and regular-file validation
  -> bounded file read
  -> strict UTF-8 decode
  -> SummarizeRequest
  -> HTTP client
  -> one POST /v1/summarize
```

Every invalid file case finishes before HTTP-client construction and network
activity. A valid file retains the fixed loopback endpoint and exactly one
native request.

### Invalid-input, privacy, and consistency boundaries

The following use the existing stable local outcome:

```text
error: invalid request input
```

They write empty stdout, exactly one stderr line, and exit 2: missing path,
permission failure, directory, non-regular file, broken link, symbolic-link
loop, path/open/stat/read failure, read failure after partial bytes, invalid
UTF-8, empty or whitespace-only file, over-limit content, explicit source
conflict, repeated `--file`, and unsupported positional forms. No separate
public filesystem or file-read error category is introduced.

Public errors and default logs must omit the supplied and resolved paths,
working directory, targets, owners, permissions, mount points, raw filesystem
exceptions, source text, partial bytes, decoding details, stack traces,
machine details, and runtime URLs. File contents must not be logged, persisted,
cached, echoed on failure, or added to request history.

The command summarizes the one bounded byte sequence successfully read from the
opened, validated regular-file descriptor during that invocation. It provides
no snapshot, stable-path, atomic-read, locking, mutation retry, or checksum
guarantee. A read failure after partial data rejects the entire input and sends
nothing.

### Output and execution compatibility

Default content, verbose, and JSON output remain source-neutral. No filename,
path, metadata, or file attribution enters output or result fields.

The fixed loopback caller endpoint, `POST /v1/summarize`, one native request,
`ClusterResult` validation, shared 120-second HTTPX timeout, request-error
mappings, routing, capability eligibility, runtime/node/adapter behavior,
topology, fallback, and attribution remain unchanged.

## Rationale

One named file option is the smallest explicit path contract. It is clear in
shell history and scripts while leaving stdin as the existing implicit fallback.
Mutual exclusion is simpler and safer than silently selecting between two known
explicit values. Leaving unused stdin unread retains RFC-0056's truthful,
non-blocking precedence rule.

Only regular files match the intended one-complete-document meaning. Bounded
reads alone constrain memory but do not prevent a FIFO or device from making
the command a special-stream interface. The pre-open plus descriptor check is
a boring compromise: it rejects ordinary special paths early and validates the
actual opened object, while explicitly documenting remaining races rather than
claiming filesystem guarantees.

Strict raw UTF-8 preserves the same deterministic byte and source-content
contract as stdin. Reusing `SummarizeRequest` and the existing native client
keeps semantic validation, HTTP behavior, and cluster authority in their
established owners.

## Alternatives considered

### Retain only `--text` and stdin

Rejected. It remains the lowest-scope contract but does not provide the
explicit reusable-path operation investigated here.

### Allow `--text` and `--file` together with precedence

Rejected. Both explicit values are known to the parser and should fail clearly
rather than silently discard one.

### Detect file-plus-stdin conflict

Rejected. Stdin may be inherited and unread. Probing it needs a read or
platform-specific behavior and recreates RFC-0056's blocking and race problems.

### Use `--file -`

Rejected. Omitted source options already select stdin. The alias would add a
second spelling and special path semantics without value.

### Expand `~`, variables, or globs

Rejected. These create an application-level path language and lookup/privacy
rules. Shell expansion outside the command remains sufficient.

### Accept every readable path or FIFOs

Rejected. This would turn `--file` into a general stream interface with
blocking, virtual-file, device, and unbounded-source semantics.

### Rely only on path metadata

Rejected. Metadata can become stale and does not validate the object actually
opened, its bytes, or its encoding.

### Rely only on bounded reading for arbitrary paths

Rejected. It bounds memory but does not protect against special-file open and
blocking behavior.

### Remove BOM with `utf-8-sig`

Rejected. It silently changes valid source content.

### Expose detailed filesystem errors

Rejected. A new category would expose operational detail without a reliably
safe, actionable distinction; paths and exceptions are privacy-sensitive.

### Introduce a generic source abstraction

Rejected. Three known command sources do not justify a framework.

### Require race-free or snapshot semantics

Rejected. It would require locking, snapshotting, or platform-specific
machinery outside this small command boundary.

### Use platform-specific non-blocking open APIs

Deferred. They may reduce a race window on some systems, but would silently
make this first contract POSIX-specific. This RFC retains ordinary path and
open behavior with documented limits.

## Trade-offs

The regular-file boundary rejects some readable operating-system objects and
does not eliminate every replacement race. That is deliberate: allowing those
objects would make a simple file option behave like another stdin or streaming
interface, while stronger guarantees would add filesystem architecture beyond
the operator need.

The pre-open check can be stale, and a concurrent change can still affect or
delay normal open. The descriptor check prevents trusting only stale metadata,
but it cannot provide atomicity. Explicitly documenting this limit is more
truthful than promising file stability.

No app-side expansion makes paths less magical and avoids repository or
configuration lookup rules, but leaves ordinary shell quoting and expansion to
operators. One stable invalid-input line minimizes privacy exposure, at the
cost of not distinguishing all local filesystem causes.

## Impact

After acceptance, a separate implementation PR may make the smallest
command-local summarize parser/input change, focused tests, and only then the
minimal accurate user documentation. It must not change `SummarizeRequest`,
the 65,536-byte limit, endpoint, one-request behavior, outputs, timeout,
routing, runtime, topology, or privacy defaults.

This RFC PR changes no production behavior, tests, README, operator workflow,
roadmap, or Phase 19.

## Implementation proof

A later implementation PR must prove at least:

1. existing `--text` remains supported;
2. stdin fallback remains supported;
3. valid relative and absolute regular files succeed;
4. valid multibyte UTF-8 and accepted whitespace succeed unchanged;
5. exactly 65,536 bytes succeeds and 65,537 bytes is rejected without
   truncation or transmission;
6. empty, whitespace-only, and invalid-UTF-8 files are invalid;
7. missing file, directory, and non-regular opened descriptor are invalid;
8. symlink to a regular file succeeds and a broken link is invalid where
   symlinks are supported;
9. `--text` plus `--file` and repeated `--file` are invalid;
10. `--file` does not read stdin;
11. invalid file input creates no HTTP client;
12. valid file input constructs one `SummarizeRequest` and sends exactly one
    `/v1/summarize` POST;
13. every output mode remains source-neutral;
14. read failure after partial bytes sends nothing and paths/exceptions do not
    leak;
15. automated tests require no live runtime or root privileges;
16. no generic source abstraction, routing, timeout, endpoint, runtime, or
    topology behavior changes; and
17. one explicit local live proof succeeds after implementation when a runtime
    is available.

FIFO, device, procfs, permission, and other platform-dependent behavior may be
tested where portable but is not required for the core suite.

## Privacy considerations

The path is private input as well as the file content. It must receive the same
non-retention and non-leaking treatment as stdin or `--text` source content.
Later documentation should use public repository-relative examples such as
`README.md`, not real operator paths. Successful stdout remains direct operator
output under existing ownership; shell and operating-system retention outside
Home AI Cluster remain outside this RFC.

## Open questions

None for this proposed narrow contract. Later implementation may select narrow
command-local helper and test names, but must preserve the specified pre-open,
opened-descriptor, bounded-read, validation, privacy, and proof boundaries.

## Decision

Accepted.
