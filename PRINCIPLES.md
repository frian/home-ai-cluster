# Principles

Status: Draft

This document defines the working principles of Home AI Cluster.

Principles are not features.

They are rules that guide decisions, reviews, implementation, and trade-offs.

When in doubt, the project should return to these principles.

---

## 1. User simplicity over developer convenience

Every architectural decision must make the system simpler for its users, even if it makes it harder for its developers.

This does not mean developers should accept unnecessary pain.

It means user clarity, safety, and control have higher priority than implementation shortcuts.

---

## 2. Local first

Home AI Cluster must work without requiring an external service.

No account should be required.

No cloud service should be required.

No hosted control plane should be required.

Cloud integration may exist later, but only as an explicit option.

Local operation is the default.

---

## 3. Privacy by default

Prompts should not be logged by default.

Responses should not be logged by default.

Request contents should not leave the local cluster unless explicitly allowed.

The safest default is:

> Do not collect what is not needed.

---

## 4. Capabilities over brand names

The cluster should reason about capabilities, not machine names, model names, runtime names, or vendor names.

A node announces what it can do.

The cluster matches requests to capabilities.

Models, runtimes, and hardware are implementation details.

---

## 5. Engine independence

Home AI Cluster must not depend on any specific AI runtime.

Runtime-specific behavior belongs behind adapters.

The core should remain stable even when engines, model formats, hardware, or vendors change.

---

## 6. Explicit boundaries

The user defines boundaries.

The cluster chooses within them.

The cluster may recommend.

The cluster may explain.

The cluster may automate allowed decisions.

But it must not silently expand its own authority.

Trust is more important than convenience.

---

## 7. Transparency over magic

Automatic decisions must be explainable.

The user should be able to understand:

* which node handled a request;
* why that node was selected;
* which capabilities were considered;
* what failed;
* what fallback was used.

The system should be helpful, not mysterious.

---

## 8. Boring solutions first

The project should prefer boring, understandable solutions.

A simple design that works is better than an elegant design nobody can operate.

Complexity is acceptable only when it makes the user experience simpler, safer, or more reliable.

Complexity must justify itself.

---

## 9. Small steps

Home AI Cluster should be built in small, verifiable steps.

The first meaningful proof is:

> One endpoint. Two machines. One routed request.

Large ideas are allowed.

Large jumps are not.

---

## 10. Documentation before architecture drift

Important decisions should be written down before they become hidden assumptions.

Questions belong in `QUESTIONS.md`.

Stable ideas belong in `FOUNDATIONS.md`.

User-facing direction belongs in `VISION.md`.

Deliberate refusals belong in `NON_GOALS.md`.

Long-term decisions belong in RFCs.

The repository is the memory of the project.

---

## 11. Agents implement decisions

AI coding agents may help implement the project.

They may write code.

They may refactor code.

They may suggest tests.

They may point out inconsistencies.

But they must not silently make architectural decisions.

Agents may implement decisions.

They must not own decisions.

Architecture belongs to the project.

---

## 12. Explainability test

Every major decision should be explainable to a developer in less than five minutes.

If a decision cannot be explained simply, it is probably not understood well enough.

Simple explanations are not a luxury.

They are a design requirement.


## Applying these principles

These principles guide not only the implementation of Home AI Cluster, but also the way it evolves.

When a decision is likely to shape a significant part of the codebase, the preferred workflow is:

1. Describe the decision in an RFC.
2. Review and refine the RFC.
3. Merge the RFC.
4. Implement the decision.

Small implementation details do not require RFCs.

Architectural decisions do.

The codebase is the implementation of architectural decisions.

RFCs preserve the reasoning behind those decisions.
