# Phase 4 Completion Assessment

Status: Assessment

Date: 2026-07-12

This document is descriptive. It assesses the current roadmap, accepted RFCs,
implementation, tests, and recorded proof results. It makes no architectural
decision and does not redefine Phase 4.

## Assessment question

Is Phase 4 complete according to the repository's current roadmap, accepted
RFCs, implementation, tests, and real proof results?

## Sources of truth

This assessment uses the Phase 4 goal and expected outcomes in
[ROADMAP.md](../ROADMAP.md), the Phase 3 closeout and Phase 4 entry boundary in
[RFC-0024](../RFC/RFC-0024-phase-3-closeout-and-phase-4-entry.md), the accepted
first Phase 4 increment in
[RFC-0025](../RFC/RFC-0025-minimal-capability-based-candidate-selection.md),
and the automatic-proof boundary in
[RFC-0026](../RFC/RFC-0026-explicit-automatic-routing-proof.md), and the
operator-facing explanation boundary in
[RFC-0027](../RFC/RFC-0027-minimal-operator-facing-routing-explanation.md).

The implementation and tests on `main` include the RFC-0025 automatic
selection and orchestration modules and their test coverage. Merged PR #147
implements the RFC-0026 proof process; merged PR #148 records its real
two-machine result in
[Automatic Routing Two-Machine Proof Result](automatic-routing-two-machine-proof-result.md).
The prior static Phase 3 proof is recorded in
[First Two-Machine Proof Result](first-two-machine-proof-result.md).
Merged PR #151 implements the accepted RFC-0027
`home-ai-cluster-explain-routing` command and its focused tests.

## Phase 4 roadmap criteria

### Capability-based routing goal

**Classification: Partially demonstrated.**

RFC-0025 defines cluster-owned automatic selection by exact capability match,
separate from discovery and execution. The selected candidate is executed
exactly once. RFC-0026 and its recorded proof demonstrate this on two real
machines: one declared-remote `chat` candidate was the sole selectable exact
match, was selected automatically, and returned `HTTP 200` with
`node_id=declared-remote`.

This is not ordinary application behavior: accepted RFC-0025 keeps ordinary
`/v1/chat` local-only and does not activate declared-remote discovery,
automatic selection, or remote transport there. The proven routing behavior is
therefore a deliberately explicit, proof-only composition, not a general
ordinary request-routing surface.

### Simple capability model

**Classification: Demonstrated.**

RFC-0025 retains the existing exact-name `Capability(name)` model and one
requested capability per `ClusterRequest`. Local and declared-remote candidate
discovery use exact declared capability matching. The implementation and
automatic-selection tests exercise `chat` exact matching; the real proof used
that same capability. Richer capability modeling remains outside RFC-0025,
but it is not required for this roadmap outcome's simple model.

### Request constraints

**Classification: Demonstrated.**

RFC-0025 defines `request.constraints.local_only` as a hard restriction after
discovery: it prevents declared-remote selection, contact, and execution. Its
normative matrix covers local and remote matches with both values of that
constraint. Tests cover the matrix and the no-selectable-candidate outcome
when `local_only` excludes the only remote candidate. RFC-0026's real proof
also deliberately constructed its proof request with `local_only=false`.

Other pre-existing constraint fields do not influence this increment. That is
a stated limitation, not evidence that the implemented `local_only` request
constraint is absent.

### Node matching

**Classification: Demonstrated.**

RFC-0025 distinguishes exact capability matching, eligibility, discovery,
selectability, selection, and execution. It specifies local adapter-backed and
declared-remote declaration-backed candidate discovery, filters candidates by
`local_only`, selects the sole candidate deterministically, and applies fixed
local precedence when both are selectable. Tests cover these cases, including
the requirement to execute only the selected candidate once. The RFC-0026
proof demonstrates the sole selectable remote case on two machines.

### Fallback when a node is unavailable

**Classification: Explicitly postponed.**

The roadmap lists fallback as a Phase 4 expected outcome. However, accepted
RFC-0025 deliberately requires exactly-once execution with no retry or
fallback, including after selected remote execution failure. It does not
permanently remove fallback from the project; it defines only the accepted
current increment. The current-state document explicitly lists fallback,
retry, and health-aware routing as postponed, and the RFC-0026 proof likewise
proves no retry or fallback.

Consequently, fallback is not demonstrated and cannot be treated as satisfied
by the proof's visible failure behavior. Defining future fallback requires an
RFC because it determines execution, failure, availability, and routing
semantics.

