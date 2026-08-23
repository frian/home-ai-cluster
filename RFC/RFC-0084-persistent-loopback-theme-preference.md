# RFC-0084: Persistent Loopback Theme Preference

Status: Accepted

Date: 2026-08-23

Author: frian

## Summary

The fixed loopback browser may retain one browser-local presentation
preference: an explicit Light or Dark override. The browser will expose exactly
three choices, **System**, **Light**, and **Dark**. System is the default and
continues to use the existing automatic `prefers-color-scheme` behavior. Light
and Dark apply immediately and persist only in `localStorage` for the same
browser profile and loopback origin.

This RFC creates one closed exception to RFC-0062 and RFC-0070's previous
blanket prohibition on browser persistence. It permits only the key
`home-ai-cluster.theme`, with only `light` or `dark` as stored values. System
means the key is absent. The exception does not permit persistence of a
request, response, conversation, file, filename, capability, operational, or
server state, and authorizes no implementation.

## Problem

The loopback browser already contains light and dark CSS custom-property
palettes and currently selects between them automatically with
`prefers-color-scheme`. A person who prefers a different presentation than
their operating-system setting has no manual override. A non-persistent
selector would lose that choice on each reload or browser restart.

The project needs a narrowly bounded decision before retaining even this
non-sensitive browser-side value, because RFC-0062 and RFC-0070 deliberately
exclude browser persistence to protect ephemeral request and content state.

## Goals

This RFC accepts a later implementation that will:

* expose exactly System, Light, and Dark;
* keep System as the default and preserve the current automatic
  `prefers-color-scheme` behavior;
* apply an explicit Light or Dark choice immediately and persist only that
  override;
* keep the preference browser-local, origin-local, and presentation-only;
* preserve accessibility, visible labeling, keyboard use, focus behavior,
  narrow-screen behavior, existing palettes, and local-first/privacy-first
  defaults; and
* remain plain HTML, CSS, and JavaScript with no dependency or frontend
  toolchain.

## Non-goals

This RFC does not authorize additional themes, user-defined colors, account or
identity preferences, server-side preferences, cookies, server sessions,
databases, synchronization across browsers, profiles, devices, or origins,
configuration-file integration, or query parameters.

It does not authorize request or response persistence, conversation history,
file or filename persistence, operational settings, runtime, model, node,
adapter, routing, or capability selection, analytics, telemetry, a frontend
framework, package manager, bundler, build step, or a redesign of the existing
light or dark palettes.

It does not authorize an API, endpoint, transport, exposure, orchestration, or
server-state change. Chat, Summarize, Classify, and Code request/content state
remain ephemeral as already decided.

## Proposal

### Exact presentation choices

The fixed loopback browser will offer exactly these three user-facing choices:

```text
System
Light
Dark
```

System is the default. With System selected, no manual browser override is in
effect and the existing `prefers-color-scheme` CSS behavior controls the
palette. Selecting Light or Dark applies that palette immediately. Small markup
and styling details remain implementation details, provided the exact
three-option behavior and accessibility requirements remain true.

### Storage contract

The entire retained browser state authorized by this RFC is:

```text
localStorage key: home-ai-cluster.theme
allowed stored values: light, dark
absence of key: System
```

Selecting System removes `home-ai-cluster.theme`; it must not store `system` or
any third value. A valid `light` or `dark` value restores the corresponding
manual override after page reloads and browser restarts for the same browser
profile and origin.

An absent, invalid, unreadable, or unwritable value fails safely to System.
Invalid values are ignored and should be removed when storage access permits,
or otherwise treated as absent. A storage read, write, or removal failure must
not break the page, prevent ordinary browser use, or create another retained
state path.

No cookie is created. The stored value is never included in an HTTP request,
server state, request body, response, URL, API contract, or capability/routing
decision. It has no synchronization mechanism across browsers, profiles,
devices, or origins.

### Closed persistence boundary

This is a browser-local presentation preference, not request, response,
conversation, file, filename, capability, operational, or server state. The
exception is closed to one fixed non-sensitive key and two fixed values. It
does not establish a general browser-settings abstraction, a general
persistence policy, or permission to retain any other application state.

In particular, a browser implementation must not persist prompts, responses,
Chat or Code messages, Summarize or Classify text, selected labels, selected
files or filenames, uploaded-file facts, request activity or safe failures,
capability state, node attribution, model/runtime facts, routing facts, or
operator/runtime configuration. It also must not use the key as an indirect
carrier for any such state.

### Relationship to accepted RFCs

