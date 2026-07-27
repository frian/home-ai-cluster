# Summarize file input investigation

## Status

Investigation only. This document proposes no accepted contract and makes no
production-code, test, CLI, or RFC change. A later RFC is required before the
ordinary native summarize CLI accepts `--file`.

## Scope

This investigates one explicit file source for the existing ordinary summarize
client:

```sh
hac summarize --file README.md
home-ai-cluster summarize --file README.md
```

Existing `--text` and standard-input forms remain in scope as compatibility
boundaries. This is not file ingestion generally: it does not investigate
positionals, multiple files, directories, traversal, parsing, formats, URLs,
or a document abstraction.

## Current behavior

Observed repository facts:

* `home_ai_cluster.command.main` owns root dispatch. Its `summarize` entry
  forwards the remaining arguments unchanged to
  `home_ai_cluster.summarize_command.main`; both `hac` and
  `home-ai-cluster` use that same root function.
* `summarize_command._parse_input()` currently accepts repeated `--text`
  syntactically, rejects more than one value locally, and otherwise reads stdin.
  There is no `--file` option.
* The command's `_read_bounded_stdin()` reads raw bytes in a short-read-safe
  loop, retains at most 65,537 bytes, rejects the 65,537th byte, and strictly
  decodes UTF-8. It does not call `isatty()` or inspect stdin when `--text` is
  present.
* After source selection and decoding, `_parse_input()` constructs exactly one
  existing `SummarizeRequest`. That model rejects empty and whitespace-only
  text and enforces the existing 65,536 UTF-8-byte limit while preserving
  accepted whitespace.
* `main()` maps local parser, source, decoding, and model failures to the
  stable `error: invalid request input` outcome before `_post_native_request()`
  can construct its HTTP client. Existing request behavior is one POST to fixed
  loopback `/v1/summarize` with the shared 120-second timeout.
* Default content, verbose, and JSON output are selected at the command edge
  after validating an existing `ClusterResult`; they are source-neutral.

RFC-0051 owns the normalized summarize request and source limit. RFC-0054
owns the ordinary native client and its safe local failures. RFC-0055 owns the
shared client timeout. RFC-0056 adds bounded stdin with explicit `--text`
precedence. A file source would amend the client input contract again; it is not
an implementation detail of RFC-0056.

## Current implementation ownership

The existing implementation makes a narrow future ownership boundary visible:

```text
source selection -> bounded raw bytes -> strict UTF-8 -> SummarizeRequest
                 -> HTTP client -> one POST /v1/summarize
```

The summarize command owns source selection and stdin mechanics.
`SummarizeRequest` owns accepted text semantics and its byte limit. The native
HTTP path owns client construction, one request, response validation, output,
and network failure mapping. A file increment should add only a command-local
file branch before the existing model construction; it does not justify a
generic source, document, stream, loader, or ingestion layer.

## Experiments

Disposable experiments used a temporary directory and removed it afterwards.
No repository code, tests, or experimental files were retained.

| Experiment | Observation | Conclusion |
| --- | --- | --- |
| Open and `fstat()` a temporary regular file | `stat.S_ISREG` was true. | An opened descriptor can establish that the consumed object is regular. |
| Open a symlink to that file and `fstat()` the descriptor | `stat.S_ISREG` was true. | Normal open behavior follows a symlink; descriptor validation sees the target file. |
| Open a FIFO non-blockingly and `fstat()` it | `stat.S_ISFIFO` was true, not regular. | Special files are distinguishable after opening, but normal blocking open of a FIFO needs separate care. |
| Open a missing path | Python raised `FileNotFoundError`. | Missing-path details need safe normalization. |
| Open a directory as binary | Python raised `IsADirectoryError`. | Directories have a distinct local exception but need not gain a public error. |
| Decode BOM-prefixed bytes with strict UTF-8 and `utf-8-sig` | Strict UTF-8 produced leading `U+FEFF`; `utf-8-sig` removed it. | A BOM-removing decoder changes source content. |
| Compare `Path("~/regular.txt")` with `expanduser()` | Expansion occurred only after the explicit `expanduser()` call. | `pathlib.Path` does not implicitly expand `~`. |

