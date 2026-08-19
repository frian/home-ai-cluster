# RFC-0078 Installed-Plugin Boundary Proof Runbook

Status: Retained procedure

## Purpose

This runbook records a repeatable, privacy-safe procedure for observing the
implemented RFC-0078 installed-plugin boundary with a temporary, separately
installed Python distribution. It is proof scaffolding only: it is not HAC
source, a bundled plugin, a provider, a published package, or a dependency.

The procedure proves real Python distribution metadata and the caller-edge
acquisition boundary. It must not claim a successful source-grounded Chat result
unless an already-running ordinary HAC server and suitable local runtime are
actually available.

## Fixed proof values

Use only these harmless fixed values:

```text
entry-point group: home_ai_cluster.external_information_acquisition.v1
entry-point name:  proof
query:             RFC-0078 installed-plugin proof query
question:          What does the fixed proof evidence contain?
source URL:        https://example.invalid/source
```

The proof plugin must reject every query except the fixed query. Its successful
return is exactly one concrete built-in `list` containing one concrete built-in
`dict` with only `title`, `url`, and `content`. Its values are deterministic and
harmless. It performs no network operation and has no provider configuration or
credential.

## Temporary distribution

Create a temporary directory outside the checkout. Create one minimal Python
distribution there with exactly this entry point in its own `pyproject.toml`:

```toml
[project.entry-points."home_ai_cluster.external_information_acquisition.v1"]
proof = "rfc0078_proof_plugin:acquire"
```

Its `acquire` value is an `async def` callable accepting only `query: str`.
For a bounded lifecycle observation, it may write a fixed marker such as
`imported` at module import and replace it with `invoked` only after accepting
the fixed query. The marker must not retain the query, question, source data,
credential, endpoint, hostname, username, or machine path.

Install the temporary distribution into the same Python environment that runs
the checkout's installed `hac` root command. For example, with the existing
repository virtual environment:

```sh
uv pip install --python .venv/bin/python <TEMPORARY_DISTRIBUTION_DIRECTORY>
```

This is an operator-local proof installation only. Do not add it to HAC's
`pyproject.toml`, lockfile, source tree, tests, or released artifacts.

## Metadata and zero-plugin observations

Before loading the entry point, inspect real metadata with
`importlib.metadata.entry_points()` and select only the fixed group. Confirm one
entry named `proof` is visible. Metadata inspection must leave the optional
module-import marker absent.

Run `hac --help` with the marker enabled and confirm the marker remains absent.
This proves the installed root help surface does not import the plugin merely
because it is installed. It is not a substitute for observing a real ordinary
HAC server startup; record that distinction in the proof result.

## Explicit caller-edge observation

Run the installed root command, not a monkeypatched test helper:

```sh
hac external-information \
  --plugin proof \
  --query "RFC-0078 installed-plugin proof query" \
  --question "What does the fixed proof evidence contain?" \
  --json
```

Confirm the marker becomes `invoked`. This shows the exact fixed query crossed
the real selected installed-entry-point boundary; the plugin must otherwise
fail. The command may then either:

- complete against an already-running ordinary HAC server, in which case retain
  only a privacy-safe structural `SourceGroundedChatResult` observation; or
- report the existing ordinary cluster/network failure, in which case retain no
  successful endpoint, routing, adapter, generated-content, or result-provenance
  claim.

Do not start a fake HTTP server or fabricate a successful source-grounded
result to fill a missing live-runtime observation.

## Cleanup and retained record

Uninstall the temporary distribution from the proof environment, re-inspect the
same entry-point group and confirm no proof entry remains, then delete the
temporary source and marker directory:

```sh
uv pip uninstall --python .venv/bin/python hac-rfc0078-proof-plugin
```

The retained result must state exactly which observations occurred, distinguish
them from the procedure, omit private values and raw logs, and state any
unavailable live-server gap. No temporary distribution source or installation
artifact belongs in the Git diff.
