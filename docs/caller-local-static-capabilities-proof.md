# Caller-local Static Capabilities Proof

Status: Complete

## Claim

An ordinary static-cluster caller can declare its fixed caller-local routing
candidate as `chat`-only while declaring an ordinary remote as
`summarize`-only. A healthy eligible local chat request remains local-first;
a summarize request excludes the healthy but ineligible local candidate and
reaches the eligible remote without local failure or fallback.

## Accepted boundaries

This proof exercises accepted RFC-0059 caller-local routing capabilities,
accepted RFC-0058 caller-owned remote declarations, existing capability
eligibility, local-first selection, native chat and summarize commands, and the
existing no-capability failure. It adds no selector, probing, scheduler,
preference, routing, fallback, status, receiver, or adapter behavior.

## Topology

The proof used one machine with two separate ordinary processes:

```text
caller static-cluster process
  local candidate: chat
  declared remote: summarize
  -> receiver hac local process
```

Both processes used the same available, operator-owned local runtime. The
caller and receiver remained separate processes and summarize crossed the real
HTTP boundary. The receiver used unchanged ordinary `hac local` composition.

## Declaration

The caller loaded a retained-shape TOML declaration equivalent to:

```toml
local_capabilities = ["chat"]

remote_node_id = "summary-remote"
remote_base_url = "http://<SUMMARY_RECEIVER>:<PORT>"
remote_capabilities = ["summarize"]
```

The local field is caller-local routing permission. The remote capability is
caller-owned declaration data; neither claims receiver capability discovery or
verification.

## Preconditions

- The caller-local runtime and receiver runtime were available before requests.
- The caller preflight projection declared local `chat` only and
  `summary-remote` `summarize` only.
- The receiver was an unchanged ordinary `hac local` process.
- No local failure condition, direct node selector, runtime probe, scheduler, or
  preference was introduced.

## Preflight observation

Ordinary declaration-aware preflight was coherent and network-free. It
projected the existing order:

```text
local: chat
summary-remote: summarize
```

This is static declaration projection, not runtime availability verification or
adapter implementation discovery.

## Healthy local chat observation

One ordinary verbose chat request through the caller succeeded with:

```text
Node: local
Adapter: ollama
```

The caller runtime was healthy. Local-first applied because local declared the
requested `chat` capability; the remote summarize-only declaration was not
eligible or selected. No direct selector was used.

## Remote summarize eligibility observation

One ordinary `hac summarize --file <SYNTHETIC_INPUT> --verbose` request through
the same caller succeeded with:

```text
Node: summary-remote
Adapter: ollama
```

The caller-local runtime remained healthy after this request. Its node declared
only `chat`, so it was excluded before selection for `summarize`; no local
summarize runtime attempt, local failure, or fallback trigger was required. The
request crossed the ordinary caller-to-receiver HTTP process boundary. No direct
selector or scheduler was used.

## No-eligible-capability observation

An otherwise ordinary temporary topology declared both the caller-local node and
the remote as `chat`-only. An ordinary summarize command returned the existing
safe public failure:

```text
error: no available summarize capability
```

This is the existing no-capability result, not local-runtime unavailability,
remote-transport unavailability, or declaration validation failure. The public
command does not expose a more detailed structured selection record, so this is
the smallest retained safe observation.

## Inline equivalence

A transient ordinary inline preflight using `--local-capability chat` and
`--remote-capability summarize` produced the same coherent ordered projection:
local `chat`, then `summary-remote` `summarize`. This agrees with the focused
automated inline/TOML construction and preflight equivalence coverage. The full
process proof was intentionally retained only once.

## What this proves

- Caller-local capability restriction is accepted for ordinary static callers.
- Preflight projects the restricted local set without network use.
- A healthy eligible local candidate remains local-first for chat.
- A healthy but ineligible local candidate is excluded before summarize
  selection.
- Summarize reaches an eligible remote without local failure or fallback.
- The existing no-capability failure remains intact.
- TOML and inline forms represent the same caller-local contract.
- The ordinary `hac local` receiver remains unchanged.

## What this does not prove

This proof does not establish runtime capability discovery or verification,
receiver capability advertisement, caller/receiver agreement, adapter
disablement, endpoint removal, best-node selection, load balancing,
performance, health-aware scheduling, model- or hardware-aware routing,
arbitrary capabilities, remote-only caller mode, generalized distributed
operation, or Phase 19.

## Privacy and sanitization

This record retains only structural outcomes and placeholder identities. It
excludes real hostnames, addresses, ports, paths, usernames, runtime URLs,
credentials, prompts, source contents, generated responses, raw logs, model
inventory, hardware details, environment data, and identifying timestamps.

## Reproduction outline

1. Start one ordinary receiver `hac local` process with an available runtime.
2. Create a private caller declaration with local `chat` and remote
   `summarize` capabilities.
3. Run ordinary declaration-aware preflight, then start `hac static-cluster`.
4. Send one ordinary verbose chat request and one summarize request from a
   small synthetic file through the caller; retain only node attribution.
5. Use a separate chat-only local-and-remote declaration for one ordinary
   summarize no-capability observation.
6. Optionally compare one inline preflight projection, then stop the temporary
   caller and receiver processes and remove private temporary files.

## Conclusion

The retained ordinary process-and-HTTP observation confirms RFC-0059's bounded
caller-local contract: local eligibility can be restricted without changing the
runtime, receiver, routing, or fallback contracts. A healthy local chat
candidate remains local-first, while summarize reaches an eligible remote
because the local candidate is ineligible.
