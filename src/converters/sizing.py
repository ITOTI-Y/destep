"""Sizing converter for DeST to EnergyPlus IDF conversion.

This module converts DeST DesignDay models to EnergyPlus SizingPeriod:DesignDay objects.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from sqlalchemy import select

from src.converters.base import BaseConverter
from src.database.models.environment import Environment
from src.idf.models.location import SizingPeriodDesignDay
from src.utils.ddy_downloader import DDY

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from src.idf import IDF
    from src.idf.models.location import SizingPeriodDesignDay
    from src.utils.pinyin import PinyinConverter

    from .manager import LookupTable


@dataclass
class MappingItem:
    winter: str = 'Htg 99.6% Condns DB'
    summer: str = 'Clg .4% Condns DB=>MWB'


class SizingConverter(BaseConverter[Environment]):
    """Converter for DeST DesignDay to EnergyPlus SizingPeriod:DesignDay.

    Each DesignDay in DeST becomes a SizingPeriod:DesignDay in EnergyPlus.
    """

    def __init__(
        self,
        session: Session,
        idf: IDF,
        lookup_table: LookupTable,
        pinyin: PinyinConverter | None = None,
    ) -> None:
        """Initialize converter.

        Args:
            session: SQLAlchemy session for database queries.
            idf: IDF instance to add converted objects to.
            pinyin: PinyinConverter for Chinese name conversion.
        """
        super().__init__(session, idf, lookup_table, pinyin)
        self._created_design_days: set[int] = set()

    def convert_all(self) -> None:
        stmt = select(Environment)
        environments = self.session.execute(stmt).scalars().all()
        for environment in environments:
            self.convert_one(environment)

    def convert_one(self, instance: Environment) -> bool:
        """Convert a single DeST Environment to IDF SizingPeriod:DesignDay.

        Args:
            instance: DeST Environment model instance.

        Returns:
            True if conversion succeeded, False otherwise.
        """
        environment = instance
        assert environment.city_name is not None
        ddy_data = self._get_ddy_data(environment.city_name)
        if not ddy_data:
            self.stats.errors += 1
            self.stats.add_warning(
                f'No DDY data found for city {environment.city_name}'
            )
            return False
        for ddy_item in ddy_data.values():
            assert isinstance(ddy_item, SizingPeriodDesignDay)
            if (
                MappingItem.winter in ddy_item.name
                or MappingItem.summer in ddy_item.name
            ):
                self.idf.add(ddy_item)
                self.stats.converted += 1
            else:
                self.stats.skipped += 1
        return True

    def _get_ddy_data(self, city: str) -> dict:
        """Get DDY data from embedded JSON file.

        Returns:
            dict[str, dict] with city name as key and DDY data as value.
        """
        ddy = DDY()
        ddy_data = ddy.get_weather_locations(city).all_of_type('SizingPeriod:DesignDay')
        return ddy_data
