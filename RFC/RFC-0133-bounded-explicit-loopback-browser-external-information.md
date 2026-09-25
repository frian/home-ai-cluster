# RFC-0133: Bounded Explicit Loopback Browser External Information

Status: Accepted

Date: 2026-09-18

Author: frian

## Summary

This RFC proposes one explicit External Information operation in the existing
ordinary/native loopback browser application.  A human supplies a distinct
acquisition `QUERY` and source-grounded Chat `QUESTION`, optionally overrides
the retained RFC-0095 exact plugin name, and explicitly submits the operation.
Only then may the already-running ordinary process resolve that exact name,
inspect the RFC-0078 entry-point group, lazy-load one selected trusted plugin,
invoke it once, reconstruct fresh RFC-0077 evidence, and execute one ordinary
source-grounded Chat operation.

```text
human External Information submission
        -> one same-origin loopback browser operation
        -> one exact selected RFC-0078 plugin
        -> one acquisition with QUERY
        -> fresh RFC-0077 evidence and QUESTION
        -> ordinary capability=chat routing
        -> generated content plus supplied-source provenance
```

This deliberately and narrowly amends the plugin invocation-location rules of
RFC-0078, RFC-0079, and RFC-0093 for this one browser operation.  It does not
turn ordinary server startup, Configuration, ordinary browser Chat, `/v1/chat`,
or any other capability handling into plugin authority.  It does not add an
executable capability, a general acquisition API, a generic plugin system, or
trusted-LAN/receiver acquisition.

## Context

RFC-0077 accepts bounded source-grounded Chat while deliberately excluding
browser behavior and acquisition.  RFC-0078 places acquisition in a distinct
one-shot `hac external-information` caller process: that caller chooses one
exact installed plugin, discovers and lazy-loads it only for the explicit
operation, invokes it once with a query, reconstructs RFC-0077 evidence, and
then calls the existing source-grounded Chat boundary.  RFC-0091 keeps the
operation concise; RFC-0095 allows a retained exact plugin name only as a
baseline for an explicit operation.  RFC-0079 and RFC-0093 remain the separate
provider-specific decisions.

RFC-0096's bounded automatic external-information fallback is limited to
native one-shot Chat and expressly excludes browser Chat.  RFC-0062 and its
successors establish a fixed same-origin ordinary loopback browser.  RFC-0130
establishes a different trusted-LAN capability-only browser authority and
deliberately does not grant it Configuration or other loopback-only authority.
RFC-0132 permits loopback Configuration to read and set the retained plugin
choice, but correctly gives those reads and mutations no acquisition effect.

The current implementation reflects these accepted boundaries: the CLI caller
performs RFC-0078 entry-point work, while the ordinary browser has no External
Information operation.  That implementation fact does not itself decide
whether browser acquisition is appropriate.  Exposing it is a new authority
decision and must be explicit.

## Problem

HAC has one explicit external-information caller edge, but an operator using
the ordinary loopback Web UI cannot make that same bounded operation.  Calling
`/v1/chat/sources` from the browser would only submit manually supplied
evidence; it supplies no RFC-0078 acquisition mechanism.  Making browser Chat
acquire sources automatically would be a materially broader disclosure and
browser-authority decision.

The smallest useful exception is therefore one separately visible, explicitly
submitted loopback-browser operation that preserves the existing acquisition
and source-grounding ordering without granting general server plugin authority.

## Goals

- Add one fixed External Information view only to the ordinary/native loopback
  browser application.
- Preserve explicit, exact RFC-0078/RFC-0095 plugin selection and one-call
  acquisition semantics.
- Keep `QUERY` and `QUESTION` visibly distinct and directed to their existing
  different recipients.
- Reuse fresh complete RFC-0077 validation and ordinary `chat` routing.
- Preserve exact native Host and same-origin mutation authority.
- Keep results ephemeral and present generated content separately from supplied
  source provenance.
- Apply a bounded confirmed-disconnect cancellation and result-abandonment rule
  to the whole HAC-owned browser operation.
- Preserve zero-activity behavior unless a person submits this operation.

## Non-goals

This RFC does not authorize automatic or conditional browser Chat acquisition;
interactive Chat CLI acquisition; query rewriting or model-generated queries;
retries, fallback plugins, repeated research, streaming, pagination,
background work, polling, scheduling, caching, or history.

