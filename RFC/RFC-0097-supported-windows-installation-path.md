# RFC-0097: Supported Windows Installation Path

Status: Draft

Date: 2026-09-02

Author: frian

## Summary

Home AI Cluster should support one low-friction native Windows installation
path for 1.0: Windows 11 x86_64 with WinGet available, upstream `uv`, the
ordinary HAC PyPI package, and a new PowerShell session after `uv` performs its
supported PATH update.

```powershell
winget install --id astral-sh.uv -e --source winget
uv tool install home-ai-cluster
uv tool update-shell
# Open a new PowerShell session.
hac --version
```

This is an installation-path compatibility promise, not an HAC installer or a
broad Windows-platform promise. HAC continues to own only its package and
commands; WinGet, Astral, PyPI, `uv`, and the operator retain their existing
responsibilities. No implementation or user-facing installation documentation
is authorized by this Draft RFC.

## Context

The non-binding 0.9 release direction requires one supported low-friction
Windows installation path before 1.0. It requires that a user need not already
understand Python packaging or `uv`, preserves separately packaged plugins, and
does not require a polished native installer merely for its own sake.

The merged [Windows installation path investigation](../docs/windows-installation-path-investigation.md)
found the upstream-tool path to be the smallest credible mechanism, but also
found that adopting it creates a durable Windows prerequisite and compatibility
promise requiring an RFC. RFC-0052 already leaves ordinary Python packaging
responsible for installation, console-script locations, upgrade, uninstall, and
PATH; it rejects an HAC-owned installer or PATH mutation. RFC-0078 preserves a
separately installed plugin boundary rather than bundling plugins into core.

## Problem

The ordinary published-package path is usable, but existing guidance does not
define one native Windows installation contract that an ordinary Windows user
can follow without prior Python-toolchain knowledge. Leaving the delivery
mechanism undefined risks either requiring that prior knowledge in practice or
adding an HAC-owned Windows layer without evidence that it is needed.

Doing nothing leaves the 1.0 release-direction exit condition incomplete. An
HAC bootstrap or conventional installer would solve a different problem while
creating new ownership and maintenance obligations.

## Goals

- Define one documented and validated native Windows 11 x86_64 installation
  path for 1.0.
- Let the user follow concrete upstream commands without manually locating
  Python, managing virtual environments, or understanding Python packaging
  before HAC is installed.
- Keep the ordinary PyPI package and separately packaged plugin model intact.
- Make the WinGet prerequisite, `uv` PATH step, new-PowerShell-session
  expectation, and boundaries of “supported” explicit.
- Preserve operator ownership of runtimes, models, network/firewall policy,
  and optional integrations.

## Non-goals

This RFC does not add or promise:

- an HAC-maintained PowerShell bootstrap, shell-profile mutation, or PATH
  mutation;
- an MSI, MSIX, EXE, Microsoft Store package, or WinGet package for HAC;
- bundled Python, system-wide Python installation, or Python lifecycle
  management by HAC;
- Windows service installation, automatic startup, firewall configuration, or
  WSL as part of this native path;
- Ollama or llama-server installation, runtime lifecycle management, or model
  download, placement, or management;
- SearXNG or external-information-provider lifecycle, plugin installation,
  credential handling, or secrets management;
- Windows 10, Windows ARM64, every Windows shell, every HAC capability/runtime
  combination, or native Windows runtime support beyond already accepted
  boundaries; or
- implementation, package metadata, release-workflow, test, or user-facing
  installation-documentation changes.

## Decision / Proposal

### Supported 1.0 installation boundary

For 1.0, HAC should document and validate this one supported native Windows
installation path:

1. Native Windows 11 on x86_64, with WinGet available.
2. PowerShell as the documented shell.
3. Install upstream Astral `uv` from the explicit WinGet source:

   ```powershell
   winget install --id astral-sh.uv -e --source winget
   ```

4. Install the ordinary published HAC PyPI distribution:

   ```powershell
   uv tool install home-ai-cluster
   ```

5. Let `uv` make its managed executable directory available to future shells:

   ```powershell
   uv tool update-shell
   ```

6. Open a new PowerShell session and verify command discovery, for example:

   ```powershell
   hac --version
   ```

This RFC defines a path, not a requirement that every user use it or a ban on
other technically valid advanced installation methods. It does not define an
upgrade policy. Existing package-version and release practices remain
authoritative for later documentation.

The prerelease command `uv tool install home-ai-cluster==1.0.0b2` is validation
evidence only. It is not part of the stable installation contract; the
normative command uses the ordinary unpinned published distribution.

### Meaning of supported

“Supported” here means that HAC documents and validates this ordinary native
Windows 11 x86_64 PowerShell route, including its explicit prerequisites and
the `uv` shell-discovery step. It does not mean HAC owns Windows infrastructure
or guarantees untested Windows, shell, runtime, model, integration, service,
or firewall combinations.

WinGet availability is an acceptable prerequisite for this one path. It does
not conflict with low friction: the user receives one concrete command to
obtain `uv`, does not manually install Python, and need not understand virtual
environments or package managers before following the instructions. The HAC
package remains the same ordinary PyPI artifact used elsewhere.

`uv tool update-shell` and a new PowerShell session are required visible steps.
They are acceptable because `uv` identifies the condition and provides the
upstream-supported command. HAC must not add its own PATH manipulation merely
to hide that one-time step.

