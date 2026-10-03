# RFC-0147: Loopback Static Routing Explanation Carrier

Status: Draft

Date: 2026-10-03

Author: frian

## Summary

Home AI Cluster should expose accepted RFC-0146 static routing explanation through one bounded loopback-only diagnostic carrier owned by the already-running ordinary process.

The carrier answers the RFC-0146 question against the effective ordinary caller composition actually serving that process:

> Given this caller's current effective composition, one accepted capability, and routing-relevant constraints, what routing facts can HAC truthfully determine before execution?

The ordinary process remains the owner of the active composition being explained. Core routing seams remain the owner of routing semantics. The carrier only projects those existing facts.

The carrier:

- performs no business request execution;
- requires no business payload;
- performs no runtime, remote, health, or availability probe;
- does not evaluate execution permission;
- does not reconstruct the caller from retained configuration;
- does not predict fallback, final attribution, or success;
- remains loopback-only;
- is not added to trusted-LAN authority;
- is not a browser UI feature;
- does not add a CLI;
- does not change RFC-0027 compatibility;
- does not widen RFC-0144's capability-only projection; and
- does not create a generic introspection or observability API.

This RFC accepts the carrier ownership and the minimum public diagnostic contract. Exact route spelling and concrete serialization details remain implementation choices unless they acquire semantic significance.

## Context

RFC-0146 accepts one bounded static-routing explanation authority for the effective ordinary caller composition.

RFC-0146 deliberately leaves its public carrier unresolved.

The accepted authority distinguishes static routing truth from execution truth. It may expose facts such as:

- requested capability;
- routing-relevant constraints;
- local candidate eligibility;
- eligible declared remotes;
- declared-remote priority order;
- accepted constraint exclusions;
- initial static selection; and
- existing static no-selection reasons.

It must not expose or predict execution-only facts such as:

- local execution permission;
- runtime availability at execution time;
- adapter invocation;
- remote transport invocation;
- receiver execution permission;
- consumed fallback;
- final node;
- terminal execution failure; or
- execution success.

The carrier therefore needs access to the exact active routing composition without itself becoming another source of routing truth.

### Current ordinary-process ownership

The ordinary local process stores its active local execution and routing composition in the running application.

The ordinary static-cluster process stores the same active local composition plus either:

- one static remote wiring; or
- one ordered static remote collection wiring.

These are the same active objects used by ordinary request handling.

RFC-0144 already demonstrates that one bounded projection can be derived directly from those active objects without reconstructing retained state. Its caller-routable capability projection reads the currently serving caller's active composition and exposes only capability membership.

RFC-0147 concerns a different and more explicit diagnostic projection, but the authority pattern is the same:

```text
active ordinary caller composition
        |
        v
existing routing authorities
        |
        v
bounded projection
```

### Existing standalone explanation commands

RFC-0027's `home-ai-cluster-explain-routing` command owns a different historical contract.

It constructs a synthetic local and declared-remote composition from explicit command inputs and explains that synthetic composition.

RFC-0146 narrows RFC-0027 accordingly:

- RFC-0027 remains authoritative for its explicitly constructed synthetic composition;
- RFC-0146 owns modern static explanation of the effective ordinary caller composition.

The current RFC-0027 launcher therefore cannot become an RFC-0146 carrier merely by reloading retained configuration or constructing another local composition.

RFC-0145's `home-ai-cluster-explain-request` command is also not the carrier needed here. It constructs and executes its own request composition and answers an actual-execution question.

### Existing loopback client precedent

RFC-0045 accepts a thin one-shot client for an already-running ordinary process rather than reconstructing the process's topology or orchestration in the client.

That precedent is relevant to any future convenience client for RFC-0147, but RFC-0147 does not accept such a client.

The first architectural decision is smaller:

> where must RFC-0146 truth be exposed so that it remains the truth of the active caller?

The answer is the ordinary process that owns that active caller composition.

## Problem

RFC-0146 is semantically complete but intentionally has no public carrier.

Without a carrier, an operator cannot ask the running ordinary process for its bounded static routing explanation.

Several superficially simple alternatives are architecturally wrong.

A separately launched command cannot reload retained configuration and claim that reconstructed state is the current caller.

A synthetic diagnostic command cannot substitute its own local and remote candidates for the caller's real composition.

A browser-only implementation would unnecessarily bind operator diagnosis to browser authority.

