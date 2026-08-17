# Retained Proof Scaffolding Investigation

Status: Investigation

Date: 2026-08-17

> Follow-up disposition: this is a pre-RFC-0075 factual snapshot. RFC-0075 was
> subsequently accepted and implemented, retiring all four installed historical
> proof launchers while retaining the historical records and Git history.
> A later bounded cleanup also removed the separately out-of-scope Phase 5 proof
> runner after confirming that ordinary runtime composition no longer required it.

## Question

Which retained proof executables and proof-named implementation seams still
have a live architectural or compatibility role now that ordinary static
multi-node operation has been implemented and physically reproduced? Which,
if any, are candidates for a later explicit retirement decision?

This is a documentation-only inventory. It changes no command, source module,
test, RFC, behavior, or compatibility contract. Accepted RFCs remain the
architectural authority.

## Current installed surface inventory

`pyproject.toml` currently declares seventeen console scripts. The ordinary
root surface is `home-ai-cluster`; `hac` is its accepted short installed alias,
not a separate implementation. RFC-0050 deliberately kept the standalone
commands supported and deliberately excluded proof utilities from root help.

| Script | Classification | Current justification | Investigation result |
| --- | --- | --- | --- |
| `home-ai-cluster` | Ordinary root/operator surface | RFC-0050 | Canonical ordinary root command. |
| `hac` | Retained standalone alias of an ordinary surface | RFC-0052 | Accepted short alias of `home-ai-cluster`; not proof scaffolding. |
| `home-ai-cluster-local` | Ordinary operator surface | RFC-0042 | Ordinary local-runtime process. |
| `home-ai-cluster-static-cluster` | Ordinary operator surface | RFC-0038; later declaration and multi-node RFCs | Ordinary explicit static multi-node process. |
| `home-ai-cluster-openai-compatibility` | Ordinary, narrow compatibility surface | RFC-0031 and subsequent compatibility RFCs | Deliberately narrow loopback compatibility process, also reached by `hac compatibility`. |
| `home-ai-cluster-chat` | Ordinary one-shot operator surface | RFC-0045, RFC-0053, RFC-0060 | Supported native client, also reached by `hac chat`. |
| `home-ai-cluster-preflight` | Accepted narrow diagnostic/inspection surface | RFC-0036 | Static coherence inspection; not proof-only. |
| `home-ai-cluster-health` | Accepted narrow diagnostic/inspection surface | RFC-0033 | Local runtime observation; not proof-only. |
| `home-ai-cluster-status` | Accepted narrow diagnostic/inspection surface | RFC-0041 | Bounded declared-static-cluster observation; not proof-only. |
| `home-ai-cluster-explain-routing` | Accepted narrow diagnostic/inspection surface | RFC-0027 | Synthetic, no-execution routing explanation. It is correctly excluded from the first root facade for scope reasons, not because it is a proof utility. |
| `home-ai-cluster-explain-request` | Accepted narrow diagnostic surface | RFC-0032 and RFC-0034 | One local, prompt-free actual-request account. |
| `home-ai-cluster-history` | Accepted narrow history surface | RFC-0035 | Prints the bounded, opt-in, prompt-free history owned by the actual-request command. |
| `home-ai-cluster-clear-history` | Accepted narrow history surface | RFC-0035 | Clears that same bounded local history. |
| `home-ai-cluster-static-proof` | Historical proof-only surface | RFC-0022 | Fixed `declared-remote-only` two-machine proof process. |
| `home-ai-cluster-automatic-proof` | Historical proof-only surface | RFC-0026 | Fixed automatic-routing proof process with no matching local candidate. |
| `home-ai-cluster-fallback-proof` | Historical proof-only surface | RFC-0028 | Fixed pre-execution local-to-declared-remote fallback proof process. |
| `home-ai-cluster-phase-12-heterogeneous-receiver` | Historical proof-only surface | RFC-0030 and RFC-0038 boundaries; disposition recorded by the Phase 13 closeout | Proof-scoped llama-server receiver. No accepted RFC makes this command an ordinary operator contract; RFC-0042 expressly keeps ordinary runtime composition separate from it. |

There is no uncertain entry in the current script table. In particular,
`explain-routing`, `explain-request`, `history`, and `clear-history` are
legitimate accepted diagnostic/history contracts and are outside this cleanup
question. Their absence from `hac` is an intentional RFC-0050 scope boundary,
not evidence that they are obsolete.

