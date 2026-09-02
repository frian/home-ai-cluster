# Aider single-target boundary investigation

Status: Investigation

Date: 2026-08-21

> **Corrective follow-up (2026-08-21):** This historical investigation correctly
> identified the unselected-path confirmation as a violation of the accepted
> one-target contract.  Its later claim that YAML `yes-always: false` produces
> `args.yes_always == False` was invalidated by post-merge real-local evidence
> and exact ConfigArgParse 1.7.1 analysis.  In Aider 0.86.2 that YAML false
> value leaves the `store_true` option at its `None` default, so confirmations
> remain interactive and default Yes.  See the [corrective
> investigation](aider-single-target-fail-closed-corrective-investigation.md).
> This follow-up supersedes only the failed `yes-always: false` enforcement
> analysis, not the original contract finding or real-local failure evidence.

## Context / observed real-local behavior

This investigation considers the reported ordinary local invocation of `hac
aider` with one selected existing Python file.  Aider 0.86.2 proposed edits for
that selected file and for an unselected sibling, then displayed:

```text
bonjour.py
Create new file? (Y)es/(N)o [Yes]:
```

The operator answered `N`, so Aider skipped the sibling and edited the selected
file.  No live model call was made for this investigation.  The installed
`aider --version` reports exactly `aider 0.86.2`; the findings below are based
on that locally installed source and its bundled documentation.

The question is not whether the reported refusal prevented this one sibling
from being created.  It is whether the supported caller edge itself constrains
Aider to the one authority granted by the operator.  It currently does not.

## Accepted RFC contract

RFC-0067 grants `code` textual assistance no filesystem authority.  RFC-0068
then creates a deliberately narrow external Aider caller edge: Aider may read
and edit the explicit target, while HAC core remains text-only.  Its fixed
invocation is expressly described as guardrails, not a sandbox
([RFC-0068](../RFC/RFC-0068-one-shot-aider-code-caller-edge.md),
"External Aider and conservative execution").  Its proof expectation is an
Aider-owned selected-target edit with **no other workspace edit**.

RFC-0069 makes the path authority unambiguous.  Only the one
operator-supplied `PATH` is accepted; if absent, the caller edge may create
only that named empty leaf.  It creates no parents, siblings, additional
targets, generated paths, or inferred paths
([RFC-0069](../RFC/RFC-0069-explicit-aider-target-creation.md),
"Explicit target rule" and "Decision").  Aider owning target-content edits
does not grant Aider an open-ended authority to select more targets.

RFC-0072 changes only the maximum Aider/native request count from one to two.
It explicitly retains RFC-0069 filesystem authority, the fixed 0.86.2 version,
and the `whole` edit format
([RFC-0072](../RFC/RFC-0072-bounded-aider-follow-up-request.md),
"Unchanged authority, privacy, timeout, and success boundaries" and
"Relationship to previous RFCs").

The command reference similarly promises "one bounded external Aider edit of
one explicitly selected file."  Its statement that there is no interactive
session is accurate only in the narrower Aider `--message` sense: `--message`
does not enter Aider's chat REPL.  It is not accurate for confirmation prompts;
the current child can stop and await terminal input before creating or editing
an unselected file.

## Current HAC invocation behavior

`_parse_input()` requires exactly one HAC `--file` and one non-blank
`--message` (`src/home_ai_cluster/commands/aider_command.py:60-81`).  It does not turn
that single HAC argument into an Aider path allowlist.

`_aider_argv()` (`src/home_ai_cluster/commands/aider_command.py:294-344`) directly
launches the installed executable with this relevant configuration:

| Current setting | Effect relevant to this investigation |
| --- | --- |
| `--model openai/home-ai-cluster`, `--openai-api-base`, `--openai-api-key` | Selects the private translator/model identity; no file restriction. |
| Temporary `--model-settings-file` containing `edit_format: whole` | Selects Aider's whole-file response parser; it does not limit filenames appearing in a response. |
| `--no-stream`, `--message TEXT` | Makes one non-streaming initial model interaction and exits after it; it does not disable edit confirmations. |
| `--config <temporary empty YAML mapping>` and `--env-file /dev/null` | Avoids ordinary config and `.env` loading, but the empty config sets no confirmation policy.  The subprocess is otherwise launched with inherited environment. |
| `--no-git`, `--no-gitignore`, `--no-auto-commits` | Disables Git behavior; it is not an editable-path allowlist. |
| `--no-auto-lint`, `--no-auto-test`, `--no-watch-files`, `--no-suggest-shell-commands`, `--no-detect-urls`, `--disable-playwright`, `--no-gui` | Disable the listed ancillary behavior; none rejects a model-named file. |
| History/analytics/cache/release/notification flags | Preserve privacy and presentation boundaries; none restricts edit paths. |
| One `--file <target>` | Supplies Aider's initial editable file.  It is not an "only this file may ever be edited" option. |

There is no `--yes-always`, no negative confirmation setting, no Aider
supported filename allowlist argument, and no parent process control of the
child's standard input.  `subprocess.run()` is called without an `env` or
`stdin` argument (`aider_command.py:388-397`), so the confirmation is
intentionally left to the terminal.  This is interactive at the observed
decision point.

## Exact Aider 0.86.2 behavior

The following source locations are from the installed Aider 0.86.2 package
(`aider-chat` tool environment); line numbers identify that version, not a
current upstream release.

1. Aider declares `--file` as an appendable option whose help says it can be
   used multiple times (`aider/args.py:730-734`).  In `aider/main.py:679-680`,
   it combines positional files and `args.file`, resolves them, and passes them
   as `fnames`.  `Coder.__init__` puts those resolved paths into
   `self.abs_fnames` (`aider/coders/base_coder.py:449-476`).  This is the
   initial editable set.
2. With the HAC model setting, `WholeFileCoder.get_edits()` parses the line
   immediately before each fenced block as a filename
   (`aider/coders/wholefile_coder.py:22-122`).  A block labelled `bonjour.py`
   therefore becomes an edit tuple even when `bonjour.py` is absent from the
   initial set.  There is no membership check in this parser.
3. `Coder.apply_updates()` passes every parsed edit through
   `prepare_to_edit()` before writing (`base_coder.py:2269-2304`).  For each
   distinct path, `prepare_to_edit()` calls `allowed_to_edit()`.
4. `allowed_to_edit()` returns immediately only when the resolved path is
   already in `self.abs_fnames` (`base_coder.py:2191-2200`).  An unselected,
   nonexistent path takes the branch at lines 2206-2224: it calls
   `confirm_ask("Create new file?", subject=path)`.  On approval it calls
   `utils.touch_file()`, adds the path to `abs_fnames`, and permits the edit.
   `touch_file()` creates missing parent directories and touches the file
   (`aider/utils.py:285-292`), so the unrestricted Aider behavior is broader
   than just one sibling.  An unselected existing file takes the analogous
   "Allow edits to file that has not been added to the chat?" branch at
   lines 2226-2240.
5. In the whole-file coder, `apply_edits()` then writes the proposed complete
   content to every permitted path (`wholefile_coder.py:124-128`).  Thus Enter
   or default Yes would create `bonjour.py` and then write its model-proposed
   content.  For an existing unselected file, it would write that file after
   the corresponding approval.

`InputOutput.confirm_ask()` has a default of `"y"` and renders `[Yes]`
(`aider/io.py:807-846`).  Empty input is replaced with that default
(`io.py:859-925`), explaining the observed prompt.  In particular, EOF is
also treated as the default at lines 883-887; merely removing interactive input
would fail open, not fail closed.

### Supported configuration assessment

Aider 0.86.2 has no documented `--file`-only or editable-path-allowlist option.
`--read` is a separate read-only input list, not a prohibition on later
model-named edits.  `--no-git`, `--no-gitignore`, and `whole` edit format do
not alter `allowed_to_edit()`.

There is, however, a version-supported general confirmation setting.  Its name
is counter-intuitive, so its exact 0.86.2 semantics matter:

1. `--yes-always` is declared with `action="store_true"` and **default
   `None`** (`aider/args.py:760-764`).  With the current empty HAC config and
   no command-line flag, that leaves the normal interactive confirmation
   behavior in place.
2. Aider's bundled sample YAML config explicitly shows
   `yes-always: false` (`aider/website/docs/config/aider_conf.md:455-456`).
   Under the same option declaration, explicit YAML `false` produces the
   Boolean value `False`; it is not the omitted `None` default.
3. Aider passes `args.yes_always` directly as the second positional argument
   when it constructs `InputOutput` (`aider/main.py:551-556`), and
   `InputOutput.__init__` stores that argument unchanged as `self.yes`
   (`aider/io.py:237-308`).
4. `InputOutput.confirm_ask()` takes the `self.yes is False` branch and sets
   `res = "n"` before any terminal input (`aider/io.py:866-869`); it then
   returns false for that response (`aider/io.py:900-925`).

Therefore `yes-always: false` is not merely "disable automatic yes."  In this
integration it is deterministic **automatic rejection** of confirmation
prompts.  The selected file needs no confirmation because it is already in
`abs_fnames`; every unselected path reaches one of the two confirmation
branches and is rejected.

The bundled options documentation also lists `--yes-always` and
`AIDER_YES_ALWAYS` (`aider/website/docs/config/options.md:710-712`).  A
temporary config alone is not sufficient for a hard guarantee if inherited
`AIDER_YES_ALWAYS` can override it.  A repair using this mechanism must make
the child environment deterministic, at minimum ensuring that setting is false
or absent according to Aider's configuration precedence, and prove that exact
launch shape against 0.86.2.

This is a fail-closed use of Aider's general confirmation mechanism, not a
dedicated path-restriction feature.

## Existing test coverage

The focused caller-edge tests are `tests/test_aider_command.py`; the only other
focused Aider coverage is root-command delegation in `tests/test_command.py`.

They prove useful caller-edge properties: exactly one HAC `--file` input is
accepted (`test_input_requires_exact_file_message...`); explicit-target
creation is narrow; temporary material is cleaned up; the bridge bounds native
requests; and `test_fixed_aider_arguments_include_all_privacy_guardrails`
checks selected fixed Aider arguments.  The latter only checks a subset of the
argv and that its final four items contain one `--file` and one `--message`
(`tests/test_aider_command.py:651-679`).

They do **not** run Aider's whole-file parser or its `allowed_to_edit()` path.
The test subprocesses are injected fakes, and no test presents a response with
an unselected existing or nonexistent filename, observes the confirmation
policy, or verifies that only the selected path can be written.  Consequently,
the tests establish "HAC passes one initial `--file`" but do not establish
"the Aider subprocess cannot edit or create another path."  This is the precise
coverage gap.

## Findings and contract classification

The observed `bonjour.py` prompt is not compatible with the accepted
single-target authority.  The request for approval exposes a new path selected
by model output, rather than by the `hac aider --file` operator input.  The
operator's refusal avoided the unauthorized write in that particular run, but
does not make the integration compliant: confirmation is not an RFC-authorized
path-selection mechanism, and default Enter accepts it.

Classification: **A — a straightforward implementation bug under an existing
accepted decision.**  The RFCs and command documentation consistently make the
path authority explicit.  The implementation mistakes Aider's initial editable
set for an enforcement boundary and leaves Aider's default general
confirmation policy active.  The documentation's phrase "no interactive
session" should be clarified when the bug is fixed, but that wording is not
the source of the authority ambiguity.

## Candidate smallest fixes — not implemented

