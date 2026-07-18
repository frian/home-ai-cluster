# End-to-End Ordinary Remote Request Proof Runbook

Status: Planned

## Safety notice

This runbook prepares one real integration proof; it does not report that a
proof has run.

The receiving Home AI Cluster process will be reachable on the trusted LAN for
this proof. That accepted prototype boundary does not provide production
authentication, encryption, or internet-safe exposure. Restrict access to the
trusted LAN, do not expose the receiver to the public internet, and remove any
temporary firewall allowance after the proof. Firewall and network policy remain
operator-owned.

Do not commit real addresses, hostnames, usernames, paths, prompts, generated
responses, credentials, runtime URLs, or declaration contents. This runbook uses
placeholders throughout; use the same treatment in any later retained evidence.

## Purpose

This runbook defines the smallest real proof of the already accepted path:

```text
home-ai-cluster-chat
  -> caller loopback POST /v1/chat
  -> ordinary static-cluster routing
  -> caller local runtime unavailable before request transmission
  -> accepted bounded fallback
  -> explicitly declared remote
  -> trusted-LAN HTTP transport
  -> ordinary receiving Home AI Cluster process
  -> receiving runtime adapter
  -> normalized ClusterResult
  -> caller-owned declared remote node_id
  -> one-shot client validation and output
```

It uses only existing ordinary commands and accepted contracts. It introduces no
new endpoint, protocol, selector, retry, client-side fallback, proof helper, or
security design. The client stays topology-blind; the running caller remains the
owner of topology, routing, fallback, transport, result validation, and declared
remote attribution.

The architectural basis is recorded in [the end-to-end investigation](phase-17-end-to-end-ordinary-remote-request-investigation.md),
[RFC-0045](../RFC/RFC-0045-one-shot-ordinary-request-command.md),
[RFC-0038](../RFC/RFC-0038-ordinary-static-multi-node-mode.md), and
[RFC-0040](../RFC/RFC-0040-multiple-explicit-static-remote-nodes.md). The
existing Phase 12 and Phase 16 records establish the component paths this proof
will compose; this runbook does not reclassify either record.

## Scope and topology

Use exactly two distinct physical machines on one trusted LAN.

```text
calling machine
  <CALLER_REPOSITORY_PATH>
  ordinary home-ai-cluster-static-cluster process on loopback
  home-ai-cluster-chat client
  default Ollama local composition, deliberately unavailable before the request
  one operator-owned declaration naming the receiving process

receiving machine
  <RECEIVER_REPOSITORY_PATH>
  operator-managed Ollama runtime, available locally
  ordinary home-ai-cluster-local process on <RECEIVER_PORT>
  explicit trusted-LAN application bind
```

The default Ollama arrangement is the preferred minimum. The caller's Ollama is
unavailable before the request; the receiver's Ollama remains available. Do not
require heterogeneous runtimes: Phase 12 already proved that separate concern.

`home-ai-cluster-local` and `home-ai-cluster-static-cluster` also support the
accepted explicit `llama-server` composition, but use it only when the operator
has a simpler existing environment. Runtime selection belongs only to process
startup. It must not enter the client invocation, request, declaration, routing
selector, or node attribution.

## Preconditions

Before starting, confirm all of the following:

- two distinct physical machines are available on the same trusted LAN;
- both checkouts use the same repository revision and have clean or understood
  working trees;
- Python and `uv` are available on both machines and dependencies are
  synchronized;
- a supported runtime is installed and operator-prepared on the receiver;
- the receiver runtime is locally available and can serve the required model or
  execution capability;
- the caller's selected local runtime endpoint will be unavailable before the
  one request;
- `<RECEIVER_PORT>` is available on the receiving machine and the caller's
  loopback port `8000` is available;
- the temporary declaration is operator-owned, outside committed repository
  content, and contains no secret;
- firewall exposure is limited to `<RECEIVER_PORT>` and the trusted LAN; and
- no private value is intended for retained evidence.

Do not continue if the two physical machines cannot be distinguished, the LAN is
not trusted, or the evidence cannot be sanitized.

## Placeholders

Use these placeholders in working notes and retained evidence:

```text
<CALLER_REPOSITORY_PATH>
<RECEIVER_REPOSITORY_PATH>
<RECEIVER_ADDRESS>
<RECEIVER_PORT>
<REMOTE_NODE_ID>
<DECLARATION_PATH>
<TEST_MESSAGE>
```

Use `ordinary-remote-proof` as the neutral value for `<REMOTE_NODE_ID>` unless a
different non-private placeholder is needed. Use a harmless, bounded test
message at execution time, but refer to it later only as
`<REDACTED_TEST_MESSAGE>`.

## Procedure

### 1. Record and compare the repository state

On the calling machine, from `<CALLER_REPOSITORY_PATH>`, run:

```sh
git rev-parse HEAD
git status --short
uv sync
```

