# Positional Chat Message Investigation

Status: Complete

## Question

What is the smallest compatible change, if the project later chooses to make
the ordinary one-shot chat command less repetitive, so that an operator can
write:

```sh
hac chat "Hello"
```

instead of:

```sh
hac chat --message "Hello"
```

This is an investigation only. It neither changes the accepted command
contract nor authorizes an implementation. In particular, RFC-0045 currently
requires `--message` and explicitly rejects positional prompt input. A later
decision therefore needs an RFC amendment or successor before code changes.

## Scope and sources

This investigation reads the project foundations and the accepted contracts
that govern this boundary: RFC-0045 (one-shot ordinary request), RFC-0049
(chat output modes), RFC-0050 (unified root command), and RFC-0052 (the `hac`
alias). It also examines `chat_command.py`, `command.py`, their focused tests,
and the current README example.

The concern is only one alternate spelling for the same one-shot user message.
It does not select an executable name as part of parsing: `hac` is an installed
alias for `home-ai-cluster`, and both call the same root `main()` function.

## Current contract

### Command path and parsing

The standalone installed command `home-ai-cluster-chat` calls
`home_ai_cluster.commands.chat_command:main`. The unified root command recognises the
exact `chat` subcommand and passes every remaining argument unchanged to that
same function. Thus both of these reach the identical chat parser:

```sh
home-ai-cluster chat --message "Hello"
hac chat --message "Hello"
```

`home-ai-cluster` and `hac` are separate installed executable names, but RFC-0052
requires both to invoke `home_ai_cluster.command:main`. Neither the root nor
the alias parses chat options, rewrites arguments, wraps output, or translates
the chat command's exit. A positional-message decision must therefore be
independent of executable name and be made in the one chat parser.

`_parse_input()` currently uses a private `argparse.ArgumentParser` subclass.
It defines `--message` with `action="append"` and `required=True`, plus a
mutually exclusive `-v`/`--verbose` and `--json` output group. Its `error()`
method raises `_InvalidRequestInput`, rather than allowing argparse to print
usage or error text. Validation then requires `len(args.message) == 1` and a
value whose `strip()` is non-empty. The original, non-blank value is retained
unchanged for the native request.

`append` makes repeated occurrences observable instead of silently taking the
first or last. The explicit length check is why exactly one occurrence is
required: repeated `--message` is invalid, rather than a multi-message input.

### Observed behavior

| Invocation shape | Current result |
| --- | --- |
| No message | No request; stdout empty; `error: invalid request input` on stderr; exit 2. |
| One non-blank `--message` | One native `POST` request with one preserved `user` message and fixed `chat` capability. |
| Blank or whitespace-only `--message` | Same local invalid-input result, before client construction. |
| Repeated `--message` | Same local invalid-input result, before client construction. |
| Unknown chat argument | Same local invalid-input result, before client construction. |
| `chat --help` | argparse help on stdout, empty stderr, exit 0, and no request. Through either root executable it retains the standalone usage identity, `home-ai-cluster-chat`. |
| `chat --version` | Chat defines no version option, so it is invalid local input: empty stdout, stable stderr line, exit 2, no request. |
| Root `--version` | Only `home-ai-cluster --version` or `hac --version` is root-owned: package version to stdout, empty stderr, exit 0. |
| `-v` or `--verbose` with valid input | One request; stdout contains content plus execution attribution; stderr empty; exit 0. |
| `--json` with valid input | One request; stdout contains the compact validated `ClusterResult` JSON; stderr empty; exit 0. |
| Both verbose and JSON | Invalid local input, exit 2, before a request. |

For valid input, the chat command owns request construction, HTTP exchange,
response validation, success presentation, and safe failure mapping. Success
stdout is owned by its selected mode: content by default, human-readable
content plus node/adapter/optional-model attribution for verbose, or compact
historical JSON for `--json`. On local invalid input and every request or
response failure, it keeps stdout empty, writes exactly one prompt-free error
category to stderr, and exits 2 for invalid input or 1 otherwise. The root
owns only its own static help, version, and unknown-subcommand behavior; after
delegation it preserves chat-owned stdout, stderr, and exit status unchanged.

The README currently illustrates the standalone form:

```sh
uv run home-ai-cluster-chat --message "Hello"
```

It is intentionally not changed by this investigation.

## Candidate command shapes

### Option A — retain `--message` only

```sh
hac chat --message "Hello"
```

This is the current accepted, explicit contract. It is clear about which value
is message content, works predictably in scripts, and has no compatibility or
parser change. Its cost is repeated-use friction for the ordinary one-value
case. It remains the lowest-risk option if that friction is not sufficient to
justify changing a durable input boundary.

### Option B — add one positional message and retain `--message`

```sh
hac chat "Hello"
hac chat --message "Hello"
```

This is the likely smallest *candidate* if the reported ergonomic need merits
an accepted change. It retains existing scripts and documentation as working
forms while allowing the short ordinary invocation. The forms should be
mutually exclusive: accepting both would create unnecessary precedence and
could accidentally submit the wrong content. A later contract should reject
both forms with the existing invalid-input category and exit 2.

