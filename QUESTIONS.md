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


## Working Answers

Status: Draft

These answers are intentionally provisional.

They are not specifications yet.

They exist to clarify the project before architecture and implementation decisions are made.

---

## 1. Why should Home AI Cluster exist?

Home AI Cluster should exist because personal AI is currently limited by the boundaries of individual machines.

Many developers and hobbyists already own several computers: a desktop, a laptop, a mini PC, a NAS, a Raspberry Pi, or an old workstation.

Each machine has resources.

Each machine can run something.

But current local AI tools usually treat each machine as an isolated island.

Home AI Cluster exists to make these machines work together as one personal AI infrastructure.

The problem is not only performance.

The problem is mental model.

The user should not have to ask:

* Which machine has this model?
* Which machine has enough RAM?
* Which machine is currently free?
* Which endpoint should I call?
* Which runtime should I use?

The user should ask the cluster.

The cluster should decide.

Home AI Cluster is justified if it makes local AI simpler, more powerful, and more understandable for people who already own multiple machines.

---

## 2. Who is it for?

The first user is a technical individual who wants local AI but owns more than one machine.

This user is likely:

* a developer;
* a Linux user;
* a self-hosting enthusiast;
* a privacy-conscious user;
* a hobbyist experimenting with local models;
* someone with several modest machines rather than one perfect machine.

The first user is not a large company.

The first user is not a cloud provider.

The first user is not someone who wants a fully managed AI platform.

The first user understands enough to install an agent, read logs, and run local AI tools, but does not want to manually orchestrate machines forever.

Home AI Cluster should eventually become simple enough for non-experts, but it should not start there.

The first target is:

> A developer who already uses local AI and wants all their computers to behave like one assistant.

---

## 3. What is the simplest useful version?

The simplest useful version is not a distributed LLM.

The simplest useful version is a local orchestrator that can discover available AI nodes and route a request to one of them.

A first useful version could do only this:

1. Run an agent on two machines.
2. Each agent announces itself.
3. Each agent reports available models and basic capabilities.
4. The orchestrator receives a chat request.
5. The orchestrator chooses a node.
6. The request runs on that node.
7. The answer is returned through one unified API.

That is enough to prove the core idea.

No dashboard is required.

No automatic model download is required.

No complex scheduling is required.

No multi-model reasoning is required.

No distributed tensor execution is required.

The first useful version should make someone say:

> “I can send one request to the cluster, and it finds the right machine.”

That is the seed of the project.

---

## 4. What does the user experience?

The user experiences one AI endpoint.

The user should not experience a list of machines.

The user should not manually choose a node for every request.

The user should not need to know where the workload runs.

The ideal experience is:

1. Install an agent on each machine.
2. Start the orchestrator.
3. See the machines appear.
4. Send AI requests to one endpoint.
5. Let the cluster choose where work runs.

The user may inspect what happened.

But inspection is different from control.

The default experience should be simple.

The advanced experience should be transparent.

The user should be able to ask:

* Which node handled this request?
* Why was this node selected?
* Which capabilities were considered?
* What failed?
* What fallback was used?

But they should not need to answer those questions before using the system.

The guiding motto is:

> The user talks to the cluster, never to a machine.

---

## 5. What is the core abstraction?

The core abstraction is not the machine.

The core abstraction is not the model.

The core abstraction is the capability.

Machines are physical resources.

Models are implementation details.

Runtimes are replaceable.

Capabilities describe what the cluster can do.

Examples of capabilities:

* chat;
* code assistance;
* embeddings;
* vision;
* summarization;
* tool calling;
* fast response;
* large context;
* low memory usage;
* private local execution;
* high quality reasoning.

A node should announce capabilities.

The orchestrator should reason about capabilities.

A user request should be matched to capabilities.

This keeps the project independent from specific models, runtimes, vendors, and hardware.

Instead of asking:

> Which machine runs Qwen?

The cluster should ask:

> Which node can handle this kind of task well enough, under the current constraints?

This abstraction is central.

If Home AI Cluster gets this wrong, the project will become complicated forever.

## 6. What does the cluster know?

The cluster should know enough to make useful decisions, but not so much that it becomes noisy, invasive, or fragile.

Each node should announce a small set of facts.

At minimum:

* node name;
* availability;
* supported capabilities;
* available runtimes;
* available models;
* basic memory information;
* basic hardware information;
* current load;
* network address;
* health status.

The cluster does not need to know everything.

It does not need to know every process running on a node.

It does not need to inspect user files.

It does not need to collect unnecessary system details.

A node should describe what it can do, not expose everything it is.

The cluster should know:

> “This node can run chat models, has these capabilities, is currently available, and can accept this kind of task.”

That is enough for early versions.

More detailed information can come later, but only when it helps the user.

---

## 7. What should the cluster decide automatically?

The cluster should decide things that reduce user complexity.

It should be able to decide:

* which node should handle a request;
* which available capability matches the request;
* which runtime adapter should be used;
* whether a node is currently unavailable;
* whether another node should be used as fallback;
* whether a task should be rejected because no node can handle it.

The cluster should not try to be magical.

Automatic decisions must be explainable.

If the cluster chooses a node, it should be possible to ask why.

A good automatic decision is one that makes the user think less without making them feel less in control.

The cluster should automate routing.

It should not hide reality.

---

## 8. What should remain explicit?

Some decisions must remain under user control.

The user should explicitly control:

* which machines are allowed to join the cluster;
* which runtimes are enabled;
* which models are available;
* whether requests may leave the local network;
* whether cloud providers are allowed;
* whether prompts may be logged;
* resource limits;
* privacy boundaries;
* destructive actions;
* automatic downloads;
* automatic updates.

