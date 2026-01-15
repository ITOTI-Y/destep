"""Schedule converter for DeST to EnergyPlus IDF conversion.

Converts ScheduleYear data to:
- Schedule:File (references external CSV files with hourly values)
- ScheduleTypeLimits (auto-generated based on schedule type)
- CSV files containing 8760 hourly values

Only schedules that are referenced by other objects are converted.
"""

from __future__ import annotations

import csv
from enum import IntEnum
from pathlib import Path
from typing import Any

from loguru import logger
from sqlalchemy import select

from src.converters.base import BaseConverter
from src.database.models.schedule import ScheduleYear
from src.idf.models.schedules import (
    ScheduleFile,
    ScheduleTypeLimits,
)


class DestScheduleType(IntEnum):
    """DeST schedule type enumeration.

    DeST schedule type codes:
    - 1: ratio (0-1 fraction)
    - 2: on_off (binary 0 or 1)
    - 3: Int (integer values)
    - 4: float (floating point)
    - 5: double (double precision)

    Note: All data values are stored as double in DeST database.
    """

    RATIO = 1  # 0-1 fraction (e.g., lighting, equipment, occupancy)
    ON_OFF = 2  # Binary on/off (0 or 1)
    INT = 3  # Integer values
    FLOAT = 4  # Floating point values
    DOUBLE = 5  # Double precision values


# Predefined ScheduleTypeLimits for DeST schedule types
SCHEDULE_TYPE_LIMITS_DEFS: dict[str, dict[str, Any]] = {
    'Fraction': {
        'lower_limit_value': 0.0,
        'upper_limit_value': 1.0,
        'numeric_type': 'Continuous',
        'unit_type': 'Dimensionless',
    },
    'On/Off': {
        'lower_limit_value': 0.0,
        'upper_limit_value': 1.0,
        'numeric_type': 'Discrete',
        'unit_type': 'Availability',
    },
    'Integer': {
        'lower_limit_value': None,
        'upper_limit_value': None,
        'numeric_type': 'Discrete',
        'unit_type': 'Dimensionless',
    },
    'Any Number': {
        'lower_limit_value': None,
        'upper_limit_value': None,
        'numeric_type': 'Continuous',
        'unit_type': 'Dimensionless',
    },
}

# Mapping from DeST type code to ScheduleTypeLimits name
DEST_TYPE_TO_LIMITS: dict[int, str] = {
    DestScheduleType.RATIO: 'Fraction',
    DestScheduleType.ON_OFF: 'On/Off',
    DestScheduleType.INT: 'Integer',
    DestScheduleType.FLOAT: 'Any Number',
    DestScheduleType.DOUBLE: 'Any Number',
}


def get_schedule_type_limits_name(schedule_type: int | None) -> str:
    """Map DeST schedule type to ScheduleTypeLimits name.

    Args:
        schedule_type: DeST schedule type code (1-5).

    Returns:
        Name of the ScheduleTypeLimits to use.
    """
    if schedule_type is None:
        return 'Fraction'  # Default to fraction for unknown types

    return DEST_TYPE_TO_LIMITS.get(schedule_type, 'Any Number')


def infer_schedule_type_from_values(values: list[float]) -> str:
    """Infer ScheduleTypeLimits name from schedule values.

    Used as fallback when no explicit type is provided.

    Args:
        values: List of numeric values from the schedule.

    Returns:
        Inferred ScheduleTypeLimits name.
    """
    if not values:
        return 'Fraction'

    min_val = min(values)
    max_val = max(values)

    # Check if binary (0 or 1 only)
    unique_values = set(values)
    if unique_values <= {0.0, 1.0}:
        return 'On/Off'

    # Check if fraction (0-1)
    if min_val >= 0.0 and max_val <= 1.0:
        return 'Fraction'

    # Check if all integers
    if all(v == int(v) for v in values):
        return 'Integer'

    return 'Any Number'


