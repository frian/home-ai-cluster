# Questions

Status: Complete

This is the completed historical founding worksheet for Home AI Cluster. Its
questions record how the project was framed in June 2026 before the architecture
was established. They are not current requirements, an unresolved backlog, or
implementation authorization.

The original provisional working answers were superseded by later accepted
decisions and are not retained as current guidance. Their full historical text
remains available in Git history:

- `587c973` — original founding questions
- `38e446c` — provisional working answers

## Historical founding questions

### 1. Why should Home AI Cluster exist?

What problem is real enough to justify the project, why is it not already solved
by existing tools, and why should someone care?

### 2. Who is it for?

Who is the first real user, and which users should the project not try to serve
at first?

### 3. What is the simplest useful version?

What is the smallest version that provides real value while keeping the core
idea understandable?

### 4. What does the user experience?

What should the user see, and what should they not have to think about when
using the cluster?

### 5. What is the core abstraction?

Should the project be organized around machines, models, capabilities, tasks,
agents, or resources?

### 6. What does the cluster know?

What information about participating systems is necessary, and what would be
noise?

### 7. What should the cluster decide automatically?

Which decisions reduce user complexity without reducing user control?

### 8. What should remain explicit?

Which decisions must remain under user control, especially around privacy,
network access, and boundaries?

### 9. What does Home AI Cluster refuse to be?

Which deliberate refusals protect the project from unnecessary complexity and
scope drift?

### 10. Why would someone use this instead of Ollama?

What distinct value should Home AI Cluster provide alongside local AI runtimes?

### 11. What does “local first” really mean?

What makes local-first an architectural constraint rather than a slogan?

### 12. What does “privacy by default” require?

What data movement, storage, logging, and network boundaries must privacy
shape?

### 13. What does engine independence mean?

How can the project remain independent of particular AI runtimes while using
their capabilities?

### 14. What is a capability?

What cluster-facing concept should describe what the system can do for a user?

### 15. What is success in one week?

This was a time-bound founding milestone question whose period has completed.
See the completed [roadmap](ROADMAP.md).

### 16. What is success in one month?

This was a time-bound founding milestone question whose period has completed.
See the completed [roadmap](ROADMAP.md).

### 17. What is success in one year?

This was a time-bound founding milestone question whose period has completed.
See the completed [roadmap](ROADMAP.md).

### 18. What must still be true in ten years?

This remains an enduring prompt. Current guidance belongs in the stable project
documents below.

### 19. What complexity are we willing to accept?

This remains an enduring prompt. Current guidance belongs in the stable project
documents below.

### 20. How do we explain Home AI Cluster in 30 seconds?

How should the project be explained simply enough to make its purpose clear?

## Authoritative current context

- [Vision](VISION.md) — the project’s user-facing direction.
- [Foundations](FOUNDATIONS.md) — the stable ideas behind the project.
- [Principles](PRINCIPLES.md) — the rules for decisions, reviews, and trade-offs.
- [Non-goals](NON_GOALS.md) — deliberate scope refusals.
- [Roadmap](ROADMAP.md) — the completed formal progression and founding milestone.
- [Project README](README.md) — current product shape and operator entry points.
- [RFC index](RFC/README.md) — the archive of proposed and accepted architectural decisions.
- [Documentation index](docs/README.md) — current operator guidance and retained project records.

These documents, especially accepted RFCs, are authoritative for current
architecture. This historical worksheet does not replace them.