A trusted-LAN implementation would widen an explicitly closed LAN authority without demonstrated need.

Expanding RFC-0144's capability-only endpoint would violate that RFC's intentionally minimal information boundary.

The carrier must therefore expose the already accepted semantic authority without broadening unrelated surfaces.

## Goals

This RFC should:

- make RFC-0146 usable against one already-running ordinary caller;
- preserve the running ordinary process as owner of the effective composition being explained;
- preserve core routing code as owner of routing semantics;
- define one bounded loopback-only diagnostic public contract;
- use only RFC-0146 semantic inputs;
- expose only RFC-0146-approved static facts;
- fail closed when the active composition cannot be explained truthfully;
- avoid request execution, probing, retained-state reconstruction, and prediction;
- avoid widening RFC-0144;
- avoid widening trusted-LAN authority;
- avoid changing RFC-0027 compatibility;
- leave a future thin CLI as a separate decision; and
- remain small, explicit, capability-centered, and engine-independent.

## Non-goals

This RFC does not define or authorize:

- a CLI command;
- modernization of `home-ai-cluster-explain-routing`;
- retirement or renaming of RFC-0027 surfaces;
- browser UI;
- trusted-LAN access;
- receiver access;
- remote administration;
- remote diagnostic forwarding;
- retained configuration reconstruction;
- health or readiness reporting;
- runtime availability reporting;
- execution-permission reporting;
- execution or orchestration;
- fallback simulation;
- final-node prediction;
- execution-success prediction;
- runtime or model inspection;
- adapter or binding inspection;
- transport-address exposure;
- generic topology inspection;
- tracing;
- telemetry;
- monitoring;
- polling;
- history;
- persistence;
- scheduling;
- scoring;
- load balancing;
- discovery;
- a generic diagnostic framework;
- a generic introspection endpoint; or
- an OpenAI-compatible diagnostic contract.

It does not change routing, fallback, capability admission, execution accounting, request execution semantics, or existing business request APIs.

## Decision

### Ordinary process owns the carrier

The RFC-0146 carrier belongs to the already-running ordinary process that owns the effective caller composition being explained.

The carrier must derive its answer from that process's active in-memory ordinary routing composition.

It must not reconstruct equivalent state from retained configuration, startup defaults, command-line assumptions, files, environment variables, or another process.

Conceptually:

```text
operator
    |
    v
ordinary loopback process
    |
    +-- active local composition
    +-- active static remote wiring, if any
    |
    +-- existing routing authorities
    |
    `-- RFC-0146 projection
```

This does not make the HTTP application the owner of routing policy.

The ownership split remains:

```text
core routing seams
    -> own routing semantics

running ordinary process
    -> owns the effective composition being explained

RFC-0147 carrier
    -> exposes a bounded projection of that truth
