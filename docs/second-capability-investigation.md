# Second Capability Investigation

## 1. Status and authority

Investigation only. This document establishes no accepted capability, changes no
RFC or roadmap, creates no Phase 18, and authorizes no implementation. It may
recommend no change.

Question: which one additional capability, if any, is the smallest credible
proof that Home AI Cluster is capability-centered rather than a distributed
`chat`-only system?

## 2. Current capability reality

`Capability(name: str)` is a model-independent value. `ClusterRequest` names
one capability; `NodeDescription` declares a non-empty capability list; and
`RuntimeAdapter.capabilities()` returns capabilities. `NodeRegistry`,
`route_request`, routing candidates, declared-remote candidates, ordered
fallback, and routing explanations compare requested capability names without a
hard-coded `chat` branch. Router tests already use `code` and `summarization`
names to prove filtering and mismatch behavior. Remote declarations also carry
declared capabilities, and remote result attribution remains cluster-owned.

That is genuine architectural support for multiple capability names and
eligibility-based selection. It is not yet proof of a second executable
capability. `ClusterRequest` is documented as a normalized *chat* request and
requires non-empty `messages: list[ChatMessage]`. Both adapters expose only
`chat(request)`, advertise only `chat`, construct chat-completions payloads,
and normalize textual chat responses. The native public route is `/v1/chat`,
its public `ChatRequest` is message-shaped, the one-shot client fixes `chat`,
and the narrow compatibility edge is explicitly chat-only. `ClusterResult` is
textual and attribution-neutral enough for another textual result, but current
proofs validate it only for chat.

Thus the generic path is capability declaration, eligibility, candidate
selection, declared-remote execution, normalized result validation, and node
attribution. The chat-specific path is normalized input, endpoint naming,
adapter execution method, runtime request/response mapping, public failures,
and every real runtime proof.

## 3. Why a second capability matters

A credible second-capability proof would show that the existing capability
model changes eligibility rather than merely labelling chat prompts. It should
show nodes with different declarations, rejection when no node is eligible,
selection of an eligible local or declared remote node, normalized textual
result and node attribution, and no engine-specific request field. It would
also test whether the adapter boundary and internal remote execution can accept
more than one request meaning without changing routing order or authority.

It would not be enough to add another capability string, use a chat prompt that
asks for a task, or select a different model. The proof value comes from a
distinct normalized request contract and execution path whose selection depends
on declared support. One native orchestration entry may remain sufficient, but
the public `/v1/chat` name cannot honestly own a non-chat request without a
separate decision.

## 4. First-user problems and evidence

| Evidence class | Current evidence | Consequence |
| --- | --- | --- |
| Explicit user need | The first user identified a second capability as an important missing piece. | A bounded second-capability decision is justified. |
| Explicit later direction | The user also wants document upload and analysis later. | It supports text-analysis value, not a selected upload contract. |
| Architectural proof value | Current routing already has generic capability filtering but only chat execution proof. | A semantically distinct textual capability would exercise the seam. |
| Missing workflow detail | No document format, size, extraction, retention, filename, metadata, interaction, or permission contract exists. | Document upload is not ready to implement or define as one capability. |
| Speculation | RAG, PDF support, OCR, indexing, embeddings, and persistent document libraries. | Exclude from this decision. |

## 5. Candidate capabilities

### A — No change

Keeps the proven chat system small and avoids request-model work. It does not
answer the explicit first-user direction or prove that the generic routing seam
supports another real execution meaning.

### B — Summarization

A text-only request can ask for a concise representation of supplied text and
return plain text. It is distinct from conversational exchange when its source
text is a first-class normalized input rather than a prompt convention. It has
direct value for reading local text and can later compose with a deliberately
separate document-text boundary. Its first form can exclude files, extraction,
persistence, sessions, and style/length controls.

### C — Document analysis

Potentially valuable, but currently bundles content ingestion, file transport,
binary parsing, extraction, questions, metadata, privacy, size, temporary
storage, and possibly retention. It is several decisions, not one proven
capability, and should not be the first increment.

### D — Text transformation

Rewrite, translation, classification, and fact extraction are either a broad
family or prompt conventions unless each receives a precise request/result
meaning. Selecting one arbitrarily has less connection to the stated document
direction than summarization.

### E — Embeddings

Would be semantically distinct, but introduces vector dimensions, normalization,
model comparability, binary/numeric result contracts, storage pressure, and a
strong pull toward retrieval infrastructure. It is not a small textual proof.

### F — Vision

Exercises capability selection but needs image/binary transport, MIME and size
rules, multimodal model availability, parsing and privacy boundaries, and a
new result/support intersection. It prematurely solves multimodal transport.

### G — Code-oriented capability

`code` is a useful router test name but has no distinct normalized behavior or
first-user workflow. Without a separate contract it is a model preference under
chat, not a capability.

### H — Tool execution

