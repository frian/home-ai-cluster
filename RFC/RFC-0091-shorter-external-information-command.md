# RFC-0091: Shorter External-Information Command

Status: Draft

Date: 2026-08-29

Author: frian

## Summary

This RFC proposes one additive shorter input spelling for the existing explicit
external-information caller edge:

~~~sh
hac external-information --plugin NAME QUERY QUESTION
~~~

The current fully explicit form remains fully supported and non-deprecated:

~~~sh
hac external-information \
  --plugin NAME \
  --query QUERY \
  --question QUESTION
~~~

The equivalent home-ai-cluster external-information root alias remains
supported as it is today. Both forms require one explicit named plugin, one
acquisition query, and one source-grounded question. They normalize to the same
existing semantic values and operation. This proposal changes only local command
input syntax; it does not authorize implementation in this Draft RFC.

## Problem

The completed 0.6 external-information daily-use-friction investigation found
that repeatedly constructing the three-value command is more ceremonial than
ordinary hac chat. It distinguished that observed syntax work from the
intentional per-operation plugin-selection authority and from the distinct
query/question semantics.

Current documentation correctly explains the plugin environment, SearXNG
ownership, process prerequisites, and full command. Documentation cannot,
however, remove repeated option spelling in a finite command. The smallest
question supported by the investigation is whether two ordinary text inputs can
use positional syntax without hiding the explicitly selected network-disclosure
destination or changing acquisition behavior.

## Goals

- Add exactly one shorter spelling with --plugin NAME visibly named.
- Require exactly one explicit plugin, one query, and one question for every
  operation.
- Retain the current full option form as an equal, non-deprecated alternative.
- Normalize equal accepted inputs to the existing plugin_name, query, and
  question values and the same downstream operation.
- Preserve RFC-0077, RFC-0078, RFC-0079, and RFC-0090 authority, privacy,
  request, routing, provider, and lifecycle boundaries.
- Keep the change to a finite local parser decision without retained state,
  configuration, or automatic acquisition.

## Non-goals

This RFC does not:

- merge, derive, rewrite, or fall back between query and question values;
- make plugin selection positional, optional, implicit, defaulted, retained, or
  selected from installed plugins;
- add a configuration file, configuration location/discovery, plugin
  preference, default, retained choice, or CLI/config precedence;
- add a capability, endpoint, request model, provider contract, plugin contract,
  network destination, dependency, executable, wrapper, alias, or CLI framework;
- change timeout, output, exit status, acquisition failures, ordinary request
  failures, evidence validation, routing, runtime, history, or persistence;
- install, configure, start, stop, supervise, repair, inspect credentials for,
  or manage health of SearXNG or another provider service; or
- add automatic external-information fallback from ordinary Chat, model-selected
  acquisition, sole-installed-plugin selection, provider ranking/fallback,
  repeated acquisition, research loops, or keyword heuristics.

## Proposal

### Two equal input forms

After a later implementation, hac external-information and
home-ai-cluster external-information will each accept exactly either:

~~~sh
--plugin NAME --query QUERY --question QUESTION
~~~

or:

~~~sh
--plugin NAME QUERY QUESTION
~~~

For example, the following are equal:

~~~sh
hac external-information \
  --plugin searxng \
  --query "Python 3.14 free threading" \
  --question "What changed in Python 3.14 free-threaded mode?"

hac external-information \
  --plugin searxng \
  "Python 3.14 free threading" \
  "What changed in Python 3.14 free-threaded mode?"
~~~

The first positional value is QUERY; the second is QUESTION. Ordinary shell
quoting is required when either contains spaces. Unquoted words are separate
arguments and are not joined by HAC.

The existing full option form remains first-class: fully supported, documented
after implementation, behaviorally equal, and suitable for scripts and
generated commands. No deprecation, warning, migration schedule, automatic
rewriting, or legacy terminology is introduced.

### Named plugin selection

--plugin NAME remains named and explicit in both forms. RFC-0078 makes exact
plugin selection a per-operation operator authority and network-disclosure
decision, rather than another user-text payload. Keeping it named preserves the
visibility of that choice, keeps provider/plugin selection visually distinct
from query and question text, and keeps installation distinct from
authorization.

