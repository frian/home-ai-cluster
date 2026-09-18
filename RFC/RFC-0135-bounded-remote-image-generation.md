# RFC-0135: Bounded Remote Image Generation

Status: Draft

Date: 2026-09-18

Author: frian

## Summary

This RFC proposes one bounded distribution extension for the existing
engine-independent `image-generation` capability.  A caller may make an
ordinary Image Generation request available to an explicitly declared remote
HAC node through the existing static-cluster routing and receiver protocol.
The selected receiver executes only against its own local Image Generation
composition and returns the already normalized still-PNG result as a bounded
raw `image/png` response.

`image-generation` becomes an accepted *explicit* static capability vocabulary
value for caller-local routing permission and declared remote-node permission.
It is not added to the default static capability set, which remains exactly:

```text
chat
summarize
```

This proposal preserves a critical distinction: local binding capability means
physical execution ownership, while caller-local static capability means
routing permission only.  A caller permission cannot create Image Generation
ownership for a textual runtime or adapter.  The effective caller-local
eligibility is conceptually:

```text
actual physical local execution ownership
∩
caller-local static routing permission
```

The existing `POST /internal/cluster/request` endpoint receives one new closed
`image-generation` request variant.  Existing request kinds retain their JSON
success representations; a successful Image Generation variant returns exact
normalized PNG bytes with `Content-Type: image/png`.  The caller bounds the
decoded candidate body while reading it to 41,943,040 bytes, independently
performs the complete normalized still-PNG validation, applies any requested
exact dimensions, and attributes the accepted result to its selected declared
remote node.  An invalid, oversized, or otherwise ambiguous post-send remote
outcome is terminal and never causes retry, fallback, or local regeneration.

## Context

RFC-0120 deliberately defined `image-generation` as a
distribution-independent semantic capability while authorizing local execution
only.  RFC-0121, RFC-0122, RFC-0126, RFC-0127, RFC-0128, RFC-0129, RFC-0130,
and RFC-0131 establish a bounded local proof: an engine-independent request,
explicit local binding ownership, one stable-diffusion.cpp adapter, complete
cluster-owned still-PNG validation, optional exact dimensions, and existing
CLI, native HTTP, loopback, trusted-LAN, and retained local-composition edges.

Separately, RFC-0012 through RFC-0018 and RFC-0028 establish the static remote
topology, transport, selection, execution, and bounded fallback boundaries.
RFC-0058 and RFC-0059 make static remote and caller-local capabilities
explicit. RFC-0098 through RFC-0106 define execution availability and
permission/refusal behavior; RFC-0108, RFC-0110, and RFC-0119 preserve
execution ownership and capability-coherent adapter contracts. RFC-0109 and
RFC-0111 bound receiver authority. RFC-0112, RFC-0113, and RFC-0132 define the
current retained Configuration projections.

The missing bounded step is therefore:

```text
ordinary image-generation request
  -> existing cluster routing
  -> explicitly declared eligible remote
  -> receiver-local Image Generation execution
  -> bounded normalized PNG returned to caller
```

## Problem

Local Image Generation may already use the cluster-facing semantic request,
but an explicitly declared capable remote cannot participate.  Treating the
binary result as a reason to introduce media infrastructure, a second receiver
route, default remote eligibility, or runtime-aware scheduling would expand
well beyond the demonstrated need.

Without an explicit decision, implementation could also accidentally conflate
caller-local static permission with local adapter ownership.  That would let a
textual runtime appear to own Image Generation merely because the caller has
permitted routing for it, violating RFC-0108 and RFC-0119.

## Goals

- Permit `image-generation` to use existing manually declared static remote
  routing when explicitly authorized.
- Preserve local-first selection, declared remote order, execution permission,
  pre-transmission safe continuation, receiver refusal, and no retry after an
  ambiguous or post-transmission outcome.
- Keep the public Image Generation request vocabulary closed to instruction
  and optional exact width and height.
- Reuse the complete normalized still-PNG contract at both receiver and caller
  sides, with a finite caller read bound.
- Preserve caller-owned remote node attribution and receiver-local execution.
- Represent the new explicit capability in the existing retained local and
  remote-node Configuration projections without adding configuration authority.

## Non-goals

This RFC does not add image input or vision, editing or image-to-image,
multiple candidates, animation, video, audio, JPEG, another output format,
base64, multipart, result URLs, output paths, filesystem saving, object
storage, or generic binary, media, blob, or asset abstractions.

