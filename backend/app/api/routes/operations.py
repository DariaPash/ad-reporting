from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_operation_log_repository, require_admin
from app.repositories.operation_log_repository import OperationLogRepository
from app.schemas.operation_log import OperationLogOut

# Журнал операций – раздел администрирования: доступен только роли admin.
router = APIRouter(
    prefix="/operations",
    tags=["operations"],
    dependencies=[Depends(require_admin)],
)


@router.get("", response_model=list[OperationLogOut])
def list_operations(
    operations: Annotated[
        OperationLogRepository, Depends(get_operation_log_repository)
    ],
    status: Annotated[
        str | None, Query(pattern="^(running|success|error)$")
    ] = None,
    limit: Annotated[int, Query(le=200)] = 50,
    offset: int = 0,
) -> list[OperationLogOut]:
    """Журнал операций. Токены и секреты в него не попадают (гарантирует
    OperationLogRepository)."""
    return [
        OperationLogOut.model_validate(o)
        for o in operations.list(status=status, limit=limit, offset=offset)
    ]
