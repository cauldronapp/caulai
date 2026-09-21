"""Pydantic request/response schemas (API boundary; never return raw ORM rows)."""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    # Plain str (not EmailStr): stub identities use non-deliverable *.invalid addresses
    # per the governance requirement, which EmailStr rejects as reserved.
    email: str
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    display_name: str
    is_service_identity: bool
    is_stub: bool
    roles: list[str] = []
    permissions: list[str] = []


class RecommendationCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = ""
    category: str = "general"
    tier: str  # auto | requires_approval | permanently_prohibited
    risk_level: str = "low"  # low | medium | high
    action_payload: dict = {}
    target_permission: str | None = None


class DecisionRequest(BaseModel):
    decision: str  # approve | reject
    payload_digest: str
    comment: str = ""


class RevokeRequest(BaseModel):
    reason: str = ""


class PauseRequest(BaseModel):
    scope: str  # global | granular
    target: str = "*"
    reason: str = ""


class SettingUpdate(BaseModel):
    value: dict