It does not add remote runtime, model, GPU, capability, health, or capacity
facts; model or provider selection; discovery; probing; load balancing,
quality ranking, scheduling, dynamic topology, credentials/authentication
changes, TLS changes, OpenAI-compatible Image Generation, new generation
controls, a health/status protocol, a new receiver endpoint, generic
streaming, remote administration, or configuration synchronization.

It also does not permit retry after ambiguous or post-transmission execution,
or redefine the existing general fallback rules.

## Proposal

### Explicit, nondefault static capability

RFC-0058 and RFC-0059 are extended so `image-generation` is valid wherever
their explicit static capability vocabulary is accepted:

- a caller-local static routing permission; and
- an allowed capability on a manually declared remote node.

It is deliberately absent from the static defaults. Existing declarations and
configurations consequently gain no Image Generation authority. A remote is a
candidate only when that caller explicitly declares its `image-generation`
capability; caller-local static eligibility similarly requires explicit local
permission.

A remote declaration such as this says only that the caller permits that
declared node to be considered for the capability:

```toml
capabilities = ["image-generation"]
```

It does not assert a runtime, model, model presence, GPU, VRAM, backend,
supported dimensions, health, capacity, availability, or credentials. The
receiver independently owns its local composition. There is no probing or
configuration synchronization.

### Ownership remains distinct from permission

RFC-0108 and RFC-0119 remain authoritative. A local binding's capability
states physical execution ownership; a caller-local static capability grants
routing permission only. For Image Generation, a local candidate is eligible
only where both are true:

```text
effective caller-local Image Generation eligibility
  = physical local Image Generation ownership
    ∩ caller-local static Image Generation permission
```

Thus a caller permission with no local Image Generation binding creates no
local candidate. Conversely, a local stable-diffusion.cpp Image Generation
binding can physically exist yet remain caller-locally ineligible when the
caller-local permission excludes `image-generation`. Later implementation must
not extend a historical single-runtime convenience that feeds caller-local
textual capabilities into textual runtime construction to Image Generation.
No new ownership abstraction is introduced by this statement.

### Existing routing and public request authority

Image Generation joins the existing ordinary static-cluster mechanics:
local-first routing, explicit static remote eligibility, declared remote order,
execution-interval and permission semantics, bounded pre-transmission safe
continuation, receiver permission/refusal, and no retry after an ambiguous or
post-transmission failure. It adds no Image Generation-specific algorithm,
ranking, scheduling, model selection, or provider selection.

The normalized `ImageGenerationRequest` may carry ordinary internal
`RequestConstraints` required to participate in that routing. This is internal
normalized-routing data, not public Image Generation vocabulary. Public
operator and HTTP requests remain closed to:

```text
instruction
optional width
optional height
```

They cannot name `local_only`, constraints, a node, remote execution, runtime,
model, or provider. The public `/v1/image-generation` projection must remain
closed and construct any routing constraints server-side. Without ordinary
static remote wiring, existing local behavior remains local. Receiver authority
is local-only regardless of a transported normalized constraint.

Existing `hac image-generation`, native `POST /v1/image-generation`, native
loopback browser Image Generation, and trusted-LAN browser Image Generation
remain the only caller surfaces. They gain neither node chooser nor remote
toggle, runtime/model selector, or provider field.

### One internal endpoint, one closed binary variant

RFC-0014's existing cluster-internal endpoint remains the only endpoint:

```text
POST /internal/cluster/request
```

It gains one closed `kind = "image-generation"` variant containing the
normalized instruction, optional width and height, and internal routing
constraints when required. Unknown fields are invalid. The request remains
JSON, cluster-internal, non-public, non-OpenAI-compatible, and neither
discovery nor management.

Existing kinds retain their successful JSON representations. A successful
Image Generation variant has exactly one success representation:

```text
Content-Type: image/png
body: exact normalized still-PNG bytes
```

This is a closed request-kind-dependent protocol rule, not content negotiation.
The caller knows the kind it sent. The endpoint transports normalized HAC
operations, and the validated PNG is Image Generation's normalized semantic
result; no runtime-specific response format crosses the boundary. No PNG
metadata, node-ID header, JSON sidecar, multipart wrapper, data URL, result
URL, path, object storage, generic blob, asset, or media object is introduced.

`ImageGenerationResult` remains the normalized core result containing
`image_bytes` and `node_id`; the wire carries only `image_bytes`.