Requires side-effect authority, permissions, sandboxing, audit boundaries, and
lifecycle choices. It is outside the local orchestration increment.

## 6. Candidate comparison

Qualitative ratings use current repository evidence, not feature appeal.

| Candidate | User value / proof value | Distinct from chat | Contract and adapter cost | Privacy / dependency pull | Small increment? |
| --- | --- | --- | --- | --- | --- |
| No change | Preserves proven scope / none | n/a | None | Lowest | Yes, but leaves stated need open |
| Summarization | Direct / high | High if text is first-class | Moderate; textual request and adapter method | Moderate; no new dependency required | Yes |
| Document analysis | Potentially high / mixed | High | High; bundles ingestion and extraction | High; files, metadata, temporary storage | No |
| Text transformation | Variable / medium | Often unclear | Moderate to broad | Low to moderate | Not without choosing one exact meaning |
| Embeddings | Indirect / high | High | High; numeric/vector contract | High; persistence pressure | No |
| Vision | Unspecified / high | High | High; binary/multimodal | High | No |
| Code | Unspecified / low | Low today | Low only by remaining chat-shaped | Low | No |
| Tool execution | Unspecified / low | High | Very high | Very high; side effects | No |

Summarization has the best supported balance: plain-text input/output is within
the two current text-generation runtime families, deterministic unit seams can
test capability eligibility and adapter mapping, it adds no dependency, and it
does not require persistence or multimodal transport. This is a plausible
assessment, not proof that both current adapters already support an accepted
summarization contract.

## 7. Summarization boundary

The smallest candidate is conceptually:

```text
capability: summarize
input: text: string
result: content: string
```

This is a real capability only if `text` is normalized source material with
summarization semantics—not a user chat message plus an undocumented system
prompt. The existing message list cannot represent that distinction truthfully
without overloading role/content semantics. A future RFC must decide non-empty
input, a deliberate bounded input-size policy, plain-text output, and safe
invalid-input and unsupported-capability behavior. It should not add length or
style selectors until evidence requires them.

`ClusterResult.content`, `adapter`, `model`, and `node_id` appear sufficient
for one textual summary; attribution stays unchanged. No capability field or
tagged result union is justified unless a result becomes ambiguous. Streaming,
files, system-prompt libraries, and hidden adapter policy remain excluded.

## 8. Document-analysis relationship

Text summarization could prepare a future document workflow, but it does not
decide one. A possible later sequence is normalized text summarization, then a
separate local text-file reading decision, then bounded document-text analysis,
then possibly PDF extraction. That sequence is not selected here.

Capability semantics, local file reading, file transport, binary upload, text
extraction, OCR, retention, indexing, and conversation over documents have
different privacy and authority boundaries. Starting with upload would bundle
them and conceal which part provides value. Document upload is therefore out of
scope for a second textual capability.

## 9. Request model and endpoint implications

`ClusterRequest` is intrinsically chat-message shaped. A second capability
requires an architectural request decision: a tagged normalized request union,
capability-specific payload, a new envelope, or a separate internal request
type. Optional chat and text fields would be weak because valid combinations,
ownership, and errors become unclear; a generic payload map would anticipate a
capability framework before it is needed.

Externally, `/v1/chat` should remain chat-only. A capability-specific native
endpoint is the smallest truthful public option for one second capability;
one general native endpoint may be justified only if the RFC can define a
small, closed, tagged contract. Both can share one internal orchestration entry
after normalization. The current internal request endpoint is typed to
`ClusterRequest`, so remote parity also depends on the same request decision.
The narrow OpenAI-compatible edge must not expand.

## 10. Result model implications

For a textual summary, the current normalized result fields appear capability-
neutral enough: `content` carries text; adapter/model remain runtime attribution;
and `node_id` remains cluster attribution. Capability need not be repeated in a
successful result if the endpoint/request type determines it. Structured or
tagged result unions are premature until a capability needs non-text output.

## 11. Adapter implications

The current protocol has one `chat(ClusterRequest)` method, and both adapters
only advertise and execute `chat`. A second capability cannot be honestly
implemented by relabelling this method. A future RFC must decide a minimal
capability-specific execution boundary and where the semantic prompt/template
lives. Core-owned hidden prompts risk policy leakage; runtime-owned prompts
risk divergent semantics. That decision must preserve a common textual
contract across Ollama and llama-server and make support explicit per adapter.

No generic adapter plugin or many-capability abstraction is warranted. The
smallest decision may be one explicitly named textual execution method and
matching adapter declaration, if evidence shows the existing generic core
execution path can carry it without misleading types.

## 12. Routing implications

Routing already accepts nodes with different capability sets, excludes local
adapters that do not advertise the requested capability, finds eligible
declared remotes, preserves local-first ordering, and reports no selectable
candidate. A remote-only `summarize` capability should therefore need no new
routing policy or scheduler; it would prove existing filtering.