One optional positional does not conflict with `-v`, `--verbose`, or `--json`:
argparse recognises those options independently, and normal shell quoting makes
`"Hello, world"` one positional value. Unquoted `hac chat Hello world` produces
two positional tokens and should be rejected, not reconstructed. Requiring
normal shell quoting for multi-word content is familiar, preserves exactly one
message boundary, and avoids declaring a variable-length trailing prompt
grammar. The input can normalize to the same one internal `message` string,
then use the unchanged native-request path.

### Option C — replace `--message` with a positional message

```sh
hac chat "Hello"
```

This is concise but breaks the accepted RFC-0045 form and existing scripts,
examples, and automation. It would require a migration path and likely a
deprecation period if it were ever justified. The concrete need is less typing
for ordinary interactive use, not removal of a clear scripting form; no
evidence supports that compatibility cost. It should not be selected merely
because the positional spelling is shorter.

### Option D — optional positional input plus stdin or interaction

```sh
echo "Hello" | hac chat
hac chat
```

This is outside the narrow decision. It creates input-source precedence,
blocking and TTY semantics, empty-stream behavior, and potentially session or
REPL expectations. It does not follow from accepting one positional value and
must not be designed as part of this investigation.

## Parsing assessment for Option B

The boring `argparse` shape is one optional positional, not `nargs="+"` or
`nargs="*"`, alongside the retained append-based option:

```python
parser.add_argument("message_positional", nargs="?")
parser.add_argument("--message", action="append")
```

After parsing, the command would count supplied sources. It would require
exactly one source and exactly one non-blank normalized value:

1. absent positional and absent option: invalid input;
2. one non-blank positional and no option: valid;
3. exactly one non-blank `--message` and no positional: valid;
4. both sources, repeated option values, blank value, or more than one
   positional token: invalid input.

An optional positional naturally rejects a second positional token through the
existing parser-error conversion. `nargs="+"` or `"*"` would instead make a
multi-token message an intentional grammar and require joining rules. Joining
arbitrary trailing tokens loses the shell's argument boundary (including how
whitespace was supplied) and makes future options harder to reason about. It
is not needed for quoted multi-word messages.

The existing mutually exclusive output group can remain unchanged. Both a
positional message and `--message` are present after `parse_args()`, so source
conflict detection is explicit and does not require a wrapper or second parser.
Once one value is selected, the existing `strip()` test can validate it while
the original value continues unchanged into `_native_request()`. The existing
`_InvalidRequestInput` boundary and its exit code 2 are sufficient for every
new local invalid form; no new error taxonomy is needed.

## Compatibility assessment

If a later RFC accepts Option B, the smallest safe contract is:

> Add one positional message form while retaining `--message` as a fully
> supported compatibility form.

`--message` should remain documented as an equal alternative, not
compatibility-only. It remains clearer in scripts and carries no demonstrated
reason for deprecation. Both accepted forms must build identical native request
bodies for equal message text and preserve the one-shot request count, fixed
capability, target, timeout, safe failure mapping, output modes, privacy,
routing, topology, transport, runtime, fallback, and lifecycle behavior.

This is nevertheless a public command-contract change. RFC-0045's explicit
prohibition on positional input cannot be bypassed as a small parser detail.
The future decision should state the two forms, exclusivity, invalid cases, and
continued no-stdin/no-session boundary before implementation.

## Explicit exclusions

This investigation excludes interactive or multi-turn chat, REPL behavior,
prompt history, conversation state, automatic stdin reading, file input,
multiple user messages, system-message options, model/node/capability
selection, new output modes, shell completion, parser libraries or CLI
frameworks, and changes to the cluster API.

It also excludes routing, topology, transport, runtime, fallback, privacy,
persistence, and lifecycle changes, along with a new roadmap phase or Phase
19. It does not modify the README, accepted RFCs, packaging, code, tests,
dependencies, or lockfile.

## Focused proof for a later implementation

A later accepted implementation should add focused command-boundary tests, not
a duplicate end-to-end suite:

1. positional message success and retained `--message` success;
2. identical normalized native request bodies for equal positional and option
   values;
3. rejection, without client construction, for both forms together, missing
   input, blank positional input, repeated option input, surplus positional
   tokens, unknown arguments, and conflicting output flags;
4. unchanged content, verbose, and JSON success presentation for positional
   input, with the existing output-mode tests retained for the option form;
5. unchanged safe stdout, stderr, and exit behavior for local failures; and
6. forwarding equivalence through `home-ai-cluster chat` and `hac chat` as
   well as the standalone parser seam where appropriate.

Request capture with an `httpx.MockTransport` or the existing narrow posting
seam is enough to prove normalization and forwarding. No live runtime, network,
model, or two-machine setup is required for this input-boundary change.

## Recommendation

Do not implement from this document. If operators confirm that the repeated
one-shot use case justifies a contract change, draft a focused RFC amendment or
successor for Option B. Keep its decision limited to one optional positional
message, fully retained `--message`, mutual exclusion, existing invalid-input
handling, and an otherwise unchanged command boundary.
