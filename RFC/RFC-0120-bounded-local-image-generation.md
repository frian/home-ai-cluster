# RFC-0120: Bounded Local Image Generation

Status: Draft

Date: 2026-09-12

Author: frian

## Summary

Home AI Cluster accepts one new closed semantic capability:

```text
image-generation
```

The capability means exactly:

```text
one bounded caller-supplied textual instruction
    ->
exactly one bounded still image
```

The capability semantics are distribution-independent.

RFC-0120 authorizes `image-generation` only inside local request-executable compositions. It does not authorize any path that transports or executes an Image Generation request remotely.

The normalized request contains one non-blank textual instruction bounded to 65,536 UTF-8 bytes. It contains no conversation history, generation controls, model/runtime selection, output-format choice, or filesystem destination.

Ordinary capability routing selects an eligible local adapter. Under RFC-0119, positive `image-generation` support requires one new explicit Image Generation execution shape. The adapter owns runtime-specific generation and normalization. HAC core independently validates the candidate image before constructing the successful result.

The normalized representation is one restricted still-PNG profile:

```text
PNG signature
IHDR
sRGB
IDAT...
IEND
end of input
```

The accepted pixel layouts are:

```text
RGB8
RGBA8
RGB16
RGBA16
```

The representation is non-interlaced, non-animated, metadata-closed, completely decodable, and bounded to:

```text
complete encoded PNG <= 41,943,040 bytes
                     <= 40 MiB

width  <= 2,048 pixels
height <= 2,048 pixels
```

The successful result contains the actual validated PNG bytes plus ordinary HAC `node_id` attribution outside those bytes.

Existing internal request/result envelopes, `RemoteTransport`, static remote capability declarations, receiver behavior, operator configuration, CLI, Web UI, and filesystem authority remain unchanged.

The first implementation may prove the architecture through direct local composition and focused in-process test adapters. It does not require a production image runtime.

## Context

RFC-0066 defines the admission rule for new semantic capabilities.

A capability must describe an explicit project-owned requirement that can affect hard eligibility without becoming a model, runtime, hardware, quality, ranking, or preference label.

Image generation meets that boundary because:

```text
text-only execution
    cannot satisfy
a request whose required result is an image
```

The distinction is semantic rather than qualitative.

RFC-0119 subsequently established the adapter architecture required for heterogeneous execution forms:

* one common adapter surface;
* explicit operation-shaped execution contracts;
* positive adapter capability claims that must have their required execution contracts before request-executable use;
* capability semantics distinct from execution mechanics;
* unchanged RFC-0108 local binding ownership;
* operation-blind routing.

RFC-0120 now defines the smallest bounded Image Generation vertical that can use that architecture.

## Problem

HAC currently has no normalized operation whose successful result is an image.

Existing result contracts are textual or small structured values. Reusing them would require one of several architectural distortions:

```text
image bytes encoded as text
a filesystem path treated as the result
a URL treated as the result
a generic binary/media abstraction introduced without evidence
```

The normalized result also needs stronger guarantees than arbitrary bytes plus a claimed media type.

For one successful Image Generation result, HAC must be able to establish that the output is:

* exactly one still image;
* finite;
* valid and completely decodable;
* bounded in encoded and decoded scale;
* represented with explicit color semantics;
* free of arbitrary runtime-private metadata;
* independent of the runtime that produced it.

The first vertical should provide those guarantees without becoming generic media architecture.

## Goals

This RFC aims to:

* accept the semantic capability `image-generation`;
* define one bounded textual request;
* define exactly one successful still-image result;
* keep the capability engine- and distribution-independent;
* authorize only local request-executable use in this RFC;
* add one RFC-0119 Image Generation execution shape;
* preserve ordinary capability routing and RFC-0108 binding semantics;
* keep runtime-specific generation and conversion behind adapters;
* define one closed normalized still-image representation;
* make HAC core independently validate that representation;
* preserve 8-bit and 16-bit RGB/RGBA fidelity;
* establish finite encoded and decoded resource bounds;
* keep arbitrary runtime metadata out of normalized results;
* preserve ordinary HAC node attribution outside image bytes;
* leave production runtime, operator surface, and remote transport for later decisions.

## Non-goals

This RFC does not add or define:

