# Phase 10 Multiple Explicit Static Remote Nodes Proof

Status: Verified

Date: 2026-07-17

## Purpose

Record operator verification that the RFC-0040 ordered explicit static remote
node behavior was reproduced through the ordinary static cluster process.

This record verifies routing and fallback behavior, not generated model quality.
It does not retain the prompt or generated response used during the proof.

## Verification basis

The proof used three real machines on one trusted LAN:

- the calling machine, represented by the cluster-owned identity `local`;
- a separate real first remote machine, represented by `remote-a`; and
- a separate real receiving machine, represented by `remote-b`.

The calling machine and the successful receiving machine used this repository
revision:

```text
fac349af5d309a91c8c55e486b30c83113409b39
```

`remote-a` was a separate real machine with no service listening at its
declared endpoint. `remote-b` was a separate real machine running the ordinary
Home AI Cluster application and an available local runtime adapter.

No real private address, machine name, base URL, model name, prompt, generated
response, filesystem path, hardware detail, credential, raw exception, raw log,
personal account detail, or secret is retained.

## Verified operator sequence

### Receiving machine preparation

The operator confirmed on `remote-b`:

- static preflight passed;
- local health passed;
- the ordinary Home AI Cluster application listened on the trusted LAN; and
- the local runtime adapter was available for ordinary local execution.

Result: **Pass**.

### Calling declaration and static preflight

The calling machine used one explicit RFC-0040 TOML declaration with remotes in
this order:

1. `remote-a`
2. `remote-b`

Declaration preflight reported a coherent static-multi-node topology in this
order:

1. `local`
2. `remote-a`
3. `remote-b`

This was static declaration validation only. It did not probe the network,
reach either remote endpoint, inspect either remote runtime, or establish that
later request execution would succeed.

Result: **Pass**.

### Ordered fallback request

The operator manually stopped the calling machine's local runtime. Calling
local health then reported it unavailable.

The ordinary static cluster process was started with:

```text
home-ai-cluster-static-cluster --declaration <operator-owned-declaration-path>
```

The calling endpoint retained its loopback-only exposure. One request was sent
through that endpoint.

The operator confirmed:

- local execution was unavailable;
- `remote-a`, the first declared remote, produced a real connection-unavailable
  failure before request transmission;
- the first unavailable remote was a real separate machine, and its unavailable
  endpoint exercised the accepted pre-request connection-unavailable fallback
  boundary;
- fallback advanced from `remote-a` to `remote-b` in declaration order;
- `remote-b` received exactly one successful `POST` request on
  `/internal/cluster/request`;
- the final response carried cluster-owned node attribution `remote-b`; and
- no retry loop or repeated successful remote request was observed.

Result: **Pass**.

### Shutdown and restoration

The calling static cluster process and the receiving application were stopped
manually. The calling local runtime was restored manually, and calling local
health then passed.

Result: **Pass**.

## Required verification checklist

1. Three real machines on one trusted LAN were used: **Pass**.
2. The calling and successful receiving machines used the recorded revision:
   **Pass**.
3. `remote-a` was a separate real machine with no service at its declared
   endpoint: **Pass**.
4. Receiving-machine static preflight and local health passed: **Pass**.
5. The receiving application listened on the trusted LAN: **Pass**.
6. The RFC-0040 declaration retained `remote-a`, then `remote-b`: **Pass**.
7. Declaration preflight reported `local`, `remote-a`, then `remote-b` without
   network probing: **Pass**.
8. Calling local health reported the manually stopped local runtime unavailable:
   **Pass**.
9. The ordinary declaration-mode process retained loopback-only calling
   exposure: **Pass**.
10. The real pre-request connection-unavailable failure at `remote-a` advanced
    fallback to `remote-b`: **Pass**.
11. `remote-b` received exactly one successful internal request: **Pass**.
12. The final response attributed execution to `remote-b`: **Pass**.
13. No retry loop or repeated successful remote request was observed: **Pass**.
14. Calling and receiving processes were stopped manually: **Pass**.
15. Calling local health passed after manual runtime restoration: **Pass**.

## Conclusion

Phase 10's ordered explicit multi-remote static cluster behavior was reproduced
successfully on three real machines at the recorded repository revision.

The reproduction confirms one declared remote can fail before request
transmission, after which the ordinary static cluster process advances once to
the next declared remote in operator-specified order and returns that remote's
cluster-owned attribution. It records no broader retry, discovery, scheduling,
or lifecycle behavior.

## Privacy boundary

This retained record contains only the placeholder identities `local`,
`remote-a`, and `remote-b`, plus the repository revision and normalized
verification results. It contains no private IP address, real machine name,
real base URL, model name, prompt, generated response, local filesystem path,
raw log, raw exception, hardware detail, credential, secret, or personal
account detail.
