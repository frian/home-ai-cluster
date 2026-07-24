# Short Operator Command Investigation

Status: Investigation only

## Purpose and authority

This investigation records one privacy-safe repeated-use operator need after
the post-Phase-18 direction investigation. It does not accept a command name,
change packaging, amend an RFC, authorize implementation, or create a roadmap
phase. Accepted RFCs, especially RFC-0050, remain authoritative.

The reported need is concrete:

> Ordinary daily use should not require typing
> `uv run home-ai-cluster preflight`.
>
> The operator wants a short installed command such as `hac preflight` or
> `hacc preflight`.

This is repeated-use friction over the executable entry point, not over
preflight behavior. The existing unified `home-ai-cluster` command already
owns the `preflight` subcommand semantics. The report asks for no new
subcommand, cluster behavior, routing behavior, or runtime behavior. `hac` and
`hacc` are candidate executable names, not selected names.

## Established baseline

`pyproject.toml` declares the Python package `home-ai-cluster` and exposes its
unified console script as:

```toml
home-ai-cluster = "home_ai_cluster.command:main"
```

The command implementation has an explicit seven-command dispatch table.
`preflight` is one of those exact subcommands and delegates directly to
`static_preflight.main`; it does not implement a second preflight path. Focused
tests establish that root delegation preserves the delegated command's
arguments, output, exit behavior, and command-owned execution.

In a repository checkout, ordinary development use can invoke the unified
surface through:

```sh
uv run home-ai-cluster preflight
```

The canonical workflow also retains the longer standalone
`uv run home-ai-cluster-preflight` form. RFC-0050 deliberately keeps that and
the other standalone scripts supported. Several longer standalone historical,
proof, diagnostic, and specialized commands remain declared in
`pyproject.toml`; this investigation concerns only the ordinary unified entry
point.

Four related but different concepts must remain separate:

1. **Python package console-script name.** A `[project.scripts]` entry asks
   Python packaging to create an executable with that name, pointing to a
   package function.
2. **`uv run` in a checkout.** `uv run home-ai-cluster preflight` resolves and
   runs the project command in the development environment. It is a useful
   repository workflow, not evidence that a short executable has been
   installed for general shell use.
3. **Installed command on `PATH`.** After an ordinary tool or package
   installation places its scripts directory on the operator's `PATH`, the
   existing command can be invoked as `home-ai-cluster preflight` without
   `uv run`.
4. **External shell aliases or wrappers.** An operator can define an alias or
   wrapper outside this repository. Such local convenience is neither a Python
   package console script nor a portable repository-owned operator contract.

No command semantics, routing, topology, runtime, transport, fallback,
privacy, persistence, or lifecycle behavior needs to change to satisfy the
reported friction.

## Is a repository change required?

Ordinary installation already removes the `uv run` prefix. For example, an
operator can install the package as a tool (including from a local checkout
with `uv tool install .`), or use another ordinary Python package installation
model, then ensure that tool environment's script directory is on `PATH`. The
packaging tool owns executable creation, upgrades, reinstalls, and uninstall;
the repository need not create an installer, mutate shell profiles, activate a
virtual environment, copy wrappers, manage symlinks, or supervise a service.

The commands therefore differ as follows:

| Form | What it requires | What it solves | What it does not solve |
| --- | --- | --- | --- |
| `uv run home-ai-cluster preflight` | Checkout plus `uv` project execution. | Uses the existing unified command during development. | Repeated long executable name; installed-shell access. |
| `home-ai-cluster preflight` | Ordinary installation and its scripts directory on `PATH`. | Removes `uv run`; preserves all accepted unified semantics. | The reported executable-name length. |
| `hac preflight` | A new package console-script alias, or operator-owned external alias. | Removes the reported repeated typing when repository-owned. | Nothing about installation, runtime, or preflight itself. |
| `hacc preflight` | A new package console-script alias, or operator-owned external alias. | Same potential shortening. | Nothing about installation, runtime, or preflight itself. |

Installation documentation is independently useful because it makes the
existing long installed command available without `uv run`. It is not, by
itself, a complete response to the stated daily typing friction. Renaming the
canonical command is not necessary: a backward-compatible alias can address
the precise need while preserving all accepted forms.

## Canonical command and alias options

