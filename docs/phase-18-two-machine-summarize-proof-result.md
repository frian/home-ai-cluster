# Phase 18 Two-Machine Summarize Proof Result

Status: Retained

## Purpose

This record retains privacy-safe evidence from the completed real two-machine
Phase 18 summarize execution. It is descriptive evidence, not a new
architectural decision. Accepted RFC-0051 remains authoritative.

## Recorded revisions and correction

The first physical attempt used:

```text
0eca30624da38dcfa1fcb2c9b1d67e488baaa72b
```

It stopped before sending a summarize request because caller preflight
truthfully reported the ordinary declared remote as chat-only. That preparation
identified an implementation defect: the shared ordinary static remote factory
declared only `chat`; inline startup, TOML startup, preflight, and status all
reused it; and the ordinary remote was consequently ineligible for
`SummarizeRequest`.

PR #337, `Fix summarize capability for ordinary static remotes`, corrected the
implementation. The completed proof used this correction commit on both
physical machines:

```text
5aece18aebf0bdde4d2c7a39a2967e8e2fdb597c
```

The correction makes ordinary declared remotes advertise exactly `chat` and
`summarize`. It did not change the topology declaration format, routing policy,
bounded fallback, transport, attribution, runtime behavior, or privacy
contract.

## Physical topology

### Caller

- ordinary explicit static-cluster process;
- topology-only declaration containing one declared receiver;
- ordinary local Ollama composition advertising `chat` and `summarize`;
- local runtime deliberately stopped before the first request; and
- caller-owned declared remote node ID `phase-18-summarize-receiver`.

### Receiver

- separate physical Windows machine;
- ordinary trusted-LAN `home-ai-cluster-local` process;
- ordinary Ollama adapter with its runtime and required model available;
- local node advertising `chat` and `summarize`; and
- handling of the received tagged summarize request through the ordinary local
  execution boundary.

## Structural preparation observations

- Both machines reported the correction commit and clean worktrees before
  execution.
- Receiver preflight was coherent; its local capabilities were `chat` and
  `summarize`.
- Receiver Ollama health was `available`, and its normalized internal runtime
  status was `available`.
- Caller static-cluster preflight was coherent. It reported `chat` and
  `summarize` for both the local node and the declared receiver.
- Before the deliberate caller-local runtime shutdown, caller status reported
  local application status `local`, local runtime status `available`, receiver
  application status `reachable`, and receiver runtime status `available`.

## Remote summarize observation

After the caller-local runtime was deliberately stopped before transmission,
one native `POST /v1/summarize` request to the caller's loopback endpoint
succeeded through the declared receiver. The request crossed the real network
boundary and was handled by the ordinary local receiver application. Under the
accepted receiver boundary, that application executes locally and does not
perform declared-remote forwarding.

The caller returned this privacy-safe structural result:

```json
{
  "content": "<non-empty summary omitted>",
  "adapter": "ollama",
  "model": "llama3.2",
  "node_id": "phase-18-summarize-receiver"
}
```

The final remote identity came from the caller-owned declaration. An IP address,
URL, hostname, adapter name, and model name did not provide cluster node
identity.

## Local-first complementary observation

After the caller-local runtime was restored, the same native summarize
operation succeeded again and returned:

```json
{
  "content": "<non-empty summary omitted>",
  "adapter": "ollama",
  "model": "llama3.2",
  "node_id": "local"
}
```

The declared receiver was no longer selected. This confirms it was not directly
targeted and that accepted local-first ordering remained active.

## History and privacy observation

After both summarize executions, the supported history inspection surface,
`home-ai-cluster-history`, returned:

```json
[]
```

No summarize history entry was observed. No source text, generated summary,
internal envelope, or private topology was retained by that supported
inspection surface. This is limited to the observed history result; accepted
automated tests separately cover the no-history contract.

## Required deviation and correction

The original Phase 18 implementation revision could not complete the ordinary
physical proof because ordinary remotes were still declared chat-only. The
runbook correctly required stopping rather than modifying topology or bypassing
capability routing. The defect was corrected in separate implementation PR
#337, and the complete physical proof was rerun successfully on the correction
commit.

The successful proof was not manufactured by putting capabilities in the TOML
declaration or directly targeting the receiver. The declaration remained
topology-only throughout.

## Conclusions

The real proof demonstrated that:

- one native summarize request crossed two physical machines;
- routing eligibility used the declared `summarize` capability;
- local-first behavior remained active;
- fallback remained bounded to accepted pre-transmission local unavailability;
- the declared receiver handled the request through its ordinary local execution
  boundary;
- final remote attribution remained caller-owned;
- the topology declaration remained topology-only;
- normalized runtime metadata remained engine-specific only in the result; and
- supported request history remained empty.

It does not establish discovery, dynamic capability exchange, scheduling, load
balancing, retries, internet-facing security, production readiness, a
generalized multi-capability architecture, Phase 19, or a new architectural
decision.

## Privacy exclusions

This retained record contains no:

- source text;
- generated summary;
- private IP address or URL;
- hostname or machine name;
- username;
- absolute filesystem path;
- declaration contents;
- raw internal request envelope;
- raw logs or runtime logs;
- authorization value or secret;
- screenshot; or
- verbose command output containing private values.