```

### One loopback-only diagnostic surface

The ordinary process may expose one explicit local diagnostic request surface for RFC-0146.

The first carrier is loopback-only.

It is not exposed through:

- the trusted-LAN browser application;
- the receiver application;
- compatibility applications;
- remote node transport; or
- any independently bound administration listener.

This RFC does not authorize rebinding the diagnostic carrier to a non-loopback address.

The exact route path is an implementation detail provided that:

- the route is clearly diagnostic rather than an ordinary business request route;
- it belongs only to the ordinary loopback application authority;
- it is not added to receiver or trusted-LAN route sets; and
- it cannot be mistaken for an OpenAI-compatible endpoint.

### Diagnostic request inputs

The public request accepts only the semantic inputs already accepted by RFC-0146.

Conceptually:

```text
accepted capability
+
accepted routing-relevant constraints
```

For the current accepted routing architecture, the public constraint input needed by this carrier is `local_only`.

The carrier must not require:

- Chat messages;
- Summarize text;
- Classify text or labels;
- Code instructions;
- Image Generation instructions;
- source-grounded evidence;
- workspace paths or content;
- generated content; or
- any other business payload.

The carrier must not construct a fake executable request solely to satisfy an existing request model.

If implementation needs a payload-free internal routing-query representation, that representation must remain bounded to the already accepted RFC-0146 semantics and must not become a new general request abstraction.

### Accepted capability validation

The carrier accepts only capability names already admitted by HAC's accepted capability vocabulary.

Unknown or invalid capability input must fail before projection.

The carrier must not:

- infer capabilities from runtime or model metadata;
- admit arbitrary adapter capability strings;
- create dynamic capability discovery; or
- extend the capability vocabulary.

### Projection boundary

The response may expose only facts already permitted by RFC-0146.

At minimum, the carrier may represent:

- requested capability;
- supplied routing-relevant constraints;
- whether a local candidate is statically eligible;
- eligible declared-remote node IDs, when present, in existing declaration priority order;
- whether an accepted routing constraint excludes an otherwise eligible candidate family;
- the initial statically selected candidate, if one exists; and
- an existing bounded static no-selection reason, if ordinary routing already owns one.

The carrier may expose less than this set if implementation can remain useful while preserving the accepted semantic authority.

It must not expose facts outside RFC-0146 merely because they are available in process memory.

In particular, the response must not expose:

- prompt or business content;
- source text;
- file or workspace content;
- credentials;
- raw retained configuration;
- raw node objects;
- raw remote declarations;
- remote base URLs;
- transport addresses;
- IP addresses or hostnames;
- adapter identity;
- adapter instance;
- binding identity or configuration;
- runtime identity;
- model identity;
- health observations;
- readiness observations;
- execution cardinality state;
- execution history; or
- raw exception text.

### Local candidate identity

The public projection does not require a local node ID.

A local candidate may be represented only as the local candidate family and its eligibility/selectability state.

This keeps the first carrier focused on routing diagnosis rather than local topology inspection.

A later demonstrated need for stronger local identity requires separate architectural evaluation.

### Declared-remote identity and order

Minimal caller-owned declared-remote node IDs may be exposed when needed to distinguish multiple eligible remotes.

Their order must be exactly the existing caller-owned declaration priority order.

The carrier must not sort, score, rank, probe, or otherwise reorder declarations.

The exposed order means:

> these declared remotes are statically eligible in this caller-owned priority order

It must not mean:

> HAC will execute all of these remotes in this sequence

Actual continuation remains an execution-time fact.

### Initial selection

The carrier may expose the initial candidate selected by the existing ordinary static selection policy.

The carrier must reuse the existing selection authority.

It must not copy, reimplement, or approximate the selection policy in the HTTP layer.

Initial selection means only:

> this is the candidate selected before execution-time facts are evaluated

It does not predict:

- execution permission;
- runtime engagement;
- fallback;
- final attribution;
- success; or
- terminal failure.

### No execution

Handling the diagnostic request must not:

- execute a business request;
- invoke an adapter;
- invoke a runtime;
- invoke remote transport;
- enter execution cardinality;
- acquire execution permission;
- reserve execution capacity; or
- mutate ordinary execution state.

The carrier is read-only with respect to request execution.

### No probing

Handling the diagnostic request must perform no:

- adapter health check;
- runtime health check;
- model inventory query;
- remote HTTP request;
- receiver request;
- remote capability verification;
- network discovery;
- filesystem discovery;
- plugin or provider access; or
- status query used to strengthen routing claims.

The response is based only on already composed caller-owned routing state.

### No retained-state reconstruction

The carrier must not load retained configuration to determine the active caller's routing truth.

Retained state and active process state remain distinct.

A retained configuration change affecting future invocations does not need to alter the already-running caller's RFC-0147 explanation.

If the serving ordinary process cannot identify its active composition truthfully, the carrier must fail closed.

### Failure boundary

The carrier must fail closed rather than guess.

Invalid semantic input should be rejected as invalid diagnostic input.

If the serving process cannot truthfully derive the requested explanation from its active composition, the diagnostic request must fail without substituting:

- retained configuration;
- defaults;
- synthetic candidates;
- adapter capability inspection;
- runtime probing;
- remote probing; or
- browser assumptions.

The failure response must be bounded and must not expose raw internal exceptions or private configuration.

Exact HTTP status codes and field spelling are implementation details unless review shows they create semantic ambiguity.

This RFC does not create a general diagnostic failure taxonomy.

### Loopback authority

The first RFC-0147 carrier is available only through the ordinary loopback process authority.

This is an exposure decision, not merely a default bind choice.

The carrier must not automatically appear in trusted-LAN routes even though the trusted-LAN application may share references to the same underlying execution composition.

The accepted distinction remains:

```text
same execution composition
!=
same route authority
```

A future need to expose RFC-0146 diagnostics to trusted-LAN requires a separate architectural decision covering that trust and information boundary.

### Relationship to RFC-0144

RFC-0144 remains unchanged.

Its caller-routable capability projection remains capability-only and browser-oriented.

RFC-0147 must not add candidate identity, ordering, selection, or explanation fields to RFC-0144's existing projection.

The two surfaces answer different questions:

```text
RFC-0144
    Which capabilities are present on this caller's routing surface?

