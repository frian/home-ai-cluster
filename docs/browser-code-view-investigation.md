# Loopback browser Code view investigation

Status: Investigation only

Date: 2026-08-14

## Purpose and scope

This documentation-only investigation determines whether the accepted textual
`code` capability may be exposed through the existing loopback browser client
without another architectural decision. It does not authorize or implement a
browser Code view, a new endpoint, an RFC, or any runtime behavior.

The candidate in scope is deliberately narrow:

```text
one Code tab
  -> one textual instruction textarea
  -> same-origin POST /v1/chat with capability: code
  -> existing textual ClusterResult
  -> returned text and existing node_id attribution
```

It excludes an editor, syntax highlighting, execution, tools, Git, repository
or filesystem access, downloads, Save As behavior, persistence, and any
browser or server authority beyond the existing text request and response.

## Current accepted browser boundary

RFC-0062 is not an accidental implementation limitation. Its accepted summary,
goals, decision, and acceptance criteria define the first loopback browser
surface as exactly three fixed views: Chat, Summarize, and Classify. Browser
JavaScript is authorized to make direct same-origin calls only to existing
`POST /v1/chat`, `POST /v1/summarize`, and `POST /v1/classify` routes. Its
capability table names those same three views and routes.

The current implementation is faithful to that boundary:

| Current view | Page element | Request | Successful display |
| --- | --- | --- | --- |
| Chat | `#chat-view` | `POST /v1/chat`, `capability: "chat"` | textual content and `node_id` |
| Summarize | `#summarize-view` | `POST /v1/summarize` | textual content and `node_id` |
| Classify | `#classify-view` | `POST /v1/classify` | selected label and `node_id` |

[`web/index.html`](../src/home_ai_cluster/web/index.html) has exactly those
three tabs and panels. [`web/assets/app.js`](../src/home_ai_cluster/web/assets/app.js)
contains exactly the three corresponding `post(...)` calls. The fixed asset
routes in [`loopback_browser.py`](../src/home_ai_cluster/web/loopback_browser.py)
serve that one page and its project-owned assets only. The focused browser
tests assert the three calls and that API-only compositions remain page-free.

RFC-0062 deliberately separates the loopback-browser application from API-only
application compositions. It preserves loopback-only same-origin access and
does not authorize CORS, a proxy, a second process, LAN browser exposure,
browser storage, server-side state, request logging, a dashboard, or an
operator surface. A fourth browser view therefore changes the accepted fixed
browser contract, even if it uses already accepted core semantics.

## Current `code` boundary

RFC-0067 accepts `code` as a closed explicit semantic capability for bounded
textual code generation, transformation, and explanation. Its accepted
contract is intentionally text-only:

| Concern | Accepted boundary |
| --- | --- |
| Request | Existing ordered-message `ClusterRequest` with explicit `capability=code` |
| Input bound | Aggregate message content no greater than 65,536 UTF-8 bytes |
| Result | Existing free-form textual `ClusterResult`, including `node_id` attribution |
| Execution | Existing Chat-like adapter method and existing internal envelope |
| Eligibility | Explicit static `code` opt-in; hard boolean eligibility only |
| Authority | Generated code and commands are response text only |

RFC-0067 expressly grants no filesystem or repository access/editing, shell or
test execution, Git, tools/function calling, agents, autonomous loops, web
access, persistence, or compatibility expansion. It also does not promise a
parseable source file, one code block, a language, syntax validity, a patch, a
diff, or file operations.

Most importantly for this investigation, its Native, browser, and compatibility
surfaces section says that the loopback web client remains unchanged and that a
Code page is a later separate convenience decision. It explicitly excludes
browser editor work, Monaco, syntax highlighting, browser filesystem/repository
access, and persistence. Its decision repeats that browser and OpenAI-compatible
surfaces remain unchanged.

The current code carries out the accepted core contract. In
[`core/models.py`](../src/home_ai_cluster/core/models.py), `ClusterRequest`
revalidates the aggregate UTF-8 message-content limit whenever
`capability.name == "code"`. [`tests/test_code_capability.py`](../tests/test_code_capability.py)
checks both aggregate multi-message accounting and rejection over 65,536 bytes.
The static capability vocabulary includes `code`, while omission remains only
`chat` plus `summarize`; a node is not silently made code-capable.

## Existing HTTP seam

No new `/v1/code` endpoint is necessary for the candidate text-only request.
The existing native `POST /v1/chat` public body already accepts non-empty
ordered `messages` plus a non-empty `capability`. Its handler constructs:

```text
ClusterRequest(
  messages=request.messages,
  capability=Capability(name=request.capability),
  constraints=existing constraints
)
```

Therefore a same-origin browser body such as the following enters the accepted
`ClusterRequest(capability=code)` path without translation or a new route:

```json
{
  "capability": "code",
  "messages": [{"role": "user", "content": "..."}]
}
```