### Bounded remote result acceptance and attribution

The exact maximum accepted encoded PNG body is **41,943,040 bytes**
(`40 * 1024 * 1024`). The caller-side HTTP transport must enforce this bound
while reading the successful response, so bytes presented as a candidate
normalized PNG never exceed the bound. `Content-Length` may reject early but
is not proof: it can be absent or misleading. When content coding applies, the
bound is on decoded entity bytes presented to HAC validation, not merely
compressed wire bytes. Chunk sizes and HTTP client APIs remain implementation
details. This is bounded whole-result reading, not streaming Image Generation.

The successful response must identify `image/png`. A non-PNG successful media
type is invalid. The caller independently applies the complete existing
normalized still-PNG validation, including the encoded-size bound, signature,
complete structure and end-of-input, accepted chunks/profile, CRC/decode
checks, bit-depth and color-type rules, RFC-0122 color signaling,
non-animation/non-interlace requirements, global geometry and decoded-resource
bounds, and every other normalized invariant. When dimensions were requested,
the caller also verifies exact IHDR equality under RFC-0131. There is no
simplified remote validator.

The receiver's validation does not establish network-result trust. This follows
the existing remote pattern: Classify checks requested labels and
source-grounded Chat checks source provenance. Image Generation independently
checks its normalized PNG result.

The caller already owns the selected declaration and its node identity. After
acceptance, it constructs or rewrites `ImageGenerationResult.node_id` to that
selected declared remote node. The receiver does not assert a trusted identity
in the PNG or an HTTP header.

After transmission may have occurred, a body that is oversized, absent,
truncated, wrong-media, invalid, unsupported, decode- or CRC-failing,
color-invalid, geometrically invalid, dimension-mismatched, or otherwise
ambiguous is terminal. Response read failure is terminal too. HAC must not
retry another node or locally regenerate, because the remote execution may
already have happened.

### Receiver-local execution

The receiver's one new accepted internal kind follows this bounded path:

```text
/internal/cluster/request
  -> closed image-generation envelope
  -> existing receiver execution permission
  -> receiver-local composition only
  -> eligible local Image Generation binding
  -> Image Generation execution contract
  -> core normalized PNG validation
  -> raw image/png success
```

The receiver never routes onward, selects a remote, selects a runtime or model
from request data, discovers Image Generation, synchronizes configuration, or
exposes a public Image Generation route merely because it accepts the internal
kind. Existing receiver permission and refusal remain authoritative; this RFC
creates no Image Generation-specific permission architecture.

### Retained Configuration and browser projection

Retained caller-local `local_capabilities` may explicitly contain
`image-generation`; this remains permission only and does not create or
configure RFC-0128's separate Image Generation companion. Retained remote-node
declarations may explicitly contain the same capability, with no added remote
facts.

RFC-0132's complete native-loopback Configuration facade is correspondingly
extended in both existing capability projections: the Local section's
caller-local routing capabilities and each Remote node section's
caller-declared allowed capabilities. This is representation of retained
authority only. It adds no runtime ownership, remote administration, probing,
provider selection, live reconfiguration, Configuration to trusted LAN, or
Configuration to receivers.

RFC-0130's trusted-LAN Image Generation surface continues to delegate to the
owner's ordinary routing truth. Therefore an instruction submitted there may
reach an explicitly declared eligible Image Generation remote. The LAN browser
still cannot declare, choose, mutate, or inspect topology; no additional
authorization checkbox is introduced.

### Disconnect and compatibility

RFC-0082 continues to own cancellation. One foreground caller operation spans
local routing, optional remote transmission, remote wait, bounded body read,
caller validation, and final result. If the originating client disconnect wins,
HAC cancels pending owned work and discards late results or failures; it does
not retry or fall back. Receiver disconnect semantics are unchanged. No promise
is made to stop already transmitted work, `sd-server`, GPU activity, or a
runtime; no cancellation endpoint, jobs, polling, or durable task is added.

Existing configurations and declarations remain valid. Because the capability
is nondefault, old local permissions and remote declarations retain their prior
routing behavior. Ordinary non-static local Image Generation is unchanged. A
physical local Image Generation companion without explicit static caller-local
permission remains caller-locally ineligible. Existing textual ownership and
existing JSON remote operations remain unchanged and wire-compatible.

## Rationale

This is the smallest extension that lets the cluster, rather than a caller,
choose within explicit operator-owned Image Generation boundaries. It retains
the project’s capability-centered, local-first, static, deterministic model
without promoting a binary result into generic media infrastructure.

