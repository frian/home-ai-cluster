# RFC-0117: Bounded Workspace-Aware Code Operator Surface

Status: Accepted

Date: 2026-09-10

## Context

Accepted RFC-0116 defines, and the product implements, one bounded workspace-aware Code interaction. It deliberately leaves the first human/operator-facing spelling and foreground presentation open.

Today, ordinary `hac code` remains RFC-0067 textual Code assistance, including RFC-0088's no-message textual conversation. `hac code-file` remains the separate RFC-0080/RFC-0081 one-target caller edge. The RFC-0116 composition is not directly invokable by an operator.

The missing decision is neither filesystem authority, action grammar, routing, nor agent architecture. It is only:

> What is the smallest explicit CLI surface by which an operator can construct one ephemeral RFC-0116 interaction with a trusted workspace root and grants, using the existing ordinary HAC Code execution path?

## Proposal

Add exactly one dedicated authority-bearing foreground command:

```text
hac code-workspace --root PATH --grant OP [--grant OP ...] MESSAGE
hac code-workspace --root PATH --grant OP [--grant OP ...] --message MESSAGE
```

`OP` is exactly one of `list`, `read`, or `write`. This command is the first operator surface for the closed RFC-0116 interaction. It does not alter `hac code`, no-message interactive Code, browser Code, `/v1/chat`, `code-file`, or `capability=code`.

The dedicated command keeps workspace authority visible and explicit. It does not hide a semantically different authority-bearing mode inside ordinary textual `hac code`. No aliases or short-option spellings are introduced.

## Public invocation contract

### Initial message

Each invocation contains exactly one non-blank initial coding instruction from exactly one source:

1. one positional `MESSAGE`; or
2. one `--message MESSAGE`.

The positional form and `--message` together are invalid. More than one `--message`, no message, and blank or whitespace-only message are invalid. There is no no-message interactive mode and no human follow-up input. One invocation starts one RFC-0116 foreground interaction only.

This freezes the established `hac code` and `code-file` one-shot message convention for the new caller edge.

### Root

Every invocation requires exactly one explicit `--root PATH`. There is no default root. The command must not infer current directory, repository root, home directory, filesystem root, a retained workspace, or a path from the initial instruction. `--root .` is valid because it is an explicit trusted host-path value, rather than an implicit default. Repeated `--root` is invalid rather than last-one-wins.

After local CLI syntax validation, the supplied root is passed to the existing RFC-0116 composition and RFC-0114 `WorkspaceAuthority`. RFC-0114 remains authoritative for root validity and filesystem/path semantics. The model does not choose, and need not receive, the physical root. The root is not retained after the invocation.

### Grants

At least one explicit repeated `--grant OP` is required. Each `OP` is exactly `list`, `read`, or `write`; unknown values are invalid CLI input. There is no default grant, implicit `read`, implicit all-operations grant, `all` spelling, model-selected grant, dynamic escalation, or retained grant.

Valid repeated grants form the fixed operation set before the first Code inference. Duplicate valid `--grant` occurrences are accepted, collapse idempotently into that set, do not add authority, and do not make grant ordering meaningful. RFC-0114 remains authoritative for operation enforcement.

### Local validation and timeout

The public invocation is validated fail-closed before its first inference. At minimum, missing/repeated root, missing/unknown grant, missing/multiple/blank message, and invalid timeout are invalid input. Parsing must not duplicate RFC-0114 filesystem or logical-path policy, nor RFC-0116 request, context, response, or action-budget policy.

`--timeout-seconds` uses ordinary Code timeout validation and default semantics. It applies separately to every ordinary Code inference in this interaction; it is not a whole-interaction deadline. Because RFC-0116 permits at most nine Code inferences, an invocation may legitimately take multiple per-request timeout intervals. This RFC adds no total deadline, deadline accounting, background cancellation, scheduler, watchdog, or queue.

## Authority, execution, and routing

For one invocation, the `hac code-workspace` CLI process:

1. receives the trusted explicit root and grants;
2. constructs and runs one RFC-0116 interaction;
3. owns the single process-local RFC-0114 `WorkspaceAuthority`;
4. performs every inference through the existing ordinary HAC Code request path; and
5. exits after final answer or terminal failure.

The long-running `hac local` application does not own or receive workspace authority merely because it handles an ordinary Code request. This proposal adds no workspace route to `hac local`, does not send root or grants through `/v1/chat` or remote envelopes, and does not invoke RFC-0115 internally. RFC-0115 remains the separate machine-facing one-shot carrier for genuinely separate local integrations.

