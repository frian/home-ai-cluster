# Code Caller Integration Investigation

Status: Investigation only

Date: 2026-08-12

## Purpose and question

This documentation-only investigation asks:

> What is the smallest useful way for an external developer tool to explicitly
> require Home AI Cluster's accepted `code` capability, without automatically
> broadening the existing Chat-only OpenAI-compatible contract?

The representative existing developer tool is Aider. A human, shell script,
editor task, or deliberately small operator-owned subprocess caller is also in
scope. This is not an authorization to add a Home AI Cluster integration,
change an RFC, or make Aider the required solution.

The bounded practical goal is to create or modify a small local administration
or maintenance script without manually copying generated text. The caller must
explicitly require `code`; HAC returns text only; and a local caller tool such
as Aider owns any resulting file creation or edit. It is not autonomous
repository development, repository indexing, an IDE, or an agent loop.

## Current accepted boundaries

[RFC-0066](../RFC/RFC-0066-capability-admission-semantics.md) requires a
caller to explicitly require a closed capability; text, language names, model
names, and presumed intent cannot infer it. [RFC-0067](../RFC/RFC-0067-bounded-textual-code-assistance.md)
then accepts `code` as the bounded semantic requirement for textual code
generation, transformation, and explanation.

`code` reuses ordered plain-text messages and a free-form textual
`ClusterResult`. Its message content is bounded to 65,536 UTF-8 bytes, and
static `code` eligibility is explicit. It does not promise parseable source,
one code block, a patch, a diff, compilation, execution, or file operations.
Generated code is response text only.

RFC-0067 deliberately preserves these surface boundaries:

- `hac code --message TEXT` is the initial explicit native caller surface.
- Native `POST /v1/chat` carries an ordered-message request including the
  explicit `capability` field; there is no `/v1/code` endpoint.
- The loopback browser remains Chat, Summarize, and Classify only; it has no
  Code surface.
- RFC-0031 OpenAI compatibility remains Chat-only. It has no `code` model,
  endpoint, alias, field, routing behavior, or coding-prompt inference.

The distinction is intentional. A compatibility `model` value is an endpoint
identifier, not a runtime, node, model, or capability selector under
[RFC-0031](../RFC/RFC-0031-minimal-openai-compatible-chat-access.md).

## Verified current semantic baseline

Current source confirms all of the following:

| Fact | Evidence |
| --- | --- |
| Compatibility requests become `Capability(name="chat")`. | [`api/openai_compatibility.py`](../src/home_ai_cluster/api/openai_compatibility.py) validates only the fixed `home-ai-cluster` identifier and constructs the explicit `chat` request. |
| Existing Aider proofs demonstrate Chat access, not explicit `code`. | The retained [Aider access proof](phase-6-aider-access-proof.md) records the RFC-0031 `POST /v1/chat/completions` request; the [static-cluster proof](aider-static-cluster-proof.md) describes the same unchanged Chat-only compatibility response. |
| `hac code` explicitly requires `code`. | [`code_command.py`](../src/home_ai_cluster/code_command.py) constructs a one-message `ClusterRequest` with `Capability(name="code")`; [`command.py`](../src/home_ai_cluster/command.py) exposes it as `hac code`. |
| The initial command needs one explicit message. | The CLI accepts exactly one non-blank `--message`; it reads neither stdin nor a file. |
| Native ordered-message `/v1/chat` can carry `capability=code`. | [`api/routes.py`](../src/home_ai_cluster/api/routes.py) accepts `messages` and `capability`, then preserves that value in `ClusterRequest`. |
| No `/v1/code` route exists. | The native public route declarations are `/v1/chat`, `/v1/summarize`, and `/v1/classify`; the route and RFC-0067 provide no `/v1/code`. |
| No compatibility `code` alias exists. | The compatibility request accepts only `model == "home-ai-cluster"`, rejects unknown fields, and always translates to `chat`. |
| The browser has no Code surface. | [`web/index.html`](../src/home_ai_cluster/web/index.html) contains only Chat, Summarize, and Classify tabs; its script sends Chat with `capability: "chat"`. |

