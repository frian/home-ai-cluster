# RFC-0075: Retire Historical Proof Launchers

Status: Draft

Date: 2026-08-17

Author: frian

## Summary

Home AI Cluster should retire exactly these four installed historical proof
launchers:

```text
home-ai-cluster-static-proof
home-ai-cluster-automatic-proof
home-ai-cluster-fallback-proof
home-ai-cluster-phase-12-heterogeneous-receiver
```

After acceptance and implementation, the four names would no longer be
installed console scripts. There would be no redirect, alias, compatibility
shim, warning wrapper, replacement launcher, migration machinery, or generic
deprecation framework. Invoking one of these names from an updated installation
would simply no longer resolve as a Home AI Cluster installed command.

This is a narrow compatibility-retirement decision. It does not change the
ordinary architecture, routing, fallback, runtimes, topology, endpoints,
capabilities, privacy boundaries, or the retained historical record. The
ordinary supported surfaces already exercise the current architecture; the old
proof records remain evidence of the exact historical procedures.

## Problem

The four launchers were deliberately introduced as small, explicit proof-only
processes:

- RFC-0022 introduced `home-ai-cluster-static-proof` for the founding static
  two-machine proof and its fixed `declared-remote-only` selection;
- RFC-0026 introduced `home-ai-cluster-automatic-proof` for automatic routing
  where the declared remote was the sole selectable `chat` candidate;
- RFC-0028 introduced `home-ai-cluster-fallback-proof` for one narrow local
  pre-execution failure followed by one declared-remote fallback; and
- Phase 12 introduced `home-ai-cluster-phase-12-heterogeneous-receiver` as a
  proof-scoped llama-server receiver.

These were appropriate bridges from accepted architecture to real-machine
evidence. They are now retained installed compatibility surfaces even though
ordinary operation no longer imports or requires their launcher modules.

The merged
`docs/retained-proof-scaffolding-investigation.md` found that ordinary static
multi-node operation, ordinary local runtime composition, ordinary
capability-centered remote selection, and ordinary bounded fallback now have
implementation and retained real-machine evidence. It also found that several
proof-specific aliases and route/app-state seams remain primarily to keep the
old proof launchers executable.

Keeping obsolete proof-only executables installed makes the distinction between
ordinary operation and historical architecture evidence less clear. It also
preserves compatibility code and tests that do not serve the ordinary operator
path. Doing nothing keeps exact historical commands directly runnable from a
current installation, but retains that cognitive and maintenance burden.

The project needs one explicit decision before changing those accepted command
surfaces. This RFC supplies that decision without pretending that ordinary
operation reproduced every historical proof topology byte-for-byte.

## Goals

This RFC proposes to:

- retire exactly the four named installed proof launchers;
- make the compatibility break explicit, narrow, and free of transitional
  command machinery;
- preserve the ordinary supported operator surfaces as the current way to
  exercise Home AI Cluster architecture;
- preserve historical RFCs, proof results, runbooks, and evidence as historical
  truth rather than rewriting them to use newer commands;
- authorize later deletion of implementation code only when a dependency review
  confirms that it is exclusively required by the retired launchers;
- preserve shared ordinary architecture and its tests; and
- use Git history plus retained documentation as the archive rather than adding
  a live legacy source package.

## Non-goals

This RFC does not retire, rename, move, deprecate, or add to `hac`:

```text
home-ai-cluster-explain-routing
home-ai-cluster-explain-request
home-ai-cluster-history
home-ai-cluster-clear-history
```

Those are accepted narrow diagnostic/history surfaces, not proof launchers.
Their exclusion from the current root command is an RFC-0050 scope decision,
not evidence that they are obsolete.

This RFC also does not:

- change the `hac` root command or its ordinary subcommand set;
- retire standalone aliases or standalone commands for ordinary operation;
- change OpenAI compatibility behavior or its separate proof-observation
  mechanisms;
- change any capability, request/result, routing, fallback, runtime, topology,
  protocol, endpoint, status, health, or preflight contract;
- add migration machinery, a general deprecation policy, or package-versioning
  policy;
- create a `legacy/`, `archive/`, `deprecated/`, or similar Python package or
  source tree;
- retire `src/home_ai_cluster/phase_5_runtime_adapter_proof.py` or its
  `python -m` proof procedure;
- introduce Docker, Kubernetes, a database, dashboard, discovery, scheduling,
  lifecycle management, or any new infrastructure.

The Phase 5 proof runner is deliberately outside this RFC. A later cleanup may
find it unused after the four launcher retirements, but that is a separate
disposition and compatibility question.

## Proposal

### Retired installed names

After acceptance and implementation, remove exactly these entries from the
installed project script surface:

