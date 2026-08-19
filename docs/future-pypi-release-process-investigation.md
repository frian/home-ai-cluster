# Future PyPI Release Process Investigation

Status: Investigation

Date: 2026-08-19

## Purpose and non-goals

This documentation-only investigation identifies the smallest boring process
for a future stable PyPI release. It does not implement a workflow or authorize
a publication, tag, GitHub Release, version change, external configuration
change, or an RFC.

It does not turn the roadmap into a release plan, define a general versioning
policy, add changelog machinery, or change Home AI Cluster architecture,
requests, routing, adapters, privacy, configuration, or compatibility.

## Evidence boundary

### Repository observations

At the time of investigation, `main` is
`eb3f432004f4d062b2377840fec86dba83da4a3a` and `pyproject.toml` declares
`0.3.0.dev0`. The PEP 440 development-release spelling deliberately gives the
current materially newer source tree a non-released identity.

The annotated `v0.2.0` tag resolves to
`1c3b9c188b5f512e607c480a5a0f4e0e2f52a5e1`. Repository history records:

- PR #467 prepared that historical source and was merged at the tagged commit.
- PR #479 added, and then used, a narrowly historical `release.yml` to publish
  `0.2.0` from that exact tag.
- PR #480 made the README PyPI-friendly; PR #481 added explicit license and
  project URL metadata; PR #482 changed `main` to `0.3.0.dev0`.
- PR #483 removed the completed historical workflow. Consequently, current
  `main` has no `.github/workflows/release.yml` and no current release
  workflow.

The retained release-readiness investigation is historical evidence, not a
current release authorization. Its conclusions correctly distinguish the
historical tag from later `main` source.

### Verified external operator configuration

Read-only authenticated GitHub API inspection on 2026-08-19 verifies that the
`pypi` environment has required reviewer `frian`, self-review prevention
disabled, no wait timer, administrator bypass disabled, no environment secrets,
and one selected deployment branch policy: `main`.

The existing PyPI Trusted Publisher configuration is **operator-confirmed
context**, rather than repository evidence: it trusts owner `frian`, repository
`home-ai-cluster`, workflow filename `release.yml`, and environment `pypi`.
This investigation did not access or modify PyPI publisher settings.

### Current official external documentation

The following primary documentation was accessed on 2026-08-19:

- [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/using-a-publisher/)
  documents the GitHub OIDC publishing action, required `id-token: write`, and
  strongly encourages an environment.