| Candidate | Aider 0.86.2 support and enforcement | Contract / RFC assessment |
| --- | --- | --- |
| **Set the private temporary Aider config to `yes-always: false`, and launch the child with a deterministic environment that cannot re-enable `AIDER_YES_ALWAYS`.** | Supported configuration.  It automatically answers No to the confirmation paths that guard all unselected files; the initially selected target still passes without a prompt.  It hard-enforces the boundary within Aider's normal whole-file edit pipeline, rather than relying on model obedience or operator input. | Preserves one target, one subprocess, `whole`, non-Git, no-shell, and Aider-owned target edits.  This is the recommended small normal bug-fix direction; it implements the already accepted authority boundary and needs no new RFC.  It should add a focused real-Aider or tightly controlled Aider-level proof for both missing and existing unselected paths. |
| Feed `N` answers through the child process's input. | No dedicated supported target-boundary option.  It might reject the current prompts, but depends on prompt sequencing and terminal/input behavior; EOF is explicitly Yes.  It is therefore brittle and must not be described as a general Aider allowlist. | Does not change architecture, but is not a credible preferred enforcement mechanism.  It would need version-pinned proof and careful handling of every confirmation. |
| Use `--dry-run`. | Supported, but prevents the selected target edit as well as all other writes. | Does not satisfy the supported editing workflow; unsuitable. |
| Copy/redirect the workspace, compare/clean paths afterward, or introduce an OS filesystem sandbox. | Not an Aider 0.86.2 single-target option; comparison/cleanup occurs after authority has already been exceeded. | Conflicts with the accepted no-inspection/no-HAC-apply boundary or adds prohibited infrastructure.  Not a candidate for this edge. |
| Change Aider version, patch Aider, or add a new Aider file-allowlist feature. | No such feature was found in 0.86.2. | Changes the pinned dependency/integration contract and is outside this bug-fix investigation; it would require separate decision work before implementation. |

## RFC impact assessment

The recommended configuration/environment repair does not add a new CLI
surface, filesystem authority, process, model request, editable target,
architecture, or dependency.  It makes the existing fixed subprocess obey the
already accepted one-target authority.  It is appropriate for a normal bug-fix
PR, including focused regression tests and a documentation correction, rather
than RFC work.

Any proposal to allow operator confirmation to expand the editable set, to add
multiple targets, to inspect/apply edits in HAC, or to change the Aider version
or edit representation would instead change accepted boundaries and require
new RFC work.

## Investigation validation

The initial validation failure did not show that the project lacks `httpx`.
`VIRTUAL_ENV` was empty, and the sandbox could not open uv's shared cache:

```text
error: failed to open file `/home/lpa/.cache/uv/sdists-v6/.git`: Read-only file system (os error 30)
```

With `VIRTUAL_ENV` unset for the validation shell and uv allowed to use its
existing cache, the exact dependency check succeeded:

```text
uv run python -c "import sys, httpx; print(sys.executable); print(httpx.__version__)"
# /.../home-ai-cluster/.venv/bin/python3
# 0.28.1
```

`uv run pytest ...` still collected under `/usr/lib/python3.14` and failed to
import `httpx`; that was a `pytest` executable-resolution mismatch, not a
missing project dependency.  Pinning pytest to the verified project
interpreter resolved it.  The following commands passed:

```text
uv run python -m pytest tests/test_aider_command.py tests/test_command.py -q
# 74 passed

uv run python -m pytest -q
# 1257 passed
```

`git diff --check` also passed.  These checks make no model request and do not
modify Aider, source, tests, dependencies, or the pre-existing untracked
`uv.lock`.

## Recommended next step

Open a small bug-fix PR that first adds a failing focused regression proof for
Aider 0.86.2's unselected existing and missing filename paths, then changes
only the private Aider launch configuration/environment to fail closed on those
confirmations.  Verify that the selected target still edits, an unselected
existing file remains unchanged, an unselected missing file and parent remain
absent, and the existing request-count, privacy, non-Git, non-shell, and
temporary-material guarantees remain intact.  No live model invocation is
needed for that proof.

## Explicit non-goals

This investigation does not implement a fix; change tests; amend or create an
RFC; change Aider version, dependencies, CLI, or architecture; contact a model
or external API; execute generated code; inspect or modify the sibling SearXNG
plugin repository; or introduce a sandbox, container, repository abstraction,
agent layer, generic developer-tool framework, or HAC patch application.
