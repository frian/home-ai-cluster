# Command Reference

Status: Current

`hac` is the short installed operator command; `home-ai-cluster` is the
canonical long root command. Both dispatch the same ordinary subcommands. This
page uses `hac` for readability. From a repository checkout, verified standalone
commands can also be run with `uv run`.

This is a lookup reference for current ordinary behavior, not a guide to the
historical proof-only commands retained in the repository.

## Invocation forms

Install the package for ordinary operator use:

```sh
uv tool install .
```

After changing a checkout, rebuild and refresh that installed snapshot without
reusing cached build artifacts:

```sh
uv tool install --force --no-cache .
```

`--force` replaces the installed tool environment. `--no-cache` ensures the
refresh does not reuse cached build artifacts from an earlier checkout state.

Use either root form:

```sh
hac <subcommand>
home-ai-cluster <subcommand>
```

For checkout use, first run `uv sync`, then use the verified standalone script
where one exists, for example `uv run home-ai-cluster-local` or `uv run
home-ai-cluster-preflight`.

## Quick command map

The ordinary root surface has thirteen commands: three foreground processes and
ten finite commands.

| Command | Purpose | Process type |
| ------- | ------- | ------------ |
| `local` | Run one local ordinary application. | Foreground service |
| `static-cluster` | Run one explicit static cluster with the local node and one or more declared remote nodes. | Foreground service |
| `compatibility` | Run the narrow loopback OpenAI-compatible chat surface. | Foreground service |
| `aider` | Run one bounded external Aider code edit. | One-shot caller edge |
| `external-information` | Acquire bounded evidence for one source-grounded Chat request. | One-shot caller edge |
| `chat` | Send one native chat request. | One-shot request |
| `code` | Send one native bounded textual code request. | One-shot request |
| `code-file` | Replace one selected file from one bounded code result. | One-shot caller edge |
| `summarize` | Send one native bounded summarize request. | One-shot request |
| `classify` | Send one native bounded classification request. | One-shot request |
| `preflight` | Inspect static declaration coherence. | Finite inspection |
| `health` | Observe local runtime health. | Finite inspection |
| `status` | Inspect one declared static cluster. | Finite inspection |

## `hac local`

**Purpose:** Start the ordinary local application in the foreground.

**Common forms:**

```sh
hac local
hac local --host 127.0.0.1 --port 8000
hac local --runtime ollama --ollama-model <MODEL_IDENTIFIER>
hac local --runtime ollama --ollama-disable-thinking
hac local --runtime-config <PATH>
hac local \
  --runtime llama-server \
  --llama-server-base-url http://127.0.0.1:<LLAMA_SERVER_PORT> \
  --llama-server-model <MODEL_IDENTIFIER>
```

**Important behavior:** The default runtime is Ollama. The closed runtime choices
are `ollama` and `llama-server`; `--ollama-model` is optional only with Ollama
and omission keeps `llama3.2`; llama-server requires both of its explicit
arguments. The application runs in the foreground. Home AI Cluster does not
install, start, stop, download models for, or supervise the external runtime.
Ordinary local compositions advertise and execute `chat`, `summarize`,
`classify`, and `code`.
`--ollama-disable-thinking` is Ollama-only and configures the process-local
Ollama adapter: it requests native `think: false` for every adapter inference.
Omission preserves the existing request shape (no `think` field). It is not a
per-request or per-capability setting.

`--runtime-config <PATH>` selects one explicit TOML runtime-composition file.
It has a closed `ollama` or `llama-server` schema: Ollama accepts optional
`model` and `disable_thinking` values in `[ollama]`; llama-server requires
`base_url` and `model` in `[llama_server]`. There is no implicit config-file
discovery. File mode is mutually exclusive with equivalent runtime-composition
options explicitly supplied by the operator; parser defaults do not conflict.
The file and CLI options are not merged.

An Ollama runtime-composition file can be:

```toml
runtime = "ollama"

[ollama]
model = "qwen3:8b"
disable_thinking = true
```

For Ollama, `[ollama]`, `model`, and `disable_thinking` are all optional;
omission preserves the existing defaults.

A llama-server runtime-composition file is:

```toml
runtime = "llama-server"

[llama_server]
base_url = "http://127.0.0.1:8080"
model = "model-name"
```

Both llama-server values are required. Runtime-composition files configure only
the caller-local runtime and remain separate from static topology declarations.

When the selected host is exactly `127.0.0.1`, open
`http://127.0.0.1:8000/` for the fixed same-origin browser page. It contains
Chat, Summarize, Classify, and Code. The page keeps Chat only in memory, shows
per-assistant node attribution, and shows accessible active feedback while a
request is running. Each view permits at most one active request, while distinct
views may have independent in-flight requests; the selected node or runtime may
still queue their execution. One explicitly selected Summarize or Classify file is read
locally with strict UTF-8 decoding and populates that view's editable text area;
the current textarea value is submitted through the existing JSON text request.
Classify preserves ordered labels and sends no multipart data or filename. Every
other `--host` value remains API-only, including `0.0.0.0`, `localhost`, and
`::1`; the page is not a LAN browser interface, dashboard, operator console, or
compatibility interface.

**See also:** [Canonical operator workflow](operator-workflow.md).

## `hac static-cluster`

**Purpose:** Start an ordinary explicit static cluster with the fixed local node
and one or more declared remote nodes.

**Common forms:**

```sh
hac static-cluster --declaration <PATH>
hac static-cluster --declaration <PATH> --runtime ollama --ollama-model <MODEL_IDENTIFIER>
hac static-cluster --declaration <PATH> --runtime ollama --ollama-disable-thinking
hac static-cluster --declaration <PATH> --runtime-config <PATH>
hac static-cluster \
  --remote-node-id <NODE_ID> \
  --remote-base-url <BASE_URL> \
  --local-capability chat \
  --remote-capability chat \
  --remote-capability summarize
```

**Important behavior:** Declaration and inline topology modes are mutually
exclusive. Declaration mode supports one or more ordered remote nodes. The
retained inline mode supports exactly one remote node. The same verified local
runtime-composition options as `hac local` are accepted. Topology is static and
explicit, and routing remains local-first and capability-centered. The process
does not discover, start, stop, supervise, or repair remote machines or runtimes.
Its optional Ollama-specific `--ollama-model` configures only the local runtime
composition; omission keeps `llama3.2` and remote declarations carry no model.
Its optional Ollama-specific `--ollama-disable-thinking` likewise configures
only that process-local adapter, requests native `think: false` for every local
adapter inference, and is neither per-request nor per-capability. Omission
preserves the existing native request shape; remote declarations carry no such
setting.
`--runtime-config <PATH>` uses the same explicit closed runtime-composition
contract as `hac local`; topology declarations remain separate.
The accepted explicit capability names are `chat`, `summarize`, `classify`, and
`code`:
use `capabilities = ["..."]` in ordered TOML entries, `remote_capabilities =
["..."]` in the legacy flat TOML form, or repeat `--remote-capability <NAME>`
for the one-remote inline form. Omission retains only `chat` plus `summarize`,
so `classify` and `code` eligibility are always explicit.
Caller-local routing capabilities use `local_capabilities = ["..."]` at the
TOML root or repeated `--local-capability <NAME>` in the complete inline form.
They control only which capabilities the caller-side static-cluster router may
consider locally; they do not disable adapters, change runtime health, remove
endpoints, configure `hac local`, change receiver behavior, verify remote
runtime capability, select a target node, or create scheduling or preference.
Omission also retains local `chat` plus `summarize`. Explicit local and remote
sets must be non-empty and use only the accepted explicit names; duplicates and
unknown names are rejected. Capability membership controls eligibility only, and its
order is not priority. Remote declaration order remains the only remote priority
rule. Declarations do not probe remotes or schedule requests.

