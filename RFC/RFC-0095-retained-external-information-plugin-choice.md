# RFC-0095: Retained External-Information Plugin Choice

Status: Accepted

Date: 2026-08-31

## Summary

Home AI Cluster may retain one optional exact RFC-0078 external-information
acquisition-plugin entry-point name.  That retained name is a baseline
selection only for a later explicit `hac external-information` operation which
does not supply `--plugin`.

The authority model remains deliberately conjunctive:

```text
retained exact plugin name
  +
explicit hac external-information invocation
  =
one RFC-0078 acquisition through that plugin
```

Retention is prior selection; execution still requires an explicit
external-information operation. Installation is availability, not authority.
This RFC neither adds provider configuration or credentials to HAC nor gives
ordinary Chat or startup external-network authority.

## Context

RFC-0078 establishes a category-specific installed-plugin boundary: one exact
caller-selected acquisition plugin, lazy discovery and loading only for an
explicit acquisition operation, one invocation, complete RFC-0077 evidence
reconstruction, no fallback, and privacy-safe acquisition failure. RFC-0091
shortens that explicit operation but leaves repeated stable plugin selection as
operator ceremony.

The retained external-information choice investigation found that retaining one
exact name is the smallest sufficient fact. Tavily and SearXNG have materially
different operator setup shapes, which is evidence against making provider
configuration common HAC state. RFC-0094 supplies the retained-configuration
substrate and its baseline/temporary-override pattern, but deliberately did
not authorize external-information configuration.

## Problem

An operator with a stable acquisition-plugin choice must currently repeat
`--plugin NAME` for every explicit external-information operation. That is
unnecessary selection friction, but it does not justify automatic acquisition,
selection inferred from installation, provider arbitration, or HAC ownership of
provider-specific setup.

## Decision / accepted architecture

### One orthogonal retained fact

HAC may retain at most one optional exact acquisition-plugin name,
conceptually:

```text
external_information_plugin: str | None
```

It must satisfy the existing RFC-0078 plugin-name contract:

- nonblank;
- at most 64 UTF-8 bytes; and
- an exact entry-point name in
  `home_ai_cluster.external_information_acquisition.v1`.

The physical serialized field name remains an internal implementation detail.
This is an orthogonal third retained domain, not a generic plugin or provider
configuration system. It does not alter RFC-0094 ownership of local runtime
composition or caller-side topology, and it does not expose or stabilize the
private retained JSON format or path.

### Meaning and authority

A retained name means only:

> When the operator explicitly requests an external-information operation and
> supplies no explicit plugin name for that invocation, use this previously
> selected exact acquisition plugin.

It does not mean that the plugin is installed, compatible, healthy, configured,
credentialed, or network-reachable. It does not authorize startup activity,
background acquisition, ordinary Chat acquisition, inference of another
plugin, or provider selection. A retained declaration may therefore exist when
its distribution is absent.

### Effective selection

The complete bounded selection rule is:

```text
explicit --plugin NAME       -> NAME for this invocation only
otherwise retained name      -> retained name
otherwise                    -> current invalid-input behavior
```

An explicit `--plugin NAME` temporarily replaces the retained choice and never
mutates it. For example, with retained `tavily`,
`hac external-information --plugin searxng QUERY QUESTION` uses `searxng` for
that invocation; the next invocation without `--plugin` uses `tavily` again.
There is no merge, ranking, list, provider arbitration, or general precedence
framework.

When a retained choice exists, the RFC-0091 daily-use form is available:

```text
hac external-information QUERY QUESTION
```

`QUERY` remains the distinct operator-supplied acquisition query and `QUESTION`
the distinct source-grounded question. HAC must not collapse them or generate a
query automatically.

The existing explicit RFC-0078 path should remain self-contained as far as
practical. An explicit `--plugin` wins completely over any retained
external-information plugin choice: no retained plugin value may influence that
operation. This statement is scoped to plugin selection; it does not define
general retained-state recovery semantics.