- [PyPI Trusted Publishing security model](https://docs.pypi.org/trusted-publishers/security-model/)
  says to treat a trusted publishing workflow like a credential, use the
  smallest trusted workflow, per-job permissions, and a dedicated environment.
- [PyPI Trusted Publishing internals](https://docs.pypi.org/trusted-publishers/internals/)
  describes publisher matching against GitHub owner, repository, workflow, and
  environment claims.
- [PyPA version specifiers](https://packaging.python.org/en/latest/specifications/version-specifiers/)
  defines `.devN` development releases and final release identifiers. Public
  versions must be unique for one distribution.
- [GitHub workflow triggers](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow)
  documents `workflow_dispatch` and `push` trigger selection.
- [GitHub deployments and environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)
  states that a selected deployment branch/tag rule is matched against the
  workflow run's `GITHUB_REF`.
- [GitHub deployment protection](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/control-deployments)
  documents that a job referencing an environment waits for its protection
  rules before it starts and before it accesses environment secrets.

The conclusions below are inferences from these sources and the repository
observations; they do not themselves change external state.

## 1. Release source of truth

For a stable release `X.Y.Z`, all of the following must agree:

```text
pyproject.toml version: X.Y.Z
tag:                    vX.Y.Z
build source:           exact commit resolved by vX.Y.Z
published artifacts:    built from that verified source and metadata version
```

The stable version is declared in the release-preparation source tree. It is
the package-metadata value to inspect; the workflow must not derive it from a
tag or rewrite it. The annotated tag is then created *from* that reviewed
release commit, using the conventional `v` prefix. The tag selects the source
to build, but the workflow must verify its peeled commit, tag name, and built
metadata rather than assuming any relationship.

Thus the relationship is: a reviewed release-preparation merge commit carries
`X.Y.Z`; `vX.Y.Z` points exactly at that commit; the build checks out that tag;
the built distributions report `X.Y.Z`; and the publish job uploads only those
distributions. The artifact is derived from the checked-out source. Tag/version
equality and tag/source identity are verification conditions, not a custom
version-management system.

## 2. Development-to-stable transition

The following ordinary lifecycle is sufficient and matches the current
`0.3.0.dev0` boundary:

1. Normal development remains on `main` at `0.3.0.dev0`.
2. One dedicated, reviewed release-preparation PR changes deliberate release
   material, including the version to `0.3.0`.
3. After it merges, create annotated tag `v0.3.0` at that exact merge commit.
4. Run the future release workflow from `main`, selecting `v0.3.0`; it builds
   and validates the tag, then waits for protected publication approval.
5. After successful publication, a separate small PR moves `main` to the next
   deliberate development identity, such as `0.4.0.dev0`.

PEP 440 permits the existing `.dev0` form and orders development releases
before their corresponding final release. No repository evidence calls for a
release-management abstraction, automated version derivation, or changelog
machinery.

## 3. Trigger choice and environment compatibility

### Option A — manual dispatch from `main`

A `workflow_dispatch` `release.yml` on `main` accepts a tag name, validates it,
checks out the tag, and builds the tag source. The workflow run's ref is
`main`, so the existing selected deployment policy permits its publish job to
use environment `pypi`. The workflow file must reside on the default branch for
manual dispatch, which also makes it reviewable before use.

This has a clear operator action and no accidental tag-push publication. The
environment approval occurs after a successful build, so the approver can see
the completed build result before authorizing publication. A failed build is
fixed or rerun without an approval request. It matches the existing Trusted
Publisher filename and environment without external changes.

### Option B — tag-push workflow

A `push` trigger limited to `v*` tags would naturally run on the tag ref and
could build that tag directly. It introduces an automatic release attempt at
tag creation, even though the environment could still stop publication.

More importantly, the present `pypi` rule selects only branch `main`. GitHub
matches deployment rules against `GITHUB_REF`; a tag-push run therefore has a
tag ref and cannot deploy to this environment unless an explicit matching tag
rule is added. That is an external configuration change. It also makes a
mistaken tag push create an unwanted run and gives less separation between tag
creation and the intentional publication attempt.

### Recommendation

Prefer **Option A**, a manually dispatched workflow from `main` with an
explicit release-tag input. It is compatible with the current environment and
publisher configuration, keeps tag/source identity explicit, preserves a
post-build approval boundary, and avoids extra automation. It does not require
the current `main`-only environment rule to change.

## 4. Build/publish separation

Future releases should retain the proven two-job form:

```text
no-OIDC build and validation job
        ↓ exact distribution artifact
protected no-checkout publish job with job-level OIDC
```

The build job checks out and verifies the selected tag; it has no `id-token:
write` permission. It builds, validates, and uploads exactly the reviewed wheel
and sdist as one GitHub Actions artifact. The publish job depends on that job,
uses environment `pypi`, receives `id-token: write` only at job scope,
downloads the artifact, and uses the standard PyPA publishing action. It does
not check out source and does not rebuild.

This preserves the key invariants: build code has no PyPI authority; approval
happens only after a successful build; the publish job receives exactly the
validated distributions; and no permanent PyPI token is stored. Current PyPI
guidance gives no concrete reason to change this shape.

## 5. Minimum useful validation

Release-preparation review should run the ordinary project test suite and lint
and inspect the intended version change before merge. Those checks demonstrate
source readiness; they need not turn the release workflow into all of CI again.

The release build workflow should perform the packaging-specific checks that
bind the published files to the release identity:

- resolve the selected annotated tag to its exact commit and check out that
  commit;
- require tag name `vX.Y.Z` and generated metadata `Version: X.Y.Z` to agree;
- build one wheel and one sdist successfully;
- require exactly the two expected versioned distribution filenames and no
  other regular distribution file;
- run `twine check` on both files;
- inspect wheel `METADATA` and sdist `PKG-INFO` for the stable version; and
- install the wheel in a clean environment and run `hac --help` as the central
  installed-command smoke check.

Repeating the full suite and lint in the release job is redundant if those are
required before the release-preparation merge. A clean installation remains
useful because it exercises the built artifact rather than the checkout.

## 6. GitHub Release object

A GitHub Release object is not required for PyPI publication, Trusted
Publishing, a tag, or the environment approval. It may be a separate optional
presentation step after a successful PyPI release, but it is not a prerequisite
and should not be coupled to the smallest publication workflow.

## 7. Existing Trusted Publisher

The future workflow can reuse `.github/workflows/release.yml` and environment
`pypi` unchanged, provided the operator-confirmed publisher still trusts owner
`frian`, repository `home-ai-cluster`, that exact filename, and that exact
environment. The recommended manual trigger runs from permitted `main`, so the
existing environment branch policy also needs no change.

Changing the publisher configuration is required only if one of those trusted
identity components changes: owner, repository, workflow filename, or
environment. A tag-push design would also require changing the GitHub
environment deployment policy to permit the relevant tag pattern, but does not
by itself require a PyPI publisher change. There is no current benefit to either
change.

## 8. Failure and retry behavior

- If release-preparation validation fails before merge, fix it in that PR; no
  tag or publication exists.
- If tag/version validation fails, stop before build or publication. Correct
  the reviewed release preparation and create an intentionally correct tag;
  do not make a published tag point at different contents.
- If a build fails after tag creation for an environmental/transient reason,
  diagnose and rerun against the same tag. If the tagged source itself needs a
  change, start a new reviewed release preparation rather than treating a
  published release tag as mutable.
- If the publish job is waiting, approval is the deliberate final authority
  gate. If it is rejected or left unapproved, nothing reaches PyPI; correct or
  cancel and make a later explicit attempt.
- If PyPI publication fails, retry only after determining whether any file was
  accepted. Do not replace an existing PyPI artifact with different contents.
  A partial or permanent source defect requires a new deliberate release
  preparation, not a rewritten published release.
- If publication succeeds but the later development-version PR fails, PyPI and
  the release tag remain valid. Fix that separate development PR; it is not a
  reason to alter the release artifact or tag.

## 9. Security boundary

PyPI publication authority is granted only when the publish job obtains a
short-lived OIDC identity with `id-token: write` and PyPI accepts it for the
configured Trusted Publisher. The environment protects that job with its
required reviewer and permitted-ref rule. PyPI trusts the configured GitHub
owner, repository, workflow filename, and environment claims.

The build job deliberately receives no OIDC publishing authority. It can only
produce artifacts; it cannot obtain the trusted identity to upload them. The
publish job should receive no checkout and no rebuild capability, narrowing the
code that executes with release authority. Because changing `release.yml` can
change what receives that authority, such changes deserve focused review. No
stored PyPI token or token-based fallback is justified.

## 10. Smallest recommended process

**Outcome B — one small future release workflow is warranted.**

Its bounded responsibilities are to accept an explicit stable tag from a
manual run on `main`; resolve and check out that tag; verify tag, source commit,
and package version consistency; build and perform the packaging-specific
validation above; upload exactly one wheel and one sdist; and let a dependent
protected `pypi` publish job download and publish those artifacts without
checkout or rebuild.

Preconditions are a reviewed stable release-preparation commit, an annotated
matching tag, the unchanged `main` deployment rule, and the existing trusted
publisher identity. The future workflow remains a separately reviewed
implementation task. This investigation does not implement it.

## Architecture boundary

No finding changes cluster architecture, requests, routing capabilities,
runtime boundaries, privacy contracts, protocols, configuration format, or
long-term application compatibility. Release packaging, tagging, and
publication mechanics here are repository/release-process maintenance. **No RFC
is required.**
