from __future__ import annotations

import json
from typing import Any, ClassVar, Dict, List, Optional

from openai import AsyncOpenAI
from pydantic import BaseModel, ConfigDict

from app.core.config import settings
from app.llm.base import BaseLLMService, LLMRequest, PromptPipeline
from app.llm.schemas.access_target_resolver import (
    AccessTargetResolverInput,
    AccessTargetResolverOutput,
)
from app.llm.system_promts.access_target_resolver import ACCESS_TARGET_RESOLVER


class _EmptyPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AccessTargetResolverService(
    BaseLLMService[AccessTargetResolverInput, AccessTargetResolverOutput]
):
    """
    ACCESS_TARGET_RESOLVER:
    - Takes queries needing access check
    - Takes available_users (provided externally)
    - Resolves target user references to IDs if possible
    - Produces:
        resolved[] (exact match)
        unresolved[] (needs clarification with candidates + question)
    """

    MODEL: ClassVar[str] = settings.OPENAI_BASE_MODEL
    INPUT_SCHEMA: ClassVar[type[AccessTargetResolverInput]] = AccessTargetResolverInput
    OUTPUT_SCHEMA: ClassVar[type[AccessTargetResolverOutput]] = AccessTargetResolverOutput

    PIPELINES: ClassVar[Dict[str, PromptPipeline]] = {
        "default": PromptPipeline(system_prompts=(ACCESS_TARGET_RESOLVER,)),
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
        input_data: AccessTargetResolverInput,
        pipeline_key: str,
    ) -> Any:
        """
        Uses Chat Completions API + strict json_schema.
        Injects available users into the SYSTEM prompt (as requested),
        and keeps USER message focused on 'needs_access_check'.
        """

        # 1) Build a dynamic system prompt that includes available user list
        # Keep it deterministic: pass only what the resolver needs.
        available_users_compact = [
            {"id": u.id, "name": u.name, **{k: v for k, v in u.model_dump().items() if k not in ("id", "name")}}
            for u in input_data.available_users.values()
        ]

        dynamic_system = (
            f"{ACCESS_TARGET_RESOLVER}\n\n"
            "AVAILABLE_USERS (requester has access to ONLY these users):\n"
            f"{json.dumps(available_users_compact, ensure_ascii=False)}\n\n"
            "Rules:\n"
            "- Resolve targets ONLY using AVAILABLE_USERS.\n"
            "- If multiple candidates match, put into 'unresolved' with candidates and a single clarify_question.\n"
            "- If no candidates match, put into 'unresolved' with empty candidates and a clarify_question.\n"
            "- Output must match the provided JSON Schema exactly.\n"
        )

        # 2) Replace the first system message produced by BaseLLMService with the dynamic one
        # If no system exists, insert it.
        patched_messages: List[Dict[str, str]] = []
        inserted = False
        for m in messages:
            if (not inserted) and m.get("role") == "system":
                patched_messages.append({"role": "system", "content": dynamic_system})
                inserted = True
            else:
                patched_messages.append(m)
        if not inserted:
            patched_messages.insert(0, {"role": "system", "content": dynamic_system})

        # 3) User payload: only the queries that need resolving
        user_payload = {
            "needs_access_check": [q.model_dump() for q in input_data.needs_access_check],
        }

        patched_messages.append(
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)}
        )

        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "access_target_resolver_output",
                "strict": True,
                "schema": self.OUTPUT_SCHEMA.model_json_schema(),
            },
        }

        resp = await self.client.chat.completions.create(
            model=model,
            messages=patched_messages,
            temperature=temperature,
            max_tokens=max_output_tokens,
            response_format=response_format,
        )

        content = resp.choices[0].message.content or "{}"
        return json.loads(content)