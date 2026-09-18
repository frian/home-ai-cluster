# RFC-0132: Bounded Loopback Retained Configuration Completion

Status: Draft

Date: 2026-09-18

Author: frian

## Summary

This RFC proposes to complete the existing ordinary/native loopback
Configuration facade for the three already accepted retained domains it does
not yet represent:

- the optional Image Generation companion;
- the optional external-information acquisition-plugin choice; and
- the retained Chat external-information fallback authorization.

It adds browser authority over those existing facts only.  It adds no retained
fact, does not change any fact's meaning, and does not create a whole-
configuration editor.  Each browser operation retains the separate ownership,
validator, reset behavior, and future-invocation semantics of its corresponding
`hac config` domain.

The ordinary/native loopback Configuration view may consequently present all
five current retained semantic domains together.  The trusted-LAN browser,
receiver authority, remote configuration, observation, discovery, and live
process reconfiguration remain excluded.

## Context

RFC-0094 establishes HAC-managed retained local configuration and separate
`config local` and `config node` ownership.  RFC-0095 adds one optional exact
retained external-information plugin name, and RFC-0096 adds one separate
retained authorization for native one-shot Chat external-information fallback.
RFC-0106 and RFC-0125 extend the complete retained local domain.  RFC-0128
adds the separate optional retained stable-diffusion.cpp Image Generation
companion, owned by `config image-generation`.

RFC-0112 accepts a native-loopback browser facade only for the complete
retained local domain.  RFC-0113 separately accepts its caller-owned retained
remote-node facade.  Both require retained-state-only reads, future-invocation
semantics, exact native Host and same-origin Origin for persistent mutation,
receiver isolation, and fail-closed evolution.  RFC-0128 explicitly leaves its
new Image Generation companion outside browser authority.  Consequently, the
current browser can represent the local and remote-node domains but not the
three later accepted domains.

RFC-0130 is a distinct trusted-LAN capability-only authority.  It deliberately
excludes Configuration, including read-only Configuration; it must not inherit
this proposed loopback authority.

## Problem

The complete current retained HAC state has five conceptual domains:

```text
local
remote_nodes
external_information_plugin
chat_external_information_fallback
image_generation
```

The native loopback Configuration view covers only `local` and `remote_nodes`.
An operator who prefers the bounded browser facade must use the CLI for the
other three retained facts, despite each already having accepted CLI semantics.

RFC-0112 deliberately prevents later retained facts from automatically gaining
browser authority.  Completing this Configuration view therefore needs an
explicit decision, rather than an implementation inference from storage shape
or from the existence of CLI commands.

## Goals

- Extend only the ordinary/native loopback Configuration facade to the three
  enumerated existing retained domains.
- Preserve separate domain ownership and the existing CLI validators and
  configure/reset semantics.
- Make retained absence explicit and preserve retained-state-only,
  future-invocation meaning.
- Require exact native Host authority for Configuration reads and RFC-0112/
  RFC-0113 Host/Origin mutation authority for persistent writes, while
  preserving receiver isolation.
- Ensure configuration reads and mutations have no runtime, plugin, provider,
  health, discovery, or network side effects.
- Preserve fail-closed behavior when a later unrepresented retained domain is
  introduced.

## Non-goals

This RFC does not add new retained facts; a generic configuration API,
framework, or retained-property editor; whole-document editing or replacement;
PATCH/merge semantics; physical retained-file editing; import/export;
profiles; selected configuration files or `--runtime-config` editing/import;
generic retained capability bindings; or public retained-storage format.

It does not add plugin/provider discovery, credential or secret management,
provider configuration, Image Generation model/backend/lifecycle or generation
controls, live reconfiguration, runtime/model/plugin/provider health or
preflight, dashboard/control-plane behavior, database or session persistence,
or automatic refresh.

It also does not add Configuration to trusted LAN, receiver authority, remote
nodes, or another machine; remote administration; configuration
synchronization; topology/runtime discovery; or any network authority.

## Proposal

### One completed, bounded loopback facade

The existing native-loopback Configuration view may present these sections:

```text
Local
Image Generation
Remote nodes
External Information
Chat external information
```

Presentation, route spelling, JSON transport shapes, and styling remain
implementation details.  This is one view over distinct semantic authorities,
not one configuration object with a single save operation:

```text
config local                 -> complete textual/local retained domain
config image-generation      -> complete Image Generation companion domain
config node                  -> one retained remote-node declaration
config external-information  -> retained plugin-choice domain
config chat                  -> retained Chat fallback-authorization domain
```

Each browser mutation changes only its owned domain and preserves every other
retained domain.  The facade must not construct a generic whole-configuration
replacement endpoint, silently preserve hidden cross-domain values, or add
cross-domain PATCH/merge behavior.  Existing CLI and browser operators may use
their respective domain facades interchangeably, subject only to accepted
last-writer-wins behavior within a mutated retained domain.

