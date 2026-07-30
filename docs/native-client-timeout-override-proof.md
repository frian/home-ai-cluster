# Native Client Timeout Override Proof

Status: Complete

## Scope

This proof validates the accepted RFC-0060 ordinary native-client timeout
override against one real slow-but-valid routed summarize request.

## Result

One ordinary summarize invocation used an explicit finite client timeout of
1200 seconds.

The request completed successfully after approximately 8 minutes and 56
seconds.

The elapsed time exceeded the previous 120-second default and demonstrated
that the explicit per-invocation client waiting boundary supports a legitimate
slow workload without changing routing, topology, remote transport, receiver,
runtime, retry, or cancellation behavior.

## Privacy

This retained proof contains no source text, generated result, address,
hostname, username, filesystem path, node identifier, model identifier,
runtime identifier, runtime URL, hardware identity, credential, token,
timestamp, or raw log.

## Conclusion

The accepted RFC-0060 client override is demonstrated in one real ordinary
routed request. No architectural scope beyond RFC-0060 is required.
