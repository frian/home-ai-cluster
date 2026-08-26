# Getting Started

Status: Current

This guide is the shortest path for a new user who wants to install Home AI
Cluster, run it locally, and try its ordinary capabilities.

Home AI Cluster is an orchestration layer. It does not install, download, start,
stop, or supervise AI runtimes or models. The default first-use path below uses
an operator-managed local Ollama runtime with the `llama3.2` model.

For exact command contracts and advanced options, use the
[command reference](command-reference.md). For the canonical operational
sequence and static multi-node operation, use the
[operator workflow](operator-workflow.md).

## 1. Install `uv`

Home AI Cluster uses `uv` for Python and package installation.

Install `uv` using the official procedure for your operating system:

- <https://docs.astral.sh/uv/getting-started/installation/>

On Linux and macOS, the official standalone installer can be run with:

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Open a new terminal if necessary, then verify the installation:

```sh
uv --version
```

## 2. Install a supported Python

Home AI Cluster currently supports Python 3.13 and 3.14.

The simplest `uv`-managed path is:

```sh
uv python install 3.13
```

Verify that `uv` can see it:

```sh
uv python list
```

Using `uv` for Python is convenient but not an architectural requirement. An
already installed compatible Python can also be used.

## 3. Install Ollama and the default model

The default Home AI Cluster runtime composition uses Ollama with `llama3.2`.

Install Ollama using its supported procedure for your operating system:

- <https://ollama.com/download>

Ensure Ollama is running, then make the default model available locally:

```sh
ollama pull llama3.2
```

You can confirm that Ollama sees the model with:

```sh
ollama list
```

Home AI Cluster does not manage Ollama or model downloads. If Ollama is stopped
later, start it using Ollama's normal operating-system procedure before using
Home AI Cluster.

## 4. Install Home AI Cluster

Install the current published package as an isolated `uv` tool:

```sh
uv tool install home-ai-cluster
```

`uv tool install` is the recommended first-use path because it keeps the HAC CLI
in an isolated Python environment without requiring you to manage that virtual
environment directly.

If you prefer `pip`, install HAC inside an explicitly managed virtual environment
rather than into the system Python. For example:

```sh
python3.13 -m venv ~/.venvs/home-ai-cluster
source ~/.venvs/home-ai-cluster/bin/activate
python -m pip install home-ai-cluster
```

This guide uses the `uv tool` path for the remaining steps.

Verify the installed command:

```sh
hac --help
```

`hac` is the short ordinary command. `home-ai-cluster` is the equivalent long
root command.

To update a previously installed published package later, use the appropriate
`uv tool` upgrade operation rather than installing a repository checkout over
it.

## 5. Start Home AI Cluster

Start the ordinary local process:

```sh
hac local
```

Keep this terminal open. The process runs in the foreground.

With the default host and port, Home AI Cluster is now available only on the
local machine at:

```text
http://127.0.0.1:8000/
```

This same process serves both the native local API and the fixed loopback browser
interface.

## 6. Try the browser

Open this address in a browser on the same machine:

```text
http://127.0.0.1:8000/
```

The current browser provides four ordinary views:

- Chat;
- Summarize;
- Classify;
- Code.

The browser is intentionally local and small. It is not a dashboard, LAN
control surface, runtime manager, or persistent server-side conversation store.

For a first test, open **Chat**, enter a short message, and submit it.

## 7. Try the command line

Leave `hac local` running and open a second terminal.

### Chat

Send one request:

```sh
hac chat "Explain local-first AI in one sentence."
```

Or start an interactive terminal conversation:

```sh
hac chat
```

Use Ctrl-D or Ctrl-C to end the interactive session. Its successful conversation
context exists only in that foreground client process and is not persisted.

### Summarize

Summarize explicit text:

```sh
hac summarize --text "Home AI Cluster routes requests by capability rather than by machine or runtime brand."
```

Or summarize a UTF-8 text file:

```sh
hac summarize --file README.md
```

### Classify

Classify text against an explicit ordered label set:

```sh
hac classify \
  --text "The invoice is due tomorrow." \
  --label invoice \
  --label personal
```

### Code

Ask for bounded textual code assistance:

```sh
hac code "Write a Python function that returns the larger of two integers."
```

`hac code` returns text only. It does not execute generated code or grant shell,
Git, repository, testing, or general filesystem authority.

## 8. Stop Home AI Cluster

Return to the terminal running:

```sh
hac local
```

and stop it with normal process interruption, usually Ctrl-C.

Ollama remains operator-owned. Leave it running or stop it separately according
to your own local setup.

## 9. Optional: use external information

Ordinary Home AI Cluster requests do not acquire Web information by themselves.
External-information acquisition is an explicit optional caller edge using one
separately installed compatible plugin.

One available plugin is
[`home-ai-cluster-plugin-searxng`](https://github.com/frian/home-ai-cluster-plugin-searxng).
It expects an operator-managed local SearXNG service and uses the explicit plugin
name `searxng`.

If you want the plugin from the initial HAC installation, use this instead of the
plain command in step 4:

```sh
uv tool install \
  --with home-ai-cluster-plugin-searxng \
  home-ai-cluster
```

If you already followed step 4 and installed HAC without the plugin, rebuild that
isolated tool environment explicitly with the plugin included:

```sh
uv tool install --force \
  --with home-ai-cluster-plugin-searxng \
  home-ai-cluster
```

With SearXNG and `hac local` already running, an example request is:

```sh
hac external-information \
  --plugin searxng \
  --query "local AI inference developments" \
  --question "What are the main recent developments?"
```

See the
[plugin README](https://github.com/frian/home-ai-cluster-plugin-searxng#readme)
for SearXNG-specific setup and the
[`hac external-information` command reference](command-reference.md#hac-external-information)
for the exact HAC boundary.

## 10. Where to go next

If this local first run works, the useful next documents are:

- [Command reference](command-reference.md) — exact syntax, options, and
  boundaries for every ordinary command.
- [Canonical operator workflow](operator-workflow.md) — preflight, health,
  startup, shutdown, recovery, and explicit static multi-node operation.
- [Configuration examples](../examples/README.md) — runtime-composition and
  static-cluster declaration examples.
- [Project README](../README.md) — current project scope and deliberate
  boundaries.

A second machine is optional. Local-only operation remains the shortest and
least complex ordinary Home AI Cluster path.