The FIFO observation is Linux/POSIX-specific. The experiment used a
non-blocking descriptor only to inspect type; it does not establish a portable
future open strategy.

## Findings

### Source-selection semantics

The smallest deterministic three-source rule to evaluate is:

1. exactly one `--text <TEXT>` is the source;
2. otherwise exactly one `--file <PATH>` is the source;
3. otherwise stdin is the source.

`--text` and `--file` should be an explicit argparse-level mutually exclusive
group. Their combination is a clear user-provided conflict and can fail before
opening a path or reading stdin. Repeated `--file`, positional tokens, and
unknown arguments should likewise remain invalid local input.

When `--file` is present, stdin should remain unread and unprobed, just as
stdin remains unread when `--text` is present today. Thus these need not and
cannot truthfully diagnose unused stdin content:

```sh
cat other.txt | hac summarize --file README.md
hac summarize --file README.md < other.txt
```

File precedence over unused stdin is an explicit source rule, not a claim that
the command detected a mixed input. Reading stdin to detect a conflict would
reintroduce the blocking, race, and platform-specific behavior RFC-0056
deliberately excludes.

### Path semantics

The smallest path contract is an ordinary supplied operating-system path:

* relative paths resolve from the process working directory;
* absolute paths are passed to the operating system normally;
* the application performs no `~`, environment-variable, glob, default
  directory, repository-relative, or configuration lookup expansion;
* `-` is not a stdin alias, because omitted source options already mean stdin;
* normal symbolic-link following is an implementation possibility, subject to
  the regular-file decision below; and
* a directory is not a valid file source.

Shell expansion remains outside the application. For example, an unquoted shell
variable may be expanded by the shell before the command receives it, whereas a
literal `~` or `$NAME` supplied to the application has no special meaning.

### Regular-file boundary

Accepting every readable path would make `--file` an alternate stream API.
FIFOs, devices, sockets, procfs/sysfs-style files, and `/dev/null` can block,
produce changing or unbounded data, or have semantics that do not match one
complete document. Bounded reading limits memory but does not by itself prevent
opening a FIFO from blocking or turn a device into a meaningful file document.

The evidence supports restricting the first contract to regular files. A
symlink resolving through ordinary open behavior to a regular target can remain
accepted; a symlink to a non-regular target is rejected by descriptor type.
Directories and every other non-regular opened object are rejected. `/dev/null`
would therefore be invalid as a `--file` source, even though empty stdin
remains a separate source case.

There is an implementation and portability decision still to make. Checking
path metadata before open can reject obvious non-regular paths but is subject to
replacement races. Opening first and checking `os.fstat()` validates the actual
descriptor, but a normal blocking open of a FIFO can already block. On POSIX,
an implementation can investigate a non-blocking descriptor open followed by
`fstat()` and then permit reads only after `S_ISREG`; that is not yet established
as the project's portable contract. A later RFC should choose the supported
platform statement and exact open/check ordering rather than hiding it in code.

### Bounded-read findings

Metadata size is not sufficient validation: it cannot prove UTF-8, can be
stale after a file changes, and is not authoritative for special or virtual
objects. A metadata precheck is therefore optional optimization, not a safety
boundary.

The robust necessary boundary is the existing short-read-safe raw-byte pattern:
read no more than 65,537 bytes in total, reject as soon as the 65,537th byte is
observed, retain no more than that amount, and do not drain an oversized file.
This remains correct if a regular file changes, reports surprising metadata, or
performs short reads. No truncation or partial transmission is permitted.

### UTF-8 findings

