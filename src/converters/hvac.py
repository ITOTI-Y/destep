"""HVAC converter for DeST to EnergyPlus IDF conversion.

Converts DeST Room data to EnergyPlus HVACTemplate objects for simplified
HVAC system configuration. Whether a room is conditioned comes from its
RoomGroup; the AC on/off and setpoint schedules come from its room type.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from idfpy.models import (
    HVACTemplateThermostat,
    ScheduleConstant,
    ZoneControlHumidistat,
)
from loguru import logger
from sqlalchemy import select

from src.converters._share import PERCENT_SCHEDULE_PREFIX
from src.converters.base import BaseConverter
from src.database.models.building import Room

if TYPE_CHECKING:
    from idfpy import IDF
    from sqlalchemy.orm import Session

    from src.database.models.misc import RoomTypeData
    from src.utils.pinyin import PinyinConverter

    from .hvac_strategy import HVACStrategy
    from .manager import LookupTable

M3_PER_HOUR_TO_M3_PER_SECOND: Final = 1.0 / 3600.0
NO_HUMIDIFICATION_SCHEDULE_NAME: Final = 'Humidistat_No_Humidification'


class HVACConverter(BaseConverter[Room]):
    """Converter for DeST HVAC configuration to EnergyPlus HVACTemplate objects.

    Creates:
    - HVACTemplate:Thermostat (one per room type, shared by rooms of that type)
    - HVACTemplate:Zone:IdealLoadsAirSystem (one per Zone)

    Uses HVACTemplate approach which EnergyPlus expands to underlying objects
    at runtime, avoiding manual creation of ZoneHVAC:EquipmentList etc.
    """

    def __init__(
        self,
        session: Session,
        idf: IDF,
        lookup_table: LookupTable,
        pinyin: PinyinConverter | None = None,
    ) -> None:
        super().__init__(session, idf, lookup_table, pinyin)
        self._thermostat_cache: dict[int, str] = {}
        self._strategy: HVACStrategy | None = None

    def set_strategy(self, strategy: HVACStrategy) -> None:
        self._strategy = strategy
        logger.info(f'HVAC strategy set to: {strategy.name}')

    def convert_all(self) -> None:
        """Convert HVAC configuration for all rooms."""
        if self._strategy is None:
            raise ValueError('HVAC strategy not set. Call set_strategy() first.')

        self._strategy.create_system_objects(self.idf)

        stmt = select(Room)
        rooms = list(self.session.execute(stmt).scalars().all())
        self.stats.total = len(rooms)

        for room in rooms:
            self.convert_one(room)

        self.log_stats()

    def convert_one(self, instance: Room) -> bool:
        """Convert HVAC configuration for a single room.

        Args:
            instance: Room instance to process.

        Returns:
            True if conversion succeeded, False otherwise.

        Raises:
            ValueError: If a conditioned room has no room type.
        """
        room = instance
        zone_name = self.lookup_table.ROOM_TO_ZONE.get(room.id)
        if zone_name is None:
            logger.debug(f'Room {room.id} has no associated zone, skipping HVAC')
            self.stats.skipped += 1
            return False

        room_group = room.room_group
        if room_group is None:
            logger.warning(f'Room {room.id} has no RoomGroup, skipping HVAC')
            self.stats.skipped += 1
            return False

        if not room_group.is_ac_room:
            logger.debug(f'Room {room.id} is not AC room, skipping HVAC')
            self.stats.skipped += 1
            return False

        if self._strategy is None:
            raise ValueError('HVAC strategy not set. Call set_strategy() first.')

        room_type = room.room_type
        if room_type is None:
            raise ValueError(
                f'Room {room.id} ({room.name}) has no room type, '
                'so its AC and setpoint schedules are undefined.'
            )

        thermostat_name = self._create_thermostat(room_type, room)
        availability_schedule_name = self._availability_schedule_name(room_type, room)
        fresh_air_flow = self._calculate_fresh_air_flow(room)
        self._strategy.add_zone_hvac(
            self.idf,
            zone_name,
            thermostat_name,
            fresh_air_flow,
            availability_schedule_name,
        )

        if self._strategy.controls_humidity:
            self._add_dehumidistat(zone_name, room_type, room)

        if fresh_air_flow is not None:
            logger.debug(
                f'Converted Room {room.id} ({zone_name}) HVAC -> '
                f'Thermostat: {thermostat_name}, '
                f'Availability: {availability_schedule_name}, '
                f'Fresh air: {fresh_air_flow:.6f} m³/s'
            )
        else:
            logger.info(f'Room {room.id} ({zone_name}): No fresh air configured')
        self.stats.converted += 1
        return True

    def _availability_schedule_name(self, room_type: RoomTypeData, room: Room) -> str:
        schedule = room_type.ac_schedule
        if schedule is None:
            raise ValueError(
                f'Room type {room_type.id} ({room_type.name}) '
                f'missing required AC schedule (ac_schedule_id). '
                f'Room {room.id} ({room.name}) cannot be configured.'
            )
        self.lookup_table.REQUIRED_SCHEDULE_IDS.add(schedule.schedule_id)
        return self.make_name('Schedule', schedule.schedule_id, schedule.name)

    def _create_thermostat(self, room_type: RoomTypeData, room: Room) -> str:
        """Create HVACTemplateThermostat for a room type.

        Thermostats are cached by room type ID since all rooms of one type
        share the same setpoint schedules.

        Args:
            room_type: RoomTypeData instance with setpoint schedules.
            room: Room instance for error context.

        Returns:
            Name of the thermostat (existing or newly created).

        Raises:
            ValueError: If required setpoint schedules are missing.
        """
        if room_type.id in self._thermostat_cache:
            return self._thermostat_cache[room_type.id]

        heating_schedule = room_type.set_t_min_schedule_ref
        cooling_schedule = room_type.set_t_max_schedule_ref

        if heating_schedule is None:
            raise ValueError(
                f'Room type {room_type.id} ({room_type.name}) '
                f'missing required heating setpoint schedule (set_t_min_schedule). '
                f'Room {room.id} ({room.name}) cannot be configured.'
            )

        if cooling_schedule is None:
            raise ValueError(
                f'Room type {room_type.id} ({room_type.name}) '
                f'missing required cooling setpoint schedule (set_t_max_schedule). '
                f'Room {room.id} ({room.name}) cannot be configured.'
            )

        self.lookup_table.REQUIRED_SCHEDULE_IDS.add(heating_schedule.schedule_id)
        self.lookup_table.REQUIRED_SCHEDULE_IDS.add(cooling_schedule.schedule_id)

        heating_schedule_name = self.make_name(
            'Schedule', heating_schedule.schedule_id, heating_schedule.name
        )
        cooling_schedule_name = self.make_name(
            'Schedule', cooling_schedule.schedule_id, cooling_schedule.name
        )

        thermostat_name = self.make_name('Thermostat', room_type.id, room_type.name)

        thermostat = HVACTemplateThermostat(
            name=thermostat_name,
            heating_setpoint_schedule_name=heating_schedule_name,
            cooling_setpoint_schedule_name=cooling_schedule_name,
        )
        self.idf.add(thermostat)

        self._thermostat_cache[room_type.id] = thermostat_name

        logger.debug(
            f'Created HVACTemplateThermostat: {thermostat_name} '
            f'(heating: {heating_schedule_name}, cooling: {cooling_schedule_name})'
        )
        return thermostat_name

    def _add_dehumidistat(
        self, zone_name: str, room_type: RoomTypeData, room: Room
    ) -> None:
        """Add a dehumidify-only humidistat from the room type's RH upper limit.

        Args:
            zone_name: Zone to control.
            room_type: RoomTypeData instance with the RH upper limit schedule.
            room: Room instance for error context.

        Raises:
            ValueError: If the RH upper limit schedule is missing.
        """
        schedule = room_type.set_rh_max_schedule_ref
        if schedule is None:
            raise ValueError(
                f'Room type {room_type.id} ({room_type.name}) '
                f'missing required humidity setpoint schedule (set_rh_max_schedule). '
                f'Room {room.id} ({room.name}) cannot be configured.'
            )
        self.lookup_table.PERCENT_SCHEDULE_IDS.add(schedule.schedule_id)
        if not self.idf.has(ScheduleConstant, NO_HUMIDIFICATION_SCHEDULE_NAME):
            self.idf.add(
                ScheduleConstant(
                    name=NO_HUMIDIFICATION_SCHEDULE_NAME,
                    schedule_type_limits_name='Any Number',
                    hourly_value=0.0,
                )
            )
        self.idf.add(
            ZoneControlHumidistat(
                name=f'{zone_name} Humidistat',
                zone_name=zone_name,
                humidifying_relative_humidity_setpoint_schedule_name=(
                    NO_HUMIDIFICATION_SCHEDULE_NAME
                ),
                dehumidifying_relative_humidity_setpoint_schedule_name=self.make_name(
                    PERCENT_SCHEDULE_PREFIX, schedule.schedule_id, schedule.name
                ),
            )
        )

    def _calculate_fresh_air_flow(self, room: Room) -> float | None:
        """Return the room's minimum fresh air flow.

        Args:
            room: Room instance with ``min_fresh_flow_num`` in m³/h.

        Returns:
            Fresh air flow rate in m³/s, or None if the room has no fresh air.
        """
        if room.min_fresh_flow_num is None or room.min_fresh_flow_num <= 0:
            return None
        return room.min_fresh_flow_num * M3_PER_HOUR_TO_M3_PER_SECOND
