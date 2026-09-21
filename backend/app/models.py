"""PostgreSQL system-of-record models. No MongoDB. All authorization data lives here."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    String, Boolean, Integer, BigInteger, Text, DateTime, ForeignKey,
    UniqueConstraint, Index,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ----- Identity & RBAC (authorization lives in PostgreSQL, NOT the IdP) -----

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    subject: Mapped[str] = mapped_column(String(255), unique=True, index=True)  # IdP subject (stub)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(String(255))
    is_service_identity: Mapped[bool] = mapped_column(Boolean, default=False)
    is_stub: Mapped[bool] = mapped_column(Boolean, default=True)
    disabled: Mapped[bool] = mapped_column(Boolean, default=False)
    token_version: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    roles: Mapped[list["Role"]] = relationship(secondary="user_roles", back_populates="users")


class Role(Base):
    __tablename__ = "roles"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    description: Mapped[str] = mapped_column(String(255), default="")
    is_system: Mapped[bool] = mapped_column(Boolean, default=True)

    users: Mapped[list["User"]] = relationship(secondary="user_roles", back_populates="roles")
    permissions: Mapped[list["Permission"]] = relationship(
        secondary="role_permissions", back_populates="roles"
    )


class Permission(Base):
    __tablename__ = "permissions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(96), unique=True, index=True)  # "resource:action"
    resource: Mapped[str] = mapped_column(String(48))
    action: Mapped[str] = mapped_column(String(48))
    description: Mapped[str] = mapped_column(String(255), default="")

    roles: Mapped[list["Role"]] = relationship(
        secondary="role_permissions", back_populates="permissions"
    )


class UserRole(Base):
    __tablename__ = "user_roles"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_id: Mapped[str] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)


class RolePermission(Base):
    __tablename__ = "role_permissions"
    role_id: Mapped[str] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    permission_id: Mapped[str] = mapped_column(ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)


class Session(Base):
    __tablename__ = "sessions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    jti: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)


# ----- Recommendation & Approval state machines -----

class Recommendation(Base):
    __tablename__ = "recommendations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(64), default="general")
    tier: Mapped[str] = mapped_column(String(32))  # auto | requires_approval | permanently_prohibited
    risk_level: Mapped[str] = mapped_column(String(16), default="low")  # low | medium | high
    action_payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    payload_digest: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    required_approvals: Mapped[int] = mapped_column(Integer, default=1)
    irreversible: Mapped[bool] = mapped_column(Boolean, default=False)
    submitted_by: Mapped[str] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


class Approval(Base):
    __tablename__ = "approvals"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    recommendation_id: Mapped[str] = mapped_column(ForeignKey("recommendations.id", ondelete="CASCADE"), index=True)
    payload_digest: Mapped[str] = mapped_column(String(64), index=True)  # binds approval to exact payload
    status: Mapped[str] = mapped_column(String(32), default="pending")  # pending|approved|rejected|revoked
    required_approvals: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    revoked_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    decisions: Mapped[list["ApprovalDecision"]] = relationship(
        back_populates="approval", cascade="all, delete-orphan"
    )


class ApprovalDecision(Base):
    __tablename__ = "approval_decisions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    approval_id: Mapped[str] = mapped_column(ForeignKey("approvals.id", ondelete="CASCADE"), index=True)
    reviewer_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    decision: Mapped[str] = mapped_column(String(16))  # approve | reject
    payload_digest: Mapped[str] = mapped_column(String(64))  # digest at time of decision
    comment: Mapped[str] = mapped_column(String(1024), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    approval: Mapped["Approval"] = relationship(back_populates="decisions")

    __table_args__ = (
        # A single reviewer may not count twice for the same approval.
        UniqueConstraint("approval_id", "reviewer_id", name="uq_one_decision_per_reviewer"),
    )


# ----- Tamper-evident (NOT immutable) hash-chained audit -----

class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    chain_env: Mapped[str] = mapped_column(String(16), index=True)
    chain_org: Mapped[str] = mapped_column(String(64), index=True)
    seq: Mapped[int] = mapped_column(BigInteger)
    timestamp: Mapped[str] = mapped_column(String(40))  # ISO string kept verbatim for canonical hashing
    actor_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    actor_label: Mapped[str] = mapped_column(String(255))
    action: Mapped[str] = mapped_column(String(96), index=True)
    resource_type: Mapped[str] = mapped_column(String(64), index=True)
    resource_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    canonical: Mapped[str] = mapped_column(Text)  # deterministic serialization that was hashed
    prev_hash: Mapped[str] = mapped_column(String(64))
    hash: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    __table_args__ = (
        UniqueConstraint("chain_env", "chain_org", "seq", name="uq_chain_seq"),
        Index("ix_audit_chain", "chain_env", "chain_org", "seq"),
    )


class AuditCheckpoint(Base):
    """Independent, write-restricted checkpoints of chain state for external verification."""
    __tablename__ = "audit_checkpoints"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    chain_env: Mapped[str] = mapped_column(String(16), index=True)
    chain_org: Mapped[str] = mapped_column(String(64), index=True)
    seq: Mapped[int] = mapped_column(BigInteger)
    hash: Mapped[str] = mapped_column(String(64))
    event_count: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    note: Mapped[str] = mapped_column(String(255), default="")


# ----- Emergency controls (operate against STUB paths only) -----

class PauseState(Base):
    __tablename__ = "pause_states"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    scope: Mapped[str] = mapped_column(String(16))  # global | granular
    target: Mapped[str] = mapped_column(String(96), default="*")  # "*" for global, "resource:action" granular
    active: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    reason: Mapped[str] = mapped_column(String(512), default="")
    engaged_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    engaged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    released_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# ----- Supporting system tables (for nav/pages) -----

class Setting(Base):
    __tablename__ = "settings"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    key: Mapped[str] = mapped_column(String(96), unique=True, index=True)
    value: Mapped[dict] = mapped_column(JSONB, default=dict)
    version: Mapped[int] = mapped_column(Integer, default=1)
    updated_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


class Connector(Base):
    __tablename__ = "connectors"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(96), unique=True)
    category: Mapped[str] = mapped_column(String(64), default="general")
    status: Mapped[str] = mapped_column(String(32), default="not_connected")


class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    kind: Mapped[str] = mapped_column(String(48), default="info")
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text, default="")
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Policy(Base):
    __tablename__ = "policies"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(128), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
    rules: Mapped[dict] = mapped_column(JSONB, default=dict)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


class ExecutionQueueItem(Base):
    """Stub execution queue. NEVER calls a live connector in Phase 1A."""
    __tablename__ = "execution_queue"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    recommendation_id: Mapped[str] = mapped_column(ForeignKey("recommendations.id", ondelete="CASCADE"), index=True)
    connector: Mapped[str | None] = mapped_column(String(96), nullable=True)
    status: Mapped[str] = mapped_column(String(24), default="queued", index=True)
    # queued|executing|executed|cancelled|drained|failed|rolled_back
    irreversible: Mapped[bool] = mapped_column(Boolean, default=False)
    rollback_eligible: Mapped[bool] = mapped_column(Boolean, default=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    result: Mapped[dict] = mapped_column(JSONB, default=dict)
    enqueued_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    enqueued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)
