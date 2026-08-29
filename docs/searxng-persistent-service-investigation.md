# SearXNG Persistent-Service Investigation

Status: Investigation

Date: 2026-08-29

## Scope and question

This is a bounded documentation investigation for the `0.6.0.dev0` daily-use
friction slice. It does not authorize a Home AI Cluster (HAC) or plugin change,
a service file, SearXNG configuration, container instructions, or an RFC.

The question is:

> Is there one current, upstream-supported, boring Linux persistent-service path
> that the SearXNG plugin README can document concisely after its existing
> foreground validation steps, while preserving direct loopback HTTP
> `127.0.0.1:8888` and leaving all lifecycle ownership with the operator?

## Current accepted ownership boundary

RFC-0078, RFC-0079, and RFC-0091 remain authoritative. SearXNG is optional
and independently installed, configured, and already running. HAC, its ordinary
server, and the separately installed plugin do not install, configure, start,
stop, upgrade, repair, supervise, health-manage, or otherwise own it.

The plugin's sole provider destination remains the literal direct HTTP endpoint
`http://127.0.0.1:8888/search`. It makes one bounded POST. There is no
configurable endpoint, HAC-owned proxy, lifecycle authority, or requirement for
ordinary HAC use.

Consequently, any future README text would need to say that the operator chooses
and enables the service; the OS and SearXNG tooling govern startup and boot;
stopping HAC does not stop SearXNG; removing the plugin does not stop or remove
SearXNG; upgrades and failures remain operator/SearXNG concerns; and ordinary
HAC remains functional without either optional component.

## Current documented operator workflow

The plugin README already documents an optional Ubuntu/Debian-oriented setup,
the fixed loopback and JSON settings, the `python -m searx.webapp` foreground
check, and an independent `curl` POST to `/search`. It explicitly identifies
that foreground process as validation only and delegates persistent setup to
SearXNG upstream. It also preserves the distinction between an
operator-validated integrated exercise on a partially prepared host and a
clean-machine installation, which this project has not validated.

## Current upstream persistence model

Official SearXNG documentation inspected on 2026-08-29 reports version
`2026.8.29+d226b78bc` on its installation, step-by-step, installation-script,
uWSGI, and `searxng.sh` pages. Its installation overview recommends either its
container or Installation Script when there is no special preference. The
script's `install all` path installs the reference setup, including uWSGI.

The step-by-step guide uses `python -m searx.webapp` after enabling debug, then
asks the operator to visit the loopback URL or run `curl`. This is a
configuration/foreground verification path, not its persistent deployment
mechanism. Its persistent guidance is uWSGI. Granian is described as a future
uWSGI replacement, but currently officially supported only in SearXNG's
container installation.

Upstream also says that distribution uWSGI implementations differ: Debian/
Ubuntu use an apps-available/apps-enabled layout and service command; Arch uses
a systemd template; and Fedora/RHEL use an Emperor-oriented layout. A single
cross-distribution service instruction would therefore be false. SearXNG is a
rolling release; its maintenance page directs operators to its installation
method's update and inspection procedures and warns that service configuration
may need migration.