* image understanding;
* vision;
* OCR;
* image editing;
* image-to-image transformation;
* multimodal Chat;
* batch generation;
* galleries or alternate candidates;
* animation;
* video or audio;
* generic media processing;
* generic `Media`, `Asset`, `Blob`, `Attachment`, or `BinaryResult` abstractions;
* a production image runtime;
* model or runtime selection;
* runtime or model discovery;
* plugin selection;
* CLI or Web UI;
* browser/public API;
* retained image configuration;
* runtime-config image syntax;
* changes to current production runtime defaults;
* static remote `image-generation` declarations;
* receiver Image Generation execution;
* remote image transport;
* base64, multipart, raw-image HTTP bodies, result URLs, or object storage;
* filesystem paths or automatic saving;
* caller-selected dimensions or aspect ratio;
* negative prompts, seed, sampler, steps, CFG, style, or quality controls;
* generic `execute()`;
* ranking, scoring, scheduling, or model preference.

## Capability semantics

HAC accepts:

```text
image-generation
```

with this complete semantic meaning:

> Produce exactly one bounded still image from one explicit bounded caller-supplied textual instruction.

The capability does not mean:

```text
understand an image
describe an image
edit an image
transform one image into another
generate several images
generate animation
handle arbitrary media
```

The name deliberately uses `image-generation` rather than `image` so generation remains distinct from possible future image-input semantics.

The semantic capability is not local-only. A future transport RFC may carry the same semantic request and result without redefining `image-generation`.

RFC-0120 extends only the local request-executable domain.

## Relationship to RFC-0066

`image-generation` satisfies RFC-0066.

### Explicit semantic meaning

It can be stated without runtime or model identity:

```text
textual instruction
    ->
one still image
```

### Explicit requirement

The caller explicitly constructs an Image Generation request. HAC does not infer image-generation intent from ordinary Chat text.

### Hard Boolean eligibility

A text-only adapter cannot satisfy the request by returning a textual image description.

### Engine independence

The capability does not name a model, runtime, GPU, provider, or engine-specific control.

### No preference semantics

The capability does not mean:

```text
best image model
preferred image model
high-quality model
creative model
```

It supplies hard semantic eligibility only.

## Request contract

The normalized request contains exactly one caller-supplied textual instruction.

Conceptually:

```text
instruction:
    non-blank UTF-8 text
    maximum 65,536 UTF-8 bytes

capability:
    fixed image-generation semantics
```

The 65,536-byte bound reuses HAC's existing bounded semantic-text scale where no image-specific reason requires another value.

The request does not contain:

```text
message history
system message
assistant history
negative prompt
seed
width
height
aspect ratio
sampler
steps
guidance / CFG
quality
style
model
runtime
batch count
output format
file path
```

No caller-controlled capability field is needed because the request's capability is fixed.

If implementation compatibility with shared routing machinery requires ordinary `RequestConstraints`, those constraints do not redefine Image Generation semantics or authorize remote execution.

RFC-0120 itself authorizes no remote Image Generation path.

## No caller-selected dimensions

The accepted result envelope permits:

```text
width  <= 2,048
height <= 2,048
```

Those are result bounds, not request controls.

A runtime may use its own configured or native generation defaults behind the adapter, provided the normalized result satisfies the HAC contract.

Explicit generation controls require a later RFC.

## Exactly one successful image

One successful request produces exactly one image.

The core does not model:

```text
zero-or-more images
candidate arrays
batches
galleries
alternate variants
best-of-N selection
```

If a runtime produces several candidates, its adapter must reduce that runtime behavior to the one-image HAC contract or fail.

Candidate selection does not become core semantics.

## Local request-executable boundary

RFC-0120 authorizes this vertical only inside local request-executable composition:

```text
normalized Image Generation request
    ->
ordinary local capability routing
    ->
eligible local adapter
    ->
RFC-0119 Image Generation execution contract
    ->
runtime-specific generation
    ->
adapter normalization
    ->
candidate HAC still-PNG bytes
    ->
cluster-owned validation
    ->
normalized Image Generation result
```

The semantic request and result are not defined as local-only objects.

The restriction is architectural scope:

> RFC-0120 authorizes no path that transports or executes this request remotely.

## Local execution and remote transport remain distinct

The current implementation shares some request/result typing across local orchestration and remote transport.

RFC-0120 must not turn that implementation coincidence into architecture.

The Image Generation request and result join the local request-executable domain.

The existing remotely transportable request set remains unchanged:

```text
Chat / Code ordered-message execution
Summarize
Classify
Source-grounded Chat
```

The existing remotely transportable result domain likewise remains unchanged.

If implementation typing currently assumes that all locally executable requests are remotely transportable, implementation may make the smallest distinction necessary to preserve:

```text
locally request-executable
    does not imply
remotely transportable
```

This does not authorize a generic local/remote request framework.

## Existing internal transport remains closed

RFC-0120 does not add Image Generation to:

```text
InternalClusterRequest
/internal/cluster/request
RemoteTransport
HttpRemoteTransport
receiver response unions
```

No Image Generation request or result is serialized by the existing internal protocol.

