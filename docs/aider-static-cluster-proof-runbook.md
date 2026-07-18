# Aider Static-Cluster Compatibility Proof Runbook

Status: Planned

## 1. Purpose

This runbook prepares one later, real, two-machine execution. It does not
report that the execution has occurred, add an implementation, or make a new
architectural decision.

The intended bounded proof is:

```text
Aider
  -> caller-local 127.0.0.1 compatibility endpoint
  -> home-ai-cluster-openai-compatibility --declaration <DECLARATION_PATH>
  -> unchanged RFC-0031 request translation
  -> ordinary explicit static-cluster composition
  -> unavailable caller-local runtime before request transmission
  -> local-first capability routing and bounded pre-execution fallback
  -> one declared trusted-LAN receiver
  -> receiver-local runtime execution
  -> caller-owned normalized result attributed internally to the declared node
  -> unchanged RFC-0031 compatibility response to Aider
```

This is a preparation for one proof attempt only. A failed attempt remains a
failed attempt.

## 2. Architectural boundary

RFC-0046 accepts exactly one explicit static-cluster form:

```sh
uv run home-ai-cluster-openai-compatibility --declaration <DECLARATION_PATH>
```

It reuses the RFC-0039/RFC-0040 declaration loader and the ordinary static
collection construction. The compatibility router remains the RFC-0031 public
edge: it translates the accepted plain-text request into a cluster-owned
`chat` request and returns the unchanged compatibility response. It does not
select a node, inspect a declaration, call a receiver, retry, or expose routing
facts to Aider.

The caller owns local-first routing, accepted bounded fallback, transport,
result validation, and declared-node attribution. The receiver remains an
ordinary, separately started Home AI Cluster process. All runtime and process
lifecycle remains operator-owned.

## 3. What this runbook proves

If every success condition and the observation gate in this runbook is met, a
later retained proof may establish one narrow fact: a real Aider v0.86.0-style,
non-streaming request reached the caller-local compatibility edge and completed
through the existing ordinary explicit static-cluster path after an unavailable
caller-local runtime advanced through the existing pre-execution fallback to
one declared remote receiver.

It may establish that Aider received one unchanged successful RFC-0031
response. It must not claim that Aider observed the selected node.

## 4. What this runbook does not prove

This runbook does not prove general Aider support, a general OpenAI-compatible
API, production readiness, performance, latency, encryption, authentication,
internet-safe deployment, or any client-visible routing result. It does not
prove support for another capability, another Aider version or mode, a second
request, another remote, retries, or failover after execution begins.

## 5. Required machines and network

Use exactly two distinct physical machines on one trusted LAN:

```text
caller
  compatibility listener: 127.0.0.1:8001 only
  Aider
  caller-local runtime deliberately unavailable

receiver
  ordinary Home AI Cluster receiving process
  one available supported local runtime and chat-capable model
```

Use exactly one static declaration containing one remote node. The declaration
and its real private address remain operator-local. Do not use a third machine,
VPN, overlay, tunnel, reverse proxy, container network, Docker, Kubernetes,
public internet exposure, cloud runtime, or hosted inference provider.

The receiver may be exposed only as required by the existing trusted-LAN
receiver workflow. The compatibility listener must remain loopback-only and
must not be reachable from the receiver or any other LAN machine.

## 6. Fixed process roles

### Caller

The caller runs the merged proof revision, the explicit compatibility command,
Aider, and temporary Aider-side configuration. Its compatibility URL is fixed:

```text
http://127.0.0.1:8001/v1/chat/completions
```

Its local runtime must be unavailable before the Aider submission. The caller
must not run a separate static-cluster process, a compatibility proxy, or a
direct receiver client for this attempt.

### Receiver

The receiver runs the same merged revision, one ordinary receiving Home AI
Cluster process, and one operator-managed supported local runtime with a
locally available chat-capable model. It does not receive the caller's
declaration, declared node ID, Aider configuration, or lifecycle control.

## 7. Required software and revisions

Before the attempt, on both machines:

```sh
git rev-parse HEAD
git status --short
uv sync
```

Proceed only if both `HEAD` values are the same merged commit and both status
commands have no output. Record only that shared commit SHA and the sanitized
roles `caller` and `receiver` in later proof notes. Do not retain repository
paths, untracked-file names, or command output.

