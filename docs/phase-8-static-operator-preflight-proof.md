# Phase 8 Static Operator Preflight Proof

Status: Pending verification

Date: 2026-07-16

## Purpose

This document records the verification boundary for the implementation of
accepted RFC-0036.

The implementation adds one explicit command:

```text
home-ai-cluster-preflight
```

The command inspects only the ordinary static local node and runtime-adapter
registries.

## Required verification

The implementation is complete only after repository verification confirms:

- the ordinary local registries produce `status: coherent` and exit zero;
- an injected node declaring a missing adapter produces `status: incoherent`,
  one `missing-adapter` issue, and a non-zero exit;
- node, capability, declared-adapter, registered-adapter, and issue ordering
  follows registry declaration order;
- adapter `health()`, `capabilities()`, and `chat()` methods are never called;
- coherent and incoherent reports emit exactly one compact JSON object on stdout
  and nothing on stderr;
- report construction failure emits no JSON and only the stable safe stderr
  message;
- report output excludes node display names, configured health details, runtime
  URLs, authorization values, prompts, responses, filesystem paths, raw
  exceptions, and private machine details;
- the existing health command and ordinary application behavior remain
  unchanged.

## Verification commands

Run from the repository root:

```text
uv run ruff check .
uv run pytest
```

## Runtime boundary

No live-runtime proof is required or appropriate for this contract.

A successful preflight must not contact Ollama, llama-server, a remote machine,
or any other runtime.

## Evidence retention

No prompt, response, runtime URL, authorization value, machine address, private
filesystem path, raw exception, or exact local command output should be retained
in this repository proof.

## Completion record

Update this section only after the verification commands complete successfully.

The final record should state the test count and confirm one explicit invocation
of `home-ai-cluster-preflight` against the ordinary local static registries.