A request path requiring remote transport therefore continues to accept only the already authorized remotely transportable domain.

## Image Generation execution shape

RFC-0119's HAC-owned capability-to-execution-shape relationship gains exactly one mapping:

```text
image-generation
    -> Image Generation execution shape
```

The execution contract conceptually accepts the normalized Image Generation request and returns one candidate encoded image representation for HAC validation.

Exact Python names remain implementation choices.

This RFC adds no generic media operation and no generic `execute()`.

An image-only adapter may therefore have:

```text
common adapter surface
+
Image Generation execution contract
```

without fake Chat, Summarize, or Classify methods.

Under RFC-0119, an adapter that positively claims `image-generation` must have this execution contract before request-executable admission.

## Adapter normalization ownership

The adapter owns runtime-specific behavior.

The core must not need to understand whether a runtime originally produced:

```text
PNG
JPEG
WebP
raw pixels
a runtime-specific image object
another runtime-private representation
```

The boundary is:

```text
runtime-native result
    ->
adapter-owned runtime-specific normalization
    ->
candidate HAC still-PNG bytes
    ->
cluster-owned validation
```

An adapter may therefore need to perform runtime-specific work such as:

* decoding another image representation;
* expanding palette or grayscale data;
* preserving or normalizing transparency;
* producing non-interlaced output;
* truthfully converting color into the required sRGB interpretation;
* removing forbidden metadata by producing a conforming normalized representation.

The core understands only the final HAC representation.

## Core validation ownership

HAC core owns the normalized result contract.

Adapter-only validation is insufficient.

Core must independently establish:

```text
fixed representation
encoded bound
geometry bounds
permitted pixel layout
color interpretation
closed chunk vocabulary
chunk integrity
exact compressed-stream completion
exact decoded scanline extent
complete decodability
absence of trailing data
```

The core does not repair arbitrary runtime output.

Nonconforming candidate output fails normalization.

## Normalized result representation

The normalized semantic image content is the actual encoded image bytes.

It is not:

```text
a path
a URL
a data URL
a base64 string
an attachment
a generic blob
```

The semantic capability remains:

```text
instruction -> image
```

The normalized HAC representation of that image is one closed still-PNG profile.

PNG is an internal normalized representation choice, not the capability name or semantic operation.

## HAC still-PNG profile

One successful normalized image consists exactly of:

```text
PNG signature

IHDR

sRGB

one or more consecutive IDAT chunks

IEND

end of input
```

No other chunks are permitted.

No bytes may follow `IEND`.

## IHDR contract

`IHDR` must:

* be the standard PNG `IHDR` chunk;
* occur exactly once and first;
* have payload length exactly 13 bytes;
* have a valid CRC;
* describe an accepted geometry and pixel layout.

Its values must satisfy:

```text
width:
    1..2048

height:
    1..2048

bit depth:
    8 or 16

color type:
    RGB truecolor
    or RGBA truecolor-with-alpha

compression method:
    0

filter method:
    0

interlace:
    0 / none
```

The normalized pixel-layout vocabulary is exactly:

```text
RGB8
RGBA8
RGB16
RGBA16
```

Palette and grayscale are not normalized layouts.

## sRGB contract

The normalized representation must contain exactly one standard PNG `sRGB` chunk.

The `sRGB` chunk must:

* occur after `IHDR` and before the first `IDAT`;
* have payload length exactly 1 byte;
* have a valid CRC;
* contain a rendering-intent value exactly in the standard range `0..3`.

No other color-identification chunks are permitted.

In particular, the profile excludes:

```text
iCCP
gAMA
cHRM
```

and untagged RGB/RGBA.

The purpose of the sole `sRGB` chunk is stable normalized color interpretation, not generic color-management support.

## IEND contract

The normalized representation must contain exactly one standard PNG `IEND` chunk.

`IEND` must:

* occur after all `IDAT` chunks;
* have the standard empty payload;
* have a valid CRC;
* be the final PNG chunk.

No bytes may follow it.

## Alpha

RGBA is accepted directly.

HAC does not force adapters to discard transparency or composite against an arbitrary background.

`tRNS` is forbidden.

Runtime-native transparency may be normalized to RGBA by the adapter.

## 16-bit samples

Both 8-bit and 16-bit normalized samples are accepted.

Restricting normalization to 8-bit would require irreversible precision reduction when a runtime legitimately produces 16-bit data.

RFC-0120 deliberately avoids making normalization an implicit precision-loss policy.

The accepted geometry keeps that representation finite.

## Grayscale and palette runtime outputs

Grayscale and indexed/palette PNG are not accepted normalized layouts.

When truthful for the source representation, an adapter may expand:

```text
grayscale -> RGB
grayscale + alpha -> RGBA
palette -> RGB/RGBA
```

before producing candidate HAC bytes.

## Color-conversion honesty

If runtime-native image data uses a non-sRGB color interpretation, the adapter must either:

1. truthfully convert it into the accepted sRGB representation; or
2. fail normalization.

An adapter must not strip a non-sRGB profile and relabel unchanged pixel values as sRGB.

Core does not become a generic color-management engine.

## Metadata and privacy policy

The profile is fail-closed.

The only permitted ancillary chunk is the required `sRGB` chunk.

The normalized image must not contain:

* textual metadata;
* EXIF;
* ICC profiles;
* comments;
* timestamps;
* generation parameters;
* software identifiers;
* runtime identifiers;
* model identifiers;
* local paths;
* private chunks;
* unknown ancillary chunks;
* arbitrary application data.

All other critical or ancillary chunk types are forbidden.

Runtime-private information must not cross the adapter boundary merely because a runtime embeds it in an image container.

## Animation

Animation is not accepted.

APNG-specific chunks, including animation-control and frame-control/data chunks, are forbidden.

The result is one still image.

The core does not select a frame from animated output.

## IDAT contract

The profile permits one or more ordinary `IDAT` chunks.

Requirements:

* at least one `IDAT` chunk exists;
* all `IDAT` chunks are consecutive;
* no non-`IDAT` chunk interrupts the IDAT sequence;
* every `IDAT` chunk has a valid CRC.

The ordered concatenation of all `IDAT` payload bytes represents exactly **one complete PNG zlib datastream**.

Validation must reject:

* truncated zlib data;
* corrupt zlib data;
* a datastream that never reaches its normal end;
* compressed bytes remaining after the end of the one accepted zlib stream.

A permissive decoding library silently ignoring unused compressed input does not satisfy this contract.

This compressed-stream completion rule is distinct from the separate requirement that no PNG bytes follow `IEND`.

## PNG filtering

PNG filter method 0 is required.

The ordinary PNG scanline filter types defined under method 0 remain valid.

No canonical filter selection is required.

Each inflated scanline must begin with one valid filter byte.

## Numerical bounds

RFC-0120 accepts exactly these independent image-result bounds:

```text
complete encoded PNG:
    <= 41,943,040 bytes
    <= 40 MiB

width:
    <= 2,048 pixels

height:
    <= 2,048 pixels
```

The encoded bound applies to the complete normalized PNG, including signature and chunk structure.

Width and height are established from validated `IHDR` data before work proportional to unbounded geometry or decompressed output is permitted.

## Derived pixel and raster facts

No independent total-pixel limit is introduced.

The accepted geometry implies:

```text
2048 * 2048
=
4,194,304 maximum pixels
```

For the largest accepted pixel layout:

```text
RGBA16 raw pixel raster:

2048 * 2048 * 4 channels * 2 bytes
=
33,554,432 bytes
=
32 MiB
```

This 32 MiB figure is the raw pixel raster only.

It is **not** the complete inflated PNG scanline stream.

## Derived inflated scanline extent

For non-interlaced PNG filter method 0, every decoded scanline contains one leading filter byte before its row data.

For the maximum accepted `RGBA16` layout:

```text
RGBA16 row bytes:

2048 * 4 channels * 2 bytes
=
16,384 bytes
```

Therefore the maximum expected inflated scanline stream is:

```text
2048 * (1 filter byte + 16,384 row bytes)
=
33,556,480 bytes
=
32 MiB + 2 KiB
```

This is a derived validation fact, not another configurable limit.

For every accepted image, the validator derives the exact row byte count from:

```text
width
channels
bytes per sample
```

and the exact required inflated byte count as:

```text
height * (1 filter byte + exact row byte count)
```

No independent decoded-byte policy knob is introduced.

## Arbitrary aspect ratio within the bounds

RFC-0120 does not introduce square-image semantics.

Any positive dimensions are valid when both axes remain within the accepted maximum.

Examples include:

```text
2048 x 512
512 x 2048
1536 x 1024
1024 x 1536
```

A dimension above 2,048 is outside the contract even when total pixel count is small.

No separate aspect-ratio or total-pixel policy is added.

## Complete bounded decode validation

Header and chunk recognition alone are insufficient.

The core must validate the one complete zlib/scanline stream represented by the concatenated IDAT payloads.

The validator must establish:

* the zlib datastream reaches its normal end;
* no compressed bytes remain after that stream end;
* inflated output contains exactly the derived number of scanline bytes;
* every row is complete;
* every scanline starts with an allowed filter byte;
* no inflated bytes are missing;
* no excess inflated bytes exist.

It must therefore reject:

