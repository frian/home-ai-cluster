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

## Interpretation and boundary

In this bounded corpus, `qwen3:8b` showed the most consistent closed-envelope
adherence and generally good code quality with some semantic imperfections.
`qwen2.5-coder:14b` showed the strongest observed semantic code quality, with
intermittent closed-envelope formatting failures. `qwen2.5-coder:7b` repeatedly
failed the closed envelope in its limited case, so broader quality was not
evaluated. `qwen3.5:9b` followed the envelope and task in some cases, but had
several semantic failures and one observed envelope failure.

These observations reinforce the separation between HAC caller mechanics and
model-generated content. A rejected invalid response demonstrates the accepted
closed-envelope contract being enforced; it does not justify model-response
repair or a more permissive envelope. Nothing observed here requires or
justifies changing RFC-0080 or RFC-0081 behavior.

## Privacy boundary

This record retains no hostname, username, target path, raw prompt, complete
generated source, private runtime URL, authorization value, or raw server log.