File contents should follow the existing stdin rule exactly: raw bytes followed
by explicit strict UTF-8 decoding. Locale text decoding, replacement decoding,
charset detection, and format detection would make the accepted source less
deterministic.

Strict UTF-8 preserves a valid leading BOM as the actual Unicode character
`U+FEFF`. `utf-8-sig` would silently remove it. The smallest consistent rule is
therefore no BOM-specific machinery: preserve strict-decoded source content,
then let `SummarizeRequest` validate it unchanged.

### Empty and whitespace-only files

After successful bounded reading and strict decoding, empty and whitespace-only
contents should reach `SummarizeRequest`. It remains authoritative for rejecting
them, yielding the existing invalid-input result: exit 2, empty stdout, and one
stable stderr line. If only regular files are accepted, `/dev/null` is rejected
earlier as non-regular but has the same public result.

### Filesystem failure behavior

Missing paths, permission denials, directories, broken links, removal or
replacement between parsing and open, ordinary read failures after partial
bytes, path/operating-system errors, symbolic-link loops, and descriptor
exhaustion are all local source-selection failures. The evidence supports
mapping them to `error: invalid request input`, with no new public file-error
category.

A distinct stable file error would expose more distinction but does not provide
an action that is both reliably classified and safe to describe without paths
or operating-system details. The existing generic local-input line is already
stable, privacy-safe, and prevents exceptions and partial contents from
leaking. It must omit supplied and resolved paths, targets, permissions,
owners, mount points, working directories, and raw exception details.

### Race and consistency semantics

No `stat` result, path name, or pre-open existence check can promise stable
file contents. A path can be replaced, a target changed, or a file appended or
truncated during the command. The command should not add locking, snapshotting,
checksums, retries, or stability guarantees.

The smallest truthful implementation-facing statement to evaluate is: the
command summarizes the bounded bytes successfully read from the opened regular
file descriptor during that invocation. This is compatible with the existing
one-complete-document boundary because it still validates and sends one final
complete byte sequence; it makes no promise that the path names a durable or
unchanged snapshot.

### Request and output boundaries

File source handling must finish before one `SummarizeRequest` construction,
HTTP-client construction, and network activity. The future flow remains:

```text
source selection -> bounded file read -> strict UTF-8 -> SummarizeRequest
                 -> HTTP client -> one POST /v1/summarize
```

Content, verbose, and JSON output remain source-neutral. No filename, path,
metadata, attribution, or result field is added to any output mode.

## Privacy boundary

A supplied path, resolved path, symlink target, current working directory, and
filesystem metadata can all be private even when the content is hidden. Default
logs and every public failure must omit them, along with source text, partial
bytes, decoding exceptions, raw read exceptions, owner/permission data, runtime
URLs, machine details, and stack traces. File content must not be retained,
echoed on failure, cached, logged, or added to request history.

If later documentation uses examples, repository-relative public names such as
`README.md` and `docs/operator-workflow.md` are safer than real operator paths.

## Testability

A later implementation can remain deterministic without a runtime:

* temporary regular files for relative and absolute paths, valid ASCII and
  multibyte UTF-8, whitespace preservation, exact 65,536-byte acceptance, and
  65,537-byte rejection;
* an injected or narrowly wrapped opened file object for short reads and read
  failure after partial bytes;
* missing path and directory tests on every supported platform;
* symlink-to-regular and broken-link tests where symlinks are supported;
* an unread stdin stream proving `--file` precedence;
* parser tests proving `--text` plus `--file` is an explicit local conflict;
* an HTTP-client factory that fails if constructed, proving invalid file cases
  do not construct it; and
* request-capture tests proving one valid file makes one unchanged
  `/v1/summarize` POST and retains all output modes.

Permission-denied, FIFO, device, procfs, and descriptor-exhaustion tests are
not portable across users or platforms and should not be required for the first
automated suite. Linux/POSIX observations about FIFOs and non-blocking open
must be labeled as such. No live runtime is needed for local input validation.

