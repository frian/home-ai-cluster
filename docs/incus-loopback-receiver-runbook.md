# Incus Loopback Receiver Dogfooding Runbook

Status: Validated operator procedure

Validated: 2026-10-12

## Purpose and boundaries

This local development setup runs the HAC caller on one physical Linux host and
an explicitly declared remote HAC node in a Debian Incus container on that same
host. It exercises real remote-node routing, receiver, and transport boundaries
inside HAC. It does not validate a physically distributed LAN. Incus, Ollama,
and both HAC process lifecycles remain operator-owned; there is no automatic
discovery or container orchestration.

This is a record of one tested environment, not a product default or an
architectural authority. Follow the [canonical operator workflow](operator-workflow.md)
and [accepted RFCs](../RFC/README.md) for the contracts. The host's tested
local bindings were Code on `qwen2.5-coder:7b` and Chat/Summarize on
`qwen3.5:9b`, with HAC execution limit `2`. The container ran HAC `1.1.0` and
Ollama with `llama3.2:1b`. Its declared node ID was `debian-1` with `chat` and
`summarize` eligibility. These names and models identify this fixture only.

The receiver is unauthenticated plain HTTP. Keep the Incus network trusted and
operator-controlled; do not expose the receiver or proxy to the public internet.
The proxy listening on host loopback does not prove that the container receiver
is unreachable from other local Incus peers.

## Prerequisites

- Functional Incus, an existing Debian container named `hac-debian-1`, and an
  existing Incus proxy device named `hac-api`.
- Ollama installed and running inside Debian, with `llama3.2:1b` already
  available; compatible HAC installed there.
- A host HAC repository checkout on `post-1.1-development` with its locked
  development environment ready, and its intended retained configuration.
- Ports `25042` and `25043` available in their respective listener contexts,
  and a trusted local Incus network.

Normal startup does not recreate the container, proxy, model, or installation.
Use separate host and container terminals; commands below name their context.

## 1. Start and inspect the container (host shell)

```sh
incus start hac-debian-1
incus list hac-debian-1
incus config device show hac-debian-1
incus config show hac-debian-1 --expanded
```

Read the container's current IPv4 address from `incus list` and inspect the
existing `hac-api` proxy settings. Substitute that concrete address for
`<CONTAINER_IPV4>` in subsequent commands. Incus may assign a different address
after a restart or network change; inspect it each time. Do not use the host's
Wi-Fi address as this local-only proxy's listen address.

## 2. Enter Debian (host shell), then inspect dependencies (container shell)

```sh
incus exec hac-debian-1 -- bash
ss -ltnp
ps aux
ollama list
hac --version
```

After `incus exec`, these commands run **inside the container**, not on the
host. Confirm Ollama and the model are available and that no conflicting HAC
listener is running. If `command -v hac` finds nothing but
`~/.local/bin/hac --version` works, use this temporary shell correction:

```sh
export PATH="$HOME/.local/bin:$PATH"
hac --version
```

This PATH change is needed only for that installation layout. Do not change
shell startup files or upgrade HAC automatically. If installed HAC and caller
versions are incompatible, stop and resolve compatibility explicitly.

## 3. Start the receiver (container shell)

```sh
hac local \
  --runtime ollama \
  --ollama-model llama3.2:1b \
  --receiver-host <CONTAINER_IPV4>
```

Replace the placeholder with the current concrete Incus IPv4 address. Keep
this foreground process running. HAC exposes two distinct listeners: its
native listener on `127.0.0.1:25042` **inside Debian**, and its restricted
receiver listener on `<CONTAINER_IPV4>:25042`. Do not bind the receiver to
`0.0.0.0`.

## 4. Check or update the existing proxy (host shell)

The tested `hac-api` device has this arrangement:

```yaml
hac-api:
  type: proxy
  bind: host
  listen: tcp:127.0.0.1:25043
  connect: tcp:<CONTAINER_IPV4>:25042
```

If `connect` still points to an old container address, update the **existing**
device using the current concrete IPv4:

```sh
incus config device set hac-debian-1 hac-api \
  listen=tcp:127.0.0.1:25043 \
  connect=tcp:<CONTAINER_IPV4>:25042
```

`listen` belongs to the physical host; `connect` targets the container's HAC
receiver. Host loopback stays stable across Wi-Fi changes, while the container
IPv4 may change. The proxy neither starts nor supervises HAC. Keep its listen
address on host loopback, not all host interfaces.

## 5. Verify receiver connectivity (host shell)

```sh
ss -ltn | grep ':25043'
curl -i --max-time 5 \
  http://127.0.0.1:25043/internal/cluster/status
```

The validated response was `HTTP/1.1 200 OK` with
`{"runtime_status":"available"}`. This establishes receiver/status
connectivity at the time of the check, not completion of a business request.
The receiver has a deliberately restricted internal route surface; `GET /` is
not its primary validation endpoint.

## 6. Inspect retained caller configuration (host repository shell)

```sh
uv run --locked hac config show
```

Inspect the existing local bindings, execution limit, and `debian-1` declaration
before changing anything. The tested caller had Code on `qwen2.5-coder:7b`,
Chat/Summarize on `qwen3.5:9b`, HAC execution limit `2`, and remote `debian-1`
with `chat` and `summarize`. Its remote URL was
`http://127.0.0.1:25043`.

