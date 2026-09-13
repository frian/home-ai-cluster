# stable-diffusion.cpp Image Generation Proof

Status: Successful

Date: 2026-09-13

## Purpose

This record retains privacy-safe evidence from one real local implementation
proof of RFC-0121 through the accepted RFC-0119/RFC-0120/RFC-0122 boundaries.
It records one bounded composition, not an ordinary Image Generation product
surface or a general claim about this runtime.

## Proof basis

The proof used HAC revision
`ba1e27c527e7140cc376d4a05ea672e93b0c56c0` and
stable-diffusion.cpp revision
`7f410a3793c5bba8eb198e962ce7a3d6095f9d89`. An operator-managed CPU-only
`sd-server`, explicitly listening on loopback, used
`v1-5-pruned-emaonly.safetensors` (SHA-256
`6ce0161689b3853acaa03779ec93eafe75a02f4ced659bee03f50797806fa2fa`).

The operator started the runtime outside HAC. HAC used ordinary programmatic
local routing through an explicit `image-generation` local capability binding.

## Observed positive result

Exactly one real request succeeded through ordinary local HAC
routing/composition. The bounded proof composition attributed the result to
`image-node`; that identifier is not a stable product identity. The adapter
identity was `stable-diffusion-cpp`.

The result contained 656257 PNG bytes with SHA-256
`682498a08e2129b41a70af73389a1fd95552bd0a2049500aa963840acccd6900`.
The final bytes passed cluster-owned still-PNG validation. HAC required no
filesystem output path, and runtime generation metadata did not survive
normalization.

## Honest color-signaling evidence

This concrete runtime/model result had the normalized chunk sequence:

```text
IHDR
IDAT
IEND
```

```text
sRGB absent
```

The real runtime produced an ordinary untagged PNG. Adapter normalization
preserved that honest untagged state; HAC did not manufacture `sRGB`. The
RFC-0122 validator accepted this closed representation. This is real evidence
for RFC-0122's two-state color-signaling decision, not a claim that all
stable-diffusion.cpp output is untagged.

## Runtime-unavailable result

After the operator-managed runtime was stopped, the same local execution path
failed as `RuntimeConnectionUnavailableBeforeRequestError` with the normalized
message `Runtime connection unavailable before request transmission`. No
transport-native detail escaped.

## Authority boundary

The operator owns runtime lifecycle, model file, device/backend, and storage.
The adapter owns native protocol mechanics and bounded normalization. HAC core
owns final still-PNG validation. HAC acquired no model-management,
runtime-management, filesystem, or image-processing authority.

## Privacy boundary

This record omits hostname, username, personal paths, full prompt, and raw
runtime transcript/logs. The model filename, upstream revision, cryptographic
hashes, result size, PNG chunk vocabulary, and normalized HAC failure are
retained as proof evidence rather than personal-environment identity.

## Scope preserved

This proof does not establish or add retained image runtime configuration, CLI
Image Generation, a Web UI, remote Image Generation, receiver transport,
runtime/model lifecycle management, filesystem output, generic media/image
processing, generic color management, or runtime-selection architecture.
