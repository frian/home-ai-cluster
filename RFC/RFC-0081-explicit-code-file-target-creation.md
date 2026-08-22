# RFC-0081: Explicit Code-File Target Creation

Status: Accepted

Date: 2026-08-22

Author: frian

## Summary

This RFC proposes a narrow amendment to accepted RFC-0080. The existing
optional caller edge:

```text
hac code-file --file PATH --message TEXT [--timeout-seconds SECONDS]
home-ai-cluster code-file --file PATH --message TEXT [--timeout-seconds SECONDS]
```

would also accept exactly one explicitly named missing PATH when its parent
already exists as a directory. After non-mutating validation, the caller would
create only that empty leaf with exclusive non-overwriting semantics, then use
the unchanged RFC-0080 one-request, closed-envelope, atomic-replacement flow.

The command surface does not change. Existing-target behavior remains entirely
under RFC-0080. This proposal grants no filesystem authority to HAC core and no
model-selected path, repository, execution, retry, or agent authority.

## Problem

RFC-0080 deliberately requires an already-existing selected target. The
retained real-model proof shows that its bounded whole-file caller works
end-to-end, but an operator creating a small script still needs a separate
empty-file step before invoking `hac code-file`.

The project should consider removing only that friction without turning the
caller into a file manager, repository tool, patch system, or coding agent.

## Goals

- Let one explicitly named missing leaf become the selected `code-file` target.
- Preserve operator ownership of the exact path and RFC-0080's one native
  `capability=code` request, response validation, replacement, failure,
  privacy, and permission behavior.
- Validate all possible input and prospective-request conditions before
  creating a missing target.
- Use simple exclusive creation and fail safely on a creation race.
- Keep HAC core text-only and preserve the existing Aider caller unchanged.

## Non-goals

This RFC does not authorize parent-directory or sibling creation, multiple new
files, directory or symlink targets, inferred or model-selected paths,
repository awareness, extension or language inference, executable-bit or
shebang interpretation, ownership/ACL/xattr policy, patches, diffs, renames,
moves, deletion, rollback deletion, locking, conflict handling, Git, shell,
linting, testing, generated-code execution, semantic code inspection, retry,
repair, reflection, agents, compatibility expansion, a new endpoint or
capability, or model/runtime/node selectors.

It does not alter `hac aider`, RFC-0069, RFC-0080 existing-target behavior, or
the existing command names, arguments, timeout semantics, native route, or
response envelope.

## Proposal

### Caller surface and existing targets

The public caller surface remains exactly:

```text
hac code-file --file PATH --message TEXT [--timeout-seconds SECONDS]
home-ai-cluster code-file --file PATH --message TEXT [--timeout-seconds SECONDS]
```

There is no `--create` flag, alternate command, or standalone executable. If
PATH exists, it must remain the RFC-0080 regular non-symlink UTF-8 target. Its
reading, request construction, response validation, atomic replacement,
permission preservation, failures, privacy, and one-request behavior are
unchanged.

### Missing-target admission and ordering

When the exact operator-supplied PATH is absent, its parent must already exist
and be a directory. Before creating a leaf, the caller completes every
non-mutating check that does not require the target:

1. CLI and input validation, including one non-blank message and timeout
   parsing.
2. Exact path and parent validation, including existing-parent-directory
   validation.
3. Construction and validation of the prospective RFC-0080 request with
   `current_content = ""`, including RFC-0067's aggregate 65,536 UTF-8-byte
   request bound.

Invalid input, an oversized prospective request, a missing parent, or a
non-directory parent therefore creates no file and makes no native request.

After those checks pass, the caller may create exactly PATH as an empty regular
file using exclusive non-overwriting semantics. It creates no parent directory,
sibling, inferred filename, extension, or repository location. The model never
receives PATH, its basename, parent, or filename; the request continues to
contain only the fixed RFC-0080 system instruction and deterministic user JSON
with `instruction` and `current_content`.

If another filesystem object appears after absence validation and before
exclusive creation, creation fails safely. The invocation must not truncate,
replace, silently adopt, or continue under existing-target rules for that path.
An operator may make a separate later invocation, which then uses ordinary
RFC-0080 existing-target semantics if the path qualifies.

### One native request and replacement

After successful exclusive empty-leaf creation, the new file becomes the
ordinary RFC-0080 selected target. The caller makes exactly one native
`POST /v1/chat` request with explicit `capability=code`, no retry, corrective
request, or continuation. The existing closed response envelope, generated
content bound, UTF-8 encoding, and atomic replacement behavior apply unchanged.

