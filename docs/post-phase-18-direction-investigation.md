# Post-Phase-18 Direction Investigation

Status: Investigation only

## Purpose and authority

This investigation asks whether completed Phase 18 and its retained real
two-machine summarize proof identify one justified next bounded increment. It
does not assume that further repository work is required, create a phase, amend
the roadmap or an RFC, or authorize implementation. Accepted RFCs remain the
architectural authority.

## Established baseline

The repository now has exactly two executable capabilities: `chat` and
`summarize`. Both have normalized local execution and can use ordinary
declared-remote execution. Routing remains capability-centered and local-first;
remote attribution remains caller-owned; runtime identity remains behind
adapters; and topology remains explicit and static. Ordinary static declarations
remain topology-only.

The internal request family is strictly closed to tagged chat and summarize
requests. A real two-machine summarize execution is retained. Supported request
history retains neither summarize source text nor generated summary. Phase 18
is complete, and no Phase 19 is accepted or planned.

The Phase 18 physical preparation did identify one relevant implementation
defect: the ordinary static remote factory had advertised only `chat`, making an
ordinary remote ineligible for `SummarizeRequest`. PR #337 corrected that
factory to advertise the two supported capabilities without changing topology
declarations, routing, fallback, transport, attribution, runtime behavior, or
privacy. The completed proof then used the corrected ordinary path. This is
evidence that the factory declaration needs retained tests and truthful
preflight, not evidence that topology must carry capability data.

## Method

Candidates below are assessed only where repository evidence identifies either a
concrete operator problem or a missing proof with distinct architectural value.
Existing accepted surfaces are distinguished from hypothetical additions. A
candidate is not justified merely because another capability or command has a
superficially similar surface.

## Candidate assessment

### A. Ordinary operator access to summarize

**Observed problem or missing evidence.** The native `POST /v1/summarize`
endpoint is usable by direct HTTP. The unified root command has no summarize
subcommand, and there is no installed one-shot summarize client. No retained
operator report establishes that direct bounded text submission is inadequate.

**Existing accepted surfaces.** The native endpoint supplies the bounded text
contract, local-first static-cluster composition, normalized result, and
caller-owned attribution. The one-shot `home-ai-cluster-chat` command is an
accepted chat-only client. RFC-0050 deliberately keeps the unified command
namespace closed, and RFC-0051 deliberately added no summarize CLI.

**Smallest credible change and contract assessment.** A text-only one-shot
client would need an input contract, validation, output presentation, and clear
handling of shell history, command-line exposure, standard input, and files.
Those choices are not a mechanical extension of chat. They change an ordinary
operator surface and therefore need an RFC before implementation.

**Proof, privacy, and risk.** A useful proof would require one concrete
operator workflow that direct HTTP cannot serve. Standard input or file input
would broaden content and retention boundaries; putting source text in process
arguments or shell history also needs explicit privacy treatment. Adding a CLI
because endpoint symmetry feels incomplete would create a contract without that
evidence.

**Recommendation.** Do not add a summarize CLI or RFC now. Collect one concrete
privacy-safe operator need first.

### B. Static capability declaration truth

**Observed problem or missing evidence.** The Phase 18 factory drift was real:
ordinary remote eligibility, preflight, and status shared one chat-only factory
despite the ordinary supported capability set including summarize.

**Existing accepted surfaces.** PR #337 corrected the factory and added focused
coverage for ordinary declaration facts, summarize eligibility, and preflight.
The successful physical proof observed the corrected preflight. Static
declarations intentionally contain only node identity and transport location;
they do not configure capabilities. There is no dynamic capability exchange.

**Smallest credible change and contract assessment.** The bounded correction is
already complete. Further strengthening may be ordinary regression testing or
documentation maintenance if a new supported capability is accepted. Moving
capabilities into TOML, probing remotes, or exchanging live capabilities would
change topology, configuration, protocol, and routing authority, and would
require an RFC.