```text
home-ai-cluster-static-proof
home-ai-cluster-automatic-proof
home-ai-cluster-fallback-proof
home-ai-cluster-phase-12-heterogeneous-receiver
```

The names cease to be Home AI Cluster installed console scripts. The project
does not provide a redirect, alias, compatibility shim, warning wrapper,
replacement launcher, deprecation period, or new migration command. An updated
installation simply does not resolve these names as Home AI Cluster commands.

This intentionally breaks compatibility for proof-only tooling. It does not
remove a current ordinary user capability.

### Ordinary supported surfaces

The following existing ordinary surfaces remain the supported ways to exercise
current architecture, as applicable:

- `hac local` for ordinary local runtime composition and receiver operation;
- `hac static-cluster` and ordinary static declarations for ordinary explicit
  static topology;
- ordinary capability routing and local-first routing;
- ordinary native `chat`, `summarize`, `classify`, and `code` requests;
- ordinary `status`, `health`, and `preflight` inspection.

These paths exercise the founding topology, capability eligibility, bounded
fallback, and heterogeneous receiver composition through ordinary contracts.
They are not asserted to reproduce every historical fixed proof topology,
selection mode, node identifier, or process argument byte-for-byte.

### Historical evidence and current-facing documentation

Historical RFCs, proof-result documents, proof records, and runbooks remain in
the repository. They continue to state the commands and procedures actually
used at the time. The old procedures must not be rewritten as though ordinary
commands were originally used.

Later implementation must update current-facing operator guidance so that it
does not present a retired launcher as a currently runnable supported command.
It may mark an old runbook or proof procedure historical/non-current and link
to the ordinary current workflow. It must preserve historical evidence rather
than deleting or rewriting it.

Git history plus retained RFCs and documentation is the archive. No parallel
legacy or archive Python implementation tree is introduced.

### Authorized implementation boundary

After acceptance, implementation may remove code and tests that a
dependency review confirms are exclusively required by the four retired
launchers. Likely candidates include:

- `src/home_ai_cluster/static_proof.py`;
- `src/home_ai_cluster/automatic_proof.py`;
- `src/home_ai_cluster/fallback_proof.py`;
- `src/home_ai_cluster/phase_12_heterogeneous_runtime_cluster_proof.py`;
- `src/home_ai_cluster/api/proof_orchestrator.py`;
- proof-only compatibility aliases such as `StaticRemoteProofWiring`,
  `StaticRemoteProofWiringError`, and `build_static_remote_proof_wiring`;
- proof-only app-state and routing branches such as
  `static_remote_proof_wiring`, `automatic_proof_orchestrator`, and
  `proof_receiving_app_wiring`; and
- tests that verify only a retired executable contract or removed proof-only
  compatibility seam.

These are candidates, not an approved deletion list. A proof-related name is
not sufficient evidence that code is disposable. Implementation must inspect
remaining imports, ordinary callers, public contracts, and test coverage before
each deletion.

### Architecture that remains

Implementation must preserve all ordinary/shared architecture, including:

- `StaticRemoteWiring` and `StaticRemoteCollectionWiring`;
- remote declarations and remote transport;
- candidate collection, capability eligibility, and selected-candidate
  execution;
- ordinary static fallback and ordinary local-first routing;
- local runtime composition and `LocalAppComposition`;
- internal receiver request handling;
- `/internal/cluster/request` and `/internal/cluster/status`;
- ordinary status, health, and preflight behavior;
- existing native capability request/result contracts; and
- current privacy boundaries.

Tests for these shared invariants must remain. If a shared invariant is
currently covered only by a proof-named test, later implementation must move or
replace that coverage with a proof-neutral test before deleting the proof-only
test.

### Relationship to earlier decisions

If accepted, RFC-0075 overrides only the continued-availability requirements
for the four named proof-only installed launchers.

RFC-0022, RFC-0026, RFC-0028, and RFC-0030 remain historical architectural
memory and evidence. Their broader decisions about static declaration,
capability routing, bounded fallback, and runtime-adapter boundaries remain in
force where later ordinary RFCs did not already refine them.

RFC-0050's general preservation of existing standalone commands no longer
applies to these four explicitly retired names. The Phase 13 closeout's
retention statement for the Phase 12 proof launcher is intentionally changed
by this later decision.

No earlier RFC is wholly superseded. This RFC changes only the later
compatibility disposition of the four named installed proof launchers.

## Rationale

The project prefers boring solutions first. The ordinary architecture that the
proof scaffolding was built to establish is now the supported operational
surface: explicit static declarations, local-first capability routing, bounded
fallback, ordinary local runtime composition, and current native requests and
inspection commands.