## Proof-scoped source inventory

| Artifact | Original purpose | Installed reachability | Ordinary dependency and replacement evidence | Retention assessment |
| --- | --- | --- | --- | --- |
| `src/home_ai_cluster/static_proof.py` | RFC-0022 process: one fixed `declared-remote` and declared-remote-only selection. | Yes, through `home-ai-cluster-static-proof`. | Ordinary `static_cluster.py` does not import it. `home-ai-cluster-static-cluster` now constructs ordinary static wiring and was physically reproduced in `docs/phase-8-ordinary-static-multi-node-proof.md`. | Historical launcher. Its exact caller-directed selection experiment is not identical to ordinary local-first operation, but its founding two-machine architecture has ordinary replacement coverage. |
| `src/home_ai_cluster/automatic_proof.py` | RFC-0026 automatic selection where the declared remote is the only selectable `chat` candidate. | Yes, through `home-ai-cluster-automatic-proof`. | No ordinary module imports it. Ordinary static capability routing and capability-specific remote execution exercise automatic eligibility and selection, but do not recreate its empty-local fixed proof composition exactly. | Historical launcher with substantial, but not byte-for-byte, ordinary replacement coverage. |
| `src/home_ai_cluster/fallback_proof.py` | RFC-0028's bounded proof composition: deliberately unavailable local Ollama, then one declared-remote fallback. | Yes, through `home-ai-cluster-fallback-proof`. | No ordinary module imports it. Ordinary `static-cluster` uses the proof-neutral static-remote fallback seam, and the Phase 8 ordinary proof records the same accepted local pre-execution failure followed by one remote request. | Historical launcher whose architectural behavior is exercised by the ordinary surface. |
| `src/home_ai_cluster/phase_12_heterogeneous_runtime_cluster_proof.py` | Phase 12 receiver with a llama-server adapter and proof-specific identity/binding. | Yes, through `home-ai-cluster-phase-12-heterogeneous-receiver`. | No ordinary module imports it. RFC-0042 added ordinary `LocalAppComposition`; `docs/phase-13-explicit-local-runtime-composition-proof.md` and the Phase 13 closeout record the ordinary `home-ai-cluster-local --runtime llama-server` receiver path. | Historical launcher. Phase 13 says to retain it as reproducibility evidence, so it needs an explicit later decision before change. |
| `src/home_ai_cluster/phase_5_runtime_adapter_proof.py` | RFC-0030 direct local proof that Ollama and llama-server satisfy the shared adapter boundary. | No `[project.scripts]` entry; executable only with `python -m`. | No ordinary module imports the proof runner. The Phase 12 receiver imports only its `local_http_url` import binding; that is therefore a proof-to-proof dependency, not an ordinary one. Ordinary runtime composition later exercises both adapters through the application boundary. | Historical proof composition, not an installed command. If Phase 12 is retired, move the URL helper import to its proof-neutral owner before considering this module dead. |
| `src/home_ai_cluster/api/proof_orchestrator.py` | RFC-0022 composition of candidate collection, explicit proof selection, and selected-candidate execution. | Indirectly, only through `static_proof.py` and the route proof-wiring branch. | Ordinary static-cluster routing uses `orchestrate_request_with_static_remote_fallback`, not this module. | Proof-only orchestration adapter; it would have no ordinary caller if the static proof surface and proof compatibility branch were retired. |

Retained proof documents establish historical evidence. Except where a document
states a live reproduction procedure, they do not by themselves require the
Python implementation to remain executable forever.

## Proof-specific ordinary-code seams

The current code deliberately separates proof-named compatibility aliases from
the proof-neutral static architecture. The following distinction is essential
to any future cleanup.