Use Aider v0.86.0, the evidence-backed version in the retained Phase 6 proof,
unless a separately documented compatible version has been assessed before this
attempt. If installed Aider help or observed request behavior differs
materially from the retained configuration, stop and document an Aider
incompatibility. Do not broaden Home AI Cluster to accommodate it.

## 8. Privacy boundary

Do not retain prompts, generated content, source content, declaration content,
private addresses, hostnames, usernames, machine names, credentials, tokens,
remote URLs, raw HTTP bodies, raw logs, shell history, screenshots, packet
captures, process environments, firewall dumps, or temporary configuration.

Use placeholders in working notes and future evidence:

```text
<DECLARATION_PATH>
<REMOTE_NODE_ID>
<RECEIVER_ADDRESS>
<RECEIVER_PORT>
<RUNTIME_MODEL_IDENTIFIER>
<AIDER_MODEL_SETTINGS_FILE>
<NULL_HISTORY_TARGET>
<ONE_HARMLESS_MESSAGE>
```

The placeholder API key is non-secret and must not be recorded. It is accepted
only as RFC-0031 loopback client compatibility, not as authentication.

## 9. Preflight checklist

Complete every item before the single submission.

### Caller

- Confirm the shared clean revision.
- Confirm `home-ai-cluster-openai-compatibility --help` shows
  `--declaration`.
- Confirm the one-remote declaration is accepted locally with:

  ```sh
  uv run home-ai-cluster-preflight --declaration <DECLARATION_PATH>
  ```

  This validates local declaration structure only and performs no network
  observation.
- Confirm neither the native caller port nor compatibility port is already
  occupied unexpectedly.
- Confirm the caller-local runtime is unavailable with:

  ```sh
  uv run home-ai-cluster-health
  ```

  Do not retain its raw output. Stop if the runtime is available.
- Confirm the retained Aider version and every required option from installed
  `aider --help` before starting. Stop if an option is absent or has materially
  different behavior.
- Confirm no repository-local Aider configuration, attached source file,
  browser feature, tool/function mode, cache, history, analytics, update check,
  auto-commit, lint, test, file-watch, or retry behavior is enabled.

### Receiver

- Confirm the shared clean revision.
- Confirm no ordinary receiver is already running unexpectedly.
- Confirm the receiver runtime and required local model are available and
  callable through its own operator-managed procedure.
- Confirm the existing local health observation reports availability without
  retaining raw output:

  ```sh
  uv run home-ai-cluster-health
  ```
- Confirm the receiver bind and firewall allowance are explicitly limited to
  the trusted LAN.

### Network

- Confirm only the minimum caller-to-declared-receiver reachability required by
  the ordinary trusted-LAN workflow.
- Confirm the receiver is not exposed beyond that trusted LAN.
- Confirm port 8001 is not reachable from the receiver or other LAN machines.
- Do not use packet capture or retain network-command output.

## 10. Receiver preparation

Prepare the runtime and its chat-capable model through the runtime's existing,
operator-managed procedure. Home AI Cluster does not install, download, start,
stop, supervise, repair, or discover it.

Start one ordinary receiver using the existing trusted-LAN bind and port chosen
by the operator. The ordinary receiver workflow documents this form:

```sh
uv run uvicorn home_ai_cluster.main:app --host 0.0.0.0 --port <RECEIVER_PORT>
```

Restrict any firewall allowance to the trusted LAN and remove it during
cleanup. This receiver exposes the ordinary internal cluster request shape; it
does not expose the compatibility endpoint and does not know the caller's
topology.

## 11. Caller preparation

Leave the caller's default local runtime stopped or otherwise unavailable before
the request. Do not create the required condition by editing code, injecting an
exception, changing a firewall during execution, or stopping a runtime after a
request begins.

The `home-ai-cluster-health` observation in the preflight checklist is the
required local check. Its availability result establishes the intended
pre-request condition; it does not route a request or contact the receiver.

## 12. Declaration preparation

Create one temporary, operator-owned declaration outside repository content. It
contains topology only and exactly one remote:

```toml
[[remote_nodes]]
node_id = "<REMOTE_NODE_ID>"
base_url = "http://<RECEIVER_ADDRESS>:<RECEIVER_PORT>"
```

Do not retain the real file, path, address, or contents. Do not add runtime,
adapter, model, credential, lifecycle, or client settings. Validate it using
the preflight command before starting the compatibility process. Invalid or
unreadable declarations are CLI startup failures, not compatibility HTTP
responses; stop without binding the listener.