Leaving every historical proof process executable forever treats evidence
scaffolding as product operation. That obscures the ordinary path for operators
and leaves proof-only compatibility seams and tests in the active maintenance
surface. Removing the obsolete launchers makes the boundary clearer without
adding a new abstraction, lifecycle system, or migration framework.

The historical value is not the current executable name alone. It is the
accepted decision, retained runbook or proof result, and repository revision
that records exactly what was tested. Git history and retained documents
preserve that truth more faithfully than moving dead code into a permanently
importable archive package.

No user-facing capability is lost. The ordinary paths remain capability-
centered, local-first, privacy-first, and engine-independent. This proposal
does not alter what a cluster can do; it removes obsolete ways of launching
historical demonstrations.

## Alternatives considered

### Retain all four launchers indefinitely

This preserves direct execution of old proof procedures from current
installations. It also preserves the distinction problem and the proof-only
compatibility burden after ordinary implementation and evidence have replaced
their operational role. Not proposed.

### Redirect each old command to an ordinary command

Rejected. The ordinary paths are not always topology-identical to the proof
paths. A redirect would misrepresent historical semantics and create a durable
compatibility shim or warning contract for no ordinary capability gain.

### Keep wrappers that print a migration warning

Rejected. It creates a deprecation framework, preserves installed command
names, and asks the project to define warning and removal policy. The narrow
break is clearer: retired proof-only names no longer resolve.

### Move proof code into `legacy/` or `archive/`

Rejected. A live archive package adds packaging, import, test, and maintenance
surface without preserving more historical truth than Git history and retained
documentation. When confirmed dead, executable code should be deleted rather
than relocated.

### Add the proof launchers to `hac`

Rejected. RFC-0050 correctly excludes proof utilities from the ordinary root
surface. Promoting them now would make historical scaffolding look like current
operator behavior, which is the opposite of this proposal.

### Retire every proof-named module or command

Rejected. A proof word is not a dependency analysis. In particular, the Phase
5 `python -m` runner is not one of the four installed launchers, OpenAI
compatibility proof observation has a separate contract, and several
proof-named tests cover shared architecture.

## Trade-offs

After implementation, the exact historical proof commands will no longer be
directly runnable from a current installation. Reproducing an old proof exactly
may require checking out the relevant historical repository revision and
following its retained proof procedure.

This is an intentional compatibility break for proof-only tooling. Git history
and retained RFC/proof documentation become the preservation mechanism.
Ordinary replacement paths are not always topology-identical to the old proofs,
so they must not be represented as rewritten historical evidence.

The proposal reduces active command, compatibility, and test surface, but it
places responsibility on later implementation to preserve shared ordinary
coverage. The required dependency review is therefore a necessary constraint,
not optional cleanup work.

## Impact

### Operators

Ordinary operators retain the existing ordinary root and standalone surfaces.
An operator using one of the four historical proof names must use a retained
historical revision to reproduce that exact procedure, or use the current
ordinary workflow when the goal is to exercise current architecture.

### Implementation

Later implementation may change only the installed script table, proof-only
source and compatibility seams confirmed dead, focused proof-only tests, and
current-facing documentation needed to stop claiming retired commands are
runnable. It must not use this RFC to change ordinary behavior.

### Documentation and history

Historical records remain. Current guidance may add historical/non-current
labels and link to the ordinary workflow. No historical command invocation is
rewritten as a newer ordinary invocation.

### Compatibility

The four installed names cease to resolve. That is the sole intended command
compatibility break. No alias, redirect, warning, or version-policy mechanism
is created.

## Proof expectations for later implementation

Later implementation is complete only when deterministic evidence shows:

1. the four retired names are absent from installed project scripts;
2. `hac` help and its ordinary command set are unchanged;
3. accepted diagnostic/history standalone commands remain installed;
4. ordinary local operation remains unchanged;
5. ordinary static-cluster operation remains unchanged;
6. ordinary capability-centered remote selection remains unchanged;
7. ordinary fallback remains unchanged;
8. internal remote request and status receiver paths remain available;
9. shared routing, wiring, adapter, and receiver tests remain covered;
10. no legacy or archive code package is introduced;
11. historical proof/result documents remain retained; and
12. current-facing documentation no longer claims the four retired launchers
    are currently runnable.

No new physical two-machine proof is required solely to delete obsolete
launchers. The ordinary replacement architecture already has retained physical
evidence. Normal regression tests are sufficient unless implementation uncovers
a behavioral uncertainty.

## Open questions

- Should all four retired launchers be removed in one implementation change or
  in separately reviewed, dependency-justified increments after this RFC is
  accepted?
- Which current-facing historical static-proof references need an archival note
  versus a direct link to the ordinary workflow?

These do not reopen the proposed retired name set, the absence of transitional
launchers, the preservation of historical evidence, or the requirement to
preserve shared architecture.

## Decision

Pending.
