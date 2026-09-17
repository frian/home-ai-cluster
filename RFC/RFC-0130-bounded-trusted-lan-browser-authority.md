# RFC-0130: Bounded Trusted-LAN Browser Authority

Status: Accepted

Date: 2026-09-17

Author: frian

## Summary

This RFC proposes one optional, explicit trusted-LAN browser capability
authority for both existing browser-owning launchers:

```text
hac local
hac static-cluster
```

It is a separate application and network authority from the existing native
loopback browser and the RFC-0109 receiver. It shares the owning launcher's
existing execution composition and, for static-cluster, its existing routing
truth; it does not create another HAC node, composition, router, or execution
limit scope.

The LAN page exposes only fixed ordinary capability use: Chat, text-only Code,
Image Generation, Summarize, and Classify. Configuration and Workspace-enabled
Code are structurally absent, not merely hidden. The LAN route set is closed;
the existing Chat request operation is additionally restricted to
`capability=chat` and `capability=code` on this authority.

Activation requires one explicit concrete non-loopback IP address. Every LAN
route requires the exact configured Host authority; capability POSTs also
require an exact same-origin Origin, appropriate existing request media type,
and no CORS authority. These checks protect browser-origin and DNS-rebinding
boundaries, not network-client identity. Plain HTTP remains suitable only when
both reachable peers and the network path are trusted for this bounded use.

This Draft proposes no authentication, TLS, credentials, configuration,
workspace, discovery, proxy process, persistence, or new routing semantics.

## Context

RFC-0062 accepts one fixed same-origin loopback browser over native HAC
capabilities. Later RFCs add ephemeral browser Chat and Code, retained local
and remote-node Configuration facades (RFC-0112 and RFC-0113), optional
workspace-enabled Code (RFC-0124), and Image Generation (RFC-0129). Those
later surfaces deliberately remain within loopback browser authority.

RFC-0109 defines a separate, closed LAN receiver authority for HAC-to-HAC
transport. RFC-0111 makes it an explicit additive `hac local --receiver-host`
activation over one foreground process and one `LocalAppComposition`. It does
not make receiver authority a browser or native-client authority.

RFC-0090 establishes 25042 as the ordinary HAC port convention. Existing
receiver evidence shows that separately selected concrete bind addresses can
reuse that numeric port while remaining separate authorities.

The existing browser is useful from another trusted operator device, such as a
phone or tablet. Rebinding its complete application to LAN would also expose
retained Configuration and host filesystem Workspace authority. The needed
decision is therefore a narrower browser authority, not a broader bind for the
current browser application.

## Problem

HAC currently offers a fixed browser only on loopback. An operator cannot use
ordinary HAC capabilities from another trusted LAN device without exposing the
complete local browser authority.

That complete authority is too broad. Retained Configuration persists HAC-owned
local configuration and static remote-node declarations. Workspace-enabled Code
can exercise explicit `list`, `read`, `write`, and `create` authority over a
host workspace. Both were accepted as loopback-only surfaces.

The useful LAN experience must work with `hac static-cluster`, not only a local
runtime, so that it retains the existing caller-local permission, local and
remote eligibility, ordered declarations, fallback, and execution accounting.
It must not create a simplified parallel router merely to serve a browser.

## Goals

This RFC proposes to:

- add one disabled-by-default, explicitly bound trusted-LAN browser authority
  to both `hac local` and `hac static-cluster`;
- preserve one launcher-owned execution composition and, for static-cluster,
  its existing routing and static-permission truth;
- expose only Chat, text-only Code, Image Generation, Summarize, and Classify;
- make Configuration and Workspace authority structurally unreachable through
  the LAN authority;
- give the LAN browser a closed, fail-closed route and request-authority
  vocabulary;
- require exact configured Host authority across the LAN surface and exact
  same-origin Origin for capability POSTs;
- state an honest trusted-peer plus trusted-network-path plain-HTTP model; and
- preserve loopback browser and receiver authority unchanged.

## Non-goals

This RFC does not add or decide:

- full current-browser LAN exposure, LAN Configuration, LAN Workspace, remote
  administration, or a cluster-management dashboard;
- authentication, authorization credentials, accounts, login, pairing, QR
  codes, browser secrets, sessions, cookies, API keys, bearer tokens, OAuth,
  HMAC, or secret persistence/rotation;
- TLS, mTLS, certificate generation, PKI, or certificate management;
- DNS, mDNS, service or interface discovery, automatic interface selection,
  wildcard binds, network probing, firewall management, or VPN integration;
- retained listener profiles, daemonization, service installation, supervision,
  PID files, a proxy process, or a generic listener framework;
- browser sessions, server-side conversation history, prompt/result retention,
  databases, analytics, or telemetry;
