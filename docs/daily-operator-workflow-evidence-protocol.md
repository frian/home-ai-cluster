# Daily Operator Workflow Evidence Protocol

Status: Evidence protocol

This is not retained proof that an exercise succeeded. It does not establish
Phase 17 or make an architectural decision. Record observations only after a
real operator executes this protocol; this document contains no live result.

## 1. Evidence question

> What concrete manual work remains when one operator prepares, inspects,
> starts, uses, recovers, and stops one receiving role and one calling role
> through the accepted ordinary static-cluster workflow?

The purpose is to distinguish real repeated operator friction from one-time
environment preparation, external runtime ownership, Home AI Cluster process
lifecycle, client-specific work, and documentation discoverability problems.

## 2. Scope

The core exercise includes exactly:

- one receiving machine;
- one calling machine;
- one explicitly selected retained static-cluster declaration;
- one externally owned runtime on the receiving machine;
- caller-local runtime unavailable or intentionally unused when a real remote
  request needs to be observed;
- one ordinary native static-cluster request; and
- optional compatibility/Aider observations only as a separately marked
  extension.

The core exercise does not depend on Aider. Exclude more than one remote,
discovery, remote process control, daemonization, `systemd`, Docker,
Kubernetes, runtime or model-download automation, service generation, process
detachment, new configuration, code changes, performance benchmarking, and
prompt or answer evaluation.

## 3. Privacy rules

Do not retain real IP addresses, hostnames, usernames, absolute local paths,
prompts, generated responses, model content, raw logs, authorization values,
API keys, shell history, process IDs, or machine-specific hardware facts.

Use placeholders such as `<RECEIVER_ADDRESS>`, `<DECLARATION_PATH>`, and
`<DECLARED_REMOTE_NODE_ID>`. An operator may inspect sensitive values during
the session but must not copy them into repository evidence.

## 4. Repository-derived baseline inventory

`uv sync`, repository checkout, runtime installation, and model acquisition are
environment preparation, not ordinary per-session commands, unless a real
session requires repair. The baseline below records current repository behavior
only; it is not a measured session count.

| Command or process | Machine role | Purpose | Duration and foreground behavior | Explicit and retained inputs | Bind/port and runtime ownership | Current stop method |
| --- | --- | --- | --- | --- | --- | --- |
| External receiving runtime | Receiving | Serve the receiver's local model | Runtime-defined, operator-managed process | Runtime-specific operator inputs; model availability is external | Runtime-defined; Home AI Cluster does not own it | Operator's runtime procedure |
| `home-ai-cluster-preflight --declaration <DECLARATION_PATH>` | Caller; optional receiver local-only form | Read-only declaration/static coherence | Finite; terminal reusable after exit | Declaration path when used; declaration is retained operator input | No listener; owns no runtime | Exits itself |
| `home-ai-cluster-health` | Receiving or caller | One local default-adapter observation | Finite; terminal reusable after exit | No CLI input | No listener; owns no runtime | Exits itself |
| `home-ai-cluster-local --host 0.0.0.0 --port 8000` | Receiving | Ordinary receiving native application | Long-running, foreground | Optional runtime-composition inputs; host and port are supplied for trusted-LAN exposure | Defaults to `127.0.0.1:8000`; explicit receiver example uses `0.0.0.0:8000`; owns no external runtime | Normal interruption |
| `home-ai-cluster-status --declaration <DECLARATION_PATH>` | Caller | One finite local and declared-remote status observation | Finite; terminal reusable after exit | Declaration path; optional selected local runtime inputs | No listener; owns no runtime | Exits itself |
| `home-ai-cluster-static-cluster --declaration <DECLARATION_PATH>` | Caller | Ordinary static local-plus-remote native application | Long-running, foreground | Declaration path; optional selected local runtime inputs | Fixed loopback `127.0.0.1:8000`; owns no external runtime | Normal interruption |
| `home-ai-cluster-chat --message <MESSAGE>` | Caller | One native request to an already-running ordinary process | Finite; terminal reusable after exit | One non-empty message; sensitive and not retained | Fixed caller loopback native endpoint; owns no runtime | Exits itself |
| `home-ai-cluster-openai-compatibility --declaration <DECLARATION_PATH>` | Caller, optional | Separate narrow compatibility application | Long-running, foreground | Declaration path | Fixed loopback `127.0.0.1:8001`; owns no external runtime | Normal interruption |
| Aider | Caller, optional external client | Bounded compatibility client only | Client-defined; outside core count | Temporary client-side settings and message | Targets caller compatibility loopback endpoint; outside Home AI Cluster runtime ownership | Stop client and remove temporary settings |

