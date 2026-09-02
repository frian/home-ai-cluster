# Aider post-edit summarization investigation

Status: Investigation

Date: 2026-08-21

## Scope and conclusion

This documentation-only, model-free investigation concerns the installed, pinned Aider 0.86.2 one-shot lifecycle after merged PR #501. It used disposable targets, a private fake OpenAI-compatible endpoint, and HAC's real `_AiderTranslator`; it made no HAC, Ollama, external-model, or generated-code request, and did not modify Aider.

**Outcome C — no deterministic compliant repair has been established.** Aider can start automatic chat-history summarization after applying a selected edit in a `--message` invocation. The current two-request edge admits one such auxiliary Aider request, but the Aider 0.86.2 process-exit race can fail it; a second summary-model attempt then exceeds the caller edge's two accepted requests. A high finite history limit works for a known controlled payload, but the accepted byte limits cannot prove a model-independent token threshold for every invocation. No magic value should be implemented.

PR #501's private continuous-No stdin mechanism remains an independently successful single-target fix. It supplies `n` only for confirmations, did not deadlock, and did not change the controlled request shapes or summary lifecycle. The expected non-terminal stdin warning is not evidence of causation.

## Accepted contract and classification

RFC-0068 provides one fixed external Aider 0.86.2 subprocess for the explicit target; RFC-0069 limits filesystem authority to it; RFC-0072 permits at least one and at most two qualifying Aider-shaped requests. Each accepted request maps to one native `capability=code` request. The optional second request is Aider-owned, not HAC-generated. There is no third native request, model selector, execution, generic loop, or change to the fixed whole-file integration.

A chat-history summarization request is **A: naturally within RFC-0072's optional Aider-owned second-request allowance** when it is the second qualifying request after a successful edit. This does not permit a third request. Suppressing incidental automatic summary would not itself expand the RFC contract, but a deterministic suppression guardrail is not yet proven.

## Retained real-local observations

Attempt #1 used the reported `time uv run hac aider --file ~/bin/system-status-qwen3.py --timeout-seconds 300 --message ...` command with Qwen3 8B. Aider printed `litellm.BadRequestError ... Error code: 400 {'error': 'Home AI Cluster request failed'}`, then `error: Aider caller edge failed`; no edit was shown. Wall time was `5m5.712s`.

Attempt #2 immediately retried the same/materially identical command against the same running setup. It printed `Applied edit to system-status-qwen3.py`, then `Summarization failed for model openai/home-ai-cluster: cannot schedule new futures after shutdown`, LiteLLM's 400 `Home AI Cluster request failed`, `summarizer unexpectedly failed for all models`, and the caller-edge error. It returned normally after `8m29.730s`. The selected file had changed but was not executed or evaluated.

The retained terminal text has no per-request timestamps or HAC server log. It therefore does **not** prove that the first native request in Attempt #1 timed out, nor how Attempt #2's duration divides between generation, native waits, and retry delay. The 305.7 seconds is strong timing-only consistency with the configured 300-second timeout.

## Translator status rules

`_AiderTranslator` in `src/home_ai_cluster/commands/aider_command.py` returns 400 for bad ingress/shape, an already failed translator, more than two accepted requests, or accepted/projected mismatch. It returns 502 when a valid accepted request cannot complete its one native request (including an HTTPX timeout), and records `failed=True`. A terminal 400 can therefore be a later valid request rejected because an earlier request produced 502 and failed the translator.

## Controlled request evidence

All cases used a fresh temporary directory, real installed Aider 0.86.2, a disposable selected target, HAC's actual translator, the actual private continuous-No helper, and a controlled native client. They used the fixed model name, whole-file setting, and `--message` lifecycle. No prompt or generated source content is retained.

### Case B — immediate native-timeout equivalent

Request 1 reached `/v1/chat/completions` with top-level `messages` and `model: "home-ai-cluster"`; roles were `system,user,assistant,user,assistant,user,assistant,user`. It passed `_valid_aider_request()` at `(accepted=0, projected=0, failed=False)`, was accepted, and made one native `capability=code` attempt. An injected immediate HTTPX timeout equivalent returned 502 and changed state to `(1,0,True)`.

LiteLLM/Aider retried once. Request 2 retained the valid Aider shape but saw `(1,0,True)` and received 400 **solely because `translator.failed` was true**; it made no second native request. The Aider child returned zero, while the outer caller edge correctly failed due to translator state. This proves the controlled 502 -> retry -> failed-state-400 sequence without waiting 300 seconds.

The strongest reconstruction of Attempt #1 is the same: native failure (plausibly the configured timeout) -> 502 -> Aider retry -> failed-state 400. It remains a reconstruction; the retained terminal evidence alone does not prove the timeout.

### Case A — successful edit followed by forced summary

With `--max-chat-history-tokens 1`, a controlled valid whole-file result was applied to the selected target. The structural records were:

| Request | roles | State before | Status and state after | Native request |
| --- | --- | --- | --- | --- |
| 1 | normal edit (eight roles) | `(0,0,False)` | 200 -> `(1,1,False)` | yes |
| 2 | summary (`system,user`) | `(1,1,False)` | 200 -> `(2,2,False)` | yes |
| 3 | summary (`system,user`) | `(2,2,False)` | 400 -> `(2,2,True)` | no |

Request 3 was rejected because accepted count was already two, not because its shape was invalid. Its child output included the same diagnostic classes as Attempt #2: summary shutdown error, LiteLLM 400, and all-models summary failure. This structurally reproduces the post-edit lifecycle without a model.