### Configuration ownership and validation

The retained name may be set or replaced atomically, removed or reset, and
shown through existing retained-configuration display. A later implementation
may choose a small finite `hac config` subcommand consistent with RFC-0094; the
exact CLI spelling is not frozen here.

Configuration-time validation validates name syntax only. It must not enumerate
or discover entry points, import a plugin, verify compatibility, inspect plugin
configuration or credentials, contact Tavily or SearXNG, or probe network or
service health. Retention records an operator choice, not live installation
truth.

HAC must not retain API keys, tokens, passwords, provider endpoints, SearXNG
lifecycle state, provider health, search parameters, filters, result counts,
cost/quota, timeout policy, fallbacks, ordered plugin lists, or provider option
dictionaries.

### Operation-time behavior

Only an explicit external-information operation performs the established
RFC-0078 selected-plugin behavior: locate exactly one matching entry point,
lazy-load it, validate its asynchronous callable contract, invoke it once,
reconstruct and validate fresh RFC-0077 evidence, and use the existing
source-grounded Chat path.

If the selected retained plugin is missing, duplicated, incompatible, unable to
load, missing provider configuration or credentials, unable to acquire, or
returns invalid data, RFC-0078's existing privacy-safe
`external-information-acquisition-failed` behavior applies where RFC-0078
assigns it. HAC must not fall back, select another installed plugin, repair or
mutate retained state, or retry through another provider.

### Tavily and SearXNG boundaries

This RFC makes no change to RFC-0093 credential ownership. `TAVILY_API_KEY`
remains entirely plugin/operator-owned: HAC does not retain, read during
configuration, show, validate, or persist it; it adds no secrets manager or OS
keyring support and does not modify the Tavily plugin. If `tavily` is retained
but the key is absent, an explicit operation reaches the selected plugin under
normal RFC-0078 operation-time behavior and fails through the existing
privacy-safe acquisition failure. There is no prompt, fallback, repair, or
credential persistence.

Similarly, retaining `searxng` does not make HAC own, configure, start, stop,
probe, or repair SearXNG. RFC-0079 remains authoritative. The different Tavily
and SearXNG setup shapes support retaining only their common selection fact.

### `hac config show`

`hac config show` may display the retained name when present, conceptually:

```text
External information
  plugin: tavily
```

It reports what the operator configured, not current plugin or provider status.
It is read-only and must not discover, import, or probe anything. It must not
display credential values or presence, installed/missing status, compatibility,
health, endpoint reachability, quota/cost, or provider-specific configuration.

### Startup and ordinary Chat invariants

A retained choice has zero effect on ordinary HAC startup. Startup must not
inspect the RFC-0078 group, import the retained plugin, read credentials,
contact a provider or service, start a service, or alter topology, routing,
adapters, or capabilities.

`hac chat QUESTION` remains unchanged. Even with retained `tavily`, an
installed Tavily plugin, and a present `TAVILY_API_KEY`, ordinary Chat must not
automatically acquire external information. Whether ordinary Chat may decide to
acquire information is a separate investigation and RFC.

### Compatibility

With no retained external-information choice, current explicit RFC-0078
behavior remains: `--plugin NAME` is required, startup and ordinary Chat are
unchanged, installed plugins remain inert, and no discovery occurs outside an
explicit acquisition. No external-network authority is added.

With a retained choice but no explicit external-information operation, HAC must
perform no plugin discovery/import, credential read, provider/service request,
ordinary Chat change, or background work. This is a primary privacy and
authority guarantee.

## Relationship to existing RFCs

### RFC-0078 revision

