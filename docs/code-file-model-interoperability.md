# Code-File Model Interoperability Observations

Status: Observed

Date: 2026-08-22

## Purpose

This record retains small manual observations from one local environment of how
several runtime-edge models behaved with the accepted RFC-0080 and RFC-0081
`hac code-file` caller. It is not a supported-model list, compatibility
guarantee, certification, benchmark, whitelist, recommendation contract, or
architectural dependency. HAC remains engine-independent and
capability-centered; model names here are observations, not requirements.

Generated files were inspected but not executed. Wall-clock times are
observational only, not controlled performance measurements; one run after a
model restart was notably slow.

The exact reusable seven-scenario procedure is retained in [Code-File Model
Interoperability Procedure](code-file-model-interoperability-procedure.md).

## Bounded corpus

The seven manual scenarios covered: trivial complete-file creation using only
`sys`; a constrained Linux system-information script using only `os` and
`shutil`; a small pure-Python aggregation function; a constrained existing-file
edit; a minimal binary-search correction preserving unrelated content; a small
feature with several simultaneous constraints; and an API-preserving
default-port behavior change.

## Observations

### Ollama `qwen3:8b` with thinking disabled

The first, third, and seventh scenarios passed in about 19.6, 28.4, and 36.9
seconds respectively. The second passed all 7 checks in about 52.4 seconds,
and the fifth passed all 6 checks in about 96.5 seconds with exactly the needed
binary-search direction change and no functional unrelated edit. The fourth was
a near-pass (7 of 8 observations) in about 19.2 seconds: it rendered angle
brackets in the requested output format literally as `<HAC demo>: ...`; that
test wording had some ambiguity. The sixth had a partial semantic failure in
about 27.3 seconds because one
`.replace("  ", " ")` cannot collapse an arbitrary run of spaces. No
closed-envelope rejection was observed in this corpus.

### Ollama `qwen2.5-coder:7b`

Only the initial trivial-creation case was pursued. `code-file` rejected the
closed envelope twice, after about 13.9 and 4.0 seconds. A separate raw
diagnostic that reproduced the native request without file mutation found an
outer `content` object containing an inner envelope, where the caller requires
outer `content` to be a string. The inner Python appeared plausible, but its
semantic quality was not systematically evaluated. This is a repeated
protocol-interoperability failure in these observations, not a general judgment
of the model's coding quality.

### Ollama `qwen2.5-coder:14b`

In this bounded corpus, observed semantic code quality was strongest. Scenarios
one through six passed at about 37.3 seconds, 56.1 seconds (7 of 7 checks),
50.8 seconds, 39.8 seconds (8 of 8 checks), 69.0 seconds (6 of 6 checks, with
a minimal one-line binary-search correction), and 42.3 seconds. The seventh
first failed the closed envelope after about 64.5 seconds, then passed on an
identical second attempt in about 43.8 seconds.

Separate raw diagnostics observed output-format variability: one semantically
correct envelope was wrapped in Markdown `json` fences, while another response
to the same native-envelope shape was valid JSON with string `content`. This
does not establish inability to follow the contract.

### Ollama `qwen3.5:9b` with thinking disabled

Scenarios one, three, and seven passed at about 16.5, 34.5, and 40.6 seconds.
The second failed in about 79.2 seconds: generated source was syntactically
invalid, calculated RAM-used rather than requested RAM-available percentage,
and added unnecessary complexity. The fourth partially failed in about 24.1
seconds: normalization was correct but `format_user` did not use the required
existing `APP_NAME` constant.

For the fifth, the first attempt failed the closed envelope after about 43.7
seconds. An identical second attempt returned a valid envelope in about 28.8
seconds, but its binary search returned immediately on a match and did not
guarantee the first occurrence. The sixth failed in about 30.0 seconds because
space collapsing was incorrect and the requested slug length was emitted as
literal text instead of calculated. Thus three of seven scenarios were full
passes in this small local corpus; this is not a general percentage-quality
claim.

### 2026-08-23 additions

#### Ollama `gemma4:12b` with thinking disabled

HAC was started with explicit Ollama model selection and
`--ollama-disable-thinking`. Each canonical scenario was attempted once, with
no corrective retry or closed-envelope rejection. Tests one through five passed
in 24.866, 90.635, 48.271, 34.506, and 73.958 seconds respectively. Inspection
found: the Test 1 file imported only `sys` and printed
`sys.version.split()[0]`; Test 2 imported only `os` and `shutil`, used
`used / total`, parsed `/proc/meminfo` directly with `MemTotal` and
`MemAvailable`, calculated available-RAM percentage, used
`os.getloadavg()[0]`, and produced exactly three intended lines; Test 3 had no
imports, exactly the four requested dictionary keys, correct empty-list
behavior, a float non-empty average, and exactly the three requested calls;
Test 4 preserved `APP_NAME`, used stripping and title case, used the existing
constant for the angle-bracket placeholders, and retained the protected final
print (a missing final newline was only formatting); and Test 5 made the
minimal `low = middle + 1` to `high = middle - 1` correction after a match,
thereby preserving protected content while continuing to the left half for the
first occurrence.

