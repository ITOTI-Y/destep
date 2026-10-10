"""Schedule converter for DeST to EnergyPlus IDF conversion.

Converts ScheduleYear data to:
- Schedule:Constant for schedules whose 8760 values never change
- Schedule:Compact for all other schedules, with explicit design-day profiles
- ScheduleTypeLimits (auto-generated based on schedule type)

Schedule:File cannot distinguish design days from ordinary days, so sizing
used whatever the hourly array held on the design-day date. In DeST data that
date is often a weekend (e.g. occupancy 0 on 7/21), which undersized zone
equipment. Schedule:Compact keeps ordinary days equal to the hourly array
while giving SummerDesignDay/WinterDesignDay a typical working-day profile.

Only schedules that are referenced by other objects are converted.
"""

from __future__ import annotations

import datetime
from collections import Counter, defaultdict
from enum import IntEnum
from typing import Any, Final

from idfpy.models import (
    ScheduleCompact,
    ScheduleConstant,
    ScheduleTypeLimits,
    SizingPeriodDesignDay,
)
from idfpy.models.schedules import ScheduleCompactDataItem
from loguru import logger
from sqlalchemy import select

from src.converters.base import BaseConverter
from src.database.models.schedule import ScheduleYear

HOURS_PER_YEAR: Final[int] = 8760
DAYS_PER_YEAR: Final[int] = 365

DEST_JAN1_WEEKDAY: Final[int] = 0
WEEKDAY_NAMES: Final[tuple[str, ...]] = (
    'Monday',
    'Tuesday',
    'Wednesday',
    'Thursday',
    'Friday',
    'Saturday',
    'Sunday',
)
SUNDAY: Final[int] = 6

DAYS_OF_YEAR = [
    datetime.date(2001, 1, 1) + datetime.timedelta(days=offset)
    for offset in range(DAYS_PER_YEAR)
]
SUMMER_MONTHS = frozenset({6, 7, 8, 9})
WINTER_MONTHS = frozenset({12, 1, 2})
SUMMER_DESIGN_DAY = 'SummerDesignDay'
WINTER_DESIGN_DAY = 'WinterDesignDay'

type DayProfile = tuple[float, ...]
type DesignDates = dict[tuple[int, int], str]


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
        return 'Fraction'

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

    unique_values = set(values)
    if unique_values <= {0.0, 1.0}:
        return 'On/Off'

    if min_val >= 0.0 and max_val <= 1.0:
        return 'Fraction'

    if all(v == int(v) for v in values):
        return 'Integer'

    return 'Any Number'


def hourly_values(data: list[int | float] | None) -> list[float]:
    """Validate DeST schedule data as exactly 8760 hourly values."""
    if data is None:
        raise ValueError('Schedule data is None')
    if len(data) != HOURS_PER_YEAR:
        raise ValueError(f'Expected {HOURS_PER_YEAR} values, got {len(data)}')
    return [float(item) for item in data]


def _day_profiles(values: list[float]) -> list[DayProfile]:
    # Rounding keeps float noise from splitting otherwise identical days.
    return [
        tuple(round(v, 6) for v in values[day * 24 : (day + 1) * 24])
        for day in range(DAYS_PER_YEAR)
    ]


def _design_day_profile(
    profiles: list[DayProfile],
    months: frozenset[int],
) -> DayProfile:
    """Most frequent non-zero in-season daily profile, i.e. a typical working day."""
    in_season = [
        profile
        for profile, day in zip(profiles, DAYS_OF_YEAR, strict=True)
        if day.month in months
    ]
    non_zero = [profile for profile in in_season if any(v != 0 for v in profile)]
    return Counter(non_zero or in_season).most_common(1)[0][0]


def _until_fields(profile: DayProfile) -> list[str]:
    fields: list[str] = []
    for hour in range(24):
        if hour == 23 or profile[hour + 1] != profile[hour]:
            fields += [f'Until: {hour + 1:02d}:00', f'{profile[hour]:.10g}']
    return fields


def _through(day_index: int) -> str:
    end = DAYS_OF_YEAR[day_index]
    return f'Through: {end.month:02d}/{end.day:02d}'