This RFC deliberately does not select:

~~~sh
hac external-information NAME QUERY QUESTION
~~~

Treating NAME as simply the first positional payload would obscure its
materially different trust role. Keeping --plugin also neither creates nor
pre-empts a later configuration decision.

### Query and question remain separate

The two text values are still separately supplied on every operation. QUERY is
the exact acquisition input passed to the explicitly selected plugin. QUESTION
is the later RFC-0077 source-grounded operator question and is not passed to the
plugin. The short form does not use one value for both, derive one from the
other, generate a query, or introduce query/question fallback.

### Exact input-form rules

Both forms normalize to the same existing semantic values:

~~~text
plugin_name
query
question
~~~

The two styles cannot be mixed. Valid examples are:

~~~sh
hac external-information \
  --plugin searxng \
  --query "bounded search" \
  --question "What do the sources say?"

hac external-information \
  --plugin searxng \
  "bounded search" \
  "What do the sources say?"
~~~

The following are invalid, with no precedence between forms:

~~~sh
hac external-information \
  --plugin searxng \
  "bounded search" \
  --question "What do the sources say?"

hac external-information \
  --plugin searxng \
  --query "bounded search" \
  "What do the sources say?"
~~~

The existing local invalid-request boundary applies before plugin discovery or
network work. It rejects:

- missing or repeated --plugin;
- blank or oversized plugin names;
- missing one or both text values;
- only one positional text value;
- more than two positional text values;
- positional query/question combined with either --query or --question;
- repeated --query or repeated --question;
- blank or oversized QUERY values under RFC-0078;
- invalid output-option combinations;
- invalid timeout syntax or value; and
- unknown arguments.

This RFC defines no variable-length positional grammar and no argument joining.
It does not move RFC-0077 QUESTION semantic validation into this local boundary.

### Preserved question-validation ordering

Both accepted spellings retain the existing RFC-0078 ordering:

~~~text
explicit QUESTION value
  -> selected plugin acquisition using QUERY only
  -> candidate-source reconstruction
  -> SourceGroundedChatRequest construction
  -> RFC-0077 QUESTION and evidence validation
~~~

The parser still requires the applicable question input source, but does not
newly validate RFC-0077 question semantics before plugin discovery. A blank or
oversized QUESTION is currently validated when the existing
SourceGroundedChatRequest is constructed after acquisition, and its failure
retains the existing acquisition-failure ownership. The short form must not
make that validation earlier or later than the retained full form.

### Normalization and unchanged behavior

For semantically equal inputs, both forms normalize to exactly the same existing
operation: exact selected-plugin validation, one selected plugin invocation
using QUERY only, candidate-source reconstruction, existing
SourceGroundedChatRequest construction and complete RFC-0077 QUESTION/evidence
validation, and the existing source-grounded request to the fixed ordinary HAC
loopback destination. Ordinary capability=chat routing then applies unchanged.

The existing timeout, content/verbose/JSON output, exit statuses, privacy-safe
external-information-acquisition-failed failure, ordinary request failures,
zero-plugin behavior, lazy loading, plugin/provider ownership, runtime,
routing, request history, and external-service lifecycle ownership remain
unchanged. The shorter spelling exposes no plugin import or provider error,
credential, configuration detail, endpoint, raw response, query, or private
topology.

### Future configuration remains separate

This RFC adds no configuration file, location, discovery, preference, default,
precedence rule, or retained operator choice. Under this proposal every
external-information operation still contains --plugin NAME.

A possible later canonical-configuration investigation may separately consider
whether an explicitly retained operator plugin choice is justified. It would be
a separate architectural decision and would need explicitly to amend RFC-0078's
per-operation selection rule if accepted. This RFC neither decides nor prevents
that future question.

## Rationale

The investigation supplies narrow evidence of repeated command-construction
ceremony; it does not support changing the three semantic values or their
authority boundaries. Two positional text values remove repeated option syntax
while leaving the explicit network-disclosure choice named and visible.

RFC-0053 is a design precedent for an additive positional spelling that retains
the explicit form and normalizes both to one internal request path. RFC-0086
applies the same bounded reasoning to independently accepted Code caller
surfaces. Neither RFC automatically authorizes this different command contract;
RFC-0078's exact external-information form requires its own visible amendment.

