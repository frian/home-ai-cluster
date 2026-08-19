# PyPI Release-Readiness Investigation

Status: Investigation

Date: 2026-08-19

## Purpose and boundary

This documentation-only investigation determines whether Home AI Cluster can
make a first legitimate PyPI publication without publishing a different
`0.2.0` artifact from the historical Git tag of that name. It records
repository inspection, local build and installation observations, and current
official PyPI, PyPA, and GitHub documentation.

No package was uploaded to PyPI or TestPyPI. No PyPI project, pending Trusted
Publisher, workflow, release, tag, version, dependency, package layout, or
configuration was created or changed. The temporary worktrees, build outputs,
and virtual environments used for the observations are not retained in this
repository.

This investigation makes no architectural decision. Release automation and
distribution metadata are release-preparation concerns; any future change must
remain local-first, privacy-first, engine-independent, capability-centered,
and small in scope.

## Evidence basis

- **Repository evidence** was read from the checked-out repository and the
  existing historical `v0.2.0` tag.
- **Local reproduction** used isolated temporary worktrees and clean temporary
  Python environments, not the repository development environment.
- **External documentation** is linked to the current authoritative PyPI,
  PyPA, and GitHub documentation.
- **Recommendations** below are inferences from those facts. They authorize no
  implementation.

## Git and version state

The observed current `main` commit was
`06edc5246cadb691065f9ebd27697c4c103c2c33`. The annotated historical
`v0.2.0` tag resolves to commit
`1c3b9c188b5f512e607c480a5a0f4e0e2f52a5e1`.

`v0.2.0` is an ancestor of `main`; `main` is 23 commits ahead of it. Both the
tagged `pyproject.toml` and current `main` declare:

```toml
version = "0.2.0"
```

The tag-to-main comparison contains 21 changed paths. In addition to retained
documentation and RFC-0077 material, it changes nine packaged implementation
files in the API, execution, model, orchestration, routing, remote transport,
and candidate-selection paths. It adds the implemented source-grounded Chat
vertical slice and its tests.

Therefore these are three distinct things:

| Item | Commit/source | Declared version | Meaning |
| --- | --- | --- | --- |
| Historical tag | `v0.2.0` at `1c3b9c1` | `0.2.0` | The only source tree that can truthfully own a PyPI `0.2.0` release. |
| Current main | `06edc52`, 23 commits later | `0.2.0` | A materially newer development tree that must not be published as `0.2.0`. |
| Future current-main release | Later explicitly versioned source | Later version | A separate future release after an intentional version change. |

Publishing current `main` as `0.2.0` would violate release/tag consistency:
two materially different artifact sets would claim the same release identity.
The current wheel uses the same filenames and has the same member paths as the
tagged wheel, but its contents differ. Its wheel SHA-256 is
`35631def64c66a5028f25012b89cca139d76dcf75ae83c84ea2465907c1e59b6`,
whereas the tagged wheel SHA-256 is
`5a0b11488d92e15462c9147464fced36efafd25cf59a67fa29ef7819b27dbeb0`.
The corresponding sdist SHA-256 values also differ. A same-version filename or
metadata header is not evidence of the same release contents.

## Historical `v0.2.0` build and artifact inspection

An isolated worktree at the exact tag was built with:

```text
git worktree add --detach <temporary-tag-worktree> v0.2.0
(cd <temporary-tag-worktree> && uv build)
```

Using `uv 0.5.9`, the build succeeded and produced:

| Artifact | Encoded package version |
| --- | --- |
| `home_ai_cluster-0.2.0-py3-none-any.whl` | `0.2.0` |
| `home_ai_cluster-0.2.0.tar.gz` | `0.2.0` |

The wheel has 54 members. It contains the expected `home_ai_cluster` package,
both runtime adapters, API and core modules, and the bundled browser assets:
`web/index.html`, `app.css`, `app.js`, and the included PDF.js files. It also
contains standard `.dist-info` metadata, `entry_points.txt`, `RECORD`, and
`licenses/LICENSE`. The wheel did not contain observed repository-only paths
such as `.git`, `dist`, `build`, `.venv`, caches, tests, docs, RFCs, or
`uv.lock`.

