# RFC-0121: Explicit stable-diffusion.cpp Image Generation Adapter

Status: Accepted

Date: 2026-09-12

Author: frian

## Summary

This RFC selects `stable-diffusion.cpp`, through one operator-managed local
`sd-server` process, as the first concrete runtime implementation of the
accepted RFC-0120 `image-generation` vertical.

The concrete adapter has stable HAC identity:

```text
stable-diffusion-cpp
```

It implements only the RFC-0119 common `RuntimeAdapter` surface and the Image
Generation execution contract. Its complete positive capability set is exactly
`image-generation`. It has no artificial Chat, Summarize, or Classify methods.

HAC communicates only with an explicitly supplied loopback HTTP `sd-server`
origin. The operator owns the runtime process, its model, lifecycle, device,
and runtime policy. The adapter privately uses the native `sd-server` Image
Generation API family, normalizes one native result into the already accepted
RFC-0120 HAC still-PNG representation, and returns candidate bytes to the
unchanged cluster-owned validator.

This is a real local-inference proof, not an ordinary operator product surface.
It authorizes programmatic construction and one explicit programmatic local
binding only. It adds no retained configuration, CLI, browser UI, remote
transport, filesystem output, model-management, job/queue abstraction, or
generic image/media infrastructure.

## Context

RFC-0119 separates the common adapter surface from explicit operation-shaped
execution contracts. It requires every positive adapter capability claim to
have its required execution contract before request-executable admission, while
leaving RFC-0108 local binding ownership and operation-blind routing unchanged.

RFC-0120 accepted the semantic capability:

```text
image-generation
```

with this complete meaning:

```text
one bounded caller-supplied textual instruction
    ->
exactly one bounded still image
```

It already accepts `ImageGenerationRequest`, `ImageGenerationResult`, the
Image Generation execution shape, local request-executable use, adapter-owned
runtime-specific normalization, cluster-owned independent still-PNG validation,
and one closed HAC still-PNG representation. It deliberately leaves the first
real production runtime and any operator product surface open.

The normalized request deliberately contains no model, runtime, dimensions,
aspect ratio, seed, negative prompt, sampler, scheduler, steps, guidance,
quality, style, batch count, output format, or filesystem path. A successful
normalized result is the actual validated HAC still-PNG bytes plus ordinary HAC
node attribution, not a model identity or a runtime-native response.

## Problem

The accepted vertical needs one real non-text runtime proof without changing
its semantic request/result contract or turning HAC into an inference engine,
runtime manager, media framework, or operator image product.

The first runtime must make the adapter boundary concrete: real local inference
must produce one runtime-native image, adapter-owned normalization must produce
a candidate RFC-0120 image, and unchanged core validation must decide whether a
normalized result exists. Runtime-owned generation details and any native
asynchronous mechanics must remain private to that adapter.

## Goals

This RFC aims to:

* select one first real local runtime for RFC-0120 Image Generation;
* preserve the semantic `image-generation` request and result contracts;
* exercise RFC-0119's operation-shaped adapter architecture with an image-only
  adapter;
* keep the runtime process, model, lifecycle, and generation policy
  operator-owned or adapter-private;
* preserve RFC-0085's HAC-owned HTTP environment/privacy boundary and the
  applicable RFC-0089 origin-only base-URL discipline;
* define a bounded adapter-specific path from native runtime output to the
  existing closed HAC still-PNG profile;
* keep the RFC-0120 validator authoritative and unchanged; and
* require a real, local, operator-started inference proof without expanding
  ordinary HAC operator surfaces.

## Non-goals

This RFC does not add or authorize:

* remote Image Generation transport, receiver Image Generation, or static
  remote `image-generation`;
* retained Image Generation configuration, an ordinary retained runtime choice,
  runtime-composition TOML syntax, CLI Image Generation, Web UI Image
  Generation, browser/public image API, or filesystem save/output paths;
* model selection in `ImageGenerationRequest`, model download, installation,
  discovery, or runtime lifecycle management;
* caller-supplied width, height, seed, steps, sampler, scheduler, guidance,
  negative prompt, arbitrary generation dictionary, or prompt-embedded runtime
  control channel;
* multiple images, batches, galleries, image understanding, image editing,
  image-to-image, video, or audio;
* HAC workflow, job, queue, polling, background-task, scheduling, ranking,
  capacity, runtime-discovery, or runtime-preference semantics;
* generic media, blob, binary, image-conversion, color-management, or image
  processing architecture; or
