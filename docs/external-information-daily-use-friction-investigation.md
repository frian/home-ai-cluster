# External-Information Daily-Use Friction Investigation

Status: Investigation

Date: 2026-08-29

## Scope and status

This is a bounded, documentation-only investigation for the 0.6 comfortable /
daily-driver development line. It is not an accepted design, an RFC, an
implementation plan, a roadmap change, or authorization to change command
behavior. It makes no architectural decision.

The question is:

> In repeated explicit `hac external-information` use, which operator steps are
> genuine repeated friction, which are intentionally visible authority or trust
> decisions, and is there one smallest bounded improvement worth a later RFC or
> documentation change?

The evidence is limited to the accepted RFCs, current implementation and tests,
current documentation, and the privacy-safe operational observations supplied
for this investigation. Examples below are synthetic. No conclusion claims a
user-study frequency or severity that this evidence does not establish.

## Current accepted contract

The exact current command shape is:

```sh
hac external-information \
  --plugin NAME \
  --query QUERY \
  --question QUESTION
```

RFC-0078 gives the three values separate meanings:

- `NAME` is the exact caller/operator-selected acquisition plugin.
- `QUERY` is the exact acquisition input supplied to that selected plugin.
- `QUESTION` is the later RFC-0077 source-grounded operator question; it is not
  passed to the plugin.

One selected plugin is invoked exactly once. Only successfully reconstructed
and fully RFC-0077-validated evidence reaches the existing source-grounded Chat
boundary. The subsequent request remains ordinary `capability=chat` routing;
this caller edge creates no external-information capability.

The same accepted boundary deliberately requires that installation is not
authorization to use a plugin. The operator selects the exact plugin for each
operation; HAC must not choose another after failure or silently fall back to
unsourced ordinary Chat. Acquisition remains separate from ordinary `hac chat`.

RFC-0077 keeps the later question structurally distinct from untrusted source
evidence. RFC-0079 supplies the concrete `searxng` plugin contract only after
the explicit selection: one bounded call to the already running,
operator-owned `127.0.0.1:8888` service. RFC-0090 fixes the ordinary HAC caller
target at `127.0.0.1:25042`.

## Smallest repeated successful workflow

The following is the smallest SearXNG-backed repeated path; it does not make
SearXNG a general HAC prerequisite.

| Frequency | Operator fact | Boundary and observation |
| --- | --- | --- |
| Infrequent setup | Install the optional plugin in the same Python / `uv tool` environment as `hac`; independently configure SearXNG. | Plugin installation makes one named distribution available, not authorized or loaded. |
| Session/startup | Start or otherwise make the operator-owned SearXNG service available at `127.0.0.1:8888`; start ordinary HAC at `127.0.0.1:25042`. | Neither service is installed, started, stopped, repaired, supervised, or health-managed by HAC. |
| Per request | Explicitly select `searxng`, supply an acquisition query, and supply a source-grounded question. Optionally choose an existing output or timeout mode. | The selected plugin receives only the query once; after validation HAC sends one source-grounded request and performs ordinary Chat routing. |

The retained real exercise establishes that this full path works when these
prerequisites hold. It also establishes practical setup confusion about plugin
environment placement and HAC-process availability, and that constructing the
three explicit values repeatedly is more ceremonial than ordinary `hac chat`.
It does not establish a need for HAC-owned SearXNG lifecycle.

## Friction classification

### Syntax ceremony

Repeated long option names, repeated `--plugin searxng`, shell quoting, and
constructing both text values are observable command-construction work. The
option spelling itself does not confer authority. In contrast, the values are
not interchangeable syntax: plugin selection is a disclosure choice, the query
is provider acquisition input, and the question is a later model instruction.
Having both text values is therefore not automatically redundant even when a
common case makes them similar.

### Authority and privacy explicitness

Repeated exact plugin selection is intentionally visible. Under RFC-0078 it is
the operator's per-operation choice of trusted installed Python and its network
disclosure destination. Removing it through a sole-installed-plugin rule,
preference, retention, or failure fallback would weaken an accepted authority
boundary, not merely remove typing. The separate query also makes the material
disclosed to the selected plugin explicit; the question must remain separate
because it is not plugin input.

### Prerequisite discoverability

Current Getting Started and command-reference guidance already says that the
plugin belongs in the same isolated tool environment (or checkout `.venv`),
that SearXNG is operator-managed at `127.0.0.1:8888`, and that `hac local` must
already be running. The command implementation can establish only its selected
entry-point metadata/load/return contract and its later HTTP result. It cannot
truthfully establish general SearXNG lifecycle or health.

The current failure split can identify an unavailable ordinary HAC target as
`ordinary cluster unavailable`; it intentionally cannot expose the details of
an acquisition-boundary failure. More documentation may help an operator
recognize these preconditions, but the observed setup uncertainty does not by
itself show a missing current-documentation fact or justify a new inspection
surface.

### Failure diagnostics

