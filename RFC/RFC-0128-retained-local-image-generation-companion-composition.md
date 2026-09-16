# RFC-0128: Retained Local Image Generation Companion Composition

Status: Draft

Date: 2026-09-16

Author: frian

## Summary

This RFC proposes one optional HAC-managed retained companion to the existing
retained local textual-runtime domain:

```text
retained configuration
    +-- existing local textual/runtime domain
    +-- optional local Image Generation companion
    +-- existing remote nodes
    +-- existing external-information facts
    +-- existing Chat fallback fact
```

The companion retains only the already accepted stable-diffusion.cpp local
composition: explicit loopback HTTP `base_url`, fixed runtime identity
`stable-diffusion-cpp`, and exact execution ownership of
`image-generation`. It is configured separately:

```text
hac config image-generation --base-url http://127.0.0.1:<PORT>
hac config image-generation --reset
```

It is not generic retained capability-binding configuration. In particular, it
does not add retained textual execution-capability ownership or reinterpret
RFC-0059 `local_capabilities`, which remains caller-local static routing
permission.

Without an explicit `--runtime-config PATH`, ordinary `hac local` would
compose the existing effective textual runtime plus this optional companion.
A selected runtime-config remains a complete, self-contained, non-merging
alternative and bypasses both retained execution-composition domains.

## Context

RFC-0094 establishes HAC-managed retained configuration. Its existing
`config local` domain owns one singular textual local runtime composition,
RFC-0059 caller-local static routing permission, and retained HAC execution
limit. It is a complete replacement/reset operation, not a field-patch
surface. RFC-0125 adds temperature to its selected textual runtime domain.

RFC-0108 distinguishes local execution ownership from RFC-0059 caller-local
static routing permission. RFC-0110 accepts an explicit self-contained
multi-binding `--runtime-config PATH` document. RFC-0126 adds its closed
Image Generation binding:

```toml
[[bindings]]
capabilities = ["image-generation"]
runtime = "stable-diffusion-cpp"
base_url = "http://127.0.0.1:<PORT>"
```

RFC-0121 selects the operator-managed loopback `sd-server` composition behind
the `StableDiffusionCppAdapter`; RFC-0127 makes the accepted local Image
Generation capability available through ordinary `hac image-generation`
against a running local HAC process.

## Problem

An operator can retain a textual runtime once, but to use ordinary Code and
ordinary Image Generation on every startup must repeat the textual composition
as a binding in a self-contained multi-binding file and select it every time:

```text
hac local --runtime-config PATH
```

The desired daily-driver workflow cannot currently be expressed:

```text
configure textual local composition once
configure local Image Generation once
hac local
use both
```

Adding Image Generation fields to `hac config local` would be poor semantics.
That command requires `--runtime` unless resetting and replaces its complete
textual/local domain. Image-only configuration there would either require
repeating textual facts or turn the existing command into patch/merge
semantics.

## Goals

- Retain the one already accepted stable-diffusion.cpp local Image Generation
  composition through HAC's existing retained-configuration concept.
- Provide one separate complete-domain configuration command for it.
- Preserve `config local` and the historical singular textual runtime domain
  unchanged.
- Compose the companion with ordinary effective textual composition only when
  `--runtime-config` is absent.
- Preserve the self-contained runtime-config and RFC-0059 boundaries.

## Non-goals

This RFC does not add arbitrary retained `[[bindings]]`, binding arrays or
IDs, binding CRUD, provider IDs, generic runtime options, generic adapter
configuration, or capability-to-provider assignment. It does not add retained
textual execution-capability ownership or reinterpret `local_capabilities`
as it.

It does not add a second user-managed configuration file, explicit config path,
another TOML source, automatic discovery, profiles, includes, inheritance, or
manual retained-file editing. Storage path, JSON fields, and byte format remain
private implementation details under RFC-0094.

It adds no per-invocation Image Generation flags; model/model path; dimensions,
aspect ratio, seed, steps, sampler, scheduler, CFG/guidance, negative prompt,
style, quality, candidate count; runtime lifecycle; health/status/preflight;
model inspection; routing explanation; remote/receiver Image Generation;
transport changes; browser Image Generation configuration; dashboard; or
control plane.

## Proposal

### One retained companion domain

HAC-managed retained configuration gains one optional domain separate from the
existing `RetainedLocalConfiguration` textual/local semantics. It contains
exactly this already accepted composition fact:

```text
runtime: stable-diffusion-cpp
base URL: explicit loopback HTTP origin/base URL
execution ownership: exactly image-generation
```

Its fixed runtime identity is deliberate. The fact is not a provider choice,
generic binding record, discovery result, health claim, or model identity. Its
presence means exact local execution ownership of `image-generation`; HAC
must not infer other capabilities from adapter observation, runtime health,
endpoint behavior, or model contents.

The URL follows RFC-0126's existing stable-diffusion.cpp/local HTTP boundary:
explicit absolute loopback `http` origin/base URL with valid port, no path,
query, fragment, user information, credentials, TLS, LAN/Internet authority,
or discovery. This RFC creates no second URL semantic.

### Separate command and ownership

The facade gains:

```text
hac config image-generation --base-url http://127.0.0.1:<PORT>
hac config image-generation --reset
```

The equivalent long facade has the same meaning. Configure replaces exactly the
companion domain; reset clears exactly it. There is no generic `--runtime` or
provider selector: this first companion is explicitly the accepted
`stable-diffusion-cpp` composition.

Its mutation preserves retained textual local configuration, execution limit,
remote nodes, external-information plugin, Chat fallback, and every other
retained domain. Conversely, `hac config local` and its reset retain their
current complete textual/local meaning and preserve the companion. `hac config
reset` remains whole-retained-state reset and clears the companion with every
other retained fact.

```text
config local
    -> existing textual/local domain

config image-generation
    -> Image Generation companion domain

config node
    -> remote topology

config reset
    -> everything
```

The implementation may extend the existing private retained representation.
The operator contract is configure through `hac config`, inspect through
`hac config show`, and consume on a later ordinary startup—not editing a
file manually.

### Ordinary composition

When no explicit `--runtime-config PATH` is selected, ordinary composition is:

```text
existing effective textual local composition
    +
optional retained Image Generation companion
```

The textual side remains exactly as accepted: a retained textual baseline when
configured, zero-argument compatible textual default when absent, explicitly
supplied textual CLI overrides, and runtime-domain replacement when textual
runtime is explicitly switched. Textual flags neither target nor mutate the
companion, and this RFC adds no Image Generation override flags.

For example:

```text
retained textual = Ollama model A
retained image = stable-diffusion-cpp at loopback URL

hac local
  -> Ollama model A + Image Generation

hac local --ollama-model model-B
  -> temporary Ollama model B + same companion

hac local --runtime llama-server ...required textual facts...
  -> temporary llama-server composition + same companion
```

The retained HAC execution limit remains process-level HAC execution policy,
not runtime composition or binding capacity. This RFC does not change it.

### Runtime-config remains complete

`--runtime-config PATH` remains a complete, self-contained alternative. It
bypasses both the retained/default textual composition and this retained Image
Generation companion:

```text
ordinary path
  = retained/default/CLI textual domain
    + optional retained Image Generation companion

explicit runtime-config path
  = runtime-config alone
```

There is no merge of an explicit textual file with retained Image Generation,
or retained textual composition with an explicit Image Generation binding. A
selected file that needs both must contain both. This preserves RFC-0074,
RFC-0094, RFC-0110, and RFC-0126's simple source boundary.

### Execution ownership and static-cluster boundary

This RFC does not add textual execution capabilities to retained configuration:

```text
retained local_capabilities
    -> RFC-0059 caller-local static routing permission

retained Image Generation companion
    -> exact local execution ownership: image-generation
```

The historical singular textual runtime remains governed by its existing
semantics; it is not retroactively an explicit textual binding. This distinction
is why general retained bindings are not proposed.

RFC-0059 does not gain `image-generation`. A static-cluster process may
therefore physically contain this local Image Generation composition while
caller-local static permission keeps it ineligible:

```text
physical Image Generation adapter exists
  + caller-local static permission excludes image-generation
  -> no caller-local Image Generation candidate
```

No remote Image Generation, static remote declaration, receiver route, or
transport behavior changes. Under ordinary `hac local`, the companion
constructs the accepted binding so RFC-0127's existing
`/v1/image-generation` and `hac image-generation` path can use it without
new request or result semantics.

### Inspection and browser boundaries

`hac config show` gains retained-fact inspection equivalent to:

```text
Image Generation:
  runtime: stable-diffusion-cpp
  base URL: http://127.0.0.1:<PORT>
```

or `Image Generation: not configured`. It reports retained facts only: it
does not contact `sd-server`, test health, inspect models, discover
capabilities, or infer availability. Exact whitespace and private storage names
are not frozen.