**See also:** [Canonical operator workflow](operator-workflow.md) for declaration
examples.

## `hac compatibility`

**Purpose:** Start the separate narrow OpenAI-compatible chat process.

**Common forms:**

```sh
hac compatibility
hac compatibility --declaration <PATH>
```

**Important behavior:** It is loopback-only by default and runs in the
foreground. It provides narrow, non-streaming chat-completions compatibility,
not the internal cluster protocol or general OpenAI API compatibility.
Summarize, classify, and code are not supported through this Chat-only surface.

**See also:** [README compatibility guidance](../README.md#run-the-minimal-openai-compatible-endpoint).

## `hac chat`

**Purpose:** Send one native chat request to an already-running ordinary process.

**Common forms:**

```sh
hac chat "Hello"
hac chat --message "Hello"
hac chat --timeout-seconds 300 "Hello"
hac chat "Hello" --verbose
hac chat "Hello" --json
```

**Important behavior:** The command sends one request to the fixed local caller
endpoint; it does not start the application. It remains topology-blind and
returns cluster-owned execution attribution. Request content is not retained by
this command. `--timeout-seconds SECONDS` accepts one base-10 integer from `1`
through `3600` for this invocation; omission keeps the 120-second default. The
value is the HTTP client's pool/connect/write/read scalar timeout, not a total
deadline. It adds no retry or cancellation. A timeout does not prove work has
stopped elsewhere, so do not immediately repeat a timed-out request on slow
hardware without accepting that it can create additional work.

**See also:** [Canonical operator workflow](operator-workflow.md).

## `hac external-information`

**Purpose:** Explicitly acquire one bounded source-evidence set through one
selected separately installed plugin, then send it through the existing
source-grounded Chat boundary.

**Form:**

```sh
hac external-information \
  --plugin <NAME> \
  --query "<EXPLICIT_OPERATOR_QUERY>" \
  --question "<OPERATOR_QUESTION>"
```

`--timeout-seconds SECONDS`, `--verbose`, and `--json` use the same caller
presentation and HTTP conventions as `hac chat`. The timeout accepts one
base-10 integer from `1` through `3600`, with a 120-second default.

**Important behavior:** No provider is bundled. The operator must explicitly
select one compatible separately installed plugin by its exact entry-point name.
Only this finite caller edge discovers and loads that plugin; the ordinary HAC
server does not discover, import, configure, or invoke acquisition plugins.
Here, "separately installed" means a compatible Python distribution in the same
Python environment that provides `hac`. HAC discovers it only through
`importlib.metadata.entry_points()` in
`home_ai_cluster.external_information_acquisition.v1`, not from a HAC
`plugins/` directory or filesystem scan. For an isolated `uv` tool, additional
plugin requirements belong in that same tool environment; for a project
checkout, install them into that project's `.venv`. Provider-specific
installation instructions belong to the provider plugin documentation.
Installation alone neither loads a plugin nor grants network access: ordinary
HAC startup, ordinary Chat, and the ordinary server remain unchanged.
The plugin receives only `--query`, may make its own one bounded provider
operation under its own configuration, credentials, and network limits, and
returns bounded title/URL/content candidates. HAC reconstructs and validates
RFC-0077 source evidence before sending exactly one validated body to existing
`/v1/chat/sources`; ordinary `capability=chat` routing then applies unchanged.

`--timeout-seconds` governs only that native HAC HTTP request. It does not
impose a timeout on plugin acquisition. The command has no provider selection,
fallback, retry, plugin enumeration, generic plugin configuration, new
capability, URL fetching, or ordinary-server network authority.

## `hac code`

**Purpose:** Send one native bounded textual code request to an already-running
ordinary process.

**Common forms:**

```sh
hac code --message "<OPERATOR_SUPPLIED_CODE_REQUEST>"
hac code --timeout-seconds 300 --message "<OPERATOR_SUPPLIED_CODE_REQUEST>"
hac code --message "<OPERATOR_SUPPLIED_CODE_REQUEST>" --verbose
hac code --message "<OPERATOR_SUPPLIED_CODE_REQUEST>" --json
```

**Important behavior:** The command requires exactly one explicit, non-blank
`--message`; it does not read code from a file or stdin. Its initial one-message
request is limited to 65,536 UTF-8 bytes and is never truncated. The client is
topology-blind: it explicitly sends `capability=code` through the existing
native `POST /v1/chat` endpoint, does not start or inspect the process, and
uses the existing 120-second omission default and per-invocation HTTP-client
timeout behavior. Default output is free-form text, `--verbose` adds execution
attribution, and `--json` returns the structured result. A topology with no
eligible code capability produces a safe no-capability failure.

Generated code is response text only. This command grants no filesystem,
repository, shell, Git, testing, tool, function, agent, or execution authority.
It does not add `/v1/code` or a standalone `home-ai-cluster-code` command.

**See also:** [Canonical operator workflow](operator-workflow.md).

## `hac code-file`

**Purpose:** Replace one explicitly selected text file from one native bounded
code result, creating one explicitly named missing leaf only when its parent
already exists.

**Common forms:**

```sh
hac code-file --file <PATH> --message "<OPERATOR_SUPPLIED_CODE_REQUEST>"
hac code-file --file <PATH> --message "<OPERATOR_SUPPLIED_CODE_REQUEST>" --timeout-seconds 300
```

**Important behavior:** The command accepts exactly one explicit target and one
non-blank `--message`. An existing target must be a regular, non-symbolic-link
UTF-8 file. One explicitly named missing leaf may be created with exclusive
non-overwriting creation only after input, parent, timeout, and
empty-current-content request validation; its parent must already exist as a
directory. It creates no parent, and a later failure may leave the requested
new target empty without rollback deletion. It sends exactly one existing native
`POST /v1/chat` request with
`capability=code`; the two request messages contain a fixed response instruction
plus the operator instruction and exact current file text (empty for a new
target), never the target path or filename. The existing 65,536-byte aggregate
code-input bound and a separate 65,536-byte UTF-8 generated-content bound apply
without truncation.

Only a closed JSON envelope containing version `1` and complete replacement
content is accepted. After all validation, the caller writes one private
same-directory temporary file, preserves only the target's ordinary `0o777`
permission bits, and atomically replaces the selected target once. It does not
execute generated content, does not retry, and adds no endpoint, capability,
standalone executable, or Aider behavior.

## `hac aider`

**Purpose:** Coordinate one bounded external Aider edit of one explicitly
selected file through the existing native `code` capability.

**Common forms:**

```sh
hac aider --file <PATH> --message "<REQUEST>"
hac aider --file <PATH> --message "<REQUEST>" --timeout-seconds 300
```

**Important behavior:** This optional caller edge requires external Aider
exactly 0.86.2 and an already-running `hac local` or `hac static-cluster`
process. It accepts exactly one target and one non-blank message. An existing
target is read and edited by Aider; a missing target may be created only as the
one named empty file after input, parent, and Aider prerequisite checks pass.
Its parent must already exist as a directory, creation never overwrites an
existing target, and a later failure does not delete a newly created target.
Missing or wrong-version Aider creates no target.

Each invocation launches one Aider subprocess and one private, ephemeral
IPv4-loopback translator. One Aider-shaped request is required; at most one
additional Aider-owned follow-up is permitted, for a maximum of two native
`capability=code` requests. The first native interaction must succeed before a
follow-up is allowed; this is not HAC retry behavior, and a third request fails
closed. Exactly the selected target is editable: model-proposed additional
existing or missing paths are automatically rejected and do not require
interactive path approval. There is no Aider chat session, Git, test, lint, or
shell automation. The translator is not RFC-0031 compatibility, which remains
Chat-only. HAC core remains text-only; Aider retains target-content authority.
All existing privacy and execution guardrails remain unchanged.
`--timeout-seconds` accepts one base-10 integer from `1` through `3600`, with a
120-second omission default, and applies independently to each native HAC
request.

## `hac summarize`

**Purpose:** Send one native bounded summarize request to an already-running
ordinary process.

**Common forms:**

```sh
hac summarize --text "Text to summarize"
hac summarize --timeout-seconds 300 --text "Text to summarize"
printf 'Text to summarize' | hac summarize
hac summarize --file README.md
hac summarize < README.md
git diff | hac summarize
hac summarize --file README.md --verbose
hac summarize --file README.md --json
```

**Important behavior:** `--text` and `--file` are mutually exclusive. With
neither, stdin is used; either explicit source ignores stdin. `--file` accepts
one regular file using ordinary operating-system path semantics: it does not
expand `~`, environment variables, or globs, and does not treat `--file -`
specially. Sources must be strict UTF-8 and at most 65,536 bytes. Oversized
input is rejected, never truncated. Content, `--verbose`, and `--json` are the
supported output modes. `--timeout-seconds SECONDS` uses the same base-10
integer range (`1` through `3600`) and 120-second omission default as `hac
chat`. It is the HTTP client's pool/connect/write/read scalar timeout, not a
total deadline; it adds no retry or cancellation. A timeout does not prove that
work has stopped elsewhere, so avoid immediately repeating a timed-out request
on slow hardware unless additional work is acceptable.

**See also:** [Canonical operator workflow](operator-workflow.md).

## `hac classify`

**Purpose:** Send one native bounded classification request to an already-running
ordinary process.

**Common forms:**

```sh
hac classify --text "The invoice is due tomorrow." --label invoice --label personal
hac classify --timeout-seconds 300 --text "The invoice is due tomorrow." --label invoice --label personal
printf '%s' 'The payment failed.' | hac classify --label technical --label billing
hac classify --file <PATH> --label label-a --label label-b --verbose
hac classify --file <PATH> --label label-a --label label-b --json
```

**Important behavior:** The command accepts exactly one bounded source through
`--text`, `--file`, or stdin when neither explicit source is supplied. `--text`
and `--file` are mutually exclusive, and either explicit source ignores stdin.
Sources are strict UTF-8 and at most 65,536 bytes; they are never truncated.
Labels are supplied through repeated ordered `--label` options: at least two and
at most 32 are required. Labels are exact values; there is no trimming, case
folding, Unicode normalization, fuzzy matching, prose repair, implicit
`unknown`, score, rationale, or multi-label result. The adapter proposes one
label and the cluster accepts it only when it exactly belongs to the supplied
label set. A successful minimal result contains `selected_label` and `node_id`.

Default, `--verbose`, and `--json` are the supported output modes.
`--timeout-seconds SECONDS` has the same `1` through `3600` range, 120-second
omission default, and one-shot HTTP-client ownership as chat and summarize; it
adds no retry, cancellation, total deadline, server timeout, or runtime timeout.
The client is topology-blind and does not start, configure, inspect, or manage
the process. Safe failures do not expose source text, labels, runtime details,
or raw adapter output.

**See also:** [Canonical operator workflow](operator-workflow.md).

## `hac preflight`

**Purpose:** Inspect local or explicit static declaration coherence.

**Common forms:**

```sh
hac preflight
hac preflight --json
hac preflight --declaration <PATH>
hac preflight --declaration <PATH> --json
hac preflight \
  --remote-node-id <NODE_ID> \
  --remote-base-url <BASE_URL> \
  --local-capability chat \
  --remote-capability summarize
```

**Important behavior:** This is static validation only: it does not observe a
runtime or remote network. Default output is human-readable; `--json` provides
compact structured output. A coherent result does not prove that a runtime or
remote application is available. Inline preflight projects the same caller-local
routing capability set as inline `hac static-cluster`; declaration and inline
topology modes remain mutually exclusive. `hac local` and standalone local-only
preflight remain unchanged.

**See also:** [Canonical operator workflow](operator-workflow.md).

## `hac health`

**Purpose:** Take one finite local runtime-health snapshot.

**Common forms:**

```sh
hac health
hac health --json
```

**Important behavior:** It observes only the local runtime, not remote nodes.
It does not monitor, poll, or change routing. Default output is human-readable;
`--json` is structured output. Unavailable observations can be result data
rather than a whole-command failure.

**See also:** [Canonical operator workflow](operator-workflow.md).

## `hac status`

**Purpose:** Inspect one declared static cluster.

**Common forms:**

```sh
hac status --declaration <PATH>
hac status --declaration <PATH> --json
hac status --declaration <PATH> --runtime ollama --ollama-model <MODEL_IDENTIFIER>
hac status --declaration <PATH> --runtime-config <PATH>
hac status \
  --declaration <PATH> \
  --runtime llama-server \
  --llama-server-base-url http://127.0.0.1:<LLAMA_SERVER_PORT> \
  --llama-server-model <MODEL_IDENTIFIER>
```

**Important behavior:** The declaration is validated before observations. The
local node is reported first and remotes follow declaration order. Observation
is finite and read-only: it does not change routing, topology, lifecycle, or
the declaration. Default output is human-readable; `--json` is compact
structured output. Unreachable or unavailable nodes can appear as result data
without making the command invocation invalid.
`--runtime-config <PATH>` uses the same explicit closed runtime-composition
contract as `hac local` and does not change status output.

**See also:** [Canonical operator workflow](operator-workflow.md).

## Output conventions

Service commands stay in the foreground. Chat, code, and summarize return
content by default; classify returns its selected label. Their `--verbose` forms
include execution attribution and their `--json` forms return compact structured
results. Successful `code-file` replacement is silent. Inspection commands are human-readable by default and offer `--json`
for automation. Individual command support is shown above.

## Common failure boundaries

Commands use stable project-owned failures and avoid exposing runtime URLs,
private addresses, raw exceptions, source contents, and stack traces. Where a
command contract requires it, local input is validated before network activity.
See the relevant command section for its specific boundary.

## Repository-checkout commands

After `uv sync`, these ordinary root forms have verified standalone checkout
scripts:

| Installed root | Repository checkout |
| -------------- | ------------------- |
| `hac local` | `uv run home-ai-cluster-local` |
| `hac static-cluster` | `uv run home-ai-cluster-static-cluster` |
| `hac compatibility` | `uv run home-ai-cluster-openai-compatibility` |
| `hac chat` | `uv run home-ai-cluster-chat` |
| `hac preflight` | `uv run home-ai-cluster-preflight` |
| `hac health` | `uv run home-ai-cluster-health` |
| `hac status` | `uv run home-ai-cluster-status` |

`hac code`, `hac code-file`, `hac summarize`, and `hac classify` are available through the
ordinary root command; none has a separate installed checkout script.

## Historical and specialized commands

The repository also retains historical proof and specialized operator commands,
including static proof, routing explanation, actual-request explanation, and
history inspection and clearing. They are not part of the ordinary ten-command
root surface and are intentionally not fully documented here.

All four historical installed proof launchers were retired by RFC-0075; their
commands remain in historical records and require the matching historical
repository revision for exact reproduction.

**See also:** [Documentation index](README.md), retained proof documents, and
the [RFC index](../RFC/README.md).

## Related documentation

- [Project README](../README.md) — project entry point, installation, and common
  examples.
- [Canonical operator workflow](operator-workflow.md) — procedural start, check,
  stop, and recovery sequence.
- [Documentation index](README.md) — current guidance and historical records.
- [RFC index](../RFC/README.md) — accepted architectural decisions.
