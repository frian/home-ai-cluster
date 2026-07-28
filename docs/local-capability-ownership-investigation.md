# Local Capability Ownership Investigation

Status: Complete

## Context

RFC-0058 makes the accepted remote capability declaration surface explicit:
ordinary static remotes may be declared as `chat`-only, `summarize`-only, or
both. The retained heterogeneous proof established that those caller-owned
declarations filter remote eligibility without changing local-first routing.

The proof also exposed a remaining ordinary limitation. The fixed local node
continues to declare both executable capabilities, so a healthy local candidate
is eligible before a declared remote for either request. Remote specialization
therefore currently needs the accepted pre-request local-unavailability path.

## Investigation question

Should an operator be able to restrict the fixed ordinary local node's declared
routing capabilities, for example to local `chat` plus remote `summarize`, so a
healthy local node is excluded for summarize by existing eligibility rules?

This investigation records the contract gap and candidate decision shapes. It
does not select a configuration surface, change routing, or define receiver
behavior.

## Current ordinary local capability model

RFC-0009 makes the local node announcement an in-process, cluster-facing manual
declaration, separate from runtime probing and adapter-owned metadata.
RFC-0042 and RFC-0043 later made the ordinary local runtime composition
explicit for both `hac local` and `hac static-cluster`.

Current implementation behavior is narrower than a configurable contract:

- `local_runtime_composition._create_local_node()` builds the fixed `local`
  description with `chat` and `summarize` for both Ollama and llama-server.
- Each concrete composition creates its adapter, then builds the node
  description from the adapter name and places both in their registries.
- The local capability list is hard-coded composition data; it is neither
  derived from adapter `capabilities()`, runtime health, runtime inventory, nor
  an ordinary operator option.
- Both current adapters independently implement and advertise `chat` and
  `summarize`. That implementation fact is distinct from the cluster-visible
  local declaration.

Core models and focused tests can construct a one-capability `NodeDescription`,
but no accepted ordinary public surface supplies such a set for the fixed local
node. Local capability ownership is an accepted declaration boundary with fixed
current composition behavior, not an adapter-discovery contract.

## Current routing consequences

Candidate discovery first filters nodes by declared availability and requested
capability. Local routing additionally requires a matching named local adapter
that implements that capability. Only then does automatic selection apply fixed
local-first precedence; it does not make an ineligible local node win.

Consequently, a local node that lacked `summarize` would produce no local
candidate for a summarize request. In static-cluster mode, an eligible declared
remote would then be selected through the existing declaration-backed remote
candidate path and existing remote order. No local runtime failure, selector, or
scheduler is needed for that outcome.

Today the local declaration contains both capabilities, so a healthy local
candidate wins for both chat and summarize. If no local or declared remote node
matches, the existing no-selectable/no-capability failure path applies. If a
local node is eligible but its runtime fails, that remains an execution-time
runtime-unavailable outcome; eligibility does not assert reachability or health.

These are accepted routing and failure boundaries. They are capability
eligibility, not preferred-node selection, optimization, or scheduling.

## Current operator surfaces

`hac local` and `hac static-cluster` share the closed local runtime-composition
arguments: runtime selection and the two llama-server values when applicable.
Neither accepts local capability input. `hac static-cluster` additionally owns
remote topology input; RFC-0058's remote capability options and TOML fields
apply only to caller-owned remote declarations.

Static preflight is separate. Its command accepts local-only or remote
declaration input, but constructs its ordinary local registry through the older
static factory rather than runtime-composition arguments. It projects its
constructed local capability list without runtime or network observation. A
future local-capability surface would therefore need an explicit decision about
how preflight receives the same declaration.

The static declaration file currently owns remote topology, not local
composition. Inline static mode likewise owns exactly one remote declaration.
Adding local data to either would change that separation; a static-cluster-only
option would instead create a different ordinary local contract from `hac local`.
Neither consequence is selected here.

## Capability declaration versus adapter implementation

| Concept | Current source and meaning |
| --- | --- |
| Local capability declaration | Fixed composition-owned node metadata that controls router eligibility. |
| Adapter implementation | Ollama and llama-server each expose executable operations through their adapter interface. |
| Runtime health/reachability | A call-time or explicit observation fact, not declaration data. |
| Local-first | Fixed precedence only among already eligible candidates. |
| Remote declaration | Caller-owned permission to consider a remote; it is not receiver runtime verification. |

Restricting a local declaration would therefore mean the capabilities the local
router is allowed to consider, not disabling an adapter, declaring a runtime
unhealthy, discovering a capability, or choosing a preferred remote. Whether it
also changes which capabilities an ordinary receiving application executes is a
separate contract question.

## Receiver implications

An ordinary `hac local` process can receive internal requests from a caller.
Its inbound handler resolves its local composition and routes the normalized
request through that local node description and adapter registry. Under current
implementation behavior, a restricted receiver-local declaration would affect
its inbound eligibility even while the adapter still implements both operations.