**Proof, privacy, and risk.** Existing focused tests and the retained preflight
observation address the demonstrated drift. A new live capability observation
would add network and trust semantics without a demonstrated need. Treating
topology declarations as capability inventories would violate their accepted
privacy and ownership boundary.

**Recommendation.** Sufficiently corrected; no follow-up repository change is
justified by this defect alone.

### C. Heterogeneous summarize execution

**Observed problem or missing evidence.** Both current adapter families
implement summarize and have automated mapping coverage. The retained physical
summarize execution used Ollama on both machines; an earlier retained proof
established heterogeneous two-machine chat execution.

**Existing accepted surfaces.** Normalized summarize semantics, capability
eligibility, remote transport, and runtime-specific adapter mappings are already
accepted. The physical proof demonstrated real remote summarize; the earlier
heterogeneous proof demonstrated the runtime-adapter boundary across machines.

**Smallest credible change and contract assessment.** A heterogeneous summarize
rerun could be performed using existing surfaces, so it would not itself need an
RFC. It would be a retained proof only, not implementation.

**Proof, privacy, and risk.** It would need to show a distinct uncertainty not
already covered by adapter tests plus the two existing physical proofs. Current
evidence identifies no such uncertainty. Repeating the proof only to combine
two completed claims has operator cost and privacy exposure without changing an
architectural conclusion.

**Recommendation.** No retained proof is currently justified.

### D. Multi-remote capability discrimination

**Observed problem or missing evidence.** Controlled tests demonstrate
capability-only eligibility and exclusion of chat-only candidates. Ordinary
declarations intentionally construct the same closed capability set for each
remote, so an operator cannot truthfully configure different remote capability
sets through accepted surfaces.

**Existing accepted surfaces.** Ordered static remote declarations, local-first
selection, and bounded pre-transmission fallback are accepted. The Phase 18
runbook correctly leaves chat-only discrimination to controlled tests rather
than manufacturing topology data.

**Smallest credible change and contract assessment.** A real physical
multi-remote discrimination proof is not available through ordinary declarations
unless existing behavior changes. Adding capability fields to declarations,
dynamic observation, or a special proof topology would change durable
configuration or capability authority and require an RFC.

**Proof, privacy, and risk.** The controlled tests are the appropriate evidence
for the presently unconfigurable distinction. A physical proof would otherwise
misrepresent static declarations or broaden operator data. The risk is
converting a sound test seam into a configuration feature for symmetry.

**Recommendation.** Keep the controlled evidence; no new proof or contract is
justified.

### E. User-facing workflow beyond raw bounded text

**Observed problem or missing evidence.** Documents, files, longer text,
chunking, RAG, embeddings, sessions, streaming, tool calling, and workflow
composition are possible future ideas. No retained operator need identifies one
as the smallest missing workflow after bounded text summarize.

**Existing accepted surfaces.** RFC-0051 deliberately bounds summarize to one
non-empty text value, one plain-text result, no files, no sessions, no streaming,
and no generic capability framework. Current native and remote execution prove
that limited contract.

**Smallest credible change and contract assessment.** Each possible direction
would first need a user-named problem and a separate investigation. File or
document input, chunking, retrieval, embeddings, and workflow composition
cannot be bundled: they create distinct content, retention, request, transport,
storage, and adapter questions. Any selected durable contract would need an RFC.

**Proof, privacy, and risk.** These inputs can carry substantially more private
content and may invite persistence, model selection, or generic orchestration.
Building a workflow framework before one concrete need would directly conflict
with the project's small, boring increment rule.

**Recommendation.** Reject bundled workflow expansion; collect a concrete need
before investigating any one item.

### F. Stop and collect evidence

**Observed problem or missing evidence.** The current repository proves the
founding multi-machine abstraction, ordinary remote execution, bounded external
tool access, two capabilities, and real remote summarize. Recent post-roadmap
and operator-workflow investigations did not establish a concrete remaining
need for automation, another tool proof, lifecycle ownership, or onboarding
machinery.

