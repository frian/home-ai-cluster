# RFC-0044: Explicit Static-Cluster Status Composition

Status: Accepted

Date: 2026-07-18

Author: frian

## Summary

Home AI Cluster should allow the existing explicit static-cluster status command
to inspect one explicitly selected supported local runtime composition.

The command should accept the same closed local runtime choice already accepted
for ordinary local and static-cluster startup:

```text
ollama | llama-server
```

When no runtime option is supplied, status inspection should remain Ollama-backed.
The command should construct one existing concrete `LocalAppComposition`, then pass
that composition's `node_registry` and `adapter_registry` to the unchanged static
cluster status collector.

Remote status observation should remain unchanged. Static declarations should
remain topology-only. Runtime identity, adapter identity, model identifiers, and
runtime URLs should not enter normalized status.

## Problem

RFC-0041 added one explicit read-only status command for an already declared
static cluster:

```text
home-ai-cluster-status --declaration <path>
```

That command validates the declaration, constructs the historical ordinary local
node and adapter registries, observes the local adapter, then observes each remote
application sequentially in declaration order.

Phase 14 changed ordinary static-cluster startup. The command
`home-ai-cluster-static-cluster` can now construct exactly one explicit local
runtime composition backed by Ollama or llama-server, while preserving Ollama as
the default.

The status command still constructs only the historical implicit Ollama
composition. An operator can therefore start an ordinary static cluster with an
explicit llama-server local composition and then run status against the same
declaration while unintentionally observing Ollama locally.

The declaration is not the missing source of information. Runtime composition is
an explicit process-local operator concern and must remain outside static topology.
The unresolved decision is whether status may receive the same explicit local
composition input as ordinary startup while preserving the accepted normalized
status contract.

## Goals

This RFC establishes that:

- `home-ai-cluster-status` may inspect one explicitly selected supported local
  runtime composition;
- the supported local runtime set remains exactly `ollama` and `llama-server`;
- no-option status remains Ollama-backed and compatible;
- the existing concrete argument, validation, and composition-construction seam
  is reused;
- declaration validation completes before local composition construction and any
  live observation;
- local composition construction completes before the status HTTP client is
  created and before any remote observation;
- local status observes the registries belonging to the selected composition;
- remote status continues through the existing normalized Home AI Cluster status
  endpoint;
- static declarations remain topology-only;
- normalized status output remains engine-independent;
- no routing, fallback, lifecycle, discovery, or monitoring behavior changes; and
- focused compatibility tests and one privacy-safe real proof are required.

## Non-goals

This RFC does not add:

- runtime, adapter, model, URL, or node fields to static declarations;
- runtime, adapter, model, or URL fields to normalized status output;
- runtime-aware remote status responses;
- request-level runtime selection;
- engine-aware routing, fallback, ordering, or scheduling;
- more than one local adapter in one status invocation;
- automatic runtime selection or discovery;
- model discovery or inventory;
- local or remote runtime lifecycle management;
- runtime installation, model downloading, start, stop, restart, supervision, or
  repair;
- background polling, monitoring, persistence, history, alerts, or notifications;
- a new status command;
- a generic runtime factory, plugin system, provider registry, dependency-injection
  container, or configuration framework;
- retained runtime configuration or environment-variable configuration;
- changes to the remote status protocol, timeout semantics, status vocabulary,
  node ordering, or exit behavior;
- changes to routing, request execution, fallback, request history, or the
  OpenAI-compatible endpoint;
- a database, dashboard, Docker, Kubernetes, or distributed configuration.

## Decision

### Extend the existing status command

The existing command remains:

```text
home-ai-cluster-status
```

It continues to require one explicit static declaration:

```sh
uv run home-ai-cluster-status \
  --declaration <DECLARATION_PATH>
```

It additionally accepts the same local runtime arguments already used by ordinary
local and static-cluster startup:

```text
--runtime ollama | llama-server
--llama-server-base-url <LOOPBACK_HTTP_URL>
--llama-server-model <MODEL_IDENTIFIER>
```

The intended explicit llama-server form is:

```sh
uv run home-ai-cluster-status \
  --declaration <DECLARATION_PATH> \
  --runtime llama-server \
  --llama-server-base-url http://127.0.0.1:<PORT> \
  --llama-server-model <MODEL_IDENTIFIER>
```

No second status command is added.

### Preserve default compatibility

When no local runtime option is supplied, status preserves its current behavior:

- declaration remains required;
- the local node ID remains `local`;
- the local composition remains the ordinary default Ollama composition;
- declared remotes remain observed sequentially in declaration order;
- the current timeout and remote status transport remain unchanged;
- normalized output and exit behavior remain unchanged.

Explicit `--runtime ollama` constructs the same ordinary Ollama composition as the
no-option path. This RFC does not add Ollama URL or model overrides.

### Explicit llama-server status composition

Selecting `llama-server` requires:

- one absolute loopback `http` base URL; and
- one non-empty model identifier.

The status command constructs the existing ordinary llama-server local composition:

