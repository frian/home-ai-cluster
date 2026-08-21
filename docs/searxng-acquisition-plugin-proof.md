# RFC-0079 SearXNG Acquisition Plugin Proof

Status: Retained result

Date: 2026-08-20

## Purpose

This record retains the privacy-safe structural observations from one completed
real execution of the [RFC-0079 SearXNG acquisition plugin live-proof
runbook](searxng-acquisition-plugin-proof-runbook.md). It is a result, not a
procedure or a new architectural decision.

## Observed real path

The complete real RFC-0079/RFC-0078/RFC-0077/ordinary Chat path completed
successfully:

```text
separately installed real searxng plugin
  -> operator-owned fixed-loopback SearXNG
  -> RFC-0078 acquisition and RFC-0077 validation
  -> POST /v1/chat/sources
  -> ordinary Chat routing and real runtime-adapter execution
  -> valid SourceGroundedChatResult
```

The separately installed entry point was discoverable in
`home_ai_cluster.external_information_acquisition.v1`. Explicit `searxng`
selection loaded the real asynchronous callable. The operator-owned SearXNG
prerequisite at the RFC-0079 fixed loopback endpoint returned a structurally
usable JSON result.

The real acquisition produced bounded candidates that passed RFC-0078
reconstruction and complete RFC-0077 validation. The existing real
`POST /v1/chat/sources` request completed, followed by ordinary Chat routing,
real runtime-adapter execution, and structurally valid
`SourceGroundedChatResult` validation. No fake provider, result,
source-grounded endpoint, router, or runtime adapter was used.

## Bounded interpretation

This establishes the intended installed-plugin integration path for the
observed real operation. It does not establish general provider reliability,
search-result correctness, or model-answer correctness.

SearXNG remained operator-owned: HAC and the plugin did not own its lifecycle.
The provider destination remained the fixed loopback endpoint; plugin selection
was explicit; candidates remained bounded; result URLs remained provenance only
and were not fetched; and routing remained ordinary Chat routing.

## Privacy exclusions

This record intentionally excludes the proof query and question, raw command
output, raw JSON, generated model text, provider URLs, source titles/snippets,
raw SearXNG responses, engine metadata, credentials, provider configuration,
usernames, paths, machine details, private topology, and runtime/model/node
identifiers.
