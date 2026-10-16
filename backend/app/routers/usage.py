"""DEV-ONLY usage/value measurement endpoints. Default-deny RBAC; audited purge."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_permission
from ..models import User
from .. import usage

router = APIRouter(prefix="/api/usage", tags=["usage"])


@router.get("/metrics")
def metrics(days: int = Query(30, ge=0, le=365), min_cell: int = Query(5, ge=1),
            tenant_ref: str | None = Query(None),
            db: Session = Depends(get_db),
            user: User = Depends(require_permission("usage:read"))):
    return usage.compute_metrics(db, window_days=days, min_cell=min_cell, tenant_ref=tenant_ref)


class PurgeIn(BaseModel):
    tenant_ref: str | None = None
    account_ref: str | None = None


@router.post("/purge")
def purge(body: PurgeIn, db: Session = Depends(get_db),
          user: User = Depends(require_permission("usage:purge"))):
    if body.tenant_ref:
        return usage.purge_tenant(db, body.tenant_ref, actor=user)
    if body.account_ref:
        return usage.purge_account_raw(db, body.account_ref, actor=user)
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="Provide tenant_ref or account_ref")
