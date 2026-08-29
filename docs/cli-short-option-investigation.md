# CLI Short-Option Investigation

Status: Investigation

Date: 2026-08-29

## Scope and motivating observation

This bounded investigation audits the current ordinary `hac` / `home-ai-cluster`
root surface for additive short aliases that remove recurring typing ceremony
without creating a second command language or hiding an operator boundary. It
does not decide, implement, document, or deprecate CLI behavior. Frequency is
qualitative, based only on current workflows, examples, retained evidence, and
the command contracts; no telemetry is claimed.

The audit covers all thirteen root commands and both root spellings. Historical
proof-only commands are excluded unless they share an ordinary parser. The root
dispatches to the same parser used by a standalone script for `local`,
`static-cluster`, `compatibility`, `chat`, `preflight`, `health`, and `status`.
Any later alias belongs to that shared parser contract, not to one entry point.

## Current ordinary CLI surface

`hac` and `home-ai-cluster` dispatch: `local`, `static-cluster`,
`compatibility`, `aider`, `external-information`, `chat`, `code`, `code-file`,
`summarize`, `classify`, `preflight`, `health`, and `status`.

Every subcommand is argparse-backed and therefore currently has automatic
`-h` / `--help`. The root dispatcher is custom: `hac --help` and
`home-ai-cluster --help` print root help and exit 0, while `hac -h` and
`home-ai-cluster -h` report `error: unknown command` and exit 2. Root
`--version` works; it has no short form.

Existing non-help aliases are exactly `-v` / `--verbose` on `chat`, `code`,
`external-information`, `summarize`, and `classify`. In each case it is a
boolean output mode mutually exclusive with `--json`; this is an existing good
consistent alias to preserve.

## Complete option inventory and assessment

Categories: **A** existing good short alias; **B** strong alias candidate;
**C** possible later alias; **D** keep long-only for clarity; **E** keep
long-only for authority/boundary visibility; **F** collision or ambiguity.
`value` includes a required option value; `flag` takes none; `repeat` records
repeatability. “MX” names a mutually exclusive input/output mode. All rows
also have argparse `-h/--help`, as noted above.