It does not add an `external-information`, `web`, `search`, `browse`,
`retrieve`, or `research` capability; static capability declarations; adapter
claims; remote-node configuration; a receiver acquisition protocol; or routing
influence from plugin/provider identity.  Acquisition remains a caller/browser
edge, and actual execution remains ordinary `chat`.

It does not add a generic server acquisition API, plugin dropdown/listing,
plugin manager, lifecycle/status/configuration API, provider framework,
secrets UI, provider configuration, health probing, credentials, provider
metadata, arbitrary URL retrieval, result-URL following, crawler, browser,
scraper, sandbox, subprocess, IPC, worker, timeout runner, or generic task
manager.  Returned URLs remain provenance strings, not HAC fetch authority.

It does not widen trusted-LAN browser authority, receiver authority,
OpenAI-compatible APIs, remote administration, or Configuration semantics.
It introduces no dependency, persistence, database, or provider-specific
configuration.

## Proposal

### One explicit native-loopback operation

The ordinary/native loopback browser may add one fixed **External Information**
view, separate from ordinary Chat.  Its form has exactly:

- an optional exact plugin-name override;
- required acquisition `QUERY`;
- required source-grounded Chat `QUESTION`; and
- one explicit submit action.

The operator must be able to see that `QUERY` and `QUESTION` are distinct.
There is no “search automatically” Chat option, same-as-query rule, query
derivation, model query generation, or repeated research.  Route URI, HTML,
CSS, JavaScript names, and exact success/failure HTTP status spelling are
implementation details where they do not affect this authority.

The operation is a bounded same-origin browser-facade request, not a new stable
general native API.  It is available only after a human uses that explicit
native-loopback control.  The current-page UI may reuse its existing browser-
wide foreground request gate so that page does not intentionally overlap its
own capability and External Information submissions.  That is page-local
presentation behavior, not a server-global concurrency guarantee.

### Narrow amendment to RFC-0078

RFC-0078 remains authoritative except for this precise additional caller edge.
Its statement that acquisition belongs only in a distinct one-shot caller
process is amended as follows:

> The ordinary/native loopback browser facade may own one explicit browser
> acquisition operation.  Only after its bounded same-origin request reaches
> that operation may the ordinary HAC process resolve the effective exact
> plugin selection, inspect the one RFC-0078 entry-point group, lazy-load the
> selected plugin, invoke its existing asynchronous acquisition callable once,
> reconstruct and validate RFC-0077 evidence, and execute one source-grounded
> Chat operation.

This permission belongs only to that browser operation.  HAC must perform no
plugin metadata discovery, import, credential access, provider access, or
network acquisition merely because HAC starts, a plugin is installed, a
retained plugin value exists, Configuration is read or written, ordinary
browser Chat runs, `/v1/chat` runs, or another capability runs.

Unlike the short-lived CLI caller, the trusted plugin runs in the already
running ordinary HAC process and its module may remain imported until that
process exits.  This is an accepted bounded usability trade-off.  It does not
claim unloading, isolation, sandboxing, process restart, IPC, or forced
cancellation.  RFC-0078's operator-installed trusted-Python-code boundary
remains authoritative; HAC invokes the selected callable once per explicit
submission and never schedules it as repeated/background work.

### Corresponding provider-specific invocation location

This same narrow exception amends only the invocation-location portions of
RFC-0079 and RFC-0093, as well as RFC-0078, for one accepted explicit
ordinary/native loopback browser operation.  It does not generally supersede
those RFCs:

```text
historical `hac external-information` operation
        -> plugin executes in its one-shot caller process

RFC-0133 explicit loopback-browser operation
        -> plugin executes in the already-running ordinary HAC process
           handling that explicitly authorized browser operation
```

For that browser operation only, the selected RFC-0079 SearXNG plugin may be
discovered, lazy-loaded, and invoked in the ordinary process after the explicit
native-loopback action is accepted.  It retains RFC-0079's one fixed literal
loopback destination, exact request shape, transport limits, disabled redirects,
deterministic normalization, no retry/pagination/result-URL fetch, and
operator-owned SearXNG lifecycle.  This is not generic ordinary-process
SearXNG authority: without an explicit browser submission, startup,
Configuration, ordinary browser Chat, and other capabilities do not discover,
import, or invoke it.

