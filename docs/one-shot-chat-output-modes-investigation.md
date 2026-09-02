# One-shot chat output modes investigation

## Status

Investigation only. This document proposes no accepted command behavior and does not modify RFC-0045.

## Observed friction

`home-ai-cluster-chat --message "Hello"` currently prints one compact complete `ClusterResult`. That is useful to scripts, but it makes the ordinary generated answer less direct to read at a terminal. Phase 17 established an explicit human-default/`--json` pattern for three finite inspection commands, not for request-and-response commands.

## Current accepted contract

RFC-0045 defines one required `--message` option; exactly one non-whitespace user message; fixed `chat` capability; and exactly one `POST` to the fixed loopback `/v1/chat` endpoint. It prohibits positional and standard-input input, files, sessions, selectors, configuration, retry, fallback, topology knowledge, and streaming.

On a successful HTTP response that validates as the authoritative `ClusterResult`, stdout MUST contain exactly one compact JSON object for the complete result; stderr MUST be empty; and exit status MUST be zero. RFC-0045 explicitly prohibits content-only output, renamed fields, wrapper metadata, pretty printing, colors, output-format selection, and partial output. Its alternatives explicitly reject content-only output because it loses normalized truthful attribution.

Failures are independent of a completed result: stdout is empty, stderr is one prompt-free stable line, and the command exits non-zero. Invalid local input is `error: invalid request input` with exit 2. Connection failure or timeout is `error: ordinary cluster unavailable`; HTTP 422, 404, and 503 map respectively to `cluster rejected request`, `no available chat capability`, and `runtime adapter unavailable`; malformed successful JSON/result data maps to `invalid cluster response`; all other client or HTTP failures map to `ordinary request failed`. Those failure lines retain the `error: ` prefix in the actual contract.

The command has one finite implementation-owned timeout and no retry or client-side fallback. It must not retain messages, generated responses, requests, or responses; it must not log prompt or generated content, create files, or add history. Direct stdout remains operator output rather than project-controlled persistence.

## Current implementation

`chat_command.py` uses a private `argparse.ArgumentParser` subclass so parser failures become the RFC-0045 invalid-input category. `--message` uses `append`; the parser requires exactly one value and rejects empty or whitespace-only text without altering another value.

It builds `ClusterRequest(messages=[ChatMessage(role="user", content=message)], capability=Capability(name="chat"))`, projects the native `messages` and `capability` JSON envelope, and makes one `httpx.Client` POST to `http://127.0.0.1:8000/v1/chat`, with a 30-second timeout and redirects disabled. It maps transport and HTTP failures before parsing a success body. For a 2xx response it calls `response.json()` and validates it with `ClusterResult.model_validate`; arbitrary successful JSON is not passed through. It currently serializes `result.model_dump()` with `json.dumps(..., separators=(",", ":"))` through `print`, which writes one final newline.

`ClusterResult` is the authoritative current model: `content: str`, non-empty `adapter: str`, optional `model: str | None`, and non-empty `node_id: str`. Thus an absent model is represented as `null`, not an empty-field omission; the current model permits an empty string, so a future presentation rule must also say what to do with that value.

Focused tests in `tests/test_chat_command.py` assert one exact request, fixed URL and content type, preserved message whitespace, compact JSON that parses to the complete result, exactly one newline, empty stderr, and exit 0 for both a string model and `None`. They also protect every stable failure mapping, empty stdout on failure, prompt-free errors, invalid result rejection, and no request for invalid input or help. They do not currently assert byte-for-byte field order or non-ASCII JSON escaping, although the implementation's model dump and default `json.dumps` behavior determine both today.

## Phase 17 precedent and semantic difference

RFC-0048 applies exactly to preflight, health, and status. Those commands first produce completed inspection results, then use a command-specific pure formatter at the CLI edge. Default human text and explicit `--json` do not depend on TTY, pipes, redirection, environment, configuration, terminal width, or color. `--json` preserves the former compact representation byte-for-byte, including ordering and one trailing newline; selected representation does not change evaluation, observations, stderr, or exit status. Phase 17 explicitly excludes chat and rejects a generic formatter/framework.

