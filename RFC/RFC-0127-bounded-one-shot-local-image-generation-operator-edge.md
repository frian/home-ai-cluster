# RFC-0127: Bounded One-Shot Local Image Generation Operator Edge

Status: Draft

Date: 2026-09-16

Author: frian

## Summary

This RFC proposes the first complete human Image Generation path as one
bounded architectural unit:

```text
one native loopback POST /v1/image-generation operation
    +
one thin one-shot hac image-generation client
```

The native operation accepts exactly one closed JSON object containing a
bounded textual `instruction`, executes the existing semantic
`ImageGenerationRequest` through ordinary local capability routing, and on
success returns the already cluster-validated PNG bytes as `image/png`. The
client sends one request to the already-running ordinary loopback HAC process
and, when its immediate stdout is non-TTY, writes exactly those bytes to stdout.

This proposal adds neither Image Generation semantics nor a storage, browser,
remote, receiver, runtime-control, or generic binary framework. It projects
the accepted RFC-0120 through RFC-0126 local result. It explicitly preserves
RFC-0059: a physical local Image Generation binding in `hac static-cluster`
does not make Image Generation caller-locally eligible.

## Problem

Accepted RFCs now establish this local execution path:

```text
explicit RFC-0126 local binding
    -> ImageGenerationRequest
    -> ordinary local capability routing
    -> Image Generation execution contract
    -> stable-diffusion.cpp adapter
    -> candidate PNG
    -> cluster-owned validation
    -> ImageGenerationResult(image_bytes, node_id)
```

There is no ordinary human path that submits the accepted semantic request to
a running HAC process and receives its validated PNG. A route alone would add
another programmatic seam; a CLI alone would bypass the existing ordinary
process/client architecture. The missing decision is the small complete
operator edge joining the two.

## Goals

- Provide one instruction-only native local Image Generation operation.
- Provide one one-shot, non-interactive `hac image-generation` client of the
  running ordinary loopback HAC process.
- Project the exact validated PNG without textualization, storage, or a
  generic binary representation.
- Preserve capability-centered local routing and all accepted Image Generation
  semantics.
- Fail before inference when stdout is an interactive terminal.
- Preserve the caller-owned filesystem authority boundary and RFC-0060 timeout
  ownership.
- Apply RFC-0082 confirmed-disconnect cancellation to this new route.

## Non-goals

This RFC does not add remote or receiver Image Generation; static
`image-generation` permission; browser Image Generation; image input, editing,
or multimodal Chat; galleries, history, persistence, output paths, automatic
filenames, temporary files, filesystem APIs, or RFC-0114 workspace authority.

It does not add JSON/base64 image output, multipart, result URLs, generic
Media/Blob/Asset or binary API abstractions, generic streaming, model/runtime
selection, installation/download, lifecycle management, dimensions, aspect
ratio, negative prompts, seeds, sampler, steps, CFG/guidance, style/quality,
multiple candidates, terminal graphics protocols, or interactive Image
Generation.

## Proposal

### One native ordinary route

The ordinary native HAC application surface gains exactly:

```text
POST /v1/image-generation
```

It is neither OpenAI-compatible nor a receiver route, is not part of
`/internal/cluster/request`, and is not a browser-private or remote Image
Generation surface.

Its request body is one closed JSON object:

```json
{"instruction":"<TEXT>"}
```

Extra fields are rejected. `instruction` remains precisely RFC-0120's
non-blank textual instruction with a maximum of 65,536 UTF-8 bytes. There is
no caller capability, model, runtime, dimension, aspect ratio, negative prompt,
seed, sampler, steps, guidance, style, quality, output-path, output-format,
history, or generic-options field. The route constructs the existing semantic
`ImageGenerationRequest` and has fixed semantic capability
`image-generation`.

Under `hac local`, it uses ordinary local capability routing and the existing
local execution path. It must not select `stable-diffusion-cpp`, an adapter by
declaration order, a model, or a runtime. An eligible explicit binding owns the
capability under RFC-0108/RFC-0110. If no eligible local capability exists, the
ordinary no-capability failure boundary applies.

### Success projection and attribution

On successful normalized execution the route returns:

```text
Content-Type: image/png
body: exact ImageGenerationResult.image_bytes
```

The bytes are the already validated still PNG byte sequence. No JSON, base64,
multipart, data URL, result URL, file path, attachment, or generic media/blob
representation is involved. Normal framework headers, including content
length, are implementation details; there is no content negotiation or
output-format request field.

RFC-0120's normalized internal result continues to retain `node_id`. This
first native/CLI projection need not expose it. The raw PNG is not changed to
carry attribution, and no header, JSON metadata, multipart payload, or verbose
CLI mode is required. A projection may expose only its primary semantic result
while the normalized core preserves full attribution; that does not justify a
new observation architecture.

