# Post-RFC-0064 External Information Access Investigation

Status: Complete

## Question

> After RFC-0064 rejected project-owned arbitrary public-URL retrieval, is
> there a different small, useful, and defensible boundary through which Home
> AI Cluster could obtain external public information without giving runtimes
> direct Internet authority, weakening privacy-first defaults, or building a
> generic retrieval, tool, or agent framework?

This is a documentation-only investigation. It does not authorize an external
information feature, an RFC, a dependency, a provider, a capability, a network
operation, a protocol, or an implementation.

## Outcome

**Outcome A — no new project-owned external-information boundary is currently
justified. Keep retrieval operator-owned.**

The existing workflow is already small, explicit, and useful:

```text
operator/browser/curl/other local tool
  -> bounded local UTF-8 text, regular file, or stdin
  -> existing HAC input
  -> existing routing and execution
```

RFC-0064 rules out the seemingly nearby alternative of HAC fetching an
arbitrary public URL. A fixed external provider avoids that particular
user-controlled-destination shape, but replaces it with explicit cloud
dependency, query disclosure, credential, result-trust, and provenance
decisions. An operator helper or service is either the current workflow under a
different name, or a new durable boundary that has not earned its complexity.
No candidate now supplies enough additional ordinary operator value to justify
those project-owned authorities.

## Scope and distinction

This investigation considers only **external information acquisition**: how
bounded current or public information could reach HAC at all.

It does not decide **automatic retrieval decision**: whether a model or host
should infer that a request needs external information. In particular, it does
not define tool calls, automatic triggers, keyword heuristics, model-selected
URLs, autonomous loops, repeated search, stopping policies, or action history.
Those are deferred unless a future accepted decision first establishes a
defensible acquisition primitive.

External information access is not thereby a new executable capability. The
accepted capability vocabulary remains `chat`, `summarize`, `classify`, and
`code`; this investigation does not create a vague `web`, `browse`,
`research`, or `retrieve` capability.

## Current main baseline

This investigation reviewed GitHub `main` at commit
`1c3b9c188b5f512e607c480a5a0f4e0e2f52a5e1`.

### Existing input and network authority

The ordinary native Summarize command already accepts exactly one bounded,
strict-UTF-8 source through `--text`, an opened regular `--file`, or stdin. It
constructs the existing `SummarizeRequest` only after local input validation.
Classify likewise consumes bounded caller-provided text. These paths make the
operator-owned workflow practical without a new source abstraction.

The runtime adapters contact only their explicitly configured Ollama or
llama-server runtime addresses. Static remote transport contacts explicitly
declared cluster receivers, and ordinary native commands contact their fixed
loopback HAC endpoint. None of these paths is public-information retrieval;
runtime adapters and selected execution nodes do not receive an arbitrary URL,
query, or Internet-retrieval authority. Routing therefore does not choose an
Internet egress identity or turn a remote node into a web gateway.

`pyproject.toml` still lists HTTPX as the only direct HTTP-client dependency.
No tracked lock file, dependency, or supported transport seam on current main
changes the RFC-0064 hostname finding. The existing HTTPX investigation's
version-specific observations are historical evidence, but its material
conclusion remains unchanged: the documented high-level hostname path cannot
prove that validation of hostname answers controls the peer actually connected
while preserving normal hostname, TLS certificate, and SNI semantics.

### RFC-0064 is governing rejected evidence

RFC-0064 is **Rejected**, not awaiting acceptance. It proposed one explicit,
caller-local public-URL input before the existing bounded Summarize path. Its
rejection records that the documented high-level HTTPX route could not prove
the required hostname-to-connected-public-peer invariant. Checking DNS answers
before `Client.get()` leaves a validation-to-connect gap; the documented API
does not provide a supported address-pinning or peer-validation mechanism that
also retains ordinary hostname HTTPS and SNI behavior.

The supporting investigation found a technically narrower form—public literal
IPv4 or IPv6, identity `text/plain`, no redirects, isolated client, and finite
inactivity and byte limits. RFC-0064 rejected that too: literal-IP URLs,
IP-valid certificates, and plain text are too limited for ordinary operator
value. No public-URL command, endpoint, capability, runtime-adapter operation,
remote-node behavior, browser surface, dependency, or implementation was
authorized.

The rejection is architectural evidence, not an invitation to re-propose
arbitrary URL retrieval for convenience.

## Candidate comparison

### 1. Operator-owned retrieval — current baseline

```text
operator-controlled browser, curl, or other tool
  -> operator-reviewed bounded text/file/stdin
  -> HAC
```

- **User value, control, and local-first fit:** It is immediately useful for
  any source an operator can access. It has manual-copy friction, but existing
  bounded file and stdin surfaces reduce that friction. The operator chooses
  the tool, destination, account, and material to submit; HAC remains fully
  usable without an Internet connection or account.
- **Authority, privacy, and safety:** HAC has no project-owned Internet
  authority, no SSRF or private-network exposure, no provider credential, and
  no cloud dependency. The operator's retrieval tool and its privacy policy
  remain outside HAC. Submitted text remains untrusted input and is not
  automatically retained by this workflow.
- **Ownership and coupling:** HAC owns the already-normalized bounded input and
  existing result only. It owns neither source retrieval nor provenance. There
  is no provider coupling, no runtime-adapter impact, and no topology or route
  change.
- **Cost and decision:** It needs no persistence/history, new implementation,
  or RFC, and has negligible overengineering risk. No repository change is
  justified merely to rename or wrap it.

### 2. Project-owned arbitrary public URL retrieval

```text
explicit URL
  -> HAC public-destination retrieval
  -> bounded text
  -> HAC
```

- **User value, control, and local-first fit:** A single command would reduce
  copying for a chosen URL, but it remains an explicit cloud-network exception
  rather than ordinary local-first operation. The URL selects the destination,
  so operator intent does not remove HAC's security responsibility.
- **Authority, privacy, and safety:** This gives HAC project-owned egress to a
  user-controlled destination. It exposes SSRF/private-network, DNS,
  redirect, resource, untrusted-content, and destination-privacy concerns.
  It need not require credentials, but safely excluding ambient credentials,
  proxies, cookies, and other inherited authority is itself part of the
  boundary.
- **Ownership and coupling:** Caller-local acquisition would preserve adapter
  and routing boundaries by passing normalized text only. Retrieval on an
  execution node would not: it would make routing change egress identity and
  give adapters/remotes retrieval authority. Source/result normalization,
  failure presentation, and minimal provenance would become HAC-owned; citations
  would be necessary if the feature claimed source support rather than merely
  input origin.
- **Cost and decision:** It requires an RFC and substantial focused security
  evidence. RFC-0064 establishes that the ordinary hostname form is blocked,
  while its safe literal-IP narrowing lacks sufficient value. It adds no
  justified persistence/history need, but its implementation complexity and
  overengineering risk are high. This candidate remains blocked.

### 3. Fixed external information provider boundary

```text
explicit information query
  -> one known or explicitly configured provider
  -> bounded structured results
  -> HAC-owned normalized representation
```

- **User value, control, and local-first fit:** A provider can offer current
  information with less manual acquisition. However, it is an account- and
  Internet-dependent opt-in exception, not a local-first default. The operator
  must explicitly allow the provider, its destination, its cost, and the query
  disclosure; a model must not select that provider or invoke it on its own.
- **Authority, privacy, and safety:** Removing a user-controlled destination
  materially reduces the RFC-0064 SSRF/destination problem at HAC's own egress:
  HAC could be limited to one provider endpoint. It does not remove risk; the
  query itself may be sensitive, the provider performs the wider retrieval,
  and returned content and source links are untrusted. HAC must still bound its
  one provider response, isolate its credential, and define its configured
  endpoint and failure behavior.
