# Explicit Ollama Thinking Disable Proof

Status: Successful

Date: 2026-08-17

## Purpose

This record retains one privacy-safe real-local observation that the accepted
RFC-0073 process-local Ollama thinking-disable choice reached a real bounded
Aider workflow and restored practically bounded completion in the observed
local environment.

## Proof basis

- The proof occurred after the accepted RFC-0073 implementation was merged
  through PR #453. The exact local revision used for the live observation is
  not retained here.
- One external local Ollama service was already running with one already-
  installed thinking-capable model. No model was downloaded or pulled.
- HAC ordinary local startup explicitly selected Ollama and used
  `--ollama-disable-thinking`.
- Aider used the already accepted bounded caller edge.

## Observed result

Before explicit thinking disable, the same bounded Aider correction workload
exceeded a 300-second caller wait and later exceeded a 600-second caller wait.

With explicit thinking disable, the same bounded Aider correction invocation
completed successfully in approximately 97 seconds and Aider applied a real
file edit. Two subsequent narrower bounded Aider correction invocations also
completed successfully, in approximately 76 seconds and 63 seconds. The final
edited Bash file passed non-executing `bash -n` syntax validation. Generated
script content was not executed for this proof.

One small native `code` smoke request also completed successfully in
approximately 21 seconds. It is secondary to the bounded Aider observation.

## Interpretation boundary

An explicitly thinking-disabled Ollama adapter completed the observed bounded
Aider workflow within approximately one to two minutes in this local
environment, whereas earlier default-thinking runs of the same correction
workload exceeded finite 300-second and 600-second caller waits.

This materially supports RFC-0073's practical motivation while preserving its
explicit operator-choice semantics. It is not a benchmark, universal performance
claim, guaranteed latency bound, model-quality claim, or Aider edit-quality
guarantee. It does not establish that thinking was the sole cause of every
earlier timeout, that all Ollama models behave alike, or that thinking should
always be disabled.

## Architecture boundary

The operator-selected choice remained process-local and adapter-owned. This
proof did not change or broaden `ClusterRequest`, capabilities, routing, remote
declarations, static-cluster TOML, Aider's accepted ownership, browser or
compatibility behavior, llama-server behavior, timeout semantics, cancellation,
runtime lifecycle or supervision, model discovery or download, result schemas,
or thinking-trace exposure or persistence.

## Privacy boundary

This record excludes prompts, generated script content, source and target
contents, filesystem paths, user or machine identity, hostnames, addresses,
model identifiers, raw Aider or HTTP/Ollama data, thinking traces, credentials,
and environment inventory. Temporary diagnostic captures are not retained.

## Scope preserved

This is retained implementation evidence only. It does not modify RFC-0073 or
authorize new reasoning controls, reasoning levels or budgets, a generic
cross-runtime abstraction, a configuration file, or cancellation or lifecycle
work.
