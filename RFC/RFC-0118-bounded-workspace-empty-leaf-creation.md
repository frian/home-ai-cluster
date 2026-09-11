# RFC-0118: Bounded Workspace Empty-Leaf Creation

Status: Draft

Date: 2026-09-11

## Context

Accepted RFC-0114 provides one caller-local workspace namespace with explicit
`list`, `read`, and existing-file `write` authority. Accepted RFC-0116 composes
that authority with ordinary bounded Code inference through a closed action
grammar and a finite action budget. Accepted RFC-0117 exposes that composition
as `hac code-workspace` with explicit per-invocation grants.

The retained RFC-0117 real-operator proof established model-directed `list`
and `read`, truthful refusal of a missing-target `write`, inability to bypass
that refusal, finite termination of repeated unproductive actions, successful
existing-file replacement, subsequent read, and independent physical host
verification of that replacement. It also established a concrete product
friction: an otherwise workspace-aware interaction cannot create a new source,
test, documentation, configuration, or other ordinary file unless the operator
first creates the target manually.

Keeping that manual `touch` step permanently is too restrictive. This RFC
proposes exactly one additional, independently granted workspace operation:
empty-leaf creation. It does not reopen RFC-0114's namespace, threat model,
routing boundary, or existing operation semantics.

## Proposal

This RFC would narrowly amend RFC-0114, RFC-0116, and RFC-0117. The workspace
operation vocabulary would become:

```text
list
read
write
create
```

`list`, `read`, and `write` retain their accepted meanings. In particular,
`write` remains complete replacement of one existing regular UTF-8 file; it
must not silently acquire missing-target creation authority.

`create` is a separate explicit authority. Replacing an existing object and
extending the workspace namespace with a new object are materially different
authorities. An existing `--grant write` must therefore not broaden, an
operator may grant `write` without namespace extension, and may grant `create`
without permission to modify an existing file. This is intentional authority
design, not unnecessary abstraction.

The resulting boundary is simple:

```text
write  may replace one existing file
create may add one empty file in one existing directory
neither creates directories
```

## `create` operation

The model/caller-visible operation is conceptually exactly:

```text
create(path)
```

It has no content field. A successful action creates exactly one new empty
regular file whose content is exactly zero bytes. Content population is a later
separate `write(path, content)` action, and independently requires `write`
authority. This RFC neither defines `create(path, content)` nor permits an
implementation to hide empty creation and replacement inside one conceptual
action.

One action has one clear commit point which the existing `success`/`refused`
outcome vocabulary can represent honestly. `create` has no request content
payload, so RFC-0114's 1 MiB replacement-content bound does not apply directly
to it. A successfully created zero-byte file is trivially valid UTF-8; the
existing strict UTF-8 and 1 MiB rules continue unchanged for a later `write`.

## RFC-0114 amendment: workspace admission and host semantics

`create(path)` uses exactly RFC-0114's logical path grammar. The special path
`.` is not a valid file target, and the complete logical path remains bounded
to 4,096 UTF-8 bytes before host translation or filesystem access. RFC-0114's
redirection-traversal prohibition and its deliberate exclusion of strong
protection against malicious same-user concurrent namespace replacement remain
unchanged.

For a requested create action:

1. the final leaf must currently be absent;
2. its parent must already exist and, under RFC-0114 resolution rules, be a
   real directory inside the granted logical namespace;
3. every parent component must remain inside that namespace and must not
   deliberately traverse a redirection object;
4. no parent, sibling, inferred path, or directory may be created; and
5. ordinary host permissions remain authoritative.

An existing final regular file, directory, redirection object, device, FIFO,
socket, or any other object causes refusal. Creation never overwrites,
truncates, adopts, or otherwise modifies an existing final object. No filename
extension, language, repository, `.gitignore`, hidden-file, sensitive-file,
credential-name, or other heuristic policy is introduced. This RFC adds no
repository awareness or filesystem-provenance policy.

On POSIX-like hosts, HAC requests ordinary non-executable creation permissions
equivalent to mode `0o666`, subject to the invoking process's normal umask. It
must not infer executable permissions from extension, shebang, content, or
model intent, and adds no chmod behavior. HAC makes no promise to preserve or
normalize ownership, ACLs, extended attributes, timestamps, or other
platform-specific metadata. On non-POSIX hosts, ordinary host creation and
permission semantics remain authoritative; this RFC claims no false
cross-platform equivalence.

