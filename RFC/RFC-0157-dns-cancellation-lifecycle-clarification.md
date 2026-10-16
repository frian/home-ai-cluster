# RFC-0157: DNS Cancellation Lifecycle Clarification for Document Enrichment

Status: Draft

Date: 2026-10-16

Author: frian

## Summary

This Draft proposes a narrow clarification to RFC-0156's document-enrichment
lifecycle boundary.  An authorized retrieval may use
`asyncio.get_running_loop().getaddrinfo()` to resolve an eligible hostname
before connecting.  On common asyncio implementations, the system resolver
work may run through an executor.  Cancelling the HAC coroutine awaiting that
work does not necessarily physically interrupt an already-running system DNS
resolution.

The proposed clarification distinguishes that residual system resolver work
from HAC-owned document retrieval.  After cancellation, global expiry, client
disconnect, or loss of the current turn's authorization, HAC must terminate
its own retrieval progression and must not consume a late DNS result.  The
only qualification is that an already-running ordinary system DNS resolution
may finish when the operating system or runtime cannot interrupt it.  That
qualification neither authorizes background document retrieval nor weakens any
application-level termination guarantee.

This is a documentation-only Draft.  It proposes no implementation, test,
dependency, configuration, Search-plugin, Chat, or public-contract change.

## Existing authority

RFC-0156 is the accepted authority for bounded caller-local document
enrichment.  Its **Retrieval, preparation, and evidence boundaries** require a
candidate to resolve before connecting, reject non-public answers, preserve
the invariant that a validated hostname cannot connect to a non-public
destination, and retain normal CA and hostname certificate verification.  It
also requires event-loop responsiveness and states that cancellation of an
asyncio task alone does not establish that an underlying blocking network
operation has ended.

Its **Partial failure, global termination, and privacy** section requires that
global expiry, caller cancellation, client disconnect, or loss of the
specific turn's authorization prevent subsequent HAC-owned stages, including
new retrieval attempts, evidence construction, routing, and Source-Grounded
Chat.  It further prohibits late Source-Grounded Chat and background
continuation after the foreground operation ends.  Its **Required
implementation proofs** require local evidence that cancellation or expiry
prevents late Source-Grounded Chat and that enrichment remains responsive.

RFC-0078 keeps acquisition caller-owned, finite, explicit, and outside
ordinary server startup and request handling.  It gives neither a generic URL
retrieval authority nor a background acquisition lifecycle.  RFC-0082 defines
the corresponding ordinary-request rule: HAC cancels its owned pending work,
stops awaiting its result, discards later results, and truthfully limits its
promise to HAC-owned cancellation rather than physical termination of every
underlying operation.  RFC-0085 preserves the separate HAC-owned HTTP
transport boundary; it does not alter resolver behavior or create an ambient
network exception.

This Draft proposes to clarify RFC-0156 only.  RFC-0156 remains authoritative
until this proposal is accepted.

## Problem

DNS awaiting and physical DNS termination are distinct.  The awaiting HAC
coroutine can receive cancellation and cease its retrieval path while an
executor-backed system resolver invocation already submitted by the ordinary
asyncio resolver continues until the operating system or runtime completes it.

That residual execution is not a late HAC retrieval result and does not show
that HAC started a connection, processed a document, built evidence, or began
Chat.  Treating it as permission for background continuation would contradict
RFC-0156.  Conversely, requiring proof that every such system DNS operation is
physically terminated would impose a guarantee unavailable through the stated
ordinary resolver mechanism and would make the accepted lifecycle requirement
untruthful.

## Proposed decision

For an RFC-0156 document-retrieval operation, after cancellation, global
expiry, client disconnect, or loss of the current turn's authorization:

1. The HAC-owned document-retrieval coroutine must stop progressing through
   its operation.
2. The cancelled retrieval must not initiate a new TCP or TLS connection.
3. No additional document-retrieval attempt may start.
4. HAC must not accept or process a late HTML result, select a late passage,
   construct late `SourceEvidence`, route, or start Source-Grounded Chat.
5. No detached HAC application task may continue document retrieval after the
   foreground operation terminates.