A separate large controlled whole-file response crossed Aider's default history threshold after the edit. Through the real translator, its summary payload can itself exceed RFC-0067's 65,536-byte aggregate native limit: request 2 then gets 502 from native-request validation and retry/fallback sees failed-state 400. That is an additional bounded-payload failure mode, not proof of Attempt #2's cause.

### Case C — finite high limit

The same controlled edit with an explicit large finite positive history limit applied the edit, made only request 1, required no human input, and exited zero. This proves only suppression for the known payload. It does not prove a safe universal value because HAC bounds bytes while Aider measures tokenizer-dependent history plus formatting and prompt overhead.

## Exact Aider 0.86.2 lifecycle

`aider/main.py:949-952` constructs `ChatSummary([main_model.weak_model, main_model], args.max_chat_history_tokens or main_model.max_chat_history_tokens)`. `main.py:1126-1134` calls `coder.run(with_message=args.message)` and returns; it does not call `summarize_end()` on the one-shot exit path.

After a successful apply, `aider/coders/base_coder.py:1585-1594` calls `move_back_cur_messages()`. That method appends current messages to done messages and calls `summarize_start()` (`1036-1044`). `summarize_start()` tests the threshold, joins a prior summary if necessary, then starts a non-daemon Python thread (`1002-1012`). Its worker calls `ChatSummary` (`1014-1023`). `summarize_end()` joins only when a later formatting/lifecycle path invokes it (`1024-1035`, including `format_messages` at `1278`); `--message` exit does not ensure that join.

`aider/history.py:15-25` tests history size; `98-123` builds a `system,user` summary request and calls `simple_send_with_retries()` for every supplied model. With the fixed custom model, `Model.get_weak_model()` sets `weak_model = self` when no distinct weak model exists (`aider/models.py:588-605`). The list thus contains the same `openai/home-ai-cluster` model twice: after one failed summary attempt, Aider can make a second attempt, which the two-request translator rejects.

### `cannot schedule new futures after shutdown`

The controlled reproduction establishes a race, not a caller-edge parsing failure. While the Aider summary thread is active, the one-shot main path may return and Python shutdown begins. In installed Python 3.12, `concurrent/futures/thread.py:18-36` wakes executor workers during shutdown; the worker path at `98-106` sets an executor's `_shutdown=True` during interpreter shutdown. `ThreadPoolExecutor.submit()` then raises the exact `RuntimeError: cannot schedule new futures after shutdown` (`165-174`).

LiteLLM 1.81.10 creates a process-global `ThreadPoolExecutor(max_workers=100)` in `litellm/litellm_core_utils/thread_pool_executor.py:1-5`. After completion, `litellm/utils.py:1628-1640` schedules its success callback with `executor.submit(...)`. That post-response submit supplies the source-level path to the observed error. `ChatSummary.summarize_all()` catches it and prints the summary failure (`history.py:114-123`), then tries its second model entry. This is separate from the later caller-edge 400.

## Retry and duration analysis

Both normal model requests and `simple_send_with_retries()` classify LiteLLM exceptions using `aider/exceptions.py`. A 502/BadGateway-style failure retries; a 400/BadRequest does not. `simple_send_with_retries()` starts at 0.125 seconds, doubles before sleeping, and stops after the next delay would exceed `RETRY_TIMEOUT = 60` (`aider/models.py:26,1024-1067`): possible sleeps are 0.25, 0.5, 1, 2, 4, 8, 16, and 32 seconds (63.75 total), subject to response. In Case B the immediate second 400 stopped after one 0.25-second retry.

Those short sleeps cannot explain Attempt #1's 305.7 seconds; one 300-second native wait plus retry is consistent but unproven. They also cannot by themselves explain Attempt #2's 8m29, which can include initial generation, summary native wait, and retry/fallback timing; no retained timestamps allocate it exactly.

## `--max-chat-history-tokens` and candidates

The option is an `int`, default `None`, documented as a soft history limit after which summary begins (`aider/args.py:221-228`). Installed-0.86.2 parser experiments found: omitted -> `None`; `0` -> `0`; `1` -> `1`; `--max-chat-history-tokens=-1` -> `-1`; and a large positive is accepted. The separated `-1` spelling is parsed as an option and errors, but the equals form proves negative integers are accepted.

Because `main.py:949-952` uses Python `or`, `0` selects the model default and **does not disable** summary. `Model` starts at 1024 and derives `min(max(max_input_tokens / 16, 1024), 8192)` (`aider/models.py:327-346`). A positive `1` triggers nearly immediately once messages move back; a negative limit makes `total > limit` true. A high finite value works only for observed content. No documented disable switch exists in 0.86.2; model settings do not provide an off state, and a distinct weak model changes where summary is sent, not whether it starts.

| Candidate | Support / determinism | Result |
| --- | --- | --- |
| High finite limit | Supported, but heuristic under current limits | Do not recommend |
| `0` | Falls back to model default | Not a solution |
| Negative | Eagerly triggers summary | Not a solution |
| Distinct weak model | Does not suppress and changes model identity | Not suitable |
| Disable flag/setting | No supported 0.86.2 mechanism found | Unavailable |

RFC-0067's 65,536 bytes and RFC-0072's two requests cannot derive a finite token maximum: bytes are not tokens, and Aider includes formatted history and prompt overhead. Choosing a number would make a model-specific assumption look like architecture.

## RFC impact and recommended next step

No implementation or RFC decision follows from this investigation. The smallest credible direction is to establish an RFC-safe deterministic Aider 0.86.2 lifecycle guardrail (or obtain new architecture evidence), then evaluate it in a separate decision/implementation task. Raising the translator limit, accepting third requests, weakening failed-state rejection, patching/upgrading/embedding Aider, killing it after edit, or inspecting output are not normal bug fixes under the accepted boundary. A new RFC is not yet justified merely to conceal this failure.
