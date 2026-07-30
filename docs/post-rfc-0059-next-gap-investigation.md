# Post-RFC-0059 Next Gap Investigation

Status: Complete

## Context

RFC-0058 and RFC-0059 are accepted and their bounded implementation,
documentation, focused tests, and retained ordinary proof records are present.
This investigation determines whether that completed sequence establishes one
next repository increment. It does not create a roadmap phase, authorize an
RFC, or authorize implementation.

## Investigation question

> After the accepted RFC-0059 sequence, what is the single most concrete and
> bounded remaining gap demonstrated by the current ordinary repository
> behavior, operator workflow, accepted contracts, or retained evidence?

## Accepted current baseline

The current executable vocabulary is closed to `chat` and `summarize`.
Ordinary static declarations can restrict remote capability sets, and an
ordinary `hac static-cluster` caller can restrict its fixed caller-local
routing set. Inline and TOML declaration forms share the same closed
`chat`/`summarize` validation and preserve omission as both capabilities.

That declaration is caller-side routing permission. It neither changes
`hac local` receiver composition nor claims a runtime implementation,
reachability, health, capability discovery, cross-node agreement, or node
selection. Routing still filters by capability, selects a local candidate first
only when it is eligible, preserves eligible remote declaration order, and
uses the existing bounded pre-transmission connection-unavailable traversal.
Status remains its accepted declaration/reachability/runtime observation; it
does not report declared capability lists.

The retained caller-local proof demonstrates the intended healthy topology:
local `chat` and remote `summarize`, with no local summarize failure, selector,
or scheduler. The earlier heterogeneous proof retains remote capability
exclusion and declaration-order evidence.

## Ordinary surface review

The shortest supported paths remain discoverable without historical proof
knowledge:

- `docs/operator-workflow.md` describes local-only and explicit static-cluster
  operation, including receiver startup, retained declaration ownership,
  preflight, health, status, chat, and summarize.
- `docs/command-reference.md` documents the eight ordinary root commands,
  their repository-checkout forms, declaration versus inline topology modes,
  and the caller-local capability boundary.
- `hac static-cluster` and `hac preflight` accept equivalent complete inline
  topology inputs with repeated `--local-capability` and
  `--remote-capability` values. TOML supports the compatible flat one-remote
  and ordered multi-remote forms.
- `hac local` remains the unchanged receiver path; `hac chat` and
  `hac summarize` are one-shot clients of an already-running local or
  static-cluster process. Health and status retain separate, finite purposes.

The workflow makes the important limitations explicit: preflight is
network-free declaration coherence, health is local-only, status is finite
observation rather than a guarantee, and declarations are operator-owned at an
explicit path. No hidden repository-only step is needed to exercise the
accepted healthy-operation specialization.

## Contract consistency review

Current source and focused tests give the accepted concepts one consistent
meaning at their intentionally different ownership boundaries:

| Surface | Observed current behavior |
| --- | --- |
| CLI and TOML parsing | Both validate the same closed non-empty unique capability sets; omission produces `chat` plus `summarize`. |
| Declaration construction | Remote capability sets are declaration-owned; caller-local sets construct only the caller's fixed local routing description. |
| Preflight | Projects those constructed local and remote sets without runtime or network observation. |
| Routing and execution | Capability membership filters eligibility; local-first is among eligible candidates; receiver execution remains unchanged. |
| Request commands | Root `chat` and `summarize` remain topology-blind one-shot clients of the caller process. |
| Status | Intentionally reports a different accepted observation contract and does not imply capability verification. |
| Documentation and proof | The canonical workflow, command reference, RFC-0058/RFC-0059 proofs, and retained Phase 18 evidence describe the same ownership and routing boundaries. |

The focused ordinary-surface test run completed successfully with **320
passed** tests across root dispatch, summarize input/output behavior, inline and
TOML declarations, preflight, static routing, local composition, and status.
This includes explicit/default capability construction, invalid local and
remote data before network use, inline/TOML equivalence, preflight projection,
and restricted caller-local eligibility.

