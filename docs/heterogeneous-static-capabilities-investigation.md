# Heterogeneous Static Capabilities Investigation

Status: Complete

## Context

The accepted ordinary static-cluster shape is one fixed local node plus one or more explicitly declared remote nodes. It is operator-owned, loaded once at startup, local-first, and deterministic. This investigation considers only whether that existing shape can declare different bounded capabilities on different nodes. It does not introduce scheduling, runtime probing, discovery, or a new capability.

The two currently executable ordinary capabilities are `chat` and `summarize`. RFC-0051 made the latter routing-visible and explicitly called for a later proof with a chat-only node and a summarize-capable node. That proof claim must be distinguished from the current ordinary declaration contract.

## Investigation question

Can the current ordinary static-cluster path represent and prove a topology in which, for example, local and remote A offer `chat`, while remote B offers only `summarize`?

No. The routing and node models can consume such descriptions, but the ordinary local and remote construction paths always create both capabilities. The current TOML and inline declaration contracts contain no per-node capability data.

## Current accepted capability model

`Capability` is a cluster-facing value with a non-empty name. A `NodeDescription` owns a non-empty list of capabilities; this is distinct from adapter implementation and from node health.

For ordinary local startup, `local_runtime_composition._create_local_node()` constructs the fixed `local` node with `chat` and `summarize`, for both Ollama and llama-server compositions. This is ordinary composition behavior, not capability probing and not adapter-derived node metadata at startup.

For ordinary static remotes, `static_cluster.create_remote_declaration()` constructs every remote with the same two capabilities. This is hard-coded construction behavior after parsing the operator-owned remote identity and base URL. The remote declaration does not query the remote application, runtime, or adapter to obtain capabilities.

The core can represent a one-capability node: `NodeDescription` accepts a non-empty list, and focused tests and proof-scoped wiring construct such nodes directly. That is not an accepted ordinary operator declaration path. The ordinary constructors have no capability argument and therefore cannot build a chat-only or summarize-only ordinary static node.

## Current declaration behavior

The TOML contract accepts either the legacy flat single-remote form (`remote_node_id`, `remote_base_url`) or an ordered `[[remote_nodes]]` array whose entries contain exactly `node_id` and `base_url`. Unknown keys fail validation. Neither shape can carry capabilities.

The inline contract accepts exactly one remote with `--remote-node-id` and `--remote-base-url`; it likewise has no capability option. Both declaration sources converge on `create_remote_declaration()`, so both produce identical implicit `chat` plus `summarize` declarations. The TOML path is the only current source for multiple remotes; inline mode remains single-remote only.

Consequently every ordinary static node created today declares both capabilities: the fixed local node and every inline or TOML remote. This says what the cluster is allowed to consider, not what a live runtime has just demonstrated.

## Current routing eligibility

Capability filtering already exists. Local routing obtains only available nodes that declare the request capability, then requires a declared local adapter that also implements it. Declared remote candidate collection filters its ordered declarations by availability and `node.capabilities` before any selection occurs.

Automatic capability routing is therefore evaluated from already eligible candidates:

1. construct eligible local and declared-remote candidate sets;
2. select eligible local first;
3. when local has no eligible candidate and the request is not `local_only`, select the first eligible declared remote.

A local node that lacks the requested capability produces no local candidate; it does not block an eligible remote. If no declared local or remote node is eligible, the request has the existing structured no-selectable/no-capability failure path. A `local_only` request excludes otherwise eligible remotes and can fail for that separate constraint reason.

This is capability eligibility, not an assertion that a candidate is reachable or that its runtime can execute the request. Runtime availability remains an execution-time concern.

## Current target selection

With multiple eligible remotes, declaration order is the deterministic rule. The first eligible remote is the initial selected remote. If the eligible local candidate fails with the accepted pre-request connection-unavailable condition, or an eligible remote fails with that same condition, bounded traversal proceeds through eligible remotes in declaration order, at most once each, and stops at the first success. Other failures stop execution.

This is an accepted contract, not merely a coincidental implementation detail: RFC-0040 defines declaration order as the only remote priority rule and rejects sorting, randomization, load balancing, scoring, and scheduling. Capability filtering determines who may be considered; declaration order determines the existing deterministic order among eligible remotes.

## Preflight and status behavior

Static preflight is local, read-only, and network-free. It projects each constructed node's declared capability names and adapter labels, and checks only whether adapters for locally resolved nodes are registered. It neither validates capability names nor capability semantics, and it does not validate remote runtime support. With an eventual heterogeneous construction path, its existing projection would display the constructed capability lists; whether input capability values must be validated is a new declaration-contract choice.

The status command deliberately reports a different fact: declaration coherence, application reachability, and runtime observation. Its public node result has only `node_id`, `application_status`, and `runtime_status`. It does **not** expose declared capabilities today. Its output would remain valid but could not itself prove heterogeneous declarations. Adding capabilities to status would change the accepted RFC-0041 status result contract and needs an explicit decision.

## Can heterogeneous nodes be represented today?

At the core model and routing-candidate level, yes: a manually built `NodeDescription` with one non-empty capability is filtered correctly. At the ordinary static operator boundary, no:

