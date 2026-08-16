# Explicit Ollama Model Selection Proof

Status: Successful

Date: 2026-08-16

## Purpose

This record retains one real-local proof of accepted and implemented RFC-0071:
an ordinary HAC process can use an explicitly selected, already-installed
Ollama model for one native bounded textual `code` request.

## Proof basis

- HAC revision tested: `bfd11ca5a4057be6a1f8b984a39785d522565a69`.
- Ollama was already running as an external local service.
- `qwen2.5-coder:1.5b` was already installed before the proof; HAC did not
  download or pull it.
- HAC started as one loopback-only ordinary local process with:

  ```text
  --runtime ollama --ollama-model qwen2.5-coder:1.5b
  ```

## Observed result

One native `POST /v1/chat` request with `capability=code` completed with HTTP
200. The request carried no `model`, `preferred_model`, or `runtime_model`
field. The successful HAC result reported:

- `node_id=local`;
- `adapter=ollama`;
- `model=qwen2.5-coder:1.5b`; and
- non-empty textual content.

Generated content was not retained or executed.

## Architecture boundary

The observation shows that the operator-selected startup value reached the
process-local Ollama adapter and that the adapter's existing execution path
reported its configured model. The native request remained model-free and
capability-centered. This proof does not show model discovery, capability-to-
model inference, routing by model, or objective model quality.

## Privacy boundary

This record excludes the prompt, generated content, raw HTTP data, raw Ollama
output, model inventory, machine or user identity, filesystem paths, private
addresses, credentials, and environment data.

## Scope preserved

HAC did not pull, automatically discover for routing, proactively load, unload,
or otherwise manage the selected model or the external Ollama service. No
browser, compatibility, Aider, request-schema, routing, declaration, status,
or lifecycle behavior was added or changed for this proof.
