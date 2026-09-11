from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.campaign import Campaign


class CampaignRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list(self, search: str | None = None) -> list[Campaign]:
        stmt = select(Campaign).order_by(Campaign.name)
        if search:
            stmt = stmt.where(Campaign.name.ilike(f"%{search}%"))
        return list(self._db.scalars(stmt))

    def get(self, campaign_id: int) -> Campaign | None:
        return self._db.get(Campaign, campaign_id)

    def get_many(self, campaign_ids: list[int]) -> list[Campaign]:
        if not campaign_ids:
            return []
        stmt = select(Campaign).where(Campaign.id.in_(campaign_ids))
        return list(self._db.scalars(stmt))

    def get_by_direct_id(self, direct_campaign_id: int) -> Campaign | None:
        stmt = select(Campaign).where(
            Campaign.direct_campaign_id == direct_campaign_id
        )
        return self._db.scalars(stmt).one_or_none()

    def upsert_from_direct(
        self,
        direct_campaign_id: int,
        name: str,
        state: str | None,
        status: str | None,
    ) -> tuple[Campaign, bool]:
        """Создаёт или обновляет кампанию из Директа (только запись в БД).
        Возвращает (кампания, была_ли_создана)."""
        campaign = self.get_by_direct_id(direct_campaign_id)
        if campaign is None:
            campaign = Campaign(
                direct_campaign_id=direct_campaign_id,
                name=name,
                state=state,
                status=status,
            )
            self._db.add(campaign)
            return campaign, True
        campaign.name = name
        campaign.state = state
        campaign.status = status
        return campaign, False