### Exclusive creation and races

Creation uses a boring exclusive, non-overwriting host primitive:

```text
validate logical request and parent
    ->
attempt exclusive creation of exactly the requested missing leaf
    ->
success, or fail closed if an object occupied that name before commit
```

If another object appears before exclusive creation commits, HAC fails closed.
It does not adopt the object, fall back automatically to `write`, truncate it,
or retry. A later explicit model action within the same bounded RFC-0116
interaction may independently request `read` or `write` for that path if the
relevant grants exist. That is a new authority decision and consumes its own
action-budget unit; it does not require a new CLI invocation merely because a
creation race occurred.

This retains RFC-0114's boundary: it adds neither directory-fd confinement,
locking, transactions, watchers, sandboxing, nor platform-specific confinement
to defend against malicious same-user concurrent namespace replacement.

### Commit and failure truth

The exclusive host creation primitive is the create action's single commit
point. Once it has successfully created the new empty leaf, creation is
committed. HAC must not later report that the filesystem creation itself did
not occur, and must not delete it as rollback.

Later inference failure, later `write` refusal or failure, action-budget
exhaustion, malformed or oversized later model output, later Code-context
failure, or observer/foreground-presentation failure does not undo creation.
A command or interaction can terminate later for a separate reason, just as
accepted post-write truth distinguishes committed filesystem state from later
presentation or continuation failure. This RFC introduces no transactional
rollback.

## RFC-0116 amendment: closed action contract

RFC-0116's closed model-response/action vocabulary would gain exactly one
fourth workspace action: `create`. Its request contains the existing closed
response framing's operation/kind identifying workspace creation and one
logical `path`; it contains no content.

No existing `final`, `list`, `read`, or `write` framing changes except as
mechanically necessary to admit this fourth closed operation. The existing
limits remain unchanged:

- at most eight actually dispatched workspace actions;
- at most nine Code inferences; and
- one dispatched `create` consumes one action-budget unit, while a subsequent
  `write` consumes another.

The project does not increase either bound merely because creation followed by
population takes two actions.

Completed actions retain exactly the accepted outcome vocabulary:

```text
success
refused
```

`create` must fit that vocabulary truthfully. This RFC adds no partial-success,
committed-with-warning, terminal-status, or transaction-state outcome. The
completed-action observer's operation vocabulary extends mechanically from
`list | read | write` to `list | read | write | create`, with the same
synchronous ordering and failure behavior. A committed create remains
physically true if a later observer failure terminates the interaction.

## RFC-0117 amendment: explicit operator surface

`hac code-workspace` would gain one additional valid explicit grant:

```text
--grant create
```

There is no default grant and no implicit relationship among grants. Valid
non-empty authority sets include `--grant create`, `--grant write`, both
`--grant create --grant write`, and every other existing non-empty explicit
subset of the four known operations. To create and populate a new file requires
both `create` and `write`, unless the desired result is intentionally empty.

Duplicate grants remain idempotent under RFC-0117's existing rule, and grant
order remains semantically meaningless.

For every actually dispatched and resolved create action, RFC-0117's
foreground stderr presentation must be able to present conceptually:

```text
workspace create "<logical path>": success
workspace create "<logical path>": refused
```

The existing safe single-line logical-path rendering requirements apply without
changing RFC-0114 path semantics. This adds no JSON event output, verbose mode,
retained history, status, audit log, or observability subsystem.

## Authority, routing, and privacy boundaries

RFC-0069 and RFC-0081 are useful boring-creation precedents: missing leaf,
existing parent, exclusive non-overwriting creation, ordinary host permissions,
and no rollback deletion. They authorize an exact operator-selected target.
This proposal is deliberately different: the model-controlled caller selects a
logical leaf within an operator-selected workspace namespace and explicitly
granted `create` operation.

The authority model is:

```text
operator selects workspace root + explicit operations
    ->
untrusted/model-controlled caller selects logical paths in that namespace
```

That model already applies to RFC-0114/RFC-0116 `list`, `read`, and `write`.
This RFC extends it only by one visible namespace-extension operation. It does
not require operator pre-approval of every future leaf, because that would
substantially recreate the manual pre-creation friction this authority removes.

