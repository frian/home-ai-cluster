# RFC-0078 Installed-Plugin Boundary Proof

Status: Retained

Date: 2026-08-19

## Purpose and scope

This record retains one privacy-safe observation of the implemented RFC-0078
installed-plugin caller boundary. It used a temporary, separately installed
local Python distribution with one `proof` entry point in the accepted
`home_ai_cluster.external_information_acquisition.v1` group. The distribution
was proof scaffolding only: it was not HAC source, a bundled plugin, provider,
published package, dependency, or committed artifact.

The proof plugin had no provider implementation, credentials, configuration,
or network behavior. It accepted only the fixed harmless proof query and
returned one deterministic built-in title/URL/content dictionary in one
built-in list. Its provenance URL used the reserved `example.invalid` domain;
HAC was not authorized to and did not fetch it.

## Actual observations

The temporary distribution installed successfully into the same virtual
environment used by the checkout's installed `hac` command. Real
`importlib.metadata.entry_points()` discovery exposed exactly one entry named
`proof` in the RFC-0078 group. The metadata observation did not import the
plugin.

With a fixed non-sensitive lifecycle marker enabled, the installed `hac --help`
surface left the marker absent. This establishes that ordinary root help did not
import the installed plugin merely because it existed. It does not establish a
separate observation of ordinary HAC server startup.

The installed root command was then invoked once with the fixed selected name,
fixed query, fixed question, and `--json`. The plugin marker changed to
`invoked`. Since the temporary async callable rejects every other query, that
observation establishes that the exact fixed query reached the selected loaded
callable through real installed entry-point metadata. Its deterministic
three-field built-in return did not produce an acquisition-boundary failure.

The caller then reported the existing safe native failure
`error: ordinary cluster unavailable`. No ordinary HAC server was listening at
the fixed loopback caller endpoint during this observation. This shows the
caller progressed beyond installed-plugin acquisition and local RFC-0077
reconstruction/validation to its native HTTP-client failure ownership. It does
not show a receiver's HTTP request record, a successful `/v1/chat/sources`
response, routing, adapter execution, generated content, or returned
`SourceGroundedChatResult` provenance.

## Cleanup observation

The temporary distribution was uninstalled after the command observation. A
second real metadata inspection of the same entry-point group returned no
entries, and the temporary source and marker directory were deleted. The
repository diff contains no proof-plugin source, package metadata, wheel,
installation artifact, dependency, or lockfile.

## Bounded findings

This observation proves only that:

- a separate installed temporary distribution can expose the exact accepted
  RFC-0078 group/name through real Python metadata;
- metadata discovery and ordinary installed root help did not import that
  plugin;
- one explicit `hac external-information --plugin proof` operation selected and
  loaded that one installed plugin;
- the fixed query reached its asynchronous callable and produced its
  deterministic successful return;
- its closed built-in title/URL/content representation passed the caller's
  acquisition and RFC-0077 validation boundary; and
- uninstalling the proof distribution restored the observed zero-entry-point
  state.

No provider acquisition, plugin fallback, automatic selection, retry, URL
fetch, new capability, server-side plugin activity, or production plugin was
observed or added.

## Remaining live-proof gap

No suitable running ordinary HAC server/local runtime was available. Therefore
this record deliberately does not claim a successful end-to-end source-grounded
request, endpoint receipt, `SourceGroundedChatResult` validation, returned
provenance, ordinary routing, remote transport, or runtime-adapter execution.
Those portions require a future live observation with an already-running
ordinary HAC server; they must not be simulated by a fake server or synthetic
successful result.

## Privacy exclusions

This record excludes machine names, usernames, home paths, non-loopback IP
addresses, credentials, provider configuration, real prompts, generated model
content, runtime/model identifiers, source content, raw logs, and temporary
filesystem locations. It retains only fixed harmless proof labels and the
structural observations required by the accepted boundary.
