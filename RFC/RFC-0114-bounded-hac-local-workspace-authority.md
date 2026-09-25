# RFC-0114: Bounded HAC Local Workspace Authority

Status: Accepted

Date: 2026-09-09

Author: frian

## Summary

This RFC proposes one new, deliberately narrow, caller-local authority: a
bounded local workspace authority over one explicitly granted host filesystem
namespace.  A replaceable caller may choose what action to request, while HAC
itself owns and enforces what the explicit grant authorizes.

One authority instance is local to one HAC process, in memory, explicitly
constructed, non-retained, non-discoverable, non-global, and non-remote.  It
has one trusted operator/composition-selected existing directory as its fixed
workspace root and one explicit non-empty subset of these independently
grantable operations:

```text
list
read
write
```

Conceptually:

```text
operator / trusted composition
        |
        | explicit workspace + operation grant
        v
HAC local workspace authority
        |
        +-- list
        +-- read
        +-- write
```

The caller sees a closed logical relative workspace namespace, not the host
absolute root.  This RFC makes no choice of operator-facing CLI spelling,
retained configuration representation, HTTP route, plugin, or harness-facing
protocol.  Names such as `hac_list`, `hac_read`, and `hac_write` are only
possible future conceptual tool labels, not a public protocol.

This is not a cluster routing capability, inference adapter, filesystem
service, sandbox, or remote filesystem orchestration.  It neither chooses nor
depends on Pi or OpenCode; their bounded model-free feasibility investigation
is external to this product decision.

## Problem

A replaceable caller can usefully navigate, read, and replace existing text
files in one operator-granted local workspace.  Leaving that authority entirely
outside HAC either duplicates filesystem policy in every caller or asks HAC to
trust an external tool's policy.  Giving a caller ordinary host paths instead
would expose more authority than the intended local workspace operation.

HAC needs a small, explicit ownership seam: callers can request an operation,
but HAC independently validates the grant, the closed logical path language,
the target, bounds, encoding, and publication behavior.  This must remain
distinct from cluster eligibility and routing.

## Decision

The project accepts one concrete local workspace authority.  This RFC changes
no behavior.  Any implementation must be a separate, smallest model-free proof
of exactly this authority.

### Authority ownership and lifetime

Construction requires one trusted operator/composition input root which resolves
to an existing directory before the authority is usable.  The selected root may
use ordinary host operating-system path semantics.  It is never model-selected.
An instance is fixed to that root and to one explicit non-empty subset of
`{list, read, write}` for its entire lifetime.

The authority grants no implicit access to the current working directory, home
directory, filesystem root, repository root, Git worktree, or parent directory.
It is not retained configuration; deciding retained workspace grants is future
architecture.

Once constructed, physical root knowledge is not repeated by the caller.  The
grant is a workspace *namespace* grant, not an inode or object-provenance
grant: names reachable through accepted logical workspace names are inside the
grant, subject to the non-traversal rules below.  It does not claim that every
underlying object physically originated below the root.

Hard links therefore are not automatic escapes.  A regular file reached through
an accepted name below the workspace is within the grant even if another hard
link to that object is elsewhere.  Whole-file host replacement changes the
selected workspace directory entry; it does not promise to mutate every other
hard link to the old object.  HAC must not attempt inode-provenance enforcement.

Likewise, a workspace namespace backed by the host OS is not HAC
remote/distributed filesystem authority.  If an operator grants a root backed
by NFS, SMB, FUSE, a bind mount, mapped storage, or another host filesystem
mechanism, it remains in the grant.  Host filesystem I/O may use whatever
backing mechanism that trusted operator has exposed, including one that uses a
network.  HAC neither inspects, detects, classifies, nor prohibits that backing
because it may use a network; it need not determine physical storage locality
and must add no mount inspection, filesystem-type policy, remote-storage
detection, or network-filesystem rejection.

### Threat model and host boundary

Once a workspace and operation subset have been granted, every operation
request is untrusted.  A caller may be buggy, adversarial, prompt-injected,
model-controlled, or malformed.  HAC must enforce the workspace and operation
grant independently of caller intent.  An operation outside the explicit grant
fails locally before HAC performs its filesystem action.

This first authority does not isolate HAC from another malicious local process
already running with the same operating-system user authority.  In particular,
it promises no race-free confinement against arbitrary hostile concurrent
namespace replacement by such a process.  Host operating-system permissions
remain authoritative.  This is intentionally not a sandbox proposal: adding a
platform-specific security subsystem merely to defend against already-equivalent
same-user OS authority is outside this bounded decision.

### Closed caller-visible path language

Callers do not submit native operating-system paths.  The logical separator is
`/` on every supported platform.  The special path `.` means the workspace root
and is valid only where the operation meaningfully targets a root directory,
principally `list`.  Every other accepted path consists of one or more ordinary
segments separated by `/`.