Test 6 completed in 42.162 seconds with a valid envelope, correct arbitrary
space collapsing, and correct slug-length calculation, but added `import re`
despite the explicit no-import constraint. This was a content-constraint
failure, not an envelope failure. Test 7 passed in 57.008 seconds: it omitted
HTTP 80 and HTTPS 443, retained explicit non-default ports and
`normalize_host`, and preserved protected signatures and unrelated behavior.

Six scenarios fully succeeded and one failed an explicit content constraint;
no envelope failure was observed. This is not a general score or certification.

#### Ollama `llama3.1:8b` with no explicit thinking control

The tested model was launched without an Ollama thinking-control option. All
seven canonical scenarios were attempted once and rejected as invalid code-file
responses after 11.305, 52.319, 29.725, 24.437, 53.310, 26.764, and 30.976
seconds respectively. Missing targets remained empty regular files, existing
baselines remained unchanged, and no heuristic extraction or repair occurred.

One separate raw diagnostic reproduced the Test 1 native request without file
mutation; it was not another corpus attempt. It observed introductory prose, a
fenced Markdown Python block, no required closed JSON envelope, and plausible
inner Python for the trivial task. The complete response and source are not
retained. Every canonical scenario was rejected at the envelope boundary in
this observation, so semantic quality was not systematically evaluated. This
is a protocol-interoperability observation, not a general judgment of Llama 3.1
code quality.

#### Ollama `deepseek-r1:8b` with thinking disabled

HAC was started with `--ollama-disable-thinking`. At this observation time, the
locally pulled `deepseek-r1:8b` tag resolved to the current DeepSeek-R1-0528
Qwen3 8B variant; that time-bounded local tag resolution is not an upstream
compatibility claim. The operator explicitly stopped the corpus after Test 5
because repeated 900-second timeouts made continuation operationally excessive;
Tests 6 and 7 were not attempted.

Test 1 passed in 31.421 seconds with a valid envelope; the minimal source
imported only `sys` and printed `sys.version.split()[0]`. Test 2 timed out
after 900.546 seconds with HAC reporting `ordinary request timed out`; its
missing target remained an empty regular file with mode 0644. Test 3 completed
in 84.038 seconds with an accepted outer envelope but failed content inspection:
the replacement contained literal backslash-n sequences rather than newline
characters, leaving one physical line that was not valid Python source. This
was not an envelope failure, and HAC did not decode or repair it heuristically.
Tests 4 and 5 timed out after 900.591 and 900.593 seconds; their existing
baselines remained strictly unchanged with empty diffs.

In this local run, after at least one caller timeout, Ollama inference continued
consuming CPU; `ollama stop deepseek-r1:8b` initially reported stopping while
work continued, HAC shutdown waited for the background request and required an
operator-forced shutdown, and the operator stopped inference before continuing.
HAC and Ollama were restarted with the same model and thinking-disabled setting
before later scenarios as necessary. These are local-run observations, not a
universal cancellation claim or architectural attribution.

The bounded outcome was one pass, one completed invalid replacement, three
explicit 900-second caller timeouts, and two scenarios not attempted by operator
decision. It is not a score and does not support a general DeepSeek quality
judgment.

## Interpretation and boundary

In this bounded corpus, `qwen3:8b` showed the most consistent closed-envelope
adherence and generally good code quality with some semantic imperfections.
`qwen2.5-coder:14b` showed the strongest observed semantic code quality, with
intermittent closed-envelope formatting failures. `qwen2.5-coder:7b` repeatedly
failed the closed envelope in its limited case, so broader quality was not
evaluated. `qwen3.5:9b` followed the envelope and task in some cases, but had
several semantic failures and one observed envelope failure.

The 2026-08-23 additions found strong closed-envelope adherence and generally
strong practical results from `gemma4:12b`, with one explicit import-constraint
violation. `llama3.1:8b` consistently failed closed-envelope interoperability
in this observation. `deepseek-r1:8b` showed severe practical irregularity in
this local environment, including repeated 900-second timeouts and one literal-
newline replacement failure. None of these observations justify changing
RFC-0080, RFC-0081, or HAC's fail-closed behavior, and none elevates a model to
a whitelist or contractual support tier.

These observations reinforce the separation between HAC caller mechanics and
model-generated content. A rejected invalid response demonstrates the accepted
closed-envelope contract being enforced; it does not justify model-response
repair or a more permissive envelope. Nothing observed here requires or
justifies changing RFC-0080 or RFC-0081 behavior.

## Privacy boundary

This record retains no hostname, username, target path, raw prompt, complete
generated source, private runtime URL, authorization value, or raw server log.