That construction invokes the core model validation above, so the 65,536-byte
aggregate code bound is authoritatively revalidated at the current native
boundary. The existing native `code` command independently demonstrates this
seam: [`code_command.py`](../src/home_ai_cluster/commands/code_command.py) constructs
the explicit `code` request then sends it through the native chat path. The
same model is also embedded in the accepted internal Chat envelope, where it
is revalidated at the receiving boundary.

The existing `/v1/chat` route then uses the normal `ClusterRequest` routing,
eligibility, fallback, adapter execution, and `ClusterResult` path. Evidence
does not support adding `/v1/code`; doing so would duplicate a truthful
accepted request representation and add an unnecessary public route.

## Smallest plausible browser implementation after authorization

The existing browser code provides nearly all mechanics needed for a fourth
fixed text-only view:

| Existing seam | Reuse for a later Code view |
| --- | --- |
| `post(path, body, activeMessage)` | Same-origin JSON POST, one-request-at-a-time handling, safe response failure display, and generic malformed/network failure display |
| `setRequestActive` | Shared request-active status and disabling of all submit buttons |
| `renderResult(container, content, nodeId)` | Text-safe rendering using `textContent` and existing `node_id` attribution |
| `byteLimit = 65536` | Immediate UTF-8 byte check; server validation remains authoritative |
| Tabs and fixed HTML panels | One additional fixed tab and panel, with no client-side router |

The minimum browser-specific work would be only a Code tab/panel, one textarea,
a form submit handler, an input check for non-blank text within the existing
65,536-byte limit, the explicit body `{"capability":"code","messages":[...]}`,
and a result container passed to `renderResult`. It would display ordinary
text, not interpret it as markup or as a file. It should create no message
history beyond the current textarea value and no special client-side behavior
such as retries, fallback, polling, streaming, cancellation, or selection.

## Architecture impact of the candidate

Provided a later decision authorizes exactly the narrow shape above, the core
and exposure boundaries remain unchanged as follows:

| Accepted boundary | Impact | Evidence |
| --- | --- | --- |
| Cluster request shape | Unchanged | Existing `/v1/chat` already constructs `ClusterRequest(capability=code)`. |
| Cluster result shape | Unchanged | `code` already returns the free-form `ClusterResult` used by Chat. |
| Routing and capability eligibility | Unchanged | Explicit `code` membership, static opt-in, ordering, and fallback are accepted in RFC-0067. |
| Adapters | Unchanged | RFC-0067 reuses the existing Chat-like adapter method. |
| Internal remote transport | Unchanged | RFC-0067 reuses `ChatInternalRequest` / `kind: "chat"` while preserving embedded `code`. |
| Fallback and node attribution | Unchanged | The request follows existing routing and renders existing result `node_id`. |
| OpenAI compatibility | Unchanged | RFC-0067 keeps compatibility Chat-only; the candidate calls native `/v1/chat`, not the compatibility process. |
| Browser network exposure | Unchanged | The page remains an RFC-0062 fixed asset on the existing loopback-only same origin; no CORS, proxy, second process, or LAN access. |
| Browser storage and server persistence | Unchanged | RFC-0062's ephemeral browser state and no server retention continue; no new storage is needed. |
| Filesystem and execution authority | Unchanged | The candidate only sends text and displays text; RFC-0067 grants neither authority. |

The one changed boundary is the accepted **browser surface contract**: it would
expand from three fixed views to four. RFC-0062 currently authorizes calls only
to its three named endpoints, and RFC-0067 expressly defers this convenience.
That is a project decision, not a local HTML/CSS/JavaScript detail.

## Recommendation — Outcome B: narrow RFC required

The implementation itself would be small and would reuse existing seams, but a
new narrow RFC is required before implementation. RFC-0062 deliberately fixes
the first browser surface around Chat, Summarize, and Classify. RFC-0067
deliberately leaves the loopback browser unchanged and defers a Code page to a
later separate convenience decision. Those accepted decisions control the
browser surface, privacy, and loopback composition boundary; an implementation
PR cannot silently widen them.

The likely RFC decision boundary is only:

- authorize one fourth fixed loopback browser view for explicit `code`;
- reuse same-origin native `POST /v1/chat` with `capability=code` and ordered
  messages, not a new endpoint;
- preserve the authoritative aggregate 65,536-byte UTF-8 bound;
- display only free-form returned text and existing `node_id` attribution;
- preserve RFC-0062 loopback-only same-origin serving and ephemeral browser
  state; and
- grant no filesystem, repository, shell, Git, tool, execution, persistence,
  or OpenAI-compatibility authority.

It should also state that existing native validation and safe failures remain
authoritative. This is an outline of the decision boundary, not a proposed RFC.

## Separate future file convenience

This investigation distinguishes the possible text-only view:

```text
prompt -> textual code response -> browser display
```

from a separate possible caller/browser-side convenience:

```text
textual response -> explicit browser-owned Download / Save As
```

The latter is outside this investigation and is not authorized by the proposed
text-only increment. It must not grant Home AI Cluster server-side filesystem
authority. Any later decision would need to address its browser-owned ownership
and safety separately rather than treating a free-form `ClusterResult` as a
file or editing contract.
