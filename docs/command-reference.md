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

| Command | Purpose | Process type |
| ------- | ------- | ------------ |
| `local` | Run one local ordinary application. | Foreground service |
| `static-cluster` | Run one explicit static cluster with the local node and one or more declared remote nodes. | Foreground service |
| `compatibility` | Run the narrow loopback OpenAI-compatible chat surface. | Foreground service |
| `chat` | Send one native chat request. | One-shot request |
| `summarize` | Send one native bounded summarize request. | One-shot request |
| `preflight` | Inspect static declaration coherence. | Finite inspection |
| `health` | Observe local runtime health. | Finite inspection |
| `status` | Inspect one declared static cluster. | Finite inspection |

## `hac local`

**Purpose:** Start the ordinary local application in the foreground.

**Common forms:**

```sh
hac local
hac local --host 127.0.0.1 --port 8000
hac local \
  --runtime llama-server \
  --llama-server-base-url http://127.0.0.1:<LLAMA_SERVER_PORT> \
  --llama-server-model <MODEL_IDENTIFIER>
```

**Important behavior:** The default runtime is Ollama. The closed runtime choices
are `ollama` and `llama-server`; llama-server requires both of its explicit
arguments. The application runs in the foreground. Home AI Cluster does not
install, start, stop, download models for, or supervise the external runtime.

**See also:** [Canonical operator workflow](operator-workflow.md).

## `hac static-cluster`

**Purpose:** Start an ordinary explicit static cluster with the fixed local node
and one or more declared remote nodes.

**Common forms:**

```sh
hac static-cluster --declaration <PATH>
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
Each remote may declare the closed capability set `chat` and/or `summarize`:
use `capabilities = ["..."]` in ordered TOML entries, `remote_capabilities =
["..."]` in the legacy flat TOML form, or repeat `--remote-capability <NAME>`
for the one-remote inline form. Omission retains `chat` plus `summarize`.
Caller-local routing capabilities use `local_capabilities = ["..."]` at the
TOML root or repeated `--local-capability <NAME>` in the complete inline form.
They control only which capabilities the caller-side static-cluster router may
consider locally; they do not disable adapters, change runtime health, remove
endpoints, configure `hac local`, change receiver behavior, verify remote
runtime capability, select a target node, or create scheduling or preference.
Omission also retains local `chat` plus `summarize`. Explicit local and remote
sets must be non-empty and use only `chat` or `summarize`; duplicates and unknown
names are rejected. Capability membership controls eligibility only, and its
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
not the internal cluster protocol or general OpenAI API compatibility. Summarize
is not supported through this surface.

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

**See also:** [Canonical operator workflow](operator-workflow.md).

## Output conventions

Service commands stay in the foreground. Request commands return content by
default; their `--verbose` forms include execution attribution and their `--json`
forms return compact structured results. Inspection commands are human-readable
by default and offer `--json` for automation. Individual command support is
shown above.

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

`hac summarize` is available through the ordinary root command; there is no
separate installed summarize checkout script.

## Historical and specialized commands

The repository also retains historical proof and specialized operator commands,
including static proof, routing explanation, actual-request explanation, and
history inspection and clearing. They are not part of the ordinary eight-command
root surface and are intentionally not fully documented here.

**See also:** [Documentation index](README.md), retained proof documents, and
the [RFC index](../RFC/README.md).

## Related documentation

- [Project README](../README.md) — project entry point, installation, and common
  examples.
- [Canonical operator workflow](operator-workflow.md) — procedural start, check,
  stop, and recovery sequence.
- [Documentation index](README.md) — current guidance and historical records.
- [RFC index](../RFC/README.md) — accepted architectural decisions.
