# RFC-0131: Bounded Image Generation Dimensions

Status: Draft

Date: 2026-09-17

Author: frian

## Summary

Home AI Cluster extends the normalized `image-generation` request with one
optional exact output-geometry pair:

```text
instruction
width
height
```

The pair is closed:

```text
width and height both absent
OR
width and height both present
```

Exactly one present is invalid. When present, each value is an integer in the
inclusive range `64..2048`. The pair is an exact semantic requirement for a
successful result, not a hint, preference, aspect-ratio suggestion, silently
rounded target, or runtime configuration value.

HAC core retains ownership of normalized PNG validation. In addition to the
existing complete still-PNG validation and global `<= 2048` axis bounds, core
must verify the candidate IHDR width and height exactly when the request names
dimensions. An adapter or runtime claim is insufficient. A candidate whose
geometry differs from the requested pair cannot become a successful HAC Image
Generation result.

When dimensions are absent, existing instruction-only semantics remain
unchanged: HAC expresses no caller-selected geometry requirement and an
adapter/runtime may use its existing configured or native default dimensions.

This RFC adds the same optional paired geometry request vocabulary to existing
Image Generation caller surfaces. It creates no new capability, route, result
representation, routing, transport, runtime selection, retained configuration,
filesystem authority, or browser authority. It authorizes a later
implementation to project a present semantic pair into the private
adapter-native mechanism appropriate to an eligible runtime.

## Context

RFC-0120 accepted the bounded `image-generation` semantic capability and one
normalized request containing only a textual instruction. It deliberately
excluded caller-selected dimensions. It also made HAC core, rather than an
adapter, authoritative for complete validation of the normalized still-PNG
result.

RFC-0121 selected stable-diffusion.cpp as the first private Image Generation
adapter while preserving the engine-independent request/result boundary.
RFC-0122 retained the closed still-PNG profile while narrowing color signaling
to truthful `sRGB` or no color-space signaling. RFC-0127 exposed the same
instruction-only operation through a native local HTTP route and one thin
`hac image-generation` client. RFC-0128 retained one optional local companion
composition, while RFC-0129 and RFC-0130 projected the unchanged operation
into the loopback and trusted-LAN browser authorities respectively.

Physical validation has now shown the limit of instruction-only geometry:

```text
"200x200px" inside an instruction
!=
an established output-geometry requirement
```

If HAC is to let a caller require output dimensions, geometry must be explicit
normalized semantic request data. That need does not make geometry a generic
runtime-control channel.

## Problem

Text in an instruction can describe a desired image but cannot establish the
observable width and height of a successful result. A runtime may interpret,
ignore, or approximate such text. Consequently, instruction-only Image
Generation cannot truthfully promise caller-selected geometry.

Adding current-engine request parameters directly to HAC would solve the wrong
problem. Names such as width and height may also occur in one runtime's native
API, but the project-owned concern is not that API knob. It is the observable
successful PNG geometry:

```text
caller requires 512 x 768
    ->
successful normalized PNG has IHDR 512 x 768
```

The architecture needs the smallest bounded request extension that can state
that requirement without exposing a generic generation-options dictionary,
runtime syntax, model policy, or silent approximation.

## Goals

This RFC proposes to:

* add one optional, paired exact geometry requirement to normalized Image
  Generation requests;
* preserve existing instruction-only requests unchanged when both fields are
  absent;
* bound each caller-selected axis to an integer in `64..2048`;
* make explicit geometry an exact observable result requirement;
* retain HAC core ownership of complete normalized PNG and exact-geometry
  validation;
* permit adapters to project the semantic pair privately into their own
  runtime-native mechanisms; and
* carry the same normalized semantics through the existing native HTTP, CLI,
  loopback-browser, and trusted-LAN-browser projections when implemented.

## Non-goals

This RFC does not add or decide:

* a new capability, routing rule, adapter-selection rule, static declaration,
  remote Image Generation transport, or receiver Image Generation;
* model, runtime, hardware, distribution, latent-grid, or engine-specific
  geometry semantics;
* a required multiple of 8, 16, 32, 64, or any other runtime-specific unit;
* aspect-ratio-only input, presets, arbitrary aspect ratios, orientation,
  resolution names, image size labels, or a generic dimensions object;