- status/health polling, capability/runtime/model discovery, dynamic view
  suppression, new routing semantics, new static permissions, or remote Image
  Generation architecture;
- External Information changes, streaming, WebSockets, SSE, CORS, a frontend
  framework, generic browser proxy schema, generic API abstraction, Docker, or
  Kubernetes.

## Proposal

### One explicit authority, two owning launchers

This Draft proposes one optional trusted-LAN browser capability authority.
It is neither a widening of RFC-0062 native/loopback browser authority nor a
widening of RFC-0109 receiver authority:

```text
one HAC process / one existing execution truth
        |
        +-- existing loopback/native browser authority
        +-- optional trusted-LAN browser capability authority
        `-- optional receiver authority where already applicable
```

The exact FastAPI, ASGI, and listener representation remains implementation
detail. The architectural distinction is durable:

```text
same execution composition / routing truth
!=
same ASGI route authority
```

`hac local` uses its existing local execution composition and semantics. LAN
activation creates no local node, adapter composition, execution-limit scope,
or routing policy.

`hac static-cluster` uses its existing static-cluster routing truth. It
preserves caller-local capability permission, local and remote eligibility,
ordered remote declarations, routing/fallback behavior, and execution-limit
accounting. It creates no parallel router and does not reinterpret permission.
In particular, this Draft does not make Image Generation static-routable. A
fixed view with no eligible candidate may show ordinary honest safe failure.

### Capability-only browser surface

The fixed LAN browser has only these human-facing views:

```text
Chat
Code
Image Generation
Summarize
Classify
```

Code is ordinary text-only `code` capability use. Workspace controls, roots,
grants, and `/workspace-code` are absent. Configuration is absent, including
read-only Configuration.

Exact HTML, labels, navigation order, responsive presentation, and reuse of
the current packaged design remain implementation details. Fixed views need not
be hidden when the invocation currently lacks an eligible candidate. The LAN
page adds no capability discovery, runtime probing, health polling, remote
status polling, or model discovery.

### Structural exclusion and closed route ownership

Not rendering a control is not an authority boundary:

```text
not rendered
!=
not authorized
```

The LAN authority owns a closed route set. It must not result from attaching the
broad native browser wrapper to an arbitrary LAN bind and must not automatically
inherit future native or framework routes. A route is reachable through this
authority only when this RFC or a later explicit architectural decision admits
it.

The first route domain is exactly:

```text
GET  /
GET  fixed packaged assets required by the capability-only page

POST /v1/chat
     capability = chat | code only