| Option | Operator friction | Compatibility | Implementation size | Contract impact | Collision or ambiguity risk | RFC implication | Recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Keep only `home-ai-cluster` | Removes `uv run` after installation, but keeps the long repeated executable. | Complete preservation. | Documentation only. | No new executable contract. | Lowest repository-owned name risk. | No RFC for installation documentation alone. | Insufficient for the recorded need unless the operator withdraws the need. |
| Add `hac` | Short, direct everyday form. | Preserves `home-ai-cluster` and all unified subcommands. | One additional script entry and focused compatibility tests. | One durable alias contract. | A short three-letter name may collide; no universal freedom can be claimed. | Narrow RFC required before implementation. | Preferred. |
| Add `hacc` | Shorter than the canonical form but has an additional typed character. | Preserves `home-ai-cluster` and all unified subcommands. | Same as `hac`. | One durable alias contract. | May be less likely to collide, but double-`c` creates a typo and recall risk. | Narrow RFC required before implementation. | Do not select absent evidence that the extra character helps. |
| Rename the canonical command | Could shorten ordinary typing. | Breaks or requires migration for the accepted root executable and documentation. | Larger than an alias because references and compatibility policy must change. | Replaces a durable accepted command identity. | Still needs a new name decision. | Broader RFC and migration decision required. | Reject. |

Do not expose both `hac` and `hacc`. They serve the same purpose, divide recall,
and multiply the durable namespace without evidence of distinct value.

## Candidate-name assessment

`hac` is the direct initialism of “Home AI Cluster.” It is shorter, readily
spoken as individual letters, and communicates the project sufficiently once
seen next to the long canonical command. `hacc` does not add a project word or
meaning beyond `hac`; its extra `c` is easy to omit, and its pronunciation and
spelling are less immediately obvious.

A local `PATH` check in the investigation environment found neither `hac` nor
`hacc`. That is only a local observation, not evidence of global availability,
trademark status, package-index availability, or collision freedom. In
particular, `hac` is a common short acronym and may collide in some operator
environments. Any eventual RFC should acknowledge that ordinary executable-name
collisions remain an operator-environment concern and preserve the canonical
long command as the unambiguous alternative. The repository should not perform
ecosystem-wide naming research or promise collision-free installation.

Across supported Python packaging environments, both names are ordinary
console-script names. Portability therefore does not distinguish them
materially. The extra character in `hacc` supplies no demonstrated clarity that
outweighs its memorability and typo cost. This evidence favors one alias,
`hac`, rather than `hacc` or both.

## Installation ownership

The smallest ordinary installation model is standard Python packaging:

* `uv tool install` can install a package and its declared console scripts;
  `uv tool install .` is suitable for a local checkout, while a published
  distribution could be installed by package name.
* An editable development installation is appropriate when an operator needs a
  checkout's changing sources; it is development convenience, not a new
  runtime mode.
* A normal package installation also generates the declared scripts in that
  environment. The operator, Python environment manager, and operating system
  own whether the appropriate scripts directory is on `PATH`.
* The selected packaging tool owns upgrades, reinstalls, and uninstalls. The
  repository should document the supported ordinary commands where useful but
  should not add its own updater or removal logic.

The repository's only possible ownership addition is one declared Python
console-script alias pointing to the exact existing unified `main` function.
It must not add a custom installer, shell-profile mutation, automatic virtual
environment activation, copied wrapper, symlink manager, daemon installation,
or service supervision.

## Compatibility boundary and proof obligations

If a later RFC accepts one alias, both `home-ai-cluster` and the alias must call
the same `home_ai_cluster.command:main` function. There must be no second
command tree, renamed Python module, altered subcommand parser, or changed
standalone command.

The minimum credible implementation proof would verify that:

* `home-ai-cluster preflight` and `hac preflight` invoke the same delegated
  implementation and have matching standard output, standard error, and exit
  status;
* all currently supported root-command behavior, including help and
  invalid-subcommand handling, matches through both executable names;
* every existing unified subcommand remains available with unchanged argument
  parsing, validation, output, failure behavior, and exit codes;
* package installation exposes both expected scripts, and an ordinarily
  installed command works without `uv run`; and
* existing standalone commands remain supported.

This is an operator-entry-point concern. It requires no two-machine proof
unless later evidence identifies a real interaction, and it must not introduce
new command semantics.

## Architectural status and next artifact

Adding a second console-script declaration is mechanically small, but it is a
durable operator-interface decision. RFC-0050 defines `home-ai-cluster` as the
one installed root command, specifies exact accepted command grammar, and
explicitly rejected aliases without evidence. The present report supplies
evidence to investigate one alias; it does not amend that accepted decision.

An RFC is therefore required before implementation. The exact next artifact is
a narrow RFC that proposes `hac` as a backward-compatible console-script alias
for `home-ai-cluster`, defines its delegation and compatibility contract,
retains `home-ai-cluster` as supported, and scopes packaging-installation
documentation and proof. It should not draft a new command framework, alter
subcommands, rename the Python package, or add a roadmap phase.

## Non-goals

This investigation excludes a new CLI framework; new subcommands; summarize
CLI access; renaming the Python package; removing `home-ai-cluster`; changing
standalone historical commands; command-semantic changes; shell completion
unless already automatic and relevant; configuration changes; runtime lifecycle
management; process supervision; a dashboard; Docker or Kubernetes; and any
cluster architecture change.

This work is not a roadmap phase and does not define Phase 19.

## Recommendation

Add hac as a backward-compatible alias for home-ai-cluster.
