# RFC-0039: Repeatable static cluster declaration

Status: Draft

Date: 2026-07-16

Author: frian

## Summary

Home AI Cluster should allow the ordinary static multi-node process accepted by
RFC-0038 to load its two retained remote declaration values from one explicitly
named local TOML file.

The operator should select that file through one new CLI argument:

```text
home-ai-cluster-static-cluster --declaration <path>
```

The first declaration should contain exactly:

```toml
remote_node_id = "remote-node"
remote_base_url = "http://192.0.2.10:8000"
```

The file should describe only the already-accepted local-plus-one-remote topology.
It should not become a generic configuration file.

Existing RFC-0038 startup through `--remote-node-id` and `--remote-base-url`
should remain supported as an independent invocation mode. Declaration-file and
inline topology arguments must not be combined in one invocation.

The file must be selected explicitly. Home AI Cluster should not search for it,
automatically discover it, watch it, reload it, or contact the remote endpoint
while loading it.

## Problem

RFC-0038 made one local-plus-one-remote topology an ordinary supported mode.
That mode is explicit, static, local-first, and operator-owned.

Repeated operation still requires the operator to reconstruct the same command:

```text
home-ai-cluster-static-cluster \
  --remote-node-id <remote-node-id> \
  --remote-base-url <remote-base-url>
```

This is sufficient for proof and occasional use, but unnecessarily fragile for
repeated operation:

- the same values must be retyped or recovered;
- shell history may retain a private LAN endpoint;
- wrappers and aliases move the declaration outside the project contract;
- long commands make operator review and correction harder.

The project now needs one narrow retained declaration without introducing
automatic discovery, a configuration subsystem, or broader topology authority.

## Goals

This RFC should:

- make the accepted static multi-node topology repeatable;
- retain only the two remote facts already accepted by RFC-0038;
- keep file selection explicit at process startup;
- preserve the existing command name and ordinary process behavior;
- preserve local-only operation as the shortest default path;
- preserve RFC-0038 routing, adapter, fallback, lifecycle, and privacy boundaries;
- perform parsing and structural validation before the application binds;
- avoid network observation while loading the declaration;
- avoid new runtime dependencies;
- keep the declaration understandable without repository knowledge.

## Non-goals

This RFC does not add or define:

- automatic file discovery;
- a default configuration path;
- a home-directory, system-wide, or repository search path;
- arbitrary node lists;
- more than one remote node;
- local-node customization;
- capability configuration;
- adapter configuration;
- model configuration;
- routing-policy configuration;
- priorities, weights, load balancing, or scheduling;
- dynamic registration or membership;
- automatic node or model discovery;
- process supervision or remote process control;
- automatic runtime startup, shutdown, repair, or retries;
- live reload or file watching;
- environment-variable substitution inside the file;
- includes, inheritance, profiles, or overlays;
- schema migration machinery;
- a distributed configuration service;
- a database;
- credentials, tokens, or authorization values;
- internet-facing operation;
- a dashboard or web UI;
- Docker or Kubernetes;
- a generic configuration framework for future features.

## Proposal

### Explicit declaration path

Add one optional argument to the existing ordinary command:

```text
home-ai-cluster-static-cluster --declaration <path>
```

The path must be supplied explicitly by the operator.

Home AI Cluster must not:

- infer a declaration path from the working directory;
- search parent directories;
- search the repository;
- search the user home directory;
- search system configuration directories;
- load a declaration merely because a conventionally named file exists.

This keeps topology selection visible in the process invocation.

### Declaration format

The first declaration format should be TOML.

The complete accepted shape should be:

```toml
remote_node_id = "remote-node"
remote_base_url = "http://192.0.2.10:8000"
```

Exactly two top-level keys are allowed:

- `remote_node_id`;
- `remote_base_url`.

Both values must be strings.

Unknown keys must fail validation before startup. Nested tables, arrays, and
additional sections are not part of this RFC.

The first format should not include a schema-version field. There is only one
small accepted shape, and no migration problem currently exists. A later RFC may
add explicit versioning if an incompatible second shape is actually proposed.

