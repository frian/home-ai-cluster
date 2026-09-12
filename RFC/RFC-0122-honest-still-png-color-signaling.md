# RFC-0122: Honest Still-PNG Color Signaling

Status: Draft

Date: 2026-09-12

Author: frian

## Summary

RFC-0120 accepts `image-generation` as one bounded caller-supplied textual
instruction that produces exactly one bounded still image. Its closed HAC
still-PNG representation currently requires exactly one standard PNG `sRGB`
chunk.

RFC-0122 proposes one narrow correction. A normalized HAC still-PNG would have
exactly one of two closed color-signaling states:

```text
truthful sRGB
OR
no color-space signaling
```

When a valid `sRGB` chunk is present, it continues to identify the samples as
sRGB and must have a truthful basis. When it is absent, HAC preserves the
RGB/RGBA samples without asserting a calibrated color space. No other
color-space chunk, color profile, result field, request control, or generic
color-management architecture is introduced.

All other RFC-0120 still-PNG requirements remain unchanged.

## Context

RFC-0120 chose a closed, independently validated still-PNG profile for local
`image-generation`. RFC-0121 then selected `stable-diffusion.cpp` through an
operator-managed local `sd-server` as the first concrete runtime proof.

Draft PR #746 exercised the intended seams without changing cluster semantics:

```text
ImageGenerationRequest
    -> image-only RFC-0119 adapter
    -> private native runtime API and job mechanics
    -> runtime PNG
    -> adapter-owned normalization
    -> RFC-0120 validation
```

The exact inspected upstream revision was:

```text
7f410a3793c5bba8eb198e962ce7a3d6095f9d89
```

Its generated-PNG path passes generated RGB/RGBA data through
`encode_image_to_vector()` and `stbi_ext_write_png_to_func()`. That path does
not emit a standard `sRGB` identification, and the inspected evidence does not
establish that generated samples are contractually sRGB. The correct Draft
PR #746 adapter therefore fails closed rather than relabeling untagged pixels.

The subsequent falsification review found that ordinary PNG writers in
practical Image Generation paths commonly do not add a standard `sRGB`
identification. Mandatory `sRGB` is consequently stronger than the semantic
meaning RFC-0120 assigned to `image-generation`.

## Problem

The current closed profile combines two distinct facts:

```text
one bounded still image
calibrated sRGB color identification
```

The first is part of `image-generation` semantics. The second cannot always be
truthfully established from a runtime's generated PNG packaging.

Forcing every adapter to manufacture `sRGB` would make unknown color semantics
look known. Requiring color conversion would require known source color
semantics and broader image-processing architecture. Rejecting otherwise valid
bounded still images solely for missing calibration would make runtime
eligibility depend on incidental PNG chunk packaging.

## Goals

This RFC aims to:

* preserve a closed bounded HAC still-PNG representation;
* preserve truthful `sRGB` identification when it is established;
* permit honest absence of a calibrated color-space assertion;
* retain all RFC-0120 non-color validation, bounds, and metadata closure; and
* preserve adapter-owned normalization and cluster-owned validation.

## Non-goals

This RFC does not:

* change the meaning of `image-generation`, its request fields, or its result
  fields;
* change PNG as the normalized representation, RGB/RGBA support, bit depths,
  image size bounds, encoded/inflated bounds, or decompression validation;
* accept arbitrary ancillary chunks, ICC profiles, `gAMA`, `cHRM`, `cICP`, or
  HDR signaling;
* define color conversion, color management, generic image processing, or a
  generic media abstraction;
* change RFC-0119, RFC-0108, RFC-0121's runtime selection, remote Image
  Generation, retained configuration, CLI, Web UI, filesystem authority,
  model management, runtime lifecycle, or dependencies.

## Proposal

### One closed two-state color rule

If accepted, RFC-0122 replaces only this RFC-0120 requirement:

```text
every normalized HAC still-PNG contains exactly one sRGB chunk
```

with:

```text
every normalized HAC still-PNG contains:
    zero or one valid sRGB chunk
```

The resulting representation is exactly one of:

```text
State 1: exactly one truthful standard sRGB chunk
State 2: no color-space signaling at all
```

There is no third color-signaling state.

Conceptually, the closed structure changes only from:

```text
PNG signature
IHDR
sRGB
IDAT...
IEND
EOF
```

to:

```text
PNG signature
IHDR
optional sRGB
IDAT...
IEND
EOF
```

Here, `optional sRGB` means zero or one valid `sRGB` chunk, not an extensible
ancillary-chunk region.

### Truthfully identified sRGB

When present, `sRGB` remains exactly one standard one-byte rendering-intent
chunk with a value in `0..3`, in the accepted position before `IDAT`. Its
meaning remains:

```text
these image samples are identified as conforming to sRGB
```

It is not a generic browser hint or a default assumption. An adapter must have
a truthful basis for preserving or producing it.

### Unspecified color calibration

When no color-space chunk is present, the PNG means:

```text
the RGB/RGBA samples are preserved
without HAC asserting a calibrated color space
```

This state neither makes the image invalid nor secretly identifies it as sRGB.
It states only that HAC has no accepted truthful calibrated color-space
assertion for those samples.

No `color_space`, `color_profile`, `calibrated`, or equivalent HAC result field
is introduced. The narrow distinction remains represented by the PNG container.

### Closed color-signaling vocabulary

`sRGB` remains the only permitted color-space chunk and becomes optional. The
normalized profile continues to reject `iCCP`, `gAMA`, `cHRM`, and `cICP`.

