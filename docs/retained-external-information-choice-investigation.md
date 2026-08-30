# Retained external-information choice investigation

Status: Investigation only

Date: 2026-08-30

## Question

What is the smallest retained external-information configuration that removes
repeated operator ceremony from explicit `hac external-information` use while
preserving provider-owned credentials, explicit external-network authority, and
the rule that plugin installation alone grants no permission?

This investigation changes no behavior and accepts no architecture. It does
not draft an RFC, retain a plugin choice, retain credentials, or alter ordinary
Chat.

## Outcome

**Outcome B — viable with one bounded architectural adjustment.**

The smallest credible later decision is for HAC to retain one exact RFC-0078
entry-point name, with the existing nonblank, at-most-64-UTF-8-byte bound. An
explicit external-information invocation may use that name when no explicit
`--plugin` is supplied. Credentials and provider/service configuration remain
persistently operator- or plugin-owned outside HAC.

This is sufficient for the 0.8 daily-use goal when “configure once” means two
separate, durable setup actions with clear owners:

```text
HAC:                choose one acquisition plugin once
provider/operator:  arrange that plugin's credential or service once
daily operation:    hac external-information QUERY QUESTION
```

It is not a claim that a retained name proves a provider is installed, healthy,
configured, affordable, or currently usable. Those are different facts with
different owners. A later RFC would be required before implementation because
this deliberately revises RFC-0078's per-operation exact-selection rule and
extends RFC-0094's bounded retained state.

## Current accepted boundaries

RFC-0078 establishes one explicit, finite caller edge, one exact selected
plugin, lazy metadata discovery and loading only for that operation, one
invocation, complete RFC-0077 evidence reconstruction, no fallback, and one
privacy-safe `external-information-acquisition-failed` failure before ordinary
routing. Installation makes a plugin available for explicit selection; it is
not network authority. HAC core owns no provider endpoint, HTTP client,
credential, provider configuration, health, or retry policy.

RFC-0091 reduces query/question syntax ceremony but intentionally preserves
the named per-operation plugin selection. RFC-0094 provides local HAC-retained
configuration for already accepted runtime and static-topology facts, while
excluding providers, plugins, credentials, and external-information authority.
It also establishes that retained configuration is a local baseline, `show`
reports what was configured rather than live truth, and explicit values are
temporary overrides.

RFC-0093 fixes Tavily's sole first-version credential mechanism: the selected
plugin reads a nonblank `TAVILY_API_KEY` from the environment of the caller
process only when its `acquire` callable runs. RFC-0079 instead fixes SearXNG
to a separately operator-installed and operated service at literal
`http://127.0.0.1:8888/search`; it adds no HAC credential or provider-config
surface. These distinct integrations are evidence for keeping provider setup
out of HAC core. [RFC-0078](../RFC/RFC-0078-optional-external-information-acquisition-plugin-boundary.md),
[RFC-0079](../RFC/RFC-0079-fixed-loopback-searxng-acquisition-plugin.md),
[RFC-0093](../RFC/RFC-0093-bounded-tavily-acquisition-plugin.md), and
[RFC-0094](../RFC/RFC-0094-retained-hac-configuration.md) remain authoritative.

## Daily-use friction

Today every operation must reconstruct `--plugin NAME`, even after an operator
has intentionally chosen one installed integration for repeated use. RFC-0091
removed unnecessary query/question option spelling, but correctly did not
decide whether a durable prior plugin choice is an acceptable authority input.
The remaining friction is stable selection, not a reason to make provider
configuration generic or automatic.

## Plugin selection versus credential availability

These are independent states:

```text
installed plugin             -> available for exact explicit selection
retained plugin name         -> prior operator selection for a future explicit operation
provider credential/service  -> selected plugin can attempt its own operation
```

Retaining `tavily` neither reads `TAVILY_API_KEY` nor establishes that it is
present. Retaining `searxng` neither starts, probes, nor proves availability of
the independently operated service. The exact name is thus the sole credible
HAC fact: it is not discovery, installation status, health, endpoint,
credential, cost, timeout, result option, or network permission for another
command.

## Tavily credential case