| Command | Long option | Existing short | Form / constraints | Cross-command concept and qualitative use | Final |
| --- | --- | --- | --- | --- | --- |
| local | `--runtime` | — | value | shared local composition; occasional process setup | C |
| local | `--runtime-config` | — | value; MX explicit composition | composition authority; occasional retained setup | E |
| local | `--ollama-model` | — | value | runtime-specific advanced composition | E |
| local | `--ollama-disable-thinking` | — | flag | runtime-specific request-shape choice | E |
| local | `--llama-server-base-url` | — | value | runtime-specific network destination | E |
| local | `--llama-server-model` | — | value | runtime-specific advanced composition | E |
| local | `--host` | — | value | bind/exposure choice; infrequent | E |
| local | `--port` | — | value | conventional server port; occasional explicit bind | B |
| static-cluster | `--declaration` | — | value; MX inline topology | shared retained declaration selection; repeated operator workflow | B |
| static-cluster | `--remote-node-id` | — | value; paired with URL | inline topology identity; rare structural proof/setup | E |
| static-cluster | `--remote-base-url` | — | value; paired with ID | inline topology/network destination; rare structural setup | E |
| static-cluster | `--local-capability` | — | repeat value | inline routing eligibility; rare structural setup | E |
| static-cluster | `--remote-capability` | — | repeat value | inline routing eligibility; rare structural setup | E |
| static-cluster | `--runtime` | — | value | shared local composition; occasional setup | C |
| static-cluster | `--runtime-config` | — | value; MX explicit composition | composition authority | E |
| static-cluster | `--ollama-model` | — | value | runtime-specific advanced composition | E |
| static-cluster | `--ollama-disable-thinking` | — | flag | runtime-specific request-shape choice | E |
| static-cluster | `--llama-server-base-url` | — | value | runtime-specific network destination | E |
| static-cluster | `--llama-server-model` | — | value | runtime-specific advanced composition | E |
| compatibility | `--declaration` | — | value | shared retained declaration selection | B |
| compatibility | `--proof-observation` | — | flag; requires declaration | proof/debug-only control | E |
| aider | `--file` | — | repeat value; exactly one valid target | same selected file concept; ordinary bounded edit | B |
| aider | `--message` | — | repeat-invalid value; MX positional | positional message already removes ceremony | D |
| aider | `--timeout-seconds` | — | value | occasional request tuning | D |
| external-information | `--plugin` | — | repeat-invalid value | named per-operation network authority | E |
| external-information | `--query` | — | repeat-invalid value; MX two positionals | positional QUERY already available | D |
| external-information | `--question` | — | repeat-invalid value; MX two positionals | positional QUESTION already available | D |
| external-information | `--timeout-seconds` | — | value | occasional request tuning | D |
| external-information | `--verbose` | `-v` | flag; MX JSON | shared output detail | A |
| external-information | `--json` | — | flag; MX verbose | shared machine-output mode | B |
| chat | `--message` | — | repeat-invalid value; MX positional | positional message already available | D |
| chat | `--timeout-seconds` | — | value | occasional request tuning | D |
| chat | `--verbose` | `-v` | flag; MX JSON | shared output detail | A |
| chat | `--json` | — | flag; MX verbose | shared machine-output mode | B |
| code | `--message` | — | repeat-invalid value; MX positional | positional message already available | D |
| code | `--timeout-seconds` | — | value | occasional request tuning | D |
| code | `--verbose` | `-v` | flag; MX JSON; invalid no-message interactive use | shared output detail | A |
| code | `--json` | — | flag; MX verbose; invalid no-message interactive use | shared machine-output mode | B |
| code-file | `--file` | — | repeat-invalid value; exactly one target | same selected file concept; ordinary bounded replacement | B |
| code-file | `--message` | — | repeat-invalid value; MX positional | positional message already available | D |
| code-file | `--timeout-seconds` | — | value | occasional request tuning | D |
| summarize | `--text` | — | repeat-invalid value; MX file | explicit source; stdin/file are concise alternatives | D |
| summarize | `--file` | — | repeat-invalid value; MX text | same selected file concept; repeated source use | B |
| summarize | `--timeout-seconds` | — | value | occasional request tuning | D |
| summarize | `--verbose` | `-v` | flag; MX JSON | shared output detail | A |
| summarize | `--json` | — | flag; MX verbose | shared machine-output mode | B |
| classify | `--text` | — | repeat-invalid value; MX file | explicit source; stdin/file alternatives | D |
| classify | `--file` | — | repeat-invalid value; MX text | same selected file concept; repeated source use | B |
| classify | `--label` | — | repeat value; ordered required labels | repeated familiar classification input | B |
| classify | `--timeout-seconds` | — | repeat-invalid value | occasional request tuning | D |
| classify | `--verbose` | `-v` | flag; MX JSON | shared output detail | A |
| classify | `--json` | — | flag; MX verbose | shared machine-output mode | B |
| preflight | `--declaration` | — | value; MX inline topology | shared retained declaration selection | B |
| preflight | `--remote-node-id` | — | value; paired with URL | inline topology identity; rare | E |
| preflight | `--remote-base-url` | — | value; paired with ID | inline topology/network destination; rare | E |
| preflight | `--local-capability` | — | repeat value | inline routing eligibility; rare | E |
| preflight | `--remote-capability` | — | repeat value | inline routing eligibility; rare | E |
| preflight | `--json` | — | flag | shared machine-output mode | B |
| health | `--json` | — | flag | shared machine-output mode | B |
| status | `--declaration` | — | required value | shared retained declaration selection | B |
| status | `--runtime` | — | value | shared local composition; occasional setup | C |
| status | `--runtime-config` | — | value; MX explicit composition | composition authority | E |
| status | `--ollama-model` | — | value | runtime-specific advanced composition | E |
| status | `--ollama-disable-thinking` | — | flag | runtime-specific request-shape choice | E |
| status | `--llama-server-base-url` | — | value | runtime-specific network destination | E |
| status | `--llama-server-model` | — | value | runtime-specific advanced composition | E |
| status | `--json` | — | flag | shared machine-output mode | B |

