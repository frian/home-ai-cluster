# Bounded Textual Code Assistance Proof

Status: Partial

Date: 2026-08-11

## Scope

This record retains privacy-safe local evidence for accepted RFC-0067 bounded
textual code assistance. It is not a complete proof and does not make a claim
about physical two-machine code execution.

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

## Physical two-machine RFC-0067 code proof: PENDING

A real physical two-machine proof remains required. It must show, with
privacy-safe retained evidence:

```text
request requires code
caller-local node chat only -> ineligible
real declared remote node chat + code -> eligible -> selected -> real network
    -> textual result attributed to remote
```

The proof must use a real second machine and real network path. A same-machine
loopback substitution is not sufficient.

## Privacy exclusions

This record retains no real prompts, pasted code, generated code, private
addresses, model or runtime identifiers, machine names, credentials, or private
filesystem paths.

## Conclusion

The local positive and negative observations support the accepted explicit,
bounded, text-only `code` capability and its safe no-candidate boundary. They
do not close the required physical two-machine RFC-0067 proof.