For that browser operation only, the selected RFC-0093 Tavily plugin executes
in the ordinary HAC process and therefore reads its nonblank `TAVILY_API_KEY`
directly from that process environment when `acquire()` is invoked.  The
historical CLI path remains unchanged: its plugin reads the key from the
one-shot `hac external-information` caller process environment.  RFC-0133 does
not copy a CLI environment into the server, forward/inject a per-request
environment, reload an environment, or add a keyring/config-file/OAuth
alternative.  A browser Tavily operation can succeed only when the already
running ordinary HAC process has the plugin-required key under RFC-0093's
existing environment-variable mechanism.

HAC core and the browser protocol do not read, parse, accept, transfer, retain,
return, log, persist, or expose that key.  The browser has no credential field
or credential input; Configuration has no credential; the key does not enter
routing, remote transport, RFC-0077 evidence, or results.  If it is missing,
blank, malformed, rejected, or otherwise unusable in the ordinary process
environment, the existing RFC-0078/RFC-0093 privacy-safe
`external-information-acquisition-failed` result applies, without another
plugin, ordinary-Chat fallback, prompt, or configuration mutation.

RFC-0079 and RFC-0093 otherwise remain authoritative for their provider
contracts: package and entry-point identity, fixed destination, exact query and
provider request, transport and proxy/environment HTTP-client isolation,
response bounds, normalization, candidate field limits, no provider metadata
across the plugin boundary, no result URL fetch, no retry/pagination/alternate
provider, privacy-safe failure, lifecycle ownership, and no generic provider
framework.  RFC-0133 changes only this explicit browser operation's invocation
location and its direct process-local state/environment credential consequence.

### Selection, input, and acquisition semantics

Effective selection extends RFC-0095 only to this explicit browser operation:

```text
explicit nonblank valid browser override -> resolve that exact name only
blank/no browser override                -> resolve retained RFC-0095 exact name
blank/no override and no retained name   -> fail before discovery/import/network
```

An explicit valid override never consults retained plugin selection merely to
choose a plugin and never mutates retained configuration.  When retained
selection is required but is malformed or unavailable, HAC must not repair,
infer, or replace it; the operation fails before plugin discovery, import, or
provider activity under the existing retained-configuration safety boundary.
This selection clarification does not make malformed unrelated configuration
generally ignorable.  HAC must not infer a sole installed plugin, a provider
from credentials, a default, a healthy provider, or a fallback.  The UI accepts
optional exact text only; it must not discover or enumerate plugins to populate
a dropdown.  Explicit names retain RFC-0078's nonblank maximum-64-UTF-8-byte
entry-point-name contract in
`home_ai_cluster.external_information_acquisition.v1`; configuration-time
retained-name rules remain RFC-0095's responsibility.

`QUERY` is exactly the RFC-0078 plugin input: it is operator supplied,
nonblank, at most 4,096 UTF-8 bytes, unrewritten, sent only to the selected
plugin, and used for exactly one acquisition call.  Equivalent local form
validation may improve feedback, but server validation is authoritative.

`QUESTION` is exactly the later RFC-0077 source-grounded Chat question.  It
is not sent to the plugin, combined with `QUERY`, or automatically derived.
The established ordering remains:

```text
selected plugin + valid QUERY
        -> one acquisition
        -> candidate reconstruction
        -> SourceGroundedChatRequest(QUESTION, evidence)
        -> complete RFC-0077 validation
        -> one ordinary source-grounded Chat operation
```

This adds no new global pre-acquisition question-validation rule.  The existing
plugin callable contract remains `async acquire(query: str) -> list[dict[str,
str]]`, including RFC-0078's closed candidate representation and all its
failure semantics.  Exactly one selected entry point may be discovered and
loaded, exactly once invoked, and its candidates must construct fresh
`SourceEvidence` values and a fresh `SourceGroundedChatRequest`.  No malformed
candidate may reach routing, remote transport, or an adapter.

### Source-grounded execution and presentation

After successful reconstruction, HAC performs exactly one existing
source-grounded Chat operation.  RFC-0077's ordinary Chat routing eligibility,
local-first behavior, declared-remote order/fallback, caller-local static
permission, remote source-grounded transport, execution attribution, and
evidence disclosure semantics remain unchanged.  A selected plugin executes
caller-locally in the ordinary process before routing; its identity cannot
affect node, runtime, model, or capability selection.  If normal Chat routing
selects a declared trusted remote, only the normalized RFC-0077 question and
evidence cross that existing boundary.