def _exact_fields(
    profiles: list[DayProfile],
    design_profiles: dict[str, DayProfile],
    design_dates: DesignDates,
) -> list[str]:
    """Date-exact encoding: runs of identical days become one Through block.

    Ordinary days keep their own hourly values regardless of the simulation
    calendar. A design-day date whose profile differs from the typical one gets
    a single-day block in which only the design day type uses the typical
    profile.
    """
    day_index = {(day.month, day.day): i for i, day in enumerate(DAYS_OF_YEAR)}
    overrides = {
        day_index[month_day]: day_type
        for month_day, day_type in design_dates.items()
        if month_day in day_index
        and profiles[day_index[month_day]] != design_profiles[day_type]
    }
    fields: list[str] = []
    start = 0
    for day in range(1, DAYS_PER_YEAR + 1):
        is_boundary = (
            day == DAYS_PER_YEAR
            or profiles[day] != profiles[start]
            or day in overrides
            or day - 1 in overrides
        )
        if not is_boundary:
            continue
        fields.append(_through(day - 1))
        if start in overrides:
            day_type = overrides[start]
            fields += [f'For: {day_type}', *_until_fields(design_profiles[day_type])]
            fields += ['For: AllOtherDays', *_until_fields(profiles[start])]
        else:
            fields += ['For: AllDays', *_until_fields(profiles[start])]
        start = day
    return fields


def _weekly_fields(
    profiles: list[DayProfile], design_profiles: dict[str, DayProfile]
) -> list[str]:
    """Weekday-group encoding.

    The year is split into maximal date ranges in which each weekday keeps one
    profile. EnergyPlus evaluates weekday names on the simulation calendar, so
    weekends follow the RunPeriod year rather than the DeST array's own
    calendar; this shifts results slightly (about -0.2% EUI for CoA in 2040).
    Sunday's profile also covers holidays and custom days.
    """
    summer = _until_fields(design_profiles[SUMMER_DESIGN_DAY])
    winter = _until_fields(design_profiles[WINTER_DESIGN_DAY])

    fields: list[str] = []
    start = 0
    while start < DAYS_PER_YEAR:
        by_weekday: dict[int, DayProfile] = {}
        end = start
        while end < DAYS_PER_YEAR:
            weekday = (DEST_JAN1_WEEKDAY + end) % 7
            if by_weekday.setdefault(weekday, profiles[end]) != profiles[end]:
                break
            end += 1

        groups: dict[DayProfile, list[int]] = defaultdict(list)
        for weekday, profile in by_weekday.items():
            groups[profile].append(weekday)
        sunday_profile = by_weekday.get(SUNDAY, profiles[start])

        fields += [
            _through(end - 1),
            f'For: {SUMMER_DESIGN_DAY}',
            *summer,
            f'For: {WINTER_DESIGN_DAY}',
            *winter,
        ]
        for profile, weekdays in groups.items():
            if profile == sunday_profile:
                continue
            names = ' '.join(WEEKDAY_NAMES[weekday] for weekday in sorted(weekdays))
            fields += [f'For: {names}', *_until_fields(profile)]
        fields += ['For: AllOtherDays', *_until_fields(sunday_profile)]
        start = end
    return fields


def encode_schedule(
    values: list[float], design_dates: DesignDates
) -> float | list[str]:
    """Return the constant value, or the shorter Schedule:Compact encoding."""
    profiles = _day_profiles(values)
    distinct = {value for profile in profiles for value in profile}
    if len(distinct) == 1:
        return distinct.pop()

    design_profiles = {
        SUMMER_DESIGN_DAY: _design_day_profile(profiles, SUMMER_MONTHS),
        WINTER_DESIGN_DAY: _design_day_profile(profiles, WINTER_MONTHS),
    }
    return min(
        _exact_fields(profiles, design_profiles, design_dates),
        _weekly_fields(profiles, design_profiles),
        key=len,
    )


