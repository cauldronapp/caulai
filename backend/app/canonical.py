"""Deterministic canonical serialization used for hashing audit events and payload digests."""
import json
import hashlib
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID


def _default(o):
    if isinstance(o, (datetime, date)):
        return o.isoformat()
    if isinstance(o, Decimal):
        return str(o)
    if isinstance(o, UUID):
        return str(o)
    raise TypeError(f"Type {type(o)} is not canonically serializable")


def canonical_json(obj) -> str:
    """Stable, whitespace-free, key-sorted JSON. Same input -> byte-identical output."""
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=_default,
    )


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def payload_digest(payload: dict) -> str:
    """Digest that binds an approval to an exact action payload."""
    return sha256_hex(canonical_json(payload))
