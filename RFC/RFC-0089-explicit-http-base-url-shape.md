# RFC-0089: Explicit HTTP Base URL Shape

Status: Accepted

Date: 2026-08-26

Author: frian

## Summary

Home AI Cluster should define the explicitly supplied HTTP base URLs used by
ordinary static remote declarations and llama-server local composition as HTTP
origins, not arbitrary resource URLs.

An accepted value would contain only a scheme, host, and optional explicit
port. It would contain no user information, query, fragment, or non-root path.
An empty path and `/` would remain equivalent inputs and normalize to one base
URL without a trailing slash.

For declared remotes, the origin identifies the receiving Home AI Cluster
application. The cluster-owned paths remain exactly:

```text
POST /internal/cluster/request
GET  /internal/cluster/status
```

For explicit llama-server composition, the origin identifies the existing
operator-owned loopback HTTP runtime. Existing scheme, loopback, lifecycle,
privacy, and engine-independence boundaries remain unchanged.

This is a validation tightening and semantic clarification. It adds no new
transport, configuration, authentication, or network authority. It does not
implement the decision.

## Problem

Accepted RFCs define `remote_base_url` and an explicit llama-server base URL,
but do not close every structural URL component. Current validation checks the
scheme and host, then removes trailing `/` characters. It can therefore accept
values containing user information, a non-root path, a query, or a fragment.

Remote request and status URLs are currently derived by textual concatenation:

```text
<transport_address>/internal/cluster/request
<transport_address>/internal/cluster/status
```

A query or fragment can make the appended text ineffective as an HTTP path. A
configured path can also appear to relocate or prefix the fixed internal
endpoints, although no accepted RFC defines such mounting behavior.

The local llama-server validator has the same unspecified component shape. It
requires absolute loopback `http`, but does not explicitly decide whether user
information, paths, queries, or fragments belong in the process-local runtime
configuration.

Implementation should not silently choose whether these components are
supported. The configuration meaning must be explicit first.

## Goals

- Define one narrow component shape for the two existing explicit HTTP base-URL
  boundaries.
- Preserve accepted remote `http` and `https` schemes and trusted-LAN scope.
- Preserve llama-server's loopback-only `http` scope.
- Preserve the common forms with either an empty path or `/`.
- Keep cluster-owned internal endpoint paths fixed and unprefixed.
- Prevent configuration values from becoming accidental credential or token
  channels.
- Authorize only a later small validation, normalization, endpoint-construction,
  test, and necessary documentation change.

## Non-goals

This RFC does not add or define authentication, authorization, credentials,
tokens, request headers, TLS policy, certificate configuration, proxies, public
Internet support, reverse-proxy mounting, configurable API prefixes, path-based
tenant routing, service discovery, DNS policy, URL rewriting, redirects, new
remote protocols, new runtime adapters, or Ollama base-URL configuration.

It does not change request, result, status, routing, fallback, capability,
attribution, persistence, logging, runtime lifecycle, listener exposure, or
privacy contracts.

It does not establish a generic URL type, configuration framework, validator
hierarchy, or shared `BaseUrl` subsystem. A later implementation may share one
small pure helper only if concrete code evidence makes that the smallest
solution.

## Existing Accepted Boundaries

This RFC preserves rather than reopens these decisions:

- RFC-0014 owns `POST /internal/cluster/request` as the normalized internal
  request endpoint.
- RFC-0041 owns `GET /internal/cluster/status` as the normalized read-only
  internal status endpoint.
- RFC-0038 defines an explicitly supplied trusted-LAN remote base URL and keeps
  the calling endpoint loopback-only.
- RFC-0039 permits an operator-owned static declaration to retain that URL but
  prohibits credentials, tokens, authorization headers, usernames, passwords,
  private keys, and arbitrary environment values.
- RFC-0040 applies one common validation and normalization rule to every
  declared remote base URL and rejects duplicate normalized URLs.
- RFC-0042 defines llama-server's explicit base URL as absolute loopback
  `http`, with local validation and no network probe.
- RFC-0043 and RFC-0044 reuse that same local composition boundary for static
  startup and status without changing cluster-facing contracts.