No native model request occurs before successful creation. If replacement
succeeds, the selected file contains the complete validated result.

### Initial permissions and later failures

The caller requests ordinary non-executable creation mode `0o666`, subject to
the invoking process's normal filesystem umask. The actual ordinary `0o777`
permission bits of that created target then become the mode that RFC-0080's
private temporary replacement preserves. The caller does not request executable
bits or impose a chmod-to-0644, ownership, ACL, xattr, shebang, or
extension-based policy.

Once exclusive creation succeeds, a later cluster, timeout, request, envelope,
output-bound, temporary-replacement, or permission-preparation failure must not
delete the empty target. A failed invocation may therefore leave the explicitly
requested new file present and empty. No rollback deletion occurs.

This proposal adds no general locking, inode tracking, conflict detection,
filesystem transaction, watcher, or concurrent-writer guarantee. It adds only
exclusive first creation of one missing leaf. Later unrelated changes, removal,
or replacement of that file remain outside the first-version concurrency
boundary.

### Authority, privacy, and Aider boundary

The sole additional caller-edge authority is creation of the exact
operator-supplied missing leaf as one empty regular file. HAC core remains
unchanged and text-only. The model has no target-selection or filesystem
authority, and generated content is never executed.

RFC-0080 privacy behavior remains unchanged: no prompt, result, retry, audit,
file-creation history, database, daemon, cache, or configuration is added.
The requested new file is ordinary operator-requested local filesystem
material.

RFC-0069 remains Aider-specific and is neither amended nor superseded. It is
useful precedent for exact leaf creation, an existing parent, non-overwriting
semantics, and no rollback deletion, but this RFC defines the independent
`code-file` rule explicitly. `hac aider` remains unchanged.

## Rationale

Creating the exact empty leaf before the request removes the demonstrated
manual `touch` friction while retaining an explicit operator-selected path and
simple failure semantics. Validating the prospective empty-content request
first prevents invalid input or an oversized request from creating filesystem
material. Exclusive creation resolves the required creation race without
inventing a content-publication protocol.

Leaving a successfully created empty file after a later failure avoids
destructive rollback once another process may have observed or changed it. The
operator asked for that exact path; deletion would add ownership and concurrency
claims that this small caller edge does not need.

## Alternatives considered

### Keep requiring manual `touch`

Rejected. It is the safest baseline but is now demonstrated unnecessary friction
for the narrow small-script workflow.

### Add `--create`

Rejected. Target existence does not alter the operator's intent or the caller
lifecycle. A new flag expands surface area without reducing authority.

### Generate first, then publish content only if absent

Rejected. Portable non-overwriting publication of prepared content would add
filesystem semantics beyond this narrow step. Exclusive empty-leaf creation
before the one native request is sufficient.

### Create one exact empty leaf before the native request

Selected. It keeps path authority explicit, validation finite, and the existing
RFC-0080 replacement path intact.

### Create missing parent directories

Rejected. Recursive directory creation is unnecessary authority expansion.

### Delete the leaf when a later request fails

Rejected. Rollback deletion risks removing a path observed or modified after
creation and adds destructive concurrency semantics.

### Continue automatically if the target appears during creation

Rejected. The race fails safely; a new explicit invocation may use the ordinary
existing-target rule.

## Trade-offs

The proposal removes one manual preparation step at the cost of one tightly
bounded caller-edge write. The new target may remain empty after a later
failure, which is a deliberate, visible trade-off for avoiding unsafe rollback.
The caller still does not promise code quality, atomic publish-if-absent of
generated content, or concurrent-writer protection.

## Impact

If accepted, a later separate implementation PR may remain localized to
`src/home_ai_cluster/code_file_command.py`,
`tests/test_code_file_command.py`, and current operator documentation. It need
not change core models, routing, runtime adapters, compatibility, Aider,
dependencies, or API contracts.

A later model-free proof must cover successful creation with an existing parent;
empty `current_content`; exactly one path-free native code request; initial
`0o666` creation subject to umask and preserved resulting mode; missing or
non-directory parent failure before creation/request; invalid and oversized
input before creation; creation-race failure without a request or target
modification; later native, envelope, output-bound, and temporary-replacement
failures leaving the target present and empty; unchanged existing-target and
symlink/non-regular rejection; and no rollback, retry, tools, execution, parent
creation, or extra target.

## Open questions

None within this proposed bounded amendment.

## Decision

Accepted. RFC-0081 narrowly amends RFC-0080 only to permit exclusive creation
of one explicitly operator-supplied missing leaf after the defined
non-mutating validation. All other RFC-0080 behavior remains unchanged.