## 5. Counting rules

### Command count

Count every explicit shell command entered during the measured session. Record
environment-preparation, inspection, startup, request/client, recovery, and
shutdown commands separately. Do not count commands shown only as explanatory
alternatives.

### Foreground-process and terminal count

Record the maximum simultaneous long-running Home AI Cluster processes, the
maximum simultaneous externally owned runtime processes directly managed for
the exercise, and the maximum terminals needed when long-running processes stay
foreground-bound. A terminal may be reused after a finite command exits; one
process does not automatically mean one permanent terminal.

### Repeated values

Count a value when the operator supplies or recovers the same logical fact more
than once. Classify it as retained operator configuration, current network fact,
fixed project contract, command-specific input, temporary client configuration,
or sensitive value that must not be retained. Record the category, never the
real value.

### Recovery event

A recovery event is one manual action needed after an expected or intentionally
induced partial failure before the workflow continues. Do not induce destructive,
unsafe, or privacy-sensitive failures.

## 6. Core exercise prerequisites

- [ ] Both machines use the same current repository revision.
- [ ] Dependencies are synchronized.
- [ ] The trusted-LAN boundary is understood.
- [ ] The receiving runtime and required model are already installed.
- [ ] A valid operator-owned declaration already exists.
- [ ] No sensitive value will be retained.
- [ ] The operator knows normal interruption for foreground processes.

These are prerequisites, not measured successful workflow steps unless a real
session requires repair.

## 7. Receiver role exercise

For each numbered step, leave these fields blank until execution:

```text
Entered command: yes/no
New foreground process: yes/no
New terminal required: yes/no
Repeated value supplied: none / category
Recovery required: yes/no
Operator note: one privacy-safe sentence
```

1. Observe whether the external runtime is already running.
2. Start it manually only if required, using its operator-owned procedure.
3. Run ordinary static preflight where applicable:

   ```sh
   uv run home-ai-cluster-preflight
   ```

4. Run the local health observation:

   ```sh
   uv run home-ai-cluster-health
   ```

5. Start the ordinary receiving application with explicit trusted-LAN exposure:

   ```sh
   uv run home-ai-cluster-local --host 0.0.0.0 --port 8000
   ```

6. Verify that the application started without retaining its private address.
7. Keep the receiving application foreground-bound for the exercise.
8. Later stop it with normal interruption.
9. Separately decide whether to leave or stop the external runtime according to
   operator policy.

## 8. Caller role exercise

Use the same blank observation fields for every numbered step.

1. Confirm the caller-local condition required for the remote observation. If a
   remote result is intended, the local runtime must already be unavailable or
   intentionally unused before request transmission.
2. Run declaration-aware static preflight:

   ```sh
   uv run home-ai-cluster-preflight --declaration <DECLARATION_PATH>
   ```

3. Run explicit static-cluster status:

   ```sh
   uv run home-ai-cluster-status --declaration <DECLARATION_PATH>
   ```

4. Start ordinary static-cluster operation from the retained declaration:

   ```sh
   uv run home-ai-cluster-static-cluster --declaration <DECLARATION_PATH>
   ```

5. Keep the caller process foreground-bound.
6. Send one ordinary request:

   ```sh
   uv run home-ai-cluster-chat --message "<OPERATOR_SUPPLIED_MESSAGE>"
   ```