## 13. Aider bounded configuration

Use the exact retained Phase 6 configuration categories and option names. The
temporary Aider model-settings file contains only this client-side model entry:

```yaml
- name: openai/home-ai-cluster
  edit_format: whole
  use_temperature: false
```

Keep that file outside the repository and remove it during cleanup. `whole`
preserves the non-function path; `use_temperature: false` prevents an
unsupported generation field.

Use this command shape once, with all placeholders resolved only locally:

```sh
aider --model openai/home-ai-cluster \
  --openai-api-base http://127.0.0.1:8001/v1 \
  --openai-api-key <NON_SECRET_PLACEHOLDER> \
  --model-settings-file <AIDER_MODEL_SETTINGS_FILE> \
  --no-stream --no-git --no-auto-commits --dry-run \
  --no-analytics --no-check-update --no-gitignore \
  --input-history-file <NULL_HISTORY_TARGET> \
  --chat-history-file <NULL_HISTORY_TARGET> \
  --env-file <NULL_HISTORY_TARGET> \
  --message "<ONE_HARMLESS_MESSAGE>"
```

Do not enable `--cache-prompts`, an LLM-history file, attached files, a browser,
linting, tests, file watching, tools, functions, model discovery, aliases, or
any extra completion parameter. Run it only in a harmless temporary or empty
working context. Before execution, verify with installed Aider help that no
additional enabled default can produce analytics, updates, history, cache,
git mutation, tool use, browser use, or a retry. If that cannot be established,
stop rather than guessing an option.

## 14. Strict startup order

Follow this order without a wrapper script or service manager:

1. Record sanitized revision and role facts.
2. Confirm both working trees are clean.
3. Prepare the receiver runtime and model.
4. Start the ordinary receiver.
5. Complete existing privacy-safe receiver readiness checks.
6. Confirm caller-local runtime unavailability.
7. Validate the one-remote declaration locally.
8. Start the caller compatibility process:

   ```sh
   uv run home-ai-cluster-openai-compatibility --declaration <DECLARATION_PATH>
   ```

9. Verify it listens only on `127.0.0.1:8001`.
10. Prepare the temporary Aider configuration.
11. Pass the observation gate in section 16.
12. Perform exactly one Aider submission only if that gate passes.
13. Collect only the bounded observations in section 16.
14. Stop the compatibility process.
15. Stop the receiver.
16. Remove temporary Aider and declaration material and verify clean
    repositories.

## 15. Single-request execution

Invoke the configured Aider command exactly once. It must send one accepted
`POST /v1/chat/completions` request to the caller-local endpoint and receive
one completed response. Do not submit a second message, retry, call the
receiver directly, use curl, use `home-ai-cluster-chat`, make a native request,
or make a model-list, metadata, tool, or source-edit request.

Stop the attempt if Aider emits an extra request, a retry, `GET /v1/models`, a
tool definition or call, streaming, an unsupported field, or a request to any
target other than the caller-local compatibility endpoint.

## 16. Bounded observations

The later proof needs bounded operator facts only: process roles, one request
count, sanitized declared node ID, response completion, success/failure class,
and the internal normalized result attribution. It must not add a public debug
route, logging hook, routing history, raw request/response capture, declaration
logging, packet capture, or a custom compatibility response field.

### Observation gate — current blocker

Before any Aider submission, identify an already existing, privacy-safe,
bounded observation seam that can establish both the one-request count and the
caller-owned internal `ClusterResult` attribution to `<REMOTE_NODE_ID>` for the
live compatibility process.

At the time this runbook was written, the merged RFC-0046 process exposes no
such operator-facing seam. RFC-0031 intentionally omits node and routing fields
from its public response; `home-ai-cluster-status` observes readiness rather
than an executed request; and the native one-shot client is not an Aider
substitute. The retained Phase 6 inspection proxy is also not an acceptable
substitute here because this runbook prohibits a proxy and raw request capture.

Therefore, do not execute section 15 until an existing accepted observation
seam has been identified and documented without changing code, the public
response, or privacy boundaries. If none exists, stop the proof before the
Aider submission and record the blocker as the outcome. Do not invent an
observation contract or treat compatibility success alone as proof of remote
attribution.

