# RFC-0115: Bounded One-Shot Local Workspace Machine Carrier

Status: Accepted

Date: 2026-09-10

Author: frian

## Summary

This RFC proposes one dedicated local machine-facing executable for consuming RFC-0114's accepted bounded workspace authority:

```text
home-ai-cluster-workspace-carrier
```

A trusted local integration starts that exact executable with one trusted host root and a non-empty fixed set of `list`, `read`, and/or `write` grants. The carrier constructs exactly one `WorkspaceAuthority`, reads exactly one bounded UTF-8 JSON request from stdin through EOF, writes one bounded UTF-8 JSON response to stdout, and exits.

The request may select one RFC-0114 operation and logical workspace path (and replacement content for `write`). It cannot select or override the root, grants, executable, environment, command, shell, or destination. The caller may choose what operation to request; HAC decides what the explicit workspace grant authorizes.

This is machine-facing although a human could invoke it manually. It is not an operator `hac workspace` command, a general CLI, a filesystem service, a tool framework, an agent architecture, or process-execution authority.

## Problem

RFC-0114 defines concrete process-local HAC workspace authority but deliberately leaves external consumption unspecified. A completed external falsification experiment demonstrated that a trusted local integration can start one exact HAC-owned process, provide authority construction inputs, send one untrusted bounded workspace request, receive one structured result, and let the process exit. The real RFC-0114 authority retained the filesystem decision boundary for allowed list/read/write and for traversal, absolute-path, redirection, outside-write, and missing-file refusal.

HTTP, one-shot fixed-child-process, and persistent stdin/stdout forms were all experimentally feasible. HTTP necessity was falsified, and no demonstrated current requirement justifies a retained child process. HAC needs the smallest supported external process seam.

## Decision

HAC should provide exactly one dedicated one-shot local machine carrier:

```text
trusted local integration
        |
        | starts exact HAC machine carrier
        | supplies trusted root + fixed grant
        v
home-ai-cluster-workspace-carrier
        |
        | construct exactly one RFC-0114 WorkspaceAuthority
        | read exactly one structured request
        v
WorkspaceAuthority
        |
        | one list/read/write result or refusal
        v
one structured response
        |
        v
process exits
```

One carrier process handles one workspace request. The OS process boundary supplies its lifecycle. There is no persistent request loop, listener, daemon, session, reconnect, multiplexing, concurrency model, process supervision, or lifecycle framework.

### Dedicated machine-facing launch surface

The installed entry point is exactly `home-ai-cluster-workspace-carrier`. Its supported startup inputs are exactly:

```text
--root HOST_PATH
--grant OPERATION
```

`--grant` occurs one or more times; `OPERATION` is exactly `list`, `read`, or `write`. For example:

```text
home-ai-cluster-workspace-carrier \
    --root /trusted/operator/selected/workspace \
    --grant list \
    --grant read
```

Repeated valid grants form one set, not multiple authorities. At least one valid grant is required; an unknown grant fails before request execution. On Windows, `HOST_PATH` has the ordinary trusted host-path semantics already accepted by RFC-0114. No model, runtime, host, port, retained-config key, shell command, arbitrary environment forwarding, plugin selection, remote node, or repository-mode option is added.

This is not a human `hac workspace` surface. It defines no pretty terminal output, prompt, TTY behavior, alias, or convenience flags. Manual invocation does not make its stdin/stdout machine protocol supported operator UX.

### Trusted construction and untrusted request boundary

The trusted parent chooses the exact executable, `--root`, and every `--grant`. These fixed startup inputs construct exactly one RFC-0114 `WorkspaceAuthority` for the complete process lifetime. The request cannot modify, extend, or override them.

The stdin request is untrusted: it may be malformed, buggy, adversarial, prompt-injected, or model-controlled. It may choose only one operation, one RFC-0114 logical workspace path, and replacement content for `write`. It contains no host root, grant, native host-path override, executable, environment, command, shell syntax, or transport destination. The carrier independently reapplies RFC-0114 validation and grants; an operation absent from the startup grant fails locally.

The carrier runs with its parent's ordinary OS identity and permissions. It bypasses neither host permissions nor RFC-0114's threat model. A process independently launching it with another root has only filesystem authority already available to its identity. This adds no credential, token, local authentication protocol, ACL framework, or sandbox promise against an equivalent same-user hostile process.

### Request framing and schema

The carrier reads exactly one UTF-8 JSON document from stdin through EOF, with a fixed 8 MiB input limit. The bound is for machine-protocol parsing and accommodates RFC-0114's one-MiB replacement even after JSON escaping. There is exactly one JSON value; ordinary JSON leading/trailing whitespace is permitted. The value must be an object. NDJSON, delimiters, request IDs, version negotiation, streaming, and a second request are not supported.

