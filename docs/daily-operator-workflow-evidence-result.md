# Daily Operator Workflow Evidence Result

Status: Retained operator evidence

## 1. Purpose and limits

This record retains privacy-safe observations from one real native two-machine
operator exercise using the accepted ordinary static-cluster workflow.

It is not a Phase 17 decision, RFC, implementation plan, general performance
proof, compatibility or Aider proof, or evidence of production readiness. It
does not select an architectural direction.

## 2. Exercise scope

The exercise used one receiving machine, one calling machine, one retained
single-remote static-cluster declaration, one externally owned receiving
runtime, one ordinary receiving application, one ordinary static-cluster caller,
and one native request. The caller-local runtime was not running.

No compatibility process or Aider client was used. The exercise did not cover
multiple remotes, discovery, remote process control, daemonization, detached
processes, service managers, runtime automation, or performance.

## 3. Privacy handling

This record retains no real address, hostname, username, absolute path, prompt,
generated response, model content, authorization value, API key, process ID,
raw log, shell history, or machine-specific hardware fact. It uses placeholders
such as `<DECLARATION_PATH>`, `<RECEIVER_ADDRESS>`, and
`<DECLARED_REMOTE_NODE_ID>` where needed.

## 4. Initial conditions

Both machines used repository commit:

```text
f7508f55613f5671ab1df7ab9add03dcf18dd486
```

On the receiving machine, the external runtime was already running and no Home
AI Cluster process was running. On the calling machine, the local runtime was
not running and no Home AI Cluster process was running.

Repository and dependency synchronization occurred before the measured core
exercise and are not included in its totals.

## 5. Receiver observations

The operator ran:

```sh
uv run home-ai-cluster-preflight
uv run home-ai-cluster-health
```

Preflight succeeded with a coherent static report. Health succeeded and observed
a healthy runtime. No recovery was required.

The ordinary receiving role then started with explicit trusted-LAN exposure:

```sh
uv run home-ai-cluster-local --host 0.0.0.0 --port 8000
```

Startup succeeded. One foreground Home AI Cluster process ran and listened on
all interfaces at port `8000`; the real address and process ID are not retained.
No recovery was required.

## 6. Declaration recovery event

The initial single-remote declaration contained an unknown key. The operator ran:

```sh
uv run home-ai-cluster-preflight --declaration <DECLARATION_PATH>
```

It failed with the normalized category `invalid declaration`. This was the only
observed recovery event.

The accepted single-remote declaration required these root keys:

```toml
remote_node_id = "<DECLARED_REMOTE_NODE_ID>"
remote_base_url = "http://<RECEIVER_ADDRESS>:8000"
```

The owning domain was retained operator configuration. The operator recovered by
rewriting the declaration to the accepted schema. Clearer declaration
documentation would have prevented or shortened that recovery; no new
architecture was required. The actual path, node identity, address, and file
contents are not retained.

## 7. Caller observations

After correction, the operator ran:

```sh
uv run home-ai-cluster-preflight --declaration <DECLARATION_PATH>
uv run home-ai-cluster-status --declaration <DECLARATION_PATH>
```

Declaration preflight succeeded and status was coherent. The caller-local runtime
was unavailable, the declared receiver application was reachable, and the
declared receiver runtime was available. No further recovery was required.

Before correction, status had reported the receiver application as unreachable
and its runtime status as unknown. That sequence does not prove a network fault:
the receiver was later confirmed listening correctly, and the retained
configuration was corrected before the successful status observation.

The operator started the caller with:

```sh
uv run home-ai-cluster-static-cluster --declaration <DECLARATION_PATH>
```

Startup succeeded, one foreground Home AI Cluster caller process ran, and no
recovery was required.

## 8. Native request observation

In another available terminal, the operator ran exactly one native request:

```sh
uv run home-ai-cluster-chat --message "<OPERATOR_SUPPLIED_MESSAGE>"
```

The request succeeded and its result attribution indicated the declared
receiver. No recovery was required. The supplied message and generated response
are not retained.

## 9. Shutdown observations

The operator stopped the foreground caller and receiver processes with normal
interruption. Normal interruption was sufficient for both roles, no PID was
needed, and no recovery was required. The external receiving runtime remained
separately operator-owned.

## 10. Measured counts

### Native core

```text
Receiver finite inspection commands: 2
Receiver startup commands: 1
Caller finite inspection commands: 2
Caller startup commands: 1
Native request commands: 1
Shutdown actions: 2
Recovery commands: 1
Maximum simultaneous Home AI Cluster foreground processes: 2
Maximum simultaneous externally owned runtime processes: 1
Maximum terminals: 3
Observed partial failures: 1
```

The shutdown actions were normal interruptions, not separate shell commands.

### Environment preparation

Repository synchronization and dependency synchronization occurred before the
measured core exercise. They are not merged into the native core totals.

## 11. Repeated values and retained configuration

The declaration path was supplied to declaration-aware preflight,
static-cluster status, and static-cluster startup. It is retained operator
configuration.

The receiver address and declared node identity were retained inside the
declaration rather than re-entered for each command.

## 12. Qualitative findings

- Repository-specific memory was required to know the accepted declaration
  schema.
- The declaration schema error was the only observed recovery event.
- Preflight gave actionable feedback before startup.
- Status gave useful live reachability and runtime information.
- Foreground operation was sufficient, and process detachment was not desired.
- Normal interruption was sufficient for both Home AI Cluster roles; no PID was
  needed.
- A stop command would not have prevented the observed problem.
- Shorter, clearer declaration documentation would likely have prevented or
  shortened the only recovery.
- Receiver and caller require distinct explicit local role commands.
- No observed friction justified remote lifecycle authority or Home AI Cluster
  ownership of the external runtime.

One exercise cannot prove that detached operation or stop behavior will never be
useful. It shows only that both were unnecessary in this measured session.

## 13. Interpretation

This evidence supports attention to documentation and command discoverability
before lifecycle automation. The declaration format is concrete documentation
friction. The repeated declaration path is measurable but does not by itself
justify a new configuration layer.

For this workflow, foreground startup plus normal interruption provided a
complete bounded lifecycle. There is no evidence here for PID files, detached
processes, a stop command, supervision, service-manager integration, remote
startup, remote shutdown, or runtime lifecycle ownership.

Any future command-surface proposal still requires an RFC when it changes
accepted startup or lifecycle behavior. This evidence should inform the next
roadmap decision; it does not conclude that no Phase 17 is needed.

## 14. Decision boundary

This result may justify a documentation improvement and may justify
investigating a narrower foreground role-command surface. It does not select
either option.

This PR must not add Phase 17. Any architectural startup or lifecycle decision
requires an RFC first.