* seed, sampler, scheduler, steps, guidance, negative prompt, style, quality,
  batch count, output format, or any other generation control;
* default-dimension selection, retained dimension configuration, or explicit
  dimensions merely to reproduce a runtime default;
* silent rounding, clamping, resizing, cropping, padding, scaling, or fallback
  to a different output geometry;
* a generic image conversion, resampling, media, asset, blob, or binary-result
  abstraction;
* any change to RFC-0120/RFC-0122's still-PNG profile other than checking a
  request's present exact geometry against its already parsed IHDR; or
* implementation, migration, compatibility shim, browser layout decision, or
  production runtime policy.

## Proposal

### One optional paired semantic requirement

`ImageGenerationRequest` gains these optional fields in addition to its
unchanged bounded `instruction`:

```text
width:  integer | absent
height: integer | absent
```

Their complete validity rule is:

```text
width absent and height absent
    -> valid instruction-only request

width present and height present
    -> valid exact-geometry request, subject to per-axis bounds

exactly one present
    -> invalid request
```

For a present pair:

```text
64 <= width  <= 2048
64 <= height <= 2048
```

Both values are integers. Fractional values, strings, booleans, zero, negative
values, values below 64, values above 2048, unknown fields, and one-sided
pairs are invalid at the normalized request boundary.

The request remains an explicit `image-generation` request with the same
capability and routing semantics. Dimensions neither introduce another
capability nor narrow routing based on model/runtime identity. An eligible
adapter must be able to execute the normalized request truthfully; it cannot
turn the pair into a best-effort request and still return success.

### Exact means exact

The pair describes a semantic output requirement, not a runtime-specific
generation knob. For example:

```text
request:
    instruction = "..."
    width = 512
    height = 768

successful normalized result:
    IHDR width  = 512
    IHDR height = 768
```

Any other candidate geometry fails the Image Generation result contract for
that request. In particular, a runtime must not silently round to a supported
grid, substitute a default, preserve only an aspect ratio, or generate another
size and rely on HAC to transform it. HAC does not add transformation authority
to make a candidate conform.

When both fields are absent, the request continues to make no assertion about
geometry beyond RFC-0120's global valid-PNG bounds. An adapter/runtime may use
its existing configured or native default dimensions. It must not invent a
present pair solely to spell that default.

### Bounded first product envelope

RFC-0120 already caps every normalized-result axis at 2048. This first
caller-selected geometry contract deliberately narrows the selectable range to
the finite useful envelope:

```text
64..2048 inclusive per axis
```

The lower bound is a bounded first product contract, not a claim that every
current or future image engine shares a particular minimum. The upper bound
does not expand RFC-0120's existing result bound. Neither value encodes a
model name, runtime name, latent-grid term, or runtime-specific multiple.

An adapter/runtime that cannot satisfy an otherwise valid HAC pair exactly
cannot return a successful result for that request. Its particular limitation
remains adapter/runtime behavior; it does not redefine the cluster-facing
semantic contract.

### Core-owned validation

HAC core continues to validate every candidate's full normalized still-PNG
profile, including RFC-0120/RFC-0122 structure, decoding, resource bounds, and
global geometry bounds. After core obtains the IHDR width and height, it must
also apply this request-dependent rule:

```text
no requested pair
    -> existing global PNG validation is sufficient

requested pair
    -> IHDR width and height must each equal the corresponding request value
```

This check belongs to core validation at result normalization, after adapter
execution and before construction of `ImageGenerationResult`. Exact internal
function signatures and the representation used to pass the request context
are implementation details.

Adapter-side checks may reject impossible native requests early, but they do
not replace HAC-owned result validation. A runtime that ignores, misreads, or
reports dimensions incorrectly therefore cannot yield a successful HAC result.

### Engine-independent adapter projection

The durable architecture is:

```text
caller semantic request
    -> ordinary image-generation capability routing
    -> eligible adapter
    -> runtime-specific projection
    -> candidate image
    -> HAC-owned normalized PNG validation
    -> successful exact-geometry result
```

Adapters may project a present semantic pair into the runtime-native mechanism
appropriate to that adapter. HAC core must not learn stable-diffusion.cpp
request syntax, native parameter names, or engine limitations.

The current stable-diffusion.cpp adapter already privately owns native request
projection. A later implementation may project present HAC width and height
into that private native Image Generation request. With both fields absent, it
must preserve current native request behavior and not add explicit geometry to
reconstruct a runtime default.