This does not authorize arbitrary ICC profiles, HDR signaling, arbitrary
primaries, arbitrary transfer functions, generic color metadata, or profile
pass-through.

### Truthfulness and normalization

The essential rule remains:

```text
unknown color semantics != sRGB
```

An adapter must not add an `sRGB` assertion to untagged RGB/RGBA samples without
evidence that they are truthfully sRGB. This RFC does not authorize actual color
conversion from an unknown source space, an `assume_srgb` switch, caller color
assertions, browser/display conventions as proof, or inference from unrelated
input-resize behavior.

Adapter-owned bounded structural normalization remains the boundary:

```text
runtime image
    -> adapter-owned bounded normalization
    -> candidate HAC still-PNG
    -> cluster-owned RFC-0120/RFC-0122 validation
    -> ImageGenerationResult
```

An adapter may normalize an untagged runtime PNG into the accepted untagged
state while preserving samples and removing disallowed metadata. It may preserve
a truthfully sRGB-tagged runtime PNG. For other known color signaling, an
adapter may fail closed; this RFC does not require stripping meaningful color
calibration merely to pass, nor does it authorize conversion or reconciliation.

### Unchanged validation

All non-color RFC-0120 still-PNG rules remain authoritative, including its
signature, `IHDR`, geometry, RGB/RGBA and 8/16-bit layouts, non-interlaced
encoding, consecutive `IDAT`, complete bounded zlib stream, scanline extent and
filters, CRCs, final `IEND`, EOF, encoded/raw bounds, unknown-critical-chunk
rejection, ancillary-chunk closure, and metadata privacy.

The minimal later implementation consequence would be only this validator
cardinality change:

```text
Before: sRGB exactly once
After:  sRGB zero or one; if present, valid and truthful
```

No implementation is authorized by this Draft.

## Rationale

### Preserve truthful sRGB and truthful uncertainty

Always stripping color signaling would create one uniform structure, but would
discard truthful sRGB information supplied by a runtime. The proposed two-state
profile instead preserves truthful information when available and truthful
uncertainty when calibration is unavailable. It remains closed and bounded.

### Do not require mandatory sRGB

Mandatory sRGB supplied a stable color interpretation, but the first real
runtime proof showed that it can require knowledge the runtime does not expose.
The semantic capability does not promise calibrated color. Keeping that
requirement would reject valid bounded still images, encourage guessing, select
runtimes based on packaging detail, or require unjustified color-management
machinery.

Engine independence normalizes the semantic operation and result
representation; it does not promise identical pixels, composition, tone,
palette, brightness, or artistic interpretation across generative engines. It
does require honest color signaling:

```text
truthfully sRGB
OR
truthfully unspecified
```

### Privacy and security

The closed profile still prevents arbitrary metadata, private model/runtime/path
leakage, and arbitrary profile-parser exposure. Optional absence of `sRGB`
does not add a parser, metadata, authority, or information-leak surface.
Mandatory `sRGB` was not itself a privacy or security control.

## Relationship to Accepted RFCs

### RFC-0120

RFC-0120 remains Accepted architectural memory and is not superseded. If this
RFC is accepted, it has precedence only where RFC-0120 requires exactly one
mandatory `sRGB` chunk or implies that every normalized result asserts sRGB.
Every non-color decision in RFC-0120 remains authoritative.

```text
RFC-0120: all decisions remain accepted except mandatory sRGB cardinality
RFC-0122: replaces that rule with zero or one truthful sRGB chunk
```

### RFC-0121

RFC-0121 remains Accepted. Its runtime selection, lifecycle ownership, native
API boundary, job privacy, programmatic composition, and normalization ownership
are unchanged. If this RFC is accepted, the selected adapter may normalize
current untagged output into the new untagged state when every other closed
profile rule is satisfied.

This is not a `stable-diffusion-cpp` exception. The same profile would apply to
every Image Generation adapter.

### Draft PR #746

Draft PR #746 remains evidence while this RFC is reviewed. It is neither
modified nor made a permanent dependency of this decision. Its contribution is
the generic lesson that a valid bounded generated image may have unspecified
color calibration.

## Alternatives Considered

### Keep mandatory sRGB

Rejected. The semantic capability does not promise calibrated color, and the
runtime evidence shows that the assertion cannot always be established without
guessing or broader color-management machinery.

### Always strip all color signaling

Rejected. It would discard truthful sRGB information genuinely supplied by a
runtime.

### Allow arbitrary color profiles

Rejected. It would expand the closed representation, parser and metadata
surface, normalization complexity, and color-management responsibility without
demonstrated need.

### Convert every result to sRGB

Rejected. Conversion requires known source color semantics; unknown RGB values
cannot be deterministically converted into sRGB merely by writing conversion
code. It would also introduce unjustified image/color-processing machinery.

### Choose a different first runtime

Rejected as the architectural correction. The evidence indicates untagged
generated PNGs are not exceptional, and runtime selection should not depend on
incidental color-chunk packaging when the semantic capability does not require
calibrated color. This does not prohibit another runtime later.

## Impact

Acceptance would authorize one narrow later implementation change to the
cluster validator and relevant adapter normalization. It would not change
`ImageGenerationRequest`, `ImageGenerationResult`, routing, remote transport,
operator configuration, CLI, Web UI, filesystem authority, model management,
runtime lifecycle, or dependencies.

## Decision

Pending.
