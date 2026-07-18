# RFC-0046: Explicit static-cluster compatibility access

Status: Accepted

Date: 2026-07-18

Author: frian

## Summary

The dedicated `home-ai-cluster-openai-compatibility` command should retain its
current local-only behavior by default. It should additionally accept one
optional operator-owned declaration:

```text
home-ai-cluster-openai-compatibility --declaration <path>
```

This form should start the same strict, loopback-only RFC-0031 compatibility
edge over the already accepted ordinary explicit static-cluster composition
identified by the declaration. It should reuse existing declaration parsing,
validation, remote ordering, static wiring, capability routing, bounded
candidate traversal, remote transport, result validation, and caller-owned node
attribution.

The compatibility protocol does not change. This RFC adds no model discovery,
streaming, tools, request-level infrastructure selection, LAN-facing
compatibility access, authentication, lifecycle automation, or generic
composition framework.

## Problem

The repository currently has two accepted but separate process constructions.

The dedicated compatibility command constructs the ordinary local-only
application and adds the RFC-0031 compatibility router. It is loopback-only and
has no topology or composition-selection input. Aider has been proved against
this narrow process.

Separately, `home-ai-cluster-static-cluster --declaration <path>` loads an
operator-owned RFC-0039/RFC-0040 declaration and constructs ordinary explicit
static-cluster wiring. That process owns capability-centered local-first routing,
accepted bounded fallback, remote HTTP transport, result validation, and
caller-owned declared-node attribution. The native one-shot client has been
proved through that ordinary path to a real remote receiver on a trusted LAN.

Those proofs do not compose today. Configuring an OpenAI-compatible client can
change only the client; it cannot make the compatibility process construct
static-cluster wiring. The missing decision is the process construction and
operator-owned topology-selection boundary. It is not a need for broader
OpenAI-compatible protocol behavior.

## Goals

This RFC should:

- preserve the existing no-argument local-only compatibility command;
- define one explicit `--declaration <path>` form for ordinary static-cluster
  compatibility access;
- reuse the accepted static declaration and wiring contracts without duplicating
  their semantics;
- keep the compatibility listener loopback-only on its existing dedicated port;
- keep client requests topology-, node-, runtime-, adapter-, and
  concrete-model-blind;
- preserve RFC-0031 request, response, authorization-placeholder, and error
  contracts unchanged;
- preserve existing capability routing, local-first behavior, bounded fallback,
  transport, and attribution ownership; and
- require a later privacy-safe real-tool proof without adding public routing
  fields.

## Non-goals

This RFC does not authorize:

- implementation code or a formal Phase 17;
- a generic composition framework, generic application factory, named profile
  system, or plugin mechanism;
- inline remote-node flags, environment-variable topology selection, automatic
  declaration discovery, or a default declaration path;
- a new declaration parser, schema, validation vocabulary, ordering rule, or
  topology format;
- streaming, tools, function calling, generation controls, model discovery,
  aliases, a model catalogue, or broad OpenAI compatibility;
- request-level node, runtime, adapter, concrete-model, topology, routing, or
  fallback selection;
- client-side or compatibility-layer routing, fallback, retry, direct remote
  calls, or runtime proxying;
- LAN-facing compatibility access, real authentication, authorization, or
  credential storage;
- discovery, scheduling, load balancing, supervision, repair, restart, remote
  process control, or automatic lifecycle ownership;
- a dashboard, database, Docker, or Kubernetes; or
- public compatibility response fields for node attribution or routing.

The roadmap remains complete through Phase 16. This is a standalone
post-roadmap architectural decision.

## Proposal

The command has exactly two supported operating modes:

```text
home-ai-cluster-openai-compatibility
home-ai-cluster-openai-compatibility --declaration <path>
```

No declaration retains the current ordinary local-only compatibility process.
With `--declaration`, the command must construct the unchanged RFC-0031
compatibility edge over the existing ordinary explicit static-cluster path
selected by that declaration.

The conceptual flow is:

```text
OpenAI-compatible client
  -> dedicated loopback-only compatibility process
  -> strict RFC-0031 request validation
  -> existing ClusterRequest with Capability("chat")
  -> existing operator-selected ordinary composition
     -> local-only when no declaration is supplied
     -> explicit static cluster when --declaration is supplied
  -> existing capability-centered local-first routing
  -> existing bounded candidate traversal
  -> existing runtime adapter or remote HTTP adapter
  -> existing normalized ClusterResult
  -> existing RFC-0031 compatibility response projection
```

The compatibility edge remains an access adapter. It does not become the cluster
protocol, runtime protocol, topology owner, direct runtime proxy, or
OpenAI-shaped routing interface.

## Command and mode selection

### Local-only default

An invocation with no arguments must retain the historical compatibility
behavior:

```text
home-ai-cluster-openai-compatibility
```

It constructs the existing local-only application behavior and binds the
compatibility listener only to its existing loopback host and dedicated port.
Existing local-only users and the retained Aider access proof require no
configuration change.

### Explicit static-cluster form

An invocation with one declaration is the sole new mode:

```text
home-ai-cluster-openai-compatibility --declaration <path>
```

The option is a process-startup input owned by the local operator. It selects an
existing ordinary explicit static remote collection; it is not sent by, exposed
to, or inferred from a compatibility client request.

This command must not accept inline remote-node arguments, runtime arguments,
environment variables, configuration files other than the supplied accepted
declaration, declaration discovery, default declaration locations, or client
selectors. The no-argument default remains necessary because it is the
compatible behavior established by RFC-0031.

## Reuse of existing declaration semantics

The declaration argument must accept the same RFC-0039 and RFC-0040 declaration
files that are accepted by:

```text
home-ai-cluster-static-cluster --declaration <path>
```

The compatibility command must reuse the accepted declaration loading and full
static validation boundary. It must not create a second parser, schema,
normalization rule, duplicate-handling rule, ordering rule, identity rule,
validation vocabulary, or migration path.

The declaration remains topology only. It contains the ordered declared remote
nodes and must not gain compatibility endpoint settings, client model values,
capabilities, runtime or adapter choices, model identifiers, credentials,
authentication data, lifecycle settings, or client metadata.

As in the existing static-cluster command, the declaration selects the remote
collection, not a request-level runtime or model. Because this RFC defines no
runtime arguments for the compatibility command, the declaration form uses the
same default local composition that the ordinary static-cluster command uses
when started with a declaration and no explicit runtime option. A later decision
about exposing additional local-composition startup inputs to this compatibility
command is outside this RFC.

Declaration loading and validation must complete before the compatibility
listener binds. They are static, local operations and must remain network-free:
they must not contact a remote node, inspect a runtime, test reachability, start
a runtime or remote application, repair a declaration, or mutate topology.

Invalid or unreadable declarations must prevent listener binding, emit the
existing compact privacy-safe CLI failure class, and exit non-zero. They are
operator startup failures, not RFC-0031 HTTP responses.

## Application construction and ownership

The implementation must construct one of two concrete existing application
shapes, not a generic composition abstraction.

Without `--declaration`, it constructs the existing local-only compatibility
application.

With `--declaration`, it must:

1. load and validate the accepted declaration before network binding;
2. construct the existing default local composition for an ordinary static
   cluster;
3. construct the existing ordinary explicit static remote collection wiring
   from that composition and the validated declarations; and
4. add the unchanged compatibility router to that application before binding the
   dedicated loopback listener.

The existing ordinary static-cluster construction remains the authority for
remote declaration registry creation, remote transport ownership, local-first
candidate order, and application lifespan. The compatibility route is only an
additional public edge over that constructed application.

This RFC does not require a generic application factory, a named composition
registry, a reusable profile framework, or a new process that owns both
compatibility and static-cluster lifecycle separately. The implementation may
use narrow internal helpers where necessary, but they must preserve the two
explicit process modes and must not become a general abstraction.

## Compatibility protocol boundary

RFC-0031 remains authoritative and unchanged.

