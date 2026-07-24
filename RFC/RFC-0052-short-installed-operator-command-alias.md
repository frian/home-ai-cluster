# RFC-0052: Short Installed Operator Command Alias

Status: Accepted

Date: 2026-07-24

Author: frian

## Summary

Home AI Cluster should add `hac` as a backward-compatible installed console-script
alias for `home-ai-cluster`.

Both executable names will invoke the exact same
`home_ai_cluster.command:main` function and expose the same accepted unified
subcommand tree. `home-ai-cluster` remains fully supported and is not
deprecated. This is an operator-entry-point and packaging contract only; it
does not change command semantics or cluster behavior.

This RFC amends RFC-0050 only where necessary to allow that additional installed
executable name. RFC-0050 remains authoritative for the unified command's
subcommands, parser, delegation, help, version, output, failure, privacy, and
lifecycle boundaries.

## Problem

The unified command already gives ordinary operations one coherent namespace,
but its executable name is cumbersome for repeated ordinary use. In a checkout,
an operator commonly types:

```sh
uv run home-ai-cluster preflight
```

Ordinary package installation already removes the `uv run` prefix, allowing:

```sh
home-ai-cluster preflight
```

It does not remove the reported repeated typing friction of the long executable
name. The operator need is for a short installed entry point, not a new
subcommand, different preflight behavior, or another cluster workflow.

The following concepts remain distinct:

1. `uv run home-ai-cluster preflight` executes the project command in a
   checkout's development environment.
2. `home-ai-cluster preflight` is the existing installed console script when
   ordinary packaging has made it available on `PATH`.
3. `hac preflight` is the proposed repository-owned installed console-script
   alias.
4. An operator-owned shell alias is external local convenience; it is not a
   portable repository contract.

## Goals

This RFC should:

* add exactly one short installed alias, `hac`;
* preserve `home-ai-cluster` as the fully supported canonical command;
* make both names invoke the exact same unified command implementation;
* preserve help, version, valid forwarding, invalid-command and invalid-argument,
  standard-output, standard-error, and exit-status behavior; and
* leave ordinary Python packaging tooling responsible for installation.

## Non-goals

This RFC does not add or change:

* `hacc`, both short aliases, a general executable-naming strategy, or an alias
  framework;
* renaming, removing, deprecating, warning on, or migrating
  `home-ai-cluster`;
* a second parser, command tree, shell wrapper, repository-managed symlink,
  custom installer, shell-profile mutation, automatic `PATH` mutation, or
  virtual-environment activation machinery;
* new subcommands or existing command semantics;
* routing, topology, runtime adapters, transport, fallback, privacy,
  persistence, status, health, or lifecycle behavior;
* lifecycle management, service installation, process supervision, a dashboard,
  Docker, or Kubernetes; or
* a roadmap phase or Phase 19.

## Proposal

### One backward-compatible alias

After later implementation, the package's console-script declarations will
conceptually include:

```toml
[project.scripts]
home-ai-cluster = "home_ai_cluster.command:main"
hac = "home_ai_cluster.command:main"
```

`hac` will delegate to the exact same `home_ai_cluster.command:main` function
as `home-ai-cluster`. It will not add a parser, dispatch table, module, wrapper,
or command implementation. The accepted seven root subcommands—`local`,
`static-cluster`, `compatibility`, `chat`, `preflight`, `health`, and `status`—
remain available through both executable names. Existing standalone commands
remain supported unchanged.

Both names preserve the accepted root behavior: help is equivalent; the
package-version-only `--version` behavior is equivalent; valid arguments are
forwarded equivalently; invalid commands and arguments behave equivalently; and
stdout, stderr, and exit status remain command-owned and equivalent.

### Installation ownership and collisions

Ordinary Python packaging tooling owns installation, upgrade, uninstall, and
the console-script locations it exposes. An ordinary installation must expose
both declared scripts. This RFC does not prescribe a custom installer or alter
the operator's `PATH`.

`hac` can collide with an executable in an operator's environment. The project
does not promise global name uniqueness or manage that collision. The fully
supported canonical `home-ai-cluster` command remains the explicit fallback.

## Rationale

`hac` directly abbreviates “Home AI Cluster.” It is shorter and more memorable
than `hacc`; the second `c` adds no distinct project meaning and creates an
extra spelling and typo opportunity. One alias addresses the reported repeated
use need without alias proliferation.

Keeping `home-ai-cluster` fully supported bounds the consequence of a local
`hac` collision without claiming that the short name is globally free. Directly
declaring both scripts against the same existing entry point is the smallest,
most transparent packaging shape. It preserves the command ownership,
local-first, privacy, and lifecycle boundaries accepted in RFC-0050.

## Alternatives considered

### Keep only `home-ai-cluster`

Ordinary installation removes `uv run`, but not the reported friction from
repeatedly typing the long executable name. Documentation alone is therefore
not a complete response to this concrete need.

### Add `hacc`

Rejected. It is longer, less immediately memorable, and adds no meaning beyond
the direct “Home AI Cluster” initialism.

### Expose both `hac` and `hacc`

Rejected. Two aliases for one purpose divide recall and enlarge a durable
namespace without distinct operator value.

### Rename or remove `home-ai-cluster`

Rejected. It would replace an accepted public executable contract and create a
compatibility migration where a backward-compatible alias suffices.

### Shell aliases, wrappers, symlinks, or custom installation

Rejected. These introduce shell, operating-system, installation, or ownership
assumptions beyond a standard Python console-script declaration. Operators may
still own their personal shell aliases outside the repository.

## Trade-offs

The alias makes repeated ordinary command use shorter while preserving an
explicit canonical fallback. It also adds one durable executable-name contract
and a possible environment-specific collision. That cost is limited by keeping
one alias, retaining the long command, and delegating to the same established
function rather than creating another command surface.

## Impact

A later implementation may add one `hac` console-script declaration and focused
packaging and compatibility tests. It must not change the existing root parser,
unified subcommand tree, standalone command implementations, package name,
dependencies, or cluster behavior.

The implementation proof must establish that:

1. package metadata declares both executable names;
2. both resolve to the exact same Python entry point;
3. an isolated ordinary installation exposes both scripts;
4. `home-ai-cluster --help` and `hac --help` have compatible behavior;
5. `home-ai-cluster --version` and `hac --version` have compatible behavior;
6. representative successful subcommands have matching stdout, stderr, and
   exit status;
7. invalid subcommands and invalid arguments have matching behavior;
8. all accepted root subcommands remain reachable through `hac`;
9. existing standalone scripts remain available; and
10. no second parser, wrapper, installer, shell mutation, dependency, or
    cluster behavior is introduced.

This proof requires no live runtime, network access, two-machine proof, or
physical cluster proof.

## Open questions

None for this narrow decision. Ordinary environment-specific executable
collisions remain outside repository ownership; the canonical long command is
the supported fallback.

## Decision

Accepted.

`hac` is the single accepted backward-compatible short installed alias for
`home-ai-cluster`. `home-ai-cluster` remains canonical, fully supported, and
not deprecated. Both executable names must delegate to the exact same
`home_ai_cluster.command:main` unified entry point.

Any later implementation is limited to packaging metadata, focused
compatibility tests, and minimal installation documentation where justified. No
implementation is included in this acceptance change, and this decision creates
no Phase 19.
