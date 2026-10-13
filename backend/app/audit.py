"""Tamper-evident hash-chained audit log.

Properties: deterministic canonical serialization, concurrency-safe monotonic
sequencing (Postgres transactional advisory lock), transactional insertion (audit
row commits atomically with the business change made in the same Session),
per-environment/org chain scope, genesis record, on-write/scheduled/on-demand
verification with gap/reorder/duplicate/tamper detection, and independent
write-restricted checkpoints.

NOTE: This is *tamper-evident*, NOT tamper-proof and never "immutable". A DB owner
compromise can rewrite history; that residual risk is documented in the runbook.
"""
import zlib
from datetime import datetime, timezone

from sqlalchemy import text, select
from sqlalchemy.orm import Session

from .models import AuditEvent, AuditCheckpoint
from .canonical import canonical_json, sha256_hex
from .config import get_chain_env, get_chain_org

GENESIS_PREV_HASH = "0" * 64


def _lock_keys(chain_env: str, chain_org: str):
    scope = f"{chain_env}:{chain_org}".encode("utf-8")
    k = zlib.crc32(scope)
    # split into two signed int4 for pg_advisory_xact_lock(int, int)
    return (k >> 16) & 0xFFFF, k & 0xFFFF


def _compute_hash(body: dict) -> tuple[str, str]:
    canonical = canonical_json(body)
    return canonical, sha256_hex(canonical)


def append_event(
    db: Session,
    *,
    actor_id: str | None,
    actor_label: str,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    payload: dict | None = None,
    chain_env: str | None = None,
    chain_org: str | None = None,
) -> AuditEvent:
    """Append a hash-chained event. Caller commits (transactional insertion)."""
    chain_env = chain_env or get_chain_env()
    chain_org = chain_org or get_chain_org()
    payload = payload or {}

    # Concurrency-safe monotonic sequencing: serialize appenders on this chain scope
    # for the duration of the transaction.
    k1, k2 = _lock_keys(chain_env, chain_org)
    db.execute(text("SELECT pg_advisory_xact_lock(:k1, :k2)"), {"k1": k1, "k2": k2})

    last = db.execute(
        select(AuditEvent)
        .where(AuditEvent.chain_env == chain_env, AuditEvent.chain_org == chain_org)
        .order_by(AuditEvent.seq.desc())
        .limit(1)
    ).scalar_one_or_none()

    if last is None:
        seq = 0
        prev_hash = GENESIS_PREV_HASH
    else:
        seq = last.seq + 1
        prev_hash = last.hash

    ts = datetime.now(timezone.utc).isoformat()
    body = {
        "chain_env": chain_env,
        "chain_org": chain_org,
        "seq": seq,
        "timestamp": ts,
        "actor_id": actor_id,
        "actor_label": actor_label,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "payload": payload,
        "prev_hash": prev_hash,
    }
    canonical, digest = _compute_hash(body)

    event = AuditEvent(
        chain_env=chain_env, chain_org=chain_org, seq=seq, timestamp=ts,
        actor_id=actor_id, actor_label=actor_label, action=action,
        resource_type=resource_type, resource_id=resource_id, payload=payload,
        canonical=canonical, prev_hash=prev_hash, hash=digest,
    )
    db.add(event)
    db.flush()
    return event


def verify_chain(db: Session, chain_env: str | None = None, chain_org: str | None = None) -> dict:
    """Recompute and validate the full chain. Detects gaps, reorder, duplicates, tamper."""
    chain_env = chain_env or get_chain_env()
    chain_org = chain_org or get_chain_org()

    events = db.execute(
        select(AuditEvent)
        .where(AuditEvent.chain_env == chain_env, AuditEvent.chain_org == chain_org)
        .order_by(AuditEvent.seq.asc())
    ).scalars().all()

    issues: list[dict] = []
    seen_seq: set[int] = set()
    prev_hash = GENESIS_PREV_HASH
    expected_seq = 0

    for ev in events:
        if ev.seq in seen_seq:  # pragma: no cover  (uq_chain_seq prevents duplicate seq via the app)
            issues.append({"type": "duplicate", "seq": ev.seq})
            continue
        seen_seq.add(ev.seq)

        if ev.seq != expected_seq:
            issues.append({"type": "gap_or_reorder", "expected": expected_seq, "found": ev.seq})
            expected_seq = ev.seq  # resync to continue reporting

        # Field-tamper detection: canonical must match a fresh serialization of stored fields.
        body = {
            "chain_env": ev.chain_env, "chain_org": ev.chain_org, "seq": ev.seq,
            "timestamp": ev.timestamp, "actor_id": ev.actor_id, "actor_label": ev.actor_label,
            "action": ev.action, "resource_type": ev.resource_type, "resource_id": ev.resource_id,
            "payload": ev.payload, "prev_hash": ev.prev_hash,
        }
        recomputed_canonical, recomputed_hash = _compute_hash(body)
        if recomputed_canonical != ev.canonical:
            issues.append({"type": "field_tamper", "seq": ev.seq})
        if recomputed_hash != ev.hash:
            issues.append({"type": "hash_mismatch", "seq": ev.seq})
        if ev.prev_hash != prev_hash:
            issues.append({"type": "broken_link", "seq": ev.seq})

        prev_hash = ev.hash
        expected_seq += 1

    head = events[-1] if events else None
    return {
        "chain_env": chain_env,
        "chain_org": chain_org,
        "event_count": len(events),
        "verified": len(issues) == 0,
        "head_seq": head.seq if head else None,
        "head_hash": head.hash if head else None,
        "genesis_ok": (events[0].prev_hash == GENESIS_PREV_HASH) if events else True,
        "issues": issues,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


def create_checkpoint(db: Session, note: str = "", chain_env: str | None = None,
                      chain_org: str | None = None) -> AuditCheckpoint | None:
    chain_env = chain_env or get_chain_env()
    chain_org = chain_org or get_chain_org()
    report = verify_chain(db, chain_env, chain_org)
    if report["head_hash"] is None:
        return None
    cp = AuditCheckpoint(
        chain_env=chain_env, chain_org=chain_org, seq=report["head_seq"],
        hash=report["head_hash"], event_count=report["event_count"], note=note,
    )
    db.add(cp)
    db.flush()
    return cp