That precedent is relevant for explicit selection, exact JSON preservation, CLI-edge formatting, and narrow implementation. It is not a decision for chat. Preflight, health, and status are finite inspection commands that expose no prompt or generated response. Chat is primarily a request-and-response command; content may therefore be the most useful default, but that is a new product and compatibility decision rather than an automatic extension of inspection output.

## Candidate output modes

The candidate is:

```text
default        content only
-v/--verbose   content plus human-readable execution attribution
--json         historical compact ClusterResult JSON
```

It is coherent only if all modes project one already validated completed `ClusterResult` after the existing request path completes. Mode selection must not alter argument validation, request construction, HTTP execution, timeout, response validation, routing, fallback, topology, runtime selection, error mapping, or privacy.

`-v`/`--verbose` and `--json` should be mutually exclusive. JSON is the one machine representation; combining it with prose would either violate that contract or create precedence/dual-output ambiguity. An RFC should select the parser-visible local error and exit behavior for the invalid combination, while keeping the normal execution failures identical in every valid mode.

## Content fidelity and newline semantics

Generated content may contain multiple lines, blank lines, Markdown, code fences, leading whitespace, trailing whitespace, no final newline, an existing final newline, and Unicode. The default content mode should project `content` without stripping, reindenting, escaping, wrapping, Markdown rendering, or otherwise normalizing it. That preserves all of those properties, including Unicode and whitespace inside the content.

The unresolved terminal rule is whether to preserve content byte-for-byte or ensure one terminal newline. Appending one newline improves ordinary shell display but changes a no-final-newline response and turns an existing final newline into two. Byte-for-byte projection is the most faithful definition and avoids a content-dependent exception, but a shell prompt can then appear on the same line. A third rule such as “append only if absent” also changes some responses and makes output conditional. The recommended RFC decision is byte-for-byte projection for content mode; normal CLI newline convention is not worth silently changing model output. It should state text/Unicode semantics rather than make an unprovable byte claim after Python text decoding.

Verbose output can delimit safely without modifying response content: write a fixed `Response:` heading and separator before content, write content exactly once, then write a fixed execution block only after an explicitly defined delimiter. This still needs a rule for content lacking a final newline: the formatter must supply structural separator text outside the content, not append or indent the content itself. An RFC should specify the exact delimiter and terminal newline behavior, including empty content (which the current model allows).

## Verbose attribution

The candidate labels `Node`, `Adapter`, and `Model` accurately project the existing `node_id`, `adapter`, and `model` fields and match the Phase 17 human label style. Exact labels, capitalization, ordering, indentation, section headings, and treatment of a missing model are durable operator-output choices and require the new RFC, not implementation discretion.

For `model is None`, verbose output should omit the `Model` line rather than invent an attribution value such as `unknown` or `none`; it is optional in the authoritative result. Empty-string models need an explicit policy because the current model permits them. Omitting a `None` or empty value is the smallest human projection, but the RFC must decide it. `--json` must continue to emit `"model":null` or the actual string unchanged.

## JSON compatibility

If adopted, `--json` must preserve the historical successful output exactly: the `content`, `adapter`, `model`, `node_id` names and their current order; values including `null`; compact separators; Python's current JSON Unicode escaping behavior; one final newline; stdout only; empty stderr; and exit 0. It must contain neither prose nor wrapper fields. The accepted RFC should make these requirements byte-for-byte and add focused tests for representative Unicode and exact serialization, not merely JSON equivalence.

This preserves an explicit machine path, but it does not preserve no-option compatibility. Scripts parsing the current default JSON will receive generated content and can fail or silently misbehave. Requiring `--json` is an honest, clear migration path only if the RFC calls the no-option change breaking, documents it prominently, and makes no claim that compatibility is automatic.

## Failure and privacy boundaries

Every normal failure behavior should remain identical in every valid output mode: empty stdout, the same stable safe stderr line, and the same exit status. There is no completed result to format. Parsing invalid mode combinations is a new local-input failure decision, but it must occur before HTTP and not expose message, response, URLs, or private details.

