from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ._base import Base


class ScheduleYear(Base):
    """Schedule year model."""

    __tablename__ = 'schedule_year'

    schedule_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Schedule ID'
    )
    type: Mapped[int | None] = mapped_column(Integer, comment='Schedule type')
    name: Mapped[str | None] = mapped_column(String(255), comment='Schedule name')
    data: Mapped[list | None] = mapped_column(comment='Schedule data (JSON)')
