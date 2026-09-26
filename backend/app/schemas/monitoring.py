from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

ApiStatus = Literal["ok", "error"]


class ApiCheckOut(BaseModel):
    direct: ApiStatus
    metrika: ApiStatus