The native `/v1/chat` capability field is an accepted native request contract.
It is not evidence for adding an arbitrary capability switch to a different
Home AI Cluster command or compatibility surface.

## Existing Aider evidence

The historical proof evidence remains useful but has a narrow meaning:

- The [Phase 6 developer-tool investigation](phase-6-developer-tool-access-investigation.md)
  selected temporary client-side configuration for Aider through the strict
  compatibility endpoint.
- The [Aider access proof](phase-6-aider-access-proof.md) recorded Aider
  v0.86.0 successfully making one non-streaming, plain-text RFC-0031 request.
- The [Aider static-cluster proof](aider-static-cluster-proof.md) recorded one
  Aider v0.86.2 request reaching an already-declared remote through the
  compatibility edge. It retained an unchanged topology-blind compatibility
  response.

Those proofs establish useful Chat access and a bounded Chat routing
composition. Because RFC-0031 and current source translate those requests to
`chat`, neither proof demonstrates that Aider explicitly required RFC-0067
`code`. A coding-oriented prompt is not capability inference.

## Current Aider primary-source findings

The current official [OpenAI-compatible API guide](https://aider.chat/docs/llms/openai-compat.html)
documents an OpenAI-compatible endpoint configured with `OPENAI_API_BASE`,
`OPENAI_API_KEY`, and an `openai/<model-name>` model. Its current
[options reference](https://aider.chat/docs/config/options.html) documents
`--openai-api-base`, `--model`, model settings and aliases, but no native
operation selector, caller request-translation hook, or provider-plugin seam.

The current official source makes that boundary concrete:

- [`args.py`](https://raw.githubusercontent.com/Aider-AI/aider/main/aider/args.py)
  exposes an OpenAI API base URL and model/settings options.
- [`main.py`](https://raw.githubusercontent.com/Aider-AI/aider/main/aider/main.py)
  places that base URL in `OPENAI_API_BASE`.
- [`models.py`](https://raw.githubusercontent.com/Aider-AI/aider/main/aider/models.py)
  builds a model/messages/stream request and calls `litellm.completion(**kwargs)`.
  Model settings can alter supported completion parameters, but are not a
  caller-owned operation translator.

No supported Aider extension or provider mechanism was found in the examined
official documentation and current configuration/completion source that would
let Aider call a non-OpenAI Home AI Cluster native operation. This is a finding
about the inspected public mechanisms, not a claim that an operator cannot
write separate software.

The locally installed executable safely reported `aider 0.86.2` with its
version-only command. The official [aider-chat 0.86.2 PyPI release](https://pypi.org/project/aider-chat/0.86.2/)
also records 0.86.2 as the latest release and gives its publication date as
2026-02-12. GitHub Releases still marks
[v0.86.0](https://github.com/Aider-AI/aider/releases/tag/v0.86.0) as Latest.
This source discrepancy does not affect the integration conclusion: both the
locally observed executable and the official PyPI release establish 0.86.2 as
the relevant version evidence, while the inspected current source and public
configuration boundary remain the same.

## Caller authority versus Home AI Cluster authority

Home AI Cluster's accepted `code` authority ends at returning free-form text:

```text
explicit code request -> textual ClusterResult
```

It has no filesystem, repository, shell, Git, test, tool, function, or
execution authority. It neither interprets nor applies its result.

A caller tool can independently have authority over its own process, working
directory, files, Git repository, or test commands. Therefore this composition
preserves the RFC-0067 boundary:

```text
HAC returns text
  -> caller interprets text
  -> caller independently chooses whether to modify a file
```

That caller-side action is not HAC tool execution. It must remain clearly owned
and controlled by the caller, including any review, confirmation, Git, or test
policy. Conversely, text-only `code` does not guarantee output suitable for an
automatic write. It does not establish a response representation, parser,
patch protocol, executable program, or safe edit authority.

The boundaries are distinct:

| Concern | Owner and current meaning |
| --- | --- |
| Semantic capability | HAC: explicit `code` requirement and hard eligibility. |
| Response representation | HAC: free-form text with normalized attribution, not a patch/file contract. |
| Caller authority | Caller: optional file, Git, shell, test, and editing actions. |
| Model authority | None beyond generating response text; no model-directed tool authority exists. |
| Project-owned execution authority | None: HAC has not accepted it. |

## Candidate approaches

### A — Existing `hac code` as the caller interface

`hac code --message ...` already gives a human, shell script, editor task, or
tiny subprocess caller an explicit native `code` request. Its default stdout
is the free-form content; `--verbose` adds attribution for people, and `--json`
provides the existing structured result for a caller that needs attribution as
well as content.

The command uses ordinary native process ownership and exit behavior: input
validation exits with status 2; connection, timeout, request, response, and
no-capability failures exit non-zero; a successful response exits zero. A
subprocess can therefore treat stdout and status as its caller interface. It
remains topology-blind: it does not start or inspect the process, select a
node, or choose a runtime. An explicitly declared remote with `code` may be
eligible through normal static routing; a chat-only declaration is excluded.

Limits remain important. It accepts exactly one explicit message, does not
read stdin or a file, and has a 65,536-byte input bound. The caller, not HAC,
controls shell history, process arguments, redirection, and any subsequent
file action. Capturing output can remove manual copy/paste, but must not be
presented as a safe automatic editing contract: the output can be prose,
multiple blocks, or otherwise unsuitable for a target file.

For the clarified need, Candidate A is necessary but not sufficient on its
own: it proves explicit text assistance, not caller-owned file creation or
editing without a caller that understands and applies the response.

**Classification: already supported composition.** No Home AI Cluster change
is needed.

### B — Tiny caller speaking the existing native request

An operator-owned small program can send the existing native request directly:

```text
POST /v1/chat
messages: ordered plain-text messages
capability: code
```

This is already an accepted native API use, so it requires no Home AI Cluster
implementation. It may be a better fit than the one-message CLI when the
caller already owns ordered messages or wants to consume the normalized JSON
result. It is not a project-owned SDK, a new integration layer, or a reason to
create either.

It has the same privacy and authority boundary as Candidate A: HAC does not
retain prompts or responses by default, while the caller is responsible for
what it retains, logs, forwards, or does with returned text. The caller still
must not imply a file-edit guarantee from free-form output.

**Classification: already supported composition.** No Home AI Cluster change
is needed.

### C — Aider through its existing OpenAI-compatible path

Aider can use the existing strict RFC-0031 endpoint, as the retained proofs
show. It cannot truthfully obtain explicit RFC-0067 `code` semantics through
that path: the route constructs `Capability(name="chat")` for every accepted
request. A coding prompt, `openai/<model>` name, or Aider model setting cannot
change that semantic fact.

**Classification: deliberately out of scope for explicit `code`.** It remains
an already-supported Chat composition, but not a `code` caller interface.

### D — Current Aider caller-side extension/provider mechanism

The examined official Aider mechanisms configure an OpenAI-compatible
completion endpoint and its model/request settings. They do not provide a
supported extension seam that translates an Aider request into HAC-native
`POST /v1/chat` with `capability=code`. There is therefore no normal supported
Aider configuration or provider mechanism to prove that path without adding a
separate process.

**Classification: no suitable currently supported mechanism found.** A later
proof cannot claim native explicit `code` access by Aider solely from current
Aider configuration.

### E — Operator-owned local bridge

An operator could independently compose:

```text
Aider
  -> caller-owned local bridge
  -> existing HAC-native /v1/chat with capability=code
  -> Home AI Cluster
```

For a deliberately bounded proof, a temporary local bridge can own one
loopback OpenAI-shaped ingress compatible with the conservative Aider setup,
translate its accepted request into the existing HAC-native ordered-message
request with the bridge's explicit `capability=code`, and project the textual
`ClusterResult` into the minimal response Aider expects. The bridge owns that
translation, listener, response projection, and all resulting logging and
privacy choices. It must not select a HAC node, runtime, or model; infer
`code` from prompt content; execute returned text; inspect a repository itself;
or become a generic compatibility service.

HAC would still own only native request handling and free-form text results.
Any file/Git/test authority would remain with Aider or another caller, never
with HAC. This is therefore an external experimental composition, not a Home
AI Cluster-supported integration and not a new HAC access contract.

The bridge cannot make RFC-0067 output a guaranteed edit representation. That
does not prevent one bounded proof: the proof can establish that Aider, acting
under its own authority, applied a result in one disposable script file. It
must never generalize that observation into arbitrary safe automated editing
or HAC filesystem authority.

**Classification: caller-side configuration/integration only, with a justified
separate proof opportunity.** It requires no HAC implementation, but a
successful proof would not make it supported Aider `code` integration.

### F — Expand Home AI Cluster OpenAI compatibility

A second compatibility model identifier, model-like `code` mapping, a new
compatibility field, a coding-prompt mapping, or another compatibility endpoint
would change an accepted public access boundary. Under RFC-0031, model is not a
capability selector; under RFC-0067 compatibility is explicitly Chat-only; and
automatic mapping is forbidden by RFC-0066. A model alias would not be a
small implementation detail.

**Classification: new architectural decision requiring RFC.** It is neither
proposed nor authorized here.

## Comparison matrix

| Candidate | Explicit `code` requirement | HAC change | Small-script value | Aider native path | Classification |
| --- | --- | --- | --- | --- | --- |
| A. `hac code` | Yes | None | Text only | No | Already supported composition |
| B. Tiny native caller | Yes | None | Text only | No | Already supported composition |
| C. Existing Aider compatibility | No; always `chat` | None | Chat only | Yes | Deliberately out of scope for `code` |
| D. Aider extension/provider | No suitable supported seam found | None | Not established | Not established | No suitable current mechanism |
| E. Operator bridge | Yes, through bridge translation | None in HAC | Yes, for one caller-owned edit proof | Indirect only | Caller-side integration/proof opportunity |
| F. HAC compatibility expansion | Could be, only after a decision | Yes | Not needed for the bounded goal | Could be | New architectural decision requiring RFC |

## Practical small-script use case

For an explicit text-only request, Candidate A is the smallest useful
interface:

```text
operator or small caller
  -> hac code --message <explicit request>
  -> stdout content and exit status
  -> caller chooses display, review, capture, or an independently controlled edit
```

It keeps the important decision visible: a caller has requested the `code`
capability. A small native HTTP caller is equally valid when it needs ordered
messages or JSON. Neither route is an autonomous editor, and neither alone
proves file creation or editing without manual copy/paste.

For the clarified user value, Candidate E adds the smallest missing caller-side
composition:

```text
Aider owns file/edit authority
        |
        v
temporary caller-side bridge
        |
        | explicit capability=code
        v
Home AI Cluster
        |
        | text only
        v
caller-side Aider handling
        |
        v
small disposable script file changed
```

## Architectural classification and outcome

**Outcome B — a bounded caller-side Aider `code` proof is justified without HAC
changes.**

Existing Aider configuration alone cannot explicitly require RFC-0067 `code`:
its existing compatibility request reaches `chat`. Existing `hac code` and
native `POST /v1/chat` nevertheless already provide the correct explicit
`code` semantics. A small temporary caller-owned bridge can compose that
accepted native surface with Aider's caller-owned file edit behavior, which
addresses the clarified no-copy/paste small-script use case.

No RFC and no Home AI Cluster implementation are recommended now. The
recommended next step is a separate, opt-in proof, not a supported integration
claim. It should establish only one explicit request in a temporary working
directory or dedicated disposable Git repository/worktree, where Aider changes
one privacy-safe generic small script through the temporary bridge. It should
use no production repository, no automatic command execution, tests, or
commits, no unrelated network feature, and no retained real prompt or generated
script in project proof documentation. The observation must say separately that
HAC produced text and Aider changed the file under caller authority.

Aider configuration guardrails are not OS-level security sandboxing. This
investigation authorizes neither a sandbox implementation nor a claim that
Aider provides one.

If the project later wants to ship, maintain, or document this bridge as a
first-class HAC integration, the smallest exact architectural question for a
future RFC is:

> What explicit public access contract, if any, may translate a non-native
> developer-tool request into `capability=code` while preserving a fixed
> compatibility endpoint identifier, closed capability vocabulary, no model or
> prompt inference, text-only HAC authority, and the existing Chat-only
> compatibility contract?

That question does not presume OpenAI compatibility is the right answer. It
must not be answered by silently mapping a model-like value, prompt, or alias
to `code`. A future supported bridge decision requires architectural review and
may require an RFC; this external proof does not prejudge it.

## Explicitly deferred work

This investigation does not authorize general OpenAI-compatible capability
routing, arbitrary `--capability`, model aliases or selection, streaming,
tools/function calling, agents, filesystem/repository/shell/Git/test authority
for HAC, RAG, embeddings, repository indexing, a generic plugin framework or
SDK, persistence, a database, Docker, Kubernetes, browser Code UI, Monaco, or
network authority for a model.

The physical two-machine RFC-0067 `code` proof remains **pending**. This
investigation does not replace it: the retained
[bounded textual code assistance proof](bounded-textual-code-assistance-proof.md)
records only local positive and no-eligible-capability evidence.

The bounded web-access investigation for one capability remains the next
separate architectural investigation after this caller-side proof work unless
evidence changes priorities. It is not authorized, analyzed, or coupled to
caller integration here.

## Evidence sources

Repository sources inspected on 2026-08-12:

- [VISION](../VISION.md), [FOUNDATIONS](../FOUNDATIONS.md),
  [PRINCIPLES](../PRINCIPLES.md), [NON_GOALS](../NON_GOALS.md),
  [ROADMAP](../ROADMAP.md), [CONTRIBUTING](../CONTRIBUTING.md),
  [AGENTS](../AGENTS.md), and the [RFC index](../RFC/README.md);
- [RFC-0031](../RFC/RFC-0031-minimal-openai-compatible-chat-access.md),
  [RFC-0046](../RFC/RFC-0046-explicit-static-cluster-compatibility-access.md),
  [RFC-0066](../RFC/RFC-0066-capability-admission-semantics.md), and
  [RFC-0067](../RFC/RFC-0067-bounded-textual-code-assistance.md);
- [Phase 6 developer-tool investigation](phase-6-developer-tool-access-investigation.md),
  [Aider access proof](phase-6-aider-access-proof.md),
  [Aider static-cluster access investigation](aider-static-cluster-access-investigation.md),
  [Aider static-cluster proof](aider-static-cluster-proof.md),
  [bounded textual code assistance proof](bounded-textual-code-assistance-proof.md),
  [command reference](command-reference.md), and
  [canonical operator workflow](operator-workflow.md); and
- current `code` CLI, native route, compatibility translation, browser, and
  root-command sources linked in the verified baseline above.

Current primary Aider sources inspected on 2026-08-12:

- [OpenAI-compatible API guide](https://aider.chat/docs/llms/openai-compat.html);
- [options reference](https://aider.chat/docs/config/options.html);
- [current argument source](https://raw.githubusercontent.com/Aider-AI/aider/main/aider/args.py);
- [current main configuration source](https://raw.githubusercontent.com/Aider-AI/aider/main/aider/main.py);
- [current completion source](https://raw.githubusercontent.com/Aider-AI/aider/main/aider/models.py); and
- [aider-chat 0.86.2 PyPI release](https://pypi.org/project/aider-chat/0.86.2/); and
- [Aider v0.86.0 GitHub release page](https://github.com/Aider-AI/aider/releases/tag/v0.86.0).
