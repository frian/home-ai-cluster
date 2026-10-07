# RFC-0151: Independent Desktop Thin Client

Status: Draft

Date: 2026-10-07

Author: frian

## Summary

Home AI Cluster should permit one independent, cross-platform Desktop thin
client for ordinary Chat. Its implementation should live in a separate
`home-ai-cluster-desktop` repository, use PySide6 / Qt Widgets for the first
window, and consume only the accepted native ordinary HAC Chat contract. HAC
remains independently usable and the sole owner of cluster semantics and
authority. This RFC proposes the boundary and first scope; it implements
nothing and remains Draft until accepted.

## Existing authority and evidence

RFC-0045 establishes a one-shot client of the already-running ordinary native
`POST /v1/chat` contract. RFC-0090 sets the current fixed ordinary loopback
target to `http://127.0.0.1:25042`. That route accepts ordered messages and the
`chat` capability and returns a normalized `ClusterResult`, including `content`
and cluster-owned attribution. The ordinary process owns routing, execution,
fallback, adapters, and result truth. The Desktop needs no new HAC route or
change to this contract.

A disposable non-Python experiment has exercised the real path from an
independent process through that native route, ordinary HAC execution, a real
runtime, and a returned `ClusterResult`. It imported no HAC implementation,
read no retained Configuration, reconstructed no topology, and made no routing,
node, model, or runtime choice. The experiment proves that the process and
contract boundary is feasible. Its Node.js implementation is disposable and
does not select a Desktop language or dependency.

A bounded comparison of Tauri 2 and PySide6 / Qt Widgets held the first Chat
scope fixed. Both can preserve the HAC boundary. PySide6 can make the native
loopback request directly through Qt Network without browser CORS or a
WebView-to-native HTTP bridge. Its remaining practical uncertainty is
cross-platform packaging. The technology choice below is this RFC's proposal,
not an already accepted consequence of that investigation.

## Problem and goals

HAC's existing loopback browser and one-shot commands already provide ordinary
Chat access. A separately packaged native window could offer a small local
presentation client while leaving those surfaces unchanged. Without an
explicit decision, Desktop implementation could silently import HAC Python
internals, gain browser or configuration authority, or add dependencies and
release obligations to the HAC core repository.

This proposal should establish one independent client and repository boundary,
choose a sufficient first UI technology, and keep the first implementation
small enough to validate on Linux, Windows, and macOS. It should not change
HAC's native, browser, compatibility, or cluster-to-cluster contracts.

## Proposed decision

### Repository and process boundary

`home-ai-cluster` remains the HAC core repository. The Desktop implementation
belongs in a separate repository expected to be named
`home-ai-cluster-desktop`. No Desktop implementation code, PySide6 / Qt
dependency, Desktop build configuration, or Desktop release pipeline is added
to `home-ai-cluster`. This RFC creates no repository.

The separate repository represents an architectural boundary: the Desktop is
one independent local client process, not a second HAC composition or a Python
package extension of HAC. HAC must work without it; the presentation client can
be replaced without changing HAC semantics. Shared implementation language
does not permit importing `home_ai_cluster` or inspecting private HAC state.

### First Desktop scope

The first implementation targets Linux, Windows, and macOS with PySide6 / Qt
Widgets. It has one application window, one user text input, one Send action,
minimal ordinary Chat presentation, returned `ClusterResult.content` display,
and a bounded, understandable HAC-unavailable presentation. It sends one
ordinary native request for capability `chat` to
`POST http://127.0.0.1:25042/v1/chat` using the existing request and response
contracts. The host and port are inherited from the currently accepted ordinary
native convention, including RFC-0090; this RFC does not establish independent
or permanent port authority. If that accepted HAC convention changes, Desktop
follows the changed native contract. HAC is already running. The Desktop neither
starts nor supervises it.

Each Send constructs a fresh ordinary `chat` request containing exactly one
newly submitted `user` message. Previously displayed requests and responses are
presentation state only: they are not automatically included in later requests,
replayed, or reconstructed as history or hidden context. The visible window is
not an implicit multi-turn session; a later Send starts new work and need not
clear the previous display.