RFC-0147 / RFC-0146
    Why is one requested capability statically routable or not,
    and what static candidate/selection facts are authoritative now?
```

They may reuse common core eligibility seams, but neither projection may independently become a second router.

### Relationship to RFC-0145

RFC-0145 remains the actual-request lifecycle authority.

RFC-0147 exposes no actual execution facts.

The carrier must not predict or manufacture:

- execution permission;
- candidate engagement;
- adapter invocation;
- transport invocation;
- remote receiver refusal;
- continuation;
- consumed fallback;
- final attribution;
- terminal failure; or
- execution success.

An operator who needs to know what actually happened during a request must use the RFC-0145 authority, not infer it from RFC-0147 output.

### Relationship to RFC-0027

RFC-0027 remains unchanged by this RFC.

Its existing launcher continues to explain only its explicitly constructed synthetic composition according to its accepted historical contract.

RFC-0147 does not:

- modernize that launcher;
- change its arguments;
- make it a client of the ordinary process;
- rename it;
- retire it; or
- alias it to the new carrier.

A future compatibility decision may choose whether a thin command should consume RFC-0147 and whether that command should reuse or replace the historical launcher name.

That decision is explicitly deferred.

### No CLI yet

RFC-0147 does not add an operator command.

A future thin client may be justified if direct HTTP use proves unnecessarily awkward.

If later accepted, such a client should remain topology-blind and routing-blind:

```text
thin client
    -> one bounded local diagnostic request
    -> ordinary process-owned RFC-0147 carrier