Retaining the original form avoids breaking scripts and operator muscle memory.
One additive parser spelling is smaller than configuration, defaults, aliases,
wrappers, or lifecycle machinery. It remains local-first and privacy-first
because it adds no acquisition destination, data retention, or hidden authority;
it remains engine-independent and capability-centered because it changes no
request, capability, or routing behavior.

## Alternatives considered

### Keep the current command unchanged

Rejected. It preserves every current boundary but leaves the observed repeated
syntax ceremony unaddressed.

### Make all three values positional

Rejected as the proposal. hac external-information NAME QUERY QUESTION would
treat the explicit plugin-selection and network-disclosure decision as ordinary
positional payload, making its distinct authority role less visible.

### Make query positional but retain --question

Rejected. It reduces less ceremony without a corresponding authority benefit;
the two text values have the same input-status even though their downstream
recipients differ.

### Make question positional but retain --query

Rejected for the same reason. It creates an arbitrary asymmetric grammar.

### Merge query and question into one value

Rejected. RFC-0078 deliberately separates plugin acquisition input from the
later RFC-0077 question. Similar wording in some requests is not semantic
equivalence.

### Use an implicit, default, or sole-installed plugin

Rejected. Installation is not authorization. Implicit selection would weaken
RFC-0078's per-operation network-authority boundary.

### Retain a preferred plugin through configuration

Deferred. It may be a future question if evidence supports a retained
operator-owned choice, but it requires configuration ownership and precedence
decisions outside this RFC.

### Add a second wrapper or alias command

Rejected. It adds command discovery, documentation, and compatibility surface
where one parser's additive spelling is sufficient.

## Trade-offs

The shorter form removes repeated option names but requires normal shell quoting
for multi-word values. Rejecting one or surplus positional values and mixed
forms is intentionally stricter than inferring intent; it preserves explicit
argument boundaries and avoids a hidden precedence rule.

The existing explicit form remains available where named values are clearer or
are generated by scripts. Keeping --plugin named retains visible authority at
the cost of retaining one option spelling, a deliberate trade-off for trust.

## Impact and implementation boundary

This Draft RFC proposes an amendment only to RFC-0078's caller input form. It
preserves RFC-0077's source-grounded request/evidence boundary, RFC-0079's
optional operator-owned SearXNG plugin and service boundary, and RFC-0090's
fixed ordinary HAC loopback destination.

If accepted, a later separate implementation may only add exactly two
positional parser inputs in the existing external-information command parser,
normalize either allowed form to existing command-input values, add focused
parser/command tests, and update current user-facing examples and command
reference.

That implementation must not add a dependency, CLI framework, second parser,
wrapper executable, new command, request-model change, provider/plugin change,
configuration, persistence, routing change, endpoint change, or service
lifecycle change.

## Later implementation proof expectations

A later implementation must demonstrate:

1. the existing full option form still succeeds;
2. the proposed short form succeeds;
3. equal inputs produce identical normalized plugin selection, acquisition
   query, and source-grounded request;
4. both root executable names preserve that behavior;
5. --plugin remains required exactly once;
6. malformed, mixed, missing, repeated-option, and unknown parser-level input
   forms fail before plugin discovery or network work;
7. invalid plugin and QUERY values retain their current local failure behavior;
8. one positional value and more than two positional values fail before plugin
   discovery;
9. equal valid QUESTION values from both forms reach the same downstream
   reconstruction path;
10. an RFC-0077-invalid QUESTION in either form retains the existing
    validation point, plugin-invocation behavior, failure code, stdout, stderr,
    and exit status;
11. output modes and timeout behavior remain unchanged;
12. acquisition failures remain unchanged;
13. no plugin is selected implicitly; and
14. focused fake-entry-point and request-capture tests suffice, without a live
    provider, SearXNG instance, runtime, model, or network proof.

## Open questions

None within this narrow proposal. Review should decide whether this one
additive spelling adequately improves the demonstrated ceremony while retaining
the named per-operation authority boundary.

## Decision

Pending.
