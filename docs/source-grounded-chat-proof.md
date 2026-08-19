# Source-Grounded Chat Proof

Status: Retained

Date: 2026-08-19

## Purpose

This record retains privacy-safe evidence from two real operator-run local
observations made after accepted RFC-0077 bounded source-grounded Chat was
implemented. It records only the bounded behavior observed through the
ordinary local HAC application and `POST /v1/chat/sources`.

## Proof boundary

Both observations used manually supplied bounded source evidence and an
already-installed local model through the ordinary local Chat adapter path.
No acquisition integration, external provider, Web/search/browse/retrieve
capability, URL fetcher, browser, crawler, plugin, or new capability was
involved. HAC did not obtain the sources or act on their provenance URLs.

This is implementation evidence for the accepted contract. It does not change
the RFC, architecture, routing, runtime-adapter boundary, or authority model.

## Factual-grounding observation

One source-grounded request contained two manually supplied bounded public
technical-release evidence snippets. The operator asked the model to answer
only from that evidence.

The request completed through the existing local Chat adapter path. The
generated response correctly identified the main requested release/version
fact, the principal feature described by the newer evidence, and one
improvement described by the older evidence. It also included one plausible
explanatory inference that the supplied evidence did not explicitly state.

The successful structured result returned generated content separately from the
supplied sources, retained supplied source order and values, and included the
accepted node, adapter, and model execution attribution shape.

This is useful factual grounding evidence, but it also demonstrates the
RFC-0077 limitation: supplied-source provenance is not claim-level factual
correctness. A plausible unsupported inference was observed even though the
main requested facts were handled correctly.

## Instruction-like hostile-source observation

A second source-grounded request contained one manually supplied factual source
and one manually supplied synthetic source with explicit instruction-like
content attempting to override the operator request. The operator asked one
simple factual question whose answer was present in the factual source.

The request completed successfully. In this observation, the model answered
from the factual evidence and did not follow the instruction-like source
content. Both supplied sources remained present in the structured result in
their original order.

The hostile source gained no HAC routing, capability, network, filesystem,
tool, configuration, or execution authority. That structural containment is
an architectural property of the RFC-0077 contract. It does not establish
general prompt-injection resistance: language-model susceptibility to
malicious source text remains model-dependent, and this single favorable
observation is not a guarantee or benchmark.

## Supplied-source provenance observation

For both successful requests, the result preserved the normalized sources that
had been supplied to the model execution, separately from generated content
and in original order. This provenance means only that those bounded source
values were supplied to that execution.

It does not say that every source was used, that a source is true, current,
complete, safe, or authoritative, or that any particular generated claim is
supported by a particular source. Provenance remains distinct from citations
and claim-level correctness.

## Bounded findings

This retained proof supports only that, in the observed ordinary local
executions:

- the implemented `POST /v1/chat/sources` vertical slice worked end to end;
- source-grounded requests executed through ordinary `capability=chat`;
- the existing Chat adapter path consumed the deterministic RFC-0077
  projection;
- generated content was returned separately from cluster-owned supplied-source
  provenance;
- supplied source values and order were retained in successful results;
- a small local model execution made meaningful use of bounded evidence; and
- one instruction-like evidence item did not override the operator request in
  one observation.

## What this proof does not establish

This proof does not establish factual correctness of all generated claims,
verified citations, source truth, authority, freshness, completeness, or
general prompt-injection resistance. It does not establish safety of arbitrary
external content or model-independent behavior.

It also does not establish or authorize acquisition architecture, Tavily or
SearXNG selection, plugin architecture, a Web/search/browse/retrieve
capability, autonomous retrieval, URL fetching, or a remote-node proof.

## Privacy exclusions

This retained record omits exact operator questions, source contents, source
URLs, full generated responses, exact model and runtime identifiers, private
topology, machine identity, usernames, paths, raw logs, credentials, and
acquisition data. It retains only structural outcomes needed to record the
observations.

## Conclusion

The observed ordinary local executions provide bounded evidence that the
implemented RFC-0077 source-grounded Chat contract works end to end with
manually supplied evidence. They support useful factual grounding and
separate supplied-source provenance while preserving the distinction between
provenance and claim-level correctness. The favorable hostile-source result is
limited to that observation and does not generalize to arbitrary malicious
source text.