Tavily is operational only when the caller process environment contains a
usable `TAVILY_API_KEY`. Its separately packaged plugin already owns that
lookup at invocation time, and RFC-0093 excludes inline CLI keys, HAC parsing,
retention, configuration, and generic secrets. An operator can persist an
environment value through their normal OS, shell, or service-session mechanism
without HAC storing or inspecting it. The appropriate mechanism is a local
operator concern, not a cross-platform HAC secret-management contract.

That means an operator need not re-enter a key per request, although they must
ensure their normal persistent execution environment supplies it to the `hac`
process. This is an honest two-part “configure once” product model: HAC retains
the choice once and the provider/operator arranges authentication once. It is
not reasonable to promise that every arbitrary terminal session automatically
has the key; that would be an OS/session deployment promise rather than a HAC
configuration fact.

## SearXNG comparison

SearXNG has a materially different configuration shape. The accepted plugin
has no HAC-managed credential and calls only its fixed loopback endpoint; its
operator separately installs, configures, starts, and maintains SearXNG and
the service's upstream engines. A retained `searxng` name therefore works with
the same HAC rule while provider readiness remains outside HAC.

The contrast is decisive: Tavily needs an API key in the caller environment;
SearXNG needs an independently operated local service. A common HAC
credential/configuration field would fit neither cleanly and would either make
provider-specific facts core-owned or grow into a generic provider framework.

## Smallest credible retained fact and authority analysis

The later retained model need contain only an optional value conceptually like:

```text
external_information_plugin: exact RFC-0078 entry-point name | absent
```

It represents a prior operator-approved selection for future *explicit*
external-information operations. It does not authorize ordinary `hac chat`,
startup, background work, configuration-time checks, plugin import, credential
inspection, service health checks, or provider contact.

The authority remains deliberately conjunctive:

```text
retained exact plugin choice
  + explicit hac external-information invocation
  = one bounded RFC-0078 acquisition through that selected plugin
```

Installation remains availability, not authority. Inferring a choice from one
installed plugin would collapse that distinction and is rejected.

## “Configure once” and credential ownership

HAC does not need to own all durable state for an operator to configure the
path once. The useful product outcome is that neither selection nor provider
authentication/service setup must be reconstructed for every request. Keeping
each fact with its natural owner is clearer than placing both in one HAC file:
HAC owns the one cross-provider choice it consumes, while each plugin/operator
owns provider-specific authentication and service configuration.

Plugin-owned persistent configuration remains a possible future
provider-specific choice, but it is not necessary for this adjustment. For
Tavily it would revise RFC-0093's environment-only mechanism; for SearXNG it
would duplicate the service's operator-owned configuration. It should be
considered only if concrete friction with persistent operator environments
appears, not introduced preemptively.

## Effective plugin selection and temporary override

The bounded effective rule is understandable and needs no general precedence
framework:

```text
explicit --plugin NAME       -> NAME for this invocation only
otherwise retained name      -> retained name
otherwise                    -> current invalid-input behavior
```

An explicit override never changes retained state. If `tavily` is retained,
one `--plugin searxng` operation uses SearXNG's service configuration alone;
HAC must not transfer, associate, inspect, or select Tavily credentials. The
next invocation without `--plugin` again selects `tavily`.

## Configuration-time versus operation-time validation

Configuration should validate only the closed RFC-0078 name syntax. It should
not discover entry points, import a plugin, check installation, read a
credential, contact a provider, or probe SearXNG. A retained declaration may
outlive package installation, just as retained configuration records declared
operator facts rather than live state.

Only the explicit operation should retain RFC-0078's normal behavior: locate
exactly one matching entry point, lazy-load it, check compatibility, invoke it
once, and validate its returned evidence. A missing, duplicate, incompatible,
unconfigured, or failing selected plugin should remain the existing
`external-information-acquisition-failed` result. No fallback, repair,
automatic replacement, or retained-state mutation is justified.

## Zero-choice invariant

With no retained external-information choice, startup and ordinary Chat remain
unchanged; installed plugins remain inert; startup imports and discovers no
acquisition plugin; and explicit external-information use still requires
`--plugin`. No external network authority is added.

