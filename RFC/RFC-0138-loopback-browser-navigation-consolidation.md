# RFC-0138: Bounded Loopback Browser Navigation Consolidation

Status: Draft

Date: 2026-09-19

Author: frian

## Summary

This RFC proposes one presentation-only consolidation of the ordinary/native
loopback browser before v1.1.  Its primary navigation becomes:

```text
Chat
Code
Image
Summarize
Classify
Configuration
```

The existing explicit RFC-0133 External Information operation is removed from
top-level navigation but remains a distinct, visible secondary operation within
the Chat presentation.  The existing automatic conversational External
Information operation from RFC-0134 remains ordinary Chat behavior, with its
current-page authorization and all of its existing limits unchanged.

The Chat presentation may declaratively show the one retained RFC-0095 plugin
name, if any.  That display is retained-configuration state only: it neither
claims nor checks plugin installation, readiness, health, credentials, or
provider reachability.  No endpoint, request contract, retained fact, routing,
plugin behavior, or trusted-LAN External Information authority changes.

## Context

RFC-0062 establishes the fixed ordinary/native loopback browser.  RFC-0077
establishes source-grounded Chat from supplied evidence, while RFC-0078 keeps
External Information acquisition bounded to one selected plugin and one
acquisition before source-grounded Chat.  RFC-0095 permits retaining one exact
plugin selection without making it installation or execution truth.  RFC-0096
separately defines retained one-shot native Chat authorization.

RFC-0132 permits the loopback Configuration facade to read and mutate the
existing retained External Information plugin choice, without discovery,
loading, provider activity, or automatic acquisition.  RFC-0133 then adds one
separate top-level loopback External Information view: optional exact plugin
override, distinct `QUERY` and `QUESTION`, one explicit submit action, one
acquisition, and source-grounded Chat.  RFC-0134 preserves that explicit view
and independently adds the optional current-page automatic External Information
authorization to ordinary loopback Chat.

RFC-0130 is a separate capability-only trusted-LAN browser authority.  It
excludes Configuration and all External Information authority.

The current ordinary loopback presentation consequently has separate
top-level Chat and External Information views.  Its Configuration view already
has access to the retained plugin-selection facade.  This RFC changes only how
these accepted browser operations are presented together.

## Problem

The primary navigation gives a separate top-level position to an optional
acquisition mechanism, rather than emphasizing the ordinary user-facing HAC
capabilities.  Yet External Information is assistance to Chat in two clearly
different accepted modes:

1. automatic conversational assistance under RFC-0134; and
2. explicit `QUERY`/`QUESTION` acquisition under RFC-0133.

Keeping those modes separate is essential to their privacy, authority, and
failure boundaries.  Keeping their presentations separate at the top level is
not.  Moving the explicit form without an RFC would silently amend RFC-0133's
separate-view requirement and RFC-0134's preservation of it.

## Goals

- Make the ordinary loopback primary navigation capability-oriented and keep
  Configuration last.
- Co-locate the two accepted External Information modes in Chat without
  merging their operations or authority.
- Preserve RFC-0133's explicit plugin override, `QUERY`, `QUESTION`,
  acquisition, source-grounded Chat, provenance, failure, cancellation, and
  loopback authority semantics.
- Preserve RFC-0134's current-page automatic Chat authorization and all its
  disclosure, decision, and failure semantics.
- Allow only declarative display of the already retained plugin selection.
- Preserve the capability-only trusted-LAN browser authority.

## Non-goals

This RFC does not add or change:

- HTTP endpoints, including `/v1/chat`, `/v1/chat/sources`, or existing
  browser-facade request or response formats;
- External Information acquisition, source provenance, plugin selection,
  `QUERY`/`QUESTION`, or RFC-0134 automatic-question-as-query semantics;
- plugin enumeration, dropdown discovery, installation detection, loading or
  compatibility probes, credential checks, provider health/reachability checks,
  or provider activity for page display;
- polling, background work, browser or server persistence, new retained
  configuration, or a plugin manager/status API;
- a new `external-information` capability, query generation or rewriting, or
  merging explicit `QUERY`/`QUESTION` into ordinary Chat;
- routing, remote transport, adapters, runtimes, receiver authority, or
  Configuration authority; or
- trusted-LAN External Information or dashboard work.

## Proposal

### Primary loopback navigation

The ordinary/native loopback browser primary navigation is exactly:

```text
Chat
Code
Image
Summarize
Classify
Configuration
```

`Configuration` remains last.  `Image` is an allowed visible presentation
label only.  It does not rename the `image-generation` capability, Image
Generation result semantics, endpoint, request, retained configuration key,
routing capability, transport kind, adapter operation, CLI command, or
documentation vocabulary where Image Generation is semantically required.

This is browser presentation only.

### One Chat presentation, two External Information operations

The dedicated top-level External Information navigation item and view are
removed.  RFC-0133's explicit External Information operation instead appears
as a clearly distinct secondary section within the Chat presentation.  A
collapsed or expandable section conceptually named `Explicit external
information` is acceptable, but exact HTML, controls, layout, and styling are
implementation details.

After this amendment, the required distinction is:

```text
Chat top-level view
  |- ordinary Chat, optionally using RFC-0134 automatic assistance
  `- distinct RFC-0133 explicit External Information operation