class ScheduleConverter(BaseConverter[ScheduleYear]):
    """Converts DeST ScheduleYear to IDF schedules and ScheduleTypeLimits.

    This converter handles:
    - ScheduleTypeLimits: Auto-generated based on DeST schedule type code
    - Schedule:Constant: Schedules whose hourly values never change
    - Schedule:Compact: All other schedules, with design-day profiles

    Only schedules registered in lookup_table.REQUIRED_SCHEDULE_IDS are converted.
    Other converters should add schedule IDs to lookup_table.REQUIRED_SCHEDULE_IDS
    when they reference schedules. Design-day dates are read from the
    SizingPeriod:DesignDay objects that SizingConverter has already added.

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
        self._design_dates: DesignDates = {}

    def _read_design_dates(self) -> DesignDates:
        """Collect (month, day) -> design day type from SizingPeriod:DesignDay."""
        design_dates: DesignDates = {}
        for design_day in self.idf.all_of_type(SizingPeriodDesignDay).values():
            if design_day.day_type in (SUMMER_DESIGN_DAY, WINTER_DESIGN_DAY):
                design_dates[(design_day.month, design_day.day_of_month)] = (
                    design_day.day_type
                )
        return design_dates

    def convert_all(self) -> None:
        """Convert required ScheduleYear objects to IDF schedules.

        Only schedules in lookup_table.REQUIRED_SCHEDULE_IDS are converted.
        If no schedules are required, nothing is converted.

        Steps:
        1. Read required schedule IDs from lookup_table
        2. Read design-day dates from the IDF
        3. Query only the required schedules
        4. Create ScheduleTypeLimits objects
        5. Convert each schedule to Schedule:Constant or Schedule:Compact

        Raises:
            ValueError: If a required schedule is absent from the database or
                fails to convert. A missing schedule would otherwise only
                surface as an EnergyPlus fatal error about an undefined
                schedule reference.
        """
        required_ids = self.lookup_table.REQUIRED_SCHEDULE_IDS
        if not required_ids:
            logger.info('No schedules marked as required, skipping schedule conversion')
            return

        self._design_dates = self._read_design_dates()
        if not self._design_dates:
            logger.warning(
                'No SizingPeriod:DesignDay found; design days will use the '
                'typical profile only where the weekday encoding is chosen'
            )

        stmt = select(ScheduleYear).where(ScheduleYear.schedule_id.in_(required_ids))
        schedules = self.session.execute(stmt).scalars().all()
        self.stats.total = len(schedules)

        logger.info(
            f'Converting {len(schedules)} required schedules '
            f'out of {len(required_ids)} requested'
        )

        found_ids = {s.schedule_id for s in schedules}
        missing_ids = required_ids - found_ids
        if missing_ids:
            raise ValueError(
                f'{len(missing_ids)} required schedule IDs are missing from the '
                f'database: {sorted(missing_ids)}'
            )

        type_limits_needed: set[str] = set()
        for schedule in schedules:
            limits_name = self._determine_type_limits(schedule)
            type_limits_needed.add(limits_name)

        self._create_schedule_type_limits(type_limits_needed)

        failed_ids: list[int] = []
        for schedule in schedules:
            if self.convert_one(schedule):
                self.stats.converted += 1
            else:
                self.stats.errors += 1
                failed_ids.append(schedule.schedule_id)

        self.log_stats()
        if failed_ids:
            raise ValueError(
                f'{len(failed_ids)} schedules failed to convert: {sorted(failed_ids)}'
            )

    def convert_one(self, instance: ScheduleYear) -> bool:
        """Convert a single DeST ScheduleYear to Schedule:Constant or Compact.

        Args:
            instance: DeST ScheduleYear model instance.

        Returns:
            True if conversion succeeded, False otherwise.
        """
        try:
            name = self.make_name('Schedule', instance.schedule_id, instance.name)
            limits_name = self._determine_type_limits(instance)

            encoded = encode_schedule(hourly_values(instance.data), self._design_dates)
            if isinstance(encoded, list):
                self.idf.add(
                    ScheduleCompact(
                        name=name,
                        schedule_type_limits_name=limits_name,
                        data=[
                            ScheduleCompactDataItem(field=field) for field in encoded
                        ],
                    )
                )
                kind = f'Schedule:Compact ({len(encoded)} fields)'
            else:
                self.idf.add(
                    ScheduleConstant(
                        name=name,
                        schedule_type_limits_name=limits_name,
                        hourly_value=encoded,
                    )
                )
                kind = 'Schedule:Constant'

            self.lookup_table.SCHEDULE_TO_NAME[instance.schedule_id] = name

            logger.debug(
                f'Converted Schedule: {name} -> {kind} (type_limits={limits_name})'
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
        if schedule.type is not None:
            return get_schedule_type_limits_name(schedule.type)

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
                self.stats.add_warning(
                    f'ScheduleTypeLimits {name} creation failed: {e}'
                )
