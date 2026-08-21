# Aider single-target fail-closed corrective investigation

Status: Corrective investigation

Date: 2026-08-21

## Scope and accepted contract

This is a documentation-only corrective investigation of the existing
`hac aider --file PATH --message TEXT` caller edge.  It neither implements a
repair nor changes the accepted authority boundary.

RFC-0068 permits one fixed Aider 0.86.2 subprocess to read and edit the
operator-selected target.  RFC-0069 makes that filesystem authority exact: the
caller may accept one operator-supplied target (or create that one missing
empty leaf with an existing parent), but no sibling, parent, inferred,
generated, or additional path.  RFC-0072 changes only the bounded request
count and explicitly retains RFC-0069 filesystem authority.  Aider's normal
OS-level access is not itself a sandbox, so the caller edge must fail closed
when Aider proposes another path.

The classification of the observed confirmation prompt remains the same:
it is an **implementation bug under an accepted authority contract**.  The
question corrected here is only which smallest mechanism can enforce that
contract.

## Historical record and correction

PR #498 correctly established the real-local failure: a whole-file response
could name an unselected path, Aider 0.86.2 prompted the operator, and manual
`N` avoided that particular unauthorized write.  That prompt was already
incompatible with the one-target contract because its default is Yes.

PR #499 made two valid, narrow caller-edge changes:

- it writes private temporary Aider configuration containing
  `yes-always: false`;
- it removes inherited `AIDER_YES_ALWAYS` from the Aider child environment.

The project-level test in `tests/test_aider_command.py` correctly proves those
two launch facts and temporary-material cleanup.  Its injected subprocess does
not parse the configuration with Aider/ConfigArgParse, parse a whole-file
response, enter `allowed_to_edit()`, or write an unselected path.  It therefore
did not prove the claimed enforcement result.

The post-merge real-local observation disproved that result: with PR #499 on
`main`, an unselected existing path still displayed Aider's `Allow edits to
file that has not been added to the chat? (Y)es/(N)o [Yes]:` prompt.  Manual
`N` produced `Skipping edits to ...`.  The child was still interactive and
defaulted to Yes.

## Corrected Aider 0.86.2 and ConfigArgParse 1.7.1 analysis

The installed exact versions were `aider 0.86.2` and `ConfigArgParse 1.7.1`.
The relevant source is the installed package, not a later upstream revision.

1. Aider creates its parser with `YAMLConfigFileParser` and
   `auto_env_var_prefix="AIDER_"` (`aider/args.py:35-42`).
2. It declares `--yes-always` as `action="store_true"` with `default=None`
   (`aider/args.py:760-764`).  Its help exposes `--yes-always`; an attempted
   `--no-yes-always` is rejected as an unrecognised argument.
3. ConfigArgParse converts configuration and environment values into command
   line arguments.  For a non-`BooleanOptionalAction` action that needs no
   value, true-like values append the option, while false-like values append
   nothing (`configargparse.py:1103-1149`, especially 1127-1141).
4. Therefore false-like YAML or environment input does **not** supply a
   false-valued argument to Aider's `store_true` action.  Argparse receives no
   option and retains its declared `None` default.

A tiny model-free parser experiment using that exact ConfigArgParse parser
shape observed:

| Input source | Observed `yes_always` |
| --- | --- |
| omitted | `None` |
| YAML `yes-always: false` | `None` |
| YAML `yes-always: true` | `True` |
| `AIDER_YES_ALWAYS=false` | `None` |
| `AIDER_YES_ALWAYS=true` | `True` |
| CLI `--yes-always` | `True` |

There is consequently no supported config, environment, or CLI spelling in
this exact launch surface that directly produces `args.yes_always is False`.
Removing `AIDER_YES_ALWAYS` in PR #499 prevents a true-like inherited setting
from enabling automatic acceptance, but the private YAML false value leaves
the normal `None` behavior unchanged.

This corrects the counter-intuitive claim in the earlier investigation.  The
following Aider mechanism is real but unreachable through PR #499's YAML:

1. `main.py:551-556` passes `args.yes_always` to `InputOutput`; its
   constructor retains the value as `self.yes` (`io.py:237-308`).
2. `InputOutput.confirm_ask()` defaults to `"y"` and displays `[Yes]`
   (`io.py:807-846`).
3. Only `self.yes is True` chooses automatic Yes and only
   `self.yes is False` chooses automatic No before reading input
   (`io.py:866-869`).
4. Otherwise it calls `input()`; empty input uses the default, and EOF is
   explicitly treated as if Enter were pressed (`io.py:874-900`, especially
   883-891).  A default-Yes confirmation therefore accepts on EOF.

In other words, `self.yes is False` would be deterministic automatic rejection,
but YAML `yes-always: false` does not produce that value.  PR #499's current
configuration is automatic neither Yes nor No: it is interactive default Yes.

## Exact unselected-path flow

The whole-file parser accepts the line immediately before a fenced block as
the filename; it does not require that filename to be among the initially
selected files (`aider/coders/wholefile_coder.py:22-122`).  The actual flow is:

```text
whole-file response naming an unselected path
  -> WholeFileCoder.get_edits()
  -> Coder.apply_updates()
  -> prepare_to_edit()
  -> allowed_to_edit()
  -> InputOutput.confirm_ask()
  -> write only if confirmation accepts