* Pillow, OpenCV, ImageMagick, Docker, Kubernetes, a database, or dashboard.

## Proposal

### One explicit image-only adapter

HAC selects `stable-diffusion.cpp`, via its `sd-server` process, as the first
concrete local implementation of RFC-0120 Image Generation.

The adapter's stable HAC identity is:

```text
stable-diffusion-cpp
```

Exact Python class names are implementation details. The adapter is permitted
to implement only:

```text
common RuntimeAdapter surface
+
Image Generation execution contract
```

Its positive capability set is exactly:

```text
image-generation
```

It must not gain fake `chat()`, `summarize()`, or `classify()` methods merely
to resemble text adapters. Under RFC-0119, its positive claim must be
execution-coherent before it is admitted into request-executable composition.
The adapter's mechanics do not themselves create support for any additional
capability.

### External operator-managed local runtime

`sd-server` is an external, operator-managed local runtime. The accepted
topology is:

```text
ordinary HAC process
        |
        | loopback HTTP
        v
operator-managed sd-server
        |
        v
operator-selected image model
```

HAC does not install, download, launch, stop, restart, supervise, update, or
otherwise manage `stable-diffusion.cpp` or `sd-server`. HAC also does not
download, install, discover, or choose models; manage device placement,
quantization, scheduling, queues, caches, or model files; or infer runtime
availability from process existence. The operator starts `sd-server` with a
model suitable for image generation.

The model and its identity remain runtime-owned configuration. No model value
is added to `ImageGenerationRequest`, and no model attribution is required in
`ImageGenerationResult`.

### Local runtime HTTP boundary

For this adapter, HAC communicates only with an explicitly supplied local
loopback HTTP `sd-server` endpoint. The endpoint is a runtime origin subject to
the applicable RFC-0089 base-URL discipline: it is not a path, query,
fragment, user-information, credential, or generic arbitrary resource URL.

HAC-owned HTTP clients retain RFC-0085's privacy/environment boundary. This
RFC does not authorize arbitrary LAN or Internet runtime endpoints, TLS,
runtime authentication, credentials, or remote HAC Image Generation. This
runtime integration is distinct from HAC remote transport. A future remote
Image Generation RFC must reuse RFC-0120 semantics rather than expose
`sd-server` directly.

### Native API is adapter-private

The private integration boundary is the native `sd-server` Image Generation API
family, whose relevant native entrypoint is:

```text
/sdcpp/v1/img_gen
```

The native API may use asynchronous submission, a job identifier, queue state,
polling/status, and result retrieval. Those facts remain wholly inside the
adapter. Exact payloads, status/result paths, polling intervals, and parsing
are implementation details and are not frozen here except where needed to
preserve the boundaries below.

In particular, native job mechanics do not authorize HAC-level types or
surfaces such as:

```text
ImageGenerationJob
HacJob
Workflow
Queue
PollingResult
BackgroundTask
```

The public execution remains one foreground HAC operation:

```text
generate Image Generation request
    -> privately submit/wait for native work
    -> obtain one native result
    -> normalize one candidate image
    -> return through the ordinary execution contract
```

Existing timeout and cancellation semantics remain authoritative. If HAC stops
waiting because the ordinary request times out or is cancelled, the adapter
stops owning the wait; this RFC does not require HAC to cancel work already
engaged inside `sd-server`.

### Instruction is not a runtime-control channel

This RFC deliberately does not select the `sd-server` OpenAI-compatible Image
Generations endpoint merely because it is synchronous or familiar. Current
`stable-diffusion.cpp` behavior on that path can accept prompt-embedded runtime
controls conceptually shaped as:

```text
<sd_cpp_extra_args>{...}</sd_cpp_extra_args>
```

That would blur RFC-0120's deliberate distinction between its only
caller-controlled semantic field, `instruction`, and runtime generation
controls. The native API keeps the textual prompt distinct from structured
runtime parameters. For this adapter:

```text
caller textual instruction
    !=
caller runtime-control channel
```

This is a runtime-specific first-adapter choice, not a general ban on
compatibility APIs.

The native runtime necessarily needs dimensions, seed, steps, sampler,
scheduler, guidance, and batch policy. They remain runtime configuration or
adapter-private invocation policy. The adapter may set private runtime
parameters when necessary to guarantee the accepted result contract, including
reducing each HAC request to exactly one runtime image selected for
normalization. It must not expose those controls through instruction parsing or
caller-supplied arbitrary dictionaries. Exact values remain implementation
details unless a later architectural bound requires otherwise.