```

It must not reconstruct routing state locally.

RFC-0045 is a useful precedent for that separation, but no CLI contract is accepted here.

### No browser UI

The loopback browser may coexist in the same ordinary application composition, but RFC-0147 does not add a browser control, page, panel, button, or JavaScript consumer.

This prevents the diagnostic authority from becoming a dashboard or from implicitly widening browser presentation scope.

A future browser consumer requires separate justification if it would expose additional operator detail through the browser.

### No trusted-LAN inheritance

The trusted-LAN application remains a separately closed route authority.

Sharing active composition objects with the ordinary process does not authorize sharing RFC-0147 routes.

No trusted-LAN URL, page, script, or capability route may gain RFC-0147 diagnostic access under this RFC.

### No generic diagnostic namespace

The carrier must remain specific to RFC-0146 static routing explanation.

Implementation must not use this work to establish a generic registry of diagnostics, arbitrary introspection queries, generic event projection, or an extensible observation framework.

A route prefix chosen for organizational reasons does not itself authorize future diagnostics.

Each materially new diagnostic authority still requires its own architectural justification.

## Privacy and security

The first carrier is loopback-only and read-only.

Its request contains no business payload.

Its response is bounded to caller-owned routing facts already permitted by RFC-0146.

The carrier must not expose:

- credentials;
- prompts;
- generated content;
- source documents;
- workspace content;
- remote URLs;
- private addresses;
- runtime or model metadata;
- raw retained state;
- raw bindings;
- raw adapters;
- health or readiness;
- execution state; or
- raw failures.

Constructing the response performs no network or runtime activity.

Because the first carrier is loopback-only, this RFC adds no new remote trust model.

Loopback reachability itself is not elevated into authentication for future stronger diagnostics.

## Compatibility

Existing ordinary request routes remain unchanged.

Existing RFC-0144 browser projection remains unchanged.

Existing trusted-LAN routes remain unchanged.

Existing receiver routes remain unchanged.

Existing RFC-0027 and RFC-0145 commands remain unchanged.

Existing retained configuration semantics remain unchanged.

Existing routing, selection, fallback, execution-permission, and result contracts remain unchanged.

No existing caller is required to consume the new diagnostic carrier.

## Rationale

The ordinary running process is the smallest truthful carrier because it already owns the exact composition being explained.

A separately launched command cannot obtain the same truth without contacting that process or constructing a different composition.

Using retained state would answer what a future or reconstructed invocation might look like, not what the active caller currently owns.

Using the loopback browser as the semantic owner would confuse a diagnostic authority with a UI boundary.

Using trusted-LAN would expose more routing structure across a network trust boundary without demonstrated need.

Adding a CLI at the same time would combine process authority with convenience-client design unnecessarily.

One loopback process-owned diagnostic carrier therefore gives RFC-0146 a truthful public home while preserving future freedom around operator presentation.

## Alternatives considered

### Modernize RFC-0027 immediately

Rejected for this RFC.

The historical launcher currently constructs and explains its own synthetic composition.

Changing it into a client of another running process would materially change its meaning and compatibility contract.

That may be reasonable later, but it is not required to establish the correct carrier.

### Extend RFC-0144

Rejected.

RFC-0144 deliberately exposes capability membership only.

Adding candidate identity, ordering, or selection would weaken its minimal browser boundary.

RFC-0147 should reuse underlying authorities, not widen RFC-0144's projection.

### Browser-only diagnostic

Rejected.

The browser can access the active composition, but the diagnostic is not inherently a browser capability.

Making the browser the only public carrier would tie operator diagnosis to UI ownership and presentation.

### Trusted-LAN diagnostic

Rejected for the first carrier.

The trusted-LAN application shares execution truth but owns a separately closed route set.

Exposing routing candidate IDs and order over LAN would require a separate trust-boundary decision.

### Reconstruct from retained configuration

Rejected.

Retained configuration is not active caller truth.

Startup overrides and process-local composition may differ.

A newly launched command may truthfully explain only the composition it itself constructs.

### Process carrier plus CLI in one step

Rejected as larger than necessary.

The process carrier is independently useful and establishes the correct authority boundary.

A thin CLI is convenience and compatibility policy that can be evaluated separately.

### No carrier

Rejected for now.

RFC-0146 exists to make a demonstrated bounded operator diagnostic possible, and the active process already provides a small truthful ownership seam.

Leaving the accepted authority permanently inaccessible would avoid a small public contract but would not serve the demonstrated diagnostic need.

## Expected implementation boundaries

A future implementation may decide:

- exact diagnostic route spelling;
- exact request and response model names;
- exact JSON field spelling;
- exact bounded HTTP failure codes;
- internal helper placement;
- whether a small payload-free query type is useful;
- exact test organization.

A future implementation must not decide without further architecture:

- trusted-LAN exposure;
- remote diagnostic access;
- browser UI;
- CLI behavior;
- RFC-0027 migration;
- broader topology detail;
- runtime/model detail;
- health/readiness;
- execution availability;
- generic introspection.

If implementation cannot expose the accepted carrier without duplicating routing policy or constructing synthetic executable requests, implementation should stop and return to architecture.

## Proof requirements

A future implementation should prove at least:

1. the carrier reads the active local ordinary composition rather than retained configuration;
2. the carrier reads active single-remote static wiring when present;
3. the carrier reads active ordered remote collection wiring when present;
4. local eligibility preserves existing binding and caller-local restrictions;
5. declared-remote eligibility preserves existing capability semantics;
6. multiple eligible remotes preserve declaration priority order;
7. `local_only` excludes remote selectability without erasing static capability eligibility;
8. initial selection reuses existing selection authority;
9. no business request is executed;
10. no fake Chat or other synthetic business payload is constructed;
11. no execution-permission operation occurs;
12. no runtime or network probe occurs;
13. retained configuration is not loaded to reconstruct active truth;
14. invalid capability input fails closed;
15. unavailable active composition fails closed;
16. remote node IDs may be exposed while URLs and addresses remain absent;
17. local binding, adapter, runtime, and model details remain absent;
18. RFC-0144 output remains unchanged;
19. RFC-0145 behavior remains unchanged;
20. RFC-0027 behavior remains unchanged;
21. trusted-LAN exposes no RFC-0147 route;
22. receiver authority exposes no RFC-0147 route;
23. ordinary routing and fallback semantics remain unchanged.

## Open questions

The following remain intentionally deferred:

- Should a later thin CLI consume this carrier?
- If so, should it use a new launcher or explicitly migrate the RFC-0027 launcher?
- What exact diagnostic route spelling should implementation use?
- What exact JSON field names should the request and response use?
- Should a future browser operator view consume the same carrier?
- Is there ever a justified trusted-LAN diagnostic subset?
- Which bounded static no-selection reasons should be projected publicly if the existing internal taxonomy contains more detail than the first carrier needs?

These questions do not change the carrier ownership decision accepted by this RFC.

## Decision

Pending.