Malformed JSON, non-object JSON, invalid UTF-8, input beyond the bound, and schema violations fail closed. Schemas are closed: unknown fields fail.

A request object containing any duplicate member name is invalid and must be rejected before grant dispatch or any RFC-0114 workspace operation. Duplicate detection uses ordinary equality of decoded JSON member-name strings, not raw lexical spelling: `"operation"` and `"oper\u0061tion"` are duplicates, as are escaped-equivalent forms of `path`, `content`, or an unknown member name. The flat request schema requires no Unicode normalization, canonical JSON, key-ordering rule, alternate serialization format, or nested-object policy. When a bounded normal failure response can be safely formed, it may use the existing `{"ok":false,"error":"..."}` shape without exposing parser internals.

`list` and `read` permit exactly `operation` and `path`:

```json
{"operation":"list","path":"."}
```

```json
{"operation":"read","path":"README.md"}
```

`content` is forbidden for those operations. `write` permits exactly `operation`, `path`, and `content`; content is required and must be a JSON string:

```json
{"operation":"write","path":"notes/state.txt","content":"replacement text"}
```

There are no generic method parameters or arbitrary argument dictionaries.

### Response framing, shapes, and exit status

Stdout is exclusively one UTF-8 machine response. For a normally handled request, the carrier writes one JSON object, may append one trailing newline, and exits. It writes no log, progress output, banner, prompt, or human diagnostic to stdout. Stderr may carry optional process diagnostics, but must not log workspace file content or request content by default. It creates no request history or retained logs.

The 8 MiB output bound is a separate carrier serialization bound, measured over
the complete serialized UTF-8 JSON response bytes. Every emitted response,
including `ok: false`, remains inside that bound. Responses are complete or
failure; they are never silently truncated. No streaming response is supported.
For the current bounded `read`, 8 MiB is intentionally sufficient for any
RFC-0114 one-MiB UTF-8 content under ordinary JSON escaping. RFC-0114 does not,
however, define one aggregate byte bound over all names in a successful `list`;
this RFC therefore does not claim that every accepted RFC-0114 result is
necessarily serializable below the carrier limit.

For a non-mutating successful `list` or `read` result whose complete success
response would exceed the carrier bound, the carrier must not return a partial
result. It may instead return one bounded normal carrier failure response when
that response can be safely formed. This adds no paging, range reads,
continuation token, or streaming form. Success shapes are closed and minimal:

```json
{"ok":true,"entries":[{"name":"README.md","kind":"file"}]}
```

for `list`, directly using RFC-0114 entry semantics;

```json
{"ok":true,"content":"..."}
```

for `read`; and

```json
{"ok":true}
```

for `write`. No metadata, native/temporary path, checksum, token, node, runtime, model, or execution detail is returned.

For a normally parsed and handled request rejected by schema validation or RFC-0114 authority, the carrier returns:

```json
{"ok":false,"error":"..."}
```

The error text is not a stable error-code taxonomy. It must not expose a stack trace, echo file content, or require a native host path. Startup failures, malformed framing, unexpected internal failures, and failures before a response can be formed terminate non-zero and may diagnose on stderr.

RFC-0114 alone defines whether a workspace `write` succeeded. Once
`WorkspaceAuthority.write()` has successfully returned, the carrier must never
generate a normal `{"ok":false,...}` response claiming that the workspace
operation failed. It then attempts to serialize and deliver the already-known
success response. If that serialization or stdout delivery fails after the
write committed, the process may terminate non-zero without a valid normal
response. The invoking parent then has an indeterminate observed write outcome:
absence of a success response does not prove that the target remained
unchanged. A valid delivered `{"ok":true}` write response followed by exit
status zero confirms that RFC-0114 returned successfully and the carrier
completed its normal response path.

A non-zero carrier exit means the complete carrier transaction did not finish
successfully; it does not universally mean that no filesystem side effect
occurred. The carrier prescribes no automatic retry: unrelated concurrent
modification remains outside existing guarantees and retry could overwrite
later content. No non-zero exit-code taxonomy is standardized.

### Delegation and architectural boundaries

The carrier delegates workspace authorization and filesystem semantics to concrete RFC-0114 authority. It does not duplicate or loosen RFC-0114 path grammar or byte bound; list entry bound; read/write byte bounds; strict UTF-8 filesystem semantics; existing-file-only replacement; redirection rejection; hard-link namespace semantics; host filesystem backing; or same-user race limitations.

`list`, `read`, and `write` remain RFC-0114 workspace authority operations, not RFC-0066 cluster capabilities. They do not affect candidate eligibility, static/remote routing, fallback, receiver advertisement, or node capability declaration. The carrier creates no `ClusterRequest`, selects no runtime, invokes no inference, or sends content to a local model or remote model. RFC-0115 adds no HAC-owned network client, listener, transport, route, or network protocol. RFC-0114 remains authoritative that HAC does not inspect or classify the trusted root's physical filesystem backing: ordinary host filesystem operations may indirectly use NFS, SMB, FUSE, mapped storage, or other backing the operator exposed.