```

`apply_updates()` obtains edits, calls `prepare_to_edit()`, and then applies
the permitted edits (`base_coder.py:2296-2304`).  `prepare_to_edit()` calls
`allowed_to_edit()` for each distinct path (`base_coder.py:2269-2294`).  The
selected path succeeds because it is already in `abs_fnames`
(`base_coder.py:2191-2200`).

For an unselected missing path, `allowed_to_edit()` asks `Create new file?`,
then on acceptance calls `touch_file()`, adds the path to `abs_fnames`, and
permits the edit (`base_coder.py:2206-2224`).  `touch_file()` can create missing
parent directories as well as the file (`aider/utils.py:285-292`).  For an
unselected existing path, it asks `Allow edits to file that has not been added
to the chat?` and permits the edit on acceptance (`base_coder.py:2226-2240`).
The whole-file writer then writes every permitted full-file edit
(`wholefile_coder.py:124-128`).

## Controlled, model-free Aider proof

All experiments used a fresh temporary directory outside the repository, the
installed Aider 0.86.2 executable, a private model-settings file selecting
`whole`, PR #499's `yes-always: false` configuration, and Aider's documented
debug `--apply FILE` mode.  `main.py:1082-1092` reads that controlled response
and calls `coder.apply_updates()` directly, so no model, HAC, network request,
or generated-code execution occurred.  No private path, response content, or
credentials were retained.

Representative launch shape (with temporary placeholder paths) was:

```text
aider --model openai/home-ai-cluster --model-settings-file <temporary-settings> \
  --config <temporary-config> --no-git --no-gitignore --file <selected> \
  --apply <controlled-whole-file-response>
