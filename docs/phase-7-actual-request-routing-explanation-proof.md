# Phase 7 Actual Request Routing Explanation Proof

Status: Complete

Date: 2026-07-16

## Purpose

This document records the explicit local live-runtime proof required by RFC-0032.

It verifies that `home-ai-cluster-explain-request` executes one actual automatically routed request and returns one request-scoped JSON account containing both routing explanation metadata and the successful normalized cluster result.

## Environment

- execution mode: explicit local operator command;
- runtime adapter: Ollama;
- runtime model observed: `llama3.2`;
- selected node id: `local`;
- ordinary FastAPI application behavior: unchanged;
- OpenAI-compatible process behavior: unchanged.

## Automated verification

The repository checks completed successfully on the implementation branch:

- `uv run ruff check .`;
- `uv run pytest`.

The initial Ruff import-order finding in `tests/test_actual_request_explanation.py` was fixed with Ruff's standard import organizer before the successful final check.

## Live command proof

One explicit invocation of `home-ai-cluster-explain-request` completed successfully against the local Ollama runtime.

Observed routing fields:

- `requested_capability` was `chat`;
- `matched_candidate_families` contained only `local`;
- `selectable_candidate_families` contained only `local`;
- `excluded_candidate_families` was empty;
- `selected_candidate_family` was `local`;
- `selected_node_id` was `local`;
- `outcome_rule` was `local-only`;
- `failure_reason` was `null`.

Observed result attribution:

- `node_id` was `local`;
- `adapter` was `ollama`;
- `model` was `llama3.2`;
- `content` was present in direct command output.

The command returned one JSON object and completed successfully in approximately 14.5 seconds on the proof machine.

## Architectural observations

The proof demonstrates that:

1. one actual request entered the existing cluster-owned request model;
2. local candidate discovery and automatic selection produced the routing explanation;
3. the selected local candidate executed successfully;
4. the explanation and result referred to the same selected node;
5. final node attribution remained cluster-owned;
6. adapter and runtime-model attribution came from the existing normalized result path;
7. no request identifier, retained history, database, metrics, tracing, or event system was required;
8. no change to `/v1/chat` or `/v1/chat/completions` was required.

## Privacy record

The prompt and generated response are deliberately not retained in this proof document.

The document records only non-sensitive proof observations required to validate the architecture. The command displayed response content directly to the operator, but Home AI Cluster did not persist it as logging, history, or repository evidence.

## Result

RFC-0032's first local live-runtime implementation proof is complete.
