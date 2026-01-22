"""Base converter classes and utilities for DeST to IDF conversion.

This module provides:
- UnitConverter: Static methods for unit conversion
- ConversionStats: Statistics tracking for conversion process
- BaseConverter: Abstract base class for all converters
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, TypeVar

from loguru import logger

from src.idf import IDF
from src.utils.pinyin import PinyinConverter

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from .manager import LookupTable

T = TypeVar('T')


class UnitConverter:
    """Static utility class for unit conversions.

    DeST uses millimeters for dimensions, while EnergyPlus uses meters.
    """

    MM_TO_M = 0.001

    @staticmethod
    def mm_to_m(value: float | None) -> float:
        """Convert millimeters to meters.

        Args:
            value: Value in millimeters, or None.

        Returns:
            Value in meters. Returns 0.0 if input is None.
        """
        if value is None:
            return 0.0
        return value * UnitConverter.MM_TO_M

    @staticmethod
    def round_coord(value: float | None, decimals: int = 3) -> float:
        """Round coordinate value to specified decimal places.

        Args:
            value: Coordinate value.
            decimals: Number of decimal places (default 3).

        Returns:
            Rounded value.
        """
        if value is None:
            raise ValueError(f'Value is error: {value}')
        return round(value, decimals)


@dataclass
class ConversionStats:
    """Statistics for tracking conversion progress.

    Attributes:
        total: Total number of source objects.
        converted: Successfully converted objects.
        skipped: Objects skipped (e.g., empty data).
        errors: Objects that failed conversion.
        warnings: List of warning messages.
    """

    total: int = 0
    converted: int = 0
    skipped: int = 0
    errors: int = 0
    warnings: list[str] = field(default_factory=list)

    def add_warning(self, message: str) -> None:
        """Add a warning message.

        Args:
            message: Warning message to add.
        """
        self.warnings.append(message)
        logger.warning(message)

    def summary(self) -> str:
        """Generate a summary string.

        Returns:
            Human-readable summary of conversion statistics.
        """
        return (
            f'Total: {self.total}, '
            f'Converted: {self.converted}, '
            f'Skipped: {self.skipped}, '
            f'Errors: {self.errors}'
        )


class BaseConverter[T](ABC):
    """Abstract base class for all DeST to IDF converters.

    Each converter transforms one type of DeST database model
    into corresponding EnergyPlus IDF objects.

    Type Parameters:
        T: The SQLAlchemy model type this converter handles.

    Attributes:
        session: SQLAlchemy database session.
        idf: Target IDF container for converted objects.
        pinyin: PinyinConverter for name generation.
        stats: Conversion statistics tracker.
    """

    def __init__(
        self,
        session: Session,
        idf: IDF,
        lookup_table: LookupTable,
        pinyin: PinyinConverter | None = None,
    ) -> None:
        """Initialize converter with database session and IDF container.

        Args:
            session: SQLAlchemy session for database queries.
            idf: IDF instance to add converted objects to.
            pinyin: PinyinConverter for Chinese name conversion.
                    If None, creates a default instance.
        """
        self.session = session
        self.idf = idf
        self.pinyin = pinyin or PinyinConverter()
        self.stats = ConversionStats()
        self.lookup_table = lookup_table

    @abstractmethod
    def convert_all(self) -> None:
        """Convert all objects of this type from the database.

        Subclasses must implement this method to:
        1. Query all relevant objects from the database
        2. Call convert_one() for each object
        3. Update self.stats accordingly
        """

    @abstractmethod
    def convert_one(self, instance: T) -> bool:
        """Convert a single database object to IDF objects.

        Args:
            instance: Database model instance to convert.

        Returns:
            True if conversion succeeded, False otherwise.
        """

    def make_name(
        self,
        prefix: str,
        id_: int,
        chinese_name: str | None = None,
    ) -> str:
        """Generate a unique IDF object name.

        Format: {prefix}_{id}[_{pinyin_name}]

        Args:
            prefix: Object type prefix (e.g., 'Zone', 'Surface').
            id_: Unique identifier from the database.
            chinese_name: Optional Chinese name to include as pinyin.

        Returns:
            Generated name string.
        """
        if chinese_name:
            pinyin_name = self.pinyin.convert(chinese_name)
            return f'{prefix}_{id_}_{pinyin_name}'
        return f'{prefix}_{id_}'

    def log_stats(self) -> None:
        """Log conversion statistics."""
        converter_name = self.__class__.__name__
        logger.info(f'{converter_name}: {self.stats.summary()}')