The sdist has 333 members. It includes the release source tree, `pyproject.toml`,
`README.md`, `LICENSE`, package and static files, tests, examples, and project
documentation/RFC records. That broader source-tree inclusion is the meaningful
difference from the installable wheel. No generated build directory, virtual
environment, cache, credential, or other obvious local state was observed in
the sdist.

This is evidence that Hatchling produced legitimate artifacts for the tagged
source; it is not a claim of bit-for-bit reproducibility across every future
builder environment.

## Installed-artifact observations

Two separate clean temporary CPython 3.14.4 environments were created. One
installed the built wheel and one installed the built sdist:

```text
uv venv --python 3.14 <temporary-wheel-environment>
uv pip install --python <temporary-wheel-python> <built-wheel>

uv venv --python 3.14 <temporary-sdist-environment>
uv pip install --python <temporary-sdist-python> <built-sdist>
```

Both installations succeeded without using the repository checkout. In each
environment:

- `import home_ai_cluster` resolved to the installed site-packages copy;
- `hac --help` succeeded and displayed the ordinary command dispatcher; and
- `home-ai-cluster --help` succeeded and displayed the same ordinary command
  dispatcher.

The installed direct runtime requirements matched artifact metadata:
`fastapi>=0.116.0`, `httpx>=0.28.0`, `pydantic>=2.11.0`, and
`uvicorn[standard]>=0.35.0`. Installation resolved those requirements and their
transitive dependencies in each clean environment; no development dependency
or live AI runtime was required for the import/help checks.

## Produced package metadata

The actual wheel `METADATA` and sdist `PKG-INFO` agree on:

- distribution name: `home-ai-cluster`;
- version: `0.2.0`;
- summary: `Local-first orchestration for personal AI runtimes.`;
- Python requirement: `>=3.13,<3.15`;
- the four runtime requirements above; and
- long-description content type: `text/markdown`.

The wheel's `entry_points.txt` contains the declared ordinary entry points,
including `hac` and `home-ai-cluster`, and the clean-install observations prove
those two central entry points were installed and usable for help.

`License-File: LICENSE` is present in the generated metadata and the bundled
license text explicitly identifies `AGPL-3.0-or-later`. Thus the artifacts do
carry the project's actual license. They do not currently emit an explicit
`License-Expression` field, `Project-URL` metadata, author/maintainer metadata,
or classifiers.

The distinction for a public release is:

- **Technically required for this build and upload:** name, version, valid
  build artifacts, and upload authorization. The built artifacts provide the
  required core name/version metadata; the build succeeded.
- **Strongly recommended, but not build blockers:** add an explicit SPDX license
  expression and useful project URLs in a future deliberate metadata change, so
  PyPI presents AGPL-3.0-or-later and the repository more directly.
- **Optional polish:** classifiers, keywords, and author/maintainer metadata.