The compatibility edge continues to provide only:

```text
POST /v1/chat/completions
```

It retains its accepted request fields, strict validation, fixed
`home-ai-cluster` endpoint identifier, non-streaming behavior, plain-text
message restrictions, one-choice response shape, compatibility error envelope,
and placeholder bearer handling. It retains the absence of model discovery,
aliases, routing fields, node fields, and custom compatibility extensions.

The compatibility client must not send or receive declaration paths, node IDs,
remote URLs, runtime names, adapter names, concrete runtime-model selectors,
routing policy, fallback controls, or lifecycle controls. It remains
topology-blind.

The normalized `ClusterResult` continues to own node attribution internally.
This RFC must not add node attribution, routing explanations, or any other
custom field to a compatibility response. The later proof must establish remote
execution without changing the public response contract.

## Routing and fallback boundary

The explicit static mode must invoke the existing cluster request path after
compatibility translation:

```text
strict compatibility request
  -> ClusterRequest(messages, Capability("chat"))
  -> existing ordinary static-cluster orchestration
```

It must not duplicate capability matching, local-first ordering, declared remote
order, fallback classification, candidate traversal, remote transport, remote
result validation, or declared-node attribution. It must not catch a local
failure and independently call a remote node.

Existing bounded candidate traversal remains cluster-owned. It may advance only
under the already accepted pre-execution failure conditions. The compatibility
edge and its client introduce no retry or fallback behavior. Remote execution
continues behind the existing remote HTTP adapter boundary, and the core router
does not become HTTP-aware because of this feature.

## Network boundary

The compatibility listener remains bound only to its existing loopback host and
dedicated port in both modes. Supplying a declaration changes only the
outbound routing of the constructed ordinary static cluster. It must not make
the compatibility endpoint reachable on the trusted LAN, public network, or
another interface.

A receiving machine remains an independently started ordinary Home AI Cluster
application. The operator alone may expose that receiver to the trusted LAN,
provide a firewall rule, and declare its address in an operator-owned
declaration. This RFC does not change the receiver's startup, transport
protocol, trust model, or exposure boundary.

## Lifecycle boundary

Home AI Cluster owns only the local compatibility process it starts. The
operator remains responsible for external runtimes, receiving applications,
declaration creation and removal, trusted-LAN exposure, firewall policy, and
starting and stopping the processes on both machines.

The declaration form must not imply or add supervision, restart, repair,
lifecycle inference, remote process control, discovery, health-aware
scheduling, background polling, or automatic topology mutation.

## Privacy and failure boundaries

Home AI Cluster must not log or retain by default through this feature:

- prompts or generated responses;
- authorization headers or placeholder bearer values;
- declaration contents, declared remote base URLs, private addresses,
  usernames, machine names, or source-code context;
- runtime URLs, concrete runtime-model details, raw transport errors, or raw
  remote response bodies; or
- request history, routing records, or proof instrumentation containing private
  topology.

The supplied declaration path may appear only in an operator-facing startup
failure when that is already consistent with accepted declaration error policy.
A remote URL must not appear in public compatibility errors, ordinary errors,
default logs, routing explanations, or retained proof evidence.

Compatibility request validation failures remain RFC-0031 HTTP errors.
Post-validation routing and runtime failures continue through the existing
compatibility error mapping. Declaration loading, validation, and process
construction failures occur before listener startup and remain CLI failures.
This RFC does not create a combined configuration/request error model.

## Compatibility and migration

The no-argument command is fully compatible with the accepted RFC-0031 local
path. It retains the same listener address, endpoint, request and response
contracts, error envelope, fixed endpoint identifier, and placeholder bearer
behavior. Existing Aider configuration and the retained local proof remain
valid.

The declaration form is additive and explicitly opt-in. It does not change the
native `/v1/chat` endpoint, existing ordinary local startup, existing
ordinary static-cluster startup, declaration files, remote receiver protocol,
result schema, routing policy, fallback semantics, or status behavior. No
migration is required.

## First implementation proof

