---
order: 97
---

# Windows Installation Path Investigation

Status: Investigation

Date: 2026-09-02

## Purpose and boundary

This documentation-only investigation asks whether a Windows 11 PowerShell
path using WinGet and `uv` is sufficient for the non-binding pre-1.0 direction
to have one supported low-friction Windows installation path.

It changes no installation guidance, package metadata, release process, CLI,
runtime, plugin, routing, configuration, or Windows behaviour. It neither
adopts an installation mechanism nor proposes an RFC. The observed
`1.0.0b2` result is evidence, not a promise about later releases or Windows in
general.

## Repository requirement and accepted boundaries

The 0.9 release direction requires one supported Windows path before 1.0 that
does not require a user to understand Python packaging or `uv` *before*
installing HAC. It deliberately leaves the delivery mechanism open. It requires
the resulting installation to preserve separately packaged plugins and says
that HAC must not become a runtime, model, SearXNG, firewall, service, or
external-provider lifecycle manager. A polished MSI, MSIX, or EXE is explicitly
not required for its own sake.

The current published-package path is `uv tool install home-ai-cluster`.
RFC-0052 also leaves ordinary Python packaging responsible for installation,
upgrade, uninstall, console-script locations, and PATH; it rejects an
HAC-owned installer, shell-profile mutation, and PATH mutation. RFC-0078's
accepted separately installed plugin boundary remains independent from ordinary
HAC installation. Nothing accepted defines a Windows support matrix, a WinGet
prerequisite, a supported shell set, or a Windows compatibility promise.

The release direction is not an architectural decision and explicitly retains
the RFC process for durable decisions. Therefore it supplies the product need,
not authority to choose the supported Windows contract.

## Observed evidence

On 2026-09-02, a clean-HAC Windows 11 Pro test VM with WinGet already available
successfully completed this PowerShell flow:

```powershell
winget install --id astral-sh.uv -e --source winget
uv tool install home-ai-cluster==1.0.0b2
uv tool update-shell
# open a new PowerShell session
hac --help
hac --version
hac config show
```

WinGet installed `uv 0.12.8` for `x86_64-pc-windows-msvc`. No manual Python
installation was performed. The package and dependencies installed from PyPI;
after `uv tool update-shell` and a new PowerShell session, the expected `hac`
command was available. `hac --version` reported `1.0.0b2`, and `hac config
show` displayed the initial unconfigured state.

The explicit WinGet source was necessary in this observation because an
unrelated Microsoft Store source certificate failure occurred first. That
environment-specific issue is not a HAC requirement or product finding.

Additional published-package smoke evidence exercised a Windows caller in a
static cluster with a remote Linux HAC node. `code-file` accepted absolute
drive-letter paths, Windows backslashes, and paths containing spaces. A valid
remote Code result replaced the selected local Windows file. A separate invalid
`code-file` response left its selected file unchanged. This supports the
observed caller path and existing code-file fail-closed behaviour; generated
code quality was not evaluated.

An older Linux `0.9.0.dev0` process emitted a historical cancellation traceback
during one remote test. It was not the published Windows candidate and is not
Windows or `1.0.0b2` regression evidence.

## Analysis

### Meaning of low friction

The direction does not require zero prerequisites or a native installer. It
requires one clear, supported sequence which an ordinary Windows user can
follow without already knowing Python packaging or `uv`. Telling that user one
literal command to install `uv` is materially different from requiring prior
knowledge of `uv`; the former supplies the missing knowledge in the
instructions, while the latter assumes it.

Within the observed boundary, WinGet is a reasonable prerequisite for that one
path. The direction requires one path, not a path that works on every Windows
installation without WinGet. It would be misleading, however, to imply Windows
10, Windows ARM64, other package sources, or shells other than a newly opened
PowerShell session without separate policy or evidence.

`uv tool update-shell` plus a shell restart is one visible setup action, but it
does not materially defeat low friction: `uv` reports the need, supplies its
own supported command, and explains the restart. It is less ownership than an
HAC script that edits a profile or PATH itself. Documentation must present it
plainly and include the restart; it must not promise that an existing shell
will immediately find `hac`.

The observed route preserves all current ownership boundaries. WinGet and `uv`
install their own software; HAC is an isolated published package and exposes
its existing scripts. HAC neither installs Python manually nor owns runtimes,
models, Ollama or llama-server lifecycle, firewall policy, external providers,
or plugin installation. Separately packaged plugins remain separately selected
and installed under the existing accepted boundary.

### Options compared

| Option | Fit with evidence and boundaries | Assessment |
| --- | --- | --- |
| A. Document WinGet → `uv` → `uv tool install` | Directly observed with the published candidate; uses existing upstream installation and PATH support; preserves package and plugin ownership. | Smallest credible mechanism. |
| B. HAC-owned PowerShell bootstrap | Would add maintenance, download-trust, execution-policy, version-drift, and Windows-testing obligations; risks owning prerequisite and profile orchestration already provided upstream. | Not justified by current evidence. |
| C. HAC-owned traditional installer/package | Could be useful later, but introduces artifact, signing, release, Python-bundling, update, and plugin-model decisions not required by the current direction. | Not required for 1.0 on present evidence. |
| D. Another mechanism | No repository or observed evidence identifies a simpler path than the tested upstream-tool route. | No candidate recommended. |

## Conclusion and decision boundary

**The observed evidence favors Option A as the smallest credible Windows
delivery mechanism. It is sufficient evidence to avoid treating an HAC-owned
bootstrap or traditional installer as a prerequisite for 1.0. It is not
sufficient authority to adopt Option A as the official supported path.**

Adoption would make a durable product and compatibility decision: HAC would
promise a particular Windows population a supported installation experience,
state a prerequisite (WinGet), identify a shell/path activation expectation,
and need to say what `1.0.x` preserves or excludes. The accepted RFCs define
the installed HAC commands and package/plugin boundaries, but not that Windows
support contract. The release direction expressly leaves this mechanism
undecided. Under the repository's RFC-before-architectural-decisions rule and
its 1.0 compatibility scrutiny, this requires a narrow RFC before user-facing
adoption.

The next step is therefore a focused RFC, not an installer or documentation
change. It should decide only the supported Windows installation contract: the
supported Windows version/architecture and PowerShell scope; whether WinGet is
an explicit prerequisite; the exact upstream `uv` and HAC commands; PATH and
shell-restart expectations; the relationship to upgrade, uninstall, and
separately installed plugins; and the explicit exclusions. It should preserve
all existing external lifecycle ownership. This investigation does not draft
that RFC.

## Remaining evidence and debt

Before a final 1.0 promise, the project needs the RFC decision above and then
validation against its accepted scope, at least a clean-HAC installation of the
final published release through the selected PowerShell path, command discovery
after shell restart, version identity, and one bounded ordinary operation.

The current observation does not establish every HAC command, every runtime,
native Windows runtime lifecycle, Windows service installation, firewall
automation, plugin installation, upgrade or uninstall behaviour, Windows ARM64,
Windows 10, or other shells. Those are not newly imposed requirements; they
remain outside this investigation unless the RFC chooses to promise them.