```text
truncated compressed data
corrupt compressed data
incomplete zlib termination
unused compressed data after zlib end
insufficient inflated data
excess inflated data
incomplete scanlines
invalid filter bytes
```

Core need not retain the fully decoded raster after validation.

It also need not reconstruct final unfiltered pixels merely to preserve them as a separate normalized object; the accepted semantic image remains the validated PNG bytes.

## Bounded validation order

The high-level validation order is:

```text
1. require complete encoded representation <= 40 MiB

2. validate PNG signature and IHDR enough to establish:
       accepted layout
       width
       height

3. enforce:
       width <= 2048
       height <= 2048
       derived exact row size
       derived exact inflated scanline size

4. validate:
       closed chunk vocabulary
       exact chunk ordering/cardinality
       required chunk lengths
       CRCs

5. validate completely:
       the single concatenated IDAT zlib datastream
       exact scanline extent
       filter bytes
       normal stream completion
       no unused compressed data

6. only then construct the successful
   normalized Image Generation result
```

An implementation may safely combine or stream these checks.

The RFC does not require multiple full buffers or choose a parsing library.

The architectural requirement is:

> No work proportional to untrusted, unbounded geometry or decompressed output may occur before the finite bounds governing that work have been established.

## No canonical re-encoding in core

Core validates the candidate representation.

It does not re-encode every accepted image into one byte-identical form.

Two valid normalized PNG byte sequences may differ in:

* DEFLATE representation;
* compression level;
* permitted filter choices;
* IDAT boundaries.

RFC-0120 therefore does not define:

* byte identity;
* hashing identity;
* deduplication;
* cache identity;
* canonical compression;
* canonical filtering.

## Result contract

One successful Image Generation result contains conceptually:

```text
validated HAC still-PNG bytes

node_id
```

The PNG bytes are the semantic image result.

`node_id` remains ordinary HAC execution attribution outside those bytes.

The result does not duplicate information derivable from the validated representation.

It therefore does not require fields for:

```text
media type
format name
width
height
bit depth
alpha presence
color type
```

There is only one accepted representation.

## Adapter and model attribution

RFC-0120 does not require adapter or model identity in the normalized result.

Existing HAC result contracts already differ where their semantics require different attribution. `ClassifyResult`, for example, requires `node_id` without adapter/model fields.

The minimum required Image Generation attribution is therefore:

```text
node_id
```

Runtime and model identity remain behind the adapter boundary unless separately justified later.

## Routing

Image Generation uses ordinary capability-based local routing.

Eligibility depends on:

```text
image-generation
```

not:

* model name;
* runtime name;
* adapter class;
* PNG implementation;
* prompt contents;
* style;
* quality;
* dimensions.

No ranking or preference is added.

The router remains operation-blind under RFC-0119.

## Adapter support and local binding ownership

These remain distinct:

```text
adapter execution support:
    adapter positively supports image-generation

local binding ownership:
    this process assigns image-generation
    to this concrete adapter instance

caller/static routing permission:
    separately accepted routing declaration/permission
```

Under RFC-0119, positive support requires the Image Generation execution contract.

Under RFC-0108, a binding may assign `image-generation` only when the adapter positively supports it.

RFC-0108 remains:

```text
binding.capabilities
    subset-of
adapter.capabilities()
```

with pairwise non-overlap.

A capable adapter may remain unbound.

Omission from a binding or routing declaration does not imply physical inability.

## First local composition proof

RFC-0120 does not create operator-facing image runtime configuration.

Its first implementation may prove the vertical with a focused in-process composition that:

1. provides the RFC-0119 common adapter surface;
2. positively supports `image-generation`;
3. satisfies the Image Generation execution contract;
4. passes RFC-0119 executable admission;
5. is explicitly bound locally to `image-generation`;
6. exposes that binding through the local node's executable capability set;
7. receives a normalized Image Generation request through ordinary local routing;
8. returns candidate image bytes;
9. succeeds only after cluster-owned validation.

This is real architecture without pretending that a production image engine or operator surface already exists.

## Static and retained capability surfaces remain unchanged

HAC accepts the semantic capability:

```text
image-generation
```

RFC-0120 does **not** automatically extend every existing surface that carries capability names.

The following remain closed to their previously accepted vocabularies:

* static remote node declarations;
* caller-local static capability configuration;
* retained remote topology;
* ordinary production runtime capability defaults;
* existing `--capabilities` surfaces;
* RFC-0110 runtime-config syntax;
* receiver transport vocabulary.

This distinction is intentional.

Semantic capability admission does not automatically authorize a configuration, binding, or transport surface to expose that capability.

A later RFC may extend one or more of those surfaces if justified.

