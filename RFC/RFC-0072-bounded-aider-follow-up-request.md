# RFC-0072: Bounded Aider Follow-Up Request

Status: Draft

Date: 2026-08-17

Author: frian

## Summary

Home AI Cluster should narrowly amend RFC-0068's Aider caller-edge lifecycle.
One fixed invocation of:

```text
hac aider --file PATH --message TEXT
home-ai-cluster aider --file PATH --message TEXT
```

would still launch exactly one supported Aider 0.86.2 subprocess and one
private loopback translator. It would require one qualifying Aider-shaped
request and permit at most one additional qualifying Aider-shaped request from
that same subprocess. Each accepted request would map to exactly one native
`POST /v1/chat` request with explicit `capability=code`; the hard maximum is
therefore two native HAC requests per invocation.

The optional second request is entirely Aider-owned. HAC does not synthesize
it, retry, inspect response or target content, or classify it as a reflection.
The bridge mechanically enforces its count and lifecycle. A first native
failure fails the invocation and cannot open the second-request allowance.

## Problem

RFC-0068 deliberately limited one fixed Aider invocation to one qualifying
request and one native `code` request. RFC-0069 then narrowly allowed the
explicit missing target to be created empty, while retaining Aider's exclusive
authority to read and edit target content.

The later whole-file reliability investigation found that a usable first
whole-file response is not guaranteed for the bounded small-script workflow.
An operator then manually evaluated another already-installed, explicitly
selected local model through RFC-0071. A trivial existing-file edit succeeded,
but a realistic new small-script request against an explicit empty target did
not yield a usable first whole-file edit. Aider attempted its ordinary
corrective continuation, which the RFC-0068 translator correctly rejected as a
second qualifying request. A stronger operator instruction requesting a
complete final file had the same bounded result. No generated code was
executed, model downloaded, or runtime lifecycle action taken.

This evidence is not a judgement about a particular model. It establishes that
one bounded Aider-owned corrective follow-up may be needed even in the narrow
workflow, and that changing the one-request boundary requires an explicit
architectural decision.

## Goals

- Permit one optional Aider-owned follow-up only after a successful first
  translated interaction.
- Keep exactly one invocation, one fixed Aider 0.86.2 subprocess, and one
  private ephemeral translator.
- Cap qualifying Aider requests and native `capability=code` requests at two.
- Preserve strict Aider-shaped ingress and ordinary capability-centered HAC
  routing for every accepted request.
- Keep response/edit interpretation with Aider and target-content authority
  outside HAC core.
- Preserve privacy and all existing caller-edge execution guardrails.

## Non-goals

This RFC does not authorize a new CLI option, a second Aider subprocess,
interactive Aider, multiple targets, a persistent bridge, reusable listener,
session, background service, configurable reflection or retry count, general
developer-tool support, an Aider upgrade, or an edit-format change.

It does not authorize HAC to retry, generate a corrective prompt, synthesize a
follow-up, inspect model response or target bytes, detect malformed whole-file
syntax, classify a request as a reflection, parse/apply edits or patches, or
change invocation success semantics. It does not authorize model, runtime,
node, or route selection; node/model affinity; filesystem/repository access
beyond RFC-0069; Git; shell, lint, test, browser, URL, tool/function, agent,
or generated-code execution; compatibility expansion; persistence; logging; or
a database.

RFC-0067's text-only `code` contract, RFC-0069 target authority, RFC-0071
model-selection boundary, and RFC-0031 Chat-only compatibility remain
unchanged.

## Proposal

### Same command and subprocess

The operator surface remains exactly:

```text
hac aider --file PATH --message TEXT
home-ai-cluster aider --file PATH --message TEXT
```

No option is added. One invocation launches exactly one already-installed,
supported Aider 0.86.2 subprocess. It must not launch, restart, or chain a
second Aider subprocess.

### Bounded, Aider-owned request lifecycle

One invocation requires at least one qualifying Aider-shaped request and may
accept at most two sequential qualifying requests. Each accepted request maps
to exactly one ordinary native request:

```text
POST /v1/chat
capability=code
```

The maximum native HAC request count is exactly two. No third qualifying Aider
request may produce a third native request. It must fail closed using the
existing small generic caller-edge failure style; this RFC creates no public
error taxonomy.