- local node ID `local`;
- capability `chat`;
- one `LlamaServerAdapter`;
- one matching `NodeRegistry`; and
- one matching `AdapterRegistry`.

The model identifier and runtime URL are used only to construct the local adapter
whose health is observed. They must not appear in normalized status, declaration
projection, remote protocol, safe errors, retained proof, or ordinary logs.

### Reuse one concrete composition boundary

The implementation reuses the existing narrow helpers that own:

- the closed runtime choices;
- runtime-specific CLI arguments;
- syntax-level argument types;
- conditional runtime validation;
- Ollama composition construction; and
- llama-server composition construction.

The command constructs exactly one `LocalAppComposition`. It then passes that
composition's `node_registry` and `adapter_registry` to the existing
`collect_static_cluster_status(...)` call.

The status collector, its signature, normalized models, remote transport, and
observation semantics do not change.

This reuse remains concrete. Two supported runtimes do not justify dynamic loading,
generic factories, plugin registration, or a dependency-injection container.

### Validation, construction, and observation order

Argument parsing may perform syntax-level validation through existing `argparse`
choices and argument types. In particular, an unsupported runtime choice or a
syntactically invalid loopback URL may fail during parsing.

After successful parsing, the required operation order is:

1. load and fully validate the explicitly selected static declaration;
2. apply conditional local runtime validation;
3. construct exactly one `LocalAppComposition`;
4. construct the declared remote registry;
5. create one status HTTP client;
6. call the existing collector with the composition's two registries;
7. observe the selected local composition;
8. observe declared remotes sequentially in declaration order;
9. emit one normalized result and exit.

Conditional runtime validation includes the cross-argument rules that:

- llama-server-specific values are rejected with Ollama;
- llama-server requires both its loopback URL and model identifier; and
- required values must be non-empty.

An invalid declaration must prevent conditional runtime validation from causing
composition construction and must prevent every live observation.

Invalid runtime values must prevent composition construction, HTTP client creation,
and every local or remote observation.

Composition construction performs no health probe, runtime discovery, model
inventory, generation request, or remote request. Live local health observation
continues to belong to the existing status collector.

### Preserve normalized status semantics

The existing local status shape remains:

```json
{
  "node_id": "local",
  "application_status": "local",
  "runtime_status": "available"
}
```

The accepted local runtime statuses remain:

- `available`;
- `unavailable`;
- `observation-failed`.

The selected runtime does not become a status dimension. The result does not
contain runtime name, adapter name, model identifier, runtime URL, executable name,
or runtime-specific reason text.

Remote observations continue to use the existing application and runtime status
vocabularies and the existing internal Home AI Cluster status protocol. Remote
applications do not need to know which local runtime the calling status command
selected.

### Keep declarations topology-only

Static declarations continue to contain only accepted remote topology facts. They
do not gain local runtime, adapter, model, URL, credential, or lifecycle fields.

The declaration selects which remote applications are observed. CLI composition
arguments select which local adapter is observed. These remain independent input
domains with no merge or precedence system.

### Preserve status boundaries

This RFC changes only local status composition selection. It does not change:

- declaration parsing or schema;
- remote node order;
- sequential remote observation;
- per-remote timeout behavior;
- the internal remote status endpoint;
- application-status or runtime-status categories;
- cluster-owned node attribution;
- result ordering;
- command exit semantics;
- routing or request candidate eligibility;
- fallback behavior;
- application or runtime lifecycle ownership.

Status remains one explicit finite read-only observation. It does not become a
monitoring service or a readiness policy.

## Rationale

The operator asymmetry is real and narrow. Ordinary static-cluster startup can
select llama-server locally, while status can still observe only Ollama locally.
This can produce a truthful observation of the wrong local composition.

The project already owns the exact concrete seam needed to fix the asymmetry.
Reusing it is simpler and safer than creating status-specific runtime parsing or
construction.

Keeping composition in explicit CLI input preserves topology-only declarations and
avoids precedence rules, retained machine-specific configuration, or hidden
environment behavior.

Keeping runtime identity out of status preserves the engine-independent operator
contract. Status answers whether the selected local composition is available, not
which engine brand implements it.

The proposal supports local-first operation, privacy-first runtime ownership,
engine-independent status contracts, capability-centered cluster concepts, boring
explicit operator choices, architecture before implementation, and small
reviewable changes.

## Alternatives considered

### Keep status fixed to Ollama

Rejected. This leaves status unable to inspect the local composition used by an
explicit llama-server static cluster.

### Infer local composition from the declaration

Rejected. Static declarations intentionally describe remote topology only. Adding
local runtime fields would mix process composition with retained topology and
create migration and precedence rules.

### Ask the running static-cluster process for its complete local status

Deferred and rejected for this increment. That would require a process-target
selection contract, local application address input, and a decision about whether
status observes a constructed composition or another running process.

### Expose runtime identity in status

Rejected. Runtime and model identity remain adapter-construction details and do not
improve the normalized cluster-facing status contract.

### Add a second llama-server status command