## Evidence review

The retained ordinary evidence is appropriately divided by what can truthfully
be observed through each surface:

- The Phase 18 closeout and two-machine summarize proof establish real local
  and declared-remote summarize execution while preserving the closed request,
  privacy, attribution, and runtime-adapter boundaries.
- The heterogeneous static-capabilities proof establishes real remote
  `chat`/`summarize` eligibility exclusion, using declaration preflight and
  request attribution. It does not claim a healthy local specialization that
  was not then configurable.
- The caller-local static-capabilities proof establishes that remaining
  healthy-operation case: chat stays local and summarize reaches an eligible
  remote without using local failure or fallback.
- Automated tests cover exact parser equivalence, invalid-input/no-network
  boundaries, and combinations that are not useful or safely constructible as
  retained live exercises.

The retained physical proofs use TOML because it is the repeatable multi-node
operator representation. There is no distinct unproven routing contract in the
inline form: it converges on the same validated declaration construction, and
focused tests exercise its equivalence and preflight/static-cluster wiring.
Repeating the physical proof with inline flags would add operator effort and
private-topology exposure without resolving an uncertainty not already covered
by proof plus tests.

Likewise, status does not prove capability membership because RFC-0058 and
RFC-0059 deliberately leave that public result unchanged. Preflight and final
request attribution are the truthful evidence seams for declaration and
routing claims. Adding a status field merely to duplicate those facts would be
a new public-contract decision, not a missing correction.

## Candidate bounded gaps

| Candidate | Concrete observation | Classification | Why it is not the next follow-up |
| --- | --- | --- | --- |
| Additional live inline proof | The retained healthy specialization uses TOML, while inline is covered by focused equivalence and wiring tests. | Evidence repetition; no RFC needed if ever useful. | No distinct behavioral uncertainty or operator problem is demonstrated. |
| Capability lists in status | Status omits capability lists while preflight projects them. | Architectural public-result change; RFC required. | The omission is deliberate, and existing preflight plus request attribution already supplies truthful evidence. |
| Receiver-local capability configuration | `hac local` remains broad although a static caller may restrict its own local candidate. | Architectural ownership/receiver-behavior change; RFC required. | RFC-0059 expressly excludes it; no mismatch or operator need requires reopening that boundary. |
| Broader input, selection, lifecycle, discovery, scheduling, or compatibility work | These remain possible future directions. | New architecture and/or absent evidence. | No current ordinary failure establishes one as a bounded need. |
| Documentation correction | The canonical workflow and command reference already include both capability forms, ownership limits, and the healthy specialization. | No demonstrated correction. | The older records that predate RFC-0058/RFC-0059 are historical evidence, not current-contract contradictions. |

## Primary finding

No single concrete, bounded post-RFC-0059 gap is demonstrated. The completed
sequence closes the previously established ordinary capability-declaration and
caller-local eligibility gap. Current code, tests, operator documentation, and
retained evidence agree on the accepted behavior.

## Architectural boundary

This finding does not treat desirable symmetry as a defect. The following would
need a new decision before implementation: changing capability ownership,
receiver behavior, declaration shape or defaults, routing/fallback policy,
status semantics, request input/output contracts, runtime adapter boundaries,
or privacy/lifecycle authority. In particular, no missing Phase 19, proof
rerun, or status expansion is inferred from the completed RFC-0059 evidence.

## Candidate follow-up categories

If a future real operator report identifies an unmet workflow, first classify
it against the existing surface without retaining prompts, responses, private
topology, credentials, or runtime logs. A demonstrated mismatch may then be a
small documentation correction, implementation correction, proof need, or a
narrow RFC question. This investigation does not select one.

## Conclusion

**Outcome A — no justified follow-up gap is currently established.**

The repository evidence supports no additional bounded documentation, proof,
consistency, implementation-correction, or architectural-contract follow-up
immediately after RFC-0059. The responsible next input is a concrete,
privacy-safe operator need, not a new phase or inferred feature.
