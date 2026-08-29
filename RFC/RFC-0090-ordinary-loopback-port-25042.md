# RFC-0090: Ordinary Loopback Port 25042

Status: Draft

Date: 2026-08-29

Author: frian

## Summary

This RFC proposes changing the fixed ordinary Home AI Cluster (HAC) loopback
convention from `127.0.0.1:8000` to `127.0.0.1:25042` before 0.5.0.

The change is one coordinated fixed-convention change. It does not introduce
configuration, discovery, fallback, service management, a new endpoint, or a
new browser port. It amends only the port-specific portions of RFC-0038,
RFC-0045, RFC-0054, and RFC-0062.

## Problem

The ordinary local launcher, ordinary static-cluster launcher, installed native
callers, and loopback browser currently use the ordinary `127.0.0.1:8000`
convention. Port 8000 is a common local development convention, creating an
avoidable collision risk when a new user first installs and uses HAC.

The [ordinary loopback port investigation](../docs/ordinary-loopback-port-investigation.md)
found 25042 to be a sufficiently defensible boring candidate. At the time of
the investigation it was unassigned in the IANA service-name registry, lies in
the IANA User Port range, and is below the documented default Linux local
ephemeral range and modern Windows dynamic range. Those facts do not guarantee
availability: an unassigned IANA port is not reserved for HAC, administrator
settings can differ, and any locally installed program can occupy a fixed port.

The 0.5 goal is predictable first installation and first use for a user without
project history. HAC remains pre-1.0, so changing this convention now has lower
compatibility cost than deferring a known collision risk until wider use.

## Goals

This RFC should:

* establish `127.0.0.1:25042` as the one ordinary fixed/default loopback
  convention;
* keep the existing ordinary process, native paths, loopback exposure, and
  same-origin browser composition predictable;
* preserve the explicit local server `--port` override without making it client
  discovery or configuration;
* amend the accepted port-specific contracts explicitly and leave all their
  other provisions unchanged; and
* make the deliberate pre-1.0 compatibility break clear and bounded.

## Non-goals

This RFC does not add or change:

* automatic free-port selection, port probing, fallback, or retry;
* service discovery, port propagation, or client discovery;
* dual-port listening, an 8000 redirect, a compatibility proxy, or a second
  listener;
* persistent, environment-variable, or generic base-URL port configuration;
* a shared endpoint abstraction introduced solely for this change;
* native endpoint paths, host/bind exposure, LAN browser access,
  authentication, TLS, Docker, or Kubernetes;
* OpenAI-compatible port 8001, SearXNG port 8888, or runtime-provider ports;
* global rewriting of explicit remote-node URLs; or
* historical proof, investigation, closeout, or retained evidence records.

## Proposal

### Ordinary port convention

After a later implementation, the ordinary HAC loopback convention is:

```text
127.0.0.1:25042
```

`hac local` and the ordinary local launcher default to that loopback port.
`hac static-cluster` uses that same fixed ordinary loopback bind. The existing
native paths do not change, including:

```text
/v1/chat
/v1/summarize
/v1/classify
/v1/chat/sources
```

The ordinary installed caller surfaces move together with the convention:
Chat; Code where it reuses the Chat native request; Summarize; Classify; Aider's
private bounded translator; external-information source-grounded Chat; and
dependent accepted caller edges that inherit those ordinary native contracts.

The loopback browser remains a direct same-origin client of its ordinary
launcher. It follows the new ordinary origin; no browser-specific second port
is introduced.

### Existing explicit `--port` boundary

`hac local --port <PORT>` remains a supported explicit server override with
its current meaning. It does not become client discovery or client
configuration. Built-in ordinary installed callers continue to use the fixed
ordinary convention, now 25042.

Consequently, an operator who deliberately starts:

```text
hac local --port 8000
```

has started an explicitly overridden server, while fixed ordinary clients target
25042. This existing server/client mismatch is deliberately not solved here.

### Amended accepted contracts

This RFC amends only the following port-specific portions of accepted RFCs:

* **RFC-0038, Ordinary static multi-node mode:** its "existing ordinary
  application port" for the ordinary static-cluster process is 25042.
* **RFC-0045, One-shot ordinary request command:** its fixed Chat target becomes
  `POST http://127.0.0.1:25042/v1/chat`.
* **RFC-0054, Minimal Summarize CLI:** its fixed Summarize target becomes
  `POST http://127.0.0.1:25042/v1/summarize`.
* **RFC-0062, Minimal Loopback Web Client:** its ordinary loopback-browser
  launcher bind and same origin become `127.0.0.1:25042`.

