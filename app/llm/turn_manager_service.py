from __future__ import annotations

import json
from typing import Any, ClassVar, Dict, List, Optional

from openai import AsyncOpenAI

from app.core.config import settings
from app.llm.base import BaseLLMService, PromptPipeline
from app.llm.schemas.turn_manager import TurnManagerInput, TurnManagerOutput
from app.llm.system_promts.turn_manager import TURN_MANAGER_PROMPT


class TurnManagerService(BaseLLMService[TurnManagerInput, TurnManagerOutput]):
    """
    Flow-signal layer:
    - decides next action (wait/micro_reply/run flows/safety)
    - optionally provides a short micro-reply
    - does not generate the full assistant response
    """

    MODEL: ClassVar[str] = settings.OPENAI_BASE_MODEL
    INPUT_SCHEMA: ClassVar[type[TurnManagerInput]] = TurnManagerInput
    OUTPUT_SCHEMA: ClassVar[type[TurnManagerOutput]] = TurnManagerOutput

    PIPELINES: ClassVar[Dict[str, PromptPipeline]] = {
        "default": PromptPipeline(system_prompts=(TURN_MANAGER_PROMPT,)),
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
        input_data: TurnManagerInput,
        pipeline_key: str,
    ) -> Any:
        # Inject user profile JSON into the system prompt (may be empty)
        profile_json = json.dumps(input_data.user_profile or {}, ensure_ascii=False)

        dynamic_system = (
            f"{TURN_MANAGER_PROMPT}\n\n"
            f"USER_PROFILE_JSON:\n{profile_json}\n"
        )

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

        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "turn_manager_output",
                "strict": True,
                "schema": self.OUTPUT_SCHEMA.model_json_schema(),
            },
        }

        resp = await self.client.chat.completions.create(
            model=model,
            messages=patched_messages,
            temperature=temperature if temperature is not None else 0.0,
            max_tokens=max_output_tokens,
            response_format=response_format,
        )

        content = resp.choices[0].message.content or "{}"
        return json.loads(content)