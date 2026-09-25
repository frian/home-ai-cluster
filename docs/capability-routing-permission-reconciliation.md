# Capability Routing-Permission Reconciliation

Status: Current clarification

## Purpose

This record reconciles already accepted capability semantics in RFC-0058,
RFC-0059, RFC-0066, RFC-0067, and RFC-0108. It introduces no capability,
routing rule, preference mechanism, model-selection behavior, configuration
surface, authority, or implementation. It neither supersedes nor reinterprets
those RFCs.

The clarification is necessary because a declaration's omission must not be
read as a claim that a model, adapter, or runtime is physically incapable of
the corresponding work.

## Three related layers

The accepted architecture separates three related, non-identical layers:

```text
capability semantic meaning
    -> project-owned closed semantic requirement

adapter/composition execution support
    -> what the concrete execution composition can truthfully execute

static capability declaration
    -> operator-owned routing permission / eligibility claim
```

RFC-0066 owns the closed semantic meaning and requires explicit caller
requirements plus boolean hard eligibility. RFC-0108 makes local binding
capabilities a truthful explicit subset of a concrete adapter instance's
execution capabilities. RFC-0058 and RFC-0059 define static declarations at
the caller-side routing boundary. The layers constrain one another, but a
routing declaration is not an exhaustive runtime inventory.

## Static remote and caller-local ownership

RFC-0058 defines a declared remote capability set as the capabilities the
caller is allowed to route to that explicitly declared remote node. The set is
static, operator-owned, caller-side routing data. It is not runtime probing,
runtime-discovered truth, health or reachability data, or a guarantee that a
remote application, adapter, or runtime implements every mechanically possible
operation.

RFC-0059 applies the same ownership distinction to the caller-local candidate.
`local_capabilities` changes the caller-visible local routing candidate; it
does not change the local adapter implementation, runtime configuration,
health, endpoint registration, or receiver composition. Adapter implementation
capability and caller routing permission therefore answer different questions.

## Admission and execution truth

RFC-0066 requires every capability name to be a closed, project-defined
semantic requirement. Membership is hard boolean eligibility, not a quality
label, ranking, or comparative preference. Positive declarations must remain
execution-truthful: a composition must be able to accept the normalized
operation without the declaration promising unavailable tools, authority,
output guarantees, or behavior.

That truthfulness requirement does not impose a completeness rule. Static
declarations remain operator-owned routing facts or claims; they need not list
every operation that an underlying composition could mechanically perform.
Neither RFC-0066 nor the earlier static-declaration RFCs authorize discovery,
model inspection, runtime probing, or capability inference to fill such an
omission.

## Code example

RFC-0067 provides a concrete example:

```text
general-purpose composition
  routing declaration: chat

coding composition
  routing declaration: code
```

The general-purpose composition may mechanically produce programming text. The
caller nevertheless need not admit it into the `code` routing domain. A Code
request considers only candidates explicitly admitted for `code`; this does
not assert that the general-purpose composition is physically incapable of
Code. It states only that the caller has not declared or allowed that candidate
for Code routing.

HAC does not infer `code` from model identity and does not inspect whether a
model is a coding model. Model and runtime identity remain adapter/process-local
rather than request-routing data. The [explicit Ollama model selection
investigation](explicit-ollama-model-selection-investigation.md) illustrates
this accepted separation but is not architectural authority.

## Truthful routing explanation

The cluster-facing explanation remains limited to the declaration-backed
eligibility facts:

```text
request required code
node-a did not declare code
node-b declared code
node-b was eligible
```

It must not be strengthened to `node-a cannot do code`. A static routing
declaration does not establish universal physical inability.

## Exclusion is not preference

```text
node-a not declared for code
    -> hard routing exclusion

node-a and node-b both declared for code,
but operator wants node-b first
    -> a different question
```

Capability membership filters hard eligibility; it does not rank otherwise
eligible candidates. Existing accepted ordering semantics remain authoritative.
This clarification introduces no preference mechanism, scoring, weights, or
fourth concept.

## Authority and operation

This clarification does not change the accepted separation between routed
capability requirements, caller-local authorities such as workspace access, and
higher-level operator workflows that may compose requests and authorities. It
does not introduce `operation` as a HAC primitive.

## Practical takeaway

Mechanical ability to perform a task does not require a caller to allow routing
that task to the composition. Omitted capability data does not imply physical
inability. A declared accepted capability means that the candidate may enter
the hard routing-eligibility set for that semantic requirement, subject to the
other accepted execution and routing constraints.
