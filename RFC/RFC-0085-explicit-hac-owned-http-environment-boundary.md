# RFC-0085: Explicit HAC-Owned HTTP Environment Boundary

Status: Accepted

Date: 2026-08-24

Author: frian

## Summary

This Draft proposes an explicit HTTPX environment boundary for every HAC-owned
HTTP client used in cluster operation: a later implementation would construct
each such `httpx.Client` or `httpx.AsyncClient` with `trust_env=False`.

The proposal confines the change to HAC-owned traffic. It does not authorize an
implementation, alter routing, create a general proxy facility, or make the
system independent of every network property supplied by its operating
environment.

## Problem

HTTPX trusts environment configuration by default. Ambient proxy and
certificate variables can therefore alter HAC-owned traffic without an explicit
HAC configuration decision. This matters both for fixed local loopback requests
and for operator-declared static remotes.

The [HAC-owned proxy environment boundary investigation](../docs/hac-owned-proxy-environment-boundary-investigation.md)
identified 15 production HTTPX constructor sites. Its synthetic proxy experiment
showed that an ambient proxy can receive a harmless HTTP request body and
destination metadata. It also showed that an unsupported SOCKS proxy setting can
prevent client construction. A passing suite under a contaminated environment
is negative evidence only: the relevant paths may not have been exercised.

The resulting boundary is consistent with [PRINCIPLES.md](../PRINCIPLES.md):
network authority must be explicit and bounded, local operation must remain
predictable, and failures must not expose unnecessary request information.

## Goals

- Make the environment boundary explicit for every HAC-owned HTTPX client used
  for cluster operation.
- Preserve each client’s existing declared destination and protocol validation.
- Prevent ambient proxy and environment certificate settings from silently
  changing HAC-owned HTTP client behavior.
- Retain normal, verifying TLS for declared remote HTTPS destinations.
- Preserve injectable-client ownership and test-only transport patterns.

## Non-goals

- Authorizing an implementation PR in this RFC’s Draft state.
- Adding a general proxy configuration, proxy credentials, or proxy discovery.
- Adding private-CA configuration, weakening TLS verification, or setting
  `verify=False`.
- Mutating or clearing process-global environment variables.
- Bypassing VPNs, Tailscale, system routes, transparent proxies, DNS, routers,
  or other network-layer controls.
- Changing provider or plugin client contracts, including those of RFC-0078 and
  RFC-0079.
- Controlling network activity performed by the Aider subprocess.
- Adding dependencies, a shared HTTP client abstraction, retries, timeout
  changes, fallback changes, cancellation changes, protocol changes, endpoint
  changes, model or capability changes, or a Roadmap Phase 19 commitment.

## Proposal

### HAC-owned HTTPX clients

A later implementation of this proposal must pass `trust_env=False` directly
when it constructs every HAC-owned `httpx.Client` or `httpx.AsyncClient` used
for cluster operation. The scope includes:

- fixed native loopback chat, summarize, and classify requests;
- the shared Code and Code File native helper;
- the source-grounded/external-information HAC loopback request;
- the Aider translator’s HAC loopback request;
- Ollama and llama-server health and execution clients; and
- static remote execution and status clients.

This is a direct constructor argument at the existing ownership point. It does
not authorize a generic client factory or abstraction unless implementation
evidence later demonstrates that one is necessary.

### Environment settings excluded from HAC-owned clients

With `trust_env=False`, the proposed clients do not inherit these ambient HTTPX
environment settings:

- `HTTP_PROXY` and `http_proxy`;
- `HTTPS_PROXY` and `https_proxy`;
- `ALL_PROXY` and `all_proxy`;
- `NO_PROXY` and `no_proxy`;
- `SSL_CERT_FILE`; and
- `SSL_CERT_DIR`.

This is not a claim of total environment independence. It does not bypass a
VPN, Tailscale, system routes, transparent proxies, DNS, routers, or any other
network-layer path outside the HTTPX environment mechanism.

### Destination and routing boundary

The proposal preserves the existing destination authority: a fixed HAC
loopback address, a runtime-validated loopback address, or an
operator-declared remote address. It does not add a proxy-routing exception or
a `NO_PROXY` checklist. HTTPX’s normal proxy environment handling is not an
appropriate substitute for a declared HAC destination boundary.

### HTTPS and certificates

Declared remote HTTP and HTTPS destinations remain supported. For HTTPS,
ordinary TLS verification remains enabled using HTTPX’s default trust behavior;
the proposal only prevents use of environment-provided CA locations. It makes
no current promise to support an ambient private CA, adds no CA configuration,
and never authorizes `verify=False`.

If an operator-supported private CA is later demonstrated as necessary, it
requires a separate investigation and RFC that specifies explicit configuration
and lifecycle behavior.