The canonical WinGet command retains `--source winget`. Real validation needed
that explicit source because an unrelated Microsoft Store source certificate
failure interfered with source resolution. This decision selects the intended
source; it does not characterize that external failure as an HAC defect or a
permanent Windows condition.

### Ownership and plugin boundaries

The selected path preserves a deliberately small ownership model:

| Owner | Responsibility |
| --- | --- |
| Microsoft / WinGet | WinGet availability and the selected upstream package source. |
| Astral / `uv` | `uv` installation and management of its tool environment and executable discovery. |
| PyPI | Distribution of the ordinary HAC package. |
| HAC | Its published package and declared commands. |
| Operator | Runtimes, models, network/firewall policy, optional integrations, and their lifecycle. |

Installing core HAC through this path neither bundles nor silently installs a
plugin. RFC-0078's separately packaged plugin boundary remains unchanged.
This RFC does not establish Windows plugin-installation support or redefine
plugin compatibility.

## Evidence

On 2026-09-02, a clean-HAC Windows 11 Pro x86_64 VM with WinGet available
installed upstream `uv` using the canonical WinGet command. No manual Python
installation occurred. `uv tool install home-ai-cluster==1.0.0b2` installed the
published candidate and dependencies; after `uv tool update-shell` and a new
PowerShell session, `hac --help`, `hac --version`, and `hac config show`
succeeded. The version report was `1.0.0b2` and configuration showed the
expected unconfigured state.

Additional privacy-safe smoke evidence showed a Windows HAC caller route Code
to a remote Linux HAC node. `code-file` accepted absolute drive-letter paths,
backslashes, and paths with spaces; a valid result updated the selected local
file, while an invalid response left its selected file unchanged. This evidence
does not assess generated-code quality or establish every Windows capability or
runtime combination.

A raw cancellation traceback observed on a separate Linux `0.9.0.dev0` host is
not Windows or published-`1.0.0b2` regression evidence. The investigation and
the published 1.0 candidate validation retain the fuller evidence boundary.

## Rationale

This route meets the demonstrated release need with existing understandable
tools. It makes no user precondition out of Python or `uv` expertise: the
instructions supply one command for `uv`, while `uv` supplies the isolated
Python tool environment. It also avoids duplicating upstream installation,
PATH, trust, and environment-management work in HAC.

The path is local-first and privacy-preserving: installation obtains software,
but it adds no HAC cloud service, account, provider, runtime, or external
information authority. It remains engine-independent and capability-centered
because it does not change runtime adapters, requests, routing, or capability
semantics. It applies the project’s boring-solutions-first principle by using a
small sequence of explicit upstream commands rather than an additional
Windows-specific product layer.

## Alternatives considered

### HAC-owned PowerShell bootstrap

Rejected for 1.0. It would make HAC responsible for upstream downloads, trust
and integrity, version drift, PowerShell execution policy and behavior, PATH
mutation, errors, and ongoing Windows-specific testing. It duplicates WinGet
and `uv` without evidence that the selected path fails the release requirement.

### MSI, MSIX, or EXE installer

Rejected as a 1.0 requirement. Such an artifact may be reconsidered if future
evidence establishes a user need, but it would now create signing, release,
packaging, Python-bundling, update, maintenance, and plugin-model questions
without a demonstrated requirement.

### Direct manual Python and pip installation

Rejected as the supported low-friction path. It exposes the user to the Python
toolchain that the release direction specifically says they should not need to
understand before installing HAC. This does not prohibit advanced operators
from using otherwise valid methods outside this supported path.

## Trade-offs

The route depends on WinGet availability, an upstream `uv` command, a PATH
update, and opening a new PowerShell session. Those constraints narrow the
promise but keep it clear and testable. They are smaller than HAC assuming
installer, shell, Python, signing, or lifecycle ownership.

The RFC intentionally does not promise Windows 10, ARM64, other shells, or
runtime integration breadth. That may feel less comprehensive, but it prevents
a one-path installation commitment from silently becoming a general Windows
compatibility policy.

## Compatibility and impact

If accepted, the 1.0 compatibility promise gains one explicit native Windows
installation route and its stated prerequisites. Existing package scripts,
plugin boundaries, runtime ownership, configuration, routing, APIs, and
release behavior do not change.

A later separate implementation/documentation PR may add the canonical commands
to the appropriate installation surfaces, state the Windows 11 x86_64 and
WinGet prerequisites, explain `uv tool update-shell` and the new-session
requirement, and avoid assuming Python knowledge. That work must implement this
decision rather than redesign it.

## Proof expectations

Before a final 1.0 promise, a later validation should, within this RFC's scope:

1. start from a clean-HAC Windows 11 x86_64 environment with WinGet available;
2. install `uv` through the canonical explicit-source command;
3. install the final published HAC package with the ordinary unpinned `uv tool`
   command;
4. run `uv tool update-shell`, open a new PowerShell session, and confirm `hac`
   discovery and published version identity; and
5. complete one bounded ordinary HAC operation.

This does not add validation obligations outside the selected support boundary.

## Open questions

None within this proposed decision. Future evidence may justify a separate
proposal for another Windows version, architecture, shell, installation method,
or broader platform promise.

## Decision

Pending.