Creation remains entirely caller-local filesystem authority. It does not become
a cluster capability; affect eligibility, routing, fallback, runtime/model
selection, or request types; add a remote filesystem protocol; disclose the
physical root or grants to a remote Code node as filesystem authority; or add
retained workspace configuration. Ordinary Code inference may remain local or
explicitly routed remotely under RFC-0116. Only ordinary textual interaction
context may cross that boundary, including logical action requests and their
textual outcomes; actual filesystem authority remains caller-local.

## Non-goals

This RFC does not authorize mkdir, recursive parent creation, directory
creation of any kind, delete, rename, move, append, patch/diff or
search/replace APIs, chmod, executable-bit inference, Git or repository
semantics, shell/process execution, tests, lint, command allowlists, generic
tools/functions, generic agents, plugin frameworks, remote filesystem access,
filesystem backend abstractions, retained workspace grants, default workspace
authority, browser workspace authority, workspace HTTP APIs, a database,
daemon, background worker, retries, or transactional rollback.

It does not broaden the separate observed `src/example.py` model-contract
behavior. That remains an independent implementation and prompt investigation.

## Rationale

The RFC-0117 proof shows that bounded workspace interaction is real, and that
missing-target refusal cannot be bypassed. The remaining manual pre-creation
step is therefore an exposed product boundary, not a hypothetical convenience
request. A separate empty-only action removes that friction while preserving
simple grants, a clear commit point, bounded action count, and RFC-0114's
caller-local authority ownership.

Separating namespace extension from existing-file replacement makes the extra
authority both visible and independently rejectable. Empty-only creation avoids
making a single outcome falsely describe an action whose content publication
could fail after the namespace change has committed.

## Alternatives considered

### Keep requiring manual pre-creation

Rejected. The real RFC-0117 proof demonstrated concrete mechanical friction
after the bounded workspace path had otherwise succeeded.

### Broaden `write`

Rejected. Replacing an existing object and extending the namespace are
materially distinct authorities; an existing `--grant write` must not silently
broaden.

### `create(path, content)`

Rejected for the first increment. Simple exclusive creation can commit the leaf
before content publication fails, which the single `success`/`refused` outcome
cannot represent truthfully without more architecture.

### One conceptual create implemented as hidden empty-create plus write

Rejected. The hidden replacement can fail after an empty leaf has committed,
leaving a partially committed conceptual action that the accepted outcome
contract cannot describe honestly.

### Exact per-file operator create allowlist

Rejected. It largely recreates manual pre-creation and path prediction, and
conflicts with the established workspace namespace-times-operation authority
model.

### Automatic mkdir

Rejected. It is unnecessary authority expansion.

### Rollback deletion after later failure

Rejected. Deletion after publication introduces destructive concurrency and
ownership semantics, and makes committed filesystem truth less reliable.

## Trade-offs

The strongest argument against this proposal is real: granting `create` lets a
model-controlled caller extend the selected workspace namespace with new names.
Those names may matter to other software, including configuration, hidden,
source, or repository-internal files. This is qualitatively stronger authority
than replacement of operator-existing files and must not be described as “just
another write.”

The project would accept that authority only because the workspace root and
`create` grant are explicit; no grant is default; creation makes only one empty
regular leaf in an existing directory; no directory or executable permission is
created; content population separately requires `write`; action count remains
bounded; and filesystem authority remains caller-local.

## Implementation boundary

If accepted, this RFC would amend only the operation, action, and grant
vocabularies described above. A later implementation must preserve all existing
behavior otherwise: RFC-0114's vocabulary becomes `list/read/write/create`,
`create(path)` means exclusive empty-leaf creation only, RFC-0116 admits the
closed `create` action, and RFC-0117 admits `--grant create`.

It would not authorize implementation beyond that accepted boundary, nor any
change to code, tests, routing, capabilities, remote authority, product
behavior outside a later implementation decision, or the non-goals above.

## Decision

Draft. This RFC proposes one narrow fourth independently grantable workspace
operation, `create`, for exclusive creation of one model-selected empty logical
leaf inside an explicitly operator-granted RFC-0114 namespace. It leaves
`list`, `read`, and existing-file `write` unchanged; extends RFC-0116's closed
action grammar and RFC-0117's explicit grants mechanically; and preserves
caller-local authority, finite action/inference bounds, and truthful committed
filesystem state without rollback.