## Cross-command concepts and candidate registry

| Letter | Proposed concept | Commands | Recommendation |
| --- | --- | --- | --- |
| `-h` | help | root only; already every argparse subcommand | strong: make root behavior consistent in the same bounded policy |
| `-v` | verbose | chat, code, external-information, summarize, classify | preserve existing A contract |
| `-f` | file | aider, code-file, summarize, classify | strong: the same caller-local selected-file concept everywhere it occurs |
| `-d` | declaration | static-cluster, compatibility, preflight, status | strong: the same retained static declaration selection everywhere it occurs |
| `-l` | label | classify | strong: conventional repeated classification input; no competing ordinary meaning |
| `-j` | JSON output | chat, code, external-information, summarize, classify, preflight, health, status | strong: consistent explicit machine-output mode, only where JSON already exists |
| `-p` | port | local | strong: conventional server spelling; reserve it exclusively for port |
| `-r` | runtime | local, static-cluster, status | possible later: coherent but startup-only and retained config reduces repetition |
| `-m` | message | chat, code, code-file, aider | reject: accepted positional forms already solve ordinary typing |
| `-t` | text or timeout | summarize/classify versus request clients | reject: one letter cannot coherently mean both |
| `-p` | plugin | external-information | reject: plugin selection must remain visibly named and would collide with port |
| `-q` | query or question | external-information | reject: two distinct concepts already have accepted positional forms |

`-f`, `-d`, `-l`, and `-j` have direct repeated-use evidence in current
ordinary examples. `-p` is a conventional but less frequent foreground-server
convenience; it is still small and unambiguous if reserved solely for port.
`-r` is coherent, but does not clear the same practical-value bar because the
default and `--runtime-config` commonly avoid repeating it.

## Authority-sensitive options and collisions

Named `--plugin` must remain long-only. RFC-0091 deliberately retains that
per-operation selection because it makes the acquisition/plugin and network
disclosure boundary visible; `-p` must not weaken it. `--host`, inline remote
identity/URL/capability options, runtime configuration, runtime-specific model
and URL choices, and `--proof-observation` likewise remain long-only: they are
rare structural, exposure, lifecycle, or runtime authority decisions and are
normally replaced by retained declarations/configuration.

No recommended alias changes validation, repeatability, mutually exclusive
forms, defaults, output, exit status, request shape, routing, privacy,
lifecycle, or authority. Long forms remain canonical and non-deprecated.

The explicit reservations are material: `-p` is port, never plugin; `-t` is
neither text nor timeout; `-q` is neither query nor question; and `-m` is not
needed beside existing positional messages. No automatic abbreviation, prefix
matching, command renaming, or new syntax family is suggested.

## 0.6 relevance

The proposed set is a concrete, small daily-driver improvement: it shortens
recurring file, declaration, label, and JSON forms while retaining long,
explicit forms for scripts and authority choices. It is worthwhile before 0.6,
but the current long forms, positional conveniences, and existing `-v` do not
fail the 0.6 exit condition. This is not a release blocker.

## Outcome

### Outcome A — one bounded RFC is justified

One bounded RFC should ask:

> Should Home AI Cluster add only the additive aliases `-f/--file` for `aider`,
> `code-file`, `summarize`, and `classify`; `-d/--declaration` for
> `static-cluster`, `compatibility`, `preflight`, and `status`; `-l/--label`
> for `classify`; `-j/--json` for every current JSON-capable ordinary command;
> `-p/--port` for `local`; and root `-h/--help` for both root spellings, while
> retaining all long forms, preserving semantic equivalence, and reserving
> collisions including `-p` for plugin and `-t` for text/timeout?

The RFC should preserve existing `-v/--verbose`, explicitly reject aliases for
message/query/question because positional forms already serve them, and retain
authority-sensitive choices long-only. `-r/--runtime` is deferred. No alias
may be implemented unless that RFC is accepted.

## Next step

If maintainers agree that the bounded set is worthwhile before 0.6, draft one
RFC answering only that question, then implement it separately after acceptance.
Otherwise the 0.6 checkpoint can proceed unchanged; this investigation itself
does not amend it.