If the gate later passes, retain only sanitized structural observations: request
count, whether compatibility completed, a success/failure class, and the
declared node ID. Never retain prompt, response content, raw transport data,
or topology details.

## 17. Success criteria

A successful later proof requires all of the following:

1. both machines use the same clean revision;
2. the receiver runtime is available before the request;
3. the caller runtime is unavailable before the request;
4. one accepted declaration starts the compatibility process;
5. the compatibility listener remains loopback-only;
6. Aider addresses only the caller-local compatibility endpoint;
7. exactly one RFC-0031-compatible request occurs;
8. no model-list, metadata, tool, streaming, or retry request occurs;
9. the request enters ordinary static-cluster routing;
10. local-first evaluation occurs and its unavailable local candidate meets the
    accepted pre-execution fallback condition;
11. bounded traversal selects the declared remote and the receiver executes it;
12. the caller-owned internal normalized result is attributed to the declared
    node through the observation gate;
13. Aider receives one unchanged successful compatibility response;
14. Aider supplied no topology, node, runtime, adapter, model, declaration,
    routing, or fallback selector; and
15. no sensitive proof data is retained.

## 18. Failure and stop criteria

Stop without retry if revisions differ, either tree is dirty, a declaration is
invalid, either required port is occupied, the compatibility listener binds
beyond loopback, the caller runtime is available, the receiver runtime or model
is unavailable, trusted-LAN reachability fails, or the observation gate fails.

Also stop for an unsupported Aider field, streaming, model discovery, tools,
retry, more than one request, direct receiver access, fallback after execution
begins, a custom public routing field, missing remote attribution, or any need
to retain private data to make a claim. Do not repair, reconfigure, patch, or
retry during the same recorded attempt.

## 19. Cleanup

After a stopped or completed attempt:

1. stop Aider;
2. stop the compatibility process;
3. stop the ordinary receiver;
4. remove the trusted-LAN firewall allowance;
5. leave the caller runtime unavailable unless the operator independently
   chooses to restore it;
6. remove temporary Aider settings, history, and cache material if any exists;
7. remove the temporary declaration; and
8. confirm neither repository has tracked or untracked proof artifacts and
   both working trees are clean.

Do not claim cleanup that cannot be checked. Retain a separate sanitized proof
document only after a successful attempt has been reviewed.

## 20. Privacy-safe retained proof template

Use only this bounded template after success:

```text
Execution date:
Shared repository commit SHA:
Physical caller and receiver roles confirmed:
Trusted-LAN boundary confirmed:
One declared remote node confirmed:
Receiver runtime available before request:
Caller runtime unavailable before request:
Compatibility listener loopback-only:
Aider version and bounded configuration categories confirmed:
One compatibility request observed:
No unsupported or preliminary request observed:
Existing observation seam used:
Caller-owned declared-node attribution: <REMOTE_NODE_ID>
Compatibility response completed without public routing extension:
Cleanup checks completed:
Outcome:
```

Do not append addresses, paths, prompt or response content, source context,
credentials, raw command output, declaration data, or raw logs.

## 21. Operator checklist

- [ ] Two physical machines on one trusted LAN only.
- [ ] Same clean merged revision on both machines.
- [ ] One temporary one-remote declaration validated locally.
- [ ] Receiver runtime/model available and ordinary receiver started.
- [ ] Caller runtime unavailable before request.
- [ ] Compatibility command started with `--declaration` on loopback only.
- [ ] Aider v0.86.0-style bounded configuration verified from installed help.
- [ ] No source attachment, cache, history, analytics, updates, git mutation,
  lint, test, browser, tool, function, model discovery, or retry behavior.
- [ ] Existing privacy-safe observation gate passed before submission.
- [ ] Exactly one Aider submission made.
- [ ] Stop conditions observed if any requirement failed.
- [ ] Processes, temporary files, firewall allowance, and artifacts cleaned up.

## 22. Explicit non-goals

This runbook does not introduce or prove general Aider support, repository
editing, automatic commits, tool/function calling, streaming, model discovery,
aliases, multiple requests, retries, multiple remotes, load balancing,
scheduling, discovery, supervision, lifecycle or installation automation,
authentication, encryption, LAN-facing compatibility access, production
readiness, performance, another capability, a generic integration framework,
or a new formal roadmap phase.

It does not change any command, configuration schema, request/response
contract, routing policy, fallback classification, transport, runtime adapter,
receiver behavior, or public attribution boundary.