Caller-owned remote declarations remain the caller's eligibility authority.
RFC-0058 explicitly says they are not runtime discovery or verification. If a
future local restriction makes the receiver reject a capability that the caller
declares for it, that is a cross-process mismatch and failure-boundary question;
the current contract does not negotiate or validate it.

Caller-local eligibility is separate from receiver execution. A caller-only
restriction and a uniform declaration shared by caller and receiver are
different potential decisions.

## Preflight and status implications

Preflight already projects declared capability lists and remains read-only and
network-free. It could represent a restricted local list only after an accepted
construction and input contract supplies one. Its current static factory and
adapter-resolution rule do not themselves authorize local capability
configuration or vocabulary validation.

Status has a different accepted purpose: declaration coherence, application
reachability, and runtime observation. Its public result contains node ID plus
application and runtime status, not capability lists. The schema can remain
valid when local eligibility changes, but it cannot prove that declaration.
Adding capability data to status would require a separate decision.

## Compatibility considerations

The compatibility baseline is fixed ordinary local declaration of:

```text
chat + summarize
```

An eventual contract would need to decide, rather than infer:

- whether omission preserves that set for every ordinary command;
- whether the non-empty `NodeDescription` invariant forbids an explicit empty
  set or whether any different meaning is intended;
- whether the RFC-0058 closed vocabulary, duplicate rejection, and
  order-without-priority rules also apply locally;
- whether a restriction changes only caller-local eligibility or all ordinary
  local application roles; and
- how existing endpoints behave when the adapter implements a capability the
  local node does not declare.

Current endpoint routes remain present for chat and summarize, but their local
execution path uses the local node declaration. This is implementation evidence,
not an accepted decision about future local restrictions.

## Candidate bounded shapes

The following are decision candidates, not selected proposals.

### Runtime-composition option

Repeatable local capability input could be applied wherever an ordinary local
runtime composition is built. It might align `hac local` and
`hac static-cluster`, but raises whether preflight and status must accept the
same input and whether receiver-side execution follows the declaration.

### Static-cluster-only local restriction

Restricting only the caller's fixed local candidate is the smallest apparent
way to demonstrate healthy-local chat plus remote summarize. It risks two
ordinary meanings for the same local node and leaves the receiver role and
local-only process unresolved.

### Local entry in the static declaration

A bounded local section could put caller-local eligibility beside remote
topology. It may make one static-cluster construction explicit, but it changes
the current remote-only declaration contract and risks a more general topology
schema. A local ID or endpoint would be unnecessary and misleading.

### No local configurability

Keeping the fixed local declaration broad preserves today’s simple contract. It
also confines healthy-operation remote specialization to a future accepted local
capability change or to the existing fallback condition.

## What a later proof could establish

With an accepted local ownership contract, an ordinary proof could show healthy
local chat plus remote-only summarize:

- chat executes locally;
- summarize excludes the healthy local node by declared eligibility and reaches
  an eligible declared remote without a local failure;
- local-first still applies among eligible candidates;
- no direct selector or scheduler is involved; and
- preflight projects the restricted local set without network activity.

It could use existing structured failure behavior when neither local nor remote
declares a request capability. It could not claim receiver behavior, remote
capability verification, status capability reporting, or cross-node agreement
unless a future contract covers them.

## Architectural boundary

An RFC is required before implementation because this work would decide:

- local capability declaration ownership and operator authority;
- a local configuration surface for `hac local`, `hac static-cluster`,
  preflight, or a declaration file;
- consistency or intentional differences between caller and receiver roles;
- compatibility defaults, vocabulary, duplicates, emptiness, and ordering;
- whether inbound local execution follows a restricted declaration;
- public endpoint and structured failure expectations; and
- any preflight input or status contract change.

The existing router already supports exclusion-before-local-first behavior, so
none of these choices requires a router policy change. Caller-owned remote
eligibility must remain separate from receiver-local execution behavior.

## Candidate follow-up categories

1. An RFC limited to fixed local capability ownership, bounded validation, and
   compatibility.
2. If accepted, a small composition and operator-surface implementation with
   preflight treatment explicitly scoped by that decision.
3. A retained ordinary proof of healthy-local chat and remote-only summarize.
4. A separate RFC only if status capability exposure or receiver/caller
   agreement needs to become a public contract.

## Conclusion

Outcome C — an explicit local capability ownership contract is required

Ordinary local capabilities are fixed by composition and no accepted
operator-facing path can restrict local capability eligibility. The smallest
future question is:

> Can an ordinary process explicitly restrict the fixed local node's bounded
> routing capabilities while preserving local-first routing, existing receiver
> behavior, and backward compatibility?

The narrowest likely decision scope is declaration ownership, one bounded
operator input surface or consistently shared construction surface, validation
and compatibility, preflight treatment, and the separation between
caller-local eligibility and receiver execution. This investigation does not
select CLI or TOML syntax, decide endpoint behavior, or authorize an RFC or
implementation.
