# Ordinary loopback port investigation

Status: Investigation only

Date: 2026-08-29

## Question

Should the ordinary Home AI Cluster (HAC) loopback convention move from
`127.0.0.1:8000` to `127.0.0.1:25042` before 0.5.0? This document records
evidence for maintainers; it makes no architectural decision and authorizes no
implementation. An investigation may recommend a decision; only an accepted
RFC can authorize the architectural change.

## Current state

Current `main` (4c4578b) has two ordinary server defaults: `hac local` uses
`LOCAL_RUNTIME_PORT = 8000`, including its explicit `--port` default, and
`hac static-cluster` uses fixed `STATIC_CLUSTER_PORT = 8000`. Both default to
loopback. The loopback browser is added only for those loopback-owned launcher
paths, so its same-origin page is the ordinary origin.

Five installed caller edges are fixed to that ordinary origin: Chat
(`/v1/chat`), Summarize (`/v1/summarize`), Classify (`/v1/classify`), Aider's
private translator (`/v1/chat`), and external-information source-grounded Chat
(`/v1/chat/sources`). They do not accept a base-URL or port option.

`hac local --port <other>` is already valid. It starts a server at the
operator-selected address, but the installed ordinary callers still request
8000. Thus it is an explicit server override, not current client discovery or
configurability. Moving the *ordinary default* would preserve that limitation:
clients would use the new fixed default and would still not discover an
arbitrary `--port`. Resolving that broader mismatch is out of scope.

The separate OpenAI-compatible process owns `127.0.0.1:8001`; the separately
packaged SearXNG plugin has its own accepted `127.0.0.1:8888` endpoint. Neither
is part of this question. Explicit operator-supplied remote-node URLs and
runtime-provider URLs are likewise not ordinary defaults.

## Current 8000 ownership

The complete repository search for `8000`, `127.0.0.1:8000`, and
`localhost:8000` returned 314 matching lines in 95 files. That raw result is
not a migration list: it includes remote examples and retained evidence. The
following classification distinguishes ownership.

### A. Current executable behavior

Seven production occurrences own the ordinary convention: the two server-port
constants above and the five fixed caller URLs. These would move together if a
future RFC changes the convention. The browser inherits the bind/origin rather
than containing a separate port constant.

### B. Current tests protecting executable behavior

Five dedicated caller test modules assert direct `127.0.0.1:8000` requests
(Chat, Summarize, Classify, Aider, and external information). Local-runtime and
static-cluster tests protect the two server defaults through their constants.
Those tests are current-contract tests and would change with an accepted port
decision. Many remaining test matches are deliberately arbitrary declared
remote addresses such as `https://remote.example:8000`; those validate explicit
URL handling and should not be rewritten merely because their fixture happens
to use 8000.

### C and E. Current user documentation and examples

Current operator-facing references occur in `README.md`, `docs/getting-started.md`,
`docs/index.md`, `docs/command-reference.md`, `docs/operator-workflow.md`, and
`docs/static-cluster-declaration.md`. Their ordinary local/browser examples
would need alignment. Remote receiver and static-declaration examples require
case-by-case treatment: a receiver started with the ordinary default should
show the new port, while an explicitly supplied remote URL remains operator
owned and is not globally rewritten.

### D. Accepted RFC contracts

| RFC | Contract | 8000 status | Future action |
| --- | --- | --- | --- |
| RFC-0038, *Ordinary static multi-node mode* | §Proposal/§Process ownership requires the existing native endpoint on the existing ordinary application port. | Implicit ordinary-port dependency, not a literal value. | Amend/clarify in the new RFC. |
| RFC-0045, *One-shot ordinary request command* | §Summary and §Decision require `POST http://127.0.0.1:8000/v1/chat` and prohibit a host/port option. | Normative literal target. | Amend. |
| RFC-0054, *Minimal Summarize CLI* | §Proposal requires `POST http://127.0.0.1:8000/v1/summarize`. | Normative literal target. | Amend. |
| RFC-0062, *Minimal Loopback Web Client* | §Network and origin boundary says loopback browser launchers own the existing `127.0.0.1:8000` bind. | Normative literal origin. | Amend. |

RFC-0049, RFC-0055 through RFC-0057, RFC-0061, RFC-0063, RFC-0067 through
RFC-0070, RFC-0077 through RFC-0078, RFC-0080 through RFC-0088, and their
accepted browser/client extensions reuse one of those ordinary fixed endpoints
or same-origin composition. They do not independently select port 8000; a new
RFC should state that their inherited endpoint references move with the amended
base contracts, without rewriting accepted history. RFC-0031 and RFC-0046 own
the separate compatibility edge, not the ordinary port. RFC-0079 owns literal
SearXNG port 8888 and must remain unchanged. RFC-0089's `:8000` remote URL
examples illustrate an explicitly supplied optional port and are not a default.

### F. Historical proof, investigation, and closeout artifacts

Historical proofs, runbooks, closeouts, and investigations contain many of the
remaining direct-loopback matches (31 documentation files and the older
RFC-0022/RFC-0026 proof contracts). They record the port true at the time of
evidence. They should remain untouched unless an artifact is explicitly a
living current runbook; they are not migration work.