### Existing caller edges

The normalized request, rather than a separate edge-specific request shape,
remains the sole semantic boundary. A later implementation may extend the
existing closed inputs as follows:

```text
POST /v1/image-generation
    JSON: instruction, optional paired width/height
    success: unchanged raw image/png

hac image-generation
    existing instruction plus --width <PIXELS> --height <PIXELS>
    success: unchanged exact PNG bytes on non-TTY stdout

loopback and trusted-LAN Image Generation views
    instruction plus optional paired dimensions
    success: unchanged one ephemeral current displayed image
```

Those projections must use the same core request validation. They do not add
new routes, response envelopes, result metadata, output paths, browser
authority, persistence, or filesystem authority.

### Bounded CLI geometry surface

RFC-0127's existing operator command gains exactly these optional CLI options:

```text
hac image-generation ... --width <PIXELS> --height <PIXELS>
```

`--width` and `--height` are the RFC-owned operator-facing names. Their
complete CLI rule is:

```text
neither supplied
    -> existing instruction-only behavior

both supplied
    -> exact geometry request

only one supplied
    -> local CLI validation failure

either outside 64..2048
    -> local CLI validation failure
```

The command preserves RFC-0127's existing instruction grammar, timeout
behavior, raw PNG success on stdout, non-TTY stdout requirement, stderr
activity/failure behavior, and absence of filesystem output. It does not add
`--size`, aspect ratio, presets, output format, output path, seed, sampler,
steps, CFG, style, or other generation controls. Exact Python parser mechanics
remain implementation details.

## Rationale

Width and height are accepted because they state an observable requirement of
the successful result. They are not accepted merely because one currently
selected runtime happens to have similarly named native parameters. The core
can establish the requirement independently from IHDR, which makes the promise
truthful across adapters and runtimes.

The all-or-nothing pair prevents ambiguous requests such as a requested width
with unspecified height. Exact matching is preferable to best effort because a
quietly changed geometry would make the normalized result contradict the
caller’s request. The `64..2048` range creates a small useful first surface
without importing engine-specific constraints into HAC semantics.

Keeping the check in HAC core preserves the existing normalized-result trust
boundary. It prevents a compliant-looking runtime request from substituting for
evidence in the returned image bytes.

## Alternatives considered

### Keep geometry inside the instruction

Rejected. Natural-language text does not establish output geometry and may be
ignored or interpreted as a visual-description request.

### Expose stable-diffusion.cpp native options in HAC

Rejected. This would make a runtime-specific control surface the normalized
architecture and would not establish an engine-independent successful-result
contract.

### Accept aspect ratio, presets, or one axis

Rejected. Each leaves one or both exact observable axes unspecified. The
smallest useful requirement is one complete width/height pair.

### Round or clamp valid HAC dimensions for a runtime

Rejected. A silently altered candidate would not satisfy the caller's semantic
request. Runtime limitations belong behind the adapter boundary and lead to
safe failure for an unsatisfied exact request.

### Require engine-grid multiples in HAC

Rejected. A multiple-of-N rule encodes current runtime assumptions rather than
the observable result requirement, unnecessarily narrowing future adapters.

### Validate exact geometry only in adapters

Rejected. Adapter claims and native request acceptance do not prove output
geometry. HAC core already owns normalized PNG validation and must remain the
authority for the result contract.

### Expand selectable dimensions to all RFC-0120-valid PNG geometries

Rejected. RFC-0120's result safety ceiling is not evidence that every smaller
geometry is a useful caller-selected first product surface. `64..2048` is the
accepted bounded envelope.

## Trade-offs

Some runtimes may be unable to fulfill valid HAC dimensions without rounding
or using their own restricted geometry rules. HAC chooses honest safe failure
over pretending that a nearby image satisfies the request.

The additional fields require consistent validation and projection across the
existing caller edges. That duplication is bounded because every edge uses one
normalized request and the raw-PNG successful result remains unchanged.

The lower bound intentionally excludes small but globally valid PNGs from
caller-selected geometry. This is a deliberate product limit and can be
revisited only by a later architectural decision.

## Proof expectations

A later implementation should prove the following focused boundary behavior;
these are proof expectations, not a requirement to add redundant tests merely
for completeness:

1. Instruction-only normalized requests remain valid and behavior-compatible.
2. Width and height are both absent or both present, and present values are
   integers within `64..2048`.
3. Strings, booleans, fractional values, partial pairs, and unknown request
   fields remain invalid where applicable.
4. An explicit exact geometry requirement survives the semantic request path
   into the eligible adapter.
5. The stable-diffusion.cpp projection sends native width and height only when
   explicitly requested, while instruction-only requests retain current native
   defaults and do not invent explicit dimensions.
6. HAC core accepts an otherwise-valid normalized PNG whose IHDR exactly
   matches the requested pair, and rejects both a width mismatch and a height
   mismatch.
7. Native `POST /v1/image-generation` accepts both the existing
   instruction-only form and the exact instruction-plus-width-plus-height form;
   it rejects a partial pair, invalid range/type, and extra fields before
   execution, and its success remains exact raw `image/png`.
8. The CLI accepts neither-or-both geometry options, rejects a partial or
   invalid pair locally, and preserves existing raw-PNG stdout behavior.
9. The loopback browser sends no geometry fields when both controls are blank,
   sends both exact integer fields when both are present, and rejects a partial
   or invalid pair locally.
10. The trusted-LAN browser preserves the same optional-pair semantics without
    widening its closed route, Host, Origin, media-type, Configuration,
    Workspace, or receiver boundaries.
11. Browser-wide one-capability-request-at-a-time behavior and current-image
    replacement/Object URL revocation remain intact.
12. Static caller-local Image Generation permission behavior remains unchanged.
13. Image Generation remains absent from remote transport and receiver
    execution.
14. No runtime/model/configuration/discovery/output-format/filesystem authority
    is introduced.

Physical image-generation proof may be useful later but is not required to
accept this RFC.

## Compatibility and impact

Instruction-only `ImageGenerationRequest` construction remains valid and
unchanged in meaning. Existing adapters keep their native defaults for those
requests. Existing raw `image/png` success, `ImageGenerationResult`, capability
routing, static permission, local composition, RFC-0128 retention, and
loopback/trusted-LAN browser authority remain unchanged.

A later implementation affects the request validators in the core model; core
PNG validation and Image Generation orchestration; private adapter projection;
the closed native HTTP request body; the one-shot CLI; and both fixed browser
forms/JavaScript. The focused proof expectations above apply across those
affected seams.

No migration is required for instruction-only clients. Clients that choose the
new pair must handle ordinary safe failure when no eligible adapter can return
the exact requested geometry.

## Open questions

None for this bounded decision. Future proposals may consider additional Image
Generation semantics only with separate evidence and an RFC; they must not be
inferred from this exact geometry pair.

## Decision

This Draft proposes that normalized `ImageGenerationRequest` gains optional
first-class `width` and `height` fields. They are both absent or both present;
exactly one is invalid. When present, both are integers, with booleans excluded
from integer validity, and each lies in the inclusive `64..2048` range.

Present width and height are exact semantic output requirements, not hints or
preferences. A successful normalized PNG must have IHDR width and height
exactly equal to the requested pair. HAC core owns this request-relative exact
geometry verification; adapter/runtime claims do not substitute for it. HAC
must not silently round, clamp, resize, crop, pad, scale, substitute an aspect
ratio, or fall back to another geometry. When both fields are absent, HAC
expresses no explicit geometry requirement and existing runtime/native
configured defaults remain unchanged.

Adapters privately project present semantic dimensions into their
runtime-native mechanisms. Instruction-only requests must not gain explicit
native dimensions merely to reproduce current runtime defaults. The same
optional pair is added to the existing native `POST /v1/image-generation`
request, `hac image-generation --width <PIXELS> --height <PIXELS>`, loopback
browser Image Generation, and trusted-LAN browser Image Generation surfaces.

This adds no route, capability, response representation, browser authority,
filesystem authority, persistence, retained configuration, runtime/model
discovery, negotiation, or generic generation-options abstraction. Remote
Image Generation, receiver Image Generation, static remote Image Generation
declarations, and Image Generation remote transport remain unauthorized.
Existing static caller-local Image Generation permission behavior is unchanged.
The normalized PNG representation and RFC-0120/RFC-0122 global image bounds
also remain unchanged. The Proposal and Rationale sections define the detailed
application of this decision.