All non-port provisions of those RFCs remain unchanged. Accepted RFC files are
historical architectural records and are not retroactively edited by this RFC.
RFC-0049, RFC-0055 through RFC-0057, RFC-0061, RFC-0063, RFC-0065, RFC-0067
through RFC-0072, RFC-0077 through RFC-0078, RFC-0080 through RFC-0081, and
RFC-0083 through RFC-0088 reuse an amended fixed ordinary target or RFC-0062's
same-origin composition where applicable. They inherit the new port without
new architectural semantics. Illustrative explicit remote `:8000` URLs do not
make an RFC an additional port-contract owner.

### Unchanged ports and explicit URLs

The separate OpenAI-compatible process remains `127.0.0.1:8001`. The separately
packaged SearXNG plugin remains `127.0.0.1:8888` under RFC-0079. Operator-owned
runtime-provider endpoints, including Ollama and llama-server endpoints, remain
unchanged.

Explicit operator-supplied remote-node base URLs remain operator values. For
example, `http://192.0.2.10:8000` does not become invalid merely because the
ordinary default becomes 25042. If a current documentation/example URL is
intended to show a remote HAC receiver using its ordinary default, a later
implementation/documentation PR may align it case by case. This RFC defines no
global replacement rule.

Historical proof, investigation, closeout, and retained evidence documents
continue to state the port true when they were created, unless separately
identified as living current documentation.

### Compatibility transition

This is a deliberate pre-1.0 compatibility change. After implementation,
scripts and manual calls that assumed ordinary HAC on 8000 must use 25042,
unless the operator explicitly launches the server on another port.

No automatic redirect from 8000, second listener on 8000, compatibility proxy,
request retry from 25042 to 8000, or automatic free-port fallback is introduced.
Those transitional mechanisms would add ambiguous process ownership and
unnecessary complexity solely for a pre-1.0 port change.

## Rationale

One fixed ordinary convention remains smaller and more predictable than dynamic
allocation because installed callers and same-origin browser behavior already
depend on a known ordinary process. The privacy and security property is the
loopback bind, not obscurity of the port number; this change is not a security
mechanism.

25042 is selected because the investigation found it sufficiently defensible,
not because it is uniquely optimal, permanently unused, or
owned by HAC. Retaining 8000 keeps a known first-use collision risk. A simple
fixed replacement now preserves a boring, explainable contract before 1.0.

## Alternatives considered

### Keep 8000

Rejected. It preserves an avoidable and already identified collision risk with
common local-development use.

### Use 25042

Preferred. It has adequate registry and default-range evidence for a fixed
ordinary convention without claiming certainty about local availability.

### Select another arbitrary User Port

Rejected. The investigation found no meaningful advantage that justifies
restarting port-number optimization.

### Dynamically choose a free port

Rejected. Clients would require discovery or propagation, and the existing
fixed-process and same-origin browser boundary would become less predictable.

### Keep 8000 temporarily and migrate later

Rejected. Later migration increases compatibility burden without an
architectural benefit and retains the known first-use risk in the meantime.

## Trade-offs

The change requires focused implementation, test, and current-documentation
alignment, and existing manual scripts using 8000 will need adjustment. A less
familiar port also has a small documentation and muscle-memory cost.

Those costs are accepted because the break is pre-1.0 and contained. Avoiding
dual listeners, redirects, configuration, and discovery keeps the ordinary
contract clear rather than hiding the break behind new machinery.

## Impact

If accepted, this RFC authorizes a later focused implementation to change the
ordinary local default, ordinary static-cluster fixed port, existing fixed
ordinary caller URLs/constants, focused behavior tests, same-origin browser
expectations, current user/operator documentation, and examples that
intentionally represent an ordinary-default receiver.

It does not require internal refactoring or a generalized endpoint constant.
An implementation may make a small natural reuse if the existing code supports
it, but must not broaden architecture to do so.

## Implementation boundary

Implementation must be a later, separate change. It must make only the minimum
changes listed above and must not introduce a configuration framework,
discovery, migration fallback, or a port-allocation subsystem.

## Proof expectations

A later implementation should retain a privacy-safe acceptance check showing:

1. zero-argument ordinary `hac local` binds to `127.0.0.1:25042`;
2. an installed ordinary Chat request succeeds against that process;
3. at least one other fixed native caller succeeds against the same port;
4. the loopback browser is served from the new ordinary origin and completes an
   existing native request;
5. ordinary static-cluster startup uses `127.0.0.1:25042`;
6. OpenAI compatibility remains on 8001 and RFC-0079's SearXNG contract remains
   on 8888; and
7. no 8000 listener, fallback listener, redirect, proxy, or request fallback is
   introduced.

The retained proof must contain no real prompts, responses, private addresses,
machine names, runtime/model identifiers, credentials, or raw logs.

## Open questions

Review should confirm that the proposed compatibility break and its bounded
documentation impact are acceptable before 0.5. No service-discovery or
configurability question is opened by this RFC.

## Decision

Pending.