Formatting a validated result at the command edge adds no routing or runtime knowledge and no project retention. It does make generated content more plainly visible in default and verbose terminal output, but successful JSON already contains it. The existing privacy boundary still prohibits logging, history, files, telemetry, prompt/response retention, and private details in errors.

## Alternatives

- Keep compact JSON as default: preserves compatibility and RFC-0045, but leaves the observed terminal-friction question unresolved.
- Make human response plus attribution the default: preserves transparency but makes the answer less copyable and still breaks default JSON consumers.
- Use content-only default with verbose attribution: best fits ordinary answer reading while making attribution available deliberately; this is the recommended candidate, subject to RFC review.
- Add only `--content-only`: preserves JSON default but makes the common terminal use verbose and leaves no human attribution convention.
- Use `--quiet`: is less clear than content-only and implies that truthful attribution is noise rather than an alternate presentation.
- Offer only `--json`, with no verbose mode: keeps one machine mode but removes the deliberate readable-attribution option.
- Select by environment or TTY: creates hidden and redirection-dependent behavior; Phase 17 is a strong precedent against it.
- Add a generic shared formatter: is disproportionate for one command and is explicitly outside the Phase 17 approach.

## Architectural assessment

This is not an implementation-level change under RFC-0045. That RFC expressly fixes compact JSON-only success output and rejects every central part of the candidate: content-only output, pretty/human output, output selection, and additional options. Changing the default also creates a lasting breaking CLI contract. The result model, request/transport boundary, and routing architecture need not change, but presentation and compatibility still require a documented decision before implementation.

One new narrow RFC is the smallest coherent next step. Its scope should decide only `home-ai-cluster-chat` success presentation: included modes and flags; mutual exclusion; exact content and structural-newline behavior; verbose labels, order, and optional-model handling; exact `--json` compatibility; migration; and preservation of existing failures, privacy, and execution semantics. It should require command-specific formatting only, no generic renderer or CLI output framework, no dependency, no core/transport model change, and no `/v1/chat` change.

The suggested title, **RFC-0049: Human-readable one-shot chat output**, is adequate if its scope explicitly includes the content-only default and historical-JSON compatibility, not only verbose prose. A slightly more exact title would be **RFC-0049: One-shot chat output modes**.

## Recommended next step

Draft one narrow RFC, preferably titled **RFC-0049: One-shot chat output modes**, before changing code or tests. Recommend the three-mode candidate with content-only default, mutually exclusive verbose and JSON modes, byte-faithful text projection, optional model-line omission, and exact explicit JSON preservation. The RFC review must decide the verbose structural delimiter and the exact handling of an empty model value; neither is accepted here.

## Non-goals

This investigation does not define a new phase, reopen Phase 17, amend RFC-0045, change the request schema or endpoint, alter core or transport models, add streaming, sessions, input sources, selectors, retry, fallback, topology, runtime behavior, logging, persistence, TTY detection, color, localization, a generic output framework, dependencies, or a dashboard.

## Files inspected

- Governing documents: `VISION.md`, `FOUNDATIONS.md`, `PRINCIPLES.md`, `NON_GOALS.md`, `ROADMAP.md`, `QUESTIONS.md`, `CONTRIBUTING.md`, `AGENTS.md`, and `RFC/README.md`.
- Accepted contracts relevant to this change: RFC-0045, RFC-0048, RFC-0023, RFC-0034, RFC-0036, RFC-0037, and RFC-0044.
- Current implementation and focused tests: `src/home_ai_cluster/commands/chat_command.py`, `src/home_ai_cluster/core/models.py`, and `tests/test_chat_command.py`.
- Current inspection formatter implementations and tests: `static_preflight.py`, `local_health_snapshot.py`, `status_command.py`, `test_static_preflight.py`, `test_local_health_snapshot.py`, and `test_status_command.py`.
- Phase 16 and 17 investigations, proofs, results, runbooks, and closeouts, including the ordinary request access, remote-request, and human-readable inspection-output records.
