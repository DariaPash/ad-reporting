from __future__ import annotations

import datetime

from pydantic import BaseModel, ConfigDict


class CampaignOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    direct_campaign_id: int
    name: str
    state: str | None
    status: str | None
    updated_at: datetime.datetime


class CampaignSyncResult(BaseModel):
    created: int
    updated: int