```

| Input control and controlled response | Existing unselected path | Missing unselected path | Selected path |
| --- | --- | --- | --- |
| closed stdin (`< /dev/null`), extra path only | prompt, then changed | prompt, then created and written | unchanged because no selected edit was supplied |
| one finite `N`, two unselected existing paths | first unchanged | not tested in this row | second changed after EOF defaulted Yes |
| continuously open `n\n` input, selected plus both extra paths | unchanged | not created | changed |

The final row used `yes n` only as a disposable test producer; an implementation
must not add that second process.  It establishes the relevant Aider behavior:
every current confirmation consumed a No, without inspecting prompt text or
depending on the order of the existing and missing path prompts.  The selected
edit required no confirmation and still applied.

The finite-input row is important.  Aider can receive any number of
model-named extra-path edits in one whole-file response.  A precomputed finite
number of `N` answers eventually reaches EOF; its next confirmation is then
accepted because Aider treats EOF as default Yes.  Closing stdin is therefore
fail-open, and feeding one `N` is not a boundary enforcement mechanism.

## Candidate mechanisms

| Candidate | Aider 0.86.2 evidence and enforcement | Non-interactive / selected edit | Contract and RFC impact |
| --- | --- | --- | --- |
| YAML/environment/CLI `yes-always: false` | No: false-like ConfigArgParse values leave `None`; no supported negative CLI spelling was found.  It protects neither existing edits nor missing-file creation. | No; prompts remain default Yes. | Not a repair. |
| `--yes-always` or true-like config/environment | Supported, but deterministically accepts confirmations. | Non-interactive, but unsafe. | Opposite of the contract. |
| `--file` and `--read` | Supported initial editable/read-only lists, not an editable-path allowlist.  `--file` is appendable and the unselected-path branches remain reachable. | Does not prevent prompts; selected edit works. | Not a repair. |
| `.aiderignore`, Git ignore, or working-directory placement | Not a general allowlist for this launch.  HAC deliberately uses `--no-git`; `allowed_to_edit()` checks only Git-ignore state before its confirmation branch (`base_coder.py:2202-2240`).  Aider also resolves response paths from its root (`base_coder.py:566-574`). | Does not deterministically cover existing and missing paths while preserving the selected target. | Not a repair; creating workspace policy/containment would expand scope. |
| `--dry-run` | Supported and stops writes, but also stops the selected target write. | Non-interactive; selected edit cannot be delivered. | Unsuitable for the accepted editing edge. |
| finite input or closed stdin | No deterministic protection: one `N` works only until EOF; EOF means default Yes. | Finite input may leave an interactive/default-accepting later prompt. | Not a repair. |
| **Aider-specific continuously open private stdin stream of `n\n` for the child lifetime** | Supported by the observed 0.86.2 `input()`/confirmation mechanism.  The controlled proof rejected both an existing and a missing unselected path while applying the selected edit.  It answers every confirmation No, independent of model obedience or prompt order, and never exposes EOF before the child exits. | Yes.  It does not require a terminal or prompt parsing; an unexpected confirmation is conservatively rejected. | Small caller-edge implementation detail: keep one Aider subprocess and use a parent-owned pipe/writer, not an extra `yes` subprocess or generic framework.  It preserves `whole`, target-content ownership, and the fixed authority boundary. |

The explicit non-solutions remain excluded: HAC parsing/applying edits, reading
target contents, workspace copying/syncing, post-write cleanup, filesystem
sandbox infrastructure, a generic subprocess policy framework, model prompt
obedience, an Aider upgrade or patch, an edit-format change, extra targets, or
a new CLI surface.  None is needed for the credible stdin direction above.

## Outcome and recommended next step

**Outcome A — a straightforward deterministic implementation fix exists within
the accepted Aider 0.86.2 caller edge.  No new RFC appears necessary.**

The smallest credible direction is a narrowly scoped change to the Aider child
launch: replace inherited terminal stdin with a private pipe that remains open
for the complete child lifetime and continuously supplies `n\n`.  It must be
implemented without a second subprocess, must close and join cleanly when the
one Aider child exits, and must retain all existing command, request-count,
privacy, non-Git, no-shell, temporary-material, and timeout boundaries.  It
does not inspect a model response, a target path, or target bytes.  The
existing focused caller-edge tests should then be extended with a regression
proof appropriate to that child-I/O launch behavior, including selected edit,
unselected existing path unchanged, and unselected missing path/parent absent.

This investigation does not authorize that implementation.  A separate normal
bug-fix PR can make and validate it; an RFC is not needed unless the proposed
implementation broadens beyond this Aider-specific child-I/O detail.

## Documentation-only validation

The parser and `--apply` experiments above were model-free and made no HAC or
model request.  No installed Aider file was modified.  Project tests were not
run for this documentation-only change because no source or test behavior was
changed; the relevant historical project test was inspected to state its exact
coverage boundary.  Final repository validation is limited to review of the
documentation-only diff and `git diff --check`.