The successful browser result keeps generated content and supplied-source
provenance structurally distinct.  It may show ordinary execution attribution
and ordered source title, URL provenance string, and bounded content snippet.
It must label these as supplied sources/source evidence, not verified
citations, and must not claim a source is true, current, used, or supports a
particular sentence.  URLs are inert plain text: HAC does not fetch, preview,
resolve, enrich, or follow them.

HAC-owned browser/server-facade state is ephemeral.  RFC-0133 introduces no
HAC-owned query, question, source, or result history; cache; database;
localStorage/session storage; or retained External Information execution state.
HAC must not deliberately retain `QUERY`, `QUESTION`, acquired sources, or a
result after the request beyond existing transient execution ownership.

This does not promise that arbitrary trusted plugin code cannot retain memory.
The acquisition plugin is operator-installed trusted Python; because it runs
in the long-lived ordinary process, its imported module and plugin-owned Python
state may remain resident until process exit.  RFC-0133 does not inspect,
scrub, unload, reset, sandbox, or otherwise control arbitrary plugin-owned
in-process state, and does not normalize it into HAC retained configuration.
RFC-0078's package-installation trust decision and provider/plugin-specific
contracts remain authoritative.

### Independent operation concurrency

RFC-0133 adds no process-global External Information scheduler, mutex, queue,
semaphore, or one-at-a-time acquisition authority.  Independently submitted
valid loopback operations, including from another tab or client, may be in
flight concurrently.  Each independently resolves one exact plugin selection,
invokes one callable once, reconstructs one RFC-0077 request, and performs at
most one source-grounded Chat execution, without retry or loop.

This RFC neither makes a trusted plugin thread-safe/reentrant nor introduces
generic concurrency management.  The operator-installed trusted-code boundary
remains authoritative.

### Browser authority and structural exclusions

Because this operation can disclose a query to a plugin/provider and trigger
external network/service activity, it requires exact accepted native Host,
exact same-origin Origin, and bounded `application/json` non-simple request
authority.  The effective native authority is independently derived from the
native listener; attacker-controlled Host and Origin values must not validate
one another.  There is no CORS, login, account, session, token, OAuth, TLS, or
generic browser authentication.  This boundary is not authentication against
an already compromised or fully capable local process.

RFC-0130 remains unchanged.  Its trusted-LAN application has no External
Information view, acquisition route, retained-plugin acquisition action, or
plugin/provider authority.  A LAN peer may not trigger external disclosure
merely for UI symmetry: RFC-0130 granted capability use, not this external
activity.  A later RFC may decide LAN authority separately.

Receiver authority likewise has no browser acquisition route, plugin discovery,
plugin invocation, or provider/network authority.  It receives only the
existing normalized RFC-0077 source-grounded Chat transport after caller-local
acquisition has succeeded and ordinary routing selects that remote.  No
acquisition protocol is added to receiver transport.

### Failure, disconnect, and zero-activity behavior

Invalid request shape, invalid explicit name, missing effective selection, or
invalid `QUERY` fail before plugin discovery, import, credential/provider
access, or network activity.  Selected-plugin discovery, loading,
configuration, callable, return-shape, or acquisition failures normalize to
the existing privacy-safe `external-information-acquisition-failed` semantic
failure.  They reveal no query, credential, endpoint, provider identity,
plugin/import detail, raw response, exception, stack trace, or private
topology; do not try another plugin; and never silently continue as ordinary
Chat.  Once a valid source-grounded request exists, RFC-0077 and ordinary Chat
execution failure ownership remains authoritative.

After an accepted browser request, HAC owns one foreground operation:

```text
acquisition -> RFC-0077 reconstruction -> source-grounded Chat
```

RFC-0082 does not automatically cover this new acquisition route, so this RFC
extends its bounded abandoned-request principle to that complete HAC-owned
operation.  If the HTTP edge confirms client disconnect while the operation is
pending, disconnect wins: HAC abandons the operation, propagates ordinary
asynchronous cancellation through work it owns best-effort, discards every
later acquisition success or failure, and must not begin source-grounded Chat.
It must not retry, select another plugin, fall back to ordinary Chat, or create
background continuation authority.  If a terminal operation result is already
owned before disconnect wins, normal completion retains RFC-0082's existing
completion-versus-disconnect precedence.