Each inference must retain the existing `ChatMessage`, `ClusterRequest(capability=code)`, native HAC HTTP request path, safe Code response validation, routing, and eligible local/remote Code execution semantics. The command must not call an adapter, choose a model or node, bypass routing, create a second Code transport, introduce request/result types, or force local inference. The exact implementation may reuse the existing private caller helper, extract a tiny reusable helper, or wrap the existing caller, provided these semantics remain unchanged.

Existing ordinary Code routing can select an explicitly configured eligible remote node. Caller-local authority never crosses that boundary. Remote Code nodes receive only ordinary bounded textual Code context; they never receive a physical root, grants, `WorkspaceAuthority`, workspace capability, or direct filesystem access. That text can include RFC-0116-accepted workspace information such as list names, read contents, and prior action/write context. Explicit use of this command enables that already-accepted disclosure behavior. Help and user documentation must explain that ordinary Code routing still applies and may send workspace text to configured remote Code nodes; this does not add a confirmation prompt, warning prompt, route inspection, remote-node preflight, local-only override, or forced-local inference.

## Foreground output and lifecycle

For every RFC-0116 workspace action actually dispatched to `WorkspaceAuthority` and resolved through its normal outcome surface, the command emits exactly one concise human-readable activity line to stderr after the outcome is known and before a subsequent Code inference. It identifies at least the operation (`list`, `read`, or `write`), RFC-0114 logical path, and outcome (`success` or `refused`). For example:

```text
workspace read src/example.py: success
workspace write src/example.py: refused
```

The examples use ordinary paths. In every actual activity line, the logical path is a deterministic, safe, human-readable rendering rather than necessarily raw path text. Its exact encoding is an implementation detail, but it must preserve one physical stderr line per dispatched action, prevent arbitrary valid logical-path content from introducing another physical line or becoming structurally indistinguishable from HAC-owned operation/outcome framing, and avoid emitting terminal control or escape characters raw in a way that can alter terminal control state. Deterministic quoting, escaping, or an equivalent single-line injective representation are acceptable; this does not select a generic protocol or machine-output format.

This is presentation-only. RFC-0114 remains exclusively authoritative for logical-path acceptance: the CLI must not reject additional paths, normalize or rewrite a path before dispatch, or otherwise change model-controlled path semantics for rendering convenience. HAC performs the foreground activity-output attempt synchronously before a subsequent Code inference and should flush according to ordinary CLI output behavior. If stderr itself fails, such as from a closed sink or I/O error, the command may terminate as an ordinary safe runtime/presentation failure; it neither rolls back nor retries a completed action, reclassifies a successful write as refused or failed, nor promises that an external sink accepted or displayed the bytes. The information and stderr channel are contractual; exact wording and whitespace are not. Activity lines must not display read contents, write contents, prompts, model responses, physical roots, remote-node internals, or runtime/model metadata. No separate requested, started, and completed events are required. A valid ninth action request rejected solely by RFC-0116's exhausted action budget is not dispatched, receives no normal activity line, and terminates through budget-exhaustion failure.

A successful completed workspace write stays successful if a later context bound, Code inference, response parse, result-size check, budget decision, or other continuation step fails. There is no rollback or automatic retry. A narrow callback/observer for completed action outcomes is an implementation detail, not a generic event architecture.

On successful final completion, the command writes only final model `content` to stdout according to ordinary HAC textual-output conventions and exits zero. Workspace activity is never mixed into stdout. This first surface adds no JSON mode, verbose attribution mode, structured machine-event output, transcript, or history.

Workspace refusal is an intermediate RFC-0116 outcome, not automatically a terminal command failure. A refusal line may be followed by another permitted action or a valid final response; in the latter case final content is written to stdout and the command exits zero.

Workspace activity and safe terminal errors use stderr. Malformed or oversized model responses, action-budget exhaustion, prospective Code context too large, ordinary Code request/inference failure, or unexpected interaction failure terminate nonzero with safe human-readable error output. Errors must not expose raw exceptions, physical root, workspace/write contents, prompts, raw model responses, or private topology/runtime details. No new stable detailed error taxonomy is created: existing HAC CLI conventions apply. At this contract level, success/final exits `0`, syntactically invalid invocation uses the existing invalid-input category (conventionally `2`), and runtime or interaction failure uses the ordinary nonzero failure category (conventionally `1`). An RFC-0114 authority-construction/root failure after valid parsing is a safe runtime failure.

## Compatibility and security boundaries

