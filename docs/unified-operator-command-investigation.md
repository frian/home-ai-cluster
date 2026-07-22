# Unified Operator Command Investigation

## 1. Status and authority

Investigation only. This document establishes no accepted command syntax or behavior, creates no Phase 18, changes neither an RFC nor the roadmap, and authorizes no implementation. No change remains a valid conclusion.

Question: should one installed `home-ai-cluster` root command provide explicit subcommands for selected, already accepted ordinary surfaces while preserving existing entry points and their contracts?

## 2. Current installed command inventory

`pyproject.toml` declares the following scripts. Classifications come from entry points, accepted RFCs, and README/workflow guidance—not names alone.

| Command | Entry point and purpose | Class / authority | Ordinary README guidance | Standalone if root exists? |
| --- | --- | --- | --- | --- |
| `home-ai-cluster-static-proof` | `static_proof:main`; fixed two-machine proof process | Proof; RFC-0022 | No | Yes |
| `home-ai-cluster-static-cluster` | `static_cluster:main`; foreground ordinary static-cluster process | Ordinary startup; RFC-0038–0040, 0043 | Yes | Yes |
| `home-ai-cluster-automatic-proof` | `automatic_proof:main`; routing proof process | Proof; RFC-0026 | No | Yes |
| `home-ai-cluster-fallback-proof` | `fallback_proof:main`; fallback proof process | Proof; RFC-0028 | No | Yes |
| `home-ai-cluster-explain-routing` | `routing_explanation:main`; finite synthetic routing explanation | Inspection; RFC-0027 | Diagnostic only | Yes |
| `home-ai-cluster-explain-request` | `actual_request_explanation:main`; finite local request account | Explanation/history source; RFC-0032–0035 | No | Yes |
| `home-ai-cluster-openai-compatibility` | `openai_compatibility:main`; foreground loopback compatibility process | Compatibility startup; RFC-0031, 0046–0047 | Yes | Yes |
| `home-ai-cluster-health` | `local_health_snapshot:main`; finite runtime observation | Inspection; RFC-0033, 0048 | Yes | Yes |
| `home-ai-cluster-preflight` | `static_preflight:main`; finite coherence inspection | Inspection; RFC-0036, 0048 | Yes | Yes |
| `home-ai-cluster-status` | `status_command:main`; finite static-cluster observation | Inspection; RFC-0041, 0044, 0048 | Yes | Yes |
| `home-ai-cluster-history` | `request_history:history_main`; prints bounded metadata history | History; RFC-0035 | No | Yes |
| `home-ai-cluster-clear-history` | `request_history:clear_history_main`; clears bounded history | History; RFC-0035 | No | Yes |
| `home-ai-cluster-phase-12-heterogeneous-receiver` | `phase_12_heterogeneous_runtime_cluster_proof:main`; receiver proof | Proof; Phase 12 | Proof-only | Yes |
| `home-ai-cluster-local` | `local_runtime:main`; foreground ordinary local process | Ordinary startup; RFC-0042 | Yes | Yes |
| `home-ai-cluster-chat` | `chat_command:main`; one native request to an already running process | Ordinary finite request; RFC-0045, 0049 | Yes | Yes |

The proof commands are not ordinary product commands. The `explain-*` commands have narrow diagnostic/account meanings, and history is tied to the explicit request-account surface rather than ordinary chat. None belongs under a root command merely because it is installed.

## 3. Concrete operator friction

The repository itself has retained limited evidence of command-selection mistakes: README and the canonical workflow require navigation among separately named preflight, health, startup, status, compatibility, and chat commands, but record no wrong-executable incident, proof/ordinary confusion, or compensating alias. The daily-workflow investigation treats personal shell functions or aliases as possible convenience, not project contracts; it does not show that they are used.

There is now explicit first-user evidence. The project's technical first user reviewed the completed post-roadmap system, identified the fragmented collection of independently named commands as a concrete missing usability feature, and selected one coherent root operator command as the next priority. This report concerns command discovery and naming coherence only; it does not report missing runtime, routing, lifecycle, topology, or configuration behavior.

