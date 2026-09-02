# Ordinary summarize CLI investigation

## Status and question

Investigation only. This document creates no RFC, accepted decision, command,
alias, implementation, packaging change, root-command change, cluster-behavior
change, roadmap phase, or Phase 19. In particular, it does not extend the
accepted seven-command root namespace.

Question: should the existing bounded `summarize` capability receive a minimal
ordinary one-shot CLI surface and, if it later does, what is the smallest
coherent contract?

The evidence supports a real operator convenience problem, but it does not by
itself accept a new public command contract. The no-change option therefore
remains valid. If a later RFC establishes that the operator need warrants a
command, this investigation finds a root subcommand with one explicit text
option to be the smallest coherent candidate. That conditional assessment is
not a decision to add `hac summarize`.

## Current state

`summarize` is an accepted cluster-native capability under RFC-0051. It has a
dedicated native endpoint:

```text
POST http://127.0.0.1:8000/v1/summarize
```

Its public body is exactly one semantic input:

```json
{"text":"source text"}
```

The normalized `SummarizeRequest` preserves source whitespace, rejects a value
whose `strip()` is empty, and limits UTF-8 source text to 65,536 bytes. Public
malformed JSON, missing or non-string text, blank text, and oversize text all
produce HTTP 422 with `{"detail":"Invalid summarize request"}` before
routing or network activity. Extra public top-level fields are ignored, as they
are for the existing chat DTO; they do not become capability inputs.

Both accepted local adapter families, Ollama and llama-server, advertise and
implement `summarize`. The adapter-owned request mapping keeps source text as
content to summarize and does not expose a caller-controlled prompt, role,
style, length, or model setting. The result is the existing normalized
`ClusterResult` shape:

```json
{"content":"summary","adapter":"adapter-name","model":"model-name-or-null","node_id":"selected-node"}
```

`content` can be empty. `node_id` remains caller/cluster-owned attribution;
`adapter` and optional `model` remain truthful execution attribution. There are
no summarize-specific result fields that require a new presentation mode.

The ordinary local-only process routes only locally. The ordinary explicit
static-cluster process uses the same existing local-first eligible-candidate
selection and bounded pre-transmission fallback for summarize as for chat. A
chat-only node is ineligible for summarize; an eligible declared trusted-LAN
node may receive source text when selected. The Phase 18 proof and closeout
record this two-machine capability proof, including remote result validation
and caller-owned final node attribution. Neither mode requires the client to
know its topology.

For a valid summarize request, no eligible capability produces HTTP 404 with
`No adapter provides capability: summarize`; runtime unavailability produces
HTTP 503 with `Runtime adapter unavailable`. Invalid runtime or remote results
remain normalized server-side failures without runtime-private details.

There is no summarize CLI today. RFC-0051 expressly excluded one from its
first increment. The root command currently has the closed accepted subcommand
set `local`, `static-cluster`, `compatibility`, `chat`, `preflight`, `health`,
and `status`; it has no `summarize` entry. The installed `hac` alias and
`home-ai-cluster` both invoke the same root function, so neither has an
independent command tree. OpenAI-compatible access remains chat-only.

The ordinary chat command is useful precedent, not an automatic answer. It is
a topology-blind one-request client at a fixed loopback target, with local
validation, a finite implementation-owned timeout, response validation, safe
failure mapping, and three output presentations. Its input is a chat message;
summarize must instead preserve the existing first-class source-text meaning.

## Operator need and boundaries

The narrow credible needs are to:

* summarize one bounded text value from a terminal without manually composing
  HTTP and JSON;
* use the same client against an already-running local-only or explicit
  static-cluster process;
* read the summary directly, request human-readable attribution, or obtain
  compact JSON for automation; and
* remain topology-blind while retaining the existing local-first and privacy
  boundaries in the running process.