- RFC-0074 retains the same llama-server boundary in an explicitly selected,
  process-local runtime-composition file that does not support secrets or
  credentials.

None of those RFCs accepts an arbitrary remote path prefix, query, fragment, or
secret-bearing URL component.

## Proposal

### Base URLs identify origins

For the existing boundaries in scope, a Home AI Cluster configuration value
described as an HTTP base URL identifies one HTTP origin.

Its complete allowed component shape is:

```text
scheme://host[:port]
```

The scheme and host rules remain boundary-specific. An explicit port is
optional. The authority contains no username, password, or other user
information. The URL contains no query or fragment delimiter and no path other
than an empty path or exactly `/`.

An empty path and `/` are equivalent input forms. Both normalize to the same
canonical base URL without a trailing slash. This RFC introduces no further
equivalence rule for omitted versus explicit default ports or other incidental
URL spelling details.

### Remote Home AI Cluster base URLs

An ordinary static remote base URL continues to:

- be absolute;
- use `http` or `https`;
- identify an explicitly declared trusted-LAN receiving application; and
- remain operator-owned topology data under RFC-0038 through RFC-0041.

Accepted examples include:

```text
http://192.0.2.10:8000
http://192.0.2.10:8000/
https://remote.example:8443
https://remote.example:8443/
```

The first two inputs normalize identically. The last two inputs normalize
identically.

Rejected examples include:

```text
http://user@remote.example:8000
http://user:secret@remote.example:8000
http://remote.example:8000/base
http://remote.example:8000?token=x
http://remote.example:8000/#fragment
```

The declared origin does not relocate, prefix, or namespace cluster-owned
endpoints. In particular, this RFC does not authorize a receiver mounted at:

```text
http://host:8000/home-ai-cluster
```

Supporting a prefix-mounted receiving application would require a separate
architectural decision based on a demonstrated need.

### Cluster-owned endpoint construction

The internal request and status paths remain exactly:

```text
/internal/cluster/request
/internal/cluster/status
```

A later implementation must construct those endpoints from the validated
origin and fixed cluster-owned path structurally. Endpoint meaning must not
depend on textual concatenation with arbitrary configured URL components.

This RFC decides the semantic result, not the Python helper, URL class, or
library API used to produce it.

### Local llama-server base URLs

An explicitly supplied llama-server base URL similarly identifies the HTTP
origin of the operator-owned local runtime. RFC-0042 and RFC-0074 remain
authoritative:

- the scheme is exactly `http`;
- the host is loopback under the existing accepted host rule;
- validation performs no network probe;
- runtime lifecycle remains operator-owned; and
- the URL remains process-local and runtime-specific.

Accepted examples include:

```text
http://127.0.0.1:8080
http://127.0.0.1:8080/
http://localhost:8080
http://[::1]:8080
```

Equivalent local forms containing user information, a non-root path, a query,
or a fragment are rejected. For example:

```text
http://user@127.0.0.1:8080
http://user:secret@127.0.0.1:8080
http://127.0.0.1:8080/base
http://127.0.0.1:8080?token=x
http://127.0.0.1:8080/#fragment
```

This decision does not broaden Ollama configuration. Existing default Ollama
construction remains unchanged because it is not part of the shared explicit
URL input boundary addressed here.

## Normalization and Compatibility

The commonly documented forms remain valid:

```text
http://host:port
http://host:port/
```

They normalize to the same base URL without a trailing slash. Existing remote
duplicate detection continues to operate on normalized values.

Configurations containing user information, a non-root path, a query, or a
fragment become invalid. This is intentional validation tightening: those
components were never part of the documented configuration shape, can conflict
with fixed endpoint ownership, and can violate the accepted no-credential
boundary.

This RFC does not claim compatibility for arbitrary path-prefix configurations
merely because current syntax-level validation may accept them.

Invalid values fail locally before application binding or status observation,
following the existing boundary's operation order. Validation remains
deterministic and network-free. Operator-facing failures remain compact and
privacy-safe and must not expose raw parsing, transport, or runtime details.

## Privacy and Security Boundary