That report turns plausible name-recall and discovery friction into a concrete operator usability gap. A root command can improve coherence, but must preserve the separate ownership of finite commands and foreground processes rather than conceal it.

## 4. Candidate root-command scope

| Candidate | Operator value and coherence | Contract/risk | RFC? |
| --- | --- | --- | --- |
| A — no change | Preserves explicit boundaries. | No new public surface. | No |
| B — ordinary finite only | Groups `chat`, `preflight`, `health`, `status` without lifecycle implication. | Omits ordinary startup; durable names/help still result. | Yes |
| C — ordinary startup and finite | Reflects canonical ordinary workflows: `local`, `cluster`, `compatibility`, `chat`, and inspection. | Most discoverable, but must preserve foreground signals and lifecycle distinctions. | Yes |
| D — all non-proof scripts | Includes history and explanation. | Elevates secondary forensic surfaces into everyday concepts. | Yes |
| E — every script | Exhaustive list. | Makes proof scaffolding look like ordinary product operation; reject absent evidence. | Yes |

Candidate C is the most coherent scope for further architectural decision: it groups ordinary foreground process commands with ordinary finite request and inspection commands, while excluding proof utilities and lifecycle management. A root command is a public operator contract, not packaging cleanup; its exact selected subcommands remain RFC decisions.

## 5. Candidate subcommand vocabulary

Possible vocabulary, if scope were accepted:

```text
home-ai-cluster local
home-ai-cluster static-cluster
home-ai-cluster compatibility
home-ai-cluster chat
home-ai-cluster preflight
home-ai-cluster health
home-ai-cluster status
```

`local` accurately names the local foreground process. `static-cluster` is more exact than `cluster`, which can hide the accepted static operator declaration. `compatibility` is more truthful than `openai`, since RFC-0031 is narrow rather than general OpenAI support. The remaining names match current purposes.

`start`, `run`, and `serve` risk implying daemonization, supervision, restart, stop, or ownership. `inspect` hides material differences between preflight, health, and status. Nested `history clear`, and nested or flat explain commands, should not be selected before deciding whether those surfaces belong under the root. No aliases or abbreviations should be assumed.

## 6. Delegation boundary

Every reviewed command entry point accepts `argv: Sequence[str] | None`; chat also has a test-only client-factory keyword. Their parsers may raise `SystemExit`, write directly to stdout/stderr, and foreground commands call `uvicorn.run`. Parser `prog` values are legacy script names, so direct calls change help/usage unless explicitly adapted.

Direct in-process delegation is the smallest future option: pass only the subcommand remainder to the existing `main()` and retain its streams, exit status, and signals. It cannot make root help byte-for-byte identical to legacy help. Small command-specific adapters might be clearer if root-oriented help is selected, but must not become a generic framework.

Subprocess delegation preserves legacy parser identity but adds PATH/install-environment reliance, child-signal forwarding, and long-running error complexity. Duplicating parsing risks drift. A generic command framework is disproportionate. These observations authorize no refactoring.

## 7. Compatibility contract

Installed scripts may be public contracts. A root would initially need to be additive:

```text
home-ai-cluster chat ...
home-ai-cluster-chat ...
```

The legacy scripts must retain exact arguments, stdout, stderr, exit codes, environment behavior, and long-running signal behavior. Root help and usage form a new contract. Old scripts should remain indefinitely unless separate evidence supports deprecation and an RFC accepts it; fewer scripts is insufficient justification.

## 8. Root and subcommand behavior

A future RFC would decide no-subcommand, `--help`, `--version`, unknown names, option placement, global options, root errors, aliases, abbreviations, and whether proof utilities appear in root help. It should prefer explicit full names, TTY-independent output, no interactive selection, no correction, no implicit startup, and no global configuration. It must not invent a generic failure category where delegated commands already own errors.

## 9. Process and lifecycle ownership