```

The visible form, explicit action, and operation boundary must remain distinct;
a separate top-level navigation tab is no longer required.

### Preserved explicit operation

The co-located RFC-0133 operation retains exactly its accepted semantics:

- optional exact plugin-name override;
- required acquisition `QUERY`;
- required source-grounded Chat `QUESTION`;
- its own explicit `Acquire and ask` action and operation result;
- supplied-source provenance;
- the existing loopback-only same-origin authority and RFC-0133 acquisition
  route/facade; and
- one selected plugin, one acquisition, and one source-grounded Chat operation.

It is operationally distinct from ordinary Chat.  Ordinary Chat `Send` must
not submit the explicit fields; `Acquire and ask` must not become ordinary
Chat; `QUERY` and `QUESTION` remain distinct; and plugin override remains
explicit.  RFC-0133 failure and confirmed-disconnect ownership are unchanged.

This narrowly amends RFC-0133's separate-browser-view requirement at the
presentation/navigation level only.  RFC-0133 continues to own explicit
override, acquisition, source-grounded execution, provenance, authority,
failures, and cancellation.

### Preserved automatic conversational operation

Ordinary loopback Chat retains RFC-0134 automatic External Information under
its existing visible control.  It remains OFF by default, current-page-only,
non-persistent, and independently sufficient authorization for that browser
surface.  It continues to use the existing RFC-0134 browser facade.

When its external branch is selected, the exact newest user turn remains both
the decision subject and acquisition `QUERY`.  It retains all existing bounds:
newest-turn-only decision and query, no query generation, rewriting, planning,
or history disclosure to the acquisition plugin, and no ordinary fallback once
acquisition has started.

The automatic RFC-0134 operation and explicit RFC-0133 operation remain two
different operations even though the user sees them in one Chat panel.
RFC-0134 continues to own automatic authorization, decision, conversational
prior-message handling, provenance, and failure behavior.

### Declarative retained-plugin state

The Chat presentation may show the retained RFC-0095 External Information
plugin choice through the existing ordinary-loopback retained-configuration
surface.  Conceptually:

```text
External information plugin: searxng
```

or, when absent:

```text
No External Information plugin configured
```

This is only declarative retained-configuration state.  It must not claim that
the plugin is installed, discovered, unique in the entry-point group,
importable, loadable, compatible, provider-configured, credential-ready,
reachable, healthy, or currently usable.

Page load and this display must not discover entry points, import or load a
plugin, inspect credentials, contact a provider, perform DNS or HTTP, or
trigger acquisition.  No new backend endpoint, plugin-status/health/discovery
API, or retained field is authorized.

### Automatic-control presentation when selection is absent

When there is no retained plugin selection, the browser may disable the
automatic External Information Chat control and explain that no External
Information plugin is configured.  This is UI eligibility/presentation only:
it does not change RFC-0134 backend semantics or authorization, and the
control remains OFF by default.

If the same page successfully saves or clears the retained plugin through the
existing Configuration surface, it may immediately update the declarative
state and the automatic-control enabled/disabled presentation.  This adds no
polling, filesystem watching, external configuration monitoring, browser
storage, or background refresh.  A change made elsewhere may require an
ordinary page reload before the presentation changes.

The explicit RFC-0133 operation must not be globally disabled merely because
no retained selection exists.  Its existing selection rules remain:

```text
retained selection + blank override  -> retained selection
no retained selection + valid override -> explicit selection
no retained selection + blank override -> bounded failure before plugin activity
```

Automatic Chat presentation must not collapse or redefine those explicit
operation rules.

### Configuration and trusted-LAN boundaries

Configuration remains the existing retained-configuration surface and last in
primary navigation.  This RFC does not change retained configuration format,
configuration authority, plugin-selection semantics, Chat retained one-shot
authorization, Image Generation configuration, remote-node configuration, or
runtime configuration.

RFC-0130 trusted-LAN browser authority remains capability-only.  Its visible
capability order may align to:

```text
Chat
Code
Image
Summarize
Classify
```

It gains no External Information operation, automatic authority,
retained-plugin display, Configuration, discovery, import, or provider
authority.  This is presentation order only; its closed route and authority
boundaries remain unchanged.

### Responsive presentation

Existing responsive/mobile browser behavior remains in place.  This RFC does
not define a responsive architecture.  Later implementation should preserve
the existing mobile and tablet behavior while changing navigation order and
presentation grouping.

## Relationship to RFC-0133 and RFC-0134

This RFC narrowly amends only their browser presentation relationship:

```text
Before
  Chat top-level view
  External Information top-level view

After
  Chat top-level view
    - ordinary/automatic Chat operation
    - distinct explicit External Information operation
```

No semantic contract is merged.  RFC-0133 retains ownership of the explicit
operation; RFC-0134 retains ownership of automatic conversational assistance.
Their existing routes, request/response contracts, authority, acquisition,
provenance, cancellation, and failure semantics remain unchanged.

## Rationale

Primary navigation should emphasize user-facing HAC capabilities rather than
one optional acquisition mechanism.  External Information is useful as
assistance to Chat, but its two accepted modes have different, visible privacy
and authority boundaries.  Co-location makes the browser easier to understand
without flattening those boundaries.  Keeping Configuration last preserves its
role as an operator-control surface rather than an ordinary capability.

## Consequences and later proof expectations

A later implementation should demonstrate at least that:

1. loopback navigation is Chat, Code, Image, Summarize, Classify,
   Configuration, with no top-level External Information tab;
2. the explicit form retains its operation shape and separates plugin override,
   `QUERY`, and `QUESTION` from automatic and ordinary Chat;
3. automatic Chat continues to use the RFC-0134 operation and defaults OFF;
4. displayed plugin state comes only from retained configuration;
5. absent retained selection disables only the automatic control, not valid
   explicit-override use;
6. an in-page retained plugin save or clear can update presentation without
   polling or persistence;
7. page load/state display causes no plugin discovery, import, or provider
   activity;
8. trusted-LAN remains capability-only with Chat, Code, Image, Summarize,
   Classify order;
9. responsive behavior remains intact; and
10. existing External Information and Chat backend routes and contracts are
    unchanged.

Existing structural or HTTP tests may prove these boundaries; this RFC does
not require browser-automation infrastructure.
