# Release Direction to 1.0

Status: Non-binding direction

This document records a working release direction from the current `0.5`
development line through `1.0.0`.

It is deliberately not a roadmap, backlog, release promise, implementation
authorization, or architectural decision. The completed historical
[`ROADMAP.md`](../ROADMAP.md) remains a record of the founding architecture
proof. Accepted RFCs remain the sole authority for architectural decisions.

The purpose of this document is narrower: give future work a stable release
shape, reduce repeated planning, and keep new ideas from silently expanding the
scope required for `1.0.0`.

## Decision boundaries

This direction does not pre-approve any candidate work named below.

In particular:

- architectural changes still require investigation and an accepted RFC before
  implementation;
- release numbers do not replace RFCs or map to new formal roadmap phases;
- candidate integrations do not select a provider or grant network authority;
- candidate configuration work does not define a configuration format,
  discovery rule, precedence policy, or secrets contract;
- candidate automatic behavior does not authorize model-directed retrieval,
  agents, research loops, retries, or implicit external network access; and
- current accepted boundaries remain authoritative until explicitly revised by
  later accepted RFCs.

## Scope-control rule

New ideas do not automatically extend this direction.

A new idea should first be tested against the theme and exit condition of the
current release. If it is not needed to satisfy that release theme, it should be
deferred rather than added merely because it is useful or interesting.

The default sequence for an architectural idea remains:

```text
observation or operator friction
  -> bounded investigation
  -> RFC when a durable decision is required
  -> small implementation
  -> proof or operator validation when useful
```

This direction should change only when accumulated evidence shows that one of
its release themes is wrong or materially incomplete.

## Release shape

| Version | Theme | Product question |
| --- | --- | --- |
| `0.5.0` | Discoverable / public preview | Can a new user find, understand, install, and first-use HAC? |
| `0.6.0` | Comfortable / daily driver | Can ordinary use stop feeling like prototype operation? |
| `0.7.0` | Interchangeable / acquisition and integrations | Do external boundaries work across genuinely different integrations? |
| `0.8.0` | Configurable and boundedly autonomous | Can HAC retain operator choices and act naturally within explicit authority? |
| `0.9.0` | Predictable / 1.0 candidate | Do we know exactly what `1.0` will promise not to break? |
| `1.0.0` | Stable local AI cluster | Is the fundamental HAC product contract stable? |

## 0.5.0 — Discoverable / public preview

### Goal

Make the existing product understandable and usable by someone who did not
participate in its development.

This release should favor consolidation and public presentation over new core
architecture.

### Candidate focus

Candidate work may include:

- finishing the static documentation site and its visual identity;
- keeping installation and first-use guidance short and current;
- aligning README, Getting Started, command reference, and operator guidance;
- adding the project logo, favicon, and domain work through separately bounded
  changes when ready;
- investigating a small multilingual entry layer for users who are not
  comfortable with English while preserving repository Markdown as the
  canonical technical source; and
- fixing concrete documentation, packaging, release, or usability defects found
  during review.

Multilingual structure is a candidate investigation, not an accepted content or
site architecture.

### Exit condition

A new user can understand what Home AI Cluster is, install the published
package, start the ordinary local path, and obtain a first result without
needing historical project knowledge.

## 0.6.0 — Comfortable / daily driver

### Goal

Remove repeated operator friction without making HAC own external service or
runtime lifecycle.

The preferred question is not "what feature can be added?" but "what repeated
work can be removed while preserving the same authority boundaries?"

### Candidate focus

Candidate investigations may include:

- simplifying `external-information` invocation so ordinary use does not require
  unnecessary repeated `plugin`, `query`, and `question` ceremony;
- documenting one boring operator-owned SearXNG service setup so normal use does
  not require manually starting it for every search;
- improving repeated startup, runtime/model selection, diagnostics, failure
  messages, and command consistency where real daily use demonstrates friction;
- keeping CLI and fixed-loopback browser behavior coherent; and
- identifying which operator choices are repeated often enough to justify later
  retained configuration.