### Ownership, providers, plugins, and tests

Provider and plugin-owned clients are excluded. Their contracts under RFC-0078
and RFC-0079, including their isolation requirements, remain unchanged. HAC
does not mutate global environment variables to enforce this proposal, and the
Aider subprocess remains responsible for its own network activity.

Where HAC provides an injectable client factory, HAC must pass
`trust_env=False` into that factory. A fully constructed injected client is
owned by its injector; HAC must not mutate its private state. Test-only ASGI
and `MockTransport` clients are likewise outside the production constructor
scope.

### Behavior preserved

The proposal preserves fixed URLs, remote URLs and their ordering, HTTP/HTTPS
validation, request and response schemas, timeouts, redirect behavior, routing,
fallbacks, cancellation, client lifetime, health and status semantics, error
privacy, plugin behavior, and runtime/model independence.

## Rationale

An explicit client boundary is narrower and more reliable than depending on a
host-specific proxy exclusion list. A plaintext HTTP proxy may observe request
bodies and destination metadata; even a harmless synthetic body confirms the
class of disclosure. An unsupported SOCKS setting can also make otherwise
valid client construction fail. Directly opting HAC-owned clients out of HTTPX
environment settings protects both privacy and availability while leaving
declared destinations and ordinary TLS semantics intact.

The investigation’s clean and contaminated full-suite passes do not establish
that every production route is protected. They only show that the suite did not
produce a failing observation for the affected paths. The proposed construction
boundary is therefore deliberate rather than inferred from incidental test
coverage.

## Alternatives considered

### Retain current behavior and rely on proxy exclusions

Rejected. It requires a host-specific `NO_PROXY` checklist, leaves behavior
dependent on ambient state, and does not prevent unsupported SOCKS settings from
affecting construction.

### Apply the boundary only to fixed loopback URLs

Rejected. HAC-owned static remote execution and status traffic would remain
subject to the same undeclared environment routing and certificate behavior.

### Apply the boundary to all HAC-owned HTTPX clients

Proposed. This matches the ownership boundary while preserving the existing
declared destination of each client.

### Preserve environment CA settings through a custom SSL context

Rejected. That retains an ambient configuration channel and obscures the
boundary. Explicit private-CA support, if needed, needs its own RFC.

### Add proxy configuration now

Rejected. It broadens authority, credentials, routing, and support obligations
beyond this narrow environment-boundary decision.

### Add private-CA support now

Rejected. There is no approved explicit configuration contract or lifecycle
design for it.

### Remove proxy variables globally

Rejected. It mutates global process state, affects non-HAC owners, and cannot
reliably define the intended boundary.

### Introduce a shared client abstraction

Rejected for now. Direct arguments at existing constructors are the smallest
change; an abstraction needs separate implementation evidence.

## Trade-offs

An operator whose remote HTTPS endpoint depends on an ambient private CA will
need explicit support before it can work under this proposed boundary. That is
intentional: it avoids silently importing trust material from the environment.
The proposal also deliberately does not make HAC immune to non-HTTPX network
interception or routing controls.

## Impact

This RFC acceptance changes no code, runtime behavior, tests, workflows,
dependencies, or lockfiles. This PR includes and authorizes no implementation.
A future implementation, if separately authorized, would make direct
constructor changes only and would preserve the behavior listed above.

Future implementation evidence should demonstrate all of the following:

- every relevant factory receives `trust_env=False`;
- static/status and runtime-adapter clients are covered;
- custom transports retain their current behavior;
- timeouts and redirect behavior are unchanged;
- a synthetic proxy cannot capture the HAC-owned request;
- an unsupported SOCKS setting cannot break client construction;
- no sensitive value is introduced; and
- locked checks and CI on Python 3.13 and Python 3.14 pass.

## Open questions

There are no open questions for this narrow proposed boundary. A demonstrated
need for explicit private-CA support is deliberately deferred to a separate
investigation and RFC.

## Decision

Accepted. Every HAC-owned HTTPX client used for fixed-loopback native requests,
local-runtime requests, declared-remote execution, and declared-remote status
must be constructed with `trust_env=False`. HAC must configure its owned client
instances directly and must not mutate process-global environment variables.
Plugin/provider-owned clients and Aider subprocess networking remain outside
this boundary.

Declared remote HTTP and HTTPS remain supported, and HTTPS verification must
remain enabled. This boundary does not support ambient `SSL_CERT_FILE` or
`SSL_CERT_DIR` private-CA discovery and adds neither proxy nor private-CA
configuration. A demonstrated need for explicit private-CA support requires a
separate future investigation and RFC. VPN, Tailscale, DNS, operating-system
routing, and transparent network controls are not altered.