This is not a document-ingestion proposal. It does not establish standard
input, paths, files, PDF extraction, encoding detection, temporary files,
upload, automatic pipe detection, batching, streaming, chunking, history,
interactive behavior, automatic process startup, request selectors, or
OpenAI-compatible summarization. Source text passed on a command line can be
retained by shell history or exposed to local process inspection, just as chat
messages can; it is not secret input.

## Candidate surfaces

| Option | Assessment | Main consequence |
| --- | --- | --- |
| A. No summarize CLI | Coherent and lowest-scope. The native endpoint is documented and sufficient for operators comfortable with HTTP. It retains manual request construction, quoting of JSON, and response handling. | No root, packaging, parser, client, or test change. |
| B. Root subcommand with `--text` | The smallest conditional candidate. `hac summarize --text "Long text"` is explicit in scripts, fits the accepted root facade model, and can reuse chat's thin-client seams without treating source text as a message. | Requires an RFC because it extends the closed root namespace and establishes a durable input/output contract. |
| C. Root subcommand with positional text | Ergonomic for a one-value terminal invocation, and chat provides a narrowly accepted positional precedent. It requires ordinary shell quoting and must reject surplus tokens rather than join them. | Adds a second spelling and a choice about whether `--text` is retained as an equal alternative; it is not smaller than B. |
| D. Dedicated standalone command only | Could keep the root namespace closed, but is less discoverable and duplicates the existing root-plus-standalone command pattern without evidence that summarize should be excluded from ordinary operation. | Requires a new package entry point and leaves `hac` unable to expose the capability through its shared root tree. |
| E. Standard input or file input | Useful for some automation in the abstract, but high-burden and outside RFC-0051's deliberate text-only boundary. It introduces source precedence, blocking and TTY behavior, encoding, size enforcement timing, path and file privacy, lifecycle, and error questions. | Do not recommend in a first command merely because summaries may be long. |

Option A should be retained unless a concrete operator workflow establishes that
the native API is insufficient. If that evidence is later accepted, B is
clearer than C for the initial contract: an explicit `--text` makes the input
purpose visible and mirrors the bounded one-value validation shape without
claiming that chat's positional ergonomics applies unchanged. D has no current
justification, and E should remain out of scope.

## Conditional contract for the smallest candidate

This section describes what a later decision would need to specify for Option
B; it is not an accepted command contract.

### Input and request

The command would accept exactly one `--text <TEXT>` source. It would require
that one source, preserve accepted whitespace unchanged, reject blank input
using the authoritative `SummarizeRequest` validation, and instantiate that
existing model before constructing an HTTP client to enforce its 65,536-byte
UTF-8 limit. The CLI must not duplicate that numeric rule in an independent
validator. Repeated `--text`, any positional token, and unknown arguments would
be local invalid input. There would be no source precedence rule because no
positional, stdin, or file source would exist.

Multi-word values require normal shell quoting. The command must not join
unquoted surplus tokens; that would create a variable-length grammar and alter
shell-provided boundaries. It would construct only `{"text": "<TEXT>"}` and
send one `POST` to the fixed ordinary loopback `/v1/summarize` target. The
fixed target works identically with an already-running local-only or explicit
static-cluster process; the client must not accept a host, port, declaration,
node, adapter, runtime, model, capability, or routing option.

The timeout should remain finite and implementation-owned, with no timeout
option, retry, client fallback, discovery, service startup, or lifecycle
behavior. The running process owns eligibility, routing, static remote
transport, and fallback.

### Success, failure, and privacy

The existing chat output convention is a strong candidate for reuse only after
validating the summarize result shape. That validation succeeds here:
`ClusterResult.content` is summary text and its attribution fields have the
same presentation meaning. A future command could therefore use exactly the
existing three modes, without inventing another one:

* default: content only, preserving content and the existing terminal-newline
  rule;
* `-v`/`--verbose`: response content plus node, adapter, and optional model;
* `--json`: the compact complete validated `ClusterResult`.

`--verbose` and `--json` would be mutually exclusive. No summarize-specific
field changes this choice, and empty summary content should follow chat's
already-defined presentation behavior.

