# Heterogeneous Static Capabilities Proof

Status: Complete

## Claim

Ordinary explicit static declarations can give two declared remotes different
bounded capability sets. The normal static-cluster router uses those sets for
eligibility while retaining local-first behavior and existing bounded fallback.

## Accepted boundaries

This proof exercises accepted RFC-0058 declaration ownership together with the
existing capability-eligibility, local-first, remote-order, pre-request
connection-unavailable traversal, native chat, and native summarize contracts.
It introduces no routing policy, selector, probing, scheduling, status field,
or local capability configuration.

## Topology

The proof used one machine and three separate ordinary processes:

```text
caller static-cluster process
  -> chat receiver local process
  -> summarize receiver local process
```

The two receivers used ordinary `hac local` startup with an available local
runtime. The caller used ordinary `hac static-cluster` startup. All request
traffic crossed real HTTP process boundaries; no transport, registry, adapter,
or application composition was mocked or invoked directly.

## Declaration

The caller loaded an ordered TOML declaration equivalent to:

```toml
[[remote_nodes]]
node_id = "chat-remote"
base_url = "http://<CHAT_RECEIVER>:<PORT>"
capabilities = ["chat"]

[[remote_nodes]]
node_id = "summary-remote"
base_url = "http://<SUMMARY_RECEIVER>:<PORT>"
capabilities = ["summarize"]
```

The declaration is caller-owned static data. It did not claim runtime discovery
or verification of either receiver capability.

## Preconditions

The caller's fixed local node retained its existing `chat` and `summarize`
declarations. To observe remote routing without changing local-first behavior,
the caller used an accepted ordinary local runtime configuration whose endpoint
was unavailable before request transmission. This produced the established
pre-request connection-unavailable condition and allowed bounded traversal to
eligible declared remotes.

Both receiver processes were available. No direct node selector was used.

## Preflight observation

Ordinary `hac preflight --declaration <DECLARATION>` reported a coherent,
network-free static multi-node projection in this order:

1. `local`: `chat`, `summarize`
2. `chat-remote`: `chat`
3. `summary-remote`: `summarize`

This observation is declaration validation only. It did not contact either
receiver, probe a runtime, or establish execution availability.

## Chat observation

One ordinary `hac chat --verbose` request through the caller endpoint succeeded
and reported caller-owned attribution to `chat-remote`. The summarize-only
remote was not selected. The result followed local-first selection, the
accepted local pre-request-unavailability condition, and bounded traversal to
an eligible remote; it did not use direct targeting.

## Summarize observation

One ordinary `hac summarize --file <SYNTHETIC_INPUT> --verbose` request through
the same caller endpoint succeeded and reported caller-owned attribution to
`summary-remote`. The input was a small synthetic UTF-8 file and neither its
contents nor the generated summary is retained.

`chat-remote` appeared first in the declaration but was not selected for this
summarize request. The request therefore crossed the real HTTP boundary only to
the eligible summarize-only receiver after the accepted local pre-request
unavailability condition.

## Negative eligibility observation

The summarize observation directly showed that a first-declared chat-only
remote was excluded for summarize. For the reciprocal case, an otherwise
equivalent declaration placed the live summarize-only remote before the live
chat-only remote. One ordinary chat request still succeeded at `chat-remote`.

Thus the first remote's declaration order did not make it eligible for the
wrong capability. These two observations establish:

```text
chat-only remote: eligible for chat; ineligible for summarize
summarize-only remote: eligible for summarize; ineligible for chat
```

The proof did not retain a no-capability response. With the fixed local node
still declaring both capabilities, an unavailable local runtime and no eligible
remote produce the existing runtime-unavailable execution outcome rather than a
no-selectable-candidate result. No local declaration was changed to manufacture
a different failure.

## What this proves

- Ordinary explicit `chat` and `summarize` remote declarations are accepted.
- Static preflight represents the two declared heterogeneous sets in order and
  remains network-free.
- Normal routing excludes a remote that lacks the requested declared
  capability.
- Chat reached a chat-only declared remote, and summarize reached a
  summarize-only declared remote.
- Local-first remained intact; existing bounded fallback reached only eligible
  remotes after the accepted local pre-request-unavailability condition.
- Existing remote declaration order and failure contracts remained unchanged.
- No scheduler or direct node selector was involved.

## What this does not prove

This proof does not establish runtime capability discovery or verification,
best-node selection, performance, load balancing, health-aware scheduling,
model- or hardware-aware routing, remote specialization, arbitrary
capabilities, heterogeneous local capabilities, generalized distributed
operation, or Phase 19.

## Privacy and sanitization

Only placeholder node identities, roles, and structural outcomes are retained.
This record excludes hostnames, addresses, ports, usernames, paths, runtime
URLs, model inventories, hardware details, timestamps, prompts, source text,
generated responses, raw logs, credentials, and environment data.

## Reproduction outline

1. Start two ordinary local receiver processes with available runtimes.
2. Create an operator-owned ordered declaration with one chat-only and one
   summarize-only remote, using private values only outside repository evidence.
3. Run ordinary declaration preflight.
4. Start an ordinary caller static-cluster process with the accepted local
   pre-request-unavailability condition.
5. Send one `hac chat` and one `hac summarize --file` request through the
   caller endpoint; inspect only their transient verbose attribution.
6. Reverse the heterogeneous declarations and repeat one chat request to
   observe exclusion of the first wrong-capability remote.
7. Stop all processes and remove temporary declarations and synthetic input.

## Conclusion

The retained ordinary process-and-HTTP proof demonstrates that RFC-0058's
explicit static remote capability declarations control routing eligibility for
the accepted `chat` and `summarize` capabilities. It preserves local-first
routing, bounded fallback, declaration order among eligible remotes, and the
existing failure boundaries without introducing an architectural decision.