On the receiving machine, from `<RECEIVER_REPOSITORY_PATH>`, run the same:

```sh
git rev-parse HEAD
git status --short
uv sync
```

Record the one shared revision in the future proof. The proof must stop if the
revisions differ. A clean worktree is preferred. If a worktree is not clean, the
operator must understand and record only that its state was understood; do not
retain unrelated file names or private local details.

### 2. Prepare the receiving runtime

Prepare and start the receiving runtime through its own supported,
operator-controlled procedure. Ensure its required model or execution capability
is already locally available. Home AI Cluster does not install, download, start,
supervise, repair, or stop that runtime.

For the default arrangement, use the existing finite local health command on the
receiving machine:

```sh
uv run home-ai-cluster-health
```

Confirm locally that the one adapter observation is `available`. Do not copy raw
health output into the retained proof: it may contain an operator-specific reason
or runtime detail. This check establishes only local runtime availability; it
does not establish LAN reachability or start the Home AI Cluster receiver.

### 3. Start the ordinary receiving application

On the receiving machine, with the default Ollama composition, start the
ordinary receiver:

```sh
uv run home-ai-cluster-local \
  --host 0.0.0.0 \
  --port <RECEIVER_PORT>
```

The no-option composition is the existing Ollama-backed default. The `--host`
and `--port` options are existing ordinary local-startup inputs. The `0.0.0.0`
bind is temporary and acceptable only under the trusted-LAN and firewall limits
in this runbook. Do not use a public or internet-facing bind.

Keep this receiver running through the one request. It is an ordinary local
application, not a remote-specific mode: it does not know the caller's declared
node ID, parse the caller declaration, or own remote routing. Its existing
internal request route executes through its one local composition.

Do not use `/v1/chat` for readiness. The optional accepted status step below is
the bounded application-and-runtime observation when that information is useful.

### 4. Create the caller declaration

On the calling machine, create one temporary operator-owned TOML file at
`<DECLARATION_PATH>`. It must not be committed. Use the current accepted ordered
remote declaration shape with exactly one remote:

```toml
[[remote_nodes]]
node_id = "ordinary-remote-proof"
base_url = "http://<RECEIVER_ADDRESS>:<RECEIVER_PORT>"
```

The declaration contains topology only. It must contain no runtime, adapter,
model, credential, token, authorization value, or lifecycle setting. The real
URL and declaration path are operator-owned and must be replaced by placeholders
in any retained proof.

Validate the declaration locally without network observation through the
existing preflight command:

```sh
uv run home-ai-cluster-preflight --declaration <DECLARATION_PATH>
```

Continue only when its static report is coherent. Preflight validates static
declaration and local registry facts; it does not demonstrate receiver
reachability, runtime availability, fallback, or request execution.

### 5. Establish caller local unavailability

Use the default caller Ollama composition and leave the caller's Ollama service
stopped or otherwise unavailable before the request. Do not stop the receiver
runtime. Do not create a failure by changing code, injecting an exception,
creating a timeout or firewall race, or terminating a runtime after request
transmission begins.

Run this one finite local observation on the calling machine:

```sh
uv run home-ai-cluster-health
```

Confirm locally that the single adapter observation is `unavailable`; do not
retain raw health output or its reason text. This is a pre-request check only. It
must not start the caller runtime. The required request-time condition remains a
connection-establishment failure before useful runtime execution, as defined by
the accepted bounded fallback boundary.

If the caller runtime is unexpectedly available, stop the proof before starting
the static caller or invoking the client. Do not attempt to make the remote win
through a request selector, topology reorder, or a second request.

### 6. Optionally inspect the declared cluster

After the declaration exists and the receiver is running, an operator may run
one accepted finite diagnostic observation on the calling machine:

```sh
uv run home-ai-cluster-status --declaration <DECLARATION_PATH>
```

For the intended condition, it should show a coherent declaration, fixed local
runtime `unavailable`, and the declared remote application `reachable` with
runtime `available`. Retain only a sanitized structural observation if it is
useful; do not retain real addresses or raw details.

This status command does not select a route, execute a chat request, prove remote
execution, alter topology, or change fallback. It is optional diagnostic evidence
only. A failure or an unexpected status is a stop condition, not a reason to
retry the later ordinary request.

### 7. Start the ordinary static-cluster caller

On the calling machine, start the ordinary static caller:

```sh
uv run home-ai-cluster-static-cluster \
  --declaration <DECLARATION_PATH>
```

The default caller composition is Ollama-backed and intentionally unavailable
for the proof. Construction does not probe that runtime. The caller exposes the
ordinary fixed loopback target consumed by the client:

```text
http://127.0.0.1:8000/v1/chat
```

The caller owns the static topology, local-first candidate order, accepted
bounded fallback, declared-remote transport, normalized remote-result validation,
and caller-owned declared remote attribution. Supply none of those facts to
`home-ai-cluster-chat`.