The [PyPA core metadata specification](https://packaging.python.org/en/latest/specifications/core-metadata/)
identifies `Metadata-Version`, `Name`, and `Version` as required fields; the
additional presentation fields are not required by that specification.

## README and PyPI presentation

The tagged artifacts were checked ephemerally with:

```text
uvx --from twine twine check <built-wheel> <built-sdist>
```

Both checks passed. The `text/markdown` long description therefore rendered
successfully under Twine's package-description validation. This confirms
rendering validity, not that every link is useful to a PyPI visitor.

The README contains no image links, but it has repository-relative links to
`docs/`, `RFC/`, and `examples/`. Those links work in a repository checkout but
would resolve relative to a PyPI project page rather than to the repository and
are therefore likely broken or misleading there. Its installed-use example is
`uv tool install .`, which is appropriate for a checkout but not for a user
installing from PyPI. A future README-oriented release-polish change should use
absolute repository links and include an installed-package command such as
`uv tool install home-ai-cluster`. These are documentation-quality improvements,
not rendering or artifact-install blockers. The [PyPA PyPI-friendly README
guide](https://packaging.python.org/en/latest/guides/making-a-pypi-friendly-readme/)
recommends `twine check` for this rendering validation.

## Current-main comparison

Current `main` was built separately from a detached temporary worktree with
`uv build`. It also produced filenames ending in `0.2.0` and the same high-level
wheel metadata identity, but its artifact hashes differ from the tagged build.
The two wheels both have 54 member paths, while the current-main sdist has 342
members rather than 333.

The unchanged member-path list is not a release-equivalence guarantee: the
nine packaged implementation files changed between the tag and `main` have
different source hashes, and the current tree also has the new source-grounded
Chat behavior. This comparison is a negative finding only. It does not approve
current `main` for PyPI `0.2.0` and does not change its version.

## PyPI project-name observation

On 2026-08-19, a read-only request to PyPI's public JSON endpoint for
`home-ai-cluster` returned HTTP `404`. This observes that no project was
available at that endpoint at that time. It does not reserve the name, create
a project, or guarantee future availability.

That last point matters for the first upload: PyPI documents that a pending
Trusted Publisher does not reserve a project name and is invalidated if someone
else registers it first. See [Creating a PyPI Project with a Trusted
Publisher](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/).

## Trusted Publishing and the historical tag

Current official PyPI documentation supports a clean tokenless GitHub Actions
path. A GitHub Trusted Publisher configuration identifies the repository owner,
repository name, and authorized workflow filename; it may also bind a GitHub
Actions environment. For this repository, the identity would need to match
owner `frian`, repository `home-ai-cluster`, and the exact future workflow
filename. PyPI strongly recommends an environment because it can require manual
approval by trusted maintainers. See [Adding a Trusted Publisher to an existing
PyPI project](https://docs.pypi.org/trusted-publishers/adding-a-publisher/).

For the first project, PyPI supports a pending publisher. A successful first
upload creates the project and converts that publisher into a normal publisher;
no permanent PyPI API token is needed. The publishing job must obtain a GitHub
Actions OIDC identity and grant `id-token: write`; PyPI documents this as
mandatory and recommends job-level permission. Its standard publishing action
uses short-lived credentials instead of a stored username, password, or API
token. See [Publishing with a Trusted
Publisher](https://docs.pypi.org/trusted-publishers/using-a-publisher/).

Security remains a release responsibility. PyPI recommends treating a trusted
workflow like a credential: trust the correct repository and a smallest,
dedicated workflow, protect changes to it, and use a dedicated environment with
manual approvers where appropriate. See [Trusted Publishing security model and
considerations](https://docs.pypi.org/trusted-publishers/security-model/).

No GitHub Actions workflow exists on current `main` or at `v0.2.0`. Adding a
future tag-push workflow would not retroactively run for the already-created
tag. The smallest clean path for this historical release is instead a
two-job, manually dispatched workflow on the default branch:

1. The build/validation job has no OIDC permission. It checks out the literal
   `v0.2.0` ref, verifies that it resolves to exactly
   `1c3b9c188b5f512e607c480a5a0f4e0e2f52a5e1`, builds and validates the wheel
   and sdist, and uploads those resulting distributions as a GitHub Actions
   artifact.
2. The minimal publish job depends on that successful build job, uses the
   dedicated protected PyPI environment, and grants job-level `id-token: write`.
   It downloads the already-built distributions and publishes them with the
   standard PyPA PyPI publishing action. It must not rebuild the package.
3. After review, configure a pending publisher that names that exact workflow
   filename and run it with the environment approval.

The workflow file may be introduced later on `main`; its build job checks out
the existing historical tag and verifies the exact tagged commit before any
build, so the distributions derive from that verified source tree. The existing
tag must not be moved or recreated. GitHub documents that `workflow_dispatch`
files must be present on the default branch and can receive explicit inputs,
which supports a later manual release driver. See [Triggering a
workflow](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow).

Two alternatives are less suitable for this first release:

- Creating a GitHub Release for the old tag and using a release-event workflow
  can also select that tag, but adds a release object and event timing to a
  one-time historical publication.
- Building locally and uploading with a permanent PyPI API token could work,
  but is less bounded than the official OIDC path and is unnecessary here.

The fixed-tag manual workflow is the smallest boring option. It neither moves
nor recreates the existing tag, permits no current-main `0.2.0` publication,
and keeps OIDC authority out of the build job. This is a recommendation, not
an implemented workflow design.

## TestPyPI

**Conclusion: optional.** TestPyPI would add a hosted-index rehearsal and can
exercise a separate TestPyPI Trusted Publisher, but it cannot reserve or prove
the production PyPI name. Its Trusted Publisher configuration and OIDC audience
are separate from production PyPI; PyPI's publishing documentation identifies
the TestPyPI repository URL and `testpypi` audience separately.

The clean local wheel/sdist builds, metadata inspection, package-description
check, and clean installations already cover the important artifact risks found
here. A TestPyPI rehearsal may be worth the additional temporary configuration
for maintainer confidence, but it is not required for this first publication
and must not be treated as production authorization.

## Future plugin-packaging facts

This section records only packaging facts relevant to the separately
investigated, unaccepted external-information plugin idea.

- The core distribution is named `home-ai-cluster`; its installed import package
  is `home_ai_cluster`.
- Independently installable Python distributions can publish ordinary package
  metadata alongside the core distribution. Nothing in the current flat
  `src/home_ai_cluster` layout obviously blocks that future investigation.
- Python packaging defines entry-point metadata as a mechanism for installed
  distributions to advertise components to other installed code; it is available
  through normal distribution metadata. See the [PyPA entry points
  specification](https://packaging.python.org/en/latest/specifications/entry-points/).

This does not choose a plugin distribution name, entry-point group, interface,
discovery behavior, package layout, or implementation. Those remain future RFC
questions if the project later decides the boundary is warranted.

## Release-readiness decision

### Observed facts

- The historical tag builds, its wheel and sdist contain the expected material,
  both install cleanly, and the principal console scripts provide help.
- Tagged artifact metadata is internally consistent at `0.2.0`; its AGPL text
  is bundled through `License-File`.
- Current `main` is materially different but still declares `0.2.0`.
- No release workflow exists; the public PyPI endpoint has no project at the
  observed name, and this investigation made no PyPI or Trusted Publisher
  configuration.
- The PyPI name endpoint returned HTTP `404` on the observation date.

### Blocking issues

The tag artifact itself has no observed build, installation, or required-core-
metadata blocker. The blocking release-preparation gap is that no protected,
tokenless Trusted Publishing path has been established to build and publish the
exact tagged commit: the required workflow is absent and this
investigation did not configure a publisher. Publishing current `main` as
`0.2.0` is blocked by version consistency.

README link/install improvements, project URLs, and an explicit license
expression are strongly recommended public-release polish, not blockers found
by this investigation.

### Recommended outcome

**B. Make a small packaging/release preparation change first.**

Add the minimal manually dispatched, protected two-job Trusted Publishing
workflow: a no-OIDC build/validation job checks out and verifies exactly
`v0.2.0`, then a dependent OIDC publish job downloads those artifacts without
rebuilding. Configure the matching pending publisher only when that reviewed
workflow is ready. Do not move or recreate the tag, or publish current `main`
as `0.2.0`.

### Version consistency

The historical `v0.2.0` tag may safely own PyPI version `0.2.0`, provided the
release artifacts are built from that exact commit. Current `main` must receive
a later version before it can be published.

### Suggested next step

Open one small release-preparation PR that adds only the reviewed, manually
dispatched GitHub Actions workflow for the existing historical tag. Its no-OIDC
build/validation job should verify the exact tagged commit and upload artifacts;
its dependent dedicated-environment publish job should receive job-level OIDC,
download those artifacts, and publish without rebuilding. Then configure the
matching pending PyPI publisher out of band and run the approved workflow once.

This is release process and packaging work, not a core architectural decision;
no RFC is indicated by the evidence here. A separate follow-up may choose to
improve public PyPI metadata and README links, but it should not be coupled to
the release-proof workflow unless maintainers deliberately want that scope.