RFC-0062 intentionally prohibited browser persistence to protect request and
conversation state in the fixed loopback client. RFC-0070 preserved that
boundary for Code content. RFC-0084 narrowly amends their blanket
no-browser-storage language only enough to permit the exact
`home-ai-cluster.theme` preference described above.

RFC-0062 and RFC-0070 remain authoritative for the loopback-only,
same-origin, fixed-asset, privacy, safe-failure, API-only receiver,
non-dashboard, and text-only boundaries. RFC-0083's current-page-only Code
conversation remains ephemeral. This RFC authorizes no persistence of content
or state protected by any of those RFCs. All other browser-state, privacy,
exposure, and authority boundaries remain unchanged.

### Expected later implementation surface

A separate implementation PR may be limited to the smallest likely surface:

* `src/home_ai_cluster/web/index.html`;
* `src/home_ai_cluster/web/assets/app.css`;
* `src/home_ai_cluster/web/assets/app.js`; and
* `tests/test_loopback_browser.py`.

The current test assertions that reject every use of `localStorage` will need
to become narrower guarantees: only `home-ai-cluster.theme` may be persisted,
and only `light` or `dark` may be stored. This RFC itself changes none of those
files.

## Rationale

The existing system-controlled palettes already provide the presentation
mechanism. One explicit preference makes the browser more usable for someone
whose operating-system choice is not their preferred application presentation,
without changing requests, results, routing, or browser exposure.

The bounded contract keeps ownership clear: the browser alone reads and writes
one non-sensitive value for its own origin; the native application never sees
or owns it. System removal provides an obvious way to return to the existing
automatic behavior. This is smaller than an account preference, cookie,
server-side setting, or a generic client-preferences system.

## Alternatives considered

### Keep automatic system-only behavior

Rejected. It retains the existing simple behavior but does not let a person
override an unsuitable operating-system preference.

### Add a non-persistent selector

Rejected. It would apply a manual choice only until reload, which does not meet
the identified convenience need and makes the selector feel unreliable.

### Use cookies

Rejected. Cookies are sent with requests and would create an unnecessary HTTP
state and server-visible surface for a browser-only presentation choice.

### Use server-side sessions or configuration

Rejected. Server persistence or configuration assigns a presentation concern to
the native application, adds retention and operational responsibility, and
does not remain browser/profile/origin-local.

### Store `system` explicitly

Rejected. Absence already accurately represents System, preserves the current
default, and makes removal straightforward. A third stored value would broaden
the closed storage contract without benefit.

### Add themes or user-customizable palettes

Rejected. More palettes, colors, and customization introduce a broader visual
settings product and persistence policy than this narrow override requires.

## Trade-offs

This is the first intentionally retained browser-side value, so it slightly
weakens the previous absolute statement that the browser stores no state. The
exception is acceptable because it is one fixed non-sensitive key with two
closed values, carries no content or identity, is never sent on the network,
has obvious removal through System, and gives the backend no responsibility.

The implementation must handle unavailable browser storage defensively and
will require focused tests that distinguish this exact exception from all other
forbidden persistence. Those costs are smaller than retaining the preference
in a cookie, server session, database, or general settings system.

## Proof expectations

A later implementation proof must verify at least that:

1. the control exposes exactly System, Light, and Dark;
2. no stored key leaves the existing system preference in control;
3. selecting Light applies and persists the light override;
4. selecting Dark applies and persists the dark override;
5. selecting System removes the stored override;
6. reload restores a valid manual override;
7. invalid or unavailable storage falls back safely to System;
8. only `home-ai-cluster.theme` and only `light` or `dark` are permitted;
9. no cookie, server state, request-field change, API change, or content
   persistence is introduced;
10. existing capability behavior and ephemeral request/content state remain
    unchanged;
11. keyboard use, visible labeling, focus behavior, and narrow-screen layout
    remain accessible; and
12. no external dependency or frontend toolchain is added.

## Impact

Acceptance authorizes only a later separate implementation PR within the
expected surface above. It does not itself implement a selector or change HTML,
CSS, JavaScript, tests, dependencies, lockfiles, APIs, routes, request or
response schemas, runtime behavior, routing, server persistence, or browser
exposure.

## Open questions

None.

## Decision

Accepted. RFC-0084 authorizes a later separate implementation of exactly one
persistent, browser-local loopback presentation preference: System, Light, or
Dark, where System is the default and is represented by absence of
`home-ai-cluster.theme`, and Light/Dark are represented only by `light`/`dark`
in `localStorage`. It narrowly amends RFC-0062 and RFC-0070 for this exact
exception and does not authorize implementation or any other browser, content,
cookie, server, API, routing, capability, authority, or exposure change.