## Alternatives considered

* **Keep `--text` and stdin only.** Lowest scope and still valid, but does not
  provide one explicit reusable-path spelling.
* **Allow `--text` and `--file` with precedence.** Rejected: two explicit
  values are reliably known and should fail clearly rather than silently discard
  one.
* **Detect file-plus-stdin conflict.** Rejected: stdin is inherited and may be
  unread; content detection needs a read or probe and adds the same false or
  blocking behavior rejected for `--text`.
* **Use `--file -` as stdin.** Rejected: stdin already has a source form and
  the alias would create two spellings and special path rules.
* **Expand paths inside the application.** Rejected: shell-like expansion,
  globs, and lookup rules create a new path language and privacy ambiguity.
* **Accept every readable byte stream.** Rejected: it broadens the CLI into a
  special-file/stream interface and permits blocking or unbounded-source
  semantics.
* **Use only metadata size checks.** Rejected: metadata can be stale and says
  nothing about UTF-8 or later file changes.
* **Use only bounded reads for every path.** Rejected for the first file
  contract: bounded reads control memory but do not prevent special-file open
  and blocking semantics.
* **Use `utf-8-sig`.** Rejected: it silently changes valid source content.
* **Add a public file-read error.** Rejected: it adds taxonomy without a
  reliably safe, actionable distinction.
* **Introduce a generic source/document abstraction.** Rejected: three known
  command sources do not justify a framework.

## Recommended smallest contract

Subject to a later RFC:

1. At most one explicit source option is allowed: `--text` or `--file`; the
   parser rejects their combination and repeated values. With neither option,
   stdin remains the source.
2. `--file` takes precedence over unused stdin and never reads or probes it.
3. A file path has ordinary process-working-directory semantics, with no
   application expansion or `-` alias.
4. Only a regular opened file is accepted; normal symlink resolution may be
   allowed only when the resulting descriptor is regular. The RFC must state
   the portable safe open/type-check strategy.
5. Read raw file bytes with the existing 65,537-byte bounded short-read loop;
   reject oversized content without truncation or draining.
6. Strict-decode UTF-8 without BOM removal, then pass unchanged text to
   `SummarizeRequest` before HTTP construction.
7. All ordinary invalid file, decoding, and read conditions use the existing
   one-line invalid-input error, with no path or exception leak.
8. Preserve one native POST, existing result validation, output modes, timeout,
   routing, runtime, and topology behavior.

## RFC-required decisions

The following durable decisions need an RFC before implementation:

* whether this explicit file path belongs in the ordinary summarize contract;
* the exact mutual-exclusion and stdin-precedence wording;
* the accepted platform/path semantics and supported path types;
* whether only regular files are accepted, including the safe portable
  open-and-`fstat` ordering and symbolic-link policy;
* the precise file-change consistency statement;
* whether all ordinary filesystem failures use invalid input, as recommended;
* the required automated proof boundary and any supported-platform statement;
  and
* the minimal post-implementation user documentation.

## Deferred work

Deferred to independent decisions are positional paths, multiple `--file`
options, multiple files, directories, recursion, globs, URLs, clipboard input,
PDF/DOCX/HTML/Markdown/source parsing, MIME or format detection, compressed
files, archives, charset detection, automatic chunking, map/reduce,
truncation, streaming, watching, locking, snapshots, checksums, retries,
stdin aliases, automatic expansion, model/runtime/node selection, routing,
endpoint or request-model changes, generic document/stream abstractions, a new
roadmap phase, and Phase 19.

## Non-goals

This investigation does not add or decide `hac summarize <path>`,
`hac summarize --file -`, multiple `--file` values, multiple files, directory
input, recursive traversal, or any file-format interpretation. It does not
modify the existing native endpoint, source limit, timeout, request model,
response model, routing, adapters, runtime behavior, topology, output modes,
or privacy defaults.
