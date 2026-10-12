from unittest.mock import MagicMock

import pytest
from idfpy import IDF
from idfpy.models import ElectricEquipment, IDFBaseModel, Lights, People

from src.converters.internal_gains import InternalGainsConverter, occupant_activity
from src.converters.manager import LookupTable
from src.database.models.building import Room
from src.database.models.misc import RoomTypeData
from src.database.models.schedule import ScheduleYear
from src.utils.pinyin import PinyinConverter


def _schedule(schedule_id: int) -> ScheduleYear:
    return ScheduleYear(schedule_id=schedule_id, name=f's{schedule_id}', type=1)


def _room_type(**overrides: object) -> RoomTypeData:
    values: dict[str, object] = {
        'id': 1,
        'name': 'office',
        'o_maxnumber': 0.1,
        'o_minnumber': 0.0,
        'o_heat_per_person': 66.0,
        'o_damp_per_person': 109.0,
        'o_per_area': 1,
        'l_maxpower': 11.0,
        'l_minpower': 0.0,
        'l_heat_rate': 0.9,
        'l_per_area': 1,
        'e_maxpower': 20.0,
        'e_minpower': 0.0,
        'e_per_area': 1,
    }
    values.update(overrides)
    room_type = RoomTypeData(**values)
    room_type.occupant_schedule = _schedule(11)
    room_type.lighting_schedule = _schedule(12)
    room_type.equipment_schedule = _schedule(13)
    return room_type


@pytest.fixture
def converter() -> InternalGainsConverter:
    converter = object.__new__(InternalGainsConverter)
    converter.idf = IDF()
    converter.lookup_table = LookupTable(ROOM_TO_ZONE={7: 'Zone_7'})
    converter.stats = MagicMock(converted=0, skipped=0)
    converter.pinyin = PinyinConverter()
    converter._created_activity_type_limits = False
    converter._lighting_corrections = {}
    return converter


def _convert(converter: InternalGainsConverter, room_type: RoomTypeData | None) -> bool:
    room = Room(id=7, name='r7', type=room_type.id if room_type else None)
    room.room_type = room_type
    return converter.convert_one(room)


def _only[T: IDFBaseModel](converter: InternalGainsConverter, model: type[T]) -> T:
    objects = list(converter.idf.all_of_type(model).values())
    assert len(objects) == 1
    return objects[0]


def test_moisture_becomes_latent_heat() -> None:
    total, sensible_fraction = occupant_activity(66.0, 109.0)

    assert total == pytest.approx(66.0 + 109.0 * 2450.0 / 3600.0)
    assert sensible_fraction == pytest.approx(66.0 / total)


def test_no_moisture_is_all_sensible() -> None:
    assert occupant_activity(58.0, 0.0) == (58.0, 1.0)


def test_per_area_type_values_are_used(converter: InternalGainsConverter) -> None:
    assert _convert(converter, _room_type())

    people = _only(converter, People)
    assert people.number_of_people_calculation_method == 'People/Area'
    assert people.people_per_floor_area == 0.1
    assert people.sensible_heat_fraction == pytest.approx(
        occupant_activity(66.0, 109.0)[1]
    )
    assert _only(converter, Lights).watts_per_floor_area == 11.0
    assert _only(converter, ElectricEquipment).watts_per_floor_area == 20.0
    required_ids = converter.lookup_table.REQUIRED_SCHEDULE_IDS
    assert required_ids == {11, 12, 13}


def test_per_room_values_become_absolute_levels(
    converter: InternalGainsConverter,
) -> None:
    _convert(
        converter,
        _room_type(o_maxnumber=40.0, o_per_area=0, e_maxpower=2000.0, e_per_area=0),
    )

    people = _only(converter, People)
    assert people.number_of_people_calculation_method == 'People'
    assert people.number_of_people == 40.0
    equipment = _only(converter, ElectricEquipment)
    assert equipment.design_level_calculation_method == 'EquipmentLevel'
    assert equipment.design_level == 2000.0


def test_zero_gains_create_no_objects(converter: InternalGainsConverter) -> None:
    empty = _room_type(o_maxnumber=0.0, l_maxpower=0.0, e_maxpower=0.0)

    assert not _convert(converter, empty)
    for model in (People, Lights, ElectricEquipment):
        assert len(converter.idf.all_of_type(model)) == 0


def test_missing_room_type_raises(converter: InternalGainsConverter) -> None:
    with pytest.raises(ValueError, match='Room 7 .* has no room type'):
        _convert(converter, None)


def test_nonzero_minimum_raises(converter: InternalGainsConverter) -> None:
    with pytest.raises(ValueError, match='non-zero e_minpower'):
        _convert(converter, _room_type(e_minpower=5.0))


@pytest.mark.parametrize(
    ('building_type', 'expected_w_m2'),
    [
        # 洗手间 is a dwelling bathroom in housing and a public toilet in schools.
        ('HighS', 6.0),
        ('sch', 3.5),
    ],
)
def test_zero_lighting_is_filled_per_building_type(
    converter: InternalGainsConverter, building_type: str, expected_w_m2: float
) -> None:
    converter.set_building_type(building_type)
    _convert(converter, _room_type(name='洗手间', o_maxnumber=0.0, l_maxpower=0.0))

    lights = _only(converter, Lights)
    assert lights.design_level_calculation_method == 'Watts/Area'
    assert lights.watts_per_floor_area == expected_w_m2
    assert 12 in converter.lookup_table.REQUIRED_SCHEDULE_IDS


def test_uncorrected_building_keeps_zero_lighting(
    converter: InternalGainsConverter,
) -> None:
    converter.set_building_type('coa')
    _convert(converter, _room_type(name='洗手间', l_maxpower=0.0))

    assert len(converter.idf.all_of_type(Lights)) == 0


def test_lighting_can_follow_occupant_schedule(
    converter: InternalGainsConverter,
) -> None:
    converter.set_building_type('uni')
    _convert(converter, _room_type(name='教室', l_maxpower=3.0))

    lights = _only(converter, Lights)
    assert lights.watts_per_floor_area == 3.0
    assert lights.schedule_name == converter.make_name('Schedule', 11, 's11')
    assert 12 not in converter.lookup_table.REQUIRED_SCHEDULE_IDS


def test_excessive_lighting_is_replaced(converter: InternalGainsConverter) -> None:
    converter.set_building_type('mall')
    _convert(converter, _room_type(name='高档商店店铺', l_maxpower=45.0))

    assert _only(converter, Lights).watts_per_floor_area == 21.0
