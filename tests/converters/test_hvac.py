import pytest
from idfpy import IDF
from idfpy.models import ScheduleConstant

from src.converters.hvac import ALWAYS_ON_SCHEDULE_NAME, HVACConverter
from src.converters.manager import LookupTable
from src.database.models.building import Room, RoomGroup
from src.database.models.schedule import ScheduleYear
from src.utils.pinyin import PinyinConverter


@pytest.fixture
def converter() -> HVACConverter:
    converter = object.__new__(HVACConverter)
    converter.idf = IDF()
    converter.lookup_table = LookupTable()
    converter.pinyin = PinyinConverter()
    converter._always_on = False
    return converter


@pytest.fixture
def room() -> Room:
    return Room(id=7, name='r7')


@pytest.fixture
def room_group() -> RoomGroup:
    room_group = RoomGroup(room_group_id=3, name='g3')
    room_group.ac_schedule = ScheduleYear(schedule_id=6, name='ac', type=2)
    return room_group


def test_dest_ac_schedule_is_used_by_default(
    converter: HVACConverter, room_group: RoomGroup, room: Room
) -> None:
    converter.set_building_type('coa')

    name = converter._availability_schedule_name(room_group, room)

    required_ids = converter.lookup_table.REQUIRED_SCHEDULE_IDS
    assert name == converter.make_name('Schedule', 6, 'ac')
    assert required_ids == {6}


@pytest.mark.parametrize('building_type', ['LH', 'sh', 'Outp', 'inp'])
def test_always_on_building_types_ignore_dest_schedule(
    converter: HVACConverter, room_group: RoomGroup, room: Room, building_type: str
) -> None:
    converter.set_building_type(building_type)

    first = converter._availability_schedule_name(room_group, room)
    second = converter._availability_schedule_name(room_group, room)

    assert first == second == ALWAYS_ON_SCHEDULE_NAME
    schedules = converter.idf.all_of_type(ScheduleConstant)
    assert list(schedules) == [ALWAYS_ON_SCHEDULE_NAME]
    assert schedules[ALWAYS_ON_SCHEDULE_NAME].hourly_value == 1.0
    required_ids = converter.lookup_table.REQUIRED_SCHEDULE_IDS
    assert required_ids == set()


def test_missing_dest_schedule_raises(
    converter: HVACConverter, room_group: RoomGroup, room: Room
) -> None:
    converter.set_building_type('coa')
    room_group.ac_schedule = None

    with pytest.raises(ValueError, match='missing required AC schedule'):
        converter._availability_schedule_name(room_group, room)
