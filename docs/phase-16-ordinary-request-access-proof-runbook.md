# Phase 16 Ordinary Request Access Proof Runbook

Status: Planned

Date: 2026-07-18

## Purpose

This runbook defines the minimum real operator proof required to confirm the
accepted RFC-0045 access path. It does not claim that the proof has run.

The proof must demonstrate:

> One operator can send one ordinary capability-centered request without
> manually constructing HTTP transport details.

Its subject is the installed `home-ai-cluster-chat --message <MESSAGE>` command
as a client of an already running ordinary Home AI Cluster process through the
existing native `/v1/chat` boundary. It does not re-prove internal routing,
adapter, fallback, or transport behavior covered elsewhere.

## Scope

Use only merged ordinary operator commands and interfaces. Do not use mocks,
custom Python wiring, proof-specific launchers, direct runtime requests, or
custom HTTP clients. This runbook records a reviewed procedure; a later retained
record alone may report real observations.

## Required revision

Run the proof from one exact repository revision that contains merged PR #281.
The later retained proof MUST record the exact Git commit, execution date,
whether each process was local-only or explicit static-cluster, and relevant
environment limitations. This runbook deliberately does not guess a revision.

## Preconditions

- Follow the applicable ordinary local-only and static-cluster preparation in
  [the canonical operator workflow](operator-workflow.md).
- Keep the external runtime and all process lifecycle actions operator-owned.
- Ensure the ordinary command target is the established loopback endpoint
  `http://127.0.0.1:8000/v1/chat`.
- Sanitize every retained environment, topology, runtime, and machine fact.

## Privacy-safe message policy

Use one deliberately neutral test message. Supply it only at execution time and
refer to it in retained evidence only as `<REDACTED_TEST_MESSAGE>`.

Do not retain the literal message, generated response content, terminal history,
runtime logs, HTTP traces, raw exception details, or screenshots when normalized
text is sufficient.

## Local-only success observation

1. Start one ordinary local-only process using the canonical operator command:

   ```sh
   uv run uvicorn home_ai_cluster.main:app --reload
   ```

2. Confirm it is listening on the established ordinary loopback endpoint.
3. Run exactly:

   ```sh
   uv run home-ai-cluster-chat --message "<REDACTED_TEST_MESSAGE>"
   ```

4. Retain only that the command exited `0`, wrote nothing to standard error, and
   wrote exactly one compact JSON object to standard output. The object must
   contain `content`, `adapter`, `model`, and `node_id`; `node_id` must truthfully
   identify the node selected by the running cluster. It must have no routing
   explanation wrapper or extra output.

Replace generated content with `<REDACTED_GENERATED_CONTENT>`, operator-specific
model values with `<REDACTED_MODEL_OR_NULL>`, and private node identities with
approved placeholders. An acceptable retained shape is:

```json
{
  "content": "<REDACTED_GENERATED_CONTENT>",
  "adapter": "<OBSERVED_ADAPTER>",
  "model": "<REDACTED_MODEL_OR_NULL>",
  "node_id": "<OBSERVED_OR_SANITIZED_NODE_ID>"
}
```

Retain an adapter identifier only when it is already architectural and does not
reveal private operator configuration. Do not fabricate values.

## Explicit static-cluster success observation

1. Follow the canonical explicit static-cluster workflow and start one ordinary
   static-cluster process, for example:

   ```sh
   uv run home-ai-cluster-static-cluster --declaration <DECLARATION_PATH>
   ```

2. Run the unchanged chat command:

   ```sh
   uv run home-ai-cluster-chat --message "<REDACTED_TEST_MESSAGE>"
   ```

3. Retain exit `0`, empty standard error, and exactly one normalized
   `ClusterResult` with truthful `node_id` attribution.

The command invocation MUST contain no declaration path, node selector, runtime
selector, adapter selector, or model selector. The result must show that the
client did not know or reconstruct static-cluster composition. Do not require a
specific remote node or manufacture remote execution; record the actual ordinary
routing result only.

## Ordinary process unavailable observation

1. Ensure no ordinary Home AI Cluster process is listening on the fixed ordinary
   loopback endpoint.
2. Run:

   ```sh
   uv run home-ai-cluster-chat --message "<REDACTED_TEST_MESSAGE>"
   ```

3. Retain only:

   ```text
   stdout: empty
   stderr: error: ordinary cluster unavailable
   exit: 1
   ```

Do not retain connection, socket, process-listing, stack-trace, or other raw
failure detail.

## Normalized cluster-owned failure observation

Use the existing normalized public failure `error: runtime adapter unavailable`.

1. Start an ordinary local-only or ordinary static-cluster process through the
   supported workflow while its operator-owned runtime is initially available.
2. Temporarily stop or make unavailable only that operator-owned runtime; runtime
   restart and lifecycle management remain operator-owned.
3. Run the unchanged chat command:

   ```sh
   uv run home-ai-cluster-chat --message "<REDACTED_TEST_MESSAGE>"
   ```

4. Retain only empty standard output, standard error exactly
   `error: runtime adapter unavailable`, and exit `1`.

Do not alter production code, use mock transports, require destructive changes,
or retain raw runtime, HTTP, model, host, port, or exception detail.

## Command contract observations

The retained proof must confirm that:

- the command is `home-ai-cluster-chat` and its only application input is
  `--message`;
- it constructs the fixed `chat` capability and targets the ordinary process,
  not a runtime or node;
- no host, port, base URL, capability, runtime, model, node, declaration, retry,
  or timeout option is used;
- one invocation represents exactly one request, with no interactive prompt or
  session;
- success is one compact normalized result and failures are stable prompt-free
  standard-error lines; and
- Home AI Cluster creates no request history or other persistence.

## Message exposure observation

The message is a command-line argument and may be exposed or retained by the
surrounding shell or operating system. This command is not secure secret input.
Use only the neutral test message and do not inspect or retain shell history or
process listings.

## Evidence to retain

Create `docs/phase-16-ordinary-request-access-proof.md` only after one
successful real proof run. It should have status `Retained` and include the
date, exact revision, sanitized environment description and startup commands,
unchanged chat-command shape, all four observations, privacy observations,
covered obligations, limitations, and a conclusion limited to what was directly
demonstrated.

## Evidence not to retain

Do not retain submitted prompts, generated responses, shell history, process
listings, private IP addresses, hostnames, usernames, absolute paths,
declarations containing private topology, private node identities, runtime or
remote URLs, operator-specific model identifiers, credentials, tokens,
authorization headers, environment dumps, raw HTTP bodies, raw exceptions, stack
traces, runtime logs, or screenshots when normalized text is sufficient.

## Proof obligations

The retained proof must establish that:

1. the installed command exists and runs as an ordinary operator command;
2. it sends one request to the already running ordinary cluster process;
3. local-only and explicit static-cluster operation use the same command and
   fixed endpoint contract;
4. success emits one complete validated normalized `ClusterResult`;
5. cluster-owned attribution remains present;
6. unavailable process maps to the accepted stable failure;
7. one real cluster-owned failure maps to the accepted stable failure;
8. standard output and standard error remain separated as RFC-0045 requires;
9. failure output contains no raw private detail;
10. the proof retains no prompt or generated response;
11. the command adds no history, configuration, discovery, retry, client
    fallback, process startup, supervision, or topology interpretation; and
12. only merged ordinary interfaces are used, not mocks or custom Python wiring.

## Limitations

The retained proof must state honestly whether one or multiple physical machines
were used and, only when privacy-safe, the runtime family present. It does not
establish remote administration, secure secret input, sessions, streaming,
tools, multimodal input, retries, discovery, or configurable targets. It proves
only the fixed Phase 16 one-shot ordinary request access path.

## Non-goals

This runbook adds no code changes, tests, endpoint, OpenAI-compatible access,
direct runtime requests, interactive chat, sessions, history, standard input,
prompt files, multiple messages, roles or system prompts, streaming, generation
controls, tools, multimodal input, node/runtime/model selection, routing change,
retry, client fallback, discovery, client declaration parsing, client process
startup or supervision, lifecycle management, configuration, authentication,
TLS, remote administration, dashboard, database, Docker, or Kubernetes.

## Completion rule

This runbook may merge before execution because it records only the reviewed
procedure. Phase 16 remains incomplete until a separate retained proof document
records real privacy-safe observations from one successful operator run.
