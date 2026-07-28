# Ordinary Daily-Use Friction Investigation

Status: Complete

## Context

This standalone documentation-only investigation evaluates ordinary daily use after the retained remote `summarize --file` proof. It examines only current accepted local-only operation and explicit static-cluster operation with one caller and one receiver. It does not propose an accepted decision, implementation, Phase 19 work, or a new operating surface.

## Current accepted boundaries

The ordinary root command separates finite request and inspection commands from foreground process commands. External runtimes remain operator-owned. Local-only operation is the default path; static-cluster operation is explicit, declaration-owned, local-first, and requires one caller process plus each receiving ordinary local process.

Current boundaries include one foreground ordinary local or static-cluster process; fixed ordinary caller loopback request targets; explicit static declarations without discovery or automatic lifecycle; finite preflight, health, and status observations with separate meanings; one-shot `chat` and `summarize` requests to an already-running ordinary process; and bounded summarize sources through `--text`, stdin, or one regular UTF-8 `--file`.

They intentionally do not provide process supervision, PID files, service installation, a universal start command, configurable caller ports, or automatic runtime lifecycle.

## Investigation questions

Does accepted current operation make routine local and one-caller/one-receiver use materially difficult? This investigation evaluates preparation, runtime ownership, process and terminal needs, fixed ports, declaration reuse, inspection sequencing, repeated requests, shutdown, recovery, and documentation consistency.

## Local-only workflow observations

Once an external runtime is available, the repeated local path is short:

1. start the operator-owned runtime;
2. use `hac health` when a finite local runtime observation is useful;
3. start `hac local` in the foreground;
4. issue repeated finite `hac chat` or `hac summarize` requests; and
5. stop the foreground process normally.

No declaration or remote reachability is required. The client is topology-blind, and a repeated request does not require a restart while the process and runtime remain usable.

Observed friction is limited to the deliberate separation between runtime ownership and application startup: the operator prepares the runtime and keeps one foreground application process available. That is an accepted boundary, not evidence that supervision is required.

## Static-cluster workflow observations

One caller and one receiver add bounded, explicit preparation:

1. prepare the receiver runtime and start one ordinary trusted-LAN `hac local` process;
2. retain and reuse one explicit caller declaration containing the declared node ID and base URL;
3. use `hac preflight --declaration <DECLARATION_PATH>` for static coherence;
4. use `hac status --declaration <DECLARATION_PATH>` when a finite receiver observation is useful;
5. start one foreground `hac static-cluster --declaration <DECLARATION_PATH>` caller; and
6. send repeated ordinary `chat` or `summarize` requests to the caller.

The declaration is reusable operator-owned state, loaded at caller startup. It is not disposable proof material, capability configuration, a runtime configuration file, or remote lifecycle authority. A usable local runtime normally wins under local-first routing; a declared receiver alone does not imply remote execution.

Observed friction is procedural: caller and receiver roles need separate foreground processes and an explicit stop order. The retained remote summarize-file proof confirms this accepted composition works without a proof-only request client or topology selector.

## Process and port observations

Ordinary process commands are foreground-bound. The local process accepts explicit host and port inputs; the static-cluster caller owns its fixed loopback port. An occupied port is therefore a startup precondition, not a routing, runtime-health, or declaration failure.

The canonical workflow identifies process and port ownership, but daily use requires an operator to connect three facts: the static caller is fixed and loopback-only; the receiver needs an explicit trusted-LAN bind; and an occupied port is resolved through normal operator process control before startup. The retained proof used transient availability checks and ordinary cleanup. This does not establish a need for configurable ports, PID files, supervision, or a service manager.

## Input-mode observations for chat and summarize

Repeated `chat` requests accept one message through the existing positional or `--message` form and use the already-running ordinary process.

Repeated `summarize` requests have three intentionally narrow source forms:

| Source | Ordinary use | Boundary |
| --- | --- | --- |
| `--text <TEXT>` | One explicit supplied source | Ignores stdin |
| stdin | One bounded UTF-8 stream with no explicit source | Pipeline or redirection |
| `--file <PATH>` | One bounded caller-local regular UTF-8 file | Reads only that file |

All summarize sources share one request/result/output path after local validation. They do not add document parsing, multiple files, remote path access, or source retention. Default content is suitable for routine reading; `--verbose` and `--json` retain their existing attribution and structured-result roles.