If that URL is stale **and those are still the intended capabilities**, replace
the complete retained node declaration:

```sh
uv run --locked hac config node debian-1 \
  --base-url http://127.0.0.1:25043 \
  --capability chat \
  --capability summarize
uv run --locked hac config show
```

The `config node` command replaces the **complete** retained declaration for
`debian-1`. Preserve the actual intended capability set; do not blindly
overwrite an independently customized declaration. Retained changes do not
reconfigure a static-cluster process that is already running; restart it after
changes.

## 7. Start the caller (host repository shell)

```sh
uv run --locked hac static-cluster
```

Keep this foreground process running in a separate host terminal. Avoid a
second caller on the same port. In another host shell, check its native
listener:

```sh
ss -ltnp | grep ':25042'
```

## 8. Run basic diagnostics (host repository shell)

```sh
uv run --locked hac explain-active-routing --capability chat
uv run --locked hac explain-active-routing --capability chat -j
uv run --locked hac explain-active-request chat \
  "Reply with exactly: HAC OK"
```

Active routing explanation is non-executing. Active request explanation submits
one real inference request and reports its validated actual-request account.
Human-readable output is the default after RFC-0153; `-j` or `--json` requests
compact JSON. A remote may be eligible while local remains selected. Local-first
routing does not guarantee remote execution.

The validated basic request attributed execution to node `local`, adapter
`ollama`, model `qwen3.5:9b`. Generated text may differ between runs.

### Optional continuation observation

In a separate dogfooding observation, two overlapping local Chat requests
occupied local HAC execution permission. A third explained Chat request
selected local initially, recorded `execution-permission-denied` there,
continued after `local-execution-permission-denied`, and recorded
`transport-invoked` for declared remote `debian-1`. It succeeded there using
Ollama / `llama3.2:1b`. This demonstrates accepted continuation semantics, not
load balancing or distributed scheduling. It is not a normal startup step; no
load generator is provided. The two long-running client requests timed out,
and their server-side completion status was not established. Their timeouts
are not evidence of success.

## Troubleshooting

| Symptom | Check and correction |
| --- | --- |
| `incus start` fails with `bind: cannot assign requested address` | The observed proxy listened on an old Wi-Fi address. Inspect `incus config device show hac-debian-1`, then reset its host listen address while the container is stopped as shown below. |
| `curl` reports `Recv failure: Connection reset by peer` | The proxy may listen while HAC is stopped or its `connect` address is stale. Run `incus exec hac-debian-1 -- ss -ltnp`, inspect `incus config device show hac-debian-1`, and confirm receiver startup and the current container IPv4. |
| `command -v hac` returns nothing inside Debian | Check `~/.local/bin/hac --version`; if present, run `export PATH="$HOME/.local/bin:$PATH"` in that shell. |
| Receiver responds but caller uses an old URL | Run `uv run --locked hac config show` on the host. Correct the retained node declaration while preserving its capabilities, then restart the caller. |
| `error: request explanation timed out` | The CLI received no completed validated account. The server may have received or begun work. Do not infer completion, cancellation, or safe retry; repeating the command submits another business request. |

For that Incus startup failure, run this on the **host while the container is
stopped**; the container IPv4 is not needed yet:

```sh
incus config device set hac-debian-1 hac-api \
  listen=tcp:127.0.0.1:25043
incus start hac-debian-1
```

After startup, inspect the current container IPv4 with `incus list hac-debian-1`.
Then check the existing proxy and update its `connect` address if necessary,
following [step 4](#4-check-or-update-the-existing-proxy-host-shell).

## Stop the environment

Stop in reverse startup order:

1. Press Ctrl+C in the host's foreground `static-cluster` terminal.
2. Press Ctrl+C in Debian's foreground `hac local` terminal.
3. Leave the Debian shell if appropriate.
4. On the host, run `incus stop hac-debian-1`.
5. On the host, run `incus list hac-debian-1` to verify it stopped. Optionally
   check that the relevant listeners are gone.

Container shutdown handles its own process lifecycle. Stop Ollama separately
only if that is the operator's intention.

## Quick reference

Host: `incus start hac-debian-1` (use the stopped-container recovery above if
needed) → `incus list hac-debian-1` (record current IPv4) →
`incus config device show hac-debian-1` (check `hac-api`; update `connect` using
step 4 if the container IPv4 changed).

Debian: `incus exec hac-debian-1 -- bash` → check `ollama list` and
`hac --version` → start `hac local --runtime ollama --ollama-model
llama3.2:1b --receiver-host <CONTAINER_IPV4>` in the foreground.

Host: check `ss -ltn | grep ':25043'` and
`curl -i --max-time 5 http://127.0.0.1:25043/internal/cluster/status` →
`uv run --locked hac config show` → start `uv run --locked hac static-cluster`
in the foreground → run `explain-active-routing` and
`explain-active-request` as above.

Stop: Ctrl+C caller → Ctrl+C receiver → leave Debian →
`incus stop hac-debian-1` → `incus list hac-debian-1`.