RFC-0078 treats the selected name as a caller-edge per-operation value rather
than a core configuration preference. This RFC revises that narrow statement:
one operator-retained exact name may satisfy selection only when an explicit
external-information operation omits `--plugin`. All other RFC-0078 boundaries
remain intact, including exact selection, one invocation, explicit-only lazy
loading, no automatic selection/fallback, provider-owned configuration and
credentials, complete RFC-0077 reconstruction, no ordinary-server authority,
and privacy-safe failures.

### RFC-0094 relationship

RFC-0094 established the retained local configuration substrate and temporary
explicit override pattern, while deliberately excluding external-information
configuration. This RFC extends the closed retained state by one orthogonal
selection domain only. It introduces neither a generic configuration framework
nor a reinterpretation of RFC-0094 runtime or topology ownership.

### RFC-0091 relationship

RFC-0091 retains `hac external-information --plugin NAME QUERY QUESTION` as
the shorter explicit form. This RFC additionally permits
`hac external-information QUERY QUESTION` only when a retained choice exists;
it does not change query/question semantics.

## Non-goals

This RFC does not authorize credential persistence, Tavily key management,
secrets storage, provider-specific configuration, startup/configuration-time
provider discovery, installation-based inference, multiple retained plugins,
preference lists, fallback or alternate-provider retry, provider health,
ordinary Chat acquisition, answerability classification, autonomous research,
provider/service lifecycle management, a generic configuration framework, or a
generic plugin framework.

It specifically does not introduce `SourceProvider`, `PluginManager`, a
provider registry, preference engine, health system, generic plugin config, or
generic secrets storage.

## Alternatives considered

### Keep per-operation `--plugin`

This preserves RFC-0078 exactly, but leaves demonstrated repeated stable-choice
friction.

### Infer the only installed plugin

Rejected. Installation is availability, not authority.

### Retain multiple plugins or an ordered preference

Rejected. This immediately requires selection and failure policy, provider
arbitration, and a preference framework.

### Retain a plugin plus credentials

Rejected. It creates secret and provider ownership beyond the demonstrated
selection problem.

### Retain a plugin plus generic external-network permission

Rejected. It prematurely combines explicit selection with the separate future
ordinary-Chat autonomy question.

### Plugin-owned default selection

Rejected. The cross-provider choice belongs to HAC/operator configuration, not
one provider plugin.

## Rationale

Repeated plugin selection is demonstrated operator friction. One exact retained
name is the smallest fact that removes it while leaving provider-specific setup
with the provider, plugin, and operator. Explicit external-information
invocation still supplies execution authority and ordinary Chat remains local
by default. Tavily and SearXNG differ materially, reinforcing that no generic
framework is needed.

## Proof expectations

A later implementation must prove:

1. no retained choice preserves the current explicit `--plugin` requirement;
2. a retained name permits an explicit operation without `--plugin`;
3. explicit `--plugin` overrides only one invocation and does not mutate state;
4. the next no-`--plugin` operation returns to the retained name;
5. configuration validates name syntax only, with no discovery, import, or network access;
6. retained choice alone causes no startup discovery/import/network access or ordinary Chat change;
7. a missing retained plugin and a missing Tavily credential use existing acquisition failure without fallback or retention;
8. `config show` reports only the retained name with no plugin/network observation;
9. removing the choice restores the explicit-plugin requirement;
10. zero installed plugins preserve ordinary HAC behavior; and
11. no credentials enter retained state.

## Open questions

None within this RFC's architectural scope.

## Decision

Accepted. HAC may retain one optional exact RFC-0078 acquisition-plugin name
as baseline selection only for an explicit external-information operation. An
explicit `--plugin` temporarily replaces that selection for one invocation;
with neither value, current invalid-input behavior remains. Configuration
validates syntax only, while RFC-0078 remains responsible for operation-time
validation and its privacy-safe failure behavior.

Credentials and provider configuration remain plugin/operator-owned; HAC does
not retain a Tavily key. Retention grants no startup or ordinary Chat authority,
and this decision adds no fallback, provider list, generic configuration,
plugin, provider, or secrets framework.
