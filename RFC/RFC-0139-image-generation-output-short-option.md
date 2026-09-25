# RFC-0139: Image Generation Output Short Option

Status: Accepted

Date: 2026-09-25

Author: frian

## Summary

This RFC proposes one additive spelling for the existing Image Generation
caller-local output destination:

```text
-o FILE == --output FILE
```

It applies to `hac image-generation`, `home-ai-cluster image-generation`, and
any existing shared parser entry path that exposes the same command parser.
Both spellings bind to the same parser destination and have exactly the same
semantics. `--output` remains supported, canonical, and non-deprecated.

## Problem

Ordinary Image Generation use has exposed small repeated typing friction:

```sh
hac image-generation --output /tmp/image.png "..."
```

The conventional shorter equivalent is useful in this concrete repeated
workflow, without changing the output authority or behavior:

```sh
hac image-generation -o /tmp/image.png "..."
```

## Goals

- Add exactly `-o FILE` as an equal spelling of existing `--output FILE` for
  Image Generation.
- Preserve RFC-0136's output-file authority and semantics without modification.
- Preserve RFC-0137's JPEG export behavior, including its output requirement.
- Keep the existing long form explicit, compatible, and canonical.

## Non-goals

This RFC does not establish a generic short-option registry, automatic
abbreviation, a rule that every long option needs a short alias, global `-o`,
`-o` on another command, a generic output abstraction, output-format option,
overwrite support, automatic filenames, or new filesystem authority.

It changes no Image Generation request or result, browser behavior, runtime,
adapter, routing, remote, receiver, configuration, persistence, fallback, or
retry behavior. It does not add `--timeout` or `-t`; the existing
`--timeout-seconds` vocabulary remains unchanged.

## Proposal

### Exact mapping

The Image Generation parser accepts exactly:

```text
-o FILE == --output FILE
```

for both ordinary root names and every existing shared parser entry path that
naturally exposes this parser. The two option strings are one argparse action
with one destination; they are not separate inputs later reconciled by command
logic.

### Preserved output behavior

`-o FILE` inherits every RFC-0136 rule exactly. The destination remains
caller-local. HAC creates only the selected missing leaf; its parent must
already exist; and HAC never overwrites an existing filesystem object. It
creates the destination only after it has received a complete successful
validated result. Without JPEG export, it writes the exact validated PNG bytes.

The path remains invisible to the request, routing, runtime, and remote
execution. Existing failures, retry behavior, fallback behavior, and the rule
against rollback deletion after a post-creation write or close failure remain
unchanged. The alias changes accepted CLI spelling only.

### JPEG interaction

RFC-0137's existing form:

```sh
hac image-generation --output FILE --jpeg "..."
```

has the equal form:

```sh
hac image-generation -o FILE --jpeg "..."
```

`--jpeg` continues to require an output destination; supplying it through
`-o` satisfies precisely the same requirement as `--output`. JPEG semantics,
encoding, format selection, suffix behavior, and normalized-PNG architecture
do not change.

### Equal spellings and canonical long form

Following RFC-0092's additive-alias principle, mixed or repeated spellings
receive no special duplicate-option, precedence, or validation rule. Existing
parser behavior remains authoritative whenever this option is supplied more
than once or through both spellings.

`--output` remains supported, canonical in architectural prose where clarity
matters, and non-deprecated. There is no warning, migration, removal schedule,
or preference requirement for existing scripts.

### Timeout non-change

This RFC does not reopen RFC-0092's decision not to assign `-t`: `--text` and
`--timeout-seconds` are distinct ordinary concepts. It adds neither `-t` nor
`--timeout`; `--timeout-seconds` remains the accepted public timeout spelling
under RFC-0060.

## Relationship to RFC-0092

RFC-0092 deliberately adopted a finite initial short-option vocabulary, but it
did not create a permanent rule that later options could never receive a
justified short form. This RFC records one later, evidence-backed alias from
the repeated Image Generation output workflow; it creates no generic alias
policy.

## Relationship to RFC-0136

RFC-0136 remains the owner of output-file authority and semantics. This RFC
amends only the accepted spelling of that caller option:

```text
-o FILE
    |
    +-- exact CLI alias only
    |
--output FILE
    |
    +-- unchanged RFC-0136 semantics
```

## Alternatives considered

### Keep `--output` only

This is valid, but leaves the concrete repeated typing friction observed during
ordinary Image Generation testing unresolved.

### Rename `--output` to `-o`

Rejected. The long form is accepted, clear, documented, and must remain
compatible.

### Add a general short-option policy

Rejected as premature abstraction. The demonstrated need is one bounded alias,
not a new CLI framework.

### Add `-t` or `--timeout` at the same time

Rejected and deferred. It is unrelated to demonstrated output friction and
would reopen RFC-0092's explicitly considered vocabulary decision and
RFC-0060's accepted public timeout spelling.

## Implementation boundary

After acceptance, one separate focused implementation PR may add `"-o"` to the
existing Image Generation `--output` argparse action, add focused parser/help/
equality tests, and update current user-facing command documentation and
examples. It must preserve all existing behavior and must not authorize
unrelated CLI cleanup.

No implementation, tests, or user-facing command documentation change belongs
in this RFC PR.

## Decision

Home AI Cluster accepts exactly `-o FILE` as an additive,
equal alias of Image Generation `--output FILE`. The long form remains
supported, canonical, and non-deprecated. RFC-0136 and RFC-0137 semantics,
including caller-local output authority and JPEG's output requirement, remain
unchanged.
