from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from src.database.models.fenestration import Door, Window
from src.idf import IDF
from src.utils.pinyin import PinyinConverter

from .base import BaseConverter

if TYPE_CHECKING:
    from .manager import LookupTable


class FenestrationConverter(BaseConverter[Window | Door]):
    def __init__(
        self,
        session: Session,
        idf: IDF,
        lookup_table: LookupTable,
        pinyin: PinyinConverter | None = None,
    ) -> None:
        super().__init__(session, idf, lookup_table, pinyin)

    def convert_all(self) -> None:
        pass

    def convert_one(self, instance: Window | Door) -> bool:
        return False
