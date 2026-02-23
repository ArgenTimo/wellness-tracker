"""
Base classes for singleton LLM services.

Goals:
- One standardized input type for all LLM services (single message or full dialogue history).
- Strong typing via Pydantic input/output schemas.
- Support for multiple pipelines (one or many system prompts).
- Child classes must define:
  - model name
  - input/output Pydantic models
  - the actual LLM call function (backend integration)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Callable, ClassVar, Dict, Generic, Iterable, List, Literal, Optional, Sequence, Type, TypeVar

from pydantic import BaseModel, Field, model_validator


# =========================
# Shared message primitives
# =========================

Role = Literal["system", "user", "assistant", "tool"]


class ChatMessage(BaseModel):
    """Single chat message in a normalized format."""
    role: Role
    content: str = Field(..., min_length=1)

    # Optional metadata if you need it later (timestamps, ids, etc.)
    name: Optional[str] = None


class LLMRequest(BaseModel):
    """
    Standardized request payload for any LLM service.

    You can pass:
    - user_message (single new message), optionally with history, OR
    - only history (if the last message is already user), OR
    - both (history + user_message appended automatically).

    pipeline:
      - lets a child service select one of multiple prompt pipelines.
    """

    user_message: Optional[str] = Field(default=None, description="Latest user message (optional if history already includes it).")
    history: List[ChatMessage] = Field(default_factory=list, description="Full dialogue history in normalized format.")
    pipeline: str = Field(default="default", description="Pipeline key (child decides available pipelines).")

    # Optional knobs, consistent across services:
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    max_output_tokens: Optional[int] = Field(default=None, ge=1)

    @model_validator(mode="after")
    def _validate_message_presence(self) -> "LLMRequest":
        if (self.user_message is None or self.user_message.strip() == "") and not self.history:
            raise ValueError("Provide either user_message or history (at least one message).")
        return self

    def iter_dialogue(self) -> List[ChatMessage]:
        """Return final dialogue: history + user_message (if provided)."""
        msgs = list(self.history)
        if self.user_message is not None and self.user_message.strip():
            msgs.append(ChatMessage(role="user", content=self.user_message.strip()))
        return msgs


# =========================
# Pipeline definition
# =========================

@dataclass(frozen=True)
class PromptPipeline:
    """
    Prompt pipeline definition.

    system_prompts:
      - one or more system prompts (some pipelines need multiple).
    """
    system_prompts: Sequence[str]


# =========================
# Generic base service
# =========================

InModel = TypeVar("InModel", bound=BaseModel)
OutModel = TypeVar("OutModel", bound=BaseModel)


class SingletonBase:
    """Lightweight singleton base (works well for service objects)."""
    _instance: ClassVar[Optional["SingletonBase"]] = None

    def __new__(cls, *args: Any, **kwargs: Any):
        if cls._instance is None or cls._instance.__class__ is not cls:
            cls._instance = super().__new__(cls)
        return cls._instance


class BaseLLMService(SingletonBase, ABC, Generic[InModel, OutModel]):
    """
    Parent class for LLM singleton services.

    Child requirements:
    - MODEL: str
    - INPUT_SCHEMA: Type[BaseModel]
    - OUTPUT_SCHEMA: Type[BaseModel]
    - call_llm(...) implementation (actual provider call)
    - pipelines mapping (at least "default")

    This class:
    - normalizes request into provider messages
    - selects pipeline
    - validates input/output
    """

    MODEL: ClassVar[str]
    INPUT_SCHEMA: ClassVar[Type[InModel]]
    OUTPUT_SCHEMA: ClassVar[Type[OutModel]]

    # Pipelines are per service.
    PIPELINES: ClassVar[Dict[str, PromptPipeline]] = {
        "default": PromptPipeline(system_prompts=()),
    }

    # Optional: attach a provider client or any dependencies later.
    # You can set this in app startup.
    client: Any = None

    def parse_input(self, data: Dict[str, Any] | InModel) -> InModel:
        """Validate/normalize input payload into INPUT_SCHEMA."""
        if isinstance(data, BaseModel):
            return data  # type: ignore[return-value]
        return self.INPUT_SCHEMA.model_validate(data)

    def build_messages(self, request: LLMRequest, *, pipeline: PromptPipeline) -> List[Dict[str, str]]:
        """
        Build provider-ready messages.

        Output format is intentionally minimal: {"role": "...", "content": "..."}.
        """
        messages: List[Dict[str, str]] = []

        for sp in pipeline.system_prompts:
            if sp.strip():
                messages.append({"role": "system", "content": sp.strip()})

        for m in request.iter_dialogue():
            messages.append({"role": m.role, "content": m.content})

        return messages

    def get_pipeline(self, pipeline_key: str) -> PromptPipeline:
        try:
            return self.PIPELINES[pipeline_key]
        except KeyError as e:
            available = ", ".join(sorted(self.PIPELINES.keys()))
            raise ValueError(f"Unknown pipeline='{pipeline_key}'. Available: {available}") from e

    async def run(self, request: LLMRequest, payload: Dict[str, Any] | InModel) -> OutModel:
        """
        One standard entrypoint for all child services.

        request: standardized conversation input (single message or history)
        payload: service-specific input model data
        """
        inp = self.parse_input(payload)
        pipeline = self.get_pipeline(request.pipeline)

        messages = self.build_messages(request, pipeline=pipeline)

        raw = await self.call_llm(
            messages=messages,
            model=self.MODEL,
            temperature=request.temperature,
            max_output_tokens=request.max_output_tokens,
            input_data=inp,
            pipeline_key=request.pipeline,
        )

        # raw can be:
        # - dict for JSON output
        # - Pydantic model
        # - string (if child converts)
        return self.OUTPUT_SCHEMA.model_validate(raw)

    @abstractmethod
    async def call_llm(
        self,
        *,
        messages: List[Dict[str, str]],
        model: str,
        temperature: Optional[float],
        max_output_tokens: Optional[int],
        input_data: InModel,
        pipeline_key: str,
    ) -> Any:
        """
        Child must implement the actual provider call.

        Best practice:
        - enforce JSON output shape
        - return a dict matching OUTPUT_SCHEMA
        """
        raise NotImplementedError