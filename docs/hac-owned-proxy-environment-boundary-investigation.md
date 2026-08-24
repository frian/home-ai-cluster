# HAC-Owned Proxy Environment Boundary Investigation

Status: Complete

Investigated main commit: `5ab115e2c48edc8bf33dded130289b2a7c6f38bd`

Observed toolchain: Python 3.13.1, HTTPX 0.28.1, httpcore 1.0.9, and uv 0.5.9.

## Purpose and source boundary

This documentation-only investigation examines environment-derived proxy and
certificate behavior for HAC-owned HTTPX clients. It authorizes no RFC or
implementation and does not audit the separate acquisition-plugin repository.

HTTPX documents that `Client` and `AsyncClient` use environment variables by
default and that `trust_env=False` disables them. Primary sources: [environment
variables](https://www.python-httpx.org/environment_variables/), [API](https://www.python-httpx.org/api/),
and [proxies](https://www.python-httpx.org/advanced/proxies/). Installed HTTPX
and httpcore source was inspected only to confirm the observed 0.28.1/1.0.9
behavior where needed.

## Production inventory

There are **15 production HTTPX constructor sites**. All omit `trust_env`, thus
default to true. `HTTP_PROXY`, `HTTPS_PROXY`, and `ALL_PROXY` (and lowercase
forms) can apply; `NO_PROXY`/`no_proxy` can bypass; `SSL_CERT_FILE` and
`SSL_CERT_DIR` can affect HTTPS verification. HTTPX defaults redirects to false.

| Category / owners | Lifetime and destination | Payload / timeout / transport | Current effect and disabling cost |
| --- | --- | --- | --- |
| Fixed HAC loopback native callers: `chat_command._post_native_request` (also Code/Code File), `summarize_command._post_native_request`, `classify_command.main`, `external_information_command._post_source_grounded_request`, and `aider_command._AiderTranslator` | One sync client to fixed HAC loopback HTTP | Messages/code, source text, labels, or bounded evidence; caller timeout, explicit no redirects, injectable factories | Ambient proxy routing applies. `trust_env=False` makes direct loopback explicit; CA behavior is irrelevant to fixed HTTP. |
| Declared remote execution: `static_cluster.create_static_cluster_http_client` and `HttpRemoteTransport` | Process-owned async client to an operator-declared HTTP or HTTPS remote | Normalized chat/summarize/classify/source-grounded request; `timeout=None`; optional injected client | Ambient proxy can reroute remote traffic. Disabling trust also stops ambient HTTPS private-CA discovery. |
| Declared remote status: `status_command.evaluate_static_cluster_status` and `HttpRemoteStatusTransport` | One async client to an operator-declared HTTP or HTTPS remote | Status metadata; default client timeout and bounded per-request status timeout | Same proxy and HTTPS CA effect. |
| Runtime loopback Ollama: health plus chat/code, summarize, classify in `OllamaAdapter` | One sync health and three async execution clients to validated local-runtime HTTP | Health metadata; messages/source text/labels; health default timeout, execution `timeout=None`; optional custom transport | Proxy applies unless a supplied transport dispatches instead. Plain HTTP bodies can be sensitive. |
| Runtime loopback llama-server: health plus chat/code, summarize, classify in `LlamaServerAdapter` | One sync health and three async execution clients to validated local-runtime HTTP | Same sensitivity, timeout, redirect, and transport shape as Ollama | Same proxy effect. |

`code_command` and `code_file_command` delegate to a shared native helper rather
than create clients. Static preflight creates none. Test-only MockTransport and
ASGITransport clients are not production routing, though strict test factories
could need signatures after a later explicit argument. Acquisition-plugin
requests are provider/plugin-owned under RFC-0078/0079 and are intentionally
not HAC-core traffic.

## Controlled local evidence

Before every experiment all upper/lowercase proxy variables and both bypass
variables were unset. Only synthetic disposable loopback values were then set.
No external proxy/service, real environment value, private address, prompt,
source, or model output was used or retained.

| Experiment | Observation |
| --- | --- |
| Default clients | Fresh sync and async clients both reported `trust_env=True`. |
| Synthetic HTTP proxy | With an empty bypass list, a disposable proxy received one connection, the absolute-form target, and a harmless marker body; the direct target received nothing. |
| `trust_env=False` | The proxy received nothing and the disposable direct target received the marker. |
| `NO_PROXY` | Adding the target's loopback literal bypassed the proxy. Current safety therefore depends on operator-controlled bypass contents; no universal bypass can cover names, literals, and arbitrary LAN destinations without choosing a routing policy. |
| Synthetic SOCKS contamination | Without installing SOCKS support, a closed synthetic SOCKS `ALL_PROXY` made default sync and async construction raise `ImportError`. |
| Custom transport | `Client` with direct `MockTransport` constructed under that SOCKS setting: custom dispatch avoids this proxy-map path, but is not proof of socket routing. |
| Certificate variables | A synthetic nonexistent `SSL_CERT_FILE` raised `FileNotFoundError` for default construction; `trust_env=False` constructed. This confirms the documented loss of `SSL_CERT_FILE`/`SSL_CERT_DIR` handling. |

The locked suite with proxy variables cleared passed **1343 tests, 0 failures**.
The suite with only closed synthetic loopback HTTP proxy variables and no bypass
variables also passed **1343 tests, 0 failures**. This is negative evidence only:
the suite mainly uses injected, mock, or ASGI transports and does not prove a
real HAC-owned socket route bypasses proxies.

## Security, privacy, and TLS compatibility

Ambient unsupported SOCKS configuration can fail client construction. Ambient
HTTP proxy routing exposes destination metadata and can expose plaintext HTTP
bodies, including messages, source text, labels, and internal envelopes. HTTPS
CONNECT exposes destination metadata; TLS interception and plaintext disclosure
are separate and require a trusted interception certificate. A legitimate
general-purpose proxy configuration should not silently redefine HAC cluster
routing. Subprocesses inherit environment independently; this finding covers
HAC HTTPX clients, not Aider or plugin network policy.

Static remotes permit HTTP and HTTPS. Retained proofs use HTTP, and the
repository does not promise ambient `SSL_CERT_FILE` or `SSL_CERT_DIR` support.
Thus `trust_env=False` would end incidental private-CA discovery. Preserving it,
rejecting such setups, or adding explicit CA configuration is architectural;
this investigation deliberately does not choose among them.

## Options and recommendation

| Option | Result |
| --- | --- |
| Keep defaults and document `NO_PROXY` | Smallest, but no direct-path guarantee; ambient SOCKS can fail construction and proxy/CA policy remains implicit. |
| Disable only fixed native loopback callers | Protects ordinary callers but leaves runtime and declared-remote paths ambient. |
| Disable for all HAC-owned fixed, runtime, and remote clients | Coherent direct HAC routing and no ambient proxy construction failure, but removes ambient HTTPS private-CA discovery. |
| Preserve CA while disabling proxies | HTTPX documents one `trust_env` switch, so this needs deliberate SSL/context policy and tests. |
| Add explicit proxy or CA configuration | Larger configuration, secrecy, precedence, and compatibility decision. |
| Defer plugin-owned acquisition | Preserves RFC-0078/0079 ownership; provider traffic must not silently become HAC core. |

No generic client abstraction is evidenced: direct constructor arguments are
smaller, while existing shared native helpers already cover several callers.

Established facts are default environment trust at all 15 sites, synthetic
proxy capture of an HTTP body, direct behavior with `trust_env=False`, and its
private-CA consequence. The recommended smallest RFC question is:

> Should all HAC-owned internal, local-runtime, and declared-remote HTTPX
> clients use `trust_env=False`, and what explicit private-CA compatibility, if
> any, belongs in that same decision?

Likely goals are direct HAC-owned routing, unchanged timeout/redirect contracts,
and explicit plugin exclusion. Likely non-goals are provider policy, proxy
configuration, retries, runtime termination, and a generic client abstraction.
Non-authorized later implementation would touch shared native helpers,
Aider/external-information factories, static process/status clients, adapter
constructors, and focused synthetic-proxy/factory tests. A full synthetic-proxy
suite could be a regression check but is not sufficient alone.

No implementation is authorized by this investigation.