This release does not, by itself, authorize HAC to install, configure, start,
stop, upgrade, supervise, repair, or health-manage SearXNG or any other external
service.

It also does not require a general automatically discovered HAC configuration
file. Repeated friction should first provide evidence for what such a file would
need to retain.

### Exit condition

An operator can leave HAC installed and use it repeatedly without reconstructing
prototype-era command details for ordinary work.

## 0.7.0 — Interchangeable / acquisition and integrations

### Goal

Prove that accepted external boundaries are genuinely independent of one
provider or one proof integration.

### Candidate focus

A strong candidate is a second separately packaged external-information
acquisition plugin using the already accepted category-specific plugin boundary.
Tavily is a useful investigation candidate because it represents a materially
different trade-off from SearXNG:

- SearXNG is free/open, operator-owned, and locally operated but requires service
  installation and lifecycle ownership;
- Tavily is an external account/API service and requires provider credentials,
  but removes local service administration and currently offers a useful free
  personal quota.

A first Tavily plugin, if separately investigated and accepted, should remain as
small as the existing acquisition contract permits: one explicit query, one
bounded provider operation, a small source set, and only title/URL/content
candidate data crossing into existing HAC validation. Provider-generated
answers, crawl, research loops, repeated acquisition, and broad SDK/provider
abstractions are not implied.

Other candidate investigation may include selectively using more existing
SearXNG features such as language, category, time range, or bounded result depth
only where concrete value justifies a contract change.

### Exit condition

A second materially different integration can use an existing HAC boundary
without changing cluster-facing concepts or turning that boundary into a generic
plugin framework.

## 0.8.0 — Configurable and boundedly autonomous

### Goal

Let an operator retain stable choices once and allow HAC to act naturally only
within those explicitly granted boundaries.

This is expected to be the most architecture-sensitive pre-1.0 release theme.

### Candidate canonical configuration investigation

By this point, accumulated daily-use evidence may justify revisiting the earlier
choice to require explicit paths for retained configuration.

A bounded investigation may ask whether HAC should have one canonical
user-level configuration location, following the platform's standard user
configuration convention, with absence preserving current behavior and an
explicit alternate-path mechanism only if justified.

Questions that require an RFC include at least:

- canonical location and discovery semantics;
- the exact closed facts that belong in the file;
- whether topology remains a separate document or is presented through one
  user-facing configuration surface while preserving internal ownership
  boundaries;
- configuration-versus-CLI precedence;
- invalid-file and partial-configuration behavior; and
- whether any provider credential belongs there at all.

The simplest acceptable result is preferred. A general configuration framework,
profiles, includes, inheritance, broad environment-variable precedence, and
arbitrary extension sections are not goals.

### Candidate external-information default

If an operator has explicitly retained one acquisition-plugin choice, ordinary
external-information use may no longer need to repeat the plugin name on every
invocation.

This must remain an operator-owned network-boundary choice. Installation alone
must not become permission for use or automatic provider selection.

Provider credentials should remain provider-owned unless a later accepted RFC
explicitly establishes a different secrets boundary.

### Candidate bounded external-information fallback for Chat

A later investigation may ask whether ordinary Chat can, when explicitly
authorized by the operator, perform one bounded decision between answering
locally and requiring external information.

The smallest credible shape is intentionally finite:

```text
one Chat question
  -> one bounded local answerability decision
  -> local answer
     OR
  -> at most one acquisition through the operator-approved plugin
  -> at most one source-grounded Chat request
  -> finish
```

This candidate must not imply automatic network authority by default. It also
must not become a research agent: no open-ended loop, repeated search, provider
fallback, URL following, crawler, model-directed tool loop, or background work.

The desired product property is:

> local first, not local only

while preserving the stronger project rule that the user defines the external
boundary before HAC acts within it.

### Exit condition

Ordinary repeated choices can be retained without hidden magic, and any
automatic behavior remains finite, inspectable, privacy-aware, and constrained
by prior operator authority.