- **Ownership and coupling:** This needs an API key or comparable credential,
  provider lifecycle and availability handling, and provider-specific request
  and response adaptation. A representative current API documents a required
  bearer API key, a query request, ranked results with URLs and content, optional
  provider-generated answers, and usage credits; these are evidence of the
  credential, trust, normalization, cost, and provenance questions, not a
  provider recommendation. [Tavily Search API](https://docs.tavily.com/documentation/api-reference/endpoint/search)
  and [API introduction](https://docs.tavily.com/documentation/api-reference/introduction).
  HAC would need to own a bounded normalized result and decide whether it
  carries result URLs/titles as provenance. Once sources affect a user-visible
  answer, explicit provenance or citations become a likely requirement rather
  than optional decoration. This is provider coupling, though it need not be
  runtime-engine coupling if acquisition stays caller-local and adapters receive
  only normalized text.
- **Cost and decision:** No routing or topology change is acceptable; provider
  acquisition must complete before routing. It adds no inherent need for
  history, but credentials, configuration, usage/billing, key storage, result
  limits, and provider failure semantics are durable architecture. A generic
  provider abstraction before one concrete accepted use would overengineer it.
  A provider-specific future RFC would be required, but no concrete provider
  use case currently justifies one.

### 4. Operator-owned or caller-owned retrieval helper

```text
operator-owned helper
  -> retrieval under the helper's explicit authority
  -> bounded normalized text/data
  -> HAC existing input
```

- **User value, control, and local-first fit:** If the operator runs a helper
  and pipes or writes its output into HAC, it is the current baseline with
  potentially better local ergonomics. HAC remains offline-capable and the
  operator owns the helper, destination, credentials, and retrieval policy.
- **Authority, privacy, and safety:** In that form HAC has no egress, SSRF
  exposure, credential, or cloud dependency. The helper, not the runtime or
  selected node, owns network access, untrusted source handling, and failures.
  If HAC launches or controls the helper, however, HAC gains indirect Internet
  authority and the same privacy and trust questions return.
- **Ownership and coupling:** Existing text/file/stdin paths already own the
  only normalized HAC input needed. A helper protocol would need to define
  process ownership, invocation, result bounds, error categories, credentials,
  provenance, versioning, and trust. That would couple HAC to a helper contract
  without benefiting runtime adapters, routing, or topology.
- **Cost and decision:** A purely external helper needs no HAC persistence,
  implementation, or RFC; documenting one particular tool is not currently
  necessary. A HAC-managed helper protocol would require an RFC and has high
  premature-abstraction risk. It is not a distinct project-owned boundary worth
  adding now.

### 5. Fixed operator-owned retrieval service

```text
explicit HAC caller
  -> explicitly configured trusted retrieval service
  -> bounded result
  -> HAC
```

- **User value, control, and local-first fit:** A trusted local service could
  centralize an operator's chosen egress and policy. It may improve control for
  an operator who already maintains such a service, but it does not make the
  ordinary single-user workflow simpler and introduces another service to run.
- **Authority, privacy, and safety:** A fixed service reduces arbitrary
  destinations at HAC's direct network edge, but the service still needs an
  explicit Internet and SSRF policy. Queries/content cross the caller-service
  trust boundary; secrets and request metadata need an explicit privacy model.
  HAC must never silently use it or delegate authority to runtimes.
- **Ownership and coupling:** HAC would need a durable configuration and
  request/result contract, authentication/credential handling, bounded
  normalization, failure ownership, and source provenance policy. Acquisition
  could remain caller-local before model routing, so adapters and selected nodes
  need no change; making it route-selected would violate the egress/topology
  boundary. The service creates operator-service coupling but should not create
  runtime-engine coupling.
- **Cost and decision:** It adds lifecycle, configuration, availability, and
  likely support burden without a need for persistence/history in HAC itself.
  It would require an RFC and has high infrastructure/overengineering risk.
  Self-hosting another service is not justified merely because it is possible.

## Boundary tests retained by this outcome

The outcome preserves these project principles:

- A model has no arbitrary network authority.
- Runtime adapters do not become HTTP or browser clients for public
  information.
- Route selection does not change Internet egress identity, visibility, or
  reachable resources.
- Acquisition, normalized input, and model generation remain separate concepts.
- Any future network operation must be explicit and finite; Chat does not
  browse merely because it decides that browsing might help.
- No cache, history, database, telemetry, browser engine, crawler, scraper,
  generic tool framework, generic provider abstraction, or OpenAI-compatible
  tool/function-calling extension follows from this investigation.

## What would change this conclusion

This conclusion is deliberately not a permanent prohibition. A later
investigation could establish a focused case for a future RFC only by showing a
concrete operator problem that current input paths do not serve, a narrowly
bounded non-arbitrary acquisition authority, explicit opt-in privacy and
credential ownership, provider or service lifecycle consequences, normalized
untrusted-result and provenance requirements, and unchanged runtime/routing
boundaries. It must not use automatic or model-directed retrieval as a reason
to skip those questions.

Until then, external/operator retrieval followed by bounded local text, file,
or stdin remains the smallest defensible boundary.