## Existing production adapters remain unchanged

Current Ollama, llama-server, and vLLM adapters do not gain `image-generation` because the semantic capability is now accepted.

Their existing support sets remain unchanged.

They need no Image Generation execution contract unless a later decision explicitly makes a concrete adapter support the capability.

## No concrete runtime

RFC-0120 does not select or privilege any image engine.

It does not accept or prescribe:

```text
Stable Diffusion
SDXL
FLUX
ComfyUI
Automatic1111
InvokeAI
Diffusers
Ollama
hosted image services
```

No runtime endpoint convention, model identifier, or engine-specific control enters the core contract.

## No filesystem authority

A successful result exists entirely as normalized image bytes.

It contains no:

```text
filename
path
temporary path
workspace root
download directory
```

RFC-0120 grants no filesystem authority.

Saving a generated image is a separate authority-bearing action and requires a later composition with explicit caller-local write/create authority.

## No implicit network authority

The normalized operation does not:

* fetch image inputs;
* upload results;
* host results;
* return hosted URLs.

RFC-0120 grants no new arbitrary network authority.

## No operator UI or API

RFC-0120 does not define:

* image preview;
* browser rendering;
* download behavior;
* CLI binary output;
* terminal image display;
* REST media responses;
* output files.

The core request/result contract exists independently of eventual presentation.

## Failure semantics

RFC-0120 preserves distinct failure layers.

### Invalid request

Examples:

```text
blank instruction
instruction > 65,536 UTF-8 bytes
```

Failure occurs before routing.

### No eligible local adapter

No locally request-executable adapter/binding supplies `image-generation`.

This is ordinary routing failure.

### Pre-execution refusal

An otherwise valid selected local candidate cannot begin work under existing execution-permission rules.

Existing execution-availability semantics remain authoritative.

### Runtime execution failure

The adapter starts generation but the runtime cannot complete it.

### Adapter normalization failure

The runtime produces output that the adapter cannot truthfully normalize into the accepted HAC still-PNG representation.

### Cluster image-result validation failure

The adapter produces candidate bytes, but HAC rejects them.

Examples include:

* encoded representation above 40 MiB;
* width or height above 2,048;
* invalid pixel layout;
* malformed `IHDR`;
* missing, duplicated, malformed, or invalid `sRGB`;
* forbidden chunks or metadata;
* malformed `IEND`;
* invalid CRC;
* invalid IDAT ordering;
* truncated or corrupt zlib data;
* incomplete zlib termination;
* compressed bytes after the one accepted zlib stream ends;
* insufficient or excess inflated scanline data;
* incomplete scanlines;
* invalid filter bytes;
* trailing bytes after `IEND`.

Only a fully validated candidate becomes a successful normalized result.

## No new post-start fallback

RFC-0120 does not introduce another-adapter retry after Image Generation execution begins.

Runtime, normalization, or result-validation failure after start remains visible.

Those failures do not become candidate ineligibility.

Existing pre-execution refusal and continuation semantics remain unchanged.

## Privacy boundary

The request and result remain private cluster data under existing HAC privacy principles.

The normalized PNG must not silently disclose runtime-private information such as:

```text
local filesystem paths
hostnames
runtime configuration
model paths
model identifiers
generation graphs
software comments
arbitrary generation parameters
private application data
```

The fail-closed chunk vocabulary enforces this boundary without requiring HAC to interpret arbitrary metadata.

Ordinary `node_id` attribution remains outside the PNG.

## Relationship to RFC-0119

RFC-0119 is the direct prerequisite for RFC-0120.

RFC-0120 adds exactly one HAC-owned relationship:

```text
image-generation
    -> Image Generation execution shape
```

It does not reopen RFC-0119's common adapter surface, executable-admission lifecycle, or operation-blind routing.

An image-only adapter may satisfy:

```text
common adapter surface
+
Image Generation execution contract
```

without unrelated textual operations.

Capability support remains explicit and is never inferred from implementation mechanics.

## Relationship to RFC-0058 and RFC-0059

RFC-0058 and RFC-0059 continue to define routing permission rather than adapter execution support.

RFC-0120 does not add `image-generation` to those existing operator-facing static declaration surfaces.

If a future RFC extends such a surface, omission must retain its accepted meaning:

> the caller has not admitted that candidate into this routing domain.

It must not mean that the runtime is physically incapable of Image Generation.

## Relationship to RFC-0108

RFC-0108 remains authoritative for local capability ownership.

An in-process RFC-0120 proof may bind:

```text
image-generation
    ->
one concrete image-capable adapter
```

provided that adapter positively supports the capability and has passed RFC-0119 executable admission.

No overlapping local owner, ranking, or selection preference is introduced.