| Seam | Current users | Ordinary role | Consequence if the corresponding proof launcher were retired |
| --- | --- | --- | --- |
| `StaticRemoteProofWiring`, `StaticRemoteProofWiringError`, and `build_static_remote_proof_wiring` in `src/home_ai_cluster/api/wiring.py` | `static_proof.py`, `api/proof_orchestrator.py`, routes, and proof-focused tests. | The aliases/wrapper are compatibility names only. They resolve to `StaticRemoteWiring` / `StaticRemoteWiringError`, while `StaticRemoteWiring` and `build_static_remote_wiring` are used by ordinary static-cluster operation. | The proof names and wrapper may become dead; the proof-neutral classes, validation, remote declaration registry, transport, and ordinary builder must remain. |
| `static_remote_proof_wiring` parameter and app-state value in `main.py` | The static proof launcher and proof tests. | None for current ordinary static-cluster construction, which uses `static_remote_wiring` or `static_remote_collection_wiring`. | The argument, state slot, and proof route branch could become dead, but only after all accepted proof compatibility callers are retired. |
| `orchestrate_static_remote_proof(...)` and its `api/proof_orchestrator.py` module | The `static_remote_proof_wiring` branch in `api/routes.py`; static proof tests. | None. Ordinary paths use static fallback orchestration. | Dead with the static-proof-only compatibility path; selected-candidate orchestration in `core` remains shared architecture. |
| `automatic_proof_orchestrator` app state and the early branch in `api/routes.py` | `automatic_proof.py`, `fallback_proof.py`, focused tests, and a test-only code-capability injection. | None for ordinary static wiring. The same route also sets `local_only=False` for ordinary `static_remote_wiring` and collection wiring independently. | The injection state and its branch would become dead if both automatic and fallback proof launchers were retired. Do not remove the ordinary static wiring checks or `local_only=False` behavior. |
| `ProofReceivingAppWiring`, `proof_receiving_app_wiring`, and `create_proof_receiving_app(...)` | Phase 12 receiver and its tests. | None. Ordinary receivers now use `LocalAppComposition`, including internal request and status handling. | The proof-specific type, constructor, state branch, and Phase 12 launcher could become dead together. The ordinary local-composition and internal-receiver paths must remain. |
| `/internal/cluster/request` and `/internal/cluster/status` | Proof receivers and ordinary static-cluster remote receivers. | Shared receiver-local execution and status boundaries. | Not disposable: ordinary remote execution and status use these routes even if every early proof launcher disappears. |

This also explains why a proof word in a name is insufficient evidence for
deletion. `StaticRemoteWiring`, remote transport, candidate collection,
selected-candidate execution, ordinary static fallback, and internal receiver
routes are proof-neutral architecture that later ordinary operation reuses.

## Test inventory

| Tests | What they primarily verify | Classification for a later retirement review |
| --- | --- | --- |
| `tests/test_static_proof.py` | RFC-0022 parser, fixed binding, declaration, client lifetime, and launcher construction. | Historical executable contract only. |
| `tests/test_automatic_proof.py` | RFC-0026 launcher, one remote automatic execution, no fallback, and default local-only isolation. | Historical executable contract; its ordinary-local isolation assertion should survive elsewhere. |
| `tests/test_fallback_proof.py` | RFC-0028 launcher composition and one bounded fallback. | Historical executable contract; the fallback algorithm is independently covered. |
| `tests/test_phase_12_heterogeneous_runtime_cluster_proof.py` | Phase 12 receiver arguments, proof composition, and ordinary-app isolation. | Historical launcher contract; preserve ordinary composition isolation coverage elsewhere. |
| `tests/test_phase_5_runtime_adapter_proof.py` | Direct RFC-0030 proof helper behavior and privacy-safe proof output. | Historical proof-runner coverage; adapter implementations and ordinary composition have independent tests. |
| `tests/test_static_remote_proof_orchestrator.py` | Proof selection modes and selected-candidate execution composition. | Primarily historical proof seam. Generic candidate selection and execution must remain covered by `test_routing_candidates.py`, `test_selected_candidate_orchestration.py`, and ordinary static tests. |
| Proof sections in `tests/test_api_wiring.py` and `tests/test_app.py` | Proof wiring aliases, route branch, proof receiver behavior, and preservation of local-only defaults. | Mixed. Alias/branch assertions are historical; local-only defaults, internal receiver locality, and ordinary static wiring are shared behavior and need retained coverage. |
| `tests/test_static_remote_wiring.py` | Proof aliases delegate to proof-neutral static wiring; ordinary single-remote and ordered collection wiring. | Mixed. The alias assertions are historical; `StaticRemoteWiring` and collection tests are ordinary shared architecture. |
| `tests/test_fallback_capability_orchestration.py` | The actual static fallback algorithm plus one legacy proof-facing wrapper delegation test. | Mostly shared architecture. Only `test_proof_facing_fallback_entry_delegates_to_neutral_seam` is proof-compatibility coverage. |
| `tests/test_command.py` | The complete installed-script table and root parser scope. | It currently enforces retained proof entry points as packaging compatibility. Any removal requires intentionally changing this test after an accepted decision. |
| `tests/test_code_capability.py` | A test injection through `automatic_proof_orchestrator`. | Test-only exercise of a proof-only injection branch, not an ordinary code-capability requirement. |

