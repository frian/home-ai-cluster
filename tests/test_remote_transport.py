import asyncio
import inspect
from typing import get_type_hints

import pytest

from home_ai_cluster.core.models import (
    Capability,
    ChatMessage,
    ClusterRequest,
    ClusterResult,
    NodeDescription,
    NodeHealth,
)
from home_ai_cluster.core.remote_transport import (
    RemoteTransport,
    RemoteTransportError,
)


class FakeRemoteTransport:
    def __init__(
        self,
        result: ClusterResult | None = None,
        error: RemoteTransportError | None = None,
    ) -> None:
        self._result = result or ClusterResult(
            content="remote result",
            adapter="remote-adapter",
        )
        self._error = error
        self.requests: list[ClusterRequest] = []
        self.nodes: list[NodeDescription] = []

    async def send(
        self,
        request: ClusterRequest,
        node: NodeDescription,
    ) -> ClusterResult:
        self.requests.append(request)
        self.nodes.append(node)

        if self._error is not None:
            raise self._error

        return self._result


def make_request() -> ClusterRequest:
    return ClusterRequest(
        messages=[ChatMessage(role="user", content="Hello")],
        capability=Capability(name="chat"),
    )


def make_node() -> NodeDescription:
    return NodeDescription(
        id="remote",
        name="Remote node",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[Capability(name="chat")],
        adapters=["remote-adapter"],
    )


async def _send_remote(
    transport: RemoteTransport,
    request: ClusterRequest,
    node: NodeDescription,
) -> ClusterResult:
    return await transport.send(request, node)


def test_remote_transport_receives_exact_cluster_request_object() -> None:
    transport = FakeRemoteTransport()
    request = make_request()
    node = make_node()

    asyncio.run(_send_remote(transport, request, node))

    assert transport.requests == [request]
    assert transport.requests[0] is request


def test_remote_transport_receives_exact_node_description_object() -> None:
    transport = FakeRemoteTransport()
    request = make_request()
    node = make_node()

    asyncio.run(_send_remote(transport, request, node))

    assert transport.nodes == [node]
    assert transport.nodes[0] is node


def test_remote_transport_returns_cluster_result() -> None:
    result = ClusterResult(content="Hello from remote", adapter="remote-adapter")
    transport = FakeRemoteTransport(result=result)

    actual = asyncio.run(_send_remote(transport, make_request(), make_node()))

    assert actual is result


def test_remote_transport_can_raise_normalized_transport_error() -> None:
    error = RemoteTransportError("remote transport failed")
    transport = FakeRemoteTransport(error=error)

    with pytest.raises(RemoteTransportError) as raised:
        asyncio.run(_send_remote(transport, make_request(), make_node()))

    assert raised.value is error


def test_remote_transport_interface_uses_normalized_cluster_objects() -> None:
    signature = inspect.signature(RemoteTransport.send)
    hints = get_type_hints(RemoteTransport.send)

    assert list(signature.parameters) == ["self", "request", "node"]
    assert hints["request"] is ClusterRequest
    assert hints["node"] is NodeDescription
    assert hints["return"] is ClusterResult