Rejecting URL user information and queries prevents these configuration
surfaces from becoming accidental channels for usernames, passwords, bearer
values, or other secrets. Rejecting fragments and non-root paths also keeps the
declared destination and fixed endpoint meaning inspectable.

This validation does not make remote HTTP Internet-secure. It adds no
authentication, encryption requirement, certificate policy, DNS protection,
proxy policy, or public-network authority. Existing trusted-LAN remote and
loopback local boundaries remain authoritative.

## Rationale

Origin-only base URLs match every repository example found for these accepted
configuration boundaries and match the fixed-path ownership already defined by
RFC-0014 and RFC-0041.

The rule is small and explainable: configuration chooses the HTTP origin; Home
AI Cluster or the runtime adapter owns the request path. It removes ambiguous
URL semantics without adding a prefix-routing feature, secret format, or new
abstraction.

Structural endpoint construction makes that ownership real in implementation
while leaving the concrete standard-library or HTTP-client mechanism open.

## Alternatives Considered

### Permit arbitrary path prefixes

Rejected. This would implicitly authorize reverse-proxy mounting and would
require explicit joining, escaping, normalization, and compatibility semantics
for two fixed cluster endpoints and runtime-owned paths. No accepted contract or
repository evidence requires it.

### Permit queries or fragments

Rejected. They do not describe an HTTP origin, can make appended paths
ineffective or surprising, and queries can become secret-bearing channels.

### Permit URL user information

Rejected. Credential-bearing declarations conflict with RFC-0039 and the local
runtime-composition no-secret boundary. Authentication requires a separate
decision.

### Preserve every value accepted by current validators

Rejected. Current syntax acceptance is the ambiguity being corrected; it is
not evidence of an intended resource-URL compatibility contract.

### Introduce a generic base-URL abstraction

Rejected. Two small validators with shared component semantics do not justify a
framework. Implementation may use one concrete pure helper if it makes the
code smaller and clearer.

## Trade-offs

Configurations that happened to use currently accepted extra components will
fail after implementation. That compatibility tightening is deliberate and
must be documented, but it is preferable to preserving undefined endpoint and
secret behavior.

Origin-only URLs do not support Home AI Cluster receivers or llama-server
runtimes exposed only beneath reverse-proxy path prefixes. Operators must use an
origin-level endpoint under this contract. A real prefix-mounting need may be
investigated separately.

The implementation may duplicate a few explicit checks or share one small
helper. This RFC prioritizes visible semantics over mandating an abstraction.

## Impact and Implementation Authorization

This Draft changes no behavior and authorizes no implementation before
acceptance.

If accepted, one later small implementation may:

1. reject URL user information, non-root paths, queries, and fragments at both
   explicit configuration boundaries;
2. continue accepting empty and `/` paths and normalize them identically without
   a trailing slash;
3. preserve remote `http`/`https` and local llama-server loopback `http` rules;
4. construct cluster-owned internal request and status URLs structurally;
5. add focused positive and negative tests for inline and file-backed remote
   declarations and CLI/file-backed llama-server composition;
6. preserve privacy-safe operator errors; and
7. update only documentation needed to clarify accepted URL examples.

That implementation must not change the vendored browser, request or response
models, routing, fallback, capabilities, runtime adapters beyond URL use,
status semantics, lifecycle, listener exposure, dependencies, or any unrelated
audit finding.

## Open Questions

None within this proposed boundary. Exact helper placement and library calls
remain implementation details.

## Decision

Accepted.

Existing explicit HTTP base URLs in this RFC's scope identify HTTP origins.
Their allowed components are a scheme, host, and optional explicit port. User
information, non-root paths, queries, and fragments are rejected. An empty path
and `/` remain equivalent and normalize to the same base URL without a trailing
slash.

Remote Home AI Cluster URLs retain their existing `http` / `https` and
trusted-LAN boundaries. Explicit llama-server URLs retain loopback-only `http`.
The cluster-owned internal request and status paths remain fixed, and
prefix-mounted receivers are not authorized.

This decision adds no authentication, TLS policy, proxy, discovery, generic URL
framework, or other network authority. Implementation remains a separate
follow-up pull request.
