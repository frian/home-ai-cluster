# Phase 8 Ordinary Static Multi-Node Proof

Status: Verified

## Purpose

Record operator verification of the ordinary static multi-node mode accepted by
RFC-0038.

This record is intentionally privacy-safe. It retains only repository revision,
sanitzed command names, placeholder node identity, normalized observations, and
pass/fail results.

## Verification basis

Repository revision:

```text
6650c183b3281758631f4ed5a99a42f94bb9f21b
```

Both machines used the same clean `main` revision, dependency synchronization
completed, and the full test suite passed on both machines before operator
verification began.

The declared remote node identifier used for the retained record is:

```text
remote-node
```

No real private address, machine name, model name, prompt, generated response,
filesystem path, hardware detail, credential, raw exception, or raw log is
retained.

## Verified operator sequence

### Ordinary local-only operation

The ordinary local-only workflow was verified independently on both machines.

On each machine:

- `home-ai-cluster-preflight` passed;
- `home-ai-cluster-health` passed while the external local runtime was usable;
- one native request completed through `127.0.0.1:8000/v1/chat`;
- returned attribution identified the local node;
- no remote URL appeared in the public response;
- the ordinary application stopped normally.

Result: **Pass**.

### Receiving-machine preparation and LAN reachability

On the receiving machine:

- local preflight passed;
- local health passed;
- the ordinary application started explicitly on `0.0.0.0:8000`;
- no temporary firewall rule was required;
- the receiving application was reachable from the calling machine over the
  trusted LAN;
- one direct reachability request completed successfully;
- returned attribution was present;
- no remote URL appeared in the public response.

Result: **Pass**.

### Calling-machine static multi-node preflight

On the calling machine, `home-ai-cluster-preflight` was invoked with one explicit
remote node declaration.

The operator confirmed:

- the preflight passed;
- the report listed the local node before `remote-node`;
- the receiving application observed no HTTP request during preflight;
- the supplied remote URL did not appear in the report or normalized errors.

This confirms that multi-node preflight remained a static, read-only inspection
and performed no network request.

Result: **Pass**.

### Local-first selection

With the calling machine's external local runtime usable,
`home-ai-cluster-static-cluster` was started with the explicit `remote-node`
declaration.

The operator confirmed:

- the process started successfully;
- it listened only on `127.0.0.1:8000`;
- one request through the calling loopback endpoint succeeded;
- returned attribution identified the local node;
- the receiving application observed no HTTP request for this request;
- no remote URL appeared in the public response.

This confirms that a usable local candidate retained precedence.

Result: **Pass**.

### Accepted remote fallback

The calling machine's externally owned local runtime was stopped normally while
the calling Home AI Cluster process remained running. Local health then reported
the runtime unavailable.

One request was sent through the calling loopback endpoint.

The operator confirmed:

- the request succeeded;
- the receiving application observed exactly one successful internal cluster
  request;
- returned attribution identified `remote-node`;
- no remote URL appeared in the public response;
- no retry loop was observed.

The public result exposed final remote attribution but did not include a separate
fallback explanation field. Fallback was therefore verified from the combined
normalized operational evidence: local runtime unavailable, one successful
remote internal request, and final attribution to `remote-node`.

Result: **Pass**.

### Optional history inspection

After the verification, `home-ai-cluster-history` returned an empty history.
Therefore no remote URL, prompt, or generated response was retained.

Result: **Pass**.

### Shutdown and restoration

Shutdown followed the canonical order:

1. the calling static multi-node process stopped first;
2. the receiving ordinary application stopped second;
3. no firewall cleanup was required because no temporary rule had been created;
4. the calling machine's external local runtime was restored manually;
5. local health passed after restoration.

The historical `home-ai-cluster-static-proof` command remained available as a
separate command and was not used as the ordinary multi-node process.

Result: **Pass**.

## Required verification checklist

1. Ordinary local-only workflow still works: **Pass**.
2. Multi-node preflight reports local then remote: **Pass**.
3. Preflight performs no network request: **Pass**.
4. Receiving application is reachable from the calling machine: **Pass**.
5. Calling static multi-node process binds only to loopback: **Pass**.
6. Usable local execution remains local: **Pass**.
7. Accepted local pre-request connection failure falls back once: **Pass**.
8. Returned attribution identifies `remote-node`: **Pass**.
9. Remote URL is absent from public responses, optional history, and retained proof: **Pass**.
10. Shutdown and firewall handling follow canonical order: **Pass**.
11. Historical proof command remains separate and unchanged: **Pass**.

## Conclusion

Ordinary explicit static multi-node operation has been reproduced successfully
on two real machines at the recorded repository revision.

The verification confirms the intended RFC-0038 boundaries:

- one local node and one explicitly declared remote node;
- local-first selection;
- exactly one accepted remote fallback path;
- final cluster-owned remote attribution;
- loopback-only exposure on the calling machine;
- static preflight without network observation;
- no retry loop, discovery, supervision, remote control, or persistent topology;
- operator-owned runtime and remote application lifecycle.

The historical explicit two-machine proof remains separate.

## Privacy boundary

This retained record contains no real private LAN address, remote base URL,
prompt, generated response, credential, authorization value, machine name,
model name, filesystem path, hardware detail, raw exception, raw log, personal
account detail, or secret.