Rejected. It would duplicate declaration validation, remote observation, output,
timeout, error, and lifecycle behavior.

### Add a generic status composition factory or plugin system

Rejected. The existing closed pair of concrete compositions is sufficient and
already shared by ordinary startup commands.

### Use environment variables

Rejected. Hidden runtime inputs would make the observed local composition harder
to inspect and would introduce a precedence system absent from current accepted
runtime composition.

### Probe runtime health during composition construction

Rejected. Construction and observation are separate responsibilities. Probing
before the status collector would duplicate observations and blur validation with
live status.

## Trade-offs

The status command gains a small argument and validation surface.

An operator must supply the same llama-server URL and model identifier used by the
corresponding ordinary process. Phase 15 does not introduce process introspection
or retained configuration to recover those values automatically.

CLI values can appear in shell history or process inspection. Credentials are not
supported. The accepted llama-server values remain a loopback URL and a model
identifier.

The command constructs an adapter only to perform one finite health observation.
That is acceptable because it matches the existing direct local status model and
requires no runtime lifecycle ownership.

The status result deliberately omits runtime identity. Operators must know which
explicit CLI composition they selected. This preserves a smaller stable contract
at the cost of not echoing operator input.

## Compatibility

The existing command remains valid and Ollama-backed:

```sh
uv run home-ai-cluster-status \
  --declaration <DECLARATION_PATH>
```

Explicit Ollama status is equivalent:

```sh
uv run home-ai-cluster-status \
  --declaration <DECLARATION_PATH> \
  --runtime ollama
```

No declaration migration, status-schema change, remote endpoint update, routing
change, or lifecycle change is required.

## Privacy and trust boundary

Home AI Cluster must not expose or retain through this feature:

- llama-server base URLs;
- model identifiers;
- adapter or runtime names in normalized status;
- raw adapter, HTTP, or transport errors;
- declaration contents or private addresses;
- filesystem paths;
- prompts or generated responses;
- credentials, authorization values, usernames, passwords, or secrets.

The selected runtime URL remains loopback-only. Runtime and model lifecycle remain
operator-owned. Status does not start, stop, restart, supervise, repair, or
download anything.

A retained proof should use placeholders for operator-specific values and should
record only normalized observations and the fact that the explicit composition
was selected.

## Impact

Implementation may affect:

- `src/home_ai_cluster/status_command.py`;
- focused status command and local composition tests;
- ordinary operator documentation;
- one retained privacy-safe Phase 15 proof; and
- Phase 15 closeout documentation.

It should not require changes to:

- status models;
- the status collector;
- the internal remote status endpoint;
- static declaration models or parsing;
- routing or fallback;
- runtime adapter protocols;
- request or result models;
- remote transport;
- request history; or
- the OpenAI-compatible endpoint.

## Implementation sequence

Implementation should proceed through small dedicated pull requests:

1. in one coherent implementation PR, extend the status command parser, perform
   conditional runtime validation, construct the selected `LocalAppComposition`,
   and pass its registries to the unchanged collector;
2. in that PR or one immediately following test-only PR, add focused compatibility,
   conditional validation, selected-composition, and no-observation-before-validation
   tests;
3. retain one privacy-safe real operator proof for explicit llama-server status;
4. update ordinary operator documentation; and
5. close Phase 15.

No merged intermediate state may accept explicit runtime arguments while still
observing the historical implicit Ollama composition.

Agents may implement the accepted decision. They must not broaden runtime choices,
status fields, declaration schema, observation protocol, routing, or lifecycle
ownership.

## Proof obligations

Phase 15 is not complete until evidence demonstrates:

1. the previous no-runtime-option command remains Ollama-backed;
2. explicit `--runtime ollama` produces the same local status composition;
3. explicit llama-server status constructs and observes the ordinary llama-server
   composition;
4. syntax-level argument rejection remains compact and performs no observation;
5. declaration validation completes before conditional runtime validation causes
   composition construction and before every observation;
6. invalid conditional runtime combinations prevent composition construction,
   HTTP client creation, and every local or remote observation;
7. local composition construction performs no live probe;
8. the command passes the selected composition's two registries to the unchanged
   status collector;
9. declared remotes remain observed sequentially in declaration order;
10. normalized local and remote status output remains unchanged;
11. no runtime, adapter, model, or URL field appears in normalized output;
12. runtime-specific values remain absent from declarations and remote protocol;
13. normalized unavailable and observation-failed outcomes retain existing exit
    semantics;
14. no routing, fallback, lifecycle, monitoring, persistence, discovery, generic
    factory, plugin, database, container, or dashboard behavior is introduced;
15. ordinary automated tests require no live runtime; and
16. one explicit live llama-server status proof retains no private address,
    hostname, username, path, credential, token, raw log, or unnecessary model
    output.

## Open questions

Only implementation-level naming and test decomposition remain open.

The architectural decision is deliberately closed: one existing status command,
one explicitly selected concrete local composition, Ollama by default, explicit
registry injection into the unchanged collector, and no runtime identity in
normalized status.