### Existing local and remote-node domains

RFC-0112 remains authoritative for the complete retained textual/local domain:
its complete-domain replacement semantics are unchanged.  To make the view
operationally complete, a later implementation may expose one clear local
reset/remove action, but only if it means exactly `hac config local --reset`.
It removes the complete local domain, not individual fields, and preserves all
other retained domains.  This does not authorize whole-retained-state browser
reset.

RFC-0113 remains authoritative for individual retained remote-node declaration
operations, validation, ordering, and isolation.  This RFC does not modify
that domain merely because the view may present all sections together.

### Image Generation companion

The browser may inspect, configure, and clear exactly RFC-0128's optional
Image Generation companion.  Its domain remains exactly fixed runtime identity
`stable-diffusion-cpp`, one explicit validated loopback HTTP `base_url`, and
exact local execution ownership of `image-generation`.  Browser configure and
clear use the same semantic validation and reset as `hac config
image-generation`; they preserve the local textual domain, remote nodes,
external-information choice, Chat fallback authorization, and every other
retained domain.

The view must not expose a runtime/provider selector, model or model path,
dimensions, seed, sampler, steps, CFG/guidance, negative prompt, style,
quality, backend/device, executable path, startup command, or lifecycle
controls.  Inspection is retained configuration only: it must not contact
`sd-server`, inspect health or models, discover a runtime, infer availability,
or test the URL.

### External-information plugin choice

The browser may inspect, set, and clear exactly RFC-0095's optional retained
acquisition-plugin entry-point name.  It is one explicit exact plugin name;
set and clear must use the same accepted semantic validation and reset as `hac
config external-information`, preserving every other retained domain.

Configuration must not enumerate or discover plugins, import a plugin, inspect
plugin/provider configuration or credentials, contact a provider, test health,
infer a default, rank providers, or create fallback.  A simple explicit text
value is sufficient.  Absence remains a first-class retained state.

### Chat external-information fallback authorization

The browser may inspect and set RFC-0096's existing boolean-like retained Chat
external-information fallback authorization.  Disabling it is exactly the
existing clear/reset meaning, and mutation preserves every other retained
domain.

This setting retains only the scope RFC-0096 already assigns: native one-shot
Chat fallback.  It does not authorize automatic external information in browser
Chat or interactive Chat.  The Configuration facade must not perform
classification, plugin discovery/loading, credential reads, acquisition,
provider access, source-grounded Chat, or network activity.

### Read and future-invocation semantics

Every Configuration section represents retained future/operator state only;
none represents the process serving the browser.  Read must not inspect current
runtime or Image Generation composition, local runtimes, remote nodes,
plugins/providers, credentials, health/status, active executions, models, or
`--runtime-config`.  Retained absence must be represented as absence, not as a
default inferred from current process state.

All mutation changes retained state for future HAC invocations only.  It does
not apply, reload, restart, reconnect, switch a live runtime, create/remove an
adapter, or reconstruct the current process.  The UI must not imply such live
effects.  In particular, changing the retained plugin or Chat fallback fact
does not make the serving browser process acquire external information.

### Request authority and isolation

Every Configuration read belongs only to the ordinary/native application and
requires the exact accepted native Host authority.  Persistent mutation also
belongs only to that application and reuses RFC-0112/RFC-0113: exact accepted
native Host authority, exact same-origin `Origin`, bounded JSON/non-simple
mutation where applicable, and no CORS authority.  Accepted authority is pinned
to HAC's effective native authority; attacker-controlled Host and Origin values
must not validate one another.  Read-only GETs do not gain an Origin
requirement.  This RFC adds no login, accounts, sessions, tokens, OAuth, TLS,
or general authentication, and does not weaken existing Host/Origin behavior.

The routes belong only to the ordinary/native application.  The trusted-LAN
application remains without Configuration routes or view under RFC-0130, and
receiver authority remains without Configuration routes.  This RFC does not
add a remote configuration protocol, synchronization, remote administration,
topology discovery, health probing, or control-plane behavior.

### Fail-closed evolution

This RFC authorizes exactly the five enumerated current retained semantic
domains.  A new separate retained domain does not become browser-readable or
browser-writable merely because it appears in retained storage.  Its existence
must not disable a mutation of another independently owned domain when that
operation can preserve the separate domain unchanged under its established
domain-isolation semantics.

The fail-closed rule instead applies when a browser-owned complete semantic
domain grows internally.  For example, if a future fact is added to the
complete `local` domain but is not represented by its browser replacement,
that operation must fail closed until an accepted architectural decision
determines browser participation.  It must not silently preserve, reset, drop,
merge, or otherwise rewrite that hidden fact.  This selects neither generic
future-schema introspection nor browser authority over unknown domains; the
detection mechanism remains an implementation detail.