This is HAC-side best-effort cancellation and result abandonment, not rollback
of external effects.  It cannot retract a `QUERY` already disclosed, cancel a
provider request already observed externally, forcibly terminate arbitrary
trusted Python, unload a plugin module, kill a thread/process, or guarantee
provider-side termination.  Once source-grounded routable execution begins,
RFC-0082's accepted ordinary execution semantics apply.

The RFC adds no generic plugin timeout or forced-cancellation mechanism.
RFC-0078's plugin-owned finite provider transport limits remain authoritative.
There is no cancellation endpoint, job ID, deadline, worker, subprocess, or
new timeout architecture.

When no explicit External Information submission occurs, startup, retained
plugin presence, Configuration reads/writes, ordinary browser Chat, other
browser capabilities, and ordinary HAC requests perform no plugin discovery,
import, credential/provider access, or provider/service network activity.  If
zero plugins are installed, the view may exist but a submitted operation fails
safely through the existing missing-plugin boundary; no other behavior changes.

## Rationale

The loopback browser is an established native operator facade.  Making one
separate action explicit preserves the key consent boundary: the operator can
see both the exact external query and the later question before initiating
provider activity.  Reusing RFC-0078's narrow plugin input and RFC-0077's
complete reconstruction avoids creating a second evidence, routing, or
provider contract.

Keeping the action out of ordinary Chat avoids treating a UI convenience as
authority to classify, disclose, or acquire automatically.  Keeping trusted
LAN excluded recognizes that another household device and network path have
not yet been granted the ability to cause external disclosure.  The one
in-process exception is smaller than inventing process lifecycle and IPC solely
to recreate the CLI boundary, provided its trusted-code lifetime consequence
is stated honestly.

## Alternatives considered

### Keep external information CLI-only

Rejected.  It preserves RFC-0078's caller-process location exactly, but does
not provide the requested explicit loopback Web operation.

### Browser directly calls `/v1/chat/sources`

Rejected.  That route accepts supplied evidence; it offers no RFC-0078
acquisition and would require manually supplied sources instead.

### Generic server acquisition API or plugin UI

Rejected.  A public/general endpoint, listing UI, or provider framework would
turn the narrow category-specific boundary into ongoing server plugin/provider
authority and weaken installation-versus-selection separation.

### Run `hac external-information` as a subprocess per submission

Rejected for this first step.  It adds subprocess lifecycle, IPC, output
translation, failure ownership, and pseudo-isolation machinery.  Installed
plugins are already trusted under RFC-0078; this RFC instead accepts the
narrow explicit in-process lifetime trade-off.

### Add trusted-LAN authority now

Rejected.  RFC-0130 did not authorize LAN peers to trigger external provider
disclosure/network activity.  That is a separate future authority decision.

### Fold External Information into ordinary browser Chat

Rejected.  Automatic/conditional acquisition for browser Chat is a distinct
authority and privacy question deliberately left for later RFC work.

### Combine query and question

Rejected.  RFC-0078/RFC-0091 assign them distinct meanings and recipients;
one input would obscure that boundary.

## Trade-offs

Web usability moves one explicit acquisition execution from a short-lived CLI
caller to an already-running native HAC process.  The selected trusted plugin
and its plugin-owned process-local state may consequently remain resident for
that process lifetime, without HAC-controlled cleanup or claimed isolation.
Independently explicit requests may share that imported module state; this RFC
does not assert thread safety or serialize them globally.  Excluding trusted
LAN leaves remote household browsers unable to perform this operation.  Separate
query and question fields are less convenient, and lack of plugin discovery UI
requires an operator to know or retain an exact name.  These restrictions
preserve explicit provider choice, source-grounding semantics, and
installation-versus-authority separation.  Provider plugins also observe the
long-lived ordinary-process environment: Tavily browser acquisition requires
`TAVILY_API_KEY` already present there, unlike a fresh CLI shell invocation.
That is less dynamically convenient but avoids browser credential transfer,
secrets storage, environment forwarding, or provider configuration.  SearXNG
has no equivalent credential consequence because its accepted first-hop
contract is credential-free.

## Impact

After acceptance, implementation may add only the smallest ordinary-loopback
External Information view and bounded same-origin browser operation, reuse the
existing exact plugin selection/validation/acquisition contract and ordinary
source-grounded Chat path, present ephemeral distinct provenance, and add
focused proofs/documentation necessary for this decision.  It must not change
the CLI, Configuration semantics, trusted-LAN app, receiver routes, public
capability API, routing, capability model, provider configuration, or
dependencies.