### Static-cluster, remote, and receiver boundaries

RFC-0126 may let a `hac static-cluster` process physically construct a local
Image Generation binding. That execution ownership is not RFC-0059 caller-local
routing permission:

```text
physical local ownership != static caller-local routing permission
```

The route must use the existing caller-local static routing view, not route
directly against the physical `LocalAppComposition`. RFC-0059 does not admit
`image-generation`; therefore an unchanged static-cluster process has no
eligible local Image Generation candidate even when it contains a binding. The
ordinary no-capability outcome is correct. This RFC neither adds the capability
to the static vocabulary nor decides whether a later RFC should do so.

`RemoteTransportRequest`, `RemoteTransportResult`, `InternalClusterRequest`,
`/internal/cluster/request`, receiver routes, static remote declarations,
ordered remote candidates, remote fallback, execution permission/refusal, and
remote-result serialization remain unchanged. The route never attempts remote
Image Generation, and the receiver never gains `/v1/image-generation`.

### Disconnect cancellation

RFC-0082 explicitly excludes future routes until separately added. This RFC
adds `POST /v1/image-generation` to its confirmed-client-disconnect policy.
While HAC routable execution is pending, a confirmed disconnect cancels the
HAC-owned pending task and discards late success or failure. If the terminal
HAC result already won, normal completion wins. There is no retry, fallback,
new candidate, cancellation endpoint, job, polling, or durable state.

This remains HAC-side cancellation only. It does not promise that
stable-diffusion.cpp or `sd-server` stops generating; its native polling and
job mechanics stay adapter-private.

### One-shot client

One installed ordinary command is proposed:

```text
hac image-generation "<INSTRUCTION>"
```

The long root alias remains equivalent under the existing unified command
architecture. The command is one-shot, non-interactive, instruction-only, and
a client of the already-running ordinary loopback HAC process. It neither
constructs a runtime nor loads runtime-config, starts HAC, or contacts
`sd-server` directly.

It accepts exactly one required positional instruction, ordinary help, and
`--timeout-seconds` with RFC-0060's existing finite client-wait semantics. It
does not accept stdin or file input, multiple instructions, interactive mode,
`--json`, `--verbose`, `--output`, model/runtime or generation controls. The
server preserves RFC-0120 semantic validation; an implementation may reject
obviously blank input locally before transmission, as existing thin clients do.

The client uses the fixed ordinary loopback authority and port from RFC-0090,
under RFC-0085's HAC-owned HTTP environment boundary. It adds no configurable
route address, proxy inheritance, external destination discovery, or new
redirect behavior.

### Exact binary stdout and TTY boundary

For a successful completed response, the command writes exactly the PNG
response bytes to its stdout byte stream: no encoding, decoding/re-encoding,
newline, prefix, suffix, status, attribution, decoration, or logging. Stderr
is silent on success. It must establish the expected bounded binary response
before beginning stdout output. The truthful process-boundary guarantee is:

```text
any request/HTTP/response failure detected before stdout emission begins
    -> zero bytes written to stdout

successful complete stdout delivery
    -> exact PNG bytes, byte-for-byte and in order
```

A bounded whole-result buffer is acceptable; RFC-0120's encoded-PNG bound is
approximately 40 MiB. This does not introduce generic streaming.

Once stdout emission has begun, a failure of that sink may leave an
already-written PNG prefix; HAC cannot retract or repair accepted bytes. An
observable stdout-write failure exits non-zero according to ordinary process
behavior and may produce one bounded human-readable stderr error if that stream
remains usable. It authorizes no retry, re-generation, restarted emission,
temporary file, filesystem authority, transactional output abstraction, or
generic streaming architecture.

Before network activity, the client tests its immediate stdout. If it is a TTY,
it fails locally, sends no Image Generation request, invokes no HAC inference,
writes one bounded human-readable failure only to stderr, exits non-zero, and
writes zero stdout bytes. There is no `--force`, `--stdout`, interactive
preview, terminal image protocol, or base64 escape hatch. Pipes and redirected
stdout are non-TTY acceptable immediate sinks; HAC does not recursively inspect
their downstream destinations.

Writing exact bytes to stdout grants HAC no filesystem destination authority.
HAC receives and opens no path, directory, filename, overwrite mode, symlink,
permissions, or temporary destination. Operator shell redirection is outside
HAC ownership and not part of the normalized result. The contract ends at the
bytes HAC writes to stdout; it does not promise byte-preserving behavior from
every shell or version. RFC-0097's Windows installation path makes no broader
PowerShell binary-redirection promise or minimum-version requirement.
Stdout delivery is a byte-stream boundary, not a transactional persistence
guarantee: a pipe, shell redirection target, or downstream process owns its
behavior after accepting bytes.

