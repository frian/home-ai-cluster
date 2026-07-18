# End-to-End Ordinary Remote Request Proof

Status: Retained

## Purpose

This record retains privacy-safe evidence of one successful real two-physical-
machine ordinary request. It composes the already accepted Phase 12 remote-
execution path with the Phase 16 one-shot client; it does not claim that every
internal boundary was first proven here.

The observed operator-facing path was:

```text
home-ai-cluster-chat
  -> caller loopback POST /v1/chat
  -> ordinary static-cluster routing
  -> accepted caller-local pre-request unavailability
  -> bounded fallback
  -> explicitly declared remote
  -> trusted-LAN HTTP transport
  -> ordinary receiving Home AI Cluster process
  -> receiving Ollama runtime adapter
  -> normalized ClusterResult
  -> caller-owned declared remote node_id
  -> one-shot client validation and output
```

See [the investigation](phase-17-end-to-end-ordinary-remote-request-investigation.md),
[the proof runbook](end-to-end-ordinary-remote-request-proof-runbook.md),
[the Phase 12 proof](phase-12-heterogeneous-runtime-cluster-proof.md), and
[the Phase 16 proof](phase-16-ordinary-request-access-proof.md).

## Repository revision

Both physical machines used:

```text
99ef65dcc16fb81cc208fcf6a68f957e7b64a8b0
```

Both working trees were clean.

## Date

The proof was executed on:

```text
2026-07-18
```

## Topology

The proof used exactly two distinct physical machines on one trusted LAN.

The calling machine ran:

- the installed `home-ai-cluster-chat` client;
- an ordinary `home-ai-cluster-static-cluster` caller;
- the default Ollama-backed local composition, with its local Ollama endpoint
  unavailable before the request; and
- one explicit remote declaration.

The receiving machine ran:

- an operator-managed Ollama runtime with `llama3.2:1b` available locally; and
- an ordinary `home-ai-cluster-local` process exposed only for the trusted-LAN
  proof boundary.

The caller declared exactly one remote node with the sanitized cluster-owned ID:

```text
ordinary-remote-proof
```

The declaration contained topology only. Its real path and URL are not retained.

## Preconditions and observations

Before the ordinary request:

- the receiving local runtime status was `available`;
- caller declaration preflight was `coherent`;
- caller local runtime status was `unavailable`;
- the declared remote application status was `reachable`; and
- the declared remote runtime status was `available`.

The caller local unavailability existed before request transmission. It was not
created after the request began.

## Ordinary request

Exactly one ordinary client invocation was executed:

```sh
uv run home-ai-cluster-chat --message "<REDACTED_TEST_MESSAGE>"
```

No retry occurred, and no direct request to the receiver substituted for the
client. The invocation had no node, runtime, adapter, model, host, port,
declaration, capability, retry, or topology option.

The observed process result was:

```text
client invocation count: 1
client exit status: 0
client standard error: empty
client standard output: exactly one compact JSON object
```

## Normalized result

The client emitted this sanitized complete normalized result:

```json
{"content":"<REDACTED_GENERATED_CONTENT>","adapter":"ollama","model":"llama3.2","node_id":"ordinary-remote-proof"}
```

The final `node_id` is the caller-owned declared remote ID and differs from
`local`. The adapter and model values are retained only because they were
returned through the existing normalized `ClusterResult` contract; generated
content is redacted.

## Architecture observations

This observation demonstrates that the unchanged Phase 16 client can participate
in one real remote execution while remaining topology-blind. The client sent only
to the caller's fixed loopback endpoint.

The ordinary caller owned the declared topology, candidate order, accepted
bounded fallback, remote transport, result validation, and declared-node
attribution. With the caller local runtime connection unavailable before request
transmission, the accepted fallback selected the one explicitly declared remote.
The request crossed the real trusted-LAN machine boundary to the ordinary
receiving application, which executed through its local Ollama composition.

The caller returned the declared remote ID, and the client validated and printed
one complete normalized result. No second client invocation was required.

## Privacy review

This record retains only the proof date, revision, clean-tree state, sanitized
roles, structural observations, one command shape, invocation count, exit and
stream observations, declared node ID, and sanitized normalized result.

It retains no actual prompt or generated-response content, private address,
hostname, username, filesystem path, declaration path or URL, credential,
token, raw log, traceback, packet capture, screenshot, shell-history content,
or unnecessary runtime detail.

## Cleanup

The runbook required operator-controlled cleanup of the ordinary static-cluster
caller, ordinary receiving application, temporary declaration, and any temporary
firewall exposure. Cleanup completion was not part of the retained observations,
so this record makes no claim that those steps were completed.

## Result

The retained proof succeeded. One unchanged ordinary client invocation reached a
real trusted-LAN receiver through the existing static-cluster fallback path and
returned a complete normalized result attributed to `ordinary-remote-proof`.

## Proof limitations

This proof establishes one request, one caller, one accepted fallback, one
declared remote, one real LAN crossing, one ordinary receiver, and one normalized
result. It does not demonstrate discovery, dynamic registration, scheduling,
load balancing, multiple remote candidates, retry, high availability,
authentication, encryption, internet-safe operation, runtime supervision,
automatic runtime lifecycle, model selection, request-level runtime selection,
broad distributed inference, or production readiness.

## Non-goals

This retained evidence adds no code, test, CLI, API, routing, fallback,
transport, topology, roadmap phase, RFC, investigation, runbook, or existing
proof behavior.
