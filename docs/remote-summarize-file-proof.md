# Remote Summarize File Proof

Status: Complete

Date: 2026-07-28

## Scope

This is a standalone post-roadmap native summarize remote integration proof. It composes accepted existing behavior:

- bounded regular-file input;
- ordinary installed `hac summarize`;
- caller-local native summarize endpoint;
- ordinary static-cluster routing;
- controlled local runtime unavailability;
- one real declared remote receiver;
- receiver-local summarize execution; and
- caller-owned declared-node attribution.

It is not Phase 19 and introduces no new architecture or capability.

## Environment

The proof used two physical machines on one trusted LAN, with matching project revision, one ordinary caller static-cluster process, one ordinary receiver local process, supported operator-owned runtimes, exactly one declared remote, and one temporary regular UTF-8 source file.

No machine hostname, username, address, checkout path, file path, declaration path, runtime URL, model path, firewall rule, or hardware detail is retained.

## Procedure

1. Both machines were synchronized to the same revision.
2. Receiver runtime availability was confirmed.
3. The receiver ordinary `hac local` process was started on the trusted LAN.
4. The caller declaration contained exactly one remote node.
5. Caller preflight was coherent.
6. The caller ordinary `hac static-cluster` process was started.
7. The caller-local external runtime was stopped while the caller process remained running.
8. One temporary bounded regular UTF-8 file was created locally on the caller.
9. Exactly one command was invoked:

   ```sh
   hac summarize --file <TEMP_SOURCE_PATH> --verbose
   ```

10. The result was observed transiently.
11. Cleanup completed.

No real path, source text, generated summary, address, or log is retained.

## Sanitized observations

```text
Caller revision matched receiver revision: yes
Preflight coherent: yes
Caller runtime unavailable before request: yes
Caller native request observed once: yes
Receiver internal request observed once: yes
Declared remote attribution observed: yes
Declared remote node ID: remote-summarize-proof
Primary invocation count: exactly one
Command completed successfully: yes
Cleanup completed: yes
```

## File ownership conclusion

The file path was interpreted only by the caller-side CLI, and bytes were read only on the caller. Strict UTF-8 decoding occurred before client construction; only decoded text entered `SummarizeRequest`. The file path was not part of the caller-native request or the remote internal request. The receiver did not access the caller filesystem, and no path was returned in the result or retained history.

This conclusion follows the accepted implementation and focused tests together with the live proof. It does not claim packet-level inspection.

## Evidence limitation

The live proof directly established one physical two-machine execution, one ordinary CLI invocation, one caller native summarize observation, one receiver internal request observation, successful remote execution, caller-declared remote attribution, controlled caller-runtime unavailability, and successful cleanup.

It did not independently expose a correlated request ID, the precise internal exception class, durable local- or remote-attempt counters, or universal absence of retry.

Existing focused automated tests remain authoritative for local-first ordering, accepted pre-request connection failure classification, no retry, one declared remote attempt in the tested topology, the tagged summarize internal envelope, receiver-local execution, caller-owned `node_id` replacement, and file-path absence from serialized requests:

- `tests/test_summarize_command.py`
- `tests/test_ordered_remote_fallback.py`
- `tests/test_static_cluster.py`
- `tests/test_routes.py`

These tests are referenced as existing evidence and were not rerun for this retained proof.

## Result

One ordinary `hac summarize --file` invocation read one bounded local regular UTF-8 file on the caller machine, reached the caller-local native summarize endpoint, followed the accepted controlled local-first fallback path to one real declared remote receiver, executed summarize through the receiver’s local runtime, and returned a normalized result attributed to `remote-summarize-proof`.

Only decoded text crossed the Home AI Cluster request boundaries; the local path remained caller-owned. Exactly one primary CLI invocation occurred, no retry telemetry was added, and no code or contract change was required.

## Cleanup

Cleanup completed. The temporary source file and declaration were removed; the receiver and caller processes were stopped; the caller runtime was restored; receiver and caller ports were freed; no firewall change remained; no proof process remained; and both working trees were clean.

No raw logs, source text, generated summary, or private infrastructure data were retained.

## Non-claims

This proof does not establish authentication, encryption, internet-safe exposure, production readiness, discovery, scheduling, load balancing, retries, supervision, automatic lifecycle, runtime or model selection, arbitrary document support, file upload, remote path access, multiple-file summarization, streaming, or Phase 19 completion.