`hac code` remains RFC-0067 textual assistance and RFC-0088 textual interactive Code with no filesystem authority. `hac code-file` remains its one operator-selected whole-file transformation under RFC-0080/RFC-0081; it is not superseded. `hac code-workspace` is the distinct multi-step caller-edge composition where the model selects logical paths only inside the operator's already-fixed RFC-0114 root and grants.

The model and workspace content can be adversarial or prompt-injected. Security does not depend on model obedience. Before inference, the operator fixes the root, grants, RFC-0116 action budget, filesystem vocabulary, and ordinary routing configuration. The model cannot expand any of these, select a network destination/runtime/model/node, or execute shells or processes. Activity-line framing is HAC-owned: model-controlled logical-path text cannot forge that framing through its safe rendering. This is not a claim to prevent prompt injection or malicious filenames, and it exposes no workspace contents beyond the already-specified activity metadata. The physical `--root` value and initial instruction are ordinary command-line arguments; HAC does not promise to hide them from ordinary host operating-system, process-inspection, shell, or command-history mechanisms that can observe argv. This local argv visibility does not send the physical root to remote Code nodes. RFC-0114's local same-OS-user boundary remains unchanged.

No root or grant is added to `hac config local`, `hac config node`, configuration files, environment variables as a new authority surface, or named workspace profiles. All authority-bearing workspace inputs remain explicit and ephemeral for one invocation.

## Non-goals

This RFC does not authorize changing ordinary `hac code`; interactive or human-follow-up workspace Code; browser or `/v1/chat` workspace authority; HTTP workspace endpoints; root/grant retention, profiles, implicit cwd roots, or implicit/escalating grants; approval or runtime-confirmation prompts; JSON, machine-event, or verbose output modes; persistence, concurrency, parallel or background actions; generic event, tool/function-calling, agent, MCP, or plugin frameworks; file operations beyond RFC-0114; repository/Git, compiler, test, formatter, shell, process, or `hac_exec` execution; remote filesystem authority; routing/capability changes; database, dashboard, Docker, or Kubernetes work.

## Alternatives considered

### `hac code --workspace ...`

Rejected for the first contract. One existing command would then own ordinary text-only Code and a distinct authority-bearing operation, including ambiguity with current no-message interactive Code.

### Implicit `--root .` or default read

Rejected. The first authority-bearing CLI must require explicit workspace selection and explicit disclosure authority; even read is real filesystem authority.

### Retained root/grant configuration

Rejected as unnecessary for the first usable surface and inconsistent with the accepted ephemeral construction.

### Server-side authority or internal RFC-0115 subprocess

Rejected. Transporting root/grants or adding a server seam is unnecessary when the caller-local RFC-0116 composition can directly own RFC-0114 authority. RFC-0115 is for a genuinely separate process boundary.

### Force local Code inference or confirm remote disclosure

Rejected. RFC-0116 preserves ordinary routing and explicitly accepts bounded textual workspace disclosure to configured remote Code execution. Explicit invocation activates that boundary; new confirmation semantics lack a stated requirement.

### Whole-interaction timeout or generic agent/tool UX

Rejected for now. Per-inference timeout plus RFC-0116's finite inference limit is the smaller timing contract, and this is one closed composition rather than a generic agent system.

## Implementation boundary

If accepted, this RFC authorizes only the smallest CLI wiring: one `code-workspace` command module and top-level registration; explicit root/grant/message/timeout parsing; construction and execution of the existing RFC-0116 state machine; ordinary Code-path inference wiring; a narrow completed success/refusal observation mechanism if needed; stderr activity; stdout final content; focused CLI tests; and minimal help/user documentation.

It does not authorize redesigning `workspace_aware_code.py` into a generic agent/event system, changing ordinary Code/routing/adapters/`ClusterRequest`/`ClusterResult`, retained workspace configuration, browser/API authority, process execution, or generic tools. If implementation requires a generic event system, protocol change, retained state, new message role, or routing change, it must stop and return to RFC review.

## Decision

Accepted. HAC accepts a dedicated `hac code-workspace` command with one explicit root, one or more explicit grants, and exactly one positional-or-`--message` instruction. It has no interactive mode, owns caller-local CLI-process RFC-0114 authority for one ephemeral RFC-0116 interaction, preserves the existing ordinary Code request and routing path, and applies existing timeout semantics independently per inference. Dispatched actions have bounded safe foreground stderr activity and final content alone goes to stdout; a refusal may still lead to a successful final exit, while terminal failures are nonzero. It adds neither retained workspace authority nor a richer tool, agent, or process surface.