class ScheduleConverter(BaseConverter[ScheduleYear]):
    """Converts DeST ScheduleYear to IDF Schedule:File and ScheduleTypeLimits.

    This converter handles:
    - ScheduleTypeLimits: Auto-generated based on DeST schedule type code
    - Schedule:File: References external CSV files with 8760 hourly values
    - CSV files: Generated in a 'schedules' subdirectory

    Only schedules that are referenced by other objects are converted.
    Use add_required_schedule() or set_required_schedule_ids() to specify
    which schedules should be converted.

    DeST Schedule Types:
    - 1: ratio (0-1 fraction) -> Fraction
    - 2: on_off (binary) -> On/Off
    - 3: Int (integer) -> Integer
    - 4: float -> Any Number
    - 5: double -> Any Number

    Note: DeST stores schedule data as an array of 8760 hourly values (one year).
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize ScheduleConverter."""
        super().__init__(*args, **kwargs)
        self._created_type_limits: set[str] = set()
        self._output_dir: Path | None = None
        self._schedules_dir: Path | None = None
        self._required_schedule_ids: set[int] = set()
        self._converted_schedules: dict[int, str] = {}  # schedule_id -> idf_name

    def set_output_dir(self, output_dir: Path) -> None:
        """Set the output directory for CSV files.

        Args:
            output_dir: Base output directory for IDF and related files.
        """
        self._output_dir = output_dir
        self._schedules_dir = output_dir / 'schedules'

    def add_required_schedule(self, schedule_id: int | None) -> None:
        """Mark a schedule as required for conversion.

        Call this method to register schedules that are referenced
        by other objects (e.g., gains, HVAC, fenestration).

        Args:
            schedule_id: Schedule ID to mark as required. None is ignored.
        """
        if schedule_id is not None:
            self._required_schedule_ids.add(schedule_id)

    def set_required_schedule_ids(self, schedule_ids: set[int]) -> None:
        """Set the complete set of required schedule IDs.

        Args:
            schedule_ids: Set of schedule IDs that should be converted.
        """
        self._required_schedule_ids = schedule_ids.copy()

    def get_schedule_name(self, schedule_id: int | None) -> str | None:
        """Get the IDF schedule name for a given schedule ID.

        Use this after conversion to get the IDF name for cross-references.

        Args:
            schedule_id: DeST schedule ID.

        Returns:
            IDF schedule name if converted, None otherwise.
        """
        if schedule_id is None:
            return None
        return self._converted_schedules.get(schedule_id)

    def convert_all(self) -> None:
        """Convert required ScheduleYear objects to IDF schedules.

        Only schedules marked as required are converted.
        If no schedules are marked as required, nothing is converted.

        Steps:
        1. Create schedules output directory
        2. Query only the required schedules
        3. Create ScheduleTypeLimits objects
        4. Convert each schedule to Schedule:File + CSV
        """
        if not self._required_schedule_ids:
            logger.info('No schedules marked as required, skipping schedule conversion')
            return

        # Ensure output directory is set
        if self._output_dir is None:
            logger.warning('Output directory not set, using current directory')
            self._output_dir = Path('.')

        # Always set schedules_dir based on output_dir
        self._schedules_dir = self._output_dir / 'schedules'

        # Create schedules directory
        self._schedules_dir.mkdir(parents=True, exist_ok=True)

        # Query only required schedules
        stmt = select(ScheduleYear).where(
            ScheduleYear.schedule_id.in_(self._required_schedule_ids)
        )
        schedules = self.session.execute(stmt).scalars().all()
        self.stats.total = len(schedules)

        logger.info(
            f'Converting {len(schedules)} required schedules '
            f'out of {len(self._required_schedule_ids)} requested'
        )

        # Check for missing schedules
        found_ids = {s.schedule_id for s in schedules}
        missing_ids = self._required_schedule_ids - found_ids
        if missing_ids:
            logger.warning(f'Missing schedule IDs in database: {missing_ids}')

        # First pass: determine which ScheduleTypeLimits are needed
        type_limits_needed: set[str] = set()
        for schedule in schedules:
            limits_name = self._determine_type_limits(schedule)
            type_limits_needed.add(limits_name)

        # Create ScheduleTypeLimits objects
        self._create_schedule_type_limits(type_limits_needed)

        # Second pass: convert all required schedules
        for schedule in schedules:
            if self.convert_one(schedule):
                self.stats.converted += 1
            else:
                self.stats.errors += 1

        self.log_stats()

    def convert_one(self, instance: ScheduleYear) -> bool:
        """Convert a single DeST ScheduleYear to IDF Schedule:File.

        Creates a CSV file with hourly values and adds Schedule:File
        reference to the IDF.

        Args:
            instance: DeST ScheduleYear model instance.

        Returns:
            True if conversion succeeded, False otherwise.
        """
        try:
            name = self.make_name('Schedule', instance.schedule_id, instance.name)
            limits_name = self._determine_type_limits(instance)

            # Ensure schedules_dir is set
            if self._schedules_dir is None:
                raise RuntimeError('Schedules directory not initialized')

            # Generate CSV filename
            csv_filename = f'{name}.csv'
            csv_path = self._schedules_dir / csv_filename

            # Write CSV file with hourly values
            self._write_schedule_csv(csv_path, instance.data)

            # Create Schedule:File reference
            # Use relative path from IDF location
            relative_csv_path = f'schedules/{csv_filename}'

            schedule_file = ScheduleFile(
                name=name,
                schedule_type_limits_name=limits_name,
                file_name=relative_csv_path,
                column_number=1,  # First column contains values
                rows_to_skip_at_top=0,  # No header row
                number_of_hours_of_data=8760.0,
                column_separator='Comma',
                interpolate_to_timestep='No',
                minutes_per_item=60,  # Hourly values
                adjust_schedule_for_daylight_savings='No',
            )

            self.idf.add(schedule_file)

            # Record the mapping for cross-references
            self._converted_schedules[instance.schedule_id] = name

            logger.debug(
                f'Converted Schedule: {name} -> {relative_csv_path} '
                f'(type_limits={limits_name})'
            )
            return True

        except Exception as e:
            logger.error(f'Failed to convert Schedule {instance.schedule_id}: {e}')
            self.stats.add_warning(
                f'Schedule {instance.schedule_id} conversion failed: {e}'
            )
            return False

    def _determine_type_limits(self, schedule: ScheduleYear) -> str:
        """Determine the appropriate ScheduleTypeLimits for a schedule.

        First tries to use the explicit type code, then falls back
        to inferring from values.

        Args:
            schedule: DeST ScheduleYear object.

        Returns:
            Name of the ScheduleTypeLimits to use.
        """
        # Use explicit type code if available
        if schedule.type is not None:
            return get_schedule_type_limits_name(schedule.type)

        # Fallback: infer from values
        values = self._extract_numeric_values(schedule.data)
        return infer_schedule_type_from_values(values)

    def _extract_numeric_values(self, data: list[Any] | None) -> list[float]:
        """Extract numeric values from schedule data.

        Args:
            data: Raw schedule data (list of 8760 hourly values).

        Returns:
            List of numeric values.
        """
        if not data:
            return []

        values: list[float] = []
        for item in data:
            if isinstance(item, (int, float)):
                values.append(float(item))
        return values

    def _write_schedule_csv(self, csv_path: Path, data: list[Any] | None) -> None:
        """Write schedule data to CSV file.

        Creates a CSV file with one value per row, 8760 rows total.
        Missing or insufficient data is padded with zeros.

        Args:
            csv_path: Path to the output CSV file.
            data: Schedule data (8760 hourly values).
        """
        # Ensure we have exactly 8760 values
        values: list[float] = []
        if data:
            for item in data:
                if isinstance(item, (int, float)):
                    values.append(float(item))
                else:
                    values.append(0.0)

        # Pad with zeros if insufficient data
        while len(values) < 8760:
            values.append(0.0)

        # Truncate if too much data
        values = values[:8760]

        # Write CSV file
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            for value in values:
                writer.writerow([value])

        logger.debug(f'Wrote schedule CSV: {csv_path} ({len(values)} values)')

    def _create_schedule_type_limits(self, type_names: set[str]) -> None:
        """Create ScheduleTypeLimits objects for the required types.

        Args:
            type_names: Set of ScheduleTypeLimits names to create.
        """
        for name in type_names:
            if name in self._created_type_limits:
                continue

            definition = SCHEDULE_TYPE_LIMITS_DEFS.get(name)
            if definition is None:
                logger.warning(f'Unknown ScheduleTypeLimits: {name}, using Any Number')
                definition = SCHEDULE_TYPE_LIMITS_DEFS['Any Number']
                name = 'Any Number'

            if name in self._created_type_limits:
                continue

            try:
                type_limits = ScheduleTypeLimits(name=name, **definition)
                self.idf.add(type_limits)
                self._created_type_limits.add(name)
                logger.info(f'Created ScheduleTypeLimits: {name}')
            except Exception as e:
                logger.error(f'Failed to create ScheduleTypeLimits {name}: {e}')
                self.stats.add_warning(
                    f'ScheduleTypeLimits {name} creation failed: {e}'
                )
