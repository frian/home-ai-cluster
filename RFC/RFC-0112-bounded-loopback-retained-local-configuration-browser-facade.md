# RFC-0112: Bounded Loopback Retained Local Configuration Browser Facade

Status: Draft

Date: 2026-09-07

Author: frian

## Summary

This Draft proposes one bounded second local facade for the retained local HAC
configuration already accepted by RFC-0094:

```text
CLI facade --------\
                    -> one retained-local semantic authority
Browser facade ----/
```

The existing native loopback browser may read and replace that complete local
domain, using the same validation and mutation meaning as `hac config local`.
It does not own a second configuration model, expose retained bytes as an API,
or change the already constructed process serving the page. The proposed
browser authority is native-loopback only, and persistent mutation requires an
accepted native Host authority plus an exact same-origin `Origin` on a bounded
JSON/non-simple request. It adds no CORS authority or general authentication.

## Context

RFC-0094 accepts HAC-managed retained configuration. Its supported semantic
operator facade includes `hac config local`, `hac config node`, and `hac config
show`; the physical retained path and bytes are deliberately not a user-facing
configuration API. The local domain currently represented by `hac config local`
contains one retained runtime composition, optional RFC-0059
`local_capabilities`, and optional HAC `execution_limit`.

RFC-0062 and later browser RFCs establish a fixed same-origin browser on the
ordinary native loopback application. RFC-0084's browser-local theme preference
is presentation state, not HAC retained state. RFC-0109 and RFC-0111 establish
a separate receiver authority with a closed route set, while the ordinary
native application remains on `127.0.0.1`. RFC-0074 and RFC-0110 separately
accept invocation-scoped `--runtime-config PATH`, including an alternative
multi-binding form; that source is not retained local configuration.

## Problem

The existing CLI is the only semantic facade for retained local configuration.
The ordinary loopback browser can already provide bounded local capability
views, but it cannot offer an equally bounded operator view of the retained
local baseline. A browser facade must not turn HAC into a configuration API,
dashboard, cluster control plane, or live process manager.

## Goals

- Add one possible native-loopback browser facade over the already accepted
  retained local configuration domain.
- Preserve `hac config local` validation and complete-domain replacement
  semantics exactly.
- Keep retained future-invocation state distinct from the current process.
- Prevent an unrelated Web origin from mutating retained HAC state merely
  because the native service is reachable on loopback.
- Preserve receiver isolation, local-first and privacy-first boundaries.

## Non-goals

This Draft does not introduce a generic configuration API or framework, direct
retained-file editing, partial PATCH or merge semantics, browser defaults,
live reconfiguration, Apply/Reload/Restart, lifecycle management, model
discovery or download, runtime installation or supervision, health/status or
execution-activity observation, scheduling or capacity controls, a database,
Docker, Kubernetes, dashboard, or control plane.

It does not expose `hac config node`, remote topology, receiver runtime/model
configuration, receiver/network configuration, hosts or ports, firewall or
service management, or configuration belonging to another machine. It does not
add retained multi-binding, a capability-to-adapter editor, or inspection,
import, or editing of `--runtime-config`.

It also does not add CORS-based third-party access, login, accounts, sessions,
OAuth, token secrets, TLS, or an authentication framework. It makes no
protection claim against arbitrary local processes or local users able to send
handcrafted loopback HTTP requests.

## Proposal

### One retained-local semantic authority

The proposed browser is a second facade, not a second configuration owner:

```text
CLI
-> configuration semantics A

Browser
-> configuration semantics A
```

The browser and CLI must use one shared retained-local validation and mutation
authority. Later implementation may extract the smallest internal semantic
operation from current CLI orchestration, including argparse-coupled code, but
only if it preserves existing semantics exactly. It must not use that refactor
to introduce a generic abstraction, provider framework, patching, new
precedence rule, changed default, or changed CLI behavior.

Transport representation and error presentation may differ between CLI and
HTTP. The valid local domain and the meaning of mutation must not differ.

### Retained local domain

The first browser domain is exactly the existing retained local configuration
domain owned by `hac config local`. It may provide read-only inspection and
creation or replacement of that domain. It may expose only the current retained
runtime choices and runtime-specific values, RFC-0059 caller-local static
routing capabilities, and retained HAC `execution_limit`.

No runtime, parameter, capability, or configuration fact is added. The exact
JSON schema and HTML controls are implementation details. Current retained
runtime vocabulary is authoritative: `ollama`, `llama-server`, and `vllm`, with
their existing applicable retained values and existing validation.

`local_capabilities` means caller-local static routing capabilities. It is not
runtime capability, node execution capability, discovered capability, or
receiver advertisement. `execution_limit` means HAC-owned process-local
execution permission policy; it is not runtime capacity, worker count, GPU
slots, engine concurrency, or model capacity.

### Retained state is not current process state

The facade represents **what HAC has retained locally for future ordinary
invocations**, not what the process serving the browser is doing. It does not
inspect the current `LocalAppComposition`, runtime, active executions,
health/status, remote nodes, or `--runtime-config`.

