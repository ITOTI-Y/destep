import pytest
from idfpy import IDF
from idfpy.models import HVACTemplateThermostat, ZoneControlHumidistat

from src.converters._share import PERCENT_SCHEDULE_PREFIX
from src.converters.hvac import NO_HUMIDIFICATION_SCHEDULE_NAME, HVACConverter
from src.converters.manager import LookupTable
from src.database.models.building import Room
from src.database.models.misc import RoomTypeData
from src.database.models.schedule import ScheduleYear
from src.utils.pinyin import PinyinConverter


@pytest.fixture
def converter() -> HVACConverter:
    converter = object.__new__(HVACConverter)
    converter.idf = IDF()
    converter.lookup_table = LookupTable()
    converter.pinyin = PinyinConverter()
    converter._thermostat_cache = {}
    return converter


@pytest.fixture
def room() -> Room:
    return Room(id=7, name='r7')


@pytest.fixture
def room_type() -> RoomTypeData:
    room_type = RoomTypeData(id=4, name='t4')
    room_type.ac_schedule = ScheduleYear(schedule_id=401, name='ac', type=2)
    room_type.set_t_min_schedule_ref = ScheduleYear(schedule_id=10, name='tmin', type=4)
    room_type.set_t_max_schedule_ref = ScheduleYear(schedule_id=7, name='tmax', type=4)
    return room_type


def test_availability_uses_room_type_ac_schedule(
    converter: HVACConverter, room_type: RoomTypeData, room: Room
) -> None:
    name = converter._availability_schedule_name(room_type, room)

    required_ids = converter.lookup_table.REQUIRED_SCHEDULE_IDS
    assert name == converter.make_name('Schedule', 401, 'ac')
    assert required_ids == {401}


def test_missing_dest_schedule_raises(
    converter: HVACConverter, room_type: RoomTypeData, room: Room
) -> None:
    room_type.ac_schedule = None

    with pytest.raises(ValueError, match='missing required AC schedule'):
        converter._availability_schedule_name(room_type, room)


def test_thermostat_uses_room_type_setpoints(
    converter: HVACConverter, room_type: RoomTypeData, room: Room
) -> None:
    first = converter._create_thermostat(room_type, room)
    second = converter._create_thermostat(room_type, Room(id=8, name='r8'))

    assert first == second == converter.make_name('Thermostat', 4, 't4')
    thermostat = converter.idf.all_of_type(HVACTemplateThermostat)[first]
    assert thermostat.heating_setpoint_schedule_name == converter.make_name(
        'Schedule', 10, 'tmin'
    )
    assert thermostat.cooling_setpoint_schedule_name == converter.make_name(
        'Schedule', 7, 'tmax'
    )
    required_ids = converter.lookup_table.REQUIRED_SCHEDULE_IDS
    assert required_ids == {10, 7}


@pytest.mark.parametrize('flow', [None, 0.0])
def test_room_without_fresh_air_gets_none(
    converter: HVACConverter, room: Room, flow: float | None
) -> None:
    room.min_fresh_flow_num = flow

    assert converter._calculate_fresh_air_flow(room) is None


def test_fresh_air_converts_m3_per_hour(converter: HVACConverter, room: Room) -> None:
    room.min_fresh_flow_num = 800.0

    assert converter._calculate_fresh_air_flow(room) == pytest.approx(800.0 / 3600.0)


def test_dehumidistat_uses_room_type_rh_upper_limit(
    converter: HVACConverter, room_type: RoomTypeData, room: Room
) -> None:
    room_type.set_rh_max_schedule_ref = ScheduleYear(schedule_id=14, name='rh', type=4)

    converter._add_dehumidistat('Z1', room_type, room)
    converter._add_dehumidistat('Z2', room_type, room)

    humidistats = converter.idf.all_of_type(ZoneControlHumidistat)
    assert list(humidistats) == ['Z1 Humidistat', 'Z2 Humidistat']
    humidistat = humidistats['Z1 Humidistat']
    assert humidistat.dehumidifying_relative_humidity_setpoint_schedule_name == (
        converter.make_name(PERCENT_SCHEDULE_PREFIX, 14, 'rh')
    )
    assert (
        humidistat.humidifying_relative_humidity_setpoint_schedule_name
        == NO_HUMIDIFICATION_SCHEDULE_NAME
    )
    percent_ids = converter.lookup_table.PERCENT_SCHEDULE_IDS
    assert percent_ids == {14}


def test_missing_rh_schedule_raises(
    converter: HVACConverter, room_type: RoomTypeData, room: Room
) -> None:
    with pytest.raises(ValueError, match='missing required humidity setpoint'):
        converter._add_dehumidistat('Z1', room_type, room)