`tests/test_openai_compatibility.py` has a separately named
`--proof-observation` facility. It belongs to the narrow compatibility proof
contract, not to these four historical launchers; it should not be removed as
collateral cleanup without its own contract review.

## Documentation dependency inventory

| Document set | Role today | Dependence on a historical executable | Effect of a later retirement |
| --- | --- | --- | --- |
| `docs/operator-workflow.md` | Current canonical operator guide. Mode 3 labels `home-ai-cluster-static-proof` as an explicit *historical* proof operation; Modes 1–2 are the ordinary paths. | Contains a runnable historical reproduction command and links to the detailed runbook. | Update the current guide and add an archival note or link. Do not rewrite its record as if static-cluster had been the original RFC-0022 command. Its condition saying this mode remains documented until ordinary proof is complete has been satisfied by the retained ordinary-mode proof. |
| `docs/static-two-machine-proof.md` and `docs/first-two-machine-proof-result.md` | RFC-0022 historical runbook and evidence. | The runbook instructs `home-ai-cluster-static-proof`; the result records it. | Preserve the evidence. Mark the runbook historical/non-current or add an archival note; do not replace its actual historical command. |
| `docs/automatic-routing-two-machine-proof-result.md` | Historical RFC-0026 proof result. | Records `home-ai-cluster-automatic-proof`. | No current operator-guide rewrite is needed; retain historical truth and, if useful, add an archival availability note. |
| `docs/rfc-0028-two-machine-fallback-proof-result.md` | Historical RFC-0028 proof result. | Records `home-ai-cluster-fallback-proof`. | Same: retain evidence, not a rewritten procedure. |
| `docs/phase-12-heterogeneous-runtime-cluster-proof.md` | Retained Phase 12 proof procedure/evidence. | Instructs the Phase 12 receiver launcher. | Mark it historical/non-current if retired; retain the commands as the record of what was actually proved. |
| `docs/phase-13-closeout.md` | Later closeout. | Explicitly says to retain the Phase 12 launcher as historical reproducibility evidence and not extend it. | It must be amended by the decision that changes disposition; this is stronger than a mere historical proof mention. |
| `docs/evidence/phase-5-runtime-adapter-proof.md` | Historical RFC-0030 evidence. | Uses `python -m home_ai_cluster.phase_5_runtime_adapter_proof`, not an installed script. | Retain unchanged as historical evidence; an archival note is sufficient if the module is later removed. |
| `docs/command-reference.md`, `README.md`, and `docs/README.md` | Current ordinary command lookup, project entry, and document index. | They do not present automatic, fallback, or Phase 12 launchers as ordinary operations. The command reference intentionally excludes historical/specialized commands; the operator workflow alone still exposes the historical static proof reproduction. | Remove any obsolete current-facing availability claim only after a decision. Keep index links to retained records. |

## Current replacement coverage