### Basic explanation of routing decisions

**Classification: Demonstrated.**

RFC-0025 requires deterministic internal explanation facts: requested
capability, matched and selectable candidate families, `local_only` exclusion,
selected node, outcome rule, and no-selectable-candidate reason. The
implementation and its tests provide those internal facts. Accepted RFC-0027
now exposes them through the explicit local
`home-ai-cluster-explain-routing` command.

For each successful command evaluation, the command writes one structured JSON
object with the eight stable RFC-0027 fields. It covers deterministic selection
and no-selection outcomes, including `local_only` exclusion and no matching
candidates, without candidate execution. Its tests cover the distinct current
routing outcomes, the JSON and exit-status contract, absence of prompt input,
and the fact that no adapter, transport, or selected-candidate execution path
is entered. The command is operator-facing while preserving the privacy
boundary: it returns routing facts, not prompt content, model output, history,
tracing, or metrics.

This does not attach explanation to ordinary `/v1/chat` or create production
observability. Those are not required to demonstrate the roadmap's basic
explanation outcome, and ordinary `/v1/chat` remains unchanged.

## Demonstrated results beyond the minimum criteria

- Local and declared-remote candidate discovery is explicit and separate from
  selection.
- The automatic policy preserves `local_only`, uses fixed local precedence,
  and fails before execution when no candidate is selectable.
- Selected execution occurs once, with caller-owned
  `node_id=declared-remote` attribution for declared-remote success.
- The real RFC-0026 proof established: `One endpoint. Two machines. One
  automatically routed request.` It included successful remote Ollama
  execution and left ordinary local-only behavior unchanged.
- The RFC-0027 command provides an explicit no-execution explanation of the
  same RFC-0025 selection facts through a stable operator-facing JSON contract.

## Remaining gaps

The roadmap's fallback outcome is explicitly postponed. RFC-0025 still defines
exactly-once execution with no retry or fallback, and no accepted decision
defines availability, failure classification, or fallback semantics. RFC-0027
does not change execution semantics. Ordinary `/v1/chat` also remains outside
the automatic remote-capable composition by accepted design.

These gaps do not invalidate the demonstrated RFC-0025/RFC-0026 proof. They
do prevent the proof from serving as evidence that every current roadmap
outcome is complete.

## Assessment conclusion

**Phase 4 is not complete.**

The repository demonstrates the proven core of capability-based routing: a
simple exact-name capability model, `local_only` request constraint, matching
and selectability, deterministic automatic selection, exactly-once execution,
internal explanation facts, and a real automatic two-machine result.

The current roadmap still expects fallback when a node is unavailable.
Operator-facing basic routing explanation is now demonstrated by accepted and
implemented RFC-0027. Fallback remains explicitly postponed by the accepted
current increment and current-state record. No accepted decision formally
redefines the roadmap's Phase 4 completion criteria.

## Consequences of the conclusion

The successful RFC-0026 proof should remain recorded as evidence for the
narrow automatic-routing capability, not as Phase 4 closure. The roadmap and
accepted RFCs should remain unchanged by this assessment.

Future work must distinguish implementation of already accepted decisions from
new architectural work. Fallback, retry, and health-aware availability require
an RFC before implementation because they change routing and failure semantics.

## Architectural boundary

This assessment does not decide whether ordinary `/v1/chat` should gain
automatic routing, what fallback policy should be, how availability should be
determined, or how an explanation might be attached to ordinary requests.
Those remain architectural questions. RFC-0025's no-fallback rule is the
accepted boundary for its narrow increment, not a permanent rejection of
fallback.

## References

- [Roadmap](../ROADMAP.md)
- [RFC-0024: Phase 3 Closeout and Phase 4 Entry](../RFC/RFC-0024-phase-3-closeout-and-phase-4-entry.md)
- [RFC-0025: Minimal Capability-Based Candidate Selection](../RFC/RFC-0025-minimal-capability-based-candidate-selection.md)
- [RFC-0026: Explicit Automatic Routing Proof](../RFC/RFC-0026-explicit-automatic-routing-proof.md)
- [RFC-0027: Minimal Operator-Facing Routing Explanation](../RFC/RFC-0027-minimal-operator-facing-routing-explanation.md)
- [Phase 4 Current State](phase-4-current-state.md)
- [Automatic Routing Two-Machine Proof Result](automatic-routing-two-machine-proof-result.md)
- [First Two-Machine Proof Result](first-two-machine-proof-result.md)