The missing work is request/execution typing, not smarter routing. Existing
fallback must remain bounded among eligible candidates and retain its current
pre-request failure rule. No hidden routing override or capability-specific
candidate order is justified.

## 13. Privacy implications

Supplied summary text is sensitive request content. RFC-0035 history must stay
prompt/content-free; summaries and sources must not enter it. The normal
cluster remote path may transmit normalized request content only to an explicitly
declared trusted-LAN node, as existing request behavior permits, with no new
logging, telemetry, temporary files, or retained configuration.

Text-only input avoids filename, MIME type, path, binary parser, extracted-text,
and temporary-file risks. Documents would add all of those risks plus metadata
leakage and retention/extraction questions. A future bounded size rule must be
privacy and resource conscious without becoming a document-storage policy.

## 14. Failure model implications

Existing no-match and runtime-unavailable behavior establishes useful shape,
but a text capability needs explicit local validation failures for malformed or
empty source text, plus a bounded oversized-input outcome if a limit is chosen.
Unsupported capability can reuse eligibility/no-match semantics after the new
request contract is normalized. Extraction failure and unsupported format are
document-specific failures and must not enter a text-only first capability.

## 15. Proof shape

A credible proof should use at least two nodes with different declarations,
one `summarize` request selected because of eligibility, truthful final node
attribution, and one unsupported-capability failure. It should exercise a local
or declared-remote path without engine-specific normalized fields or hidden
routing override. Two supported runtime compositions would strengthen the claim
if both implement the same accepted semantics.

Unit and integration evidence should precede another two-machine proof: first
prove request validation, adapter mapping, generic eligibility, normalized
result validation, and remote transport parity. A real two-machine proof is
then warranted only after the textual contract is accepted and both sides have
the required bounded runtime support.

## 16. Architecture and RFC assessment

Summarization requires an RFC. Its cohesive boundary is one textual capability,
normalized request shape, native endpoint decision, minimal adapter execution
boundary, textual result reuse, capability eligibility, and bounded failures.
Document ingestion is a separate decision and must not be bundled. If request
normalization cannot stay closed and small, stop and investigate that boundary
before selecting a capability implementation.

## 17. Phase classification

This is not automatically Phase 18. A standalone post-roadmap RFC and bounded
implementation are appropriate if it composes existing routing and transport
without broader protocol or ingestion authority. A formal phase becomes
justified only if the accepted work must jointly redefine the public request
model, remote protocol, adapter contract, proof obligations, and a durable
multi-capability direction beyond one small textual increment.

## 18. Recommendation

Draft one narrow RFC for **bounded text summarization**. Its intended scope is
one new textual capability; normalized source text; plain textual result;
explicit capability-based routing; and no file reading, upload, PDF, OCR,
persistence, session, embeddings, streaming, tools, scheduler, or generic
capability framework.

Stopping condition: stop the RFC and do not implement if a closed truthful
request/endpoint/adapter boundary cannot be defined without a general request
framework or document-ingestion authority. In that case, perform one narrower
request-model investigation instead.

## 19. Boundaries retained

Excluded: document upload, PDF parsing, OCR, binary transport, RAG, embeddings,
vector stores, databases, sessions, streaming, tool execution, multimodal
support, prompt libraries, discovery, scheduling, lifecycle management, model
downloads, dashboards, Docker, Kubernetes, generic capability plugins, and
broad OpenAI-compatible expansion.

## 20. Files inspected

- Governing documents: `VISION.md`, `FOUNDATIONS.md`, `PRINCIPLES.md`,
  `NON_GOALS.md`, `ROADMAP.md`, `QUESTIONS.md`, `CONTRIBUTING.md`, `AGENTS.md`,
  `RFC/README.md`, and `README.md`.
- Accepted RFCs governing capabilities, normalization, routing, adapters,
  remote execution, failures, observation, runtime composition, ordinary
  operator access, and RFC-0050: RFC-0003–0007, RFC-0009–0010, RFC-0012–0018,
  RFC-0020, RFC-0023, RFC-0025, RFC-0027–0028, RFC-0030–0035,
  RFC-0038–0040, RFC-0042–0046, RFC-0048–0050.
- Investigations and retained evidence: post-roadmap direction and unified
  command investigations; native end-to-end remote-request proof and runbook;
  Phase 12 heterogeneous runtime investigation/proof; Aider static-cluster
  proof/runbook; and real-tool routing investigation.
- Implementation: `core/models.py`, `node.py`, `router.py`,
  `routing_candidates.py`, `orchestrator.py`, `executor.py`, and
  `remote_transport.py`; `adapters/base.py`, `ollama.py`, and
  `llama_server.py`; API routes/wiring; ordinary local, static-cluster,
  compatibility, chat, status, health, and preflight command modules.
- Focused tests: models, router, routing candidates, orchestrator, executor,
  remote transport, Ollama, llama-server, API routes/wiring, static cluster,
  runtime composition, and ordinary command tests.