As with chat, a valid local input would make one request; successful HTTP alone
would not be enough. The client would validate the response as the existing
`ClusterResult` before emitting any stdout. Invalid local input would have no
stdout, one stable prompt-free stderr line, and exit 2. Connection failure or
timeout, HTTP 422, 404, 503, unexpected status, malformed success response,
and other request failures would retain chat's safe category-oriented mapping,
non-zero exit behavior, and empty stdout. A later RFC would need to decide
whether the accepted chat-only 404 wording is generalized or becomes the
parallel `no available summarize capability`; this investigation makes no
string-level decision.

The command would not log, save, cache, or otherwise retain source text,
summaries, request bodies, or response bodies. Its direct stdout is operator
output; shell history, process inspection, terminal scrollback, and redirection
remain outside project control. It must not show raw URLs, exceptions, response
bodies, source text, summaries, private node identities, remote addresses, or
credentials in failures.

### Compatibility, impact, and proof

Option B would add one root subcommand while preserving all seven accepted
ones, their forwarding, outputs, errors, and lifecycle. Both installed root
names would inherit it through their one shared entry point; no new alias is
needed. It need not add a standalone script or package dependency, but would
change the root help, dispatch table, package-level command documentation, and
focused tests. It would be a public compatibility addition, not a replacement
for direct API use.

Focused proof should cover the exact request body and target; text whitespace
and UTF-8 boundary preservation; missing, blank, repeated, positional,
surplus, and unknown input rejection before client construction; output modes;
response validation; each safe failure category; forwarding through both root
names; and local-only/static-cluster topology blindness through the fixed
caller endpoint. Request-capture tests are sufficient: this client decision
does not require a live runtime, network, model, or two-machine run.

## Likely reuse seams

No implementation is authorized, but the current seams are deliberately
small:

* `src/home_ai_cluster/commands/chat_command.py` supplies the closest parser,
  one-request `httpx` client construction, finite timeout, response validation,
  safe failure boundary, and three result formatters. A future summarize client
  should reuse or narrowly mirror these client-edge responsibilities, not the
  chat request model.
* `src/home_ai_cluster/core/models.py` supplies `SummarizeRequest` validation
  and the authoritative `ClusterResult` validator. It should remain the source
  of the 65,536-byte and result-shape rules rather than gaining a parallel CLI
  model.
* `src/home_ai_cluster/api/routes.py` is the native `/v1/summarize` authority;
  a client would consume, not alter, it.
* `src/home_ai_cluster/command.py` owns the closed root help and `_COMMANDS`
  delegation table. If accepted, it is the root integration seam; the root
  should still forward remaining arguments unchanged.
* `pyproject.toml` already maps `home-ai-cluster` and `hac` to that same root
  function. Option B needs no additional alias or entry point; Option D would.
* `tests/test_chat_command.py` and `tests/test_command.py` are the focused
  precedent for client and root-forwarding proof. `tests/test_routes.py` and
  `tests/test_core_models.py` already establish the endpoint and native
  summarize validation that the client must not duplicate inconsistently.

## Questions for any future RFC

1. Is observed manual-HTTP friction sufficient to justify a new durable root
   subcommand, or is the existing native API the appropriate boundary?
2. If accepted, should the initial input remain explicit `--text` only, or is
   there concrete evidence that a positional form adds enough value to justify
   two equal spellings?
3. Should the existing chat error category wording be generalized for a second
   capability, or should a summarize command use a parallel specific 404 line
   while preserving the same failure class?
4. Does the project want the chat formatter implementation shared narrowly, or
   duplicated in a small explicit summarize command to keep capability-specific
   request construction visible? This is an implementation choice after the
   public contract is accepted.

Until those questions are decided through the appropriate RFC process, the
accepted state remains: native bounded summarize API only; chat-only
OpenAI-compatible access; seven root subcommands; and no summarize CLI.