A later implementation is complete only when it demonstrates at least:

1. existing local-only compatibility startup remains unchanged;
2. existing RFC-0031 tests continue to pass;
3. omitting `--declaration` constructs the existing local-only composition;
4. supplying one valid RFC-0039 declaration constructs the accepted static
   cluster composition;
5. supplying one valid RFC-0040 declaration preserves declared remote ordering;
6. declaration parsing and validation are reused rather than duplicated;
7. invalid declarations fail before listener binding;
8. declaration loading and validation perform no network observation;
9. the compatibility listener remains loopback-only in both modes;
10. compatibility request and response contracts remain unchanged;
11. client requests cannot select topology, node, adapter, runtime, or concrete
    model;
12. routing remains capability-centered and local-first;
13. bounded fallback remains the existing cluster-owned behavior;
14. remote transport remains behind the existing adapter boundary;
15. successful remote execution retains caller-owned declared-node attribution
    internally;
16. public compatibility responses contain no custom node or routing fields;
17. public and operator failures do not expose remote URLs or raw errors;
18. prompts, responses, authorization values, declaration contents, and private
    topology are not logged by default;
19. ordinary automated tests require no live runtime or remote machine;
20. one later explicit Aider proof can run across two physical machines without
    protocol expansion; and
21. no generic composition framework, discovery, lifecycle automation,
    authentication, LAN-facing compatibility access, or broad OpenAI
    compatibility is introduced.

A later Aider proof may inspect the caller-owned normalized result at an
existing internal seam or through focused proof-only observation. It must not
add node IDs to the compatibility response, public routing fields, request
history containing node attribution, raw HTTP logging, or packet capture. The
exact proof mechanics remain an implementation and runbook concern only when
they preserve these boundaries.

## Rationale

This is the smallest decision that composes two accepted, independently proven
paths without redefining either one. RFC-0031 already establishes that an
OpenAI-compatible client can enter a cluster-owned `chat` request without
making OpenAI protocol semantics part of routing. RFC-0039 and RFC-0040 already
establish repeatable operator-owned declarations and ordered ordinary static
remote collections. The ordinary remote request proof establishes that this
static path can reach a real receiver while preserving caller-owned attribution.

Using the existing compatibility command avoids a second user-facing access
command. Keeping `--declaration` optional preserves the local-only default and
makes multi-machine operation a visible operator action. Reusing the existing
declaration loading and static wiring avoids duplicate topology semantics,
configuration drift, and a second routing path.

The narrower approach is preferable to broadening the protocol: the user keeps
using an ordinary tool while the running cluster, not the tool, decides where
the `chat` capability executes.

## Alternatives considered

### Keep the compatibility process permanently local-only

Rejected. It leaves the strongest evidence-backed developer tool unable to
exercise the established ordinary static-cluster value. Repeating the existing
Aider proof would establish no new routing evidence.

### Add a separate static-cluster compatibility command

Rejected. A second command would duplicate process naming, defaults, validation,
documentation, and future compatibility behavior without adding a distinct
operator need. One optional explicit mode is smaller.

### Expose both native and compatibility endpoints from the static-cluster command

Rejected. It would make the ordinary static-cluster process own the
compatibility access contract and blur the separate edge boundary. It also
changes the established compatibility command rather than extending it
explicitly.

### Add inline remote-node arguments to the compatibility command

Rejected. RFC-0039 and RFC-0040 already establish declarations as the
repeatable topology source. Inline remote input would duplicate topology modes
and validation.

### Use environment variables for declaration selection

Rejected. Hidden input and precedence rules would make topology less explicit
and add configuration behavior absent from the accepted commands.

### Automatically discover a declaration

Rejected. Discovery, implicit file locations, and automatic topology selection
conflict with explicit operator control and would require a different
architecture.

### Add a generic named composition or profile system

Rejected. Two concrete modes are sufficient. A generic system would introduce
unearned configuration and lifecycle abstraction.

### Make the client select topology through `model` or another request field