## 0.9.0 — Predictable / 1.0 candidate

### Goal

Stop expanding the product shape and determine exactly which contracts are ready
to become stable.

This is a relative feature and architecture freeze. New work should need a high
bar: it should fix a concrete blocker to an honest `1.0.0`, not merely improve
an interesting area.

### Candidate focus

Review and harden:

- supported install and upgrade paths;
- a supported low-friction Windows installation path that does not require prior
  Python knowledge and preserves the existing package/plugin model;
- supported Python versions and package/release automation;
- ordinary CLI contracts and configuration behavior;
- local and explicit static-cluster operation;
- capability semantics and routing attribution;
- runtime-adapter and remote-node boundaries;
- fixed-loopback browser behavior;
- external-information and installed-plugin trust boundaries;
- any accepted canonical configuration contract;
- any accepted bounded external fallback contract;
- credentials, configuration-file permissions, diagnostics, logging, history,
  and external disclosure boundaries;
- documentation and examples; and
- which peripheral integrations remain explicitly bounded or experimental even
  when the core becomes stable.

### Candidate low-friction Windows installation

Before `1.0.0`, a Windows user should have one supported installation path that
does not require understanding Python packaging or `uv` before installing HAC.
The exact delivery mechanism is deliberately not selected here: a small
PowerShell bootstrap, package-manager path, traditional installer, or another
boring mechanism should be compared on evidence rather than assumed now.

The installation path should preserve the existing separately packaged plugin
model rather than forcing plugins into a frozen HAC executable merely for
installer convenience. It should install HAC and make its command available;
it should not silently become a runtime, model, SearXNG, firewall, service, or
external-provider lifecycle manager.

A polished `.exe` or `.msi` is therefore not itself a `1.0` requirement. The
product requirement is lower friction: an ordinary Windows user can install HAC
without prior Python knowledge while the resulting installation preserves the
same understandable ownership boundaries as other platforms.

### Exit condition

The project can state precisely what `1.0.x` intends to preserve and what remains
outside that compatibility promise, and one supported Windows installation path
is practical for a user who does not already know the Python toolchain.

## 1.0.0 — Stable local AI cluster

### Goal

`1.0.0` means that the fundamental Home AI Cluster product contract is stable.
It does not mean that every imaginable AI-infrastructure feature has been
implemented.

The stable product should remain recognizable as:

> Many machines. One AI.

An operator addresses one capability-centered local system rather than choosing
runtime brands or machines for ordinary requests. Multiple personal machines and
replaceable runtimes may participate while topology, runtime lifecycle, trust,
and external-information authority remain understandable and operator-owned.

A stable `1.0.0` may include retained operator configuration and bounded external
information only if those behaviors have first been separately investigated,
accepted where architectural, implemented in small steps, and proven before the
`0.9` freeze.

### Not required for 1.0

`1.0.0` does not require Home AI Cluster to become an infrastructure platform.
In particular, the release direction does not require:

- automatic node discovery;
- scheduling or dynamic ranking;
- runtime or model lifecycle management;
- a generic agent framework;
- a generic plugin framework;
- a database or general persistence layer;
- a dashboard architecture;
- Docker or Kubernetes architecture;
- cloud control-plane behavior;
- broad OpenAI API emulation;
- distributed inference; or
- open-ended autonomous research.

Any later need for those areas must stand on its own evidence and project
decision process rather than being treated as unfinished `1.0` work.

### Exit condition

The project is willing to treat the fundamental local-first,
privacy-first, engine-independent, capability-centered operator contract as a
stable compatibility promise rather than an early prototype shape.

## Working shorthand

The intended maturation sequence is:

```text
0.5  discoverable
0.6  comfortable
0.7  interchangeable
0.8  configurable and boundedly autonomous
0.9  predictable
1.0  stable
```

The desired outcome is not a much larger system. It is a system that is easier
to use, easier to explain, and more predictable without becoming harder to
understand.