### Why TOML

TOML is preferred because:

- it is readable as a small operator-owned declaration;
- the two accepted values map directly to two explicit keys;
- Python 3.13 provides `tomllib` in the standard library;
- no new runtime dependency is required;
- no custom parser is required;
- it avoids turning shell syntax into project configuration semantics.

This RFC does not establish TOML as a project-wide configuration standard. It is
only the accepted serialization for this one narrow declaration.

### Invocation modes

The ordinary static multi-node command should support exactly two independent
multi-node invocation modes.

#### Existing inline mode

```text
home-ai-cluster-static-cluster \
  --remote-node-id <remote-node-id> \
  --remote-base-url <remote-base-url>
```

This RFC does not deprecate or change that contract.

#### Declaration mode

```text
home-ai-cluster-static-cluster --declaration <path>
```

The declaration supplies both accepted remote values.

### No precedence system

Declaration mode and inline mode must not be combined.

An invocation that supplies `--declaration` together with either
`--remote-node-id` or `--remote-base-url` must fail before startup with a compact
operator-facing error and non-zero exit status.

This deliberately avoids override and merge rules.

The command should therefore accept one complete source of topology facts, never
multiple competing sources.

### Local-only operation

Ordinary local-only startup remains unchanged and default.

The local application must not automatically load a declaration. A declaration
must affect only an explicit `home-ai-cluster-static-cluster --declaration ...`
invocation.

### Static validation

Declaration loading should perform local parsing and structural validation before
the application binds its endpoint.

At minimum, startup must fail when:

- the supplied path does not exist;
- the path cannot be read;
- the content is not valid TOML;
- the top-level value is not the accepted mapping shape;
- either required key is missing;
- either value is not a string;
- an unknown key is present;
- `remote_node_id` is empty;
- `remote_node_id` conflicts with the existing local node ID;
- `remote_base_url` fails the same accepted URL validation as RFC-0038;
- declaration mode and inline mode are combined.

After parsing, the resulting two values must enter the same construction and
validation path used by the accepted inline RFC-0038 mode.

Loading and validating the declaration must not:

- contact the remote endpoint;
- perform DNS resolution for observation purposes;
- test LAN reachability;
- inspect the remote application, runtime, or model;
- run health polling;
- mutate the file;
- repair any value.

The accepted RFC-0036 preflight meaning remains unchanged.

### Failure and privacy behavior

Operator-facing failures should identify the failed category and, when useful,
the explicitly supplied declaration path.

Failures and logs must not expose the retained `remote_base_url` value.

The declaration content must not be copied into:

- normalized public errors;
- request history;
- routing explanations;
- proof records;
- ordinary logs.

The remote node ID may continue to appear where cluster-owned node attribution is
already accepted.

### Retention boundary

The declaration is operator-owned local state.

It is not intended to be committed with real private values. Repository examples,
if later added, must use documentation-only addresses and placeholder node IDs.

The declaration must not contain:

- credentials;
- tokens;
- authorization headers;
- usernames or passwords;
- private keys;
- arbitrary environment values.

Home AI Cluster should read the file at startup, validate it, construct the
existing process-local declarations, and not write back to it.

No file permission enforcement is introduced. Documentation may recommend normal
operator-only permissions when appropriate, but permission policy remains owned
by the operating system and operator.

### Lifecycle and reload boundary

The declaration is read once during process startup.

Changes to the file after startup must have no effect on the running process.
Applying a changed declaration requires an explicit process restart by the
operator.

Home AI Cluster must not watch, reload, rewrite, lock, or synchronize the file.

### Compatibility

This RFC preserves:

- the existing `home-ai-cluster-static-cluster` command name;
- existing RFC-0038 inline arguments;
- ordinary local-only startup;
- the historical proof command as a separate proof-only mode;
- the accepted one-local-plus-one-remote topology;
- local-first routing and narrow fallback;
- cluster-owned attribution;
- operator-owned runtime and remote application lifecycle;
- loopback-only calling endpoint defaults.

Nothing is deprecated by this RFC.