7. Record only whether the request succeeded and whether the existing result
   attribution indicated `<DECLARED_REMOTE_NODE_ID>`; do not retain the message
   or generated content.
8. Stop the calling process with normal interruption.

Do not add `--proof-observation` to this native core exercise. Native result
attribution is the existing privacy-safe observation boundary for this purpose.

## 9. Optional compatibility extension

This is optional and outside the native core total. If used, record separate
counts for work needed to stop or avoid a conflicting native caller, start
`home-ai-cluster-openai-compatibility --declaration <DECLARATION_PATH>`, send
one direct compatibility request, optionally configure the bounded Aider client
proof, clean up temporary client settings, and stop the compatibility process.

Do not merge these counts into the core total or claim general Aider support.

## 10. Safe recovery observations

Record only failures safely encountered, or one explicitly safe failure chosen
by the operator. Do not deliberately create every case and do not retain raw
errors or private facts.

| Normalized category | Detected at step | Owning domain | Manual recovery action category | Documentation already explained it? | Would another command or architecture have helped? |
| --- | --- | --- | --- | --- | --- |
| Occupied port at startup |  | Home AI Cluster process |  |  |  |
| Invalid declaration in preflight |  | Retained configuration |  |  |  |
| Receiving application unavailable in status |  | Network |  |  |  |
| Receiving runtime unavailable |  | External runtime |  |  |  |
| Caller-local runtime unexpectedly usable |  | External runtime |  |  |  |
| Wrong process still running |  | Home AI Cluster process |  |  |  |
| Forgotten temporary client configuration |  | Client |  |  |  |

## 11. Results worksheet

Leave every field uncompleted until a real session.

### Native core totals

```text
Receiver finite commands:
Receiver startup commands:
Caller finite commands:
Caller startup commands:
Native request commands:
Shutdown actions:
Recovery commands:
Maximum simultaneous Home AI Cluster foreground processes:
Maximum simultaneous externally owned runtime processes:
Maximum terminals:
Repeated retained values:
Repeated reconstructed values:
Temporary values:
Observed partial failures:
```

### Optional compatibility totals

```text
Additional commands:
Additional long-running process:
Additional terminal:
Temporary client files or settings:
Cleanup actions:
```

### Qualitative observations

- Which step required repository-specific memory?
- Which step required internal application knowledge?
- Which repeated value was not already retained safely?
- Which inspection command gave actionable information?
- Which command duplicated information already known?
- Was foreground operation sufficient? Was process detachment actually desired?
- Was normal interruption sufficient for shutdown? Was a PID needed?
- Would a stop command have prevented an observed problem?
- Would shorter documentation have removed the main friction?
- Did receiver and caller need different local-role commands?
- Did any friction justify remote lifecycle authority or Home AI Cluster runtime
  ownership?

## 12. Interpretation rules

- If friction is command discoverability and no lifecycle recovery problem is
  observed, improve documentation before proposing lifecycle code.
- If one local role requires internal module knowledge but foreground
  interruption is sufficient, investigate a narrow foreground role command.
- If detached operation is not needed, do not introduce PID files, lifecycle
  state, or stop commands.
- If foreground interruption is sufficient, keep stop semantics outside a first
  RFC.
- If retained declarations already cover repeated facts, do not create another
  configuration file. If repeated facts have different owners, do not combine
  them into generic configuration.
- If optional Aider work dominates only the extension, keep it client-side.
- No result may justify remote startup, remote shutdown, or external-runtime
  ownership in a first increment.

## 13. Completion boundary

The protocol is complete when its repository-derived baseline is reviewed, the
exercise sheet works without repository archaeology, privacy and counting rules
are explicit, and the blank results worksheet is ready for a real operator
session. It must not fabricate a live result or select architecture.

After a real session, retain results in a separate documentation-only PR. Do not
put observations in this protocol PR unless André explicitly supplies them.
