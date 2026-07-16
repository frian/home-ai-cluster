# Phase 7 Structured Actual Request Failures Proof

Status: Completed

Date: 2026-07-16

## Purpose

This document records the explicit local proof required by accepted RFC-0034.

The proof used the ordinary local command:

```text
home-ai-cluster-explain-request
```

No remote node, distributed proof wiring, retry, reselection, fallback, history, or retained state was involved.

## Successful local proof

One explicit local request completed successfully through the ordinary local Ollama adapter.

The observed structured account confirmed:

- top-level status `succeeded`;
- one local matched and selectable candidate family;
- selected candidate family `local`;
- selected node id `local`;
- outcome rule `local-only`;
- no routing failure reason;
- successful result attribution to node `local`;
- successful result attribution to adapter `ollama`;
- a normalized model value was present;
- failure was `null`;
- process exit status was zero.

Prompt content, generated response content, exact runtime details, and machine-specific information are intentionally not retained here.

## Structured local failure proof

One explicit local request used an unsupported capability so that automatic selection produced no selectable candidate without requiring runtime shutdown or artificial network failure.

The observed structured account confirmed:

- top-level status `failed`;
- no matched candidate family;
- no selectable candidate family;
- no selected candidate family;
- no selected node id;
- outcome rule `no-selectable-candidate`;
- routing failure reason `no-matching-candidate`;
- result was `null`;
- failure status `no-selectable-candidate`;
- failure reason `no selectable routing candidate`;
- process exit status was non-zero.

The failed account was emitted as JSON on standard output without exposing exception, transport, authorization, runtime URL, payload, or private machine details.

## Conclusion

The implementation proves that one explicit local command can return a truthful request-scoped account for both successful and failed actual requests while preserving shell failure semantics, privacy boundaries, and same-selection routing explanation.