## Rationale

An explicitly named local TOML file solves the actual Phase 9 problem: repeated
command reconstruction.

It does so without granting Home AI Cluster new authority:

- the operator still selects the topology explicitly;
- the topology remains static and process-local;
- the retained facts are unchanged from RFC-0038;
- no source precedence exists;
- no discovery occurs;
- no remote observation occurs during loading;
- no process or runtime lifecycle becomes cluster-owned.

Rejecting mixed declaration and inline arguments is intentionally less flexible
than an override system. That restriction makes the active topology easier to
inspect and explain.

The proposal remains "boring" by using a standard-library parser and one flat,
closed shape.

## Alternatives considered

### Continue CLI-only operation

Rejected for Phase 9.

CLI-only operation remains supported, but it does not solve repeated declaration
reconstruction and can retain private endpoint values in shell history.

### Environment variables

Rejected.

Environment variables would hide topology from the visible command, require a
new naming contract, and create implicit process-environment precedence. They
would also be less convenient to inspect as one complete declaration.

### Shell wrapper or alias

Rejected as the project contract.

Operators may still use wrappers, but shell-specific wrappers move validation and
portability outside Home AI Cluster. They do not provide one engine-independent,
repository-defined declaration boundary.

### JSON

Rejected.

JSON would work technically, but it is less comfortable for a small hand-edited
operator declaration and does not improve validation or dependency behavior.

### YAML

Rejected.

YAML would require another dependency or a custom parsing choice and introduces a
broader, more complex syntax than this two-field declaration needs.

### Automatic file discovery

Rejected.

Automatic discovery would require path conventions, search order, working-directory
semantics, and hidden activation rules. Explicit selection is clearer and safer.

### CLI values override declaration values

Rejected.

Overrides would introduce a precedence system and make the effective declaration
depend on merging two sources. The first increment needs no such flexibility.

### Declaration values override CLI values

Rejected for the same reason.

The command should use one complete source, not merge competing sources.

### Replace inline CLI mode

Rejected.

The accepted RFC-0038 contract remains useful for proofs, temporary operation,
and compatibility. Phase 9 adds a repeatable path; it does not require migration.

### Add schema versioning now

Rejected.

There is no second schema and no migration requirement. Versioning would add a
future-facing field without solving a present problem.

### Support arbitrary remote-node lists

Rejected.

That would reopen topology, ordering, identity, routing, and validation decisions
that Phase 9 explicitly preserves.

## Trade-offs

This proposal makes repeated operation easier and safer to inspect.

It introduces:

- one new CLI argument;
- one small TOML parser boundary using the Python standard library;
- one closed two-key declaration shape;
- one additional startup failure surface.

It deliberately makes ad hoc overrides harder. Operators must edit the file or
use the existing inline mode rather than combine sources.

The declaration contains a private LAN endpoint on disk. This is an explicit
trade-off: persistence is the feature needed for repeatability. The risk is kept
narrow by prohibiting credentials, avoiding repository commitment of real values,
redacting the endpoint from project-owned outputs, and leaving file ownership to
the operator.

## Impact

If accepted, implementation should affect only the ordinary static cluster
startup boundary and its tests.

Expected follow-up work includes:

- parse one explicitly selected TOML file with `tomllib`;
- validate the closed two-key shape;
- route parsed values through existing RFC-0038 construction;
- reject mixed invocation sources;
- add focused CLI and privacy-boundary tests;
- update the canonical operator workflow;
- add a placeholder-only example only if it materially improves operation;
- record the resulting Phase 9 current state and proof.

The RFC does not require changes to request or response schemas, routing policy,
adapter contracts, runtime ownership, or distributed protocols.

## Open questions

- Should implementation expose declaration parsing as a small pure function for
  focused tests, or keep it inside the command module?
- Should documentation recommend a conventional filename while still requiring
  an explicit path?
- Is a repository placeholder example useful enough to justify maintaining it,
  or is an inline documentation example sufficient?

These are implementation and documentation questions. They do not change the
architectural decision proposed here.

## Decision

Pending.
