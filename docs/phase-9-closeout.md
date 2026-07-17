# Phase 9 Closeout

Status: Complete

Date: 2026-07-17

## Goal

Phase 9 made the verified ordinary static multi-node mode convenient to start repeatedly without changing its static architecture.

The phase success condition was:

> One operator can restart the same explicit static cluster without rebuilding
> its declaration by hand.

That condition has been met.

## Completed outcomes

Phase 9 delivered:

- one explicit operator-selected TOML declaration file;
- exactly one declared remote node in addition to the existing local node;
- the startup command `home-ai-cluster-static-cluster --declaration <path>`;
- strict startup validation before application construction and server startup;
- compact repository-owned CLI errors;
- an operator document for the declaration mode;
- a safe repository example containing no real private address or secret;
- a retained real two-machine proof of declaration-mode operation.

## Architectural basis

RFC-0039 defines the accepted declaration contract:

- exactly two top-level TOML keys: `remote_node_id` and `remote_base_url`;
- string values only;
- unknown keys and nested sections rejected;
- no default path, search path, environment source, merge, precedence, or reload;
- no secrets in the declaration;
- no network observation while loading the declaration;
- no new runtime dependency.

The implementation preserved the previously accepted RFC-0038 topology and behavior.

## Verified behavior

Real operator verification on two machines confirmed:

- both machines used the same repository revision;
- receiving-machine preflight and health passed;
- the calling process started from the explicit declaration file;
- the calling endpoint remained bound to loopback;
- a usable local runtime retained precedence;
- no receiving-machine request occurred during local-first execution;
- after the calling local runtime became unavailable, the accepted fallback selected `remote-node`;
- the receiving machine observed exactly one successful internal request during fallback;
- local health passed after manual runtime restoration.

## Preserved boundaries

Phase 9 did not add:

- automatic node or model discovery;
- process supervision;
- remote process or runtime control;
- file watching or reload;
- environment-variable topology;
- configuration merging or precedence;
- direct node targeting;
- additional nodes;
- retry loops, balancing, scoring, or scheduling;
- a generic configuration system;
- persistent topology owned by Home AI Cluster.

External runtimes, remote applications, declaration files, and lifecycle actions remain operator-owned.

## Retained evidence

The completed phase is represented by:

- `RFC/RFC-0039-repeatable-static-cluster-declaration.md`;
- `docs/static-cluster-declaration.md`;
- `examples/static-cluster.toml`;
- `docs/phase-9-repeatable-static-cluster-declaration-proof.md`.

## Conclusion

Phase 9 is complete.

The ordinary static local-plus-one-remote cluster can now be restarted from one explicit, validated, privacy-safe declaration without reconstructing its topology arguments by hand.

The result remains local-first, privacy-first, engine-independent, capability-centered, static, explicit, and operator-owned.

No next architectural phase is selected by this closeout. Any new architectural direction requires separate roadmap work and an RFC before implementation.