The documentation-sensitive point is precedence: explicit `--text` or `--file` intentionally leaves inherited stdin unread. This is documented behavior, not a command-contract ambiguity.

## Preflight, health, and status sequencing

| Command | Current purpose | Does not establish |
| --- | --- | --- |
| `hac preflight` | Static declaration coherence | Runtime or network availability |
| `hac health` | Local runtime observation | Remote reachability or static-cluster state |
| `hac status --declaration <DECLARATION_PATH>` | Finite local/declared-remote observation | Routing, process startup, or successful request |

Health is useful before local startup or while diagnosing the local runtime. Preflight is useful when a declaration changes or before a static caller restart. Status is useful when a receiver is involved and a bounded readiness observation is needed; it is not a prerequisite for every repeated request.

The current workflow states these distinctions, but they are distributed across the canonical workflow and command reference. A concise daily-use reminder could prevent treating preflight as a network check or health as a remote-cluster check.

## Recovery from realistic mistakes

Current accepted recovery remains small and manual:

- repair or start an unavailable external runtime, then rerun the relevant finite observation;
- correct an invalid retained declaration, then rerun preflight;
- check declaration and receiver process before calling an unreachable receiver a network fault;
- stop a conflicting process through ordinary operator control before retrying startup;
- do not change topology merely to force a remote result when local-first selects local;
- correct invalid local summarize input before expecting a network request; and
- investigate unexpected request failure rather than treating a second request as an accepted retry.

None of these observations establishes a missing supervisor, topology controller, retry policy, or automatic repair system.

## Documentation overlap or inconsistencies

The canonical workflow is procedural authority; the command reference is lookup authority. Both describe the same ordinary commands, but their separation creates small documentation friction:

- the workflow carries start/check/stop sequence and receiver-role detail, while the reference carries concise option and fixed-boundary detail;
- proof runbooks provide physical-machine evidence but are not daily-use procedures;
- the retained remote summarize proof is evidence, not a replacement for current operator documentation; and
- installed-command and checkout `uv run` examples are both valid, so an operator must recognize which context a document uses.

No contradiction in accepted command behavior was found. The friction is discoverability and role separation, not incompatible instructions.

## Observed versus hypothetical friction

### Observed friction

- Static operation requires two role-specific foreground processes and explicit manual cleanup.
- Fixed ports require resolving a conflict before startup.
- The three inspection commands have distinct scopes.
- Guidance is distributed across a workflow, command lookup page, and historical proof material.

### Documentation friction

- The distinction between “start once, then send repeated requests” and proof-only preparation is not in one compact comparison.
- Fixed caller-versus-receiver port ownership and inspection scope require cross-reading.
- The documentation index correctly distinguishes roles, but historical proof links are numerous enough that a new operator can mistake evidence for current workflow.

### Hypothetical friction

Process supervision, PID files, service installation, configurable ports, a universal start command, automatic runtime repair, and a generic configuration framework could reduce manual steps. No observed evidence establishes that any is necessary or appropriate.

### Implementation friction

No implementation defect or missing accepted behavior was found. The retained proof and current command contracts support both examined paths.

### Architectural questions

No new architectural question was found. If repeated real daily use later establishes that operators cannot reliably control accepted foreground process and fixed-port boundaries with current documentation, the question would be whether a new operator lifecycle surface is justified. That would require a later RFC before design or implementation.

## Candidate follow-up categories

1. **Documentation maintenance:** clarify daily start/check/request/stop sequencing, fixed-port ownership, and when each finite inspection is useful. No RFC is required.
2. **Operator evidence collection:** gather repeated real daily-use observations before inferring a durable product gap. No RFC is required.
3. **Possible later architectural investigation:** only if repeated evidence identifies a bounded lifecycle or startup authority gap. That question would require an RFC before a decision or implementation.

## RFC classification

This investigation makes no architectural decision. The observed issues are documentation and procedure discoverability only, so no RFC is required for its conclusion or for documentation maintenance. A future operator-surface change affecting process lifecycle, port ownership, startup authority, or configuration would be architectural and would require a separate RFC.

## Conclusion

**Outcome B — documentation or wording friction only.**

The accepted local-only and one-caller/one-receiver static workflows are usable once role boundaries are understood. The real remote `summarize --file` proof demonstrates that existing ordinary surfaces compose successfully. The material daily-use opportunity is clearer navigation and wording around process roles, fixed ports, inspection scope, and separation between current workflow and historical proof evidence—not a new command, lifecycle mechanism, or architectural change.
