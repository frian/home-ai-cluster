# RFC-0117 Workspace-Aware Code Proof

Status: Post-1.0 development record

## Purpose

This factual, privacy-safe record retains one real operator exercise of the
accepted RFC-0114, RFC-0116, and RFC-0117 workspace-aware Code path on `sat`.
It is evidence of implemented behavior only. It makes no new architectural
decision, supported-workflow, benchmark, model-quality, or release claim.

## Proof setup and boundary

The operator used the disposable caller-local workspace
`/tmp/hac-workspace-proof`. It initially contained:

```text
README.txt
    Project: Home AI Cluster
    Status: experimental workspace proof

docs/note.txt
    The secret number for this test is 42.
```

The physical host root was proof setup only. The model-facing interaction used
RFC-0114 logical paths such as `README.txt` and `docs/note.txt`; RFC-0117 kept
the physical root caller-local. The explicit grants, the root, and the
workspace authority were ephemeral to each `hac code-workspace` invocation.

## List and read exploration

One real `hac code-workspace` invocation granted only `list` and `read` and
asked the model to inspect the workspace and find the secret number. HAC
reported these completed actions:

```text
workspace list ".": success
workspace read "README.txt": success
workspace list "docs": success
workspace read "docs/note.txt": success
```

The final response was:

```text
The secret number stored in 'docs/note.txt' is 42.
```

This establishes narrowly that the real operator surface ran; the model made
multiple workspace requests; HAC enforced the explicit `list`/`read` grant;
the resulting workspace outcomes were reinjected into the bounded Code
interaction; and that interaction ended with a normal final response. It does
not establish autonomous repository understanding or general model quality.

## Missing-target creation refusal

A later exercise granted `list`, `read`, and `write` and asked the model to
create `result.txt`. The target did not exist. As RFC-0114 specifies, `write`
replaces one existing regular UTF-8 file and does not create a missing target.
The relevant activity included:

```text
workspace write "result.txt": refused
```

In one run, the model repeated work after that refusal and the bounded
interaction ended with:

```text
error: code-workspace action budget exhausted
```

This is expected boundary evidence: granting `write` did not silently grant
creation, the caller-local authority refused the missing target, the model did
not bypass that authority, and the existing action budget bounded the
unproductive continuation. The inability to create the file is not a bug in
this proof and this record proposes no future solution.

## Existing-file replacement

The operator then pre-created `result.txt` with placeholder content. A final,
deliberately mechanical real-model exercise granted only `read` and `write`
and instructed:

```text
Read docs/note.txt. Replace the existing file result.txt with exactly the complete text you read from docs/note.txt, with no additional text. Then read result.txt and confirm whether its content is identical.
```

HAC reported:

```text
workspace read "docs/note.txt": success
workspace write "result.txt": success
workspace read "result.txt": success
```

The final response was:

```text
Success, the content of result.txt matches the content read from docs/note.txt
```

Independent host verification with `cat /tmp/hac-workspace-proof/result.txt`
returned exactly:

```text
The secret number for this test is 42.
```

This is the key proof result. It establishes one real operator path through:

```text
ordinary Code inference
    -> RFC-0116 workspace action request
    -> caller-local RFC-0114 authority
    -> successful existing-file replacement
    -> subsequent model-requested read
    -> final response
```

The physical result was independently verified afterward. This does not claim
transactional semantics beyond RFC-0114, code correctness, or general agent
capability.

## Model-behavior observations

Two exploratory attempts requested `src/example.py`, which did not exist in
the disposable workspace, and HAC refused the read. The repeated request is
notable because the same literal appears in the current RFC-0116 internal
response-format example. This proof does not establish whether that example
caused the model behavior; investigating that question is separate work.

One exploratory run also wrote syntactically valid but semantically wrong
content:

```text
Secret: <number>
Source: src/example.py
```

That observation distinguishes filesystem-authority success from model task
correctness. The later mechanical replacement exercise, not this exploratory
result, is the retained evidence for successful write/read truth.

## Boundaries preserved

This proof does not add or change architecture, workspace authority, file
creation authority, routing, model selection, runtime behavior, tests, RFCs,
or product behavior. It does not establish model-independent correctness,
general autonomous behavior, repository understanding, shell/process access,
remote filesystem authority, or a supported benchmark or promise.

## Architecture references

- Accepted RFC-0114 — bounded HAC local workspace authority
- Accepted RFC-0116 — bounded workspace-aware Code interaction
- Accepted RFC-0117 — bounded workspace-aware Code operator surface