For example, retained Ollama/model A remains the browser's subject when the
current process was explicitly launched with Ollama/model B. A process launched
with `--runtime-config PATH` neither supplies browser facts nor becomes
inspectable, importable, reproducible, or editable through this facade.

Saving changes retained state only. It does not reconstruct or mutate the
current composition; the retained baseline applies only on future ordinary
invocations according to RFC-0094's existing rules. The browser must not imply
live reconfiguration through Apply, Reload, Restart, live model switch, live
adapter replacement, or process reconstruction. If no retained local
configuration exists, the facade may represent that absence directly and must
not invent default/current truth by observation.

### Read semantics

The browser may expose a bounded, read-only projection of the retained local
domain through HAC's validated retained-configuration authority. Frontend code
must not read the physical file, and the implementation must not parse `hac
config show` text. Read has no runtime, process, remote-node, network,
execution-count, or runtime-config observation authority.

### Complete-domain replacement mutation

Browser mutation has the existing `hac config local` meaning:

```text
browser
-> complete desired retained local domain
-> shared semantic validation
-> replace retained local domain
```

It explicitly does not mean:

```text
browser partial fields
+ existing retained local state
-> implicit merge
```

No generic PATCH, field preservation, browser-specific defaulting, retained
merge framework, or partial reset is accepted. A write-capable view must
explicitly represent every mutable fact in the complete local domain it
replaces. It must not silently preserve, silently reset, automatically merge,
or re-submit stale hidden values. Values inapplicable to a selected runtime do
not need to appear as active values; the existing runtime-domain validation
remains authoritative.

RFC-0112 authorizes browser read/write only for the retained-local facts within
this accepted bounded domain. A later retained-local fact does not automatically
extend browser authority merely because it is added to retained configuration.
Its later architectural decision must explicitly decide whether and how it
participates in this facade. Until then, browser mutation must fail closed
rather than silently preserve, reset, drop, merge, or otherwise rewrite that
unrepresented fact. The detection mechanism is an implementation detail.

Existing CLI reset/removal authority remains valid. A later implementation may
separately expose the existing complete local-domain removal operation under
the same semantic and request-authority rules, but browser reset is not
required for the first proof and must never create a partial reset/merge path.

An open page can become stale if another local operation changes retained
state. A later complete browser save may replace that newer domain: this is the
accepted last-writer-wins consequence of complete-domain replacement. This
Draft does not add ETags, revisions, compare-and-swap, optimistic locking,
merge conflict resolution, or distributed coordination.

### Request-authority boundary

Loopback binding alone is insufficient for browser mutation authority. The
proposed narrow property is:

> An unrelated Web origin must not be able to mutate retained HAC state merely
> because the native HAC server is reachable on loopback.

The first mutation boundary is:

```text
native configuration surface only
+ accepted native Host authority
+ exact same-origin Origin for mutation
+ bounded JSON/non-simple mutation request
+ no cross-origin CORS authority
```

The configuration facade belongs only to the ordinary/native application. Its
accepted host is RFC-0111's `127.0.0.1`, at the invocation's effective native
port, conceptually `http://127.0.0.1:<effective-native-port>`. Checks are
pinned to HAC's accepted effective authority, not derived by trusting arbitrary
client input. Exact HTTP parsing and normalization are implementation details.

Configuration requests must also be addressed to that accepted native
authority. The boundary is not merely `Origin == Host`: attacker-controlled
values must not validate one another. This requirement is bounded to the new
facade and does not impose a new global Host policy on historical native routes.

A persistent mutation is eligible for normal semantic validation only when its
`Origin` exactly corresponds to the accepted effective native origin. Absent,
`null`, or foreign Origin must be refused before retained mutation. The exact
HTTP error status/body remains an implementation detail unless a small existing
repository convention later requires otherwise. Mutation uses bounded JSON and
a non-simple request shape as defense in depth against form submission; CORS
preflight is not its authorization mechanism. No cross-origin CORS permission,
custom identity header, browser secret, or token is accepted.

### Local-process threat boundary

This is not a general local authentication model. A separate local process can
construct raw loopback HTTP and forge `Host` and `Origin`. The proposal blocks:

```text
unrelated Web origin
X-> persistent retained configuration mutation
```

It does not classify a local handcrafted request as authenticated or
unauthorized, and does not attempt to protect against arbitrary local software
or users with loopback access. Accounts, login, sessions, OAuth, TLS,
operating-system authentication, and ACLs require a separate security decision.

### Native and receiver isolation

RFC-0109 and RFC-0111 remain exact:

```text
native/local authority: loopback browser, native routes, configuration facade
receiver authority: explicit receiver bind, RFC-0109 closed route set only
```

The configuration read and mutation routes must exist only on the native app;
they must not be included by `create_receiver_app(...)`. This is a structural
route-authority boundary, not convention. The proposal does not broaden the
accepted receiver route set.

### Multi-binding and topology boundaries

