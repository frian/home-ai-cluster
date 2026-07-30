"""Core data models for Home AI Cluster."""

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    TypeAdapter,
    field_validator,
    model_validator,
)


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


class SummarizeRequest(BaseModel):
    """A normalized bounded source-text summarization request."""

    text: str
    constraints: RequestConstraints = Field(default_factory=RequestConstraints)

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        """Keep source text non-blank and within its UTF-8 byte bound."""
        if not value.strip():
            raise ValueError("text must not be blank")
        if len(value.encode("utf-8")) > 65_536:
            raise ValueError("text must not exceed 65,536 UTF-8 bytes")
        return value

    @property
    def capability(self) -> Capability:
        """The fixed capability exposed to capability-based routing."""
        return Capability(name="summarize")


class ClassifyRequest(BaseModel):
    """A normalized bounded source-text classification request."""

    text: str
    labels: list[str] = Field(min_length=2, max_length=32)
    constraints: RequestConstraints = Field(default_factory=RequestConstraints)

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        """Keep source text non-blank and within its UTF-8 byte bound."""
        if not value.strip():
            raise ValueError("text must not be blank")
        if len(value.encode("utf-8")) > 65_536:
            raise ValueError("text must not exceed 65,536 UTF-8 bytes")
        return value

    @field_validator("labels")
    @classmethod
    def validate_labels(cls, value: list[str]) -> list[str]:
        """Keep ordered labels bounded, non-empty, and exactly unique."""
        for label in value:
            if not label:
                raise ValueError("labels must not contain empty values")
            if len(label.encode("utf-8")) > 128:
                raise ValueError("labels must not exceed 128 UTF-8 bytes")
        if len(set(value)) != len(value):
            raise ValueError("labels must be unique")
        return value

    @property
    def capability(self) -> Capability:
        """The fixed capability exposed to capability-based routing."""
        return Capability(name="classify")


class InternalSummarizeRequestBody(BaseModel):
    """Strict summarize body used only by the closed internal envelope."""

    model_config = ConfigDict(extra="forbid")

    text: str
    constraints: RequestConstraints = Field(default_factory=RequestConstraints)

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        return SummarizeRequest(text=value).text

    def normalized_request(self) -> SummarizeRequest:
        """Reconstruct the accepted normalized summarize request."""
        return SummarizeRequest(text=self.text, constraints=self.constraints)


class InternalClassifyRequestBody(BaseModel):
    """Strict classify body used only by the closed internal envelope."""

    model_config = ConfigDict(extra="forbid")

    text: str
    labels: list[str]

    @model_validator(mode="after")
    def validate_request(self) -> "InternalClassifyRequestBody":
        ClassifyRequest(text=self.text, labels=self.labels)
        return self

    def normalized_request(self) -> ClassifyRequest:
        """Reconstruct the accepted normalized classification request."""
        return ClassifyRequest(text=self.text, labels=self.labels)


class ChatInternalRequest(BaseModel):
    """The closed internal envelope for one normalized chat request."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["chat"]
    request: ClusterRequest


class SummarizeInternalRequest(BaseModel):
    """The closed internal envelope for one normalized summarize request."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["summarize"]
    request: InternalSummarizeRequestBody


class ClassifyInternalRequest(BaseModel):
    """The closed internal envelope for one normalized classify request."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["classify"]
    request: InternalClassifyRequestBody


InternalClusterRequest = Annotated[
    ChatInternalRequest | SummarizeInternalRequest | ClassifyInternalRequest,
    Field(discriminator="kind"),
]
INTERNAL_CLUSTER_REQUEST_ADAPTER = TypeAdapter(InternalClusterRequest)


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


class ClassifyResult(BaseModel):
    """A successful normalized bounded classification result."""

    selected_label: str
    node_id: str = Field(min_length=1)


class DeclarationStatus(StrEnum):
    """The static declaration status reported by an explicit status operation."""

    COHERENT = "coherent"


class ApplicationStatus(StrEnum):
    """Normalized status of the application serving a cluster node."""

    LOCAL = "local"
    REACHABLE = "reachable"
    UNREACHABLE = "unreachable"
    REQUEST_FAILED = "request-failed"
    INVALID_RESPONSE = "invalid-response"


class RuntimeStatus(StrEnum):
    """Normalized status of a node's declared runtime observation."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    OBSERVATION_FAILED = "observation-failed"
    UNKNOWN = "unknown"


class InternalClusterStatusResponse(BaseModel):
    """The receiving application's normalized local runtime observation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    runtime_status: Literal[
        RuntimeStatus.AVAILABLE,
        RuntimeStatus.UNAVAILABLE,
        RuntimeStatus.OBSERVATION_FAILED,
    ]


class ClusterStatusNode(BaseModel):
    """One privacy-safe normalized status result for a cluster-owned node."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    node_id: str = Field(min_length=1)
    application_status: ApplicationStatus
    runtime_status: RuntimeStatus


class ClusterStatusResult(BaseModel):
    """One privacy-safe normalized status result for a static cluster."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    declaration_status: DeclarationStatus
    nodes: tuple[ClusterStatusNode, ...] = Field(min_length=1)