## Relationship to remote transport

The semantic capability, normalized request, and normalized result are intentionally distribution-independent.

RFC-0120 authorizes them only for local request-executable use.

The existing remotely transportable domain remains unchanged.

A future remote-transport RFC may define how the same semantic request and result cross a process boundary. That decision must not redefine `image-generation` or replace the normalized result merely for HTTP convenience.

RFC-0120 therefore accepts no:

```text
base64 wire encoding
multipart
raw-image HTTP body
result URL
remote endpoint
receiver Image Generation execution
```

## Compatibility

Existing behavior remains unchanged:

* Chat is unchanged;
* Summarize is unchanged;
* Classify is unchanged;
* Code is unchanged;
* current text adapters gain no Image Generation support;
* current production runtime defaults remain unchanged;
* static capability validation surfaces remain unchanged;
* static remote declarations remain unchanged;
* retained configuration remains unchanged;
* internal request/result envelopes remain unchanged;
* receiver behavior remains unchanged;
* remote transport remains unchanged;
* no public API route is added;
* no CLI command is added;
* no browser UI changes;
* no filesystem or network authority is granted.

RFC-0120 adds the semantic capability and local request-executable vertical without making it remotely transportable or operator-configurable.

## Alternatives considered

### Reuse Chat request/history

Rejected.

Image Generation has one textual instruction and one image result. Conversation roles and history are not part of the first semantic contract.

### Put base64 image data in `ClusterResult.content`

Rejected.

That would make a serialization encoding masquerade as textual semantic output.

### Return a filesystem path

Rejected.

A path introduces filesystem identity, lifetime, accessibility, and authority instead of returning the image itself.

### Return a URL

Rejected.

A URL introduces hosting, retrieval, network, credential, disclosure, and lifetime semantics.

### Generic binary or media result

Rejected.

The semantic result is one validated image, not arbitrary bytes.

No shared media abstraction has been earned.

### Arbitrary bytes plus MIME type

Rejected.

A claimed media type does not establish bounded geometry, complete decodability, metadata safety, color semantics, or still-image cardinality.

### Decoded pixel arrays

Rejected.

This would force unnecessary core semantics for memory layout, channels, pixel storage, and low-level media representation.

A validated encoded image is smaller and remains suitable for future transport decisions.

### JPEG as the normalized representation

Rejected.

Normalization would require HAC to choose lossy quality policy.

### WebP as the normalized representation

Deferred for the first slice.

It exposes a broader codec/container surface, including lossy/lossless and animation behavior, without a demonstrated advantage over the restricted PNG profile.

### Full unrestricted PNG

Rejected.

General PNG includes grayscale, palette, `tRNS`, interlace, arbitrary ancillary metadata, ICC profiles, and other features outside the first contract.

### 8-bit-only PNG

Rejected.

It would silently require irreversible precision reduction for legitimate 16-bit runtime output.

### RGB-only PNG

Rejected.

It would require transparency loss or a background-compositing policy.

### Untagged RGB/RGBA

Rejected.

Color interpretation would become decoder/device dependent.

### Arbitrary ICC profiles

Rejected.

They would introduce generic profile and color-management semantics beyond the first slice.

### Canonical re-encoding in core

Rejected.

Validation does not require canonical compression, filters, or IDAT splitting.

Runtime-specific normalization belongs in adapters.

### Caller-selected dimensions

Deferred.

The first request does not need another control surface. The 2,048-axis values are result bounds, not caller entitlements.

### Remote transport in the same RFC

Rejected.

The local request/result contract can exist independently of wire representation.

### Production runtime selection in the same RFC

Rejected.

Engine-independent semantics should exist before choosing a concrete image engine.

## Trade-offs

### No immediate operator surface

RFC-0120 intentionally accepts no CLI, Web UI, public API, runtime configuration, or production image adapter.

The first implementation is an architectural local proof rather than an operator-facing feature.

This is intentional:

> fake in distribution, but not fake in architecture.

### Fixed normalization adds adapter work

A runtime that does not naturally produce the accepted profile may require adapter-side decoding, conversion, and re-encoding.

That cost keeps runtime-native formats out of the core.

### sRGB narrows color scope

Wide-gamut, HDR, and arbitrary profile semantics remain outside the first result.

Adapters unable to perform truthful conversion must fail normalization.

### 16-bit support increases bounded decode size

The maximum raw `RGBA16` pixel raster is 32 MiB, and the corresponding maximum inflated non-interlaced scanline stream is 32 MiB + 2 KiB.

This remains finite and avoids hidden precision loss.

### Closed metadata discards runtime artifact metadata

This is intentional.

The normalized result represents the generated image, not incidental runtime metadata.

