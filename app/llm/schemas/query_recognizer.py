from __future__ import annotations

from typing import List, Literal
from pydantic import BaseModel, Field, ConfigDict


QueryType = Literal["explicit", "implicit"]


class RecognizedQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: QueryType
    summary: str = Field(..., min_length=1)
    original_fragment: str = Field(..., min_length=1)


class QueryRecognizerOutput(BaseModel):
    """
    Strict output schema for LLM_QUERIES_RECOGNIZER.
    """
    model_config = ConfigDict(extra="forbid")

    queries: List[RecognizedQuery]