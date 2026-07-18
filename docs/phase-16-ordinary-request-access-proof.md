# Phase 16 Ordinary Request Access Proof

Status: Retained

Date: 2026-07-18

## Purpose

This retained record reports one real operator execution of the accepted
RFC-0045 one-shot ordinary request path. It demonstrates that the installed
`home-ai-cluster-chat` command can send one capability-centered request to an
already running ordinary Home AI Cluster process without manually constructing
HTTP transport details.

## Observed revision

The proof ran from clean revision
`4917b3bc748822cdea1050392c898bf8e6193567`. The worktree was clean before
the observations began.

## Environment

The observations ran on one physical machine. The external runtime family was
Ollama. The static-cluster request selected the local candidate, so this proof
did not exercise real network transport. The runtime lifecycle remained
operator-owned throughout the proof; no runtime configuration, model
identifier, URL, or machine-specific detail is retained.

## Privacy treatment

The same deliberately neutral message was supplied only at execution time and
is retained here as `<REDACTED_TEST_MESSAGE>`. Generated content is retained
only as `<REDACTED_GENERATED_CONTENT>`. No shell history, process listing,
runtime log, declaration contents, private topology, model identifier, raw
exception, raw HTTP detail, trace, history, or screenshot is retained.

## Ordinary process unavailable

With no ordinary Home AI Cluster process running on the fixed endpoint, the
ordinary client command was run:

```sh
uv run home-ai-cluster-chat --message "<REDACTED_TEST_MESSAGE>"
```

The observation was:

```text
command: uv run home-ai-cluster-chat --message "<REDACTED_TEST_MESSAGE>"
stdout: empty
stderr: error: ordinary cluster unavailable
exit: 1
```

## Local-only success

The ordinary local-only process was started with:

```sh
uv run home-ai-cluster-local
```

The unchanged ordinary client command was:

```sh
uv run home-ai-cluster-chat --message "<REDACTED_TEST_MESSAGE>"
```

It exited `0`, wrote nothing to standard error, and wrote exactly one compact
complete `ClusterResult` to standard output. Its sanitized observed result was:

```json
{"content":"<REDACTED_GENERATED_CONTENT>","adapter":"ollama","model":"<REDACTED_MODEL_OR_NULL>","node_id":"local"}
```

The selected node attribution was `local`.

## Normalized runtime failure

The ordinary local-only process was started while the operator-owned runtime
was available. The runtime was then temporarily made unavailable through its
normal operator-owned lifecycle and restored after the observation. The
unchanged ordinary client command produced:

```text
command: uv run home-ai-cluster-chat --message "<REDACTED_TEST_MESSAGE>"
stdout: empty
stderr: error: runtime adapter unavailable
exit: 1
```

## Explicit static-cluster success

The ordinary static-cluster process was started with the existing canonical
static declaration shape:

```sh
uv run home-ai-cluster-static-cluster --declaration <REDACTED_DECLARATION_PATH>
```

The unchanged ordinary client command was:

```sh
uv run home-ai-cluster-chat --message "<REDACTED_TEST_MESSAGE>"
```

It received no declaration, node, runtime, adapter, model, host, port, or
capability selector; exited `0`; wrote nothing to standard error; and wrote one
compact complete `ClusterResult` to standard output. Its sanitized observed
result was:

```json
{"content":"<REDACTED_GENERATED_CONTENT>","adapter":"ollama","model":"<REDACTED_MODEL_OR_NULL>","node_id":"local"}
```

The observed attribution was `local`. This proof does not claim that a remote
node was selected or executed.

## Shared command contract

Both success observations used exactly the same client shape:

```sh
uv run home-ai-cluster-chat --message "<REDACTED_TEST_MESSAGE>"
```

Its only application input was `--message`. It targeted the already running
ordinary process through the fixed endpoint, constructed the fixed `chat`
capability, and included no host, port, URL, capability, runtime, model, node,
declaration, retry, or timeout option. Each invocation represented one request
with no interactive session, client process startup, supervision, topology
interpretation, history, or persistence. The command did not start or inspect
the cluster process.

## Proof obligations covered

- The installed command ran as an ordinary operator command.
- The same command reached both local-only and explicit static-cluster ordinary
  processes through the fixed endpoint contract.
- Both success observations returned one complete normalized `ClusterResult`
  with cluster-owned attribution and separated standard output and standard
  error.
- An unavailable ordinary process produced the accepted stable
  cluster-unavailable failure.
- A real cluster-owned runtime failure produced the accepted stable runtime
  adapter-unavailable failure.
- The retained record contains neither the submitted message nor generated
  content and uses only merged ordinary interfaces.

## Limitations

The proof used one physical machine and does not demonstrate remote execution,
remote administration, secure secret input, sessions, streaming, tools,
multimodal input, retries, discovery, configurable targets, or lifecycle
ownership. The command-line message may be visible to the surrounding operating
system. This proof covers only the fixed Phase 16 one-shot ordinary request
path.

## Conclusion

At the observed revision, one operator sent one ordinary capability-centered
request through an already running local-only or explicit static-cluster process
without manually constructing HTTP transport details. The real run also
observed stable unavailable-process and runtime-unavailable failures without
raw private details.
