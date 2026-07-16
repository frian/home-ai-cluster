# Phase 8 Ordinary Static Multi-Node Proof

Status: Pending operator verification

## Purpose

Record future operator verification of the ordinary static multi-node mode
accepted by RFC-0038. This is a pending proof scaffold, not a successful
two-machine result.

## Implemented repository evidence

The repository currently provides:

- `home-ai-cluster-static-cluster` for one local node and one explicitly
  declared remote node;
- `home-ai-cluster-preflight` support for the same local-plus-declared-remote
  static declaration projection;
- ordinary local-only operation as the default path;
- `home-ai-cluster-static-proof` as a separate historical proof process;
- local-first narrow fallback through a proof-neutral orchestration seam;
- cluster-owned remote result attribution;
- no discovery, supervision, remote control, network preflight, retry loop, or
  persistent topology.

## Required operator verification

The operator must confirm all of the following before this record can be
completed:

1. the local-only workflow still works;
2. multi-node preflight reports local then remote;
3. preflight performs no network request;
4. the receiving application is reachable from the calling machine;
5. the calling static multi-node process binds only to loopback;
6. usable local execution remains local;
7. the accepted local pre-request connection failure falls back once to the
   declared remote;
8. returned attribution identifies the declared remote node;
9. the remote URL is absent from public errors, retained history, and proof
   records;
10. shutdown and temporary-firewall cleanup follow the canonical order;
11. the historical proof command remains separate and unchanged.

## Pending completion record

Pending operator verification. Do not add execution dates, actual node IDs,
addresses, model names, machine names, request or response contents, timings,
hardware details, filesystem paths, screenshots, raw logs, or raw exceptions
until a privacy-safe completion record is explicitly prepared.

## Privacy boundary

Do not retain real private LAN addresses, prompts, generated responses, remote
base URLs, credentials, authorization values, machine names, filesystem paths,
hardware details, raw exceptions, personal account details, or secrets.

Allowed retained evidence is limited to sanitized command names, repository
revision, fixed public statuses, cluster-owned placeholder node IDs, pass/fail
statements, normalized failure categories, and test counts.