### Local executable and remote transport domains diverge

The implementation may need to distinguish locally request-executable request/result types from the smaller remotely transportable domain.

That distinction reflects the accepted architecture rather than introducing generic distribution machinery.

## Implementation authorization

If accepted, RFC-0120 authorizes only the local core vertical required to prove this architecture.

Implementation may add:

* the semantic capability `image-generation`;
* one dedicated normalized Image Generation request;
* one dedicated normalized Image Generation result;
* one Image Generation execution contract under RFC-0119;
* the corresponding RFC-0119 capability-to-execution-contract admission rule;
* local request dispatch;
* local capability-routing proof;
* local RFC-0108 binding proof;
* cluster-owned HAC still-PNG validation;
* the smallest typing distinction required to keep Image Generation outside existing remote transport;
* focused in-process test adapters.

It does not authorize:

* a production image runtime;
* image runtime configuration;
* static or retained image capability configuration;
* remote Image Generation transport;
* receiver Image Generation execution;
* CLI;
* Web UI;
* browser API;
* output files;
* filesystem authority.

## Impact

### Capability model

HAC gains the semantic capability `image-generation`.

Existing operator-facing static and remote capability surfaces remain closed.

### Request/result model

HAC gains one dedicated Image Generation request and result for the local request-executable domain.

The result contains validated PNG bytes plus `node_id`.

### Adapter contracts

RFC-0119 gains one capability-to-execution-shape relationship:

```text
image-generation
    -> Image Generation execution shape
```

Existing execution shapes remain unchanged.

### Local execution

Local request-variant dispatch gains the Image Generation path.

### Validation

HAC gains one capability-specific closed still-PNG validation contract.

No generic media validator is introduced.

### Routing and binding

Ordinary local capability routing and RFC-0108 subset/non-overlap semantics remain unchanged.

### Remote execution

The remotely transportable request/result domain remains unchanged.

### Existing production runtimes and operator surfaces

No change.

### Authority

No new filesystem or network authority.

## Decision

Home AI Cluster accepts the semantic capability:

```text
image-generation
```

with the distribution-independent meaning:

```text
one non-blank caller-supplied textual instruction
    <= 65,536 UTF-8 bytes

        ->

exactly one bounded still image
```

RFC-0120 authorizes that capability only inside local request-executable compositions.

It does not authorize any path that transports or executes Image Generation remotely.

Ordinary local capability routing selects an execution-coherent local adapter. RFC-0119 gains:

```text
image-generation
    -> Image Generation execution shape
```

The adapter owns runtime-specific generation and normalization.

HAC core independently validates the candidate representation before constructing a successful result.

The normalized image representation is exactly:

```text
PNG signature

IHDR
    standard payload length = 13 bytes

sRGB
    exactly one
    payload length = 1 byte
    rendering intent = 0..3

one or more consecutive IDAT chunks
    whose ordered payload concatenation is
    exactly one complete PNG zlib datastream

IEND
    exactly one
    empty payload

end of input
```

All accepted chunks require valid CRCs.

No other critical or ancillary chunks are permitted.

The accepted pixel layouts are exactly:

```text
RGB8
RGBA8
RGB16
RGBA16
```

with:

```text
compression method = 0
filter method      = 0
interlace          = none
```

Animation, palette, grayscale normalized layouts, `tRNS`, arbitrary metadata, arbitrary color profiles, and unknown chunks are outside the profile.

The independent bounds are:

```text
complete encoded PNG <= 41,943,040 bytes
width                <= 2,048 pixels
height               <= 2,048 pixels
```

Derived maximum geometry is:

```text
4,194,304 pixels
```

The maximum raw `RGBA16` pixel raster is:

```text
2048 * 2048 * 4 * 2
=
33,554,432 bytes
=
32 MiB
```

The corresponding maximum inflated non-interlaced scanline stream includes one filter byte per row:

```text
2048 * (1 + 16,384)
=
33,556,480 bytes
=
32 MiB + 2 KiB
```

These are derived validation facts, not additional policy knobs.

The validator must derive the exact expected inflated stream size for each accepted image and require exactly one complete zlib stream, with no unused compressed bytes, no missing or excess inflated bytes, complete scanlines, and valid filter bytes.

Validation must establish finite encoded and geometry bounds before performing work proportional to decompressed output.

A successful result contains the validated PNG bytes and ordinary `node_id` attribution outside the PNG.

Existing remote request/result envelopes, static remote declarations, retained/runtime image configuration, production adapters, CLI, Web UI, browser API, filesystem authority, and remote transport remain unchanged.

No generic media abstraction, generic execution operation, ranking system, post-start fallback rule, or production image runtime is accepted by this RFC.
