# RFC-0118 Workspace Empty-Leaf Creation Proof

Status: Post-1.0 development record

## Purpose

This factual, privacy-safe record retains one real operator exercise of the
accepted and implemented RFC-0114, RFC-0116, RFC-0117, and RFC-0118
workspace-aware Code path on `sat`. The proof was performed on the merged
`post-1.0-development` implementation at
`ca5f58308650845b5a8c1dd722313072e4444a28`.

It is evidence of implemented behavior only. It makes no new architectural
decision, supported-workflow, benchmark, model-quality, general agent-capability,
or release claim. The accepted RFCs remain the canonical architecture; this
record does not replace them.

## Proof setup and boundary

The operator recreated the disposable caller-local workspace from scratch:

```sh
rm -rf /tmp/hac-workspace-proof
mkdir -p /tmp/hac-workspace-proof/docs

printf '%s\n' \
  'Project: Home AI Cluster' \
  'Status: RFC-0118 creation proof' \
  > /tmp/hac-workspace-proof/README.txt

printf '%s\n' \
  'The secret number for this test is 42.' \
  > /tmp/hac-workspace-proof/docs/note.txt

find /tmp/hac-workspace-proof -maxdepth 2 -type f -print
```

Before the interaction, the relevant `find` output was exactly:

```text
/tmp/hac-workspace-proof/README.txt
/tmp/hac-workspace-proof/docs/note.txt
```

`result.txt` did not exist before the `hac code-workspace` invocation. The
physical host root was proof setup only. The model-facing interaction used
RFC-0114 logical paths such as `docs/note.txt` and `result.txt`; the physical
root, grants, and workspace authority were caller-local and ephemeral to this
invocation. No retained workspace grant or default grant was used.

## Empty-leaf creation and replacement

The operator used the ordinary `hac code-workspace` path with explicit `read`,
`create`, and `write` grants:

```sh
uv run hac code-workspace \
  --root /tmp/hac-workspace-proof \
  --grant read \
  --grant create \
  --grant write \
  'Read docs/note.txt. Create a new file named result.txt. Then replace result.txt with exactly the complete text you read from docs/note.txt, with no additional text. Then read result.txt and confirm whether its content is identical. Do not use any other workspace path.'
```

HAC reported the following completed actions and final response:

```text
workspace read "docs/note.txt": success
workspace create "result.txt": success
workspace write "result.txt": success
workspace read "result.txt": success
Identical content confirmed.
```

This establishes one successful path through:

```text
ordinary Code inference
    -> model-requested RFC-0116 read
    -> caller-local RFC-0114 read authority
    -> model-requested RFC-0118 create
    -> caller-local exclusive empty-leaf creation
    -> model-requested existing-file write
    -> caller-local RFC-0114 write authority
    -> model-requested read
    -> final response
    -> independent host verification
```

The result is narrow. HAC successfully read `docs/note.txt`, created the
previously absent `result.txt`, then wrote that now-existing file, and reread
it before the model returned a normal final response. `create` and `write`
remain distinct authorities: the successful `create` created the missing empty
leaf, and the later successful `write` populated it. This proof does not show
or imply that `write` can create a missing target, that `create` can publish
arbitrary content in one action, or that HAC created a parent directory.

## Independent physical host verification

After the interaction completed, the operator independently verified the host
filesystem with:

```sh
printf '\n--- result.txt ---\n'
cat /tmp/hac-workspace-proof/result.txt

printf '\n--- physical comparison ---\n'
cmp /tmp/hac-workspace-proof/docs/note.txt \
    /tmp/hac-workspace-proof/result.txt \
  && echo 'MATCH'
```

The observed output was:

```text
--- result.txt ---
The secret number for this test is 42.

--- physical comparison ---
MATCH
```

The model said `Identical content confirmed.` The host-side `cat` independently
showed the expected physical content, and `cmp` independently established
identity with `MATCH`. These are distinct evidence sources.

## Relationship to the RFC-0117 proof

The earlier RFC-0117 proof demonstrated missing-target `write` refusal,
inability to bypass that authority, and successful replacement only after the
operator manually pre-created `result.txt`. That refusal was correct under
RFC-0114 before RFC-0118; it was not a bug. This RFC-0118 proof establishes
only the narrower new fact that the manual pre-creation step is no longer
required when the operator explicitly grants `create`.

## Routing and model-behavior observations

This proof used the ordinary `hac code-workspace` path. It required no Pi,
OpenCode, Aider, generic tool framework, hidden shell, or RFC-0115 workspace
carrier for filesystem mutation. The significant filesystem-authority fact is
that HAC mediated the read, create, and write operations through its
caller-local workspace authority. This record makes no claim that no external
component exists elsewhere in the inference or runtime stack.

Unlike two exploratory runs retained in the RFC-0117 proof, this specific run
did not request the unrelated `src/example.py` path. It followed the instructed
logical paths `docs/note.txt` and `result.txt`. This is a factual observation
only; it does not fix, disprove, explain, or otherwise address that separate
model-contract observation.

## Boundaries preserved

This one proof does not establish general model correctness, autonomous
repository understanding, arbitrary software-development correctness,
transactional filesystem semantics, rollback semantics beyond the accepted
RFCs, directory creation, delete/rename/move authority, shell or process
execution, Git authority, retained workspace configuration, remote filesystem
authority, model-independent success rates, performance or reliability
benchmarks, or a release promise.

It does not add or change architecture, workspace authority, routing, model
selection, runtime behavior, tests, RFCs, or product behavior.

## Architecture references

- Accepted RFC-0114 — bounded HAC local workspace authority
- Accepted RFC-0116 — bounded workspace-aware Code interaction
- Accepted RFC-0117 — bounded workspace-aware Code operator surface
- Accepted RFC-0118 — bounded workspace empty-leaf creation
