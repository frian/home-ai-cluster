# Smallest Supported Aider Code Integration Investigation

Status: Investigation only

Date: 2026-08-13

## Question

What is the smallest supportable caller-side integration that makes the proven
Aider-to-explicit-HAC-`code` composition useful for ordinary small
administration or maintenance scripts, without expanding Home AI Cluster (HAC)
authority or turning it into a general developer agent?

The retained [Aider code bridge proof](aider-code-bridge-proof.md) establishes
one bounded one-machine composition. It does not itself authorize an
integration, implementation, public contract, or architectural decision.

## Fixed baseline

RFC-0067 makes `code` a closed semantic requirement that callers must request
explicitly. Native `POST /v1/chat` carries that requirement and returns a
free-form textual result. Existing routing, including a future eligible
declared remote `code` node, remains cluster-owned; a caller does not select a
node, runtime, or model.

HAC has no filesystem, repository, Git, shell, test, lint, tool/function, or
code-execution authority. Aider independently owns any file read or edit under
its own process and user authority. Its safety flags are operational guardrails,
not a security sandbox.

The accepted RFC-0031 compatibility edge remains Chat-only: its fixed endpoint
identifier is not a capability selector and it constructs `chat`. Prompt or
model-name inference cannot select `code` under RFC-0066. The proven temporary
bridge instead translated one strict loopback Aider-shaped request to the
native request with fixed explicit `capability=code`.

The physical two-machine RFC-0067 `code` proof remains pending and separate.

## Evidence and user value

One real bounded execution showed that Aider can consume one textual result
from an explicit native `code` request and modify one disposable caller-owned
target file. The bridge accepted one request, forwarded `code`, and stopped;
HAC retained no filesystem or execution authority.

This establishes technical feasibility and the smallest concrete no-copy/paste
small-script outcome. It does not establish that an interactive session,
multi-request protocol, retries, a persistent listener, a generic developer
tool surface, or compatibility expansion is needed for that outcome.

The current runbook remains useful evidence, but requires an operator to create
temporary files, manage bridge lifecycle, and reproduce conservative Aider
configuration. That is excessive friction for ordinary repetition of this
narrow task. A supported surface must reduce that friction without absorbing
the file-edit authority that belongs to Aider.

## Candidate comparison

| Candidate | Explicit `code` | User friction | HAC change/support | Aider coupling and public surface | Authority/lifecycle/privacy | One-shot adequacy and RFC |
| --- | --- | --- | --- | --- | --- | --- |
| A. Proof/runbook only | Yes | High manual setup | None; no commitment | None beyond documented proof | Temporary operator owns everything | Proven adequate once; no RFC |
| B. Documented outside helper | Yes | Lower only for operators who maintain it | No project executable; example-level support | Helper still has an implicit private contract | Operator owns lifecycle and privacy | May move copy/paste into a helper; no RFC |
| C. Shipped strict one-shot bridge | Yes, fixed by adapter | Bridge setup remains with operator | New project-owned access adapter | Strict Aider-shaped ingress becomes public | Adapter owns one listener/response and cleanup; no file authority | Technically sufficient, but does not remove all workflow friction; RFC needed |
| D. Shipped one-shot launcher | Yes, fixed by adapter | Lowest for the stated task | New project-owned caller edge | Couples to explicit external Aider invocation and strict subset | Helper owns bridge lifecycle only; Aider owns the file edit | Sufficient for one edit; RFC needed |
| E. Persistent/multi-request bridge | Could remain explicit | Lower for sessions, unproven need | Larger lifetime and support commitment | Broader client/protocol expectations | State, retries, shutdown, recovery, privacy, and drift grow | Not justified; separate RFC if ever needed |
| F. Expand compatibility for `code` | Would require a new mapping | Low client setup | Changes accepted compatibility architecture | Public compatibility semantics and likely broader expectations | Risks treating model-like input as capability selection | Rejected/deferred; RFC required before any consideration |

All candidates A through D preserve engine independence and ordinary capability
routing when they send the accepted native request. Only E and F add broader
protocol or lifecycle pressure. None gives HAC filesystem authority.

## One-shot versus interactive

For the stated goal—create or modify one small script without manual
copy/paste—the successful proof is direct evidence that one submission, one
textual result, and one caller-owned edit are sufficient. The goal does not
require a conversation, iterative repair, automatic retry, or a long-lived
listener.

One-shot support has an important boundary value: it can define one accepted
request, one native request with fixed `code`, one response projection, and
deterministic cleanup. A persistent session would instead need an explicit
request-count and process-lifetime contract, sequential/concurrent behavior,
retry and failure-recovery meaning, shutdown ownership, privacy/logging rules,
and a maintained response to Aider request-shape drift. Current evidence does
not justify those commitments. Interactive and multi-request support should be
deferred, not silently included as implementation convenience.

## Core versus caller edge

This does not belong in HAC core. It does not help core orchestration by adding
a capability, routing rule, or runtime behavior; those already exist. Nor is
it merely outside the project if the project chooses to support the proven
ordinary no-copy/paste composition: the value is that an explicit native
`code` request can retain cluster-owned eligibility and routing rather than
wrapping a local runtime directly.

The smallest credible location is a project-owned optional caller/access edge
for the one proven concrete tool, Aider. It should not cause a plugin framework
or generic developer-tool abstraction. It must remain separate from the
existing Chat-only compatibility edge and the native cluster core.

## Supported-shape assessment

A strict bridge alone (Candidate C) makes a narrow protocol available but
leaves the operator to coordinate a listener, temporary configuration, Aider,
and cleanup. That retains much of the proof-only friction. A one-shot launcher
(Candidate D) is the smallest form that can own only this coordination while
leaving Aider's edit authority intact. It is still caller-side composition:
the helper may invoke an already-installed external Aider process, but it does
not read a repository semantically, parse or apply a patch, execute output, run
tests, run Git, or choose a node, runtime, or model.

External Aider must remain an explicit optional prerequisite, not a HAC
dependency. A supported shape would need a stated tested-version/request-shape
expectation and safe failure when that expectation is not met. It must bind
only loopback, start only the temporary bridge, use the fixed native mapping to
`code`, propagate a small failure without raw prompt or runtime data, clean up
on every outcome, and neither log nor persist prompts or responses by default.

It must not launch the HAC process, make repository meaning part of HAC,
provide a generic OpenAI server, or represent its Aider invocation as HAC file
editing. Aider retains the disposable-target edit under caller authority.

## Outcome

**Outcome C — a supported strict one-shot caller edge is justified.**

The proof establishes a real, bounded no-copy/paste small-script outcome, and
the current manual lifecycle is enough friction to justify a narrow supported
edge. The support commitment is architectural because it would make ownership,
ingress, lifecycle, external-tool coupling, and privacy behavior public and
maintained. An RFC is required before implementation.

The smallest exact RFC question is:

> What optional, loopback-only, one-shot project-owned caller/access adapter
> may coordinate an already-installed Aider invocation with one strict
> Aider-shaped request translated to native `POST /v1/chat` with fixed explicit
> `capability=code`, while preserving textual-only HAC authority, caller-owned
> file edits, privacy-safe cleanup, engine-independent cluster routing, and the
> existing Chat-only compatibility contract?

That RFC must decide the public contract, rather than this investigation:

- ownership of the adapter and whether it invokes Aider;
- strict accepted ingress and response projection;
- one-request-only semantics, loopback binding, lifecycle, cleanup, and
  failure propagation;
- external Aider prerequisite and version/request-shape support boundary;
- no default prompt/response logging or persistence;
- no authority over files, repositories, shell, Git, tests, lint, tools, or
  execution; and
- its distinct relationship to native `/v1/chat` and Chat-only RFC-0031
  compatibility.

## Explicit deferrals

This investigation does not authorize an implementation, executable name or
flags, a persistent or multi-request bridge, retries, a generic developer-tool
protocol, plugin framework, SDK, repository indexing, RAG, tools/function
calling, shell/test/Git automation, auto-commit, model or runtime discovery,
prompt-based capability inference, browser Code UI, dashboard, persistence,
web retrieval, or the physical two-machine proof implementation.

## Conclusion

One-shot is sufficient for the proven small-script goal. A narrowly supported
project-owned caller edge may be worth adding because it can remove proof-only
operational friction while preserving HAC's capability-centered cluster value
and text-only authority. It must first be defined by a separate RFC; it must
not become a persistent Aider service or an expansion of OpenAI compatibility.
