# Aider Whole-File Edit Reliability Investigation

Status: Investigation only

Date: 2026-08-16

## Question

Does an observed one-shot edit of an existing target that reports `Applied edit`
but leaves the target byte-for-byte unchanged show a Home AI Cluster defect or
an unaccepted architectural gap?

This record retains no target path, prompt, generated source, model identity,
or full terminal transcript.

## Accepted boundary

RFC-0068 fixes one `hac aider --file PATH --message TEXT` invocation to one
external Aider 0.86.2 invocation, at most one Aider-shaped request, and at most
one native `POST /v1/chat` request with `capability=code`.  It fixes the Aider
configuration to the whole-file edit representation, prohibits caller-edge
retries, and makes Aider—not Home AI Cluster—the owner of selected-target
reading and editing.

RFC-0069 only permits creation of one missing empty target after bounded
preconditions.  It does not change the existing-target editing boundary.

## Current implementation

The caller edge configures Aider's private model entry with `edit_format:
whole`.  Its private translator admits one strict Aider-shaped request,
preserves the ordered plain-text messages in one `ClusterRequest`, sends it as
`capability=code`, and projects only the resulting textual content back into
the Aider-shaped response.  It neither reads target contents nor compares,
rewrites, or otherwise interprets target bytes.

The command's successful outcome is bounded to a successful Aider subprocess
and one completed bridge request.  It does not currently mean that the target
bytes changed.

## Aider 0.86.2 whole-file contract

The installed Aider 0.86.2 source was checked against the upstream `v0.86.2`
tag.  Its whole-file prompt requires a filename line followed by a fenced,
complete updated file body and says not to omit or elide content.

Its `WholeFileCoder` parser is intentionally less strict than that prompt: it
can infer a filename from a preceding line, an earlier filename mention, or the
single chat file, and it accepts a currently open block at end of response.  It
does not verify that a parsed listing is a complete replacement body.  Its edit
application writes the parsed body to the selected path.  The surrounding
reporting code prints `Applied edit to <path>` for a parsed and prepared edit
path; it does not compare the file before and after the write.  Aider's
one-shot `--message` path can also return process success when no edit is
extracted.

Accordingly, an `Applied edit` line establishes that Aider parsed and attempted
an edit for that path, not that a byte difference was produced.

## Observed failure

One missing-target run produced a non-empty script.  Later existing-target runs
reported success while leaving the target unchanged, including after a trivial
comment-insertion request.  The visible response was not a complete whole-file
listing: it contained explanatory or marker material and a filename, but no
complete updated body.

The raw response is intentionally not retained.  The source evidence therefore
supports, but cannot reconstruct, the specific parse path.  The observation is
consistent with a response that did not satisfy the whole-file contract and
with Aider's permissive parser/reporting accepting a path without a resulting
byte difference.

## Source-level explanation

Aider—not HAC—parses the returned text.  In Aider 0.86.2, the strict
whole-file instruction is a prompting contract rather than a strict parser
validation boundary.  Once the parser yields a selected path, `apply_updates`
reports that path after attempting the write, without a byte-difference check.
That explains why the terminal wording can coexist with unchanged bytes.

If parsing instead yields no edit, Aider's one-shot message entry point does
not itself require an edited-file count before returning.  HAC then observes a
successful child process and its completed single bridge request, as RFC-0068
defines.  No evidence indicates a translation, routing, or native `code`
execution failure.

## HAC responsibility

HAC does not violate RFC-0068 or RFC-0069 on this evidence.  Its translator
preserves the accepted messages, sends the fixed native textual request, and
returns `ClusterResult.content` without changing it into an edit protocol.  It
has no authority or visibility to decide whether Aider parsed a valid whole-file
listing or whether the selected target changed.  RFC-0068 intentionally assigns
those concerns to Aider and excludes caller-edge target-content reading and
editing.

## Options

### A. No project change

The operator may select and evaluate another already-supported local model
using the ordinary model-selection configuration.  This leaves the fixed
whole-file representation, one-request lifecycle, and authority partition
unchanged.  It is the appropriate present action.

### B. Change project-owned prompting

Changing or adding project-owned instructions to force a response shape would
alter the fixed preserved-message/whole-file contract.  It is not an
implementation-only correction and would require an RFC.

### C. Change edit representation

Using another Aider edit format would change RFC-0068's fixed whole-file
representation.  It requires a new RFC.

### D. Retry after malformed output

A retry, including Aider reflection after malformed output, would create a
second qualifying Aider request and native request.  It conflicts with
RFC-0068's no-retry one-request boundary and requires a new RFC.

### E. Detect unchanged targets

Caller-edge byte-difference detection would introduce selected-target reading
and a new outcome authority outside the current Aider-owned editing boundary.
It requires a new RFC.

### F. Change success/reporting semantics

Treating an unchanged target as a HAC failure would be a new user-visible
caller-edge outcome contract and, in practice, needs the target observation in
option E.  It requires a new RFC.

## RFC impact

No amendment is justified by the present evidence.  Any future project change
to prompting, edit format, retry behavior, target-byte observation, or
success/reporting semantics is an Outcome C architectural change and needs a
new RFC before implementation.

## Conclusion

**Outcome A — no project change justified.**  The available evidence points to
model whole-file-response compliance and Aider 0.86.2 parsing/reporting
semantics, not to an HAC breach of RFC-0068 or RFC-0069.

## Recommended next step

An operator may manually try a different already-installed, explicitly selected
local model for the same bounded one-shot workflow, without downloads,
lifecycle changes, configuration expansion, retries, or HAC code changes.  If
that evidence establishes a product need for any option B through F, open a new
narrow RFC first.
