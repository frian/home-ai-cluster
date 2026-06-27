# Contributing

Status: Draft

Home AI Cluster is built in small, understandable steps.

The project values clear decisions, boring solutions, local-first design, privacy by default, and architecture that can still be understood years later.

Contributing to Home AI Cluster is not only about adding code.

It is also about preserving the reasoning behind the code.

---

## Project philosophy

Home AI Cluster exists to make multiple personal computers behave like one local AI system.

The guiding idea is:

> Many machines. One AI.

The user should talk to the cluster, never to a machine.

This project should remain:

* local-first;
* privacy-first;
* engine-independent;
* capability-centered;
* understandable;
* useful to personal users before infrastructure teams.

When contributing, prefer simple designs that make the system easier to understand and easier to trust.

A clever solution is not automatically a good solution.

A boring solution that works clearly is usually better.

---

## How we work

The project is developed through small, reviewable changes.

The preferred workflow is:

```text
discussion
  -> branch
  -> change
  -> draft pull request
  -> review
  -> merge
```

For architectural decisions, the workflow is:

```text
discussion
  -> RFC
  -> draft pull request
  -> review
  -> merge
  -> implementation
```

Code should implement decisions.

It should not hide them.

If an important decision only exists in code, it is too easy to lose the reasoning behind it.

---

## Before writing code

Before implementing a change, ask:

> Is this an architectural decision?

If the answer is no, a normal pull request is enough.

If the answer is yes, write or update an RFC first.

A decision probably deserves an RFC when it affects:

* core architecture;
* agent or orchestrator responsibilities;
* node discovery;
* capability modeling;
* runtime adapter interfaces;
* routing behavior;
* privacy boundaries;
* configuration format;
* protocol design;
* long-term compatibility.

Small implementation details do not require RFCs.

Architectural decisions do.

The goal is not to create bureaucracy.

The goal is to make important decisions visible before they disappear into code.

---

## RFCs

RFCs live in the `RFC/` directory.

An RFC should explain:

* the problem;
* the proposed decision;
* the reasoning;
* the alternatives considered;
* the trade-offs;
* the impact;
* the open questions.

An RFC is not a TODO list.

An RFC is not a blog post.

An RFC is not user documentation.

An RFC is project memory.

A good RFC should be understandable months or years later by someone who was not part of the original discussion.

---

## Branches

Use branch names that describe the intent of the change.

Examples:

```text
rfc-0003-runtime-adapter-interface
docs-contributing
bootstrap-python-project
feature-static-node-registry
fix-routing-explanation
refactor-adapter-interface
```

Prefer specific names over vague names.

Avoid names like:

```text
changes
misc
work
temp
fixes
```

A branch name should help someone understand what kind of change to expect.

---

## Pull requests

Pull requests should be small enough to review comfortably.

A pull request should usually represent one coherent idea.

Examples:

* add one RFC;
* document one workflow;
* bootstrap the Python project;
* add one adapter interface;
* implement one routing behavior;
* fix one bug.

A pull request should explain what changed and why.

A good pull request makes review easier.

A good pull request also makes future archaeology easier.

Someone reading the project history should be able to understand how the project evolved.

---

## Draft pull requests

Draft pull requests are useful for work that is still being shaped.

Use a draft pull request when:

* an RFC is being discussed;
* a design is not final;
* feedback is expected before merge;
* the change should be visible before it is ready.

A draft pull request is not a failure state.

It is a workspace.

When the change is ready, mark it as ready for review, then merge it when accepted.

---

## Commits

Each commit should represent one coherent idea.

A commit message should answer:

> What does this commit add, change, or fix?

Good examples:

```text
Add RFC-0003 runtime adapter interface
Document architecture-before-implementation workflow
Bootstrap Python project
Implement static node registry
Add Ollama runtime adapter
Fix node capability matching
```

Avoid vague messages:

```text
changes
misc
work
temp
fixes
```

The Git history should read like the story of the project.

---

## Reviews

Reviews should protect clarity, but they should also protect contributors.

A review is not a test of authority.

It is a conversation about how to make the project better.

When reviewing a change, ask:

* Is the change understandable?
* Does it respect the project principles?
* Does it make the system simpler for the user?
* Does it preserve local-first and privacy-first defaults?
* Does it keep runtime-specific details behind adapters?
* Does it introduce complexity that is justified?
* Should this have been an RFC?

When giving feedback, prefer explanations over commands.

Good review comments help the contributor understand the reasoning behind the suggestion.

A useful review says not only:

> Change this.

but also:

> This may be clearer because...

Assume good intent.

Ask questions before assuming mistakes.

Be direct when something matters, but remain kind.

Review is not only about finding problems.

Review is also how the project protects its direction, teaches its values, and helps contributors do better work.

---

## Keep it boring

Home AI Cluster should prefer boring, understandable solutions.

If a solution feels clever, look for a simpler one.

Complexity is acceptable only when it makes the user experience simpler, safer, or more reliable.

Do not add infrastructure because it is fashionable.

Do not add abstraction because it feels elegant.

Do not add process because large projects do it.

Start small.

Make the decision explicit.

Implement the smallest useful version.

Then improve it.

---

## AI coding agents

AI coding agents may help implement the project.

They may write code, suggest tests, refactor, and point out inconsistencies.

But they must not silently make architectural decisions.

Architectural decisions belong to the project.

Agents may implement decisions.

They must not own decisions.

When an AI-generated change introduces or assumes an architectural decision, that decision should be made explicit, usually through an RFC.

---

## Final rule

A contributor should be able to understand why the project is built this way, not only how it is built.

The codebase shows what Home AI Cluster does.

The documentation and RFCs explain why it does it that way.
