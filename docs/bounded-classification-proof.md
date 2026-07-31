# Bounded Classification Proof

Status: Retained

## Proof question

Can the accepted RFC-0061 bounded `classify` capability select one exact
operator-supplied label through ordinary local execution and ordinary static
remote execution, while preserving cluster-owned node attribution and exact
result validation?

## Accepted boundary and implementation status

RFC-0061 is the authoritative architectural decision. It defines one bounded
classification request with ordered labels, one adapter-proposed label, and
cluster-owned acceptance only when that proposal exactly belongs to the original
label set. This record is privacy-safe evidence of the accepted implementation;
it does not change the architecture, RFC, or operator contract.

The implementation sequence is complete through the native `hac classify`
command, ordinary local composition for Ollama and llama-server, internal
classification transport, explicit static capability eligibility, and ordinary
static-cluster routing. The retained observations below include the corrective
implementation work through PR #399.

The proven execution shape is:

```text
bounded native request
  -> capability-centered node selection
  -> local execution or internal remote transport
  -> runtime-specific structured output
  -> adapter decoding
  -> cluster exact-membership validation
  -> minimal ClassifyResult
```

Runtime-specific structured output is an adapter-local detail. The adapter
decodes one proposal string; it does not decide label membership. The unchanged
executor remains the owner of exact membership against the original ordered
labels.

## Bounded cases and input forms

Every completed proof used these bounded cases:

| Source form | Labels | Selected label |
| --- | --- | --- |
| explicit `--text`: invoice due tomorrow | `invoice`, `personal` | `invoice` |
| explicit `--text`: medical appointment | `finance`, `medical` | `medical` |
| stdin: failed payment | `technical`, `billing` | `billing` |

The first two cases exercised explicit `--text`; the third exercised stdin.
Only these short sanitized input descriptions and selected labels are retained.
No raw model output, prompts, runtime logs, or private command history is
retained.

## Ordinary local Ollama proof

An installed ordinary `hac classify` command ran against an ordinary local
Ollama composition. All three bounded cases succeeded. Each minimal result was
attributed as:

```text
node_id: local
```

Ollama used its adapter-local constrained structured-output mechanism. The
adapter decoded its proposal string, and the cluster accepted it only through
the existing exact-membership boundary.

## Ordinary local llama-server proof

The same installed ordinary command and the same three bounded cases ran
against an ordinary local llama-server composition. All succeeded, each with:

```text
node_id: local
```

llama-server used its separate adapter-local structured-output mechanism. That
mechanism did not alter the request, result, routing, or validation contract.
The decoded proposal still crossed the unchanged executor exact-membership
boundary.

## Loopback static remote proof

### Topology and declarations

One machine ran separate ordinary caller and receiver processes, exercising the
real process and HTTP boundaries while keeping the topology loopback-only:

```text
native hac classify client
  -> caller-side static-cluster process
  -> internal classification transport
  -> separate receiver process
  -> receiver-local llama-server runtime
```

The caller-local declaration listed only:

```text
chat
```

The declared remote `remote-classifier` listed only:

```text
classify
```

These are caller-owned static eligibility declarations, not receiver-side
capability discovery or runtime verification. Because the caller-local node was
not eligible for `classify`, it could not be selected; the declared remote was
the only eligible classification candidate. Remote selection was therefore
mandatory without a direct node selector, local failure, retry, or fallback
trigger.

### Observation

All three bounded cases succeeded through the internal classification transport.
Each returned caller-owned remote attribution:

```text
node_id: remote-classifier
```

This exercises local ineligibility, explicit remote `classify` eligibility, the
closed internal classification request, receiver-side validation and local
execution, result return to the caller, and caller-owned remote identity. It
also covers both explicit `--text` and stdin through the remote path.

## Physical two-machine remote proof

### Topology and declarations

One ordinary caller machine and one separate Raspberry Pi-class receiver ran on
a real local network. The receiver was a separate operating-system instance
with a separate Home AI Cluster installation, checkout, and receiver-local
Ollama runtime using a small locally available instruct model. The runtime was
private to the receiver; only the Home AI Cluster receiver was reachable from
the caller across the local network.

The sanitized path was:

```text
native hac classify client on caller
  -> caller-side static-cluster process
  -> real local network
  -> receiver process on separate machine
  -> receiver-local Ollama runtime
```

The caller-local node declared only `chat`. The declared remote logical node ID
`raspberry-pi` declared `classify`. The local caller was consequently ineligible
for classification, so the declared physical receiver was the only eligible
classification candidate. This required real internal HTTP transport across the
LAN; no direct runtime access or direct node selector was used.

### Observation

All three bounded cases succeeded across the physical network boundary. Each
returned:

```text
node_id: raspberry-pi
```

This retains evidence of separate machines, processes, installations, files,
and runtimes; a receiver listening on a non-loopback network interface; real
LAN transport; capability-centered remote selection; receiver-local runtime
execution; explicit `--text` and stdin coverage; result return to the caller;
and caller-owned physical remote attribution.

The physical proof is specifically one ordinary caller machine, one declared
physical remote receiver, one receiver-local Ollama runtime, and real LAN
transport.

## Defects found and corrected

The proof work exposed implementation defects, not new architectural decisions:

1. ordinary local runtime composition initially did not advertise `classify`;
2. standalone local health reporting initially omitted `classify`;
3. XML-like label prompts could lead Ollama to return markup instead of an exact
   label; and
4. XML-like label prompts could lead llama-server to return markup instead of an
   exact label.

PRs #396, #397, #398, and #399 corrected those implementation defects. They
restore the accepted RFC-0061 contract without changing capability semantics,
routing, transport, or executor ownership.

## What this proves

RFC-0061 now has retained ordinary evidence for:

- Ollama local execution;
- llama-server local execution;
- static remote classification through the real internal transport;
- physical two-machine classification through a real LAN;
- capability-centered mandatory remote selection when the caller-local node is
  ineligible;
- exact result validation at the unchanged cluster boundary;
- local and remote node attribution; and
- explicit text and stdin input.

## Limitations and non-claims

This evidence does not establish dynamic discovery, receiver-side runtime
capability discovery or verification, scheduling, load balancing, retries,
generalized failover beyond accepted ordered fallback contracts, supervision,
lifecycle management, automatic deployment, authentication, encrypted cluster
transport, internet or WAN operation, multiple simultaneous physical remote
nodes, heterogeneous remote adapters across several physical nodes, concurrency
or performance characteristics, generic structured output as a cluster
capability, or production hardening of exposed network listeners.

It does not add distributed infrastructure. It records the current static
architecture across two physical machines only within the stated proof shape.

## Privacy and sanitization

This record excludes real usernames, home-directory or checkout paths, physical
hostnames, process identifiers, timestamps, private LAN or VPN addresses,
credentials, tokens, raw model output, full runtime logs, model-cache paths,
hardware serial numbers, and machine-specific package paths. `raspberry-pi` is
retained only as the declared logical node ID returned to the caller, not as a
physical hostname.

## Conclusion

Within the accepted RFC-0061 boundaries, the implementation and proof sequence
are complete. One bounded native request can execute locally or traverse the
existing internal static remote transport, use adapter-local structured output,
and return a minimal result only after cluster-owned exact label validation.
The retained local, loopback-remote, and physical-LAN observations provide
evidence for that behavior without expanding the architecture or its claims.
