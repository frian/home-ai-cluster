# RFC-0069: Explicit Aider Target Creation

Status: Accepted

Date: 2026-08-13

Author: frian

## Summary

This RFC narrowly amends RFC-0068's target-existence rule. For `hac aider
--file PATH --message TEXT`, the project-owned caller edge may create exactly
the explicitly supplied missing target as one empty file when its existing
parent is a directory. Aider then retains all target-content reading and
editing authority.

No parent, sibling, multiple, generated, inferred, or content-populated file is
authorized. HAC core remains text-only. Where this RFC differs from RFC-0068
only on target existence and creation, this RFC governs after acceptance.

## Problem

RFC-0068 requires the single caller-selected target to exist. That keeps
filesystem authority narrow, but adds an unnecessary manual `touch` step to the
primary small-script use case before the one-shot caller edge can invoke Aider.

The project needs the smallest explicit decision that lets the operator name a
new target directly without turning the caller edge into a general filesystem
or repository tool.

## Goals

- Remove the separate empty-target creation step for one explicitly supplied
  Aider target.
- Preserve operator ownership of the path and Aider ownership of target content.
- Keep HAC core text-only and the caller edge's filesystem authority bounded.
- Preserve every RFC-0068 request, lifecycle, routing, compatibility, privacy,
  and one-shot boundary other than target existence.

## Non-goals

This RFC does not authorize parent-directory or sibling creation, multiple
targets, candidate-path discovery, filename selection, prompt-derived paths,
repository/workspace discovery, repository inspection, patch application,
content population by the caller edge, rollback deletion, or any filesystem,
repository, shell, Git, test, lint, tool/function, or execution authority for
HAC core. It does not change Aider 0.86.2, one explicit message, the private
loopback translator, request-count limits, native `capability=code`, no retry,
no Chat fallback, persistent/interactive Aider exclusion, RFC-0031 Chat-only
compatibility, or the pending physical RFC-0067 proof.

## Proposal

### Explicit target rule

For `hac aider --file PATH --message TEXT`, only one operator-supplied PATH is
accepted.

1. If PATH exists and denotes the accepted single-file target, RFC-0068
   behavior is unchanged: the caller edge does not edit its contents and Aider
   owns target reading and editing.
2. If PATH does not exist, its parent must already exist and be a directory.
   The caller edge may create exactly PATH as one empty file using
   non-overwriting creation semantics. It must never truncate, replace, or
   overwrite an existing target. If PATH becomes present between absence
   validation and creation, the edge must fail safely or continue only under
   the accepted existing-single-file rule; it must never truncate that path.
   After creation, Aider owns target reading and editing; the caller edge must
   not write generated or model content into the target.
3. An existing non-file target fails. The edge creates no parent directories,
   sibling files, multiple targets, or paths discovered or inferred from a
   prompt. It does not inspect repository semantics, apply patches, or populate
   the new file itself.

The path remains explicitly operator supplied. This is not a generic new-file
workflow, workspace model, repository-root lookup, filename-generation rule, or
extension policy.

### Prerequisites before target creation

Before creating a missing target, the caller edge completes non-mutating
prerequisite validation: command/input validation, target-parent validation,
and the external Aider presence and version validation required by RFC-0068.
Invalid input, missing Aider, or an unsupported Aider version therefore creates
no target. Only after those prerequisites pass may the edge create the
explicitly requested missing empty target.

### Authority and failure boundary

RFC-0068's project-owned caller edge gains exactly one additional
caller-visible filesystem action: creation of the explicitly requested missing
target as an empty file. Its filesystem authority is limited to that action and
its own private temporary integration material. This is not HAC core authority.

HAC core remains text-only and gains no filesystem or repository access, file
creation/editing, shell, Git, test/lint, tool/function, or generated-code
execution authority. Aider still owns target content reading and editing.

After the edge successfully creates the explicit empty target, a later failure
does not delete it. A failed invocation may therefore leave the explicitly
requested file present, empty, or modified by Aider. Existing targets are never
deleted. This avoids destructive rollback after Aider may have created
caller-owned work and avoids target-inspection semantics.

## Rationale

Creating exactly the named empty file removes a pointless manual step while
keeping the decision visible: the operator selected the target path. Requiring
an existing parent limits the new authority to one leaf file and avoids
recursive directory creation or path discovery. Leaving content entirely to
Aider preserves the RFC-0068 authority partition and keeps HAC core text-only.

## Alternatives considered

### Keep requiring operator `touch`

Rejected. It is unnecessary friction for the primary new-small-script workflow.

### Allow an arbitrary Aider or caller-edge new-file workflow

Rejected. It would make path and file-creation authority broader and less
explicit than one named empty leaf target.

### Create exactly one explicit empty target

Selected. It removes the manual step while retaining an operator-supplied path,
existing parent, and Aider ownership of all target content.

### Create missing parent directories automatically

Rejected. Directory creation expands filesystem authority without being needed
for this narrow workflow.

## Trade-offs

The benefit is direct new-script creation with no separate empty-file command.
The cost is one bounded caller-edge filesystem write. The path is explicit, the
parent already exists, only one empty file may be created, and no content,
repository, or directory authority follows. This is materially smaller than
general file or repository authority.

## Impact and implementation boundary

After acceptance, a later RFC-0068 implementation may accept an existing
target or create one explicitly named missing empty target with an existing
directory parent. No other implementation behavior is authorized by this RFC.
This RFC does not implement that change.

## Open questions

None within this narrow amendment.

## Decision

Accepted. RFC-0069 narrowly amends RFC-0068 only for target existence and
creation; all other RFC-0068 architecture remains unchanged.

`hac aider --file PATH --message TEXT` may use an existing accepted single-file
target. If PATH is missing, its parent must already exist and be a directory.
Only after command/input, parent, and required Aider 0.86.2 prerequisite checks
pass, the caller edge may create exactly PATH as one empty file. Creation uses
non-overwriting semantics and must never truncate, replace, or overwrite an
existing path. If PATH appears during creation, the edge must fail safely or
continue only under the accepted existing-file rule.

The caller edge creates no parent directories, sibling files, inferred paths,
or additional targets, and never writes generated or model content into the
target. Aider owns target-content reading and editing. After the explicit target
is created, a later failure does not roll it back or delete it; a failed
invocation may leave the requested target empty or Aider-modified.

HAC core remains text-only and gains no filesystem, repository, editing, shell,
Git, test, lint, tool, or execution authority.