### Timeout and failure behavior

`--timeout-seconds` remains RFC-0060's caller-owned HTTP waiting bound. It is
not a server, runtime, generation, or cluster-wide deadline and does not
promise downstream termination. A timeout may cause server-side confirmed
disconnect handling, but the caller and server boundaries remain separate.

The route/client reuse existing bounded concepts: invalid CLI shape or TTY
stdout is local failure before request; malformed semantic input is rejected;
no capability, execution permission denial, runtime unavailability, client
timeout, unavailable HAC, and unexpected/invalid native response retain their
ordinary meanings. This RFC creates no Image Generation failure taxonomy.
Existing command conventions may choose strings and exit codes where none is
architecturally necessary. Every failure detected before successful PNG
emission begins writes zero stdout bytes. A stdout-sink failure after emission
begins may leave an unretractable prefix; HAC must never intentionally mix
textual failure output into stdout. Human-readable failures remain on stderr.

## Rationale

The route and CLI belong in one RFC because they are the first useful complete
human Image Generation path. A route-only RFC leaves the operator seam open;
a CLI without a native route cannot respect the existing process/client
architecture. Browser presentation is independently useful but introduces UI
state, accessibility, current-image lifecycle, and separate authority and
cancellation questions.

Raw PNG directly projects accepted semantic image bytes rather than inventing a
text or storage representation. TTY fail-closed avoids unsafe arbitrary binary
terminal output without adding a second presentation mode. Stdout is the
smallest operator edge because it remains outside filesystem destination
authority.

## Alternatives considered

### Browser first

Deferred. It adds presentation state, accessibility/UI work, current-image
lifecycle, and separate cancellation/authority concerns not needed here.

### Native route only

Rejected as the complete next step. It creates a programmatic seam but leaves
the ordinary human workflow external to HAC.

### `--output PATH`

Rejected. It grants filesystem destination authority and creates overwrite,
path, and symlink semantics without need.

### JSON/base64, multipart, or result URL

Rejected. JSON/base64 textualizes and inflates accepted bytes; multipart has
no second required payload; a URL/temporary file requires state, lifetime, and
filesystem decisions.

### Raw stdout on a TTY or an override

Rejected/deferred. Arbitrary potentially large binary output is not a suitable
terminal default, and no demonstrated need justifies an escape hatch.

### Make static Image Generation routable now

Rejected. That changes RFC-0059 caller-local permission and is a separate
routing decision.

## Compatibility and impact

Existing textual commands and requests, HTTP routes, RFC-0059 vocabulary,
receiver and remote transport, and Image Generation core/runtime/configuration
semantics remain unchanged. The only additive operator surface is the native
local route and one one-shot command. Shell-redirection compatibility is not a
cross-platform persistence guarantee.

A later implementation may add only the route, its application composition and
RFC-0082 coverage, the thin client and root dispatch, focused tests, and later
operator documentation/proof. It must not add browser assets, generic binary
infrastructure, route exposure on the receiver, remote transport, filesystem
output, runtime controls, or an Image Generation redesign.

## Proof expectations

Implementation must prove at least:

1. an eligible `hac local` request routes semantically as `image-generation`;
2. success is `image/png` and byte-for-byte validated normalized PNG;
3. no JSON/base64/multipart/path/result URL is involved;
4. non-TTY CLI stdout is exact PNG, with silent successful stderr;
5. TTY stdout fails before HTTP request or adapter invocation;
6. every request/client/server/response failure before stdout emission leaves
   stdout with zero bytes;
7. a simulated stdout sink failure after accepting a prefix causes no retry,
   re-generation, textual stdout contamination, or filesystem fallback;
8. RFC-0060 timeout behavior remains and RFC-0082 covers this route without
   promising `sd-server` termination;
9. a physical static binding remains ineligible under unchanged RFC-0059;
10. no remote route, receiver route, filesystem destination, browser surface,
   generation control, model/runtime choice, or lifecycle behavior appears.

The smallest proof may use an in-process/test adapter with known valid PNG;
RFC-0121 already proves the physical `sd-server` path.

## Open questions

Exact internal response buffering, command module placement, error strings,
and exit-code reuse are implementation details within this contract. Browser
projection, static caller-local permission, output persistence, and remote
Image Generation require separate RFC decisions.

## Decision

Draft.

If accepted, Home AI Cluster will add exactly one bounded local native
`POST /v1/image-generation` projection and one thin one-shot
`hac image-generation` client under the conditions above, while preserving
accepted Image Generation semantics and all static, remote, receiver,
filesystem, and browser boundaries.
