# Static Cluster Declaration

Status: Operator documentation

Date: 2026-07-17

This document describes the accepted RFC-0039 file-based declaration mode for
ordinary explicit static multi-node operation.

It does not replace the canonical operator workflow in
`docs/operator-workflow.md`. It only replaces repeated reconstruction of the two
remote topology arguments on the calling machine.

## Scope

The declaration describes exactly one remote node for the existing ordinary
local-plus-one-remote topology.

It contains exactly two top-level TOML keys:

```toml
remote_node_id = "remote-node"
remote_base_url = "http://192.0.2.10:25042"
```

The file must not contain sections, nested tables, unknown keys, secrets, or
additional configuration.

Home AI Cluster reads the explicitly selected file once at process startup. It
does not discover, merge, reload, watch, copy, rewrite, log, or expose the file
or its remote URL.

## Prepare a local declaration

Copy the repository example to an operator-owned local path:

```sh
cp examples/static-cluster-single-remote.toml <operator-owned-declaration-path>
```

Edit only the two values:

```toml
remote_node_id = "<remote-node-id>"
remote_base_url = "http://<receiving-lan-address>:25042"
```

Do not commit a real private LAN address, machine name, secret, prompt, or
response to the repository.

For the accepted ordered multi-remote and caller-local eligibility examples,
see [`examples/README.md`](../examples/README.md). This document remains the
single-remote declaration guide.

The declaration path is always supplied explicitly. There is no default path,
search path, environment-variable source, or precedence system.

## Start the calling process

After preparing the receiving machine according to
`docs/operator-workflow.md`, start the ordinary static multi-node process on the
calling machine:

```sh
uv run home-ai-cluster-static-cluster \
  --declaration <operator-owned-declaration-path>
```

The calling endpoint remains:

```text
http://127.0.0.1:25042/v1/chat
```

The host, port, local-first routing, narrow remote fallback, transport,
application lifecycle, and external runtime ownership are unchanged from the
inline RFC-0038 mode.

## Inline mode remains supported

The existing inline form remains valid:

```sh
uv run home-ai-cluster-static-cluster \
  --remote-node-id <remote-node-id> \
  --remote-base-url http://<receiving-lan-address>:25042
```

Use either the declaration mode or the complete inline mode.

Do not combine `--declaration` with either inline option. Do not supply only one
inline option.

## Startup failures

The process exits before application construction and before server startup if
the declaration cannot be loaded or validated.

Failure categories include:

- file not found or unreadable;
- invalid TOML;
- missing or unknown keys;
- non-string values;
- invalid or conflicting remote node ID;
- invalid remote base URL.

CLI errors remain compact and do not expose the declaration contents, the
private remote URL, raw TOML parser details, or raw operating-system errors.

Correct the operator-owned file, then start the process again. Home AI Cluster
does not repair or rewrite the declaration.

## Boundaries

This mode does not add:

- discovery;
- remote process control;
- remote runtime ownership;
- reload or file watching;
- environment-variable topology;
- configuration merging or precedence;
- a general configuration system;
- additional nodes;
- direct node targeting;
- new routing or fallback behavior.

The topology remains one local node plus one explicitly declared remote node.