The second request is optional and Aider-owned. HAC neither automatically
retries nor creates another prompt or request. It does not inspect the first
model response, evaluate whole-file syntax, compare target bytes, or compare
the two message lists. In particular, enforcement must not depend on a
particular Aider error string, message wording, or a semantic determination
that a request is a "reflection." The bridge simply permits one additional
independently qualifying request during the fixed child-process lifetime.

```text
validate prerequisites
  -> create private temporary integration configuration
  -> start one private loopback translator
  -> launch one fixed Aider 0.86.2 subprocess
  -> accept request #1
  -> native capability=code request #1
  -> project response #1
  -> either Aider exits
       or accept request #2
          -> native capability=code request #2
          -> project response #2
  -> request #3 fails closed
  -> Aider exits
  -> close translator
  -> clean temporary material

native request #1 failure
  -> invocation failure
  -> no native request #2
```

A second qualifying request is allowed only once the first accepted request has
produced a successful native HAC result and the translator has returned the
corresponding successful Aider-shaped response. If native request #1 times
out, is unavailable, returns non-success, has malformed success, or otherwise
fails at the existing caller edge, the invocation fails without a second native
request. The optional follow-up is not a HAC retry.

If Aider sends qualifying request #2, normal existing native timeout,
validation, routing, and result behavior applies. A second native failure
permits no third request. There is no loop, Aider-default reflection allowance,
or configurable retry count.

After projecting successful response #1, the translator may remain alive only
for the lifetime of that same fixed Aider subprocess so one optional follow-up
can arrive. If Aider exits after request #1, the translator closes normally.
It remains non-persistent, non-reusable, non-interactive, private, and not
externally discoverable.

### Unchanged ingress and translation contract

Both requests independently satisfy RFC-0068's accepted strict ingress
contract: exact private `POST /v1/chat/completions`; fixed endpoint model;
optional `stream=false`; non-empty ordered plain `system`, `user`, and
`assistant` messages; no tools/functions; no unknown generation fields; no
multimodal content; no model discovery; and loopback-only access. Invalid
requests fail closed. Permitting a second request does not relax the protocol
shape.

For each accepted request, the translator preserves the ordered Aider messages
and constructs the existing `ClusterRequest` with `capability=code`. It adds no
project-owned corrective instruction. Prior assistant output, target context,
or corrective instructions contained in a second Aider request remain
Aider-owned messages and are preserved under the existing rules.

RFC-0067's aggregate 65,536-byte textual input validation remains
authoritative independently for each native request. This RFC adds neither a
combined two-request budget nor a separate Aider limit, and does not enlarge
the existing limit. A rejected second request under that validation fails
normally and cannot lead to a third request.

### Unchanged routing and model boundaries

Each native request is an independent ordinary `capability=code` request.
Existing routing, local-first selection, declared-remote order, availability,
and fallback behavior apply independently. This RFC adds no node, adapter,
runtime, or model affinity; sticky/session routing; same-node guarantee;
first-request reuse; model selection; or model inference. The two requests may
therefore route to different eligible nodes under existing behavior.

RFC-0071 remains unchanged. The caller edge gains no `--model`,
`--ollama-model`, runtime selector, capability-to-model mapping, or node
selection. Model choice remains process-local and adapter-owned by the
already-running HAC process/node. The supported Aider version remains exactly
0.86.2 and the edit representation remains `whole`.

### Unchanged authority, privacy, timeout, and success boundaries

RFC-0069 remains authoritative: the caller edge may create only the explicitly
named missing target as an empty file under its existing conditions. Aider owns
target reading and editing; HAC core remains text-only. This RFC adds no target
inspection, rollback, diff parsing/application, directory creation, repository
inspection, or other file-edit authority. A failed invocation may leave the
explicit target empty or Aider-modified, as RFC-0069 already permits.

The fixed Aider guardrails remain unchanged: no Git or auto-commit, lint/test
automation, shell execution, generated-code execution, URL/browser tooling,
repository map, tools/functions, agents, or persistence. The extra request
does not authorize prompt, target-content, generated-content, raw HAC response,
private-path, or credential persistence/logging. Temporary integration material
remains private and is removed as before.

RFC-0060's existing finite native timeout applies independently to each native
request. This RFC creates neither an Aider-process deadline nor a cancellation
contract. The invocation is structurally bounded by at most two native
requests, not by semantic response interpretation. A successful Aider exit
after one request without changing the target is not redefined; this RFC does
not solve unchanged-target reporting.

## Rationale

Exactly one Aider-owned follow-up is the smallest evidence-driven expansion of
the established caller edge. It allows Aider to carry out its own normal
corrective interaction only after HAC has successfully supplied a first textual
result, while preserving hard limits that are visible, testable, and
independent of Aider's internal wording or defaults.

Count- and lifecycle-based enforcement preserves the authority boundary. HAC
continues to route text and project a minimal response; Aider continues to
interpret that response and decide whether another interaction is needed. It
avoids coupling the project to Aider parser internals or creating a project
agent that judges edits and constructs repairs.

## Alternatives considered

### Keep exactly one request

Rejected. It remains simpler, but real-local evidence shows that Aider's normal
corrective continuation can be needed for the bounded small-script workflow.

### Permit Aider's full default reflection loop

Rejected. It would turn the caller edge into a wider multi-request loop whose
bound depends on Aider internals.

### Permit exactly one additional Aider-owned follow-up

Selected. It is the smallest evidence-driven expansion and preserves a hard
project-owned bound.

### Semantically recognize malformed-edit reflections

Rejected. Message-shape or parser-based recognition would couple HAC to
Aider's internal wording and semantics.

### HAC-generated retry or correction

Rejected. HAC must not own edit-protocol reasoning, retry, or corrective
prompt creation.

### Configurable reflection/retry count

Rejected. There is no demonstrated need to add operator-configurable lifecycle
complexity.

### Change edit format or upgrade Aider

Rejected for this RFC. Each is a separate version or representation decision.

### Inspect target bytes and retry when unchanged

Rejected. It would expand caller-edge filesystem authority and success
semantics, which are outside this decision.

## Trade-offs

An invocation may now make twice as many native/model requests as RFC-0068,
increasing possible latency, local compute, and conversational context. The
private translator may live slightly longer and implementation must maintain a
small finite state machine.

Those costs are bounded by one Aider subprocess, at most two accepted/native
requests, no loop, no configuration knob, no persistence, no new execution or
filesystem authority, and no model or routing coupling.

## Relationship to previous RFCs

RFC-0067 remains unchanged. RFC-0068 is narrowly amended only for its
one-request/native-request limit and corresponding translator termination and
follow-up lifecycle. RFC-0069 and RFC-0071 remain unchanged. RFC-0031 remains
Chat-only. Every other RFC-0068 boundary remains authoritative.

After acceptance, where RFC-0072 conflicts with RFC-0068 only on at most one
qualifying Aider request, at most one native request, translator termination
after the first response, or no Aider-owned follow-up, RFC-0072 governs. It
does not supersede RFC-0068 wholesale.

## Impact and proof expectations

After acceptance, a separate implementation/proof may change only the
caller-edge lifecycle needed for this amendment. It must leave the CLI, model,
runtime, node, routing, compatibility, browser, filesystem, execution,
privacy, and persistence boundaries described above unchanged.

Later focused tests must establish:

1. Existing one-request success sends exactly one native `capability=code`
   request.
2. One valid second request after successful projected response #1 produces
   exactly one second native `capability=code` request.
3. Ordered messages are preserved independently for both requests.
4. HAC never generates the second request.
5. A third qualifying request fails and never produces a third native request.
6. Native request #1 failure does not permit native request #2.
7. Native request #2 failure does not permit native request #3.
8. Strict ingress validation remains unchanged for both requests.
9. Existing Aider version/edit format, target authority, and no-Git,
   no-test/lint, no-shell, no-browser/tool, and no-persistence guardrails stay
   unchanged.
10. No CLI/model/runtime/node/routing/compatibility/browser changes occur.
11. Ordinary static-cluster operation stays topology-blind: each request routes
    normally by `code` with no affinity.

A later real-local privacy-safe proof may show a bounded invocation in which
Aider uses its second request and completes an edit. It must not retain prompt
text, generated source, private paths, machine identity, credentials, raw HTTP,
or raw model output, and it must not execute generated code.

## Open questions

None within this narrow contract. Edit-format changes, Aider-version changes,
and target-byte/success observation require separate decisions.

## Decision

Pending.
