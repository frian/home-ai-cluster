# Phase 9 Repeatable Static Cluster Declaration Proof

Status: Verified

Date: 2026-07-17

## Purpose

Record operator verification of the file-based ordinary static multi-node declaration mode accepted by RFC-0039.

This record is intentionally privacy-safe. It retains only the repository revision, placeholder node identity, normalized observations, and pass/fail results.

## Verification basis

Repository revision on both machines:

```text
ef915382a52b379b5b89571a002fd338e7d0c2b4
```

The declared remote node identifier retained for this record is:

```text
remote-node
```

No real private address, machine name, model name, prompt, generated response, filesystem path, hardware detail, credential, raw exception, or raw log is retained.

## Verified operator sequence

### Receiving machine

The operator confirmed:

- local preflight passed;
- local health passed;
- the ordinary receiving application started successfully;
- the receiving application was available for the calling machine over the trusted LAN.

Result: **Pass**.

### Calling declaration mode

The calling machine started the ordinary static multi-node process with:

```text
home-ai-cluster-static-cluster --declaration <operator-owned-declaration-path>
```

The operator confirmed:

- the declaration-mode process started successfully;
- the calling endpoint bound only to the existing loopback address and port;
- no inline topology arguments were required;
- the declaration remained operator-owned and explicitly selected.

Result: **Pass**.

### Local-first selection

With the calling machine's external local runtime usable, one request was sent through the calling loopback endpoint.

The operator confirmed:

- the request succeeded;
- returned attribution identified the local node;
- the receiving machine observed no internal request for this local-first request.

This confirms that file-based declaration did not change local-first routing behavior.

Result: **Pass**.

### Accepted remote fallback

The calling machine's externally owned local runtime was stopped normally while the calling Home AI Cluster process remained running.

The operator confirmed:

- local health reported the calling runtime unavailable;
- one request through the calling loopback endpoint succeeded;
- returned attribution identified `remote-node`;
- the receiving machine observed exactly one successful internal request;
- no retry loop was observed.

This confirms that file-based declaration preserved the accepted narrow remote fallback path.

Result: **Pass**.

### Restoration

The calling machine's external local runtime was restored manually.

The operator confirmed:

- local health passed after restoration.

Result: **Pass**.

## Required verification checklist

1. Both machines used the same repository revision: **Pass**.
2. Receiving preflight and health passed: **Pass**.
3. Declaration-mode process started successfully: **Pass**.
4. Calling endpoint retained the accepted loopback-only bind: **Pass**.
5. Usable local execution remained local: **Pass**.
6. The receiving machine observed no request during local-first execution: **Pass**.
7. Local runtime unavailability was observed before fallback: **Pass**.
8. Accepted fallback returned attribution to `remote-node`: **Pass**.
9. The receiving machine observed exactly one successful internal request during fallback: **Pass**.
10. Local health passed after runtime restoration: **Pass**.

## Conclusion

The RFC-0039 file-based declaration mode has been reproduced successfully on two real machines at the recorded repository revision.

The verification confirms that repeatable static declaration changes only how the existing two remote topology facts are supplied. It does not change:

- the one-local-plus-one-remote topology;
- local-first selection;
- the accepted narrow remote fallback;
- loopback-only exposure on the calling machine;
- operator-owned runtime and remote application lifecycle;
- static, explicit topology ownership;
- the absence of discovery, reload, file watching, precedence, or generic configuration behavior.

## Privacy boundary

This retained record contains no real private LAN address, remote base URL, prompt, generated response, credential, authorization value, machine name, model name, filesystem path, hardware detail, raw exception, raw log, personal account detail, or secret.