Raw PNG is simpler and more truthful than an envelope: it is already the
normalized semantic result. Request kind fixes the success representation, so
there is no negotiation ambiguity. A finite read bound and independent caller
validation prevent a declared remote from forcing unbounded buffering or from
turning receiver validation into a transitive trust assumption. Preserving the
existing terminal post-send rule avoids double execution, which remains more
important than a speculative second attempt for a large result.

Keeping permission separate from ownership prevents static topology choices
from silently changing what a local adapter can execute. That preserves
capability-coherent execution while allowing existing routing to decide only
among real, explicitly permitted candidates.

## Alternatives considered

### Dedicated internal Image Generation endpoint

Rejected. The established normalized execution endpoint already carries
closed operation variants. A second receiver route expands route authority and
protocol surface without a demonstrated need.

### Base64 in JSON or multipart

Rejected. Base64 creates a larger second representation; multipart adds a
container and metadata semantics. Neither improves the normalized PNG result.

### Result URL, object storage, or temporary file

Rejected. These introduce lifecycle, storage, filesystem, and authority
decisions outside one completed bounded result.

### Generic media/blob abstraction

Rejected. One demonstrated binary capability is insufficient reason to invent
a cross-capability abstraction.

### Default `image-generation` static eligibility

Rejected. It would give old declarations new local or remote routing authority
without an operator’s explicit choice.

### Permission creates local ownership

Rejected. It directly violates RFC-0108 and RFC-0119’s ownership boundary.

## Trade-offs

Remote Image Generation introduces bounded binary transport and duplicate
validation work. That cost is deliberate: the result has a finite accepted
size, the caller must not trust a remote response merely because a receiver
validated it, and the alternative would be broader storage or media design.
The static declaration remains intentionally less convenient than discovery or
scheduling, but keeps the user’s trust and privacy boundary explicit.

## Impact and amendments

This Draft explicitly amends rather than rewrites accepted history:

- RFC-0058 and RFC-0059 gain `image-generation` as an explicit, nondefault
  static capability value.
- RFC-0013 and RFC-0014 gain this closed internal request kind and its
  request-kind-dependent raw-PNG success representation.
- RFC-0120’s local-only distribution scope is extended to this bounded remote
  transport path.
- RFC-0127’s prior no-remote native Image Generation boundary is extended for
  ordinary server-side routing without changing its public request shape.
- RFC-0128’s previous exclusion of static Image Generation permission is
  superseded only by the permission/ownership rule here.
- RFC-0131’s remote Image Generation exclusion is lifted while its exact
  geometry contract remains mandatory at receiver and caller validation.
- RFC-0132’s local and remote capability projections gain this explicit value.

It remains compatible with RFC-0108 ownership, RFC-0109 receiver authority,
RFC-0119 execution contracts, and RFC-0130’s trusted-LAN authority. After a
future acceptance, implementation may make the smallest corresponding core,
transport, receiver, retained-configuration, loopback Configuration, and
focused test/documentation changes. This Draft itself authorizes no production
implementation, migration, dependency, or retained-storage-format expansion.

## Implementation proof expectations

A later implementation should demonstrate that:

1. `image-generation` is explicit and nondefault, and permission never creates
   physical Image Generation ownership;
2. local eligibility is physical ownership intersected with caller permission,
   while declared eligible remotes use existing routing;
3. public Image Generation remains closed, the internal envelope has exactly
   one closed variant, and receivers execute it locally only;
4. Image Generation success is raw `image/png`, bounded during decoded-body
   read to 41,943,040 bytes, completely revalidated by the caller, and checked
   for requested exact geometry;
5. invalid, oversized, wrong-media, or ambiguous remote outcomes cannot cause
   a second execution attempt, and caller-owned node attribution is retained;
6. existing JSON kinds remain wire-compatible;
7. retained local and remote capability validation and both native-loopback
   Configuration projections accept explicit `image-generation`;
8. existing CLI, native, loopback, and trusted-LAN caller surfaces gain no node
   selection while being able to use accepted remote routing;
9. old configurations and declarations retain their prior behavior; and
10. disconnect during remote execution or bounded reading cannot cause retry.

## Open questions

No architectural blocker remains within this proposal. Private Pydantic class
names, helper placement, HTTP streaming method and chunk size, and browser
control layout remain implementation details.

## Decision

Pending.