| Boundary | Current behavior |
| --- | --- |
| Ordinary local composition | Hard-codes `chat`, `summarize` |
| Inline remote declaration | Has no capability input; construction hard-codes both |
| TOML remote declaration | Schema rejects capability fields; construction hard-codes both |
| Routing candidates | Filters arbitrary declared capability lists correctly |
| Preflight | Displays constructed lists but validates no capability vocabulary |
| Status | Does not expose capabilities |

Thus a proof using direct test/proof wiring can establish core eligibility, but it cannot prove that an operator can express and inspect a heterogeneous ordinary static topology using the accepted declaration interface.

## Smallest possible contract gap

The missing contract is explicit per-node capability data at the ordinary composition/declaration boundary. A bounded follow-up would need to decide how that data reaches both remote construction paths and, separately, whether and how the fixed local composition becomes explicit.

For TOML, the narrowest apparent surface is a per-remote field in each accepted remote entry. Inline mode would need a corresponding explicitly bounded syntax if it is to express it; it cannot do so today. The fixed local node has no topology-file entry, so remote-only schema work would not express the full example topology when local capabilities must differ.

These observations identify the gap only. They do not select a field name, syntax, capability vocabulary, local configuration surface, or ownership model.

## Backward-compatibility considerations

Existing ordinary use implicitly declares both `chat` and `summarize`. Keeping that result when a new explicit field is absent would preserve the currently verified inline and TOML behavior, but the meaning of absence is an architectural compatibility decision that must be recorded before implementation.

The following are likewise unmade contract choices:

* whether an explicit empty set is invalid, meaningful as a disabled node, or disallowed because `NodeDescription` currently requires at least one item;
* whether capability names use a closed accepted vocabulary or accept arbitrary non-empty names;
* whether duplicate names are rejected or normalized;
* whether declaration order inside a capability list is observable or semantically irrelevant; and
* whether any explicit declaration must agree with local adapter support, and where that validation belongs.

The present code preserves list order and does not enforce uniqueness or a closed capability vocabulary. That implementation fact is not a declaration contract for new operator input.

## What a bounded proof would establish

Once an accepted ordinary declaration and construction contract exists, a bounded proof could establish all of the following without claiming scheduling:

* a chat-only declared node is ineligible for `summarize`;
* a summarize-only declared node is ineligible for `chat`;
* local-first applies only after capability eligibility;
* preflight reports the declared heterogeneous construction accurately;
* a request with no eligible declared node fails through the existing structured no-capability path; and
* eligible remotes retain the existing declaration-order selection and bounded traversal behavior.

Current status output cannot establish a claim about heterogeneous capability declarations because it intentionally omits them. A proof may use preflight and request attribution without changing status, unless a future RFC explicitly expands status.

## Capability filtering versus scheduling

Filtering asks one bounded question: does an available, declared node advertise the requested capability? Existing local-first and declaration order then provide deterministic precedence among that filtered set. Runtime reachability and runtime availability are observed or encountered at separate execution and status boundaries.

None of this determines which node is fastest, strongest, least loaded, lowest cost, or otherwise optimal. It provides no probing, dynamic mutation, round-robin behavior, weighting, priority configuration, retries beyond the already accepted pre-request bounded traversal, or scheduler.

## RFC boundary

An RFC is required before implementation if a follow-up changes any of these accepted contracts:

* per-node capabilities in the static TOML or inline declaration schema;
* how ordinary local capabilities are supplied or who owns them;
* the implicit default capability set or the meaning of field absence;
* validation, duplicate handling, vocabulary, or ordering semantics for operator-declared capabilities;
* candidate eligibility, local-first behavior, remote declaration order, or bounded fallback traversal;
* structured no-capability or constraint failure semantics; or
* the preflight or status output contract.

No RFC is needed merely to recognize the existing gap or to document evidence. The implementation details of an already accepted contract could remain small, but this investigation does not supply that decision.

## Candidate follow-up categories

1. Decision framing for explicit static per-node capability ownership and backward compatibility.
2. If accepted, a narrowly scoped declaration/composition implementation with focused validation and routing evidence.
3. A retained ordinary static heterogeneous proof using only capability eligibility, local-first precedence, declared order, and existing structured failures.
4. A separate decision only if capability declarations must become part of the public status result.

## Conclusion

Outcome C — a bounded declaration or capability-ownership gap exists

Core node descriptions and routing already support capability eligibility, but
ordinary inline and TOML declarations cannot express distinct per-node capability
sets. Ordinary local and remote construction currently supplies the same implicit
`chat` and `summarize` capabilities. This prevents an ordinary operator-facing
heterogeneous proof.

The gap requires an RFC before implementation because it affects declaration and
capability-ownership contracts. This investigation does not select a schema,
compatibility rule, validation policy, local capability configuration surface,
status expansion, or implementation plan.

The smallest future RFC question is:

> Can an explicit static node declaration define a bounded set of supported
> capabilities while preserving deterministic local-first routing and backward
> compatibility?

Fixed local-node capability ownership may need separate treatment if the intended
topology also requires heterogeneous local capabilities.