At most one ordinary Chat request may be in flight. Send is unavailable while
one is pending; the first client has no request queue, background second Chat
request, or automatic retry. After a valid success, bounded failure, or client
timeout, the user may explicitly initiate another Send. The fixed client-side
wait bound is 120 seconds, without user configuration. On expiry the Desktop
presents a bounded timeout failure and makes Send available again. A timeout
does not prove that HAC did not execute the earlier request. The Desktop must
not claim that work was cancelled, not executed, or rolled back; a later Send
is new work.

A successful Chat presentation requires a successful HTTP response valid under
the accepted native ordinary `ClusterResult` contract, including expected Chat
content. Malformed or unexpected responses, redirects, transport failures,
timeouts, and unsuccessful HTTP responses are failures, not partial successes.
Ordinary user-visible failure must be bounded and understandable, without raw
exception dumps, tracebacks, arbitrary response bodies, private transport
details, unexpected returned URLs, or implementation diagnostics. This does not
constrain separately controlled development logs or tests and adds no telemetry
or persistent error logging.

The client may validate the narrow wire shape and present the returned content
and safe failure. It must not interpret attribution into availability, health,
routability, or a routing decision. No session, conversation persistence, or
client-side fallback is defined. The first window does not expose node, model,
runtime, adapter, or capability selection.

### HAC authority stays in HAC

The Desktop owns none of: topology, node or model discovery and selection,
capability semantics, routability, routing, runtime or adapter selection,
execution policy, fallback, health semantics, retained Configuration semantics
or mutation, HAC or runtime process lifecycle, filesystem or Workspace
authority, HAC-to-HAC transport, or compatibility protocol behavior.

It must not read retained HAC Configuration, infer active state from retained
state, contact Ollama or another runtime, reproduce routing logic, or access
HAC private implementation objects. If a later Desktop need has no accepted
native client contract, the requirement returns to HAC architecture before
implementation. A Desktop-owned workaround or second source of truth is not
authorized. New or changed HAC-owned observations, operations, authority, or
native client contracts belong in `home-ai-cluster` and follow its normal
architectural/RFC process where required.

### Client authority, privacy, and existing surfaces

The first client communicates only with the accepted local ordinary native Chat
surface. For its HAC request, it bypasses system, environment, and application
HTTP proxies, connects directly to the accepted ordinary loopback target, and
does not follow HTTP redirects. A redirect response is a bounded request
failure; it causes no request to the redirect target. This closes the first
Desktop request's local-first and privacy-first outbound boundary without
changing HAC. It must not require changes to HAC Host, Origin, CORS, loopback,
or other authority boundaries for Desktop convenience. It adds no listener,
telemetry, analytics, cloud service, remote Desktop control, or default prompt
or response retention.

RFC-0062's loopback browser and RFC-0130's separate trusted-LAN browser
authority remain browser-specific and unchanged. Browser facades do not become
generic Desktop APIs. RFC-0031 and RFC-0046's OpenAI-compatible access remains
a separate adapter boundary; the Desktop does not use it as its HAC integration.
RFC-0147 through RFC-0150's active explanation carriers and thin clients do not
expand this first Chat-only Desktop scope. The presence of multiple clients
does not select a generic HAC SDK, client framework, or control-plane API.

### Technology and distribution boundary

PySide6 / Qt Widgets is the proposed initial Desktop technology because Qt
Network fits the native loopback contract directly and Widgets suffices for the
first presentation requirement. Reusing Python is not itself the reason: the
Desktop must remain an independent HTTP client. Tauri 2 could also respect the
boundary, but its Rust, frontend build, WebView, IPC, and permission surfaces
add complexity not justified by this first window. This decision makes no
claim that PySide6 is universally superior or that a later migration is
planned. Reconsideration requires a concrete problem and the normal decision
process.

Desktop-only implementation, presentation, packaging, and technology decisions
belong to the Desktop project's own decision process after that repository
exists. A later framework change that preserves HAC contracts and authority
does not inherently require a new HAC architectural decision.

