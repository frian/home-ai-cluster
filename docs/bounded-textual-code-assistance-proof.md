# Bounded Textual Code Assistance Proof

Status: Retained

Date: 2026-08-11

## Scope

This record retains privacy-safe local and physical two-machine evidence for
accepted RFC-0067 bounded textual code assistance.

## Automated baseline

Merged automated coverage establishes the relevant implementation boundaries:

- bounded ordered-message normalization for `code`;
- explicit static capability eligibility;
- reuse of the legacy ordered-message remote transport;
- preservation of RFC-0034 diagnostic request construction;
- reuse of existing Chat-like adapter execution; and
- absence of new code execution authority.

This is a summary of coverage boundaries, not a retention of implementation
details, prompts, responses, runtime observations, or private test material.

## Local positive observation

The repository owner started one ordinary local process against an existing
operator-owned local runtime and invoked the native `code` client with one
explicit code request. The request succeeded with free-form textual assistance.
Verbose output attributed execution to the local cluster node and configured
adapter, using the existing Chat-like execution path.

Home AI Cluster did not execute the returned text. The observation establishes
only bounded textual assistance through the explicit native capability; it does
not establish filesystem, repository, shell, Git, testing, tool, function,
agent, or execution authority.

## Local no-eligible-capability observation

The caller-local declaration was `chat`-only and its declared remote was also
`chat`-only. The remote address was intentionally nonoperational. An explicit
`code` request initially exposed a failure-boundary defect: routing correctly
found no selectable candidate, but the ordered-message handler surfaced HTTP
500. PR #431 corrected that handler translation without changing routing
design.

After the correction, the same local exercise returned HTTP 404 and the native
client reported the safe code-specific no-capability failure, without a
traceback. The ineligible remote did not need to be reachable. Focused automated
coverage also proves that remote transport is not invoked when no declared
candidate is eligible.

## Bounded conclusion

The retained local observations support these two bounded outcomes:

```text
explicit code request
    -> eligible local `code` capability handling
    -> textual result with attribution
```

```text
code request
    + no code-capable declaration
    -> no selectable candidate
    -> safe no-capability failure
    -> no ineligible remote request
```

## Retained physical two-machine RFC-0067 code proof

The repository owner manually completed this proof on two separate physical
machines at repository revision `9ec386a9e65e7c96c21382440ebc63e6091c5992`.
Both machines used that revision. One machine ran the ordinary caller-side
static-cluster process; the separate receiver machine ran an ordinary receiver
process with its own operator-owned local runtime. The processes communicated
over a real local network, not loopback.

The caller-local routing declaration contained only `chat`. The declared remote
logical node `code-remote` contained `chat` and `code`. Static preflight was
coherent, and static status observed the remote application as reachable and
its runtime as available. The caller-local runtime was also healthy and
available; it was excluded from this request because it did not declare `code`,
not because of runtime failure.

One explicit native `code` request sent to the already-running caller process
therefore selected the eligible declared remote directly. The request crossed
the real LAN to the separate receiver and returned a non-empty textual
code-assistance result. Verbose attribution identified `code-remote`.

This was direct capability-centered selection, not fallback:

```text
request requires code
caller-local node chat only -> ineligible
declared remote code-remote chat + code -> eligible -> selected -> real LAN
    -> non-empty textual result attributed to code-remote
```

No fallback trigger, direct node selector, retry, discovery, scheduling, or
runtime/model choice appeared in the request. Home AI Cluster returned text
only. It did not execute the generated code or gain filesystem, repository,
shell, Git, testing, tool, agent, or execution authority.

## Privacy exclusions

This record retains no real prompts, pasted code, generated code, private LAN
addresses, physical hostnames, usernames, filesystem paths, process IDs, model
or runtime identifiers, credentials, or other machine-specific private details.

## Conclusion

The local positive and negative observations support the accepted explicit,
bounded, text-only `code` capability and its safe no-candidate boundary. The
retained physical observation closes the required RFC-0067 two-machine proof:
an ineligible healthy caller-local node was excluded, and an eligible declared
physical remote returned textual assistance through ordinary real-LAN static
routing. This evidence does not claim production readiness or introduce an
architectural conclusion beyond accepted RFC-0067.
