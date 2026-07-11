"""Core data models for Home AI Cluster."""

from typing import Literal

from pydantic import BaseModel, Field


class Capability(BaseModel):
    """A cluster capability, independent of model or runtime names."""

    name: str = Field(min_length=1)


class AdapterHealth(BaseModel):
    """Minimal runtime adapter availability information."""

    available: bool
    reason: str | None = None


class NodeHealth(BaseModel):
    """Minimal node health information."""

    healthy: bool
    reason: str | None = None


class NodeDescription(BaseModel):
    """A cluster-visible description of a node."""

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    availability: Literal["available", "unavailable", "unknown"]
    health: NodeHealth
    capabilities: list[Capability] = Field(min_length=1)
    adapters: list[str] = Field(min_length=1)


class ChatMessage(BaseModel):
    """A normalized chat message accepted by the cluster core."""

    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1)


class RequestConstraints(BaseModel):
    """Optional constraints the router may consider later."""

    local_only: bool = True
    prefer_fast_response: bool = False
    min_context_size: int | None = Field(default=None, ge=1)


class ClusterRequest(BaseModel):
    """A normalized chat request for Home AI Cluster."""

    messages: list[ChatMessage] = Field(min_length=1)
    capability: Capability
    constraints: RequestConstraints = Field(default_factory=RequestConstraints)


class RuntimeResult(BaseModel):
    """Runtime-specific result data produced by an adapter."""

    content: str
    adapter: str = Field(min_length=1)
    model: str | None = None


class ClusterResult(BaseModel):
    """A successful normalized result returned by the cluster."""

    content: str
    adapter: str = Field(min_length=1)
    model: str | None = None
    node_id: str = Field(min_length=1)