Rejected. The RFC-0031 model field is an endpoint identifier, not a routing or
topology selector. Client-side topology input would violate capability-centered,
cluster-owned routing.

### Expose node attribution in the compatibility response

Rejected. The existing compatibility projection deliberately omits cluster
routing fields. A later proof can use internal or focused proof-only observation
without broadening the public contract.

### Implement fallback in the compatibility layer

Rejected. Fallback classification and candidate traversal are cluster-owned.
Duplicating them at the edge would create a second route and potentially send
requests directly to remotes.

### Expose the compatibility process on the trusted LAN

Rejected. Placeholder bearer behavior is not security. The compatibility edge
remains loopback-only; only the separately operator-controlled receiver may be
temporarily exposed on the trusted LAN.

### Add real authentication in the same RFC

Rejected. Authentication requires separate identity, credential, storage,
deployment, and security decisions and is not needed for the loopback proof.

### Broaden OpenAI compatibility to accommodate more tools

Rejected. Streaming, tools, model discovery, aliases, generation controls, and
other provider semantics remain unsupported by the cluster models and are not
required for the bounded Aider path.

## Trade-offs

The command gains one explicit optional startup input and associated validation
path. Operators who want an ordinary tool to reach a static cluster must supply
the same declaration they already own for ordinary static startup. That is more
manual than hidden configuration but preserves clarity and control.

The compatibility process remains deliberately limited: one loopback listener,
one fixed endpoint identifier, one `chat` capability, no client topology
selection, and no public routing attribution. This means it will not satisfy
tools that require streaming, tool calls, model listing, aliases, or broader
provider behavior.

Reusing the default static local composition in the declaration mode avoids
adding runtime options here, but it means operators needing another local
composition cannot infer support from this RFC. That limitation is intentional:
the current problem is static topology composition, not a general
compatibility-process configuration system.

## Impact

If accepted, a later implementation may modify the compatibility command and
application construction, focused command and compatibility tests, and
documentation needed to explain the new explicit mode. It may reuse existing
static declaration and wiring helpers.

It must not change core request or result models, runtime adapter interfaces,
the native endpoint, compatibility request or response models, routing
algorithms, fallback classification, remote transport protocol, declaration
format, receiver behavior, status semantics, lifecycle ownership, or the
compatibility network binding.

This RFC itself changes only architectural documentation. It does not activate
the new mode until a later implementation PR is reviewed and merged.

## Open questions

The following implementation details remain open and must be resolved without
broadening this decision:

- the smallest internal helper boundary that shares existing static construction
  without becoming a generic factory;
- the exact compact CLI wording for unreadable or invalid declarations, subject
  to accepted declaration error policy;
- how focused proof-only observation exposes the internally attributed remote
  result without retaining private request or topology data; and
- whether a later implementation's local default can directly reuse the
  existing default registry construction or must use the existing explicit local
  composition helper, while preserving the same observable local-only behavior.

The following remain outside this RFC and need separate evidence and, where
architectural, a separate RFC:

- runtime-selection options for the compatibility command;
- streaming, tools, model discovery, aliases, generation controls, and broader
  compatibility;
- real authentication, non-loopback compatibility access, or remote clients;
- lifecycle automation, discovery, scheduling, load balancing, or supervision;
- a generic composition, profile, or configuration framework; and
- any change to public compatibility response attribution.

## Decision

Accepted.

The existing no-argument `home-ai-cluster-openai-compatibility` command remains
the unchanged local-only default. The sole explicit static-cluster compatibility
mode is:

```text
home-ai-cluster-openai-compatibility --declaration <path>
```

It reuses RFC-0039/RFC-0040 declaration loading, validation, ordering, and
ordinary static-cluster construction. RFC-0031 compatibility protocol, loopback
binding, client topology blindness, routing and fallback ownership, lifecycle
and privacy boundaries, and public response shape remain unchanged.

This decision does not accept a generic composition framework, broader
OpenAI compatibility, LAN-facing compatibility access, authentication,
discovery, scheduling, supervision, or lifecycle automation.
