# Aider Static-Cluster Access Investigation

Status: Complete

## Question

Can the already-supported Aider compatibility setup be composed unchanged with
the ordinary explicit static-cluster compatibility mode, so that one real Aider
request is routed to a declared remote node and returned successfully to Aider?

This is an evidence review only. It does not authorize an implementation,
contract change, new proof execution, or RFC.

## Scope and preserved boundary

The reviewed composition is limited to the already accepted path:

```text
Aider
  -> loopback Home AI Cluster OpenAI-compatible endpoint
  -> existing cluster-owned chat request
  -> ordinary static capability routing
  -> declared remote node
  -> existing remote execution path
  -> normalized result
  -> existing compatibility projection
  -> Aider
```

It does not add a capability; a request-level node, runtime, adapter, or model
selector; OpenAI-compatible response fields; broader OpenAI compatibility;
streaming; tool calling; model discovery; persistence; prompt or response
logging; an observation framework; a compatibility process; network exposure;
remote lifecycle management; discovery; scheduling; web retrieval; a dashboard;
or Docker or Kubernetes.

The rejected RFC-0064 material was reviewed only to preserve its conclusion:
no project-owned URL retrieval, network authority, dependency, or browser
change is authorized. This investigation performs no web retrieval.

## Evidence inspected

| Evidence | Established fact |
| --- | --- |
| [RFC-0031](../RFC/RFC-0031-minimal-openai-compatible-chat-access.md) | The loopback-only, non-streaming compatibility edge translates the strict request into the existing cluster-owned `chat` request and projects its normalized result without exposing routing attribution. |
| [RFC-0038](../RFC/RFC-0038-ordinary-static-multi-node-mode.md), [RFC-0039](../RFC/RFC-0039-repeatable-static-cluster-declaration.md), and [RFC-0040](../RFC/RFC-0040-multiple-explicit-static-remote-nodes.md) | An operator-owned declaration constructs ordinary static local-plus-declared-remote routing; eligibility is capability-based, local-first applies among eligible candidates, and declared remote order is deterministic. |
| [RFC-0028](../RFC/RFC-0028-minimal-pre-execution-candidate-fallback.md) | An eligible local candidate may advance once to an already-declared remote only when the local runtime connection is known to have failed before request transmission; no retry, reselection, or broader fallback is implied. |
| [RFC-0023](../RFC/RFC-0023-result-node-attribution.md) and the accepted remote transport RFCs | After remote execution, the caller owns the final normalized attribution using the declaration node ID; a transport address is not node identity. |
| [RFC-0046](../RFC/RFC-0046-explicit-static-cluster-compatibility-access.md) | `hac compatibility --declaration <path>` (the installed form of `home-ai-cluster-openai-compatibility`) is the existing compatibility edge over the unchanged ordinary explicit static-cluster composition. The declaration is a startup-only topology input, not a request selector. |
| [RFC-0047](../RFC/RFC-0047-bounded-compatibility-proof-observation.md) | The optional declaration-only `--proof-observation` flag emits one content-free final stderr line containing the accepted request count, outcome, and final caller-owned result node ID. The HTTP response remains topology-blind. |
| [Phase 6 developer-tool investigation](phase-6-developer-tool-access-investigation.md) and [Aider access proof](phase-6-aider-access-proof.md) | Aider's non-streaming, plain-text `openai/home-ai-cluster` configuration can use the fixed loopback endpoint with temporary client-side settings that suppress unsupported streaming and `temperature`. |
| [Aider static-cluster proof runbook](aider-static-cluster-proof-runbook.md) and [retained proof](aider-static-cluster-proof.md) | The exact composition was run once on two trusted-LAN machines: one Aider request reached the declaration-backed compatibility process, the caller-local runtime was unavailable before execution, the declared receiver executed the request, the final observation named the declared node, and Aider received an unchanged successful response. |
| [Current compatibility process](../src/home_ai_cluster/openai_compatibility.py) and [static-cluster construction](../src/home_ai_cluster/static_cluster.py) | The executable composition still loads the declaration before binding, passes its remote collection to the ordinary static-cluster application constructor, adds the existing compatibility router, and retains loopback binding. |
| [RFC-0064](../RFC/RFC-0064-bounded-public-url-summarization.md) and [its HTTP-client investigation](rfc-0064-http-client-boundaries-investigation.md) | The rejected retrieval proposal authorizes no web access or related expansion; it is unrelated to and does not reopen this local trusted-LAN composition. |

## Inference from the evidence

1. Supplying `--declaration` to the compatibility command selects the existing
   ordinary static-cluster application construction. The compatibility route
   remains a public-edge translator; it neither selects a node nor performs
   remote execution itself.
2. A declared remote can be the truthful final candidate without a selector.
   In the retained bounded proof, local-first initially selected the eligible
   caller-local `chat` candidate, its runtime was unavailable before request
   transmission, and the accepted one-time fallback reached the already
   eligible declared remote. This is existing failure behavior, not a new
   preference or scheduling rule.
3. Aider cannot and must not observe node attribution in its RFC-0031 response.
   RFC-0047 is sufficient for the proof because it observes the same final
   caller-owned `ClusterResult.node_id` before compatibility projection, emits
   no prompt or response content, and adds no HTTP contract field.
4. No Home AI Cluster code, dependency, contract, topology, routing, privacy
   boundary, or Aider-support change is required. The retained proof already
   demonstrates the requested end-to-end behavior using the existing accepted
   Aider client-side configuration and the existing compatibility command.

## Outcome

**Outcome A — the end-to-end Aider static-cluster remote proof can be performed
unchanged with existing accepted behavior.**

This is stronger than a proposed follow-up: the repository already retains the
completed bounded proof. Therefore no additional proof PR is recommended. If a
future execution is needed for a materially different Aider version or mode, it
must first remain within the same strict client-side configuration and proof
boundaries; it must not broaden Home AI Cluster to accommodate a client change.

No RFC or implementation is recommended.