## Rationale

The existing CLI has already established five small, separately owned retained
domains.  Extending the established loopback facade to the final three is less
ambitious and clearer than elevating private storage into a browser-editable
whole document.  Separate finite operations keep CLI and browser semantics
aligned, avoid stale cross-domain rewrites, and keep future domain additions
subject to explicit review.

Retained-state-only reads and future-invocation-only writes preserve an honest
operator model: Configuration records declared future choices, while health,
availability, provider installation, and running-process truth retain their
separate owners.  Keeping the authority loopback-only continues to distinguish
local operator configuration from the deliberately capability-only trusted-LAN
browser and receiver protocol.

## Alternatives considered

### Keep the three domains CLI-only

Rejected.  It preserves an unnecessary inconsistency in the existing bounded
Configuration view without protecting a boundary that the accepted domain
semantics and loopback request authority cannot already preserve.

### One generic configuration document or save operation

Rejected.  It would collapse distinct owners and create whole-state rewrite,
merge, future-field, and stale-page semantics not accepted by the CLI.

### Infer configuration from current runtime, plugins, or provider state

Rejected.  Retained choice is not live truth; inference would add observation,
discovery, credential, and potentially network authority.

### Add Configuration to trusted LAN or receiver authority

Rejected.  RFC-0130 deliberately bounds trusted-LAN authority to capability
use, and receiver authority is not an operator administration protocol.

## Trade-offs

The view remains intentionally less convenient than a generic settings page:
it has explicit per-domain operations, no plugin picker, no live status, and
no apply/restart controls.  That limitation avoids a new control plane,
provider/runtime observation, and accidental authority expansion.  As with the
existing domain facades, ordinary local last-writer-wins behavior is retained;
this RFC adds no revision, locking, or conflict-resolution system.

## Impact

After acceptance, implementation may add only the smallest native-loopback
Configuration sections, bounded retained read and finite per-domain mutation
operations, shared existing semantic validation/reset reuse, Host/Origin
enforcement, route isolation, focused tests, and operator documentation needed
to realize this proposal.  It must preserve all existing CLI behavior and
retained files; no migration, dependency addition, or public retained-storage
path/key/format is required.

This Draft RFC authorizes no implementation.

## Proof expectations

A later implementation must prove at least that:

1. loopback read represents all five current retained semantic domains without
   runtime, network, plugin, or provider observation;
2. local browser mutation remains RFC-0112 complete-domain replacement, and a
   local reset, if implemented, removes only that complete local domain;
3. Image Generation configure/reset uses RFC-0128 validation and preserves
   every other domain;
4. external-information set/clear uses RFC-0095 validation and performs no
   discovery, import, credential, or network work;
5. Chat fallback enable/disable mutates only RFC-0096 authorization and
   triggers no classification, acquisition, or network work;
6. remote-node behavior remains RFC-0113-compatible;
7. every Configuration read requires exact native Host authority, and every
   persistent mutation additionally requires exact same-origin Origin;
8. trusted-LAN and receiver applications contain neither Configuration routes
   nor a Configuration view;
9. mutation of one retained domain preserves all other domains;
10. unrepresented growth within a browser-owned complete domain fails closed
    rather than being silently rewritten, while a new separate retained domain
    remains unauthorized and is preserved by unrelated domain mutations when
    semantically safe;
11. no runtime/model/plugin/provider health or discovery, or live process
    reconfiguration, occurs; and
12. no dependency or public retained-storage-format expansion is introduced.

## Open questions

None within this proposed boundary.  Browser authority for a later retained
domain, Configuration beyond native loopback, or generic configuration
semantics requires separate architectural consideration.

## Decision

Home AI Cluster proposes to extend only the native-loopback Configuration
browser facade to the three currently unrepresented accepted retained domains:
the Image Generation companion, external-information plugin choice, and Chat
external-information fallback authorization.  Each remains a separately owned
retained domain with its existing validator and semantics; configuration reads
and writes retain future-state-only meaning, have no observation, discovery, or
network side effects, and do not live-reconfigure the serving process.

Configuration reads require exact native Host authority; persistent mutation
additionally retains RFC-0112/RFC-0113 exact same-origin Origin authority.
The proposal preserves trusted-LAN, receiver, remote, and synchronization
exclusions.  Unrepresented growth within a browser-owned complete domain fails
closed, while a new separate retained domain remains unauthorized and does not
disable unrelated domain mutation that can preserve it safely.  It does not add
a generic configuration framework, whole-document editing, or dashboard/control
plane authority.  This RFC remains Draft pending operator acceptance after
review.