If the caller cannot bind its loopback endpoint, stop. Do not change the client
target, start another caller, or use a direct receiver request as a substitute.

### 8. Send exactly one ordinary request

With both ordinary processes running, invoke exactly once on the calling machine:

```sh
uv run home-ai-cluster-chat --message "<TEST_MESSAGE>"
```

Use one harmless bounded message. Do not place its literal content in the future
retained proof, shell-history evidence, screenshots, logs, or documentation.
Observe the command's exit status, standard output, and standard error as
separate streams. Sanitize output before retention; retain only the normalized
result structure and required node-attribution evidence.

Do not retry the command. Do not substitute curl for the client, call the
receiver directly, invoke `/v1/chat` manually, or add a node, runtime, adapter,
model, host, port, capability, topology, retry, or timeout selector. One
invocation represents exactly one ordinary request.

### 9. Validate the result

Accept the proof only if all of the following are true:

- the one-shot client exits `0`;
- standard error is empty;
- standard output is exactly one compact JSON object;
- that object is a complete valid `ClusterResult`, not content-only output;
- `node_id` equals `ordinary-remote-proof` (or the declared sanitized remote ID);
- `node_id` is not `local`;
- the client invocation contained no infrastructure selector; and
- no second client request was made.

The existing result may include `adapter` and `model` fields. Retain them only
when necessary and already public through the result contract; otherwise replace
their concrete values with placeholders. Replace generated `content` with
`<REDACTED_GENERATED_CONTENT>`.

### 10. Shut down and clean up

After the observation, the operator must:

1. stop the ordinary static-cluster caller;
2. stop the ordinary receiving Home AI Cluster application;
3. revert the temporary firewall exposure;
4. remove or securely handle the temporary declaration;
5. restore the caller runtime only if the operator wants it restored; and
6. confirm that no proof-specific Home AI Cluster process remains.

External runtime shutdown remains an operator decision. Home AI Cluster does not
claim ownership of runtime cleanup, remote process control, supervision, or
repair.

## Failure and stop conditions

Stop this proof attempt without retry if any of the following occurs:

- repository revisions differ;
- the receiver runtime is unavailable;
- the receiver ordinary application is unreachable;
- the caller local runtime is unexpectedly available;
- declaration validation fails;
- the static caller cannot bind its loopback endpoint;
- the one-shot client exits non-zero;
- standard error is non-empty on an apparent success;
- standard output is invalid or not one complete result;
- `node_id` is `local`;
- `node_id` differs from the declared remote ID;
- a second invocation would be needed to obtain success; or
- private data cannot be safely sanitized.

After stopping, the operator may investigate the environment outside this proof
claim. Do not rewrite a failed attempt as success. A retained proof may report
only a later, separately executed successful run.

## Evidence worksheet

Record only this privacy-safe worksheet for a future run:

```text
Proof date:
Repository revision:
Calling machine role confirmed:
Receiving machine role confirmed:
Two physical machines confirmed:
Trusted-LAN boundary confirmed:
Caller local runtime unavailable before request:
Receiver runtime available:
Receiver ordinary process reachable:
Declaration validated:
Static caller started on fixed loopback target:
Client invocation count:
Client exit status:
Client stdout shape:
Client stderr state:
Result node_id:
Result node_id differs from local:
Temporary firewall exposure removed:
Temporary declaration handled:
Proof outcome:
```

Do not add real addresses, hostnames, usernames, filesystem paths, prompts,
generated responses, credentials, raw logs, or packet-capture fields.

## Future retained-proof boundary

Create [`end-to-end-ordinary-remote-request-proof.md`](end-to-end-ordinary-remote-request-proof.md)
only after one real successful run. It may retain the repository revision, date,
sanitized two-machine roles and command shapes, trusted-LAN confirmation, one
invocation count, exit status, standard-output and standard-error structure, a
sanitized complete result shape, declared remote attribution, limitations, and
non-goals.

It must not retain actual prompt or generated-response content, private IP
addresses, hostnames, usernames, home or repository paths, credentials, tokens,
real runtime URLs, real declaration contents, raw logs, packet captures,
tracebacks, or unnecessary model or adapter identity.

## Proof limitations

Even a successful run proves only this bounded ordinary two-machine composition.
It does not prove discovery, dynamic registration, scheduling, load balancing,
retries, high availability, authentication, encryption, internet-safe operation,
runtime supervision, automatic lifecycle, model selection, or broad distributed
inference.

## Non-goals retained

This runbook adds no code, tests, commands, APIs, RFCs, roadmap phase, discovery,
dynamic registration, remote process control, process supervision, automatic
runtime startup, retry, client-side fallback, direct node selection, new endpoint
or protocol, authentication or TLS design, packet capture, proof helper command,
generic proof framework, Docker, or Kubernetes.
