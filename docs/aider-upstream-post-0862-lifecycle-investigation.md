# Aider upstream post-0.86.2 lifecycle investigation

Status: Current

Date: 2026-08-22

## Question

Does upstream Aider development after the installed caller edge's pinned
`v0.86.2` provide a deterministic, supported solution to the one-shot
`--message` chat-history-summarizer lifecycle problem?

This is a documentation-only investigation. It changes neither the Home AI
Cluster (HAC) version contract nor its implementation.

## HAC boundary

RFC-0068 defines the optional explicit caller edge:

```text
hac aider --file PATH --message TEXT [--timeout-seconds SECONDS]
```

It invokes exactly Aider `0.86.2`, with one selected target, whole-file edits,
and a private loopback translator. RFC-0069 permits only creation of the one
explicit missing target. RFC-0072 amends RFC-0068 solely to permit one
Aider-owned follow-up: the translator accepts at most two qualifying Aider
requests and makes at most two native `capability=code` requests. A third
request fails closed and makes no third native request.

HAC does not inspect a target or model output to decide success, retry or
correct an edit, ignore Aider failure, kill Aider after an edit, embed or patch
Aider, or own Aider's chat lifecycle. The private continuous-`No` child input
established by the earlier single-target proof remains out of scope here.

## Release and source facts

Facts were checked on 2026-08-22.