RFC-0110's explicit invocation-scoped `--runtime-config PATH` accepts
multi-binding local runtime composition; it does not accept retained
multi-binding through `hac config local`. This proposal therefore excludes
retained multi-binding, a browser binding editor, browser construction of
multiple retained adapters, and every runtime-config inspection/import/editing
path. A future retained multi-binding decision needs its own RFC before any
browser exposure.

The browser does not expose `hac config node`, retained remote declarations,
remote URLs/capabilities, receiver configuration, or another machine's state.
Each machine continues to own its local runtime composition locally; the page
is not a cluster control plane. It also excludes host and receiver bind values,
ports, network exposure, firewall management, service installation,
daemonization, supervision, lifecycle, and model installation/download.

## Privacy and security

Retained configuration remains HAC-managed local state. The browser may expose
only the bounded local facts necessary for this facade, must not broaden
ordinary logging of private values, and must not disclose remote topology. The
request-origin boundary is useful protection from unrelated Web origins, not a
claim of general authentication. Local-first and privacy-first defaults remain
unchanged.

## Compatibility

The facade is additive. Existing `hac config local`, `hac config show`, `hac
config node`, retained-storage authority, explicit CLI overrides, RFC-0074 and
RFC-0110 runtime-config behavior, native capability routes, browser capability
behavior, receiver isolation, absence of retained configuration, and accepted
zero-argument behavior remain compatible. No operator is required to use the
browser facade.

## Rationale

The existing native loopback browser is the smallest useful second local facade
because it can reuse the existing local process and semantic authority without
making stored bytes or current process state public configuration truth.
Complete replacement keeps browser and CLI meaning aligned and avoids implicit
state ownership. The narrowly pinned Host and Origin conditions address the
specific unrelated-origin browser threat without prematurely inventing a
general local identity system.

## Alternatives considered

### Keep configuration CLI-only

This remains simple and functional, but retains avoidable operator friction and
prevents the existing browser from serving as a bounded second facade.

### Read-only browser first

This is conservative, but is rejected for the proposed decision because the
mutation semantics and request-authority questions are narrow enough to decide
together without new infrastructure.

### Edit retained storage directly

Rejected: physical representation is not the supported API, and direct editing
would duplicate or bypass HAC validation and persistence authority.

### Partial PATCH, merge, or hidden-field preservation

Rejected: each creates mutation semantics that `hac config local` does not own,
including stale and implicit-state hazards.

### Live apply to the current process

Rejected: retained state is a future-invocation baseline; live application
would introduce composition and lifecycle authority.

### Login, tokens, or sessions

Rejected as disproportionate to the narrow unrelated-Web-origin threat model.

### Include topology or network configuration

Rejected: that would cross topology, control-plane, and network-authority
boundaries.

## Trade-offs and consequences

Complete replacement is intentionally last-writer-wins, so an old browser page
can overwrite newer retained local state. This avoids silently creating a
concurrency system. The view is intentionally unable to explain current process
truth, runtime health, or effective CLI overrides; that limitation preserves
truthful ownership boundaries. The Host/Origin checks improve browser-origin
safety but deliberately do not protect against arbitrary local processes.

## Implementation boundary

After acceptance, a later implementation may add one native-loopback browser
configuration view, one bounded retained-local read surface, one complete-domain
replacement mutation surface, controls representing every mutable local fact,
the stated request-authority checks, minimal shared semantic-authority reuse,
focused frontend/backend and route-isolation tests, and operator documentation.
It must not implement anything outside this Draft's non-goals. This RFC PR
authorizes none of that implementation.

## Proof expectations

A later implementation must prove at minimum that:

1. the facade exists only on native loopback authority and never on the receiver;
2. read reports retained state, not runtime/process truth, and represents absence
   without observation;
3. valid same-origin mutation replaces the complete local domain through the
   same validation and replacement behavior as the CLI;
4. every mutable local fact is explicitly represented, with no hidden preserve,
   reset, or merge, and invalid configuration does not mutate state;
5. a later unsupported retained-local fact cannot be silently lost, preserved,
   reset, dropped, merged, or otherwise rewritten by browser mutation;
6. unacceptable Host authority prevents disclosure/mutation as applicable, and
   absent, `null`, or foreign Origin prevents mutation before persistence;
7. exact same-origin mutation works on a non-default effective native port and
   grants no unrelated-origin CORS authority;
8. retained mutation does not change the running `LocalAppComposition`, while a
   future ordinary invocation consumes the retained baseline under RFC-0094;
9. `--runtime-config` remains separate and uninspected, retained multi-binding
   is absent, and remote/receiver/network configuration remains unexposed; and
10. existing CLI configuration, native browser behavior, and RFC-0109/RFC-0111
   route isolation remain compatible.

## Open questions

None remain within this Draft's proposed boundary. A future retained
multi-binding domain, general local authentication, or a demonstrated stale
state product problem requires separate RFC consideration.

## Decision

Pending review. This Draft proposes that Home AI Cluster accept the bounded
native-loopback retained-local configuration browser facade described above;
no implementation is authorized unless and until this RFC is reviewed and
accepted.
