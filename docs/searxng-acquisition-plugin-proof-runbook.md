# RFC-0079 SearXNG Acquisition Plugin Live-Proof Runbook

Status: Retained procedure

## Purpose and scope

This runbook defines a repeatable, privacy-safe procedure for the
post-implementation live proof required by accepted RFC-0079. It is a
procedure, not a proof result. Do not record success until the observations in
this runbook have actually occurred.

The intended path is:

```text
separately installed real searxng plugin
  -> already-running operator-owned loopback SearXNG
  -> RFC-0078 acquisition caller
  -> RFC-0077 reconstruction and validation
  -> POST /v1/chat/sources
  -> ordinary chat routing and runtime execution
```

This procedure does not authorize HAC, its plugin, or a proof runner to install,
start, stop, configure, upgrade, repair, supervise, or health-poll SearXNG. It
does not add a provider dependency, a new server mode, a fake server, a test
router, a fake adapter, or a proof-only endpoint.

## Fixed proof values

Use only these harmless, public values. They are fixed so the proof runner can
recognize the procedure structurally without retaining a private query or
question in a later result record.

```text
entry-point group: home_ai_cluster.external_information_acquisition.v1
entry-point name:  searxng
proof query:       SearXNG search engine
proof question:    According to the supplied sources, what is SearXNG?
```

The result record need not reproduce provider URLs, snippets, raw JSON, or
generated answer text.

## Prerequisites

Before beginning, the proof runner must establish each of these facts. If one
is unavailable, stop the relevant observation and record only the precise
structural gap; do not manufacture a success.

1. Use current HAC `main` and the sibling
   `home-ai-cluster-plugin-searxng` checkout at clean `main`. The plugin source
   is implementation evidence, not HAC source or a dependency.
2. Use an isolated Python environment that runs the tested installed `hac`
   command. Do not add the plugin to HAC `pyproject.toml`, `uv.lock`, source,
   or repository.
3. An operator has independently installed, configured, and already started
   SearXNG with JSON output enabled at exactly:

   ```text
   http://127.0.0.1:8888/search
   ```

   This literal loopback destination is the only permitted provider
   prerequisite. Do not substitute a hostname, another port, LAN/public
   address, TLS endpoint, credential, or environment override.
4. The ordinary documented HAC server and its ordinary local runtime path are
   already available for the eventual real request. Their lifecycle remains
   outside this runbook.

Where practical, first observe ordinary HAC in a separate environment without
the optional plugin. Installation makes an entry point available for explicit
selection only; it must not change ordinary HAC startup or ordinary Chat.

## Build and separately install the real plugin

Build the wheel from the clean sibling plugin `main`, using its ordinary package
workflow. Inspect only non-sensitive artifact facts needed for this proof:

- distribution name: `home-ai-cluster-plugin-searxng`;
- development version actually built;
- Python requirement and `httpx` runtime dependency; and
- exactly one entry point in the fixed group with the name `searxng`.

Install that built wheel, rather than only an editable source checkout, into the
same isolated Python environment used by the tested `hac` command. Keep the
wheel outside the HAC repository. Do not add it as a HAC dependency or copy its
source into HAC.

Before lazy loading, inspect real `importlib.metadata.entry_points()` metadata
and select only the fixed group. Confirm exactly one entry named `searxng` is
visible. Metadata discovery alone must not import the plugin. Then load that
one entry and confirm that it is the real asynchronous callable. Retain only
the structural metadata outcome, not environment paths or raw command output.

## Provider prerequisite observation

Before the HAC acquisition command, verify that the operator-owned SearXNG
prerequisite is reachable and can produce a structurally acceptable JSON search
response. This is a prerequisite check, not a retained provider proof.

Use exactly one direct request, if a direct check is needed:

```text
POST http://127.0.0.1:8888/search
Content-Type: application/x-www-form-urlencoded

q=SearXNG search engine
format=json
```

Do not follow redirects or make a second provider request. Inspect only the
structural facts needed to proceed: HTTP 200, JSON object, `results` list, and
at least one usable title/URL/content candidate. Immediately discard the raw
response; do not retain its URLs, snippets, engine metadata, service
configuration, or command log.

If this prerequisite is unavailable, returns a redirect/non-200 response, has
JSON disabled, fails its finite request, or has no usable candidates, stop the
live-path observation. Record only the applicable non-sensitive unavailable
condition.

## Real HAC end-to-end observation

Use the real installed `hac` command and the existing ordinary documented HAC
server/runtime workflow. Do not monkeypatch HAC, replace SearXNG with a fake
HTTP server, fabricate SearXNG results, fabricate a `/v1/chat/sources`
response, or substitute a fake routing or adapter path.

Run exactly one explicit caller operation:

```sh
hac external-information \
  --plugin searxng \
  --query "SearXNG search engine" \
  --question "According to the supplied sources, what is SearXNG?" \
  --json
```

The proof may claim a successful end-to-end observation only when all of these
were actually observed through the real path:

1. real entry-point discovery and explicit `searxng` selection;
2. real installed plugin lazy load and one provider acquisition;
3. RFC-0078 candidate reconstruction and complete RFC-0077 validation;
4. real `POST /v1/chat/sources` completion;
5. ordinary Chat routing and real runtime-adapter execution; and
6. successful `SourceGroundedChatResult` validation.

Plugin acquisition alone does not establish the later caller, endpoint,
routing, adapter, or result stages. Likewise, successful tests do not establish
a live observation.

## What a later retained proof may claim

After an actual successful run, a separate retained result may state only
structural observations such as:

- real plugin metadata was discoverable and explicit selection loaded it;
- the fixed loopback provider request completed structurally;
- acquisition produced candidates accepted by RFC-0078 and RFC-0077;
- the existing source-grounded endpoint completed;
- ordinary Chat execution completed; and
- a structurally valid `SourceGroundedChatResult` was returned.

The future result belongs in
`docs/searxng-acquisition-plugin-proof.md`. Create it only after an actual
observation. It must distinguish observed success from an unavailable gap and
must not infer an unobserved stage from a prior one.

## Failure observations

Expected non-successful outcomes include missing plugin metadata, unavailable
SearXNG, JSON-disabled/non-200 provider response, provider timeout or format
failure, zero usable candidates, RFC-0077 validation failure, unavailable HAC
server, unavailable ordinary runtime, and ordinary request failure.

For any such outcome, retain only a privacy-safe structural status. Use an
existing normalized HAC failure string only when it was actually observed; do
not predict or invent one. Never retain exception detail, raw command output,
or provider data to explain a failure.

## Cleanup

If the wheel was installed only for this proof, uninstall the separate plugin
distribution from the proof HAC environment. Re-inspect the fixed entry-point
group if useful to confirm that no `searxng` entry remains.

Do not remove or modify the sibling plugin source repository. Do not modify the
operator-owned SearXNG service. Do not leave proof wheels, temporary source
directories, logs, raw responses, copied results, plugin dependency entries, or
lockfile changes in the HAC repository.

## Privacy exclusions

The runbook and any retained result must exclude:

- private queries or questions;
- result/source URLs, snippets, raw SearXNG responses, and generated content;
- credentials, cookies, provider configuration, and engine identities;
- usernames, home paths, machine names, non-loopback addresses, private
  topology, and raw command logs; and
- node, runtime, or model identifiers unless strictly necessary for a
  demonstrably non-sensitive structural fact.

Result URLs remain provenance strings only. Neither the plugin nor HAC may
resolve, connect to, fetch, preview, or otherwise treat them as destinations.
