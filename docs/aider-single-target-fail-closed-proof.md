# Aider single-target fail-closed proof

Status: Successful

Date: 2026-08-21

## Purpose

This record retains privacy-safe, model-free evidence for the implemented
single-target enforcement repair.  It follows the historical sequence:

```text
PR #498: observed unselected-path confirmation failure
  -> PR #499: insufficient YAML yes-always repair
  -> PR #500: corrected ConfigArgParse and stdin investigation
  -> this proof: implemented private continuous-No child input
```

It implements the already accepted RFC-0068/RFC-0069/RFC-0072 authority: only
the one operator-selected Aider target is editable.  It does not add an RFC,
new command, dependency, model request, HAC request, or generated-code
execution.

## Implemented mechanism

The fixed Aider caller edge starts exactly one Aider subprocess with a private
parent-owned pipe as stdin.  A dedicated non-daemon Python thread owns only the
pipe's write end and continuously writes `n\n` while the child is running.  The
parent keeps the read end open for the complete child lifetime, closes it after
the child returns or raises, and joins the writer.  When that final read end is
closed, the blocked writer receives a broken-pipe error, closes its write end,
and exits.

This is specific to the fixed Aider 0.86.2 caller edge.  It launches no helper
subprocess, does not read prompt text, model responses, filenames, or target
contents, and does not predict or count confirmations.  Every Aider
confirmation therefore receives No without exposing EOF while Aider is alive.
The initially selected target needs no confirmation and remains editable.

The caller still removes only inherited `AIDER_YES_ALWAYS`: in Aider 0.86.2 a
true-like value bypasses stdin and automatically accepts confirmations.  The
misleading temporary `yes-always: false` value was removed; the remaining
private empty YAML config continues to prevent ordinary Aider config discovery.

## Model-free real-Aider proof

The proof used the installed `aider 0.86.2`, a fresh temporary directory outside
the repository, Aider's documented `--apply FILE` debug path, and the actual
private-pipe helper from `aider_command.py`.  `--apply` supplies a controlled
whole-file response directly to Aider's edit pipeline, so no model endpoint,
HAC native endpoint, or generated code ran.  No private paths, response text,
credentials, or raw transcript are retained.

The controlled response included one edit for each of:

- the selected existing target;
- an unselected existing file;
- an unselected missing nested file.

Observed result:

```text
aider=0.86.2 selected=changed existing=unchanged missing=not-created
```

Aider displayed its normal confirmation text for both unselected paths, but
received automatic No from the private pipe; no human input or interactive
approval was required.  The missing file's parent directory was also absent
after the proof.  The process returned zero and the private temporary proof
material was removed.

## Scope preserved

This proof does not make Aider a filesystem sandbox or general developer-tool
framework.  HAC still does not parse/apply edits, inspect response paths or
target bytes, copy workspaces, clean up unauthorized edits, run shell commands,
or add filesystem infrastructure.  The existing one-subprocess, `whole`,
non-Git, no-test, no-lint, no-shell, bounded translator, and two-request
boundaries remain unchanged.
