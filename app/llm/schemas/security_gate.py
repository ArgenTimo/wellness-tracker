from __future__ import annotations

from typing import List
from pydantic import BaseModel, ConfigDict

from app.llm.schemas.query_recognizer import RecognizedQuery


class SecurityGateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    queries: List[RecognizedQuery]


class SecurityGateOutput(BaseModel):
    """
    IMPORTANT for Structured Outputs (strict JSON Schema):
    all properties must be required. Lists may be empty.
    """
    model_config = ConfigDict(extra="forbid")

    valid_queries: List[RecognizedQuery]
    needs_access_check: List[RecognizedQuery]
    dangerous_queries: List[RecognizedQuery]