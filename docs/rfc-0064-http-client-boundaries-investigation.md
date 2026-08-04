# RFC-0064 HTTP Client Boundaries Investigation

Status: Complete

## Question

> Can the repository's existing Python and HTTP-client stack implement the
> caller-local public-destination invariant and finite retrieval bounds required
> by Draft RFC-0064 without a new dependency or an unsafe
> validation-to-connect gap?

This documentation-only investigation records repository facts, official-library
facts, and controlled local observations. It does not authorize retrieval,
change Draft RFC-0064, or establish an implementation contract.

## Current Repository Baseline

The tracked project dependency is HTTPX >=0.28.0; the checkout used for these
observations resolves HTTPX 0.28.1, httpcore 1.0.9, and Python 3.13.1. No lock
file is tracked. The pre-existing untracked uv.lock was not used or changed.

The ordinary chat, summarize, and classify native commands each create a
one-shot HTTPX Client with a scalar 120.0-second timeout and
follow_redirects=False. RFC-0060 establishes that scalar as pool, connect,
write, and read inactivity limits, not a total command deadline. Current
ordinary clients safely map HTTPX connection, timeout, and request exceptions
without exposing the underlying detail.

The current summarize command selects exactly one of --text, --file, or stdin,
constructs SummarizeRequest(text=...), and POSTs only text to the fixed native
endpoint. The current internal remote summarize envelope likewise carries only
normalized text and constraints. Existing tests use HTTPX MockTransport and
ASGITransport extensively; those transports prove request and failure boundaries
without opening a socket. They do not expose DNS selection or a connected peer.

Draft RFC-0064 proposes caller-local acquisition before that unchanged text-only
path. It requires a stronger public-destination invariant than existing trusted
home-LAN remote transport needs.

## Existing HTTP Client Behavior

### Repository fact

HTTPX is the only HTTP client dependency. Existing production calls use Client
or AsyncClient. They do not configure trust_env, cookies, authentication,
headers, limits, or a custom transport. The current explicit
follow_redirects=False proves that redirects are an ordinary HTTPX client option,
but does not establish a retrieval-safe client configuration.

### Official-library facts

HTTPX documents trust_env=True by default. Environment variables, including
HTTP_PROXY, HTTPS_PROXY, and ALL_PROXY, are used unless a Client is constructed
with trust_env=False. See [HTTPX environment variables](https://www.python-httpx.org/environment_variables/)
and the [HTTPX API reference](https://www.python-httpx.org/api/).

HTTPX Client defaults include follow_redirects=False, trust_env=True, a five
second scalar timeout, connection pooling, and a client-local cookie jar. The
API accepts follow_redirects=False, trust_env=False, headers, auth, cookies,
limits, and a transport. A fresh isolated Client can therefore disable
environment inheritance and redirects, provide no auth or cookies, set fixed
headers, and be closed after the one request. There is no .netrc option in the
documented Client constructor; unlike Requests, HTTPX does not document .netrc
credential discovery. A direct search of the installed HTTPX 0.28.1 and
httpcore 1.0.9 packages found no netrc reference. A focused isolated-client
test should still protect that boundary before implementation.

HTTPX documents stream() with iter_bytes() for content-decoded chunks and
iter_raw() for undecoded wire chunks. Its documentation says gzip and deflate
are automatically decoded for ordinary content access and identifies iter_raw()
as the way to avoid HTTP content decoding. It also exposes
response.num_bytes_downloaded for raw download progress. See the [HTTPX
quickstart](https://www.python-httpx.org/quickstart/) and [client
documentation](https://www.python-httpx.org/advanced/clients/).

### Controlled observations

A loopback-only HTTP/1.1 server returned a 100-byte gzip body representing
18,432 decoded bytes. With Client(trust_env=False, follow_redirects=False):

* iter_bytes() delivered 18,432 decoded bytes;
* response.num_bytes_downloaded reported 100;
* iter_raw() delivered 100 encoded bytes.

A second loopback-only response was 1,051 gzip bytes representing 1,048,576
plain bytes. The first iter_bytes() chunk was the full 1,048,576 bytes, while
response.num_bytes_downloaded was 1,051. The installed HTTPX GZipDecoder calls
zlib.decompressobj().decompress(data) without a caller-supplied output limit.

Therefore an application can count both raw and decoded totals, but a decoded
limit checked after each iter_bytes() chunk does not prevent one compressed input
chunk from allocating or emitting a larger decoded chunk first. HTTPX alone does
not make a strict decoded/decompressed resource limit safe for accepted content
encodings.

A MockTransport observation found that HTTPX 0.28.1 sends
Accept-Encoding: gzip, deflate and User-Agent: python-httpx/0.28.1 by default.
Supplying fixed headers replaced them with Accept-Encoding: identity and the
chosen User-Agent. This is useful evidence for an isolated future client, not a
user-facing change.

## DNS Resolution and Connected-Peer Evidence

### What the documented high-level client provides

HTTPX accepts a URL hostname, but its documented Client and HTTPTransport
constructors expose no resolved-address list, selected peer address,
prevalidated-address connector, original-host/SNI override, or DNS-pinning
argument. The observed HTTPTransport signature has proxy, local_address,
retries, socket_options, and limits, but no resolver, network-backend, or
destination-address parameter. HTTPX's documented custom transport seam
accepts a transport object; it does not describe a supported public API for
controlling one hostname connection while preserving HTTP Host and HTTPS SNI.

These facts apply equally to HTTP and HTTPS, IPv4 and IPv6: the high-level URL
path delegates hostname resolution and address selection beneath the public
Client surface. HTTPS additionally needs the hostname for certificate and SNI
semantics, so replacing a hostname with a prevalidated numeric URL is not an
equivalent general hostname solution.

### Controlled observation and its limitation

For one loopback HTTP/1.1 response, response.extensions contained a
network_stream object. Calling its server_addr extra-info before consuming the
body returned the loopback peer tuple. This is not a documented HTTPX response
contract, was available only after connection, and became unusable after the
server closed the socket. It cannot establish a pre-connect policy or a stable
cross-version/cross-protocol enforcement mechanism.

A request wrapper or ordinary custom transport also receives control only at a
layer that would need to reproduce or replace the connection behavior to choose
the address. Validating socket.getaddrinfo results before calling Client.get()
has a time-of-check/time-of-use gap: HTTPX can resolve again or select another
answer. Validating one answer is weaker still. Connection-pool reuse would
further make an address assertion depend on a previous connection unless the
retrieval client is one-shot and closed.

### Finding

The existing documented high-level HTTPX stack cannot enforce this required
invariant for hostnames:

> A validated hostname must not cause Home AI Cluster to connect to a
> non-public destination.

Doing so needs a deliberately designed low-level connection/resolution seam or
substantial custom networking, plus HTTPS host/SNI and pool semantics. This
investigation found no small documented HTTPX mechanism that proves the
invariant without that work.

For a literal IP URL, there is no hostname lookup or validation-to-connect
resolution change. With trust_env=False, no explicit proxy, one fresh Client,
and no redirect, the URL's public literal is the direct destination requested by
the high-level client. This is the only narrowly evidenced form that avoids the
hostname gap; HTTPS remains usable only when the server certificate is valid for
that IP literal.

## Public Address Classification

Python 3.13's ipaddress documentation defines is_global using the IANA special
registries, notes 3.13 classification corrections, and states that IPv4-mapped
IPv6 inherits the underlying IPv4 classification. It also documents the special
case that 100.64.0.0/10 is neither private nor global. See [Python 3.13
ipaddress](https://docs.python.org/3.13/library/ipaddress.html).

The controlled Python 3.13.1 classification exercise found:

| Class | Representative result |
| --- | --- |
| Public unicast | 8.8.8.8 and 2001:4860:4860::8888: global |
| Loopback/private/link-local/unspecified | not global |
| Reserved/documentation | not global |
| Shared 100.64.0.0/10 | neither private nor global |
| IPv4-mapped IPv6 | follows its embedded IPv4 value |
| 64:ff9b:1::/48 and 2002::/16 | not global in 3.13 |
| Multicast | 224.0.0.1 and ff00::1 reported global |

Consequently address.is_global alone is not sufficient for RFC-0064's stated
policy because it admits multicast. A simple standard-library rule is sufficient
without a custom range table: require is_global and reject is_multicast. The
future implementation must pin its supported Python semantics with tests,
including the representative classes above, because the standard library changed
is_private/is_global classifications in Python 3.13.

This rule classifies a literal. It does not solve hostname resolution or confirm
the connected peer.

## Streaming, Decompression, and Size Bounds

HTTPX can separately observe raw bytes through iter_raw(), decoded bytes through
iter_bytes(), and decoded text through iter_text(). HTTPX's per-operation read
timeout bounds socket inactivity while waiting for body data; it does not bound
total body size or total wall-clock duration. Response headers arrive before the
streaming iterator begins, so a Client request/stream call can classify status
and media headers before accepting a body.

The evidence supports these enforceable boundaries only when response content
encoding is absent or identity:

1. use a fresh isolated Client with a fixed Accept-Encoding: identity header;
2. reject any response Content-Encoding other than absent or identity before
   reading its body;
3. use iter_raw(), stop once 65,537 bytes are observed, and classify it as too
   large;
4. strict-decode the at-most-65,536 retained bytes as UTF-8; and
5. pass that same bounded text to the existing SummarizeRequest validation.

Under that narrowed content rule, wire bytes, decoded bytes, strict UTF-8 bytes,
and the final source share the honest 65,536-byte maximum. The application must
not trust Content-Length as enforcement.

The existing stack does not provide an equally safe strict decoded-byte bound
while accepting gzip, deflate, or other content encoding. Neither a smaller
header nor an after-chunk counter fixes the observed decompression-before-limit
behavior. Compressed content must remain out of scope unless a later RFC accepts
a bounded streaming decompressor or different evidence.

## Timeout Ownership

HTTPX documents a five-second default network-inactivity timeout and a Timeout
object with distinct connect, read, write, and pool values. A scalar populates
all four. Connect includes establishing a connection; read is an inactivity
limit while receiving response data; write applies to sending request data; pool
limits waiting for an available pooled connection. See [HTTPX
timeouts](https://www.python-httpx.org/advanced/timeouts/).

HTTPX has no documented total-operation timeout. Combining five-second connect
and read limits does not create a 15-second total: a server can make progress
before each read timeout indefinitely. A synchronous monotonic check around
stream iteration also cannot interrupt a currently blocked call. Therefore a
strict total retrieval deadline would need an explicit implementation mechanism,
not an HTTPX Timeout value.

The accepted 120-second ordinary native inference timeout remains separate. It
waits for the local cluster endpoint after retrieval, while a future retrieval
client would own its own short fixed limits and its own normalized failures.

## Fixed Request Configuration

A future retrieval client must be fresh and isolated for one request, then
closed. It should use trust_env=False; follow_redirects=False; no proxy; no auth;
an empty cookie jar; no caller headers; no retries; and no cross-invocation
connection reuse. A fresh one-request Client has no prior response cookie state;
the future implementation should also test that it neither sends nor retains
cookies.

The smallest observable header policy is fixed Accept-Encoding: identity and a
fixed non-identifying User-Agent. Identity is needed to make the single
65,536-byte raw/text limit honest. The User-Agent wording remains an RFC
presentation/privacy choice; the experiment only shows that HTTPX otherwise
sends a version-identifying default. HTTP-required Host behavior remains client
owned. No browser state, .netrc behavior, or automatic proxy behavior may be
assumed from ordinary client defaults.

These are client configuration choices, except the decision to allow only
identity content and to avoid connection reuse: those are required RFC boundary
choices because they define security and resource semantics.

## Candidate Numeric Limits

The recorded evidence supports these intentionally simple values for a narrowed
literal-IP, identity-only first increment:

| Bound | Recommendation | Evidence and trade-off |
| --- | --- | --- |
| Connect timeout | 5 seconds | Matches HTTPX's documented default; a public endpoint that cannot connect within this short explicit operation fails rather than holding the command. |
| Header/read inactivity timeout | 5 seconds | Matches the documented default. It allows a slow server only while it makes progress; it does not permit an indefinitely silent body. |
| Encoded, decoded, strict UTF-8, and final source bytes | 65,536 | For identity text/plain these are the same representation; a larger body is unnecessary for the existing summarize contract. |
| Strict total retrieval timeout | No current enforceable value | HTTPX has no total timeout, and a synchronous after-the-fact timer is not strict. A 15-second product target is reasonable only after a separate implementation mechanism is evidenced. |

Five seconds is deliberately much shorter than the accepted 120-second local
inference wait. This is an explicit Internet input-acquisition bound, not a
model-execution allowance. It may reject some slow public servers; that is the
trade-off for a boring first increment.

## Options

### A — Retain arbitrary public hostnames with existing high-level HTTPX

Rejected. Pre-validating DNS answers does not control the address HTTPX
connects, and the documented client has no connected-peer enforcement hook.

### B — Add a narrow low-level transport/network backend

Not selected by this investigation. It might preserve hostname, HTTPS SNI, and
the invariant, but the evidence did not establish a small supported seam. It
would need an explicit design and proof across IPv4, IPv6, TLS, failures, and
pool reuse before being described as narrow.

### C — Narrow the contract to literal public IP URLs and identity text

Selected. Literal public IPs eliminate DNS selection and rebinding. Rejecting
content encoding makes the existing streaming API's raw byte limit equal the
decoded and final source limit. This is narrower and less convenient, but is the
only direction the current evidence supports without custom networking or a new
dependency.

### D — Keep retrieval operator-owned outside Home AI Cluster

Still the safest general-web workflow. It remains the fallback if literal-IP
URLs do not provide enough user value.

## Decision

**Outcome C — Contract must be narrowed.**

The existing stack cannot enforce the connected-public-peer invariant for
hostnames. It can support a strictly smaller first contract: one public literal
IPv4 or IPv6 HTTP/HTTPS URL, no redirects, proxy environment disabled, no
credentials or cookies, identity-only text/plain, a fresh closed Client, a
5-second connect/read boundary, and a 65,536-byte raw/final source boundary.

This investigation does not authorize an implementation or accept any RFC
change.

## Required RFC-0064 Corrections

Before Draft RFC-0064 can be accepted, it should:

1. replace hostname support with literal public IPv4/IPv6 URL support, or defer
   retrieval entirely until a separately evidenced hostname-safe transport is
   accepted;
2. state the standard-library classification rule as is_global and not
   is_multicast, with Python-version regression tests, rather than is_global
   alone;
3. require a fresh client with trust_env=False, follow_redirects=False, no
   explicit proxy/auth/cookies/retries, and no cross-invocation pooling;
4. fix Accept-Encoding: identity and reject every non-identity Content-Encoding
   response before body consumption;
5. define a 65,536-byte raw, decoded, strict UTF-8, and final-source maximum;
6. use 5-second connect and read inactivity limits, separately from the
   accepted 120-second inference timeout; and
7. remove any promise of a strict total retrieval timeout until an explicit,
   evidenced implementation mechanism is accepted.

The existing source URL presentation, caller-local ownership, text-only remote
transport, and no-browser boundary remain compatible with this correction.

## Deferred Work

This investigation does not authorize hostname retrieval, DNS pinning,
connected-peer transport hooks, proxy support, compression support, HTML,
redirects, total-deadline machinery, caching, cookies, credentials, retries,
background work, browser changes, a generic fetch/retrieval capability, search,
tools, agents, remote-node Internet access, source-code changes, tests, or
dependencies.
