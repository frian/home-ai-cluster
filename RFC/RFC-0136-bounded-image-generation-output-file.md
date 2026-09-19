# RFC-0136: Bounded Image Generation Output File

Status: Accepted

Date: 2026-09-19

Author: frian

## Summary

Home AI Cluster should add one optional caller-local output destination to the
existing one-shot Image Generation command:

    hac image-generation --output FILE "<INSTRUCTION>"

When `--output FILE` is supplied, the Image Generation client receives the
ordinary complete successful PNG response exactly as it does today, then creates
exactly the operator-supplied missing file and writes the PNG bytes to it.

The output path remains entirely caller-local.

It is not added to `ImageGenerationRequest`, the native HTTP request, cluster
routing, remote transport, receiver protocol, runtime adapters, retained
configuration, or normalized Image Generation results.

The first version deliberately supports only creation of a missing leaf whose
parent directory already exists. It does not overwrite an existing filesystem
object.

This RFC adds one bounded caller-edge filesystem authority. It does not add
storage management, automatic filenames, directories, generic binary
persistence, media abstractions, result history, or JPEG.

## Problem

RFC-0127 accepted the first one-shot Image Generation operator edge:

    hac image-generation "<INSTRUCTION>"

Successful non-TTY use writes the exact PNG response bytes to stdout.

RFC-0127 deliberately kept filesystem destination authority outside HAC. It
explicitly excluded output paths and rejected `--output PATH` because accepting
a path would require architectural decisions about destination authority,
overwrite behavior, path semantics, and symbolic links.

That boundary was appropriate for the first operator edge.

The remaining practical inconvenience is that saving an image requires shell
redirection or another downstream process:

    hac image-generation "..." > image.png

Home AI Cluster can provide the ordinary convenience:

    hac image-generation --output image.png "..."

without changing Image Generation semantics or turning HAC into a storage
system.

The architectural question is narrow:

> What exact filesystem authority does an explicitly supplied Image Generation
> output path grant to the caller edge?

## Goals

This RFC should:

- add one optional explicit `--output FILE` destination to the existing one-shot
  Image Generation command;
- keep the destination entirely caller-local;
- create exactly one explicitly named missing output file;
- require its parent directory to already exist;
- write only the complete successful PNG result;
- preserve the exact PNG bytes returned by the existing native operation;
- prevent models, runtimes, routing, remotes, and receivers from seeing or
  selecting the output path;
- fail rather than overwrite any existing filesystem object;
- preserve existing stdout behavior when `--output` is absent; and
- keep filesystem authority small enough to explain independently of any generic
  storage abstraction.

## Non-goals

This RFC does not add:

- JPEG or any other output format;
- an output-format option;
- overwrite or replacement of existing files;
- `--force`;
- automatic filenames;
- generated filenames;
- default output directories;
- directory creation;
- parent-directory creation;
- multiple output files;
- galleries;
- image history;
- retained output configuration;
- result storage;
- temporary result storage exposed to the user;
- generic Media, Blob, Asset, File, or Storage abstractions;
- filesystem APIs;
- RFC-0114 workspace authority;
- remote filesystem authority;
- output paths in native HTTP requests;
- output paths in internal cluster requests;
- output paths in remote transport;
- receiver-side persistence;
- runtime-side persistence;
- model-selected paths;
- model-visible paths;
- file discovery;
- path inference from the instruction;
- deletion, rename, move, append, or editing;
- persistence guarantees stronger than the ordinary host filesystem;
- or any change to Image Generation routing, fallback, execution permission, or
  anti-double-execution behavior.

JPEG remains a separate later architectural decision.

## Proposal

### Caller surface

The existing command gains one optional argument:

    hac image-generation [--output FILE] "<INSTRUCTION>"

The long root-command alias remains equivalent under the existing command
architecture.

When `--output` is absent, RFC-0127 behavior is unchanged.

The command therefore continues to require non-TTY stdout before network
activity when it will emit PNG bytes to stdout.

When `--output FILE` is present, stdout is not the Image Generation result sink
and the RFC-0127 stdout-TTY rejection does not apply.

A successful `--output` invocation writes no PNG bytes to stdout.

Ordinary bounded human-readable failures remain on stderr.

### Exact caller-local authority

`FILE` is supplied explicitly by the operator.

The caller edge may create exactly that one filesystem leaf.

It may not derive, infer, normalize into another semantic destination, or choose
a filename from:

- the Image Generation instruction;
- model output;
- routing metadata;
- node identity;
- timestamps;
- runtime information;
- image dimensions;
- or any other generated value.

The path is not part of Image Generation semantics.

It remains an operator-selected caller destination.

### Missing-leaf-only rule

The selected output path must not already exist.

Its parent must already exist and be a directory.

The caller does not create parent directories.

After non-mutating command and destination validation, the output file must be
created using exclusive non-overwriting semantics.

If any filesystem object appears at the selected path before exclusive creation
succeeds, the invocation fails.

The caller must never truncate, replace, follow, or overwrite that object.

This rule applies regardless of whether the existing object is:

- a regular file;
- a symbolic link;
- a directory;
- a device;
- or another filesystem object.

No `--force` or overwrite mode is introduced.

### Request and routing boundary

The output path never enters the HAC request architecture.

The native request remains the existing Image Generation request.

Conceptually:

    operator
      -> caller-local output choice
      -> ordinary POST /v1/image-generation
      -> ordinary Image Generation routing/execution
      -> complete successful PNG response
      -> caller-local file creation/write

The following remain unchanged and contain no output path:

- `ImageGenerationRequest`;
- `ImageGenerationResult`;
- `POST /v1/image-generation` request body;
- `RequestConstraints`;
- static routing;
- remote-node declarations;
- `RemoteTransportRequest`;
- `InternalClusterRequest`;
- `/internal/cluster/request`;
- receiver execution;
- runtime adapter requests;
- stable-diffusion.cpp integration.

A remote node may generate the PNG, but it never learns where the caller later
stores it.

The remote/result anti-double-execution boundary accepted by RFC-0135 is
unchanged.

Filesystem publication occurs only after Image Generation execution has already
produced one terminal successful result at the caller.

A local filesystem failure must never trigger regeneration, remote fallback,
another remote attempt, or another Image Generation request.

### Complete result before filesystem publication

The client must establish the complete successful bounded native PNG response
before creating the output file.

No output file is created while:

- Image Generation execution is still pending;
- the HTTP response is incomplete;
- the response status is unsuccessful;
- the response media type is unacceptable;
- the response exceeds its accepted bound;
- or the existing client response validation has not completed.

Only after the caller possesses one complete accepted successful PNG result may
it create the selected output leaf.

This preserves a simple authority ordering:

    generate successfully
      -> validate complete result
      -> create exact requested destination
      -> write exact result bytes

A failed Image Generation request therefore creates no output file.

### Exact byte preservation

The caller writes exactly the successful PNG response bytes to the selected
file.

It does not:

- decode and re-encode the image;
- alter PNG metadata;
- alter dimensions;
- append or prepend bytes;
- add a newline;
- convert formats;
- or otherwise transform the result.

The saved file is therefore the same byte sequence that RFC-0127 would emit to
non-TTY stdout.

### File write behavior

After exclusive creation succeeds, the caller writes the complete PNG bytes to
that file.

The RFC does not require a generic transactional-file abstraction.

The created file is a caller-owned result destination, not HAC-managed retained
storage.

If writing or closing the newly created file fails, the invocation fails.

After exclusive creation succeeds, the caller performs no rollback deletion.
The explicitly requested file may therefore remain present and incomplete after
a later write or close failure.

This is deliberate. Once the new leaf is visible in the host namespace, another
process may observe, move, replace, or otherwise race with that pathname. The
caller does not attempt to recover object identity, lock the namespace, or
delete by pathname after failure.

A post-creation filesystem failure is terminal. It must not cause retry,
regeneration, alternate routing, destination substitution, overwrite, or
deletion.

HAC claims no stronger host-filesystem transactional, concurrency, rollback, or
durability guarantee.

### Ordinary host permissions

Creation uses ordinary host filesystem permissions and process authority.

HAC does not bypass the operating system's access controls.

This RFC does not define a cross-platform mode, ACL, ownership,
extended-attribute, timestamp, or metadata-preservation contract because no
existing target is replaced.

The newly created file receives whatever ordinary creation semantics the
supported host platform and invoking process provide.

### Success behavior

On successful `--output FILE` completion:

- exactly one output file exists at the explicitly requested path;
- its content is exactly the successful PNG result;
- stdout contains no PNG result;
- stderr is silent;
- the command exits successfully.

The command does not print the path, routing information, attribution,
dimensions, or a success message merely because `--output` was used.

Existing architectural observation surfaces remain separate.

### Failure behavior

Before successful exclusive output-file creation, HAC creates no destination
object and modifies no existing destination object.

If the selected path was absent, failures before exclusive creation leave it
absent. If another filesystem object already occupies or concurrently wins the
selected path, the invocation fails and leaves that object unchanged.

This includes:

- invalid command shape;
- invalid destination parent;
- already-existing destination;
- unavailable HAC;
- timeout;
- no eligible Image Generation capability;
- execution refusal;
- runtime failure;
- remote failure;
- invalid native response;
- oversized response;
- or any other unsuccessful Image Generation outcome.

If exclusive creation succeeds but file writing or closing later fails, the
command exits non-zero and performs no rollback deletion. The explicitly
requested file may remain present and incomplete.

No failure after a completed Image Generation result may trigger:

- another Image Generation request;
- local regeneration;
- remote fallback;
- another remote candidate;
- or destination substitution.

Human-readable errors remain on stderr and must not be written into the output
file or stdout result stream.

## Relationship to existing architecture

### RFC-0127

This RFC narrowly extends RFC-0127's one-shot caller edge.

RFC-0127 correctly kept the first version at a byte-stream boundary and
explicitly left output persistence for a later decision.

This RFC supplies that later decision without changing the existing native Image
Generation operation.

When `--output` is absent, RFC-0127 remains unchanged.

### RFC-0135

RFC-0135 makes Image Generation distributable through existing static routing
while preserving strict terminal behavior after potentially executed remote
requests.

This RFC acts only after one successful ordinary native Image Generation
response has reached the caller.

A filesystem failure is therefore outside routing and execution.

It cannot cause fallback or regeneration.

### RFC-0080 and RFC-0081

RFC-0080 and RFC-0081 establish useful precedent that one explicitly
operator-selected path may authorize narrow caller-edge filesystem behavior
without granting filesystem authority to the model or HAC routing core.

This RFC uses the same architectural principle but does not reuse or generalize
their text-file replacement mechanism.

Image Generation needs no existing-target replacement, content envelope, UTF-8
semantics, or code-specific workflow.

The first Image Generation output authority is smaller:

> create one explicitly selected missing leaf and fill it with one already
> completed PNG result.

### RFC-0114

This RFC does not use or extend RFC-0114 workspace authority.

There is no workspace root, grant set, logical relative-path namespace,
list/read/write operation vocabulary, or reusable filesystem authority.

`--output FILE` is one direct caller-edge destination for one invocation.

## Rationale

An explicit output path is a useful operator convenience and no longer needs to
be simulated through shell redirection.

Keeping the path caller-local preserves the architecture already established by
Image Generation:

- requests describe generation;
- routing selects execution;
- runtimes produce images;
- remotes return normalized image results;
- the caller decides where its received result goes.

Requiring a missing target is deliberately conservative.

Supporting overwrite immediately would require additional decisions about:

- replacement behavior;
- symbolic links;
- target races;
- metadata preservation;
- atomic replacement;
- host-platform differences;
- and possible `--force` semantics.

None of those decisions is required to make `--output FILE` useful.

A missing-leaf-only first version therefore follows the project's small-step and
boring-solutions principles.

It also keeps this RFC about one thing:

> explicit persistence of one completed Image Generation result.

## Alternatives considered

### Keep shell redirection only

Rejected as the long-term operator experience.

RFC-0127's stdout boundary was the correct first proof, but an explicit
one-file output option is a small useful convenience that can now be defined
safely.

### Allow overwriting existing files

Deferred.

Overwrite introduces replacement, race, symbolic-link, metadata, and
host-filesystem semantics that are unnecessary for the first explicit output
destination.

A later RFC may add explicit overwrite behavior if demonstrated use justifies
it.

### Add `--force`

Rejected for this RFC.

There is no overwrite mode for `--force` to modify.

### Automatically generate filenames

Rejected.

The operator owns destination selection.

Filename generation would introduce policy, naming, collision, directory, and
retention questions unrelated to Image Generation execution.

### Save images server-side

Rejected.

The ordinary HAC process, selected node, receiver, and runtime do not need
output-destination authority.

Server-side storage would also make remote and local execution materially
different.

### Send the output path to a remote node

Rejected.

The path belongs to the caller's filesystem namespace and has no meaning or
authority on a remote execution node.

It would also incorrectly combine routing/execution with caller persistence.

### Reuse RFC-0114 workspace authority

Rejected.

One explicitly selected output file does not justify workspace roots, grants,
reusable file operations, or Code-oriented interaction machinery.

### Create a generic storage or media abstraction

Rejected.

The project currently needs exactly one PNG written to exactly one
operator-selected path.

No broader abstraction has been earned.

### Add JPEG at the same time

Rejected.

JPEG changes the Image Generation output-format contract and is an independent
architectural decision.

## Trade-offs

The primary limitation is that repeated generation to the same filename requires
the operator to remove or rename the previous file first.

That is intentional.

The benefit is a substantially smaller and safer first filesystem authority with
no replacement semantics.

A host write or close failure may leave an incomplete newly created file.

Avoiding that possibility portably would require stronger publication machinery,
object-identity tracking, or filesystem semantics than this small convenience
warrants. The caller deliberately performs no rollback deletion after creation.

The path remains subject to ordinary host operating-system behavior and
permissions.

These limitations are acceptable because the feature remains explicit, local,
bounded, and easily explained.

## Impact

After acceptance, one implementation PR may add only the smallest caller-edge
implementation necessary for:

- parsing `--output FILE`;
- destination validation;
- preserving RFC-0127 behavior when absent;
- complete native Image Generation response acquisition before file creation;
- exclusive creation of exactly one missing output leaf;
- exact PNG byte writing;
- terminal post-creation write/close failure without rollback deletion;
- appropriate CLI tests;
- and user-facing command documentation.

It must not change:

- Image Generation semantic request/result models;
- native server request shape;
- static capability semantics;
- routing;
- remote transport;
- receiver behavior;
- adapter behavior;
- retained configuration;
- browser behavior;
- Image Generation format;
- or JPEG support.

## Proof expectations

A later implementation should prove at least:

1. existing `hac image-generation "<INSTRUCTION>"` behavior is unchanged
   without `--output`;
2. successful `--output FILE` creates exactly the explicitly selected missing
   leaf;
3. its parent must already exist as a directory;
4. an existing destination of any kind fails without modification;
5. the destination path never appears in the native request, semantic request,
   routing, remote transport, receiver, or runtime adapter;
6. no output file is created before one complete successful acceptable PNG
   response exists;
7. native request, timeout, routing, execution, remote, MIME, response-bound, or
   response-validation failure leaves the destination absent;
8. the successful file bytes exactly equal the successful PNG response bytes;
9. successful `--output` writes no PNG bytes or success decoration to stdout
   and keeps stderr silent;
10. an output-file creation or write failure causes no retry, regeneration,
    alternate remote attempt, or fallback;
11. an exclusive-creation race never truncates or overwrites the object that won
    the path;
12. post-creation write or close failure performs no rollback deletion and may
    leave the explicitly created file present and incomplete;
13. no parent directory, sibling, automatic filename, retained state, generic
    filesystem API, workspace authority, storage abstraction, overwrite mode,
    or JPEG support appears.

## Open questions

No architectural question is blocking if this boundary is retained.

Implementation may choose internal command/helper names, error text, exit-code
reuse, and ordinary platform file-opening primitives. It must not add
post-creation rollback deletion.

Overwrite behavior, stronger publication guarantees, automatic naming, other
output formats, and JPEG remain later separate decisions.

## Decision

Accepted.

Home AI Cluster will add one optional caller-local `--output FILE` destination
to the existing one-shot Image Generation command. The path remains entirely
outside Image Generation semantics, routing, remote transport, receiver
execution, runtime adapters, normalized results, and retained configuration.

The first accepted authority is deliberately limited to exclusive creation of
one explicitly operator-selected missing leaf whose parent already exists,
after one complete successful acceptable PNG result has reached the caller. The
caller writes the exact PNG bytes, does not overwrite any existing filesystem
object, creates no parent directories, and performs no rollback deletion after
successful creation. A later write or close failure is terminal and may leave
the newly created file present and incomplete.

Filesystem failure never authorizes regeneration, retry, alternate remote
execution, local fallback, destination substitution, overwrite, or deletion.
Existing RFC-0127 stdout behavior remains unchanged when `--output` is absent,
and RFC-0135 anti-double-execution semantics remain authoritative.

This decision adds no overwrite mode, `--force`, automatic naming, retained
storage, workspace authority, generic filesystem/media/storage abstraction, or
JPEG support.
