from __future__ import annotations

import json
from typing import Any, ClassVar, Dict, List, Optional

from openai import AsyncOpenAI
from pydantic import BaseModel, ConfigDict

from app.core.config import settings
from app.llm.base import BaseLLMService, LLMRequest, PromptPipeline
from app.llm.schemas.security_gate import SecurityGateOutput, SecurityGateInput
from app.llm.system_promts.security_gate import LLM_SECURITY_GATE


class _EmptyPayload(BaseModel):
    """
    Optional, but kept to mirror the recognizer style if you ever want
    a pipeline that doesn't require queries (rare).
    """
    model_config = ConfigDict(extra="forbid")


class SecurityGateService(BaseLLMService[SecurityGateInput, SecurityGateOutput]):
    """
    LLM Security Gate:
    - Classifies recognized intents into: valid / needs_access_check / dangerous
    - Uses file_search tool with SECURITY_VECTOR_STORE_IDS (RAG policy)
    - Uses Responses API (required for tools)
    """

    MODEL: ClassVar[str] = settings.OPENAI_BASE_MODEL
    INPUT_SCHEMA: ClassVar[type[SecurityGateInput]] = SecurityGateInput
    OUTPUT_SCHEMA: ClassVar[type[SecurityGateOutput]] = SecurityGateOutput

    PIPELINES: ClassVar[Dict[str, PromptPipeline]] = {
        "default": PromptPipeline(system_prompts=(LLM_SECURITY_GATE,)),
        # You can add more variants (e.g. hardened) if needed.
    }

    def __init__(self) -> None:
        if self.client is None:
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def call_llm(
            self,
            *,
            messages: List[Dict[str, str]],
            model: str,
            temperature: Optional[float],
            max_output_tokens: Optional[int],
            input_data: SecurityGateInput,
            pipeline_key: str,
    ) -> Any:
        """
        Uses Responses API with tools=file_search + vector_store_ids.
        Forces strict JSON Schema output via Responses text.format (NOT response_format).
        """
        if not settings.SECURITY_VECTOR_STORE_IDS:
            raise RuntimeError(
                "SECURITY_VECTOR_STORE_IDS is empty. "
                "Set it in .env (JSON list recommended)."
            )

        # Responses API structured outputs:
        # response_format is for chat.completions, but for responses we must use text.format
        text_format = {
            "type": "json_schema",
            "name": "security_gate_output",
            "strict": True,
            "schema": self.OUTPUT_SCHEMA.model_json_schema(),
        }

        user_payload = input_data.model_dump()

        resp = await self.client.responses.create(
            model=model,
            tools=[
                {
                    "type": "file_search",
                    "vector_store_ids": settings.SECURITY_VECTOR_STORE_IDS,
                }
            ],
            input=[
                *messages,
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
            ],
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            text={"format": text_format},  # ✅ correct for Responses API
        )

        content = getattr(resp, "output_text", None) or "{}"
        return json.loads(content)