| Historical proof executable or module | Property originally demonstrated | Current ordinary evidence | Equivalence assessment |
| --- | --- | --- | --- |
| Static proof | One endpoint, two machines, one request over one explicit declared remote with caller-directed declared-remote-only selection. | `home-ai-cluster-static-cluster`; `docs/phase-8-ordinary-static-multi-node-proof.md`; current native `chat`, `summarize`, `classify`, and `code` paths. | The ordinary mode proves the founding two-machine architecture and has broader operational coverage. It does **not** reproduce the old declared-remote-only selection policy exactly. |
| Automatic proof | Automatic capability selection reaches the declared remote because it is the only selectable `chat` candidate. | Ordinary static declarations with capability eligibility; later capability-specific remote execution proofs, including physical two-machine `classify` and `code` evidence. | Ordinary paths exercise capability-based remote selection. The exact empty-local proof topology is historical-only. |
| Fallback proof | One selected local candidate fails before transmission, then one already discovered remote candidate executes once. | Ordinary static-cluster fallback; `docs/phase-8-ordinary-static-multi-node-proof.md`; later ordinary remote request and capability proofs. | Materially equivalent architectural behavior is now ordinary and physically reproduced. |
| Phase 12 heterogeneous receiver | A caller remains runtime-neutral while a receiver runs llama-server. | Ordinary `home-ai-cluster-local --runtime llama-server`, ordinary static-cluster caller, and the Phase 13 retained ordinary proof. | Materially superseded by the ordinary composition, which RFC-0042 required not to use the Phase 12 launcher. |
| Phase 5 adapter proof runner | Both explicit local adapters produce cluster-owned results and unavailable failures through the adapter boundary. | Adapter tests plus ordinary local runtime composition and later heterogeneous operation. | The direct two-adapter runner remains useful historical evidence, but its exact direct-comparison procedure is not an ordinary operator feature. |

Later ordinary evidence is therefore strong enough to justify a retirement
*decision discussion* for the first four launchers. It is not evidence that
those executable contracts have already ceased to exist.

## Findings

1. No retained historical proof executable is required by ordinary current
   operation. `static-cluster`, `local`, the native capability clients, and
   the internal receiver routes do not import the proof launcher modules.
2. The static, automatic, and fallback launchers remain installed primarily
   because accepted RFCs created explicit proof-only process contracts and
   RFC-0050 intentionally preserved standalone installed commands. The Phase
   12 launcher additionally has an explicit later closeout retention statement.
3. Retiring the historical launchers would make the proof aliases/wrapper,
   static proof route branch and orchestrator, automatic-proof injection
   branch, and Phase 12 proof-receiver composition candidates for deletion.
   Their removal must be sequenced with their callers and focused tests.
4. The static remote wiring implementation underneath the proof aliases, the
   routing/execution primitives, static fallback, and internal receiver routes
   are shared ordinary architecture. They must not be moved or deleted merely
   because an old proof module uses them.
5. The explanation and history commands are accepted narrow diagnostic/history
   surfaces. They are deliberately outside `hac` but not in the proof-retirement
   set.
6. A new permanent `legacy/` or `archive/` Python directory would add a second
   live packaging and import boundary without preserving more historical truth
   than Git history plus retained RFCs, runbooks, proof records, and closeouts.
   If a later decision removes dead executable code, deletion is preferable to
   relocation; preserve the historical documents.

## Decision boundary

### Factual inventory

The installed proof commands, their source modules, their route/app-state
seams, their focused tests, and their historical documents still exist on the
current branch. Ordinary static multi-node operation and ordinary heterogeneous
receiver composition are separately implemented and physically reproduced.

### Evidence-supported observations

The ordinary surface now covers the founding remote topology, accepted bounded
fallback, capability-specific remote execution, and heterogeneous receiving
runtime operation. The historical launchers are no longer required to operate
those ordinary paths.

### Possible future cleanup

A bounded future change could retire selected installed proof launchers and
then remove code and tests that have no remaining caller, while retaining proof
documents and preserving shared routing, fallback, adapter, and receiver
coverage. Deletion is preferable to moving executable code to an archive
package.

### Required architectural/compatibility decision

That change must **not** proceed from this investigation. Removing an installed
script changes an accepted standalone compatibility surface: RFC-0022,
RFC-0026, and RFC-0028 name their proof commands, RFC-0050 preserves existing
standalone commands, and the Phase 13 closeout explicitly retains the Phase 12
launcher. Retirement, deprecation, redirection, or replacement therefore needs
a new RFC before implementation. The RFC must choose the exact command set,
whether any command remains reproducible, documentation disposition, migration
or absence-of-migration policy, and the precise shared tests that remain.

## Recommended next step

Do not change executable code in this PR. If the project wants less retained
scaffolding, first open one narrowly scoped RFC on retirement of the four
historical installed proof surfaces. Start with an explicit choice about
`home-ai-cluster-static-proof`, because it is the only historical launcher still
presented as a runnable mode in the canonical workflow. The RFC can decide
whether the static, automatic, fallback, and Phase 12 launchers retire together
or in separately justified increments; it should not broaden `hac` or alter
ordinary routing to compensate.