RFC-0112's browser facade keeps only its accepted retained-local authority.
This RFC adds no Image Generation browser form, binding editor, or dashboard.
Existing browser or CLI mutation of the textual local domain must preserve the
companion, and companion mutation must preserve the textual domain. RFC-0112's
fail-closed rule for unrepresented future retained facts remains authoritative.

### Lifecycle, security, and engine independence

The endpoint is explicit operator configuration, not observed truth. RFC-0121
remains authoritative: the operator manages `sd-server` lifecycle and
model/model-file/backend/device ownership. HAC gains no executable/model path,
startup command, service manager, autostart, supervision, installation, or
download authority.

The companion preserves local-only retained facts, loopback-only authority, no
credentials, no ambient proxy inheritance, no remote synchronization, no
prompt/image retention, and no filesystem output authority. Engine independence
is preserved because cluster-facing request/routing semantics remain
capability-centered; this RFC retains one closed concrete adapter composition
behind that boundary. An alternate Image Generation engine requires a later RFC.

## Compatibility and migration

Existing retained configuration remains valid: semantically, it is existing
state with the Image Generation companion absent. No migration is required.

Existing `hac config local`, textual runtime CLI overrides, `hac config
node`, `hac config external-information`, `hac config chat`, `hac config
reset`, and explicit runtime-config documents remain valid. No old runtime
configuration becomes generic bindings, and `local_capabilities` remains
neither Image Generation ownership nor execution ownership.

## Rationale

One separate companion is smaller than retaining RFC-0110's general binding
collection. The demonstrated operator problem is one ordinary textual
composition plus one accepted Image Generation composition. It does not justify
persistent textual execution ownership, ambiguity for textual CLI overrides, or
generic binding CRUD.

Separating domains preserves RFC-0094 complete-domain semantics: `config
local` does not acquire image-only patch behavior, and Image Generation
configuration does not require textual repetition. Keeping runtime-config
complete avoids a precedence ladder and retains an explicit source of truth for
multi-binding invocations.

## Alternatives considered

### General retained capability bindings

Rejected for now. They require new persistent textual execution-capability
ownership and ambiguous targeting for existing textual CLI overrides when
multiple textual bindings exist. They solve more architecture than the current
problem needs. A second specialized capability with equivalent concrete
retention needs could justify reconsideration; that evidence does not exist.

### Put Image Generation in `hac config local`

Rejected. It would either force textual repetition for Image-only mutation or
introduce patch semantics to an established complete-domain command.

### Keep runtime-config only

Rejected as the sole daily-driver path. It remains valid and self-contained,
but cannot express configure-once ordinary Image Generation without repeatedly
selecting a file.

### New user-managed retained file

Rejected. RFC-0094 already owns HAC-managed retention; another file would add a
source, selection, and manual-schema problem without need.

## Trade-offs and consequences

The proposal adds one retained domain and one narrow runtime-specific command,
not a symmetric generic model. A future alternate engine or broader retained
composition requires another RFC. That constraint is acceptable because it
solves the current workflow without pretending that generic retained bindings
or textual execution ownership have been decided.

## Implementation proof expectations

Later implementation must prove that:

1. existing retained configurations load with Image Generation absent;
2. configuring or resetting the companion preserves all other retained domains;
3. `config local` mutation/reset preserves the companion, while whole
   `config reset` clears it;
4. `config show` reports retained Image Generation facts without network or
   runtime observation;
5. ordinary `hac local` composes existing effective textual runtime plus the
   companion;
6. textual runtime/model/temperature overrides, including explicit runtime
   replacement, leave the companion active;
7. explicit `--runtime-config` bypasses both retained execution-composition
   domains and never merges with the companion;
8. the companion constructs exactly the accepted stable-diffusion.cpp adapter
   and owns only `image-generation`;
9. invalid/non-loopback base URLs fail locally;
10. static-cluster composition does not expand RFC-0059 Image Generation
    permission, and no remote/receiver Image Generation appears;
11. browser mutation cannot silently delete or mutate the companion; and
12. no status, health, lifecycle, generation-control, model, or observation
    authority, dependency, or lockfile change is introduced.

## Open questions

None within this proposed bounded contract. A second Image Generation runtime,
broader browser authority, static caller-local Image Generation permission, or
general retained bindings requires a separate architectural decision.

## Decision

Pending.