### Runtime result normalization

The selected runtime's output is not automatically the closed RFC-0120 HAC
still-PNG representation. The boundary is:

```text
runtime PNG
    ->
bounded adapter-owned structural normalization
    ->
candidate HAC still-PNG
    ->
independent RFC-0120 validation
```

Current evidence relevant to this adapter is that image generation produces
ordinary 8-bit RGB/RGBA image data, PNG output is encoded through
`stb_image_write`, and runtime image handling uses the sRGB image-sample
convention where it performs color-space-aware resizing. That observation does
not by itself establish either the color interpretation of generated output
samples or RFC-0120's exact closed PNG chunk vocabulary.

The adapter must request runtime output with generation metadata disabled where
the runtime offers that control; for current `sd-server`, this is the
runtime-private equivalent of:

```text
embed_image_metadata = false
```

Runtime generation parameters, model names, software identifiers, paths,
timestamps, comments, and other metadata must not cross the normalized-result
boundary. RFC-0120 validation remains final authority.

For this first adapter, normalization should be bounded structural PNG work
that preserves pixel samples, rather than a generic image-processing pipeline.
The adapter may:

* base64-decode the runtime response under explicit bounds;
* parse the PNG container under explicit bounds;
* require RFC-0120-compatible 8-bit RGB or RGBA `IHDR` values;
* reject unsupported, interlaced, or incompatible representations;
* omit runtime ancillary metadata;
* produce exactly one `sRGB` chunk only when the generated samples are
  truthfully sRGB;
* preserve an encoded `IDAT` pixel stream when that is truthful;
* produce valid PNG chunk CRCs and final structure; and
* fail closed if truthful normalization cannot be established.

This RFC does not require raster decoding/re-encoding or make Pillow, OpenCV,
ImageMagick, generic color management, a generic conversion service, or a
generic media abstraction architectural requirements. If implementation evidence
shows truthful normalization cannot fit this bounded adapter-specific boundary,
implementation must stop for architectural review rather than silently add an
image-processing subsystem.

### Color honesty and unchanged core validation

RFC-0120 remains authoritative: non-sRGB data must not be relabeled as sRGB.
This RFC makes no formal universal color-profile claim for
`stable-diffusion.cpp`. Current upstream evidence that some image-processing
paths use an sRGB convention does not by itself establish the color
interpretation of generated output samples.

The adapter may add RFC-0120's required `sRGB` identification without changing
pixel samples only when implementation evidence establishes that the generated
samples are truthfully sRGB. Otherwise normalization must fail closed. If
truthful normalization requires actual color conversion or a broader
image-processing/color-management subsystem, implementation must stop and
return to architectural review rather than silently introducing that machinery.

The core must not become a generic color-management engine. Nor does the core
accept runtime-specific exceptions or a weakened still-PNG profile. The flow
remains:

```text
adapter produces candidate bytes
        |
        v
RFC-0120 core PNG validator
        |
        +-- valid -> ImageGenerationResult
        |
        +-- invalid -> fail
```

Final result validation does not move into the adapter.

### Health, failure, and local binding

`health()` remains descriptive and adapter-owned under the common adapter
surface. It must test a meaningful `sd-server` HTTP readiness boundary rather
than process existence. The exact stable native health/status path, if one is
needed, remains an implementation detail.

Runtime transport failure, malformed response, queue rejection, generation
failure, timeout, and normalization failure should use existing HAC-owned
failure semantics whenever those semantics match exactly. This RFC does not add
a runtime-failure taxonomy merely to expose `sd-server` detail. It does not
leak HTTP-client exceptions, native JSON envelopes, runtime job objects, or raw
upstream errors through normalized HAC contracts.

Routing semantics remain unchanged. The adapter may participate only through
an explicit programmatic local binding whose capability set is exactly:

```text
image-generation
```

RFC-0108's binding ownership proof remains separate from adapter support, and
routing remains operation-blind. Mechanical support does not itself make the
adapter available to an arbitrary composition. No static remote capability
vocabulary, remote fallback, ranking, preference, or RFC-0108 semantics change.

### Programmatic proof only

The first real proof authorizes programmatic construction/composition of the
adapter and its one local binding. It does not add `stable-diffusion-cpp` to
retained `hac config local`, ordinary runtime choices, runtime-composition
TOML, CLI startup selections, browser configuration, or ordinary installed
Image Generation commands.

The sequence is intentional:

```text
real architecture proof
    first

operator convenience
    later
```

## Rationale

This is the smallest useful next step because it proves all accepted seams with
one real non-text inference result while leaving cluster-facing semantics
independent of runtime, model, job, image-file, and media-processing identity:

```text
semantic capability
    RFC-0120

operation-shaped execution contract
    RFC-0119

engine-specific adapter
    RFC-0030 / RFC-0107 precedent

explicit local capability binding
    RFC-0108

runtime-owned inference details
    engine independence

cluster-owned normalized result validation
    RFC-0120
```

An external loopback runtime keeps inference dependencies, model lifecycle,
device placement, and model storage outside HAC. The native API prevents a
caller instruction from becoming an accidental runtime-control channel. Bounded
structural PNG normalization makes the runtime-specific difference visible at
the correct adapter boundary, while independent core validation preserves the
truth of the normalized result.

The intended proof is minimal in operator surface but real in inference.

## Alternatives considered

### Ollama

Ollama is attractive because HAC already has an Ollama adapter and RFC-0119
allows one adapter to implement several operation-shaped execution contracts.
It is not selected because current upstream Image Generation support is not a
sufficiently stable basis for the first real HAC proof: experimental support
introduced in 2026 was subsequently removed, and current versions continue to
reject image-generation models. This does not make Ollama architecturally
unsuitable forever; stable future upstream support can be evaluated separately.

### ComfyUI

ComfyUI can hide workflow and queue mechanics behind an adapter, so it does not
demonstrate that HAC requires a workflow or job abstraction. It is not selected
for the first proof because its runtime-private workflow, node, queue, and
completion mechanics are substantially more than is needed to test RFC-0120.
Future ComfyUI support is not rejected.

### Diffusers

Diffusers usefully demonstrates that HAC must not generalize all runtimes into
external HTTP servers: an in-process runtime remains architecturally possible.
It is not selected first because it would bring PyTorch, model loading, device
placement, memory/lifecycle coupling, and image-pipeline dependencies into the
HAC process. This pragmatic choice is not a permanent external-runtime rule.

### OpenAI-compatible sd-server Image Generations endpoint

Protocol familiarity and synchronous behavior are insufficient reasons to use
this endpoint. For this first adapter, its prompt-embedded
`sd_cpp_extra_args` behavior weakens the clean RFC-0120 separation between
caller text and runtime controls. The native API is therefore selected. The
compatibility endpoint is not globally forbidden.

## Trade-offs

The proof adds one concrete adapter, local loopback HTTP translation, private
native-job waiting, and bounded PNG structural normalization. It also depends
on an operator having started a suitable local runtime/model, while deliberately
offering no ordinary configuration or user-facing product path.

These costs are acceptable because they keep each concern at its correct owner:
the operator owns runtime lifecycle and model policy, the adapter owns native
protocol and normalization, and the core owns the stable result contract. The
alternative would either weaken RFC-0120 or prematurely add broad image/runtime
infrastructure.

## Impact and proof expectations

Acceptance would authorize a separate bounded implementation and proof. It
would not make `stable-diffusion.cpp` an ordinary supported operator runtime
until that implementation, its evidence, documentation, and subsequent product
decisions are complete.

The implementation is complete only when it demonstrates all of the following:

1. The ordinary automated suite remains independent of an installed or running
   `sd-server`.
2. The adapter satisfies the RFC-0119 Image Generation execution contract and
   claims exactly `image-generation`.
3. A real operator-started loopback `sd-server` with one suitable local image
   model is used.
4. One real Image Generation request succeeds through ordinary local HAC
   routing/composition and exactly one real image is returned.
5. The returned bytes pass the unchanged RFC-0120 validator; runtime generation
   metadata does not survive normalization; and HAC needs no filesystem output
   path.
6. Stopping or making `sd-server` unavailable produces a HAC-owned failure
   without leaked transport details.
7. The proof adds no remote transport, operator configuration, CLI, Web UI, or
   generic media abstraction.
8. A focused regression proves that literal instruction text resembling
   runtime-private control syntax remains caller text and cannot authorize
   arbitrary runtime generation parameters.

## Open questions

Exact adapter class names, native payload details, readiness/status path,
polling cadence, private invocation defaults, and parsing mechanics remain
implementation details. They may not broaden the boundaries in this RFC.

An operator selection/configuration surface, remote Image Generation transport,
and support for other image runtimes require separate RFC decisions if later
justified.

## Decision

Accepted.