Starting this exact executable is trusted composition, not `hac_exec`. The request cannot choose a program, command, argv, shell, interpreter, or environment. No generic process authority is introduced.

## Rationale and alternatives

The external experiment proved a smaller-than-HTTP seam using the real merged RFC-0114 authority. One-shot process lifetime is a clear, natural lifecycle and keeps trusted construction outside untrusted request data. Single-document bounded JSON is enough without making a general RPC protocol.

Persistent stdio is deferred: although feasible, no requirement justifies a retained process, multi-request loop, shutdown protocol, restart semantics, session state, correlation, stdout lifetime management, or supervision. Startup overhead has not been shown materially problematic. A future RFC may revisit persistence if measured use makes one-shot startup insufficient.

HTTP is deferred: its necessity was falsified. This RFC adds no TCP listener, socket, host/port, route, browser surface, CSRF/origin concern, listener authentication/token, or network protocol. A future consumer unable to start a local child needs new evidence for another carrier.

OpenCode, Pi, and Aider are experiment evidence, not carrier contract. Their adapters map their own vocabulary to public semantic operations `list`, `read`, and `write`; experimental `hac_list`, `hac_read`, and `hac_write` names are not protocol names.

## Privacy and security consequences

Untrusted requests fail closed and cannot expand a grant or select a physical root. The carrier adds no HAC-owned network client, listener, transport, route, or network protocol; it adds no content/path/history persistence or default request/response logging. The machine response is the explicit disclosure to its invoking parent. Root and grants are not authentication credentials, but the root may be sensitive local metadata because ordinary host process-inspection mechanisms may expose startup argv subject to host permissions and platform behavior. The carrier does not promise to conceal startup arguments. Seeing a root does not itself grant filesystem access; OS permissions and RFC-0114's existing same-user threat boundary remain authoritative. The carrier is not a sandbox and adds no same-user isolation guarantee beyond RFC-0114.

## Non-goals

This RFC does not authorize an operator workspace CLI; persistent carrier; HTTP; daemon, service, or listener; authentication framework; retained workspace configuration; generic RPC, tool, or plugin framework; MCP; OpenCode/Pi/Aider integration; inference, routing, cluster capability, remote workspace access, or filesystem backend abstraction; shell, arbitrary process execution, `hac_exec`, or command allowlists; file creation, delete, move, rename, patch, search, Git/repository semantics; sessions, concurrency, streaming, request IDs, protocol negotiation, database, Docker, or Kubernetes.

## Implementation boundary and proof expectations

Acceptance authorizes one later separate implementation PR only: the dedicated installed entry point, one small machine-facing carrier module, closed startup parsing, bounded stdin JSON parsing, delegation to existing `WorkspaceAuthority`, bounded stdout JSON serialization, focused tests, and the minimal packaging change needed to install it. It must not add a human CLI, HTTP, persistence, harness integration, model/runtime logic, routing, retained configuration, or generic abstractions.

That proof must demonstrate: the exact launcher exists; empty, missing, or invalid root fails rather than falling back to cwd, while explicit `"."` remains valid when RFC-0114 accepts it; at least one grant is required; unknown grants fail; requests cannot override root/grant; ungranted operations fail; exactly one request is consumed and extra material rejected; malformed, non-object, oversized, and non-UTF-8 request fails; duplicate `operation`, `path`, and `write` `content` members, including an escaped-equivalent name such as `operation` plus `oper\u0061tion`, are rejected before any workspace action; with both `read` and `write` granted, `{"operation":"read","operation":"write","path":"target.txt","content":"changed"}` is rejected without mutating the target; unknown and operation-inappropriate fields fail; granted list/read/write delegate successfully; RFC-0114 traversal, absolute-path, redirection, and missing-write refusal remain effective; every serialized stdout response is complete-or-failure and inside the carrier output limit; oversized success results are never silently truncated; a forced stdout-delivery failure after successful RFC-0114 `write` produces no normal `ok:false` claim that the write failed, and documentation/tests make clear that missing acknowledgment does not prove absence of the committed write; no default content/path logging; success exits zero and failure non-zero; no HAC-owned listener, transport, or network protocol, inference/runtime import/call, or persistent loop; Linux and native Windows behavior is tested; and the existing full suite remains green.

## Consequences and future work

RFC-0114 continues to own workspace semantics; this RFC adds only trusted startup carriage and one-shot bounded JSON framing. This acceptance authorizes only the later separate implementation proof described above; it does not itself implement the carrier. Persistence or another transport requires its own evidence and RFC rather than an unreviewed extension.

## Decision

Accepted.