Before filesystem access HAC rejects an empty path, leading or trailing `/`,
empty segments, `.` or `..` segments, backslash, colon, NUL, native absolute
syntax, Windows drive-absolute and drive-relative forms (including `C:foo`),
Windows root-relative forms, UNC forms, `\\?\\` extended namespace forms,
`\\.\\` device namespace forms, NTFS alternate-data-stream syntax, and any
other native namespace-escape syntax.  It performs no application-level `~`,
environment-variable, glob, repository-relative alias, or configuration
variable expansion.  Host-invalid or reserved names may additionally fail
locally.

The complete caller-supplied logical path string has a fixed maximum of 4,096
UTF-8 bytes, measured before host-path translation or filesystem access.  `.`
is within that bound.  UTF-8 encoding failure and a path over the bound are
invalid local input; HAC never truncates a path.  A 4,096-byte logical path may
still fail ordinary semantic validation or a host operating-system/filesystem
component or total-path limit.  HAC does not promise every path within its input
bound is representable or valid on every host.  The bound limits HAC-owned
input; it neither overrides host limits nor adds per-segment limits,
normalization, Unicode canonicalization, case folding, expansion, or native
path aliases.

### Filesystem redirection

The authority must not deliberately traverse caller-reachable filesystem
redirection objects: symbolic links, Windows junctions, or reparse-point
traversal that redirects resolution.  The rule is semantic rather than a
POSIX-only symlink claim.

A redirection object may be visible as a child in `list`, but `list` must not
traverse it.  It cannot be the final `read` or `write` target.  These rules do
not claim protection from a same-user process replacing a validated component
with a redirection object during a race window; that remains excluded hostile
concurrent namespace mutation.

### `list`

`list` targets exactly one existing workspace directory and may target `.`.  It
returns immediate children only: no recursion, globbing, search, Git
interpretation, repository inspection, or redirection traversal.  A successful
entry exposes only `name` and one minimal `kind`:

```text
file
directory
redirection
other
```

Dotfiles and hidden files are ordinary entries.  HAC must not silently filter
`.env`, `.git`, credential-looking files, or any other name.  A redirection can
be reported as `redirection` without becoming traversable authority.

The result is finite and complete-or-failure.  The first fixed bound is 1,024
immediate entries: if more are observed, the complete request fails rather than
returning a truncated apparently complete prefix.  Successful entries are in
deterministic name order.  There is no directory snapshot guarantee under
unrelated concurrent mutation.  If a host filename cannot be faithfully
represented in the textual caller contract, HAC fails the complete listing
rather than lossy-decoding, replacing characters, or omitting it.

### `read`

`read` targets exactly one existing final regular file.  It rejects a directory,
redirection object, FIFO, socket, device, and every other non-regular object.
It reads one complete observed byte sequence from one opened regular-file
object, returns strict UTF-8 text, and neither detects nor guesses another
encoding.  Empty UTF-8 content is valid.

The first maximum is 1,048,576 UTF-8 source bytes (1 MiB).  HAC enforces the
limit on bytes actually read rather than trusting pre-read metadata.  An
implementation may retain at most the bound plus one byte to detect overflow;
observing byte 1,048,577 fails with no partial content.  There are no
range/head/tail/chunk operations, truncation, snapshot, stable-path identity,
locking, checksum, retry, or coherent multi-read guarantees.  Truthful success
means HAC read the complete bounded byte sequence observed through one accepted
opened regular-file operation through observed EOF.

### `write`

`write` targets exactly one existing final regular file and accepts one complete
replacement string, strict-encoded as UTF-8.  Empty replacement is valid.  It
rejects missing targets, directories, redirection objects, FIFOs, sockets,
devices, and all other non-regular objects.  The first maximum is 1,048,576
UTF-8 replacement bytes.

This is whole-file replacement only: no append, patch, diff application,
search/replace, line edits, ranged writes, file or directory creation, delete,
rename, or move.  Creation is deliberately out of scope.  RFC-0080 and
RFC-0081 are useful incremental-authority precedents, but do not force a future
creation decision here.

The publication shape reuses RFC-0080 only as a publication precedent, not as
proof of workspace confinement:

```text
validate request and grant
    ->
validate target
    ->
validate complete UTF-8 replacement and bound
    ->
prepare private same-directory temporary replacement
    ->
complete all fallible pre-publication work
    ->
one same-directory host replacement/publication operation
```

HAC must not truncate the selected target in place.  Failure before final
publication leaves prior selected-target content unchanged.  HAC performs
exactly one same-directory host filesystem replacement/publication operation
after all fallible pre-publication work.  Once that operation has successfully
committed according to its host primitive, no later fallible cleanup or check
may falsely report failure.  There are no transaction libraries, locking,
journals, recovery daemons, conflict detection, compare-and-swap, repository
transactions, or protection from unrelated concurrent writers.