**Existing accepted surfaces.** The canonical workflow, finite preflight,
health, status, explicit startup commands, direct native endpoints, one-shot
chat access, and retained proofs already give a technical operator bounded ways
to prepare, observe, and use the cluster.

**Smallest credible change and contract assessment.** No immediate
implementation or architectural repository change is the smallest responsible
response. The next useful input is external evidence from one real operator
workflow. That evidence may later justify a repository investigation, RFC,
refinement, or proof. An eventual documentation refinement may need no RFC; any
change to capabilities, input, configuration, lifecycle, routing, or trust
authority would need an investigation and, if architectural, an RFC.

**Proof, privacy, and risk.** Evidence collection should retain only the
problem category and existing-surface failure, never request content, generated
content, private topology, credentials, or runtime logs. Continuing repository
work without this evidence risks feature-driven architecture.

**Recommendation.** This is the strongest current outcome.

## Comparison

| Candidate | Concrete evidence | User value | Architectural impact | RFC required | Proof cost | Overengineering risk | Outcome |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A. One-shot summarize access | No retained need beyond direct HTTP; chat client is intentionally chat-only. | Unknown until an operator names a workflow. | New ordinary input and CLI contract. | Yes before implementation. | A distinct operator workflow and privacy-safe proof. | Medium: input, files, and history scope creep. | Defer. |
| B. Static capability truth | One factory drift, corrected in PR #337 with tests and proof preflight. | Already restored truthful eligibility. | None for the completed correction. | Only for TOML, probing, or exchange changes. | Already met for the defect. | High if topology becomes capability configuration. | No change. |
| C. Heterogeneous summarize | Adapter tests plus separate heterogeneous chat and remote summarize proofs. | No distinct unmet user value. | None for a proof-only rerun. | No for a proof; yes for contract changes. | Two-machine operator exercise. | Medium: repetition mistaken for new evidence. | No proof now. |
| D. Multi-remote discrimination | Controlled chat-only exclusion; ordinary declarations share one capability set. | Existing correctness is tested. | New physical distinction needs new authority. | Yes for declaration or observation changes. | Not truthfully available through ordinary surfaces. | High: configuration-by-symmetry. | Keep controlled tests. |
| E. Files, RAG, workflows, and related ideas | No concrete operator need. | Potential but unbounded. | New input, storage, transport, or execution semantics. | Yes. | Large and capability-specific. | Very high: generic framework. | Reject bundled expansion. |
| F. Collect evidence | Completed proofs did not establish a concrete remaining first-user need. | Avoids accidental authority and preserves focus. | None. | No. | One future privacy-safe operator report. | Lowest. | Collect evidence before selecting the next increment. |

## Decision boundary

No candidate above turns a missing symmetry into a requirement. A future
operator report should state the current surface attempted, the concrete task it
could not complete, and the privacy-safe category of the missing behavior. That
evidence can then be classified as a documentation gap, a bounded refinement,
a proof gap, or an architectural question. The project must not infer discovery,
dynamic capability exchange, scheduling, retries, lifecycle management,
configuration expansion, broader network trust, model management, generic
workflows, or a future roadmap phase from this investigation.

## Project maturity and remaining direction

This conclusion does not mean that Home AI Cluster is complete.

The repository has established a credible architectural and operational
foundation, but many product and system directions remain unexplored. These may
include broader operator workflows, additional capabilities, stronger
trusted-network boundaries, richer content inputs, model and runtime operation,
and other later possibilities already identified by the roadmap.

The investigation concludes only that the repository does not yet contain
enough concrete evidence to select one of those directions as the next bounded
increment.

The next stage is therefore problem discovery and qualification, not project
closure.

## Primary recommendation

No specific repository increment is currently justified by retained evidence.
The project is not complete; identify and investigate one concrete operator
need before selecting further implementation work.
