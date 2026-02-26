from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.llm.schemas.query_recognizer import RecognizedQuery


MatchType = Literal["id", "name_token"]


class AvailableUser(BaseModel):
    """
    A user entry the requester has access to.

    Forward-compatible: allow extra fields (email, first_name, last_name, etc.).
    """
    model_config = ConfigDict(extra="allow")

    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)


class AccessTargetResolverInput(BaseModel):
    """
    Input for ACCESS_TARGET_RESOLVER.

    - needs_access_check: queries that mention "someone else"
    - available_users: users the requester is allowed to access
    """
    model_config = ConfigDict(extra="forbid")

    needs_access_check: List[RecognizedQuery]
    available_users: Dict[str, AvailableUser]


class ResolvedTarget(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(..., min_length=1)
    target_user_id: str = Field(..., min_length=1)
    target_user_name: str = Field(..., min_length=1)
    match_type: MatchType


class CandidateUser(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)


class UnresolvedTarget(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(..., min_length=1)
    candidates: List[CandidateUser]
    clarify_question: str = Field(..., min_length=1)


class AccessTargetResolverOutput(BaseModel):
    """
    IMPORTANT for strict JSON schema:
    all fields should be required (no defaults).
    Arrays can be empty, but keys must exist.
    """
    model_config = ConfigDict(extra="forbid")

    resolved: List[ResolvedTarget]
    unresolved: List[UnresolvedTarget]