6. HAC-owned network transports must retain bounded shutdown behavior and
   report cleanup limitations truthfully.
7. HAC must not consume a cancelled DNS result to resume the terminated
   operation.

The term *bounded shutdown behavior* retains RFC-0082's meaning: bounded HAC
ownership and authority, not a promise that every library, operating-system
resource, or external operation is released immediately or within a specified
duration.

### Strictly limited system DNS qualification

An already-running system DNS resolution initiated through the ordinary
asyncio resolver mechanism may finish after cancellation of its awaiting HAC
coroutine when the operating system or runtime provides no mechanism to
interrupt that resolution.

This residual system work is permitted only as an underlying runtime
limitation.  It must not trigger a subsequent HAC action, initiate a
connection, resume document processing, produce a late result accepted by
HAC, or carry application callbacks that continue retrieval.  It is not proof
of physical termination and does not guarantee immediate release of
operating-system resources.

The qualification applies only to already-running system DNS resolution.  It
does not exempt blocking HTTP reads, TLS operations, HAC-owned transports,
application workers, detached HAC tasks, or any other asynchronous operation
from their existing RFC-0156 and RFC-0082 obligations.

## Security and privacy invariants

The clarification grants no new destination or disclosure authority.  The
existing explicit caller-owned authorization, public HTTPS restriction,
public-address DNS validation, destination pinning, TLS and hostname
verification, sequential up-to-five policy, per-document and overall
deadlines, memory and response bounds, no-retry rule, and no-provider-fallback
rule remain unchanged.

A residual resolver invocation cannot authorize a connection or disclose an
HTTP request, question, HTML, evidence, or Chat content.  It does not create a
new retrieval attempt, persistence, logging, worker, service, or background
HAC operation.  Default privacy boundaries and the prohibition on prompt or
response logging remain unchanged.

## Alternatives considered

### Retain the existing ambiguity

Rejected.  It leaves unclear whether an uninterruptible system resolver is a
violation of RFC-0156 despite the absence of a subsequent HAC action.

### Require physical termination of every DNS operation

Rejected.  Ordinary `asyncio.getaddrinfo()` does not supply that guarantee on
common implementations.  Requiring it would imply a resolver, supervisor, or
other infrastructure decision outside RFC-0156 and would not be a truthful
application-level lifecycle contract.

### Distinguish HAC-owned continuation from residual system resolver execution

Proposed.  This preserves the strict application-level stop rule while
describing the platform limitation precisely and without authorizing broader
background activity.

## Non-goals

This Draft does not authorize a custom DNS resolver, subprocess supervisor,
worker pool, queue, background retrieval service, generic network framework,
new caller authority, Search or Chat change, implementation change, test
change, dependency change, configuration change, or production activation.

It does not amend RFC-0156 directly, authorize generic URL retrieval, change
the Search-plugin contract, or establish a physical DNS-termination promise.

## Required evidence

Before a future implementation relying on this clarification is considered
ready, focused local tests must demonstrate:

- cancellation of the awaiting HAC coroutine;
- no subsequent TCP/TLS connection and no additional retrieval attempt;
- no subsequent HAC document processing, passage selection, evidence
  construction, routing, or Source-Grounded Chat;
- bounded HAC-owned transport shutdown behavior with truthful reporting of
  cleanup limitations; and
- that a late resolver completion, where simulated, is not consumed to resume
  the terminated operation.

The tests need not and must not claim to prove immediate physical termination
of an already-running system resolver operation invoked through
`asyncio.getaddrinfo()`.  They must instead distinguish that unprovable
platform property from the application-level behavior HAC owns and can prove.

## Compatibility

The proposal preserves RFC-0156's caller-local, authorized, sequential,
bounded document-enrichment architecture.  It introduces no new transport,
runtime adapter, routing behavior, request or response format, configuration,
or retained state.  It makes the existing no-late-Chat and no-background HAC
continuation requirements testable without claiming control over an
uninterruptible underlying system resolver.

## Decision status

Draft.  This proposed clarification is not accepted authority.  W002-004
remains open, and RFC-0156 continues to govern until maintainers explicitly
accept this RFC.