POST /v1/summarize
POST /v1/classify
POST /v1/image-generation
```

The fixed packaged asset set remains closed, but individual asset paths and
filenames are implementation details. It may include existing PDF.js assets
needed for browser-local Summarize preprocessing, a dedicated capability-only
JavaScript asset, or other safe fixed assets required by the page. This
authorizes no arbitrary filesystem static serving, directory listing,
user-provided asset path, runtime file, generated-image URL, or media store.

The following are structurally excluded at minimum:

- `/workspace-code` and all Workspace UI authority;
- retained local Configuration browser routes;
- retained remote-node Configuration browser routes;
- `/v1/chat/sources` and `/internal/chat/external-information-decision`;
- `/internal/cluster/request`, `/internal/cluster/status`, and receiver-only
  routes;
- OpenAI-compatible, runtime-native, status, health, preflight, and operator
  inspection surfaces; and
- framework documentation/schema defaults and every future native route not
  explicitly admitted to trusted-LAN browser authority.

The concrete spelling of framework defaults is not a long-term architectural
contract. The durable rule is that application or framework defaults do not
widen this closed authority. This is closed cluster-owned policy, not an
operator-configurable route allowlist.

### Request-domain closure

Route closure is insufficient because the existing Chat request operation
accepts a capability field. On trusted-LAN browser authority, that operation is
restricted to exactly:

```text
capability = chat
capability = code
```

It must not accept arbitrary present or future capability names merely because
the native request representation does. This narrows authority only: it does
not redefine native Chat or Code request/result contracts and does not require
a generic browser proxy schema.

Image Generation preserves RFC-0127's bounded instruction and raw PNG success
semantics; it adds no dimensions, format choice, controls, output path,
filesystem destination, or remote routing. Summarize preserves its native text
semantics; browser-local selected text/PDF preprocessing may be retained only
with fixed packaged assets and the existing semantic text request, not an upload
service. Classify preserves native ordered-label semantics.

### Explicit bind and port authority

Trusted-LAN browser authority is disabled by default. Activation requires one
operator-supplied concrete non-loopback IP address. A later implementation
should use the standard-library concept of a concrete IP value and fail locally
before listener startup for wildcard/unspecified addresses such as `0.0.0.0`
or `::`, loopback addresses, hostnames/DNS names, malformed addresses, and other
invalid values. HAC must not enumerate interfaces, choose an address, use mDNS,
discover services, probe reachability, rewrite hostnames, or choose Wi-Fi versus
Ethernet.

The operator-facing spelling should use simple symmetry with RFC-0111's
explicit receiver activation rather than a new configuration framework. This
Draft proposes `--lan-browser-host <ADDRESS>` on both launchers. It does not
retain listener configuration.

An optional `--lan-browser-port <PORT>` may override the port and requires
`--lan-browser-host`. Otherwise the LAN browser defaults to 25042. A distinct
concrete bind address may reuse the same numeric port. If explicitly requested
authorities conflict on the same exact `IP + port`, startup fails visibly. HAC
must not choose, increment, or probe another port; merge route authorities;
silently disable either authority; or fall back to a wildcard bind. The
operator can select another explicit port.

### Browser-origin protection and threat model

The configured LAN bind and effective browser port define one accepted Host
authority. Every LAN route—page, assets, and capability routes—requires that
exact Host authority. Capability POSTs additionally require exact same-origin
Origin, the appropriate existing bounded request media type, and no CORS
authority. Missing Origin, `Origin: null`, foreign Origin, or unacceptable
Host/Origin/media type fails before execution. CORS preflight is not
authentication, and wildcard CORS is not introduced.

The page must forbid cross-origin framing. The particular standards-compliant
header mechanism is implementation detail; reusing the existing CSP-style
approach is a suitable candidate.

Host and Origin are not client authentication. A raw LAN HTTP client can forge
them. The security model is deliberately:

> A network peer able to reach the trusted-LAN browser listener is trusted to
> exercise the bounded capability-only surface.

Host/Origin instead protect browser-origin and DNS-rebinding-style threats.
Plain HTTP supplies no confidentiality, integrity, or server authentication. A
passive network observer may read prompts and results; an active on-path
adversary may alter page/JavaScript, prompts, results, or requests. The
operator must therefore trust both reachable peers and the network path for
this bounded use. Wi-Fi security, firewall rules, VPN/overlay networks, and
similar protections remain operator-owned, not HAC integrations.

No authentication or TLS mechanism is selected here. LAN reachability alone is
sufficient only for this bounded capability-only surface; it cannot authorize
future LAN Configuration or Workspace authority without a separate security
decision.

### Lifecycle, state, privacy, and compatibility

The LAN listener belongs to its owning foreground invocation. Normal shutdown
ends all that invocation's authorities, and startup failure must not
intentionally leave a partial independently managed authority running. This
adds no daemon, service, process supervision, PID file, background lifecycle,
or second process requirement.

Browser state remains current-page-only: Chat and Code conversations and the
current generated Image stay ephemeral, with no server-side session,
conversation persistence, LAN session ID, cookie, database, or persisted
prompt/result. Existing theme preference may remain browser-local presentation
state; different origins need not synchronize storage.

LAN access adds no logging of prompts, responses, source text, labels, generated
image content, retained configuration, workspace paths, or private LAN
addresses beyond unavoidable ordinary server/network operation. It adds no
analytics or telemetry, and request content must not enter URL/query/path
metadata.

Zero-argument `hac local`, loopback browser Configuration and Workspace,
`hac static-cluster` loopback behavior, routing and static permission,
receiver authority, remote request/status contracts, native request/result
contracts, retained configuration, Image Generation restrictions, and the
OpenAI compatibility boundary remain unchanged. LAN activation is additive and
must not make loopback operation depend on LAN availability.

## Rationale

The smallest useful LAN experience is ordinary capability use from another
trusted device, not a complete administrative browser. Keeping a separately
closed route authority makes the stronger Configuration and Workspace powers
unreachable instead of relying on presentation conditions.

Including both existing browser-owning launchers preserves the project motto:
the user talks to HAC rather than choosing a different LAN-only local mode.
Static-cluster routing remains explicit, capability-centered, deterministic,
and operator-owned. Sharing its existing execution truth also avoids falsely
representing a second composition as the same node.

An explicit concrete bind, one ordinary port convention, fail-visible conflict,
and no discovery are boring operator-owned network choices. Host/Origin and
anti-framing preserve browser authority without misleadingly claiming that
plain HTTP authenticates LAN clients or secures hostile network paths.

## Alternatives considered

### Bind the complete existing browser app to LAN

Rejected. It would expose loopback-only Configuration, Workspace, and broad
inherited native/framework routes.

### Hide Configuration and Workspace controls

Rejected. UI visibility is not route or authority control.

### Reuse receiver authority

Rejected. RFC-0109 owns a separate closed HAC-to-HAC transport authority.
Receiver and browser route sets must not fuse merely because both can bind a
LAN address.

### `hac local` only or `hac static-cluster` only

Rejected as complete first scope. Both are existing browser-owning launchers;
the same bounded browser concept should preserve each launcher's execution and
routing semantics rather than create an arbitrary product split.

### Add authentication or TLS first

Deferred. This Draft limits exposure to an explicitly activated,
capability-only surface and states its trusted-network limitations honestly. It
does not claim stronger protection is unnecessary for future authority.

### Wildcard bind or automatic interface selection

Rejected. Both expand or choose network authority without the operator's
explicit concrete decision.

### Separate proxy or web process

Rejected unless later implementation evidence proves it necessary. It would
add another lifecycle and request recipient without a demonstrated need.

## Trade-offs

The LAN listener intentionally trusts any reachable peer and its network path
for ordinary bounded capability use. It is not appropriate for hostile LANs or
paths, and it offers no Configuration or Workspace authority. That limitation
is the trade-off that keeps the first LAN decision small without prematurely
choosing an authentication or TLS system.

Fixed views may be visible when no existing eligible candidate can execute
them. Honest ordinary failure is preferable to coupling the browser to new
capability discovery or observation.

Maintaining a closed second route authority adds focused implementation work,
but it avoids inherited future authority and preserves the distinct loopback
and receiver contracts.

## Compatibility and impact

If accepted, implementation may add only the smallest launcher, closed
application, packaged capability-only browser assets, shared existing handler
reuse, and focused tests needed to realize this authority. It must return to
architectural review if it appears to require a second HAC node/composition,
duplicate router/accounting state, generic listener/proxy/authentication
framework, persistence, broader route authority, or altered routing semantics.

RFC-0062 remains loopback browser authority; RFC-0109 and RFC-0111 remain
receiver authority; RFC-0112 and RFC-0113 remain loopback Configuration; and
RFC-0124 remains loopback Workspace authority. RFC-0127 through RFC-0129 retain
their Image Generation execution, composition, and browser boundaries except
for this separately proposed capability-only LAN projection.

## Proof expectations

A later implementation should prove at least that:

1. zero-argument launch remains loopback-only and unchanged;
2. explicit valid activation works for both `hac local` and `hac static-cluster`;
3. wildcard, loopback, hostname, malformed, and invalid LAN hosts fail locally
   before listener startup;
4. each LAN authority shares its owner's composition/routing truth rather than
   creating another node, composition, router, or execution accounting scope;
5. static-cluster requests preserve existing local/remote routing, permission,
   fallback, and declaration order;
6. the LAN authority exposes exactly the positive execution route set in this
   RFC, plus only its fixed page and required packaged assets, and excludes
   receiver, Configuration, Workspace, caller-internal, framework,
   compatibility, inspection, and future unrelated native routes;
7. LAN `/v1/chat` accepts only `chat` and `code` capability values;
8. Configuration and `/workspace-code` are structurally absent, and LAN Code is
   text-only;
9. exact configured Host is required on every LAN route and capability POSTs
   require exact same-origin Origin, acceptable media type, and no CORS;
10. cross-origin framing is forbidden;
11. direct raw LAN clients can exercise the bounded surface with valid syntax,
    consistent with the stated trusted-peer model;
12. plain HTTP operation makes no false confidentiality, integrity,
    authentication, or server-identity claim;
13. fixed views may remain visible without eligible candidates and fail safely;
14. loopback Configuration/Workspace and receiver authority remain unchanged
    and separate;
15. bind conflicts fail visibly without fallback or route-authority merging;
16. foreground shutdown stops all invocation authorities; and
17. no authentication, TLS, discovery, daemonization, persistence, dashboard,
    generic listener framework, or routing change is introduced.

## Open questions

None necessary to implement this proposed bounded authority. Exact internal
application construction, HTTP parsing/normalization, error status/body,
anti-framing mechanism, HTML layout, and handler reuse remain implementation
details provided they preserve the authority properties above.

Future Configuration or Workspace LAN exposure, stronger client authorization,
TLS, listener retention, status/discovery, and broader browser capability
authority require separate architectural consideration.

## Decision

This Draft proposes one optional trusted-LAN browser capability authority for
both `hac local` and `hac static-cluster`. It shares each launcher's existing
execution composition and routing truth while remaining a distinct, closed
application authority from loopback/native browser and receiver authority. It
exposes only Chat, text-only Code, Image Generation, Summarize, and Classify;
restricts `/v1/chat` to `chat|code`; excludes Configuration and Workspace;
requires exact configured Host across all LAN routes and exact same-origin
Origin for capability POSTs; forbids CORS and cross-origin framing; and requires
one explicit concrete non-loopback bind.

The proposal relies on a trusted-peer plus trusted-network-path plain-HTTP
model, explicitly does not treat Host/Origin as client authentication, and
selects no authentication or TLS mechanism. It preserves loopback and receiver
authorities, existing static-cluster routing and permission, and all current
capability semantics.
