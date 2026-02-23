from __future__ import annotations

import json
from typing import Any, ClassVar, Dict, List, Optional

from pydantic import BaseModel, ConfigDict
from openai import AsyncOpenAI

from app.core.config import settings
from app.llm.base import BaseLLMService, LLMRequest, PromptPipeline
from app.llm.schemas.query_recognizer import QueryRecognizerOutput
from app.llm.system_promts.queries_recognizer import LLM_QUERIES_RECOGNIZER


class QueryRecognizerInput(BaseModel):
    """
    For this service we don't need extra parameters besides the conversation input (LLMRequest).
    Kept for consistency and future extensibility.
    """
    model_config = ConfigDict(extra="forbid")


class QueryRecognizerService(BaseLLMService[QueryRecognizerInput, QueryRecognizerOutput]):
    MODEL: ClassVar[str] = settings.OPENAI_BASE_MODEL
    INPUT_SCHEMA: ClassVar[type[QueryRecognizerInput]] = QueryRecognizerInput
    OUTPUT_SCHEMA: ClassVar[type[QueryRecognizerOutput]] = QueryRecognizerOutput

    PIPELINES: ClassVar[Dict[str, PromptPipeline]] = {
        "default": PromptPipeline(
            system_prompts=LLM_QUERIES_RECOGNIZER
        ),
        # Example of a multi-system-prompt pipeline
        "hardened": PromptPipeline(
            system_prompts=(
                "LLM_QUERIES_RECOGNIZER_PROMPT_PLACEHOLDER",
                "Output MUST follow the provided JSON Schema exactly. No extra keys.",
            )
        ),
    }

    def __init__(self) -> None:
        # You can also inject this from FastAPI startup instead of constructing here.
        if self.client is None:
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def call_llm(
        self,
        *,
        messages: List[Dict[str, str]],
        model: str,
        temperature: Optional[float],
        max_output_tokens: Optional[int],
        input_data: QueryRecognizerInput,
        pipeline_key: str,
    ) -> Any:
        """
        Uses Structured Outputs via response_format json_schema (strict=true).
        The model is constrained to match the schema during generation.
        """
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "query_recognizer_output",
                "strict": True,
                "schema": self.OUTPUT_SCHEMA.model_json_schema(),
            },
        }

        resp = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_output_tokens,
            response_format=response_format,
        )

        content = resp.choices[0].message.content or "{}"
        return json.loads(content)