# RFC-0113 Retained Remote-Node Proof

Status: Post-1.0 development record

## Purpose

This factual record retains the already completed real operator proof of the
accepted RFC-0113 retained remote-node browser facade. It records caller-owned
retained topology on `sat` and ordinary remote execution on `rasp`; it makes no
new architectural decision or behavior claim.

## Relevant boundary

RFC-0094 defines retained configuration as a local baseline for later ordinary
invocations. RFC-0113 extends the loopback browser facade to caller-owned
retained remote-node declarations only. A browser change therefore changes
retained future state, not the already constructed process or its
`LocalAppComposition`.

## Environment

The proof used two real HAC machines:

- caller/local machine: `sat`;
- remote receiver machine: `rasp`.

The receiver was configured by its own local operation. The browser on `sat`
managed only `sat`'s retained declaration of `rasp`: its node ID, an explicit
HTTP base URL, and caller-declared allowed capabilities.

## Observed proof sequence

### Initial retained addition

Using the RFC-0113 browser configuration facade on `sat`, the operator added a
retained declaration for `rasp` with allowed capability `summarize`. `hac
config show` immediately reflected that retained declaration.

An ordinary running `hac static-cluster` composition that consumed the retained
topology routed a real `summarize` request from `sat` to `rasp`. The result
identified `rasp` as the executing node. This established that the
browser-created declaration was valid ordinary HAC topology, not browser-only
state.

### Retained modification while running

While that `static-cluster` process remained running, the browser edited
`rasp`'s allowed capability from `summarize` to `chat`. Immediately after the
save, `hac config show` reported `chat` as the retained future state.

The running process was neither reconstructed nor reconfigured. It retained
its startup topology and continued to route `summarize` to `rasp`. This was
the expected retained-state distinction, not a stale-state failure.

### Restart consumes the modification

After that ordinary process was stopped and started again, it consumed the new
retained state. `summarize` was no longer available through that topology; the
ordinary request failed with exit status `1`. `chat` was eligible for `rasp`,
and a real `chat` request routed to `rasp`.

### Retained removal while running

While the restarted process was running with `rasp` eligible for `chat`, the
browser removed the retained `rasp` declaration. `hac config show` immediately
showed no retained remote node.

The running process remained unchanged and continued to route `chat` to
`rasp` using the topology it had consumed at startup.

### Restart after removal

After stopping that process, an attempted `hac static-cluster` startup found no
retained static remote topology for that invocation and correctly refused with
exit status `2`.

## Conclusion

Browser mutation changes retained future state immediately; the current process
remains unchanged; the next launch consumes the new retained state.

The proof demonstrates both retained directions:

- Modification changes retained inspection immediately, leaves the current
  process unchanged, and is consumed after restart.
- Removal changes retained inspection immediately, leaves the current process
  unchanged, and is consumed after restart.

## Boundaries preserved

This proof does not show that the browser configures `rasp`, observes its
runtime or model facts, probes its URL, discovers capabilities, validates
health, or administers the remote machine. It does not add live topology
reconfiguration, `LocalAppComposition` reconstruction, HAC reload/restart,
current-process mutation, connection testing, scheduling, or a control plane
or dashboard.

The configured URL and allowed capabilities remain inert caller-declared
retained facts until a future ordinary invocation consumes them under the
accepted configuration and startup semantics.