## Retained-choice-but-no-operation invariant

With a retained name but no explicit external-information operation, startup
and ordinary Chat still remain unchanged. HAC must not discover or import the
plugin, read provider credentials, inspect the SearXNG service, perform health
checks, or make a provider request. Retention is selection data, not execution
or an ambient permission.

## Zero-credential behavior and failure behavior

If `tavily` is retained but `TAVILY_API_KEY` is absent, an explicit
external-information operation selects Tavily and fails through the existing
privacy-safe acquisition-failure path. It must not prompt, store a value, fall
back to SearXNG or ordinary Chat, or change retained state. This is acceptable:
the retained choice removes repeated selection ceremony, while missing provider
setup remains an accurate provider-owned operation failure.

The same operation-time failure treatment applies to a missing plugin,
incompatible entry point, unavailable SearXNG, invalid credential, or provider
transport failure. The caller-visible failure must continue to avoid exposing
the query, credential, endpoint details, provider response, or configuration
state.

## Privacy and secret-storage analysis

**Home AI Cluster does not need to become a secret store for the 0.8
external-information usability problem.** HAC-held credentials would create a
new secret-at-rest responsibility: masking in `config show`, error/log/history
exposure controls, backups and copies, replacement and removal semantics,
platform-specific permissions, and security-sensitive retained JSON. File mode
`0600` would address only one narrow filesystem property, not those lifecycle
and portability responsibilities.

It would also make one provider-specific secret a pressure for a generic secret
abstraction, contradicting the smallest sufficient boundary and the existing
provider ownership decisions. Provider/operator-owned durable credentials are
sufficient for repeated explicit use and preserve privacy-first, boring
solutions-first ownership. No encryption, keyring, vault, or generic secrets
manager is required or recommended by this evidence.

## Relationship to future Chat fallback

Three questions remain separate:

```text
Which plugin does an explicit acquisition operation use?
How does that plugin authenticate or reach its service?
May ordinary Chat initiate acquisition automatically?
```

This investigation answers only the first, while preserving existing ownership
of the second. A retained name and available credential do not grant ordinary
Chat external-network authority. A future automatic fallback needs its own
explicitly accepted operator-authority boundary; this investigation does not
define answerability, fallback, or any Chat acquisition mechanism.

## Alternatives considered

| Alternative | Assessment |
| --- | --- |
| A. Keep current per-operation `--plugin` | Safest current boundary, but leaves the demonstrated stable-choice ceremony intact. |
| B. Retain one exact name only | Smallest viable adjustment; preserves explicit operation authority and provider-owned setup. |
| C. HAC retains name and credentials | Disproportionate secret, lifecycle, portability, and provider-ownership expansion for 0.8. |
| D. Plugin-owned persistent provider configuration | Could be provider-specific later, but not required now and would revise Tavily's accepted credential mechanism. |
| E. Infer from installation | Rejected: installation is availability, not authority. |
| F. Retain name plus generic external-network permission | Rejected: prematurely combines explicit-operation ergonomics with future ordinary-Chat autonomy. |

## Later RFC decision surface

If the project chooses to proceed, one later RFC should be limited to:

- one optional retained exact RFC-0078 entry-point name;
- use only by an explicit external-information operation when `--plugin` is absent;
- one-invocation explicit `--plugin` override with no retained-state mutation;
- current invalid-input behavior when neither selection exists;
- syntax-only configuration validation and operation-time plugin validation;
- existing acquisition-failure behavior for absent, incompatible, unconfigured, or failing plugins;
- set, replace, remove, and show concepts without fixing final CLI spelling;
- `config show` displaying only the configured name, not credentials or live status;
- no HAC-held secret, provider option, profile, generic configuration framework, or generic secrets framework; and
- no startup, ordinary Chat, fallback, or automatic acquisition behavior change.

## Final recommendation

Adopt no behavior in this investigation. Consider a narrowly scoped later RFC
for Outcome B only: one retained exact acquisition-plugin name as a baseline
for an operator's next explicit external-information command. Retain no
credential or provider configuration in HAC. This removes repeated selection
ceremony while leaving network authority explicit, provider ownership intact,
and ordinary Chat local by default.