Primary upstream evidence: [installation](https://docs.searxng.org/admin/installation.html),
[step-by-step installation](https://docs.searxng.org/admin/installation-searxng.html),
[Installation Script](https://docs.searxng.org/admin/installation-scripts.html),
[uWSGI](https://docs.searxng.org/admin/installation-uwsgi.html),
[`utils/searxng.sh`](https://docs.searxng.org/utils/searxng.sh.html), and
[maintenance](https://docs.searxng.org/admin/update-searxng.html).

## Direct HTTP `127.0.0.1:8888` requirement

Persistence alone is insufficient. RFC-0079 requires the plugin to reach
SearXNG directly by HTTP at `127.0.0.1:8888`; a Unix socket behind an unspecified
reverse proxy does not meet that evidence requirement.

The current official uWSGI page says that the Installation Script installs a
uWSGI setup that listens on a socket. Its maintained distribution templates use
`socket = /usr/local/searxng/run/socket`; that is not a TCP HTTP listener at the
accepted endpoint. The page documents the distribution-specific lifecycle for
that template, but no SearXNG-maintained direct-HTTP `127.0.0.1:8888` variant,
stable generation command for one, or concise configuration delta from its
socket default. Its installation script likewise describes installing the uWSGI
application, not an HTTP-listener variant.

The upstream documentation does provide reverse-proxy material, but adding a
proxy merely to translate the socket for this local plugin would add operator
machinery and does not answer this slice. Copying or locally modifying a large
generated `searxng.ini` to select an undocumented uWSGI HTTP option would freeze
configuration that upstream has not supplied as this contract.

## Candidate comparison

| Candidate | Evidence-based assessment |
| --- | --- |
| A. Keep foreground validation only | Accurately preserves the existing verified workflow, but does not remove repeated manual starts. |
| B. Official Installation Script / `searxng.sh` | Upstream-supported for installation, maintenance, and a uWSGI reference setup, but that setup defaults to a socket. It does not establish direct HTTP at `127.0.0.1:8888`. |
| C. Distribution uWSGI service with SearXNG template | Upstream documents per-distribution enable/start mechanisms, but the maintained template is socket-oriented and the service mechanism differs by distribution. It cannot truthfully be reduced to a direct-HTTP path. |
| D. Custom unit running `python -m searx.webapp` | Rejected for this documentation follow-up: upstream presents it in the debug/validation sequence, not as its persistent deployment mechanism. |
| E. Container deployment | Officially available, and Granian is currently supported there, but outside this non-container-first slice. |
| F. HAC or plugin lifecycle management | Incompatible with the accepted operator-owned boundary and out of scope. |

## Distribution/version considerations

The existing plugin setup is Ubuntu/Debian-oriented, so a later smallest path
could be limited to that family. However, the current evidence cannot support
even that narrow README addition: Debian/Ubuntu's supported uWSGI lifecycle
still begins with the upstream socket template. Arch and Fedora/RHEL must not be
covered by borrowed Debian commands; their upstream service models differ, and
the Fedora/RHEL Emperor/Tyrant path has separately documented caveats.

No Linux distribution or release was newly operator-validated in this
investigation.

## Evidence limitations

This investigation establishes only documentation facts, not an installed
service. The earlier successful operator exercise used an already partially
prepared host; it did not validate a clean-machine SearXNG installation.
Neither that exercise nor the current upstream pages establishes that an
upstream-supported persistent service exposes direct loopback HTTP on port
8888. It would be incorrect to turn the foreground validation success or a
socket-backed persistent service into that claim.

## Outcome

### Outcome B — evidence is insufficient

There is not currently one documented path that the plugin README can concisely
recommend while truthfully proving the fixed direct HTTP contract. Upstream
supports persistent uWSGI deployment and distribution-specific management, but
its installation tooling and maintained template default to a Unix socket.
Current official SearXNG documentation does not establish a stable,
upstream-maintained direct-TCP HTTP `127.0.0.1:8888` configuration or generation
mechanism for that persistent service. A custom `webapp` unit, copied uWSGI
configuration, or HAC/plugin-owned proxy would fill the gap by invention rather
than evidence.

The smallest next evidence-gathering step is to obtain a current official
SearXNG-supported direct-HTTP persistent-service configuration or generation
mechanism that preserves `127.0.0.1:8888`; only then should an operator exercise
that exact path on its stated distribution and verify it with the existing
independent `curl` POST. If that evidence arrives, a separate docs-only PR in
`frian/home-ai-cluster-plugin-searxng` can add a short operator-owned section.
No RFC is required for such a documentation-only follow-up because it would not
change HAC or plugin behavior or ownership.

## Next step

Do not change either repository's user documentation now. Revisit this bounded
question only after the missing upstream direct-HTTP evidence exists; otherwise
retain the current foreground-validation text and upstream persistent-service
delegation.