* PyPI lists [`aider-chat 0.86.2`](https://pypi.org/project/aider-chat/0.86.2/)
  as its newest published distribution, uploaded 2026-02-12. Its release
  history has no later published version.
* Upstream's `v0.86.2` tag resolves to commit
  [`253f0368b873ba30d8ee26e463718f0c03614ddf`](https://github.com/Aider-AI/aider/commit/253f0368b873ba30d8ee26e463718f0c03614ddf),
  whose message is `version bump to 0.86.2` (2026-02-11).
* The newest upstream tag is `v0.86.3.dev`, not a published release or an
  operator version contract. GitHub's Releases page still presents only
  `v0.86.0` as its latest GitHub Release; this presentation does not contradict
  the newer PyPI/tag evidence. Upstream issue
  [#5242](https://github.com/Aider-AI/aider/issues/5242) records that mismatch.
* The pinned `main` commit inspected and tested was
  [`5dc9490bb35f9729ef2c95d00a19ccd30c26339c`](https://github.com/Aider-AI/aider/commit/5dc9490bb35f9729ef2c95d00a19ccd30c26339c)
  (2026-05-22). It is after `v0.86.2` and is not contained by any later stable
  tag.

Therefore `0.86.2` remains the newest usable published Aider version contract.
No published release after it exists to qualify for Outcome A.

## Source comparison

The following authoritative upstream files were compared at the tag and pinned
`main` commit:

| Area | `v0.86.2` | `5dc9490` | Finding |
| --- | --- | --- | --- |
| [`aider/main.py`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/main.py) | creates `ChatSummary([main_model.weak_model, main_model], args.max_chat_history_tokens or main_model.max_chat_history_tokens)` | byte-identical relevant code | no disable state; `0` falls back to the model default |
| [`aider/coders/base_coder.py`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/coders/base_coder.py) | starts a non-daemon thread in `summarize_start`; `summarize_end` joins only when later called | byte-identical lifecycle | the one-shot return path has no explicit final wait or termination |
| [`aider/history.py`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/history.py) | loops every entry in `self.models` in `summarize_all()` | byte-identical | duplicate model entries are attempted separately after failure |
| [`aider/args.py`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/args.py) | `--max-chat-history-tokens` is `int`, default `None`, described as a soft threshold | byte-identical | no supported disable flag/config/model setting |
| model/weak-model construction | HAC's custom model has no distinct configured weak model | unchanged construction | `weak_model == main_model`, so the list has the same model twice |

`main.py` still calls `coder.run(with_message=args.message)` and returns on its
completion. The summary starts from `move_back_cur_messages()` after an edit;
there is no final `summarize_end()` in that one-shot exit path. A later normal
formatting path may join the thread, but that is not an exit-lifecycle
guarantee. The retained source comparison shows no post-tag change in
`main.py`, `history.py`, or the relevant summarizer lifecycle in
`base_coder.py`.

`ChatSummary.summarize_all()` catches an exception from its first model attempt
and continues through every model in the supplied list. It does not deduplicate
identical model objects. With HAC's custom model, the first failed summary
attempt can therefore be followed by the same model as a second summary
attempt.

The current upstream diff after `v0.86.2` changes model aliases/settings,
dependency compatibility, symlink handling, no-auto-commit staging, and other
unrelated behavior. It changes none of the listed lifecycle files except
unrelated `base_coder.py` file-staging conditions. No post-tag commit or merged
or open pull request was found that implements a final summary wait, cancellation,
or a summarization disable switch.

## Supported settings and rejected false fixes

`--weak-model` selects a model for commit messages and chat-history
summarization; it does not turn summarization off. A distinct weak model would
change destination, not suppress the request, and is not suitable for the
fixed HAC model contract.

`--max-chat-history-tokens` is a soft threshold, not a disable switch. `None`
selects the model default. Because `main.py` uses Python `or`, `0` also selects
the model default. Positive finite values merely postpone summarization for
particular content; a huge value is neither a proof nor a deterministic
architecture-safe bound. Negative values make the threshold easier to exceed.
The deliberately tiny value used below is only a test forcing mechanism.

No current CLI flag, configuration key, or model-setting off state disables
chat-history summarization completely. The following remain rejected:

* upgrading or pinning an unreleased commit without an RFC version-contract
  decision;
* increasing the soft threshold, setting it to zero, or choosing an arbitrary
  huge threshold;
* relaxing HAC's two-request bound, ignoring an Aider exit failure, or treating
  a changed file as success;
* killing Aider, monkey-patching it, embedding its Python API, or adding HAC
  retries/corrective prompts or semantic inspection.

## Issue and retry evidence

Upstream issue [#3700](https://github.com/Aider-AI/aider/issues/3700), opened
2025-04-01, remains open, unassigned, unlabelled, and has no linked pull request
or concrete closing change. It reports the same shutdown error:
`cannot schedule new futures after shutdown`, followed by two summary failures.
This is consistent with, but does not prove the cause of, any historic HAC run.

The current upstream dependency change from LiteLLM `1.81.10` at `v0.86.2` to
`1.82.3` at the pinned `main` is not a lifecycle fix. Aider's ordinary and
summary request retry behavior can affect timing after API failures, but neither
the source comparison nor the controlled response-success reproduction finds a
new wait/cancel behavior. Retry-related changes must not be confused with a
summarizer lifecycle solution.

## Controlled model-free reproduction

Two isolated `/tmp` virtual environments were created outside HAC. Each run
started a temporary local `127.0.0.1` OpenAI-compatible fake endpoint, made no
Ollama/HAC/model request, and recorded the requests. It returned one
deterministic valid whole-file edit for request 1 and `summary` for later
requests. The command used `--message`, explicit `--file`, whole edits,
`--no-git`, and `--max-chat-history-tokens=1` solely to force the test path.

| Aider source | Result |
| --- | --- |
| exact `v0.86.2` / `253f0368` | exit `0`; target became `print('edited')`; three model requests: normal edit first, then two summary-shaped `system,user` requests |
| pinned `main` / `5dc9490` | identical: exit `0`, edited target, then two summary-shaped requests |

The two summary requests demonstrate both that post-edit summarization begins
and that the duplicate same-model fallback remains possible. Since the process
exited successfully only after the fake endpoint answered both summaries, this
particular successful response case does not itself display the shutdown error;
it does prove that current `main` has not removed the third-request path.
The source path and open issue remain the evidence for the shutdown-race class.

Compatibility observations from the same source and runs are favorable but do
not authorize an upgrade: `--message` remains one-shot; whole edits and explicit
file targets remain supported; `--no-git` remains available; no mandatory shell
or tool execution was introduced; an explicit HAC-created target remains a
valid Aider target; and HAC's single-target fail-closed input guard remains
conceptually valid. These observations do not make an unreleased commit a
supported HAC version.

## Outcome and smallest next step

**Outcome D — no deterministic upstream fix or supported disable mechanism is
currently available.**

There is no later published release, no upstream-main lifecycle change, no
supported full disable switch, and no post-`v0.86.2` candidate commit to test as
a fix. The smallest justified step is no implementation change: retain the
existing `0.86.2` contract and return this evidence for architectural review if
the project wants to reconsider the caller edge. Any Aider version-contract or
lifecycle change requires an RFC before implementation.
