from __future__ import annotations

from typing import Any, Dict, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


TurnAction = Literal[
    "wait",
    "micro_reply",
    "run_reply_flow",
    "run_main_flow",
    "respond_safety",
]


class TurnManagerInput(BaseModel):
    """
    Optional extra context for the decider.
    Forward-compatible: allow user profile fields to grow over time.
    """
    model_config = ConfigDict(extra="forbid")
    user_profile: Dict[str, Any] = Field(default_factory=dict)


class TurnManagerOutput(BaseModel):
    """
    Strict flow signal + optional micro-reply.
    This layer does NOT generate the full assistant response.
    """
    model_config = ConfigDict(extra="forbid")

    action: TurnAction
    micro_reply_text: str
    reason: str
    confidence: float = Field(..., ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _contract(self) -> "TurnManagerOutput":
        # Enforce: wait => empty micro reply
        if self.action == "wait" and self.micro_reply_text != "":
            raise ValueError('micro_reply_text must be "" when action="wait"')
        return self