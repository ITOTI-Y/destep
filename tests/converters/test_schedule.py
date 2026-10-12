import pytest

from src.converters.schedule import (
    DAYS_PER_YEAR,
    SUMMER_DESIGN_DAY,
    SUMMER_MONTHS,
    WINTER_DESIGN_DAY,
    WINTER_MONTHS,
    DayProfile,
    _day_profiles,
    _design_day_profile,
    _exact_fields,
)

WORKDAY = [0.0] * 8 + [1.0] * 10 + [0.0] * 6
WEEKEND = [0.0] * 24
BOTH_DESIGN_DAYS = frozenset({SUMMER_DESIGN_DAY, WINTER_DESIGN_DAY})


@pytest.fixture
def profiles() -> list[DayProfile]:
    # Day index 0 is a Monday; days 5 and 6 of each week are the weekend.
    values = [
        value
        for day in range(DAYS_PER_YEAR)
        for value in (WEEKEND if day % 7 in (5, 6) else WORKDAY)
    ]
    return _day_profiles(values)


@pytest.fixture
def design_profiles(profiles: list[DayProfile]) -> dict[str, DayProfile]:
    return {
        SUMMER_DESIGN_DAY: _design_day_profile(profiles, SUMMER_MONTHS),
        WINTER_DESIGN_DAY: _design_day_profile(profiles, WINTER_MONTHS),
    }


def _block(fields: list[str], through: str) -> list[str]:
    start = fields.index(through)
    end = next(
        (i for i in range(start + 1, len(fields)) if fields[i].startswith('Through:')),
        len(fields),
    )
    return fields[start:end]


def test_shared_date_gets_both_design_day_overrides(
    profiles: list[DayProfile], design_profiles: dict[str, DayProfile]
) -> None:
    # 1/20 is day index 19, a Saturday in the DeST calendar.
    fields = _exact_fields(profiles, design_profiles, {(1, 20): BOTH_DESIGN_DAYS})

    block = _block(fields, 'Through: 01/20')
    assert f'For: {SUMMER_DESIGN_DAY}' in block
    assert f'For: {WINTER_DESIGN_DAY}' in block
    assert block[-3:] == ['For: AllOtherDays', 'Until: 24:00', '0']


def test_design_date_on_workday_needs_no_override(
    profiles: list[DayProfile], design_profiles: dict[str, DayProfile]
) -> None:
    # 1/22 is day index 21, a Monday that already has the typical profile.
    fields = _exact_fields(profiles, design_profiles, {(1, 22): BOTH_DESIGN_DAYS})

    assert f'For: {SUMMER_DESIGN_DAY}' not in fields
    assert f'For: {WINTER_DESIGN_DAY}' not in fields