Cross-platform packaging remains to be validated. The Desktop repository owns
its eventual build and release work. This RFC selects no bundle format,
installer, signing or notarization system, CI release matrix, updater, or
deployment service. A later bounded packaging proof is required before claiming
supported distributable releases on all three target platforms. Packaging
uncertainty does not permit embedding HAC in the Desktop.

## Non-goals

This RFC does not implement the Desktop or create its repository. It does not
start, stop, install, supervise, or restart HAC; install runtimes; add a tray,
auto-start, or auto-update; persist conversations; or add generic settings,
retained Configuration, node, model, cluster-dashboard, or health-dashboard UI.

It does not add filesystem or Workspace Code authority, a generic Desktop-to-HAC
SDK or client framework, streaming without a separate decision, advanced
Markdown/rendering architecture, Image Generation UI, External Information UI,
or commitments to other future presentation features. It does not implement
packaging or choose installers, signing, notarization, or release automation.

## Alternatives considered

| Alternative | Assessment |
| --- | --- |
| Continue with only the browser client | Remains a valid access path and is not deprecated. It does not provide a separately packaged native local window. |
| Tauri 2 for the first window | Can preserve the native HAC boundary with scoped native HTTP. For this Chat-only need it adds Rust/Cargo, frontend build tooling, OS WebView dependencies, and WebView/native IPC and permissions. Direct WebView requests would create pressure for HAC CORS changes. Defer without predicting a migration. |
| Put Desktop code in `home-ai-cluster` | Would bring Desktop dependencies, toolchains, and releases into the core repository and make the implementation boundary easier to blur. The separate repository better reflects an independent client. |
| Import HAC Python internals from PySide6 | Rejected. Language reuse is not authority. The accepted integration is the native HTTP client contract. |

## Consequences

The process and repository boundaries stay explicit. HAC remains usable without
Desktop dependencies and independent of the presentation technology; Desktop
cannot silently become another orchestrator. Existing native, browser, and
compatibility behavior stays unchanged.

The cost is a separate repository and release lifecycle, PySide6 / Qt packaging
and cross-platform validation, and possibly a small amount of independent
wire-response validation. Later Desktop needs may expose missing HAC-owned
observations and require separate HAC decisions. None is solved here.

## Falsifiable implementation proof

Before the first Desktop implementation claims this RFC, demonstrate:

1. The Desktop runs as a separate process with no `home_ai_cluster` import or
   private-state access; HAC is already running and is not started by Desktop.
2. One Send action submits an accepted ordinary `chat` request directly to the
   inherited native loopback endpoint; real HAC routes and executes it through
   a real runtime, and the window presents valid `ClusterResult.content`.
3. Transport evidence shows system, environment, and application HTTP proxies
   are bypassed, redirects are not followed, and client proxy or redirect
   behavior cannot send the request outside the accepted ordinary loopback
   destination. A redirect yields bounded failure without another request.
4. While one Chat request is pending, Send is unavailable and no second request
   starts or queues. After its terminal presentation, Send becomes available;
   no automatic retry occurs.
5. Two sequential Sends produce two independent ordinary `chat` requests, each
   with exactly one newly submitted `user` message and no prior displayed
   request or response as context.
6. The client presents timeout failure after the fixed 120-second wait, enables
   a new explicit Send, and neither retries automatically nor claims the earlier
   work was cancelled, not executed, or rolled back.
7. Valid native success presents Chat content; malformed, unexpected, redirect,
   transport, timeout, and unsuccessful HTTP responses yield bounded,
   understandable user-visible failure without raw private details.
8. Desktop code makes no direct runtime request, routing decision, or node,
   model, adapter, or runtime selection, and reads no retained Configuration.
9. No HAC API, browser authority, compatibility behavior, Host/Origin/CORS
   rule, or loopback exposure changes to make the Desktop work.
10. Linux, Windows, and macOS packaging feasibility is investigated separately
    before claiming supported distributable releases for all three.

Real ordinary HAC integration is required where execution is claimed; a
transport fake alone cannot establish it. Validation should remain
proportional to the small client.

## Open questions

No unresolved architectural question blocks review of this narrow proposal.
Platform packaging feasibility remains an implementation and distribution
question to validate before release claims.

## Decision

Draft. This RFC does not authorize Desktop implementation until accepted.
