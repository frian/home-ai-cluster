# Questions

Status: Draft

Home AI Cluster starts with questions, not answers.

This document exists to protect the project from premature implementation.

Before writing code, choosing technologies, designing APIs, or building features, we must be able to answer these questions clearly.

If a question cannot be answered simply, the project is not ready for that decision yet.

---

## 1. Why should Home AI Cluster exist?

What problem is real enough to justify this project?

Why is this not already solved by existing tools?

Why should someone care?

---

## 2. Who is it for?

Who is the first real user?

A developer?

A hobbyist?

A small team?

A privacy-conscious user?

Someone with one powerful machine?

Someone with many modest machines?

The project cannot serve everyone at first.

---

## 3. What is the simplest useful version?

What is the smallest version of Home AI Cluster that provides real value?

What can we remove and still keep the core idea alive?

What is the first version that makes someone say:

> “Ah, I get it.”

---

## 4. What does the user experience?

What should the user see?

What should the user never have to think about?

Should the user choose a machine?

Should the user choose a model?

Should the user know where the workload runs?

The user talks to the cluster, never to a machine.

---

## 5. What is the core abstraction?

Is Home AI Cluster about machines?

Models?

Capabilities?

Tasks?

Agents?

Resources?

The wrong abstraction will make the project complicated forever.

---

## 6. What does the cluster know?

What information does each node announce?

CPU?

GPU?

RAM?

Available models?

Current load?

Power state?

Network speed?

Capabilities?

How much knowledge is necessary, and how much is noise?

---

## 7. What should the cluster decide automatically?

Should it decide where a request runs?

Which model to use?

Whether to use one model or several?

Whether to fall back to another node?

Whether to reject a task?

Automation is only useful when it reduces user complexity.

---

## 8. What should remain explicit?

What decisions must stay under user control?

Privacy boundaries?

Allowed machines?

Allowed models?

Network access?

Resource limits?

Automatic behavior must never feel like loss of control.

---

## 9. What does Home AI Cluster refuse to be?

What will the project deliberately not do?

It is not an LLM.

It is not an inference engine.

It is not a model format.

It is not a cloud platform.

It is not Kubernetes for AI.

It is not tied to any specific runtime, vendor, or model.

What else must it refuse?

---

## 10. Why would someone use this instead of Ollama?

Ollama already makes local AI easy.

What does Home AI Cluster add?

Multiple machines?

Automatic discovery?

Capability routing?

Unified access?

Better resource usage?

A simpler mental model?

The answer must be obvious.

---

## 11. What does “local first” really mean?

Does it mean no cloud by default?

No external dependency?

No account required?

No telemetry?

No remote model execution unless explicitly configured?

Local first must be a design constraint, not a slogan.

---

## 12. What does “privacy by default” require?

What data moves between machines?

What data is stored?

What data is logged?

Can prompts leave the current machine?

Can prompts leave the local network?

Can a node inspect another node’s requests?

Privacy must be built into the architecture from the beginning.

---

## 13. What does engine independence mean?

How can the project work with Ollama, llama.cpp, vLLM, MLX, or future runtimes?

What is the minimum interface an engine must expose?

What should Home AI Cluster know about a runtime?

What should it deliberately ignore?

The project must not depend on any specific AI engine.

---

## 14. What is a capability?

Is “chat” a capability?

Is “vision” a capability?

Is “code” a capability?

Is “embedding” a capability?

Is “fast response” a capability?

Is “runs locally only” a capability?

The cluster should reason about capabilities, not brand names.

---

## 15. What is success in one week?

What can be achieved without writing production code?

A clear vision?

A first RFC?

A repository structure?

A working vocabulary?

A shared mental model?

Early success is clarity.

---

## 16. What is success in one month?

What should exist after the first month?

A minimal repository?

A documented architecture?

A prototype?

Two machines discovering each other?

A request routed from one node to another?

The goal must be small enough to finish.

---

## 17. What is success in one year?

What would make the project worth continuing?

A useful local orchestrator?

A small open source community?

A stable agent protocol?

A working dashboard?

Integration with developer tools?

The one-year vision should be ambitious but believable.

---

## 18. What must still be true in ten years?

Which ideas should survive changes in models, hardware, runtimes, and vendors?

Multiple machines should behave like one AI.

The user should not manage machines manually.

The architecture should remain understandable.

The project should stay local-first.

What else must never change?

---

## 19. What complexity are we willing to accept?

Every feature has a cost.

Discovery has a cost.

Scheduling has a cost.

Security has a cost.

Engine abstraction has a cost.

Distributed execution has a cost.

Which complexity helps the user?

Which complexity only flatters the developer?

---

## 20. How do we explain Home AI Cluster in 30 seconds?

If the project cannot be explained simply, it is not understood well enough.

A possible answer:

> Home AI Cluster lets you install an agent on your computers so they can work together as one personal AI. You keep using your tools as before. The cluster decides where the work runs.

This answer should improve as the project becomes clearer.
