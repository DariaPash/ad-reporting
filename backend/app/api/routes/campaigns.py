from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_campaign_repository, get_import_service
from app.repositories.campaign_repository import CampaignRepository
from app.schemas.campaign import CampaignOut, CampaignSyncResult
from app.services.import_service import ImportService

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.get("", response_model=list[CampaignOut])
def list_campaigns(
    campaigns: Annotated[CampaignRepository, Depends(get_campaign_repository)],
    search: str | None = None,
) -> list[CampaignOut]:
    """Список/поиск кампаний для формы отчёта."""
    return [
        CampaignOut.model_validate(c) for c in campaigns.list(search=search)
    ]


@router.post("/sync", response_model=CampaignSyncResult)
def sync_campaigns(
    import_service: Annotated[ImportService, Depends(get_import_service)],
) -> CampaignSyncResult:
    """Обновить справочник кампаний из Яндекс Директа."""
    return import_service.sync_campaigns()
