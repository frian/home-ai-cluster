# RFC-0137: Bounded Caller-Local JPEG Export

Status: Draft

Date: 2026-09-19

Author: frian

## Summary

Home AI Cluster should add one explicit caller-local JPEG export mode to the
existing one-shot Image Generation output-file edge:

    hac image-generation --output FILE --jpeg "<INSTRUCTION>"

The cluster operation itself remains unchanged.

Image Generation continues to produce exactly one fully validated normalized
HAC still-PNG result. Routing, remote transport, receiver execution, runtime
adapters, native HTTP success, browser presentation, retained configuration,
and `ImageGenerationResult` remain PNG-only.

Only after the caller has received one complete accepted normalized PNG may the
one-shot CLI optionally convert that result into one JPEG file.

JPEG export is deliberately not inferred from the output filename. Existing
behavior therefore remains unchanged:

    hac image-generation --output image.jpg "..."

still writes the exact PNG bytes accepted by RFC-0136.

JPEG requires the explicit `--jpeg` flag and requires `--output FILE`.

The first JPEG export supports only normalized 8-bit RGB source PNGs. It does
not define alpha compositing, 16-bit precision reduction, generic image
conversion, output-format negotiation, or a multi-format cluster result.

## Problem

RFC-0120 deliberately chose one closed still-PNG profile as HAC's normalized
Image Generation representation. PNG is an internal normalized representation,
not the capability name, but the first RFC explicitly rejected JPEG as that
normalized representation because doing so would require a lossy quality
policy.

RFC-0127, RFC-0129, RFC-0130, RFC-0131, and RFC-0135 subsequently project the
same normalized PNG through CLI, browser, exact-dimension, trusted-LAN, and
remote-routing boundaries without redefining the Image Generation result.

RFC-0136 then adds one bounded caller-local filesystem destination:

    hac image-generation --output FILE "<INSTRUCTION>"

That command still writes the exact normalized PNG bytes regardless of the
filename suffix.

The remaining narrow operator need is not:

> make the cluster's semantic result multi-format

but:

> let an operator explicitly export one already successful normalized image as
> a conventional JPEG file.

Those are different responsibilities.

Changing the normalized result to JPEG or adding an output-format request field
would reopen core validation, adapter normalization, native HTTP, receiver
protocol, remote transport, browser behavior, and result typing merely to
provide one local file-export convenience.

The smaller decision is to keep Image Generation PNG-normalized and make JPEG a
caller-local derivative.

## Goals

This RFC should:

- add one explicit `--jpeg` option to the existing one-shot
  `hac image-generation` command;
- require `--output FILE` whenever `--jpeg` is used;
- preserve the exact existing PNG behavior when `--jpeg` is absent;
- keep JPEG conversion entirely caller-local;
- perform conversion only after one complete successful normalized PNG has been
  received and validated;
- create the destination only after JPEG conversion has completed successfully;
- preserve the generated image's exact width and height;
- use one fixed high-quality JPEG encoding policy rather than exposing another
  control surface;
- reject normalized source layouts that would require a new alpha or precision
  policy;
- preserve RFC-0136 exclusive missing-leaf creation and no-rollback semantics;
- add no Image Generation protocol, routing, remote, runtime, browser, or
  retained-configuration change.

## Non-goals

This RFC does not add:

- JPEG as HAC's normalized Image Generation representation;
- JPEG to `ImageGenerationResult`;
- a media type or format field in normalized results;
- `output_format` in `ImageGenerationRequest`;
- HTTP content negotiation;
- JPEG responses from `POST /v1/image-generation`;
- JPEG responses from `POST /internal/cluster/request`;
- JPEG transport between HAC nodes;
- runtime-native JPEG passthrough;
- browser JPEG selection;
- browser download management;
- suffix-based output-format inference;
- automatic renaming;
- automatic extension changes;
- a generic `--format` option;
- WebP, AVIF, GIF, TIFF, or another format;
- a JPEG quality option;
- chroma-subsampling selection;
- progressive-JPEG selection;
- alpha compositing;
- background-color selection;
- 16-bit-to-8-bit precision conversion;
- generic image conversion;
- generic media/blob/asset abstractions;
- output overwrite;
- rollback deletion;
- temporary result files;
- result history or retained storage;
- model/runtime selection;
- OpenAI-compatible Image Generation.

## Proposal

### Caller surface

The existing one-shot command gains one boolean option:

    --jpeg

The accepted caller forms become conceptually:

    hac image-generation "<INSTRUCTION>"
    hac image-generation --output FILE "<INSTRUCTION>"
    hac image-generation --output FILE --jpeg "<INSTRUCTION>"

`--jpeg` without `--output FILE` is invalid caller input and must fail before
network activity.

No JPEG stdout mode is introduced.

Without `--output`, RFC-0127 remains unchanged: successful output is exact PNG
bytes on non-TTY stdout.

With `--output FILE` but without `--jpeg`, RFC-0136 remains unchanged:
successful output is the exact normalized PNG bytes written to the explicitly
selected file.

### No suffix inference

The output pathname has no format semantics.

In particular:

    --output picture.jpg

does not imply JPEG.

It remains an explicitly selected path receiving PNG bytes unless `--jpeg` is
also present.

Likewise, HAC does not require a `.jpg` or `.jpeg` suffix when `--jpeg` is
present.

This deliberately preserves RFC-0136 compatibility and avoids making filename
conventions an implicit control surface.

### Cluster representation remains PNG

The ordinary Image Generation request remains exactly the existing normalized
request.

The following remain unchanged:

- `ImageGenerationRequest`;
- `ImageGenerationResult`;
- the HAC still-PNG profile;
- core PNG validation;
- exact geometry validation;
- adapter execution contracts;
- stable-diffusion.cpp normalization;
- `POST /v1/image-generation`;
- `POST /internal/cluster/request`;
- remote transport;
- receiver behavior;
- local-first and ordered-remote routing;
- browser Image Generation;
- retained configuration.

The caller still requests and receives PNG from HAC.

The `--jpeg` flag must never appear in a native request, internal request,
routing constraint, remote declaration, adapter request, or runtime request.

The fact that one current runtime can natively encode JPEG does not change this
boundary. Runtime-native format features remain adapter-private unless a
separate architectural decision changes the normalized HAC result.

### Operation ordering

JPEG export follows this ordering:

    ordinary Image Generation execution
      -> complete successful normalized PNG
      -> complete caller-local JPEG conversion
      -> exclusive output-file creation
      -> JPEG byte write

The destination must not be created while:

- Image Generation is pending;
- the native response is incomplete;
- the PNG exceeds its accepted bound;
- PNG validation has not succeeded;
- requested dimensions have not been established;
- JPEG source-layout eligibility has not been established;
- or JPEG encoding is incomplete.

A request, routing, runtime, remote, response, validation, source-layout, decode,
or JPEG-encoding failure therefore leaves an absent destination absent.

Filesystem publication begins only after one complete JPEG byte sequence exists
at the caller.

### First accepted source layout

RFC-0120/RFC-0122 permit normalized PNGs whose IHDR layout is:

- 8-bit RGB;
- 8-bit RGBA;
- 16-bit RGB;
- or 16-bit RGBA.

The first JPEG export accepts only:

    bit depth = 8
    color type = RGB truecolor
    no alpha

An otherwise valid normalized PNG outside that subset causes JPEG export
failure after Image Generation has succeeded but before destination creation.

This is deliberate.

JPEG has no alpha channel, so accepting RGBA would require an explicit
compositing/background policy.

Accepting 16-bit source data would require an explicit precision-reduction
policy because ordinary JPEG export is 8-bit.

Neither policy is required for the first useful JPEG export.

HAC must not silently drop alpha, choose a background color, or silently reduce
16-bit samples merely because an image library can do so.

### JPEG encoding policy

JPEG export is intentionally lossy and uses one fixed first-version policy:

    quality = 95
    chroma subsampling = 4:4:4
    progressive = false

No caller option changes these values.

The fixed high-quality policy exists because JPEG necessarily requires a lossy
encoding choice. The project makes that choice explicitly rather than hiding a
library default or widening the command with quality controls before a need is
demonstrated.

The JPEG export preserves the normalized image's exact pixel dimensions.

The export does not copy prompt text, runtime metadata, model metadata, node
identity, EXIF, XMP, comments, or arbitrary source metadata into the JPEG.

Ordinary structural metadata emitted by the selected JPEG encoder is an
implementation detail.

RFC-0122's optional normalized PNG color signaling is not promoted into a new
JPEG color-management contract. JPEG export is a caller-requested lossy
derivative and does not claim a stronger calibrated-color guarantee than the
underlying semantic Image Generation capability.

### Encoder implementation

The project should use a mature maintained image codec library rather than
implement JPEG parsing or encoding itself.

A normal runtime dependency such as Pillow is an acceptable boring solution for
this bounded caller-local conversion and may be added by the implementation.

The codec dependency does not become part of HAC core Image Generation
semantics, adapter interfaces, routing, transport, or runtime selection.

The implementation should decode only the already completely validated,
bounded normalized PNG.

It should produce the complete JPEG in caller memory before filesystem
creation.

No temporary file or generic conversion service is required.

### Filesystem behavior

After JPEG bytes are fully established, RFC-0136 filesystem authority applies
unchanged.

The caller may exclusively create exactly the raw operator-supplied missing
leaf whose parent already exists.

It must not:

- create parents;
- infer another destination;
- normalize into a different semantic destination;
- overwrite an existing object;
- follow or replace an existing symlink;
- retry against another destination;
- or delete after successful creation.

The final JPEG write uses binary semantics on supported platforms.

If exclusive creation fails, the invocation fails without modifying the object
that occupies the path.

If writing or closing the newly created file fails, the invocation fails and
performs no rollback deletion. The selected file may remain present and contain
a JPEG prefix or otherwise incomplete JPEG data.

### Failure and retry boundary

JPEG conversion occurs after Image Generation has already produced one terminal
successful normalized result.

Therefore a JPEG conversion or filesystem failure must never cause:

- another Image Generation request;
- regeneration;
- another remote candidate;
- local fallback;
- runtime fallback;
- destination substitution;
- format fallback to PNG;
- or automatic retry.

A failed JPEG export is an export failure, not evidence that Image Generation
should run again.

This preserves RFC-0135 anti-double-execution semantics.

### Output streams

Successful JPEG file export is silent:

    stdout = empty
    stderr = empty

Human-readable failures remain on stderr.

No JPEG bytes are written to stdout.

No PNG fallback bytes are written to stdout when JPEG export fails.

## Relationship to accepted architecture

### RFC-0120 and RFC-0122

RFC-0120/RFC-0122 remain authoritative for the normalized Image Generation
result.

This RFC does not replace, widen, or weaken the closed HAC still-PNG profile.

It acts only after that semantic result exists.

RFC-0120 rejected JPEG as the normalized representation because normalization
would require a lossy quality policy. This RFC does not reverse that decision.
It instead makes one explicit caller-local lossy export policy while retaining
PNG as the single normalized representation.

### RFC-0127

RFC-0127 stdout remains exact PNG.

No JPEG stdout mode is introduced.

TTY behavior without `--output` remains unchanged.

### RFC-0131

Explicit dimensions remain an exact semantic requirement on the normalized PNG.

JPEG export preserves those established dimensions exactly and does not add
resizing.

### RFC-0135

Remote Image Generation continues to transport and independently validate only
the normalized PNG representation.

JPEG conversion happens only after the complete successful PNG has reached the
originating caller.

Conversion failure never re-enters routing.

### RFC-0136

RFC-0136 remains the filesystem authority owner.

Its default exact-PNG file behavior, raw path spelling, missing-leaf-only rule,
exclusive creation, binary writing, and no-rollback semantics remain
authoritative.

This RFC only adds an explicitly requested byte transformation before RFC-0136
publication.

## Rationale

Keeping JPEG at the caller edge preserves the distinction between:

    semantic cluster result
        and
    operator-selected presentation/export artifact

The capability remains engine-independent even though one current engine happens
to support JPEG itself.

Using runtime-native JPEG directly would make a caller presentation choice
cross adapter, result, routing, transport, receiver, and HTTP boundaries.

That would be substantially larger than the demonstrated need.

An explicit `--jpeg` flag is preferred over suffix inference because
RFC-0136 already established that the output filename is opaque. Changing
`--output picture.jpg` from PNG bytes to JPEG bytes would silently change
existing behavior.

The narrow 8-bit RGB input subset avoids two otherwise unavoidable policy
decisions:

- what background should replace alpha;
- how should 16-bit values be reduced to 8-bit.

Those can remain separate later decisions if real generated results require
them.

A fixed high-quality encoding policy avoids prematurely adding quality and
subsampling controls while making the lossy choice visible in architecture.

## Alternatives considered

### Make JPEG a normalized HAC result

Rejected.

It would widen `ImageGenerationResult`, core validation, adapters, HTTP
projection, remote transport, receiver protocol, and browser assumptions.

It would also reverse RFC-0120's intentionally single-representation result
without evidence that the cluster itself needs multiple formats.

### Ask stable-diffusion.cpp for JPEG

Rejected as the HAC boundary.

The current runtime supports JPEG, but runtime-specific output-format support is
not capability semantics.

Using it directly would either leak runtime control into the request or require
HAC to carry JPEG through its normalized result and transport contracts.

### Infer JPEG from `.jpg` or `.jpeg`

Rejected.

RFC-0136 already treats the output path as an opaque operator-selected
destination and writes PNG regardless of suffix.

Suffix inference would silently change existing behavior and make filename
spelling an implicit format control.

### Add generic `--format png|jpeg`

Rejected for the first slice.

Only one new derivative format is justified.

A generic format vocabulary would imply an extension point before a second
format has earned it.

### Add `--jpeg-quality`

Deferred.

JPEG needs a quality policy, but no demonstrated need requires another operator
control.

The first export uses one fixed high-quality policy.

### JPEG stdout

Deferred.

The current stdout contract is intentionally exact normalized PNG.

JPEG is being added because bounded filesystem output now exists; changing
stdout is unnecessary.

### Composite RGBA onto white or black

Rejected.

Either color would be a new arbitrary presentation policy.

The first version fails closed instead.

### Drop alpha without compositing

Rejected.

Transparent pixels retain RGB values that need not correspond to an intended
visible background. Silent alpha removal is not an honest export policy.

### Down-convert 16-bit normalized PNG

Deferred.

Precision reduction is irreversible and unnecessary for the first generated
images that use ordinary 8-bit RGB.

### Implement a JPEG encoder in HAC

Rejected.

A mature codec library is the boring solution. HAC should not own JPEG codec
implementation.

## Trade-offs

JPEG export adds one image-codec dependency to the ordinary package if the
implementation uses the intended mature-library approach.

That is additional package weight for users who do not use JPEG export.

The alternative would be a custom codec, engine-specific format leakage, or
optional-install complexity. For one bounded user-facing feature, one mature
ordinary dependency is the simpler operational model.

The first export may reject a future valid normalized RGBA or 16-bit result.

That is preferable to silently inventing alpha compositing or precision
reduction rules.

JPEG bytes are not deterministic across every codec/library/platform version,
and this RFC does not promise byte-for-byte reproducibility across
installations. The contract is the fixed encoding policy and preserved image
dimensions, not a stable file hash.

## Impact

A later implementation may add only the smallest caller-edge work necessary
for:

- parsing `--jpeg`;
- rejecting `--jpeg` without `--output` before network activity;
- retaining existing PNG behavior otherwise;
- establishing 8-bit RGB eligibility from the already validated PNG;
- decoding that bounded PNG caller-locally;
- encoding one complete JPEG in memory under the fixed policy;
- exclusively writing it through the RFC-0136 destination authority;
- one mature JPEG codec dependency;
- focused tests;
- and command documentation.

It must not modify:

- semantic Image Generation request/result models;
- the normalized still-PNG contract;
- native HTTP request or response shape;
- remote transport;
- receiver behavior;
- routing;
- execution permission;
- stable-diffusion.cpp request format;
- retained configuration;
- browser behavior;
- or OpenAI compatibility.

## Proof expectations

A later implementation should prove at least:

1. existing Image Generation without `--jpeg` remains unchanged;
2. existing `--output FILE` without `--jpeg` still writes exact PNG bytes
   regardless of filename suffix;
3. `--jpeg` without `--output` fails locally before any request;
4. JPEG export sends the same ordinary Image Generation request as PNG export
   and never sends `jpeg`, a format field, or the output path;
5. one complete accepted normalized PNG exists before JPEG conversion;
6. only 8-bit RGB normalized PNG is accepted by the first JPEG exporter;
7. RGBA and 16-bit normalized PNG cause export failure without destination
   creation;
8. JPEG encoding completes before exclusive destination creation;
9. successful JPEG export preserves exact width and height;
10. the result is one decodable single JPEG image encoded with quality 95,
    4:4:4 chroma subsampling, and non-progressive output;
11. prompt, runtime, node, model, EXIF, XMP, comment, and arbitrary source
    metadata are not copied into the JPEG;
12. successful stdout and stderr are empty;
13. existing destination, symlink, directory, parent, path-spelling, binary-mode,
    and creation-race guarantees from RFC-0136 remain intact;
14. conversion, exclusive-create, write, or close failure causes no second
    Image Generation request, fallback, regeneration, deletion, or PNG-format
    fallback;
15. no HTTP, routing, remote, receiver, adapter, configuration, browser, generic
    format, generic media, or JPEG-normalized-result behavior appears.

## Open questions

No broader Image Generation format architecture is required by this proposal.

Implementation may choose private helper boundaries and exact bounded error
strings.

A mature codec library such as Pillow is expected rather than custom JPEG code.

RGBA compositing, 16-bit precision reduction, JPEG quality controls, additional
export formats, JPEG stdout, and any future multi-format normalized result
remain separate decisions.

## Decision

Pending.