The HAC guarantee is this one same-directory host replacement operation after
complete pre-publication validation.  It is not a guarantee of stronger
atomicity, durability, visibility, cross-client atomicity on network filesystems,
snapshot isolation, or distributed transaction semantics than the host
filesystem replacement primitive exposes.  RFC-0080 is precedent for the
same-directory replacement shape, but this RFC's broader operator-granted host
namespace prevents HAC from promising more across arbitrary filesystems.

The RFC promises no preservation of inode identity, owner/group, ACLs,
extended attributes, timestamps, hard-link identity, arbitrary filesystem
metadata, or power-loss durability.  On POSIX a later proof may preserve the
selected target's ordinary `0o777` bits following RFC-0080; it must not turn
that into a false cross-platform metadata promise.  Windows ACL or equivalent
identity awaits an honest platform-specific proof.  Across platforms, HAC must
not deliberately broaden authority beyond ordinary host OS permissions.

### Privacy and composition boundary

Workspace root, requested relative paths, directory names, file contents, and
replacement contents are private local inputs.  This authority does not invoke
an inference runtime, construct a `ClusterRequest`, route, or introduce a
HAC-owned network request, client, transport, remote-filesystem protocol, or
remote filesystem orchestration.  It adds no request or prompt history, grant
persistence, content cache, or default path/content logging.  Host filesystem
I/O may use a networked backing mechanism explicitly exposed through the
trusted granted namespace; that is distinct from HAC gaining network authority
and privacy claims do not pretend all backing storage is physically local.  A
successful read necessarily discloses content to this authority's authorized
caller; what that caller later does is a separate authority and privacy
decision.  This RFC does not claim a future external harness cannot send
returned text elsewhere.

No implicit sensitivity policy exists.  HAC must not filter `.env`, `.git`,
credentials, dotfiles, filenames, extensions, ignore files, Git ignore rules,
or perceived secrets.  The trade-off is explicit: `read` grants the caller
readable regular UTF-8 files anywhere in the accepted namespace subject to the
operation rules.  The operator-selected workspace plus operation set is the
authority boundary; hidden heuristics would invent a second one.

## Relationship to accepted architecture

RFC-0066 cluster capabilities determine node eligibility.  `list`, `read`,
and `write` are permissions inside this one local authority, not new cluster
capabilities.  They affect no node eligibility, local/remote candidate
selection, static routing, fallback, runtime adapter selection, remote node
declaration, or cluster capability vocabulary.

RFC-0067's `code` remains bounded textual assistance without filesystem or tool
authority.  This workspace authority is not automatically attached to `code`.
RFC-0057 supplies useful regular-file, actual-byte-bound, strict-UTF-8,
reject-not-truncate, and truthful-race-limit precedents, but its ordinary-path
symlink-following behavior is deliberately not reused.

RFC-0080 and RFC-0081 remain caller-edge precedents.  This RFC introduces a
new reusable HAC-owned local authority beyond one exact operator-selected
`code-file` target; it does not supersede or silently migrate `code-file`.
RFC-0094 gains no retained root or grant.  RFC-0108 is precedent for keeping
process-local ownership facts distinct from caller-side routing permission:
this is another explicit local ownership seam, not a reason to broaden routing
capability semantics.

## Rationale

Ordinary host filesystem primitives are sufficient for this small authority;
HAC does not need an external filesystem service.  Keeping enforcement in HAC
prevents replaceable callers from reproducing security policy and avoids another
mandatory service in an ordinary installation.  The authority is useful before
creation exists: it can list an existing workspace, read existing source/text,
and replace existing files.

Namespace semantics truthfully describe what an operator grants despite hard
links and mounts.  Refusing sandbox claims keeps the design portable and
boring.  Explicit roots and operations are clearer than inferred
sensitive-file rules.  Separating the authority from cluster routing preserves
capability-centered routing instead of overloading it.

## Alternatives considered

### Keep all filesystem authority outside HAC

Rejected.  HAC would need to trust or duplicate policy in external tools, and
ordinary use would gain a dependency despite direct implementability.

### Make list/read/write cluster capabilities

Rejected.  RFC-0066 capabilities govern node eligibility and routing; these
local operations do not need those semantics.

### Separate filesystem service or MCP-style server

Rejected for the first version.  Installation, lifecycle, transport, and
security complexity are unnecessary.

### Follow redirects whose resolved target is below the root

Rejected.  It adds traversal and race complexity and makes the boundary harder
to explain consistently on Linux and Windows.

### Reject hard links or mounted/network-backed storage

Rejected.  Both require an untruthful or unnecessary physical-provenance and
locality policy.  The operator owns the granted host namespace; HAC adds no
remote filesystem protocol.

### Add creation, recursive list/search/glob, or patch/edit now