### G. Incidental or unrelated occurrences

Examples, tests, and RFCs also use `:8000` for hypothetical remote endpoints,
trusted-LAN receivers, and URL-shape validation. Their port is explicit
operator input, not an HAC default. The bundled PDF.js asset was excluded from
semantic conclusions despite containing numeric text that makes raw searching
noisy.

## Candidate port 25042

### IANA status

On 2026-08-29, a direct check of IANA's current CSV registry found no row for
either TCP or UDP port 25042. It is therefore unassigned in that registry at
the time checked, not reserved for HAC and not guaranteed to stay unused. IANA
defines User Ports as 1024–49151; 25042 is in that range.

### OS ephemeral and dynamic ranges

The current Linux kernel documentation gives the default IPv4 local-port range
as 32768–60999. Microsoft documents a default dynamic TCP/IP range of
49152–65535 for modern Windows. Port 25042 is below both defaults, so it avoids
collision with ordinary automatic outbound-port allocation on those defaults.
Administrators can change either range; this is a default-range observation,
not a universal guarantee.

### Observed usage

No current public, methodologically described port-prevalence dataset was
available in this investigation that could make a reliable claim about zero or
low real-world use of 25042. A registry lookup and default ephemeral ranges are
strong evidence for their narrower questions, but neither measures local
developer-tool collisions. The recommendation intentionally does not depend on
the prior unverified Shodan-top-1000 assertion or treat absence from any scan as
absence of use.

### Practical assessment

25042 is a defensible boring candidate: it is memorable enough for a documented
fixed local endpoint, currently unassigned, in the IANA User Port range, and
outside common Linux and Windows automatic ranges. Its principal downside is
that no fixed port can prevent a locally installed program from claiming it,
and less familiar numbers modestly increase documentation/muscle-memory cost.
Those downsides are smaller than retaining a development-tool convention that
is commonly occupied on first use. No evidence here supports dynamic allocation
or a search for a mathematically unused port.

## Contract impact and smallest coherent future change

If accepted, one coherent implementation would change only the ordinary
convention together: the `hac local` default, fixed static-cluster bind, five
ordinary caller URLs, their focused tests, loopback-browser origin tests, and
living user-facing ordinary examples. It would retain `--port` exactly as it
is; it would not add discovery, environment configuration, fallback selection,
or compatibility behavior.

It would not move OpenAI compatibility 8001, SearXNG 8888, runtime-provider
ports, explicit remote-node URLs, or historical evidence. An ordinary receiver
operator who deliberately supplies `--port 8000` could continue to do so, but
fixed clients would not target it; that existing boundary should be documented,
not solved incidentally.

## Alternatives considered

* **Keep 8000.** Familiar but carries a credible collision risk with ordinary
  development/local-web tooling at the 0.5 first-use stage.
* **Use 25042.** Supported by the bounded registry and OS-default evidence;
  entails a contained RFC, implementation, test, and current-documentation
  alignment cost before 1.0.
* **Use another arbitrary high User Port.** Could be defensible, but this audit
  found no evidence that another candidate is materially better; choosing one
  would restart a small, unnecessary optimization exercise.
* **Dynamically select an available port.** Rejected. It would require client
  discovery/propagation, make the browser origin and fixed-client contracts
  less predictable, and expands scope into configuration/lifecycle design.

## Recommendation

**C. Change to 25042; amend specific accepted RFC(s).** The first-use benefit
and pre-1.0 timing justify a deliberate fixed-convention change. The conclusion
is bounded: it says 25042 is defensible today, not uniquely optimal or immune
to local collisions.

## Required RFC path

Draft one new, narrow RFC that changes the ordinary fixed loopback convention
to `127.0.0.1:25042`. It should explicitly amend RFC-0038's ordinary static
port dependency and RFC-0045, RFC-0054, and RFC-0062's literal contracts, and
state that their accepted dependent caller/browser extensions inherit the new
ordinary origin. Accepted RFC files should not be edited retrospectively. Only
after acceptance should a focused implementation/documentation PR follow.

## Non-goals

This investigation does not change a port, code, tests, URLs, RFCs, the plugin
repository, 8001, 8888, automatic free-port selection, service discovery,
persistent/configuration/environment port settings, endpoint abstractions,
migration compatibility, or historical evidence.

## Sources

* [IANA Service Name and Transport Protocol Port Number Registry](https://www.iana.org/assignments/service-names-port-numbers) and its [CSV form](https://www.iana.org/assignments/service-names-port-numbers/service-names-port-numbers.csv), checked 2026-08-29.
* [Linux kernel IP sysctl documentation: `ip_local_port_range`](https://www.kernel.org/doc/html/latest/networking/ip-sysctl.html).
* [Microsoft: TCP/IP port exhaustion troubleshooting](https://learn.microsoft.com/en-us/troubleshoot/windows-client/networking/tcp-ip-port-exhaustion-troubleshooting).
* Repository audit on `main` commit `4c4578b`, including `src/`, `tests/`,
  current docs, examples, accepted RFCs, and retained artifacts.