RFC-0078 normalizes missing or duplicate selected entry point, incompatibility,
load/import failure, missing or invalid plugin configuration, acquisition
failure, plugin exception, and invalid returned evidence to the privacy-safe
`external-information-acquisition-failed` code. This broad result costs
diagnostic precision, but avoids revealing provider/configuration/import,
endpoint, query, credential, raw-response, or private-topology details.

Changing the caller-visible acquisition taxonomy would amend an accepted
privacy/error boundary and is RFC-worthy. The supplied evidence does not show
that a safe differentiated taxonomy has been identified or that its benefit
outweighs its disclosure risk.

### External-service lifecycle

SearXNG installation, startup, stop, upgrade, repair, supervision, and health
management remain operator-owned. They are explicitly out of scope here. HAC
must remain useful with no SearXNG service or acquisition plugin.

## Candidate comparison

| Candidate | Assessment | RFC classification |
| --- | --- | --- |
| A — status quo plus clearer documentation | Current living guidance already covers same-environment installation, fixed service/process prerequisites, exact syntax, and boundaries. Documentation cannot remove repeated command construction; no specific missing fact is evidenced. | No RFC for a factual documentation correction, but no documentation change is justified by this evidence. |
| B — shorter syntax with three explicit values | Could reduce option-name and shell-construction ceremony while retaining explicit plugin, query, and question values. The exact RFC-0078 command contract and durable installed CLI surface make this more than an undocumented spelling change. | RFC-worthy; it must explicitly preserve or amend the accepted caller command contract. |
| C — use one text as query and question by default | May help a common-looking case, but the two values intentionally address different recipients and semantics. The evidence does not show semantic equivalence across repeated use. | RFC-worthy if ever proposed; it would amend RFC-0078's separate query/question boundary. Not justified as this investigation's one question. |
| D — implicit/default plugin selection | Reduces typing by making installation or prior state authorize a disclosure destination. It conflicts with exact per-operation selection. | RFC-worthy and currently incompatible with RFC-0078's authority boundary; not recommended. |
| E — retained plugin preference/configuration | Adds configuration ownership, storage, precedence, zero-plugin and multi-plugin behavior, and retained disclosure policy. | RFC-worthy new configuration domain; premature abstraction here. |
| F — finite availability/readiness inspection | Metadata/load compatibility could answer a narrow pre-request question, but external service health cannot follow from it. The evidence shows setup confusion, not that a new command is smaller than existing documentation or safe diagnostics. | Likely RFC-worthy caller surface; insufficient justification. |
| G — differentiated diagnostics | Could distinguish plugin availability from other acquisition failure, but would alter the deliberate fixed privacy-safe error code. | RFC-worthy amendment to RFC-0078; no safe concrete taxonomy is evidenced. |
| H — HAC-owned SearXNG lifecycle | Outside the 0.6 boundary and contrary to current operator ownership. | Not a candidate for this work; would require future evidence and RFC. |
| I — automatic acquisition from ordinary Chat | Would hide provider invocation or introduce model/heuristic selection and loops. | Out of scope; separate future architectural topic, not command-ceremony work. |

No candidate introduces retained state, fallback, provider ranking, generic
plugin abstraction, configuration framework, service supervision, or automatic
acquisition in this investigation. Candidate B has the smallest apparent
implementation surface and no retained state, but its final design, failure
behavior, and compatibility impact are intentionally undecided.

## Relationship to earlier investigations

This does not duplicate the post-RFC-0064 investigation: that asked whether HAC
could obtain external information at all, while RFC-0064 remains Rejected and
RFC-0077 through RFC-0079 now govern the accepted narrow path. It does not
duplicate the optional-external-integration investigation, which established
the category-specific acquisition-plugin boundary that became RFC-0078. It also
does not duplicate the ordinary daily-use-friction investigation: that work
considered ordinary local/static Chat and Summarize operation, not this optional
external-information caller edge.

This investigation reopens none of their settled questions: no provider
selection, generic framework, URL acquisition, service ownership, or ordinary
Chat fallback is under consideration.

## Outcome

### Outcome C — one bounded RFC-worthy ergonomics question is justified

The observed recurring construction of three explicit values supports exactly
one later architectural question:

> Should RFC-0078 add one alternative, shorter `hac external-information`
> command spelling that still requires one explicit plugin name, one explicit
> acquisition query, and one explicit source-grounded question for every
> operation?

This question would amend or clarify RFC-0078's accepted exact caller command
contract. It does not decide a syntax, alter the three semantic values, make a
plugin implicit, or authorize implementation. A later Draft RFC must determine
whether any concrete spelling preserves the accepted input validation,
per-operation network-authority visibility, error ownership, and compatibility
expectations.

The evidence is sufficient for this narrow question because documentation cannot
remove repeated command syntax, while it is insufficient for the broader
candidate set. It is not evidence that query and question should merge, that a
plugin preference should be retained, or that diagnostics/lifecycle should
expand.

The required progression remains:

```text
investigation
  -> RFC if a durable architectural decision is justified
  -> implementation only after acceptance
```

No implementation is immediately authorized by this investigation.