Deferred or rejected.  Existing-file replacement and one-level listing are
already useful and materially narrower; whole-file replacement has the simpler
proven publication model.

### Defend against malicious same-user namespace mutation

Rejected as a first-version guarantee.  It would push HAC toward a
platform-specific sandbox/security subsystem.

### Add implicit sensitive-file filters

Rejected.  Explicit workspace and operations are clearer than hidden heuristic
policy.

### Generic authority, plugin, filesystem-backend, or harness framework

Rejected.  The project has earned only this concrete authority, not an abstract
base class or general framework.

## Non-goals

This RFC does not choose or integrate Pi, OpenCode, Aider replacement, any
harness, generic agent architecture, generic plugin framework, generic
authority framework, filesystem backend abstraction, HAC-owned remote/distributed
filesystem access or protocol, synchronization, discovery, recursive repository work,
repository awareness, Git semantics, shell, process execution, `hac_exec`,
command allowlists, sandboxing, chroot, containers, Docker, Kubernetes, VMs,
seccomp, namespaces, database, daemon, watchers, background workers,
automatic inference, network authority, retained workspace configuration,
public HTTP filesystem endpoint, a new cluster capability, routing/fallback
changes, creation, directory creation, delete/rename/move, or patch/edit/search
APIs.

## Trade-offs

Some otherwise valid host paths are inaccessible because the logical grammar is
smaller than native path syntax.  Symlink/junction-heavy workspaces can be
inconvenient.  Directories over 1,024 entries fail rather than truncate; files
over 1 MiB and binary or non-UTF-8 files are unavailable.  There is no creation,
and same-user concurrent mutation is not isolated.

Mounts and hard links make workspace a namespace grant rather than physical
storage ownership.  Same-directory host replacement does not preserve all
metadata, and Windows and POSIX cannot honestly share every metadata or race guarantee.
These costs are acceptable for a first bounded authority: they keep the
authority understandable, explicit, model-free, and portable.

## Later implementation boundary and proof

After acceptance, one separate implementation PR may add only the smallest
concrete core/model-free proof: fixed existing root, explicit operation subset,
logical parsing, list/read/write, bounds, redirection rejection, fail-closed
behavior, and same-directory host existing-file replacement.  It must not add CLI
activation, HTTP API, retained configuration, Pi/OpenCode or plugin integration,
automatic model calls, routing behavior, or remote filesystem transport.

That PR must prove at least:

1. construction requires one explicit existing directory and a non-empty grant;
2. ungranted operations fail before filesystem action;
3. `.` lists the root; accepted relative names work; exactly 4,096 UTF-8
   logical-path bytes satisfy HAC's own bound subject to ordinary semantic and
   host validation, while 4,097 bytes fail before filesystem access; traversal
   and native, drive-relative, UNC, device, and ADS-like forms fail;
4. symlink traversal fails where supported, and junction/reparse traversal fails
   where practical; redirect entries may list but cannot be traversed;
5. lists are non-recursive, sorted, complete at 1,024 entries, and fail at
   1,025; unrepresentable names fail without alteration or omission;
6. existing regular UTF-8 reads, including empty files, succeed; invalid UTF-8,
   non-regular targets, and observed byte 1,048,577 fail without partial output;
   metadata length alone is not authoritative;
7. existing-file whole replacement, including empty and exactly 1,048,576-byte
   replacement, succeeds; oversized replacement, missing targets, and redirect
   targets fail without creation or mutation;
8. temporary/pre-publication failure retains prior content; success performs
   one same-directory host replacement/publication operation after complete
   pre-publication validation, with guarantees no stronger than that host
   primitive exposes;
9. no delete, rename, move, append, patch, mkdir, or new-file behavior exists;
10. hard-link behavior follows namespace rather than provenance semantics;
11. tests need no model, runtime, HAC-owned network activity, Ollama,
    llama-server, vLLM, Pi, OpenCode, Aider, Git, external filesystem service,
    root, or admin privileges; supported Linux and native Windows CI exercise
    the portable contract; and
12. tests make no claim to protect against arbitrary malicious same-user
    concurrent namespace mutation.  Mount semantics may be policy-tested
    without privileged mount fixtures.

## Open questions

No architectural question is blocking if this exact boundary is retained.
Implementation may choose internal names, helper decomposition, private
temporary-name generation, exception classes, result representation, and
platform primitives.  It must not reopen locality, retention, routing,
redirection traversal, creation, sandboxing, or Pi/OpenCode dependence.

## Accepted decision

This accepted RFC records one bounded HAC-owned local workspace authority with
the fixed root, explicit `list`/`read`/`write` grants, closed logical namespace,
non-traversal, bounded text, and existing-file host replacement semantics
specified above.  The RFC changes no behavior.  Implementation is permitted
only in a later separate PR and only within the later implementation boundary
recorded here.