The cluster may recommend.

The cluster may explain.

The cluster may choose among allowed options.

But it must not silently expand its own authority.

Automatic behavior must stay inside boundaries chosen by the user.

Trust is more important than convenience.

---

## 9. What does Home AI Cluster refuse to be?

Home AI Cluster refuses to be another LLM.

It refuses to be another inference engine.

It refuses to be another model format.

It refuses to be a cloud platform.

It refuses to be Kubernetes for AI.

It refuses to require a specific vendor, runtime, model, or hardware platform.

It refuses to make simple local AI harder.

It refuses to hide important decisions behind magic.

It refuses to optimize for enterprise complexity before personal usefulness.

Home AI Cluster should not compete with Ollama, llama.cpp, vLLM, MLX, or future runtimes.

It should connect them.

It should orchestrate them.

It should make them easier to use together.

The project must remain focused on one question:

> How can multiple personal computers behave as one AI?

Anything that does not serve that question belongs outside the core.

---

## 10. Why would someone use this instead of Ollama?

Ollama makes local AI simple on one machine.

Home AI Cluster should make local AI simple across many machines.

That is the difference.

Someone would use Home AI Cluster if they have more than one computer and want:

* one endpoint instead of many;
* automatic node discovery;
* capability-based routing;
* fallback between machines;
* better use of idle hardware;
* a unified view of available local AI resources;
* runtime independence;
* a simpler mental model.

Ollama answers:

> “How do I run a model locally?”

Home AI Cluster answers:

> “How do all my computers work together as one local AI?”

The project should integrate with tools like Ollama, not replace them.

If Home AI Cluster cannot explain its value without attacking existing tools, the value is not clear enough.

The goal is not to be better than Ollama.

The goal is to make multiple Ollama-like environments, llama.cpp servers, and future runtimes feel like one coherent personal AI system.

## 11. What does “local first” really mean?

Local first means that Home AI Cluster should work without requiring any external service.

No account should be required.

No cloud service should be required.

No internet connection should be required for normal operation once the necessary software and models are installed.

The default assumption is:

> The cluster runs on machines owned or controlled by the user.

Local first does not mean cloud providers can never be supported.

It means cloud execution must be optional, explicit, and outside the default path.

A user should be able to install Home AI Cluster on a private network and use it without anything leaving that network.

Local first is not a marketing phrase.

It is an architectural constraint.

If a feature requires an external service, it must be treated as optional.

If a feature breaks offline usage, it does not belong in the core.

---

## 12. What does “privacy by default” require?

Privacy by default means that Home AI Cluster must minimize data movement, data storage, and data exposure.

Prompts should not be logged by default.

Responses should not be logged by default.

Request contents should not leave the local cluster unless the user explicitly allows it.

Nodes should not inspect more information than they need.

The orchestrator should know how to route a task, not everything about the user.

The system should make privacy boundaries visible and understandable.

A user should be able to answer:

* Where can my prompt go?
* Which machines can process it?
* Is anything stored?
* Is anything sent outside my network?
* Which runtime handled the request?

Privacy cannot be added later as a layer.

It must shape the architecture from the beginning.

The safest default is:

> Do not collect what is not needed.

---

## 13. What does engine independence mean?

Engine independence means that Home AI Cluster must not be built around one specific AI runtime.

Ollama may be supported.

llama.cpp may be supported.

vLLM may be supported.

MLX may be supported.

Future runtimes should be supportable without redesigning the project.

The orchestrator should not care how a model is executed internally.

It should care about what a node can do.

A runtime adapter should translate between Home AI Cluster and a specific engine.

The core should speak in terms of:

* capabilities;
* requests;
* constraints;
* results;
* health;
* availability.

The core should not speak in terms of one vendor’s API as if it were the architecture.

Engine independence protects the project from fashion, churn, and vendor lock-in.

Today’s favorite runtime may not be tomorrow’s best option.

Home AI Cluster should survive that.

---

## 14. What is a capability?

A capability is something the cluster can do for the user.

It is not a model name.

It is not a machine name.

It is not a runtime name.

Examples of capabilities include:

* chat;
* code assistance;
* embeddings;
* vision;
* summarization;
* tool calling;
* long context;
* fast response;
* high quality reasoning;
* local-only execution;
* low memory execution;
* structured output.

Capabilities should help the orchestrator match a request to a suitable node.

A capability may describe a function:

> This node can generate embeddings.

A capability may describe a quality:

> This node can provide fast responses.

A capability may describe a constraint:

> This node can process requests without leaving the local network.

Capabilities should be simple enough to understand, but precise enough to guide routing decisions.

The cluster should not ask first:

> Which model should run this?

It should ask:

> What does this request need?

Then it should find the best available node that can satisfy those needs.

---

## 15. What is success in one week?

Success in one week is clarity.

Not code.

Not a prototype.

Not a dashboard.

Not an architecture diagram with too many boxes.

The first week should produce a shared understanding of the project.

A successful first week may include:

* `QUESTIONS.md`;
* initial working answers;
* `FOUNDATIONS.md`;
* `VISION.md`;
* `PRINCIPLES.md`;
* `NON_GOALS.md`;
* a minimal repository structure;
* a clear vocabulary;
* a first definition of the smallest useful version.

The goal is to make future decisions easier.

If after one week we can explain Home AI Cluster clearly in 30 seconds, the week succeeded.

If we know what the project refuses to be, the week succeeded.

If we have avoided premature implementation, the week succeeded.

Early success is clarity.