This Draft RFC authorizes no implementation.

## Proof expectations

A later implementation must prove at least that:

1. the view and action exist only in ordinary/native loopback, never
   trusted-LAN or receiver authority;
2. exact native Host, exact same-origin Origin, and JSON are required;
3. an explicit valid override has one-operation precedence without consulting
   retained selection for plugin choice, while blank uses the retained RFC-0095
   name and unavailable/malformed required retained selection fails safely;
4. missing/invalid selection or invalid `QUERY` fails before discovery or
   network activity;
5. exactly one selected entry point is discovered, loaded, and invoked per
   successful acquisition attempt;
6. startup, Configuration, ordinary browser Chat, and other capabilities do
   not inspect plugin metadata or provider state;
7. acquisition output is freshly and completely RFC-0077 validated, and
   malformed output cannot reach routing;
8. source-grounded Chat uses existing ordinary routing, with remotes receiving
   normalized question/evidence only;
9. result URLs are never fetched or followed, and generated content remains
   distinct from ordered supplied-source provenance;
10. a confirmed disconnect during acquisition abandons HAC-owned work,
    discards late results, and cannot start source-grounded Chat or publish a
    late result; completion already owned retains RFC-0082 precedence;
11. acquisition failures reveal no private plugin/provider/query detail and
    create no fallback, retry, repeated acquisition, or ordinary-Chat fallback;
12. HAC itself adds no query/question/source/result history, cache, or other
    persistence; this does not require proving arbitrary trusted plugins cannot
    retain process-local memory;
13. independently submitted valid operations may be concurrent, with no
    process-global scheduler or serialization guarantee; no Capability or
    generic plugin/provider/acquisition API/dependency is added; and
14. the explicit browser path may invoke the existing RFC-0079 SearXNG plugin
    in the ordinary process only after explicit loopback submission, while
    preserving its fixed destination/request/normalization/lifecycle rules;
15. a browser Tavily operation uses only the existing plugin-owned
    `TAVILY_API_KEY` mechanism from the ordinary HAC process environment; HAC
    core/browser requests neither read, accept, transfer, persist, log, nor
    expose it, and unusable credentials yield only the existing privacy-safe
    acquisition failure;
16. the historical CLI path retains caller-process environment credential
    behavior, while startup, Configuration, ordinary browser Chat,
    trusted-LAN, and receiver do not inspect credentials or invoke providers
    merely because a plugin or environment variable exists; and
17. no live provider/network test is required: fake plugin/environment proof
    and bounded request capture suffice for this boundary.

## Open questions

None within this proposed boundary.  Automatic browser or interactive Chat
acquisition, trusted-LAN External Information, plugin/provider management,
secrets UI, retained history, clickable/fetched URLs, research loops, and
remote acquisition execution require later architectural decisions.

## Decision

Accepted: HAC adds one explicit External Information operation only to the
ordinary/native loopback browser.  It accepts an optional exact plugin override
or else the RFC-0095 retained selection, distinct operator-supplied `QUERY` and
`QUESTION`, and exactly one selected RFC-0078 acquisition-plugin invocation.
Only for that explicit browser operation, the plugin executes in the already-
running ordinary HAC process; HAC reconstructs fresh RFC-0077 evidence, then
uses ordinary source-grounded `capability=chat` routing.  Generated content and
supplied-source provenance remain distinct.  Exact native Host, same-origin
Origin, and bounded JSON authorize the browser action; bounded disconnect
abandonment/cancellation spans acquisition through source-grounded Chat.

This accepts neither process-global acquisition serialization nor HAC-owned
query/source/result persistence.  Trusted in-process plugin state may remain
resident until process exit.  RFC-0079 SearXNG and RFC-0093 Tavily contracts
remain unchanged except for this browser invocation location; Tavily reads
`TAVILY_API_KEY` from the ordinary HAC process environment for browser
acquisition, while historical CLI acquisition reads it from its one-shot caller
environment.  No browser credential field/transfer, secrets or configuration
framework, plugin discovery UI, generic acquisition API, new Capability,
automatic browser Chat acquisition, trusted-LAN/receiver acquisition, provider
fallback, retry/research loop, or arbitrary URL retrieval is accepted.