| Class | Current commands |
| --- | --- |
| Finite local command | `chat`, `preflight`, `health`, routing/request explanation |
| Long-running local process | `local` |
| Long-running static-cluster process | `static-cluster` |
| Compatibility process | `openai-compatibility` |
| Read-only observation | `preflight`, `health`, `status` |
| Local history operations | `history`, `clear-history` |
| Proof utilities | static, automatic, fallback, and Phase 12 proof commands |

The canonical workflow retains foreground processes and operator-owned terminal, runtime startup, and shutdown. A facade must add no daemon mode, PID files, restart policy, polling, process discovery, background work, or `start`/`stop` manager.

## 10. Privacy assessment

Static root help need not inspect runtimes, declarations, topology, or environment. A facade must add no prompt/response logging, telemetry, shell-history rewriting, hidden files, retained configuration, analytics, history, environment inspection, or network access. Help must avoid exposing runtime- or topology-specific details that existing boundaries keep separate.

## 11. Architecture and RFC assessment

A root owns a durable namespace, stable subcommand names, compatibility expectations, help/error behavior, and lifecycle presentation. It is an architectural operator-surface decision, not merely a `pyproject.toml` packaging detail. Implementation requires an accepted RFC.

## 12. Phase classification

If accepted later, this would be a small standalone post-roadmap refinement—not maintenance and not Phase 18. User visibility alone does not create a phase.

## 13. Recommendation

**Draft a narrow RFC for an additive `home-ai-cluster` root command that delegates to a selected set of already accepted ordinary command surfaces.** The explicit first-user report justifies this next decision; it does not itself accept command syntax or implementation.

The RFC should be limited to one new installed entry point; explicit full subcommands; selected ordinary startup, request, compatibility, and inspection surfaces; and strict preservation of existing request, output, failure, process, signal, routing, runtime, topology, and privacy behavior. Existing standalone commands remain supported without deprecation. It must exclude proof commands, history and explanation commands unless separately justified by the RFC, daemonization, supervision, start/stop/restart management, implicit startup, global configuration, discovery, scheduling, generic CLI or plugin frameworks, and Phase 18.

Stopping condition: stop after the RFC has selected the exact subcommand set and vocabulary, compatibility/help/error rules, and delegation boundary, or reject the facade. Do not implement before that accepted decision.

## 14. Boundaries retained

Excluded: new runtime, routing, topology, fallback, retry, or configuration behavior; supervision, daemonization, start/stop/restart, discovery, scheduling, configuration generation, shell completion, prompts, TUI, dashboard, generic command/plugin frameworks, unreviewed aliases, removal/deprecation, database, Docker, and Kubernetes.

## 15. Files inspected

- Governing documents: `VISION.md`, `FOUNDATIONS.md`, `PRINCIPLES.md`, `NON_GOALS.md`, `ROADMAP.md`, `QUESTIONS.md`, `CONTRIBUTING.md`, `AGENTS.md`, `RFC/README.md`, `README.md`, and `pyproject.toml`.
- Accepted operator-surface RFCs: RFC-0031; RFC-0035 through RFC-0049; and earlier governing RFCs for static proofs, routing explanation, and request explanation (RFC-0022, RFC-0026–0028, RFC-0032–0034).
- Phase 14–17 investigations, proofs, and closeouts; `operator-workflow.md`, daily-workflow records, post-roadmap investigations, human-readable inspection and one-shot chat investigations, and retained native/compatibility proof records.
- Fifteen installed scripts across fourteen distinct implementation modules (the two history scripts share `request_history.py`) and focused command tests: `test_static_proof.py`, `test_static_cluster_cli.py`, `test_automatic_proof.py`, `test_fallback_proof.py`, `test_routing_explanation.py`, `test_actual_request_explanation.py`, `test_openai_compatibility.py`, `test_local_health_snapshot.py`, `test_static_preflight.py`, `test_status_command.py`, `test_request_history.py`, `test_phase_12_heterogeneous_runtime_cluster_proof.py`, `test_local_runtime_composition.py`, and `test_chat_command.py`.
