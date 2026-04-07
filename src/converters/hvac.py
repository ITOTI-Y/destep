"""HVAC converter for DeST to EnergyPlus IDF conversion.

Converts DeST Room/RoomGroup data to EnergyPlus HVACTemplate objects
for simplified HVAC system configuration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger
from sqlalchemy import select

from src.converters.base import BaseConverter
from src.database.models.building import Room
from src.database.models.gains import OccupantGains
from src.idf.models.hvac_templates import (
    HVACTemplateThermostat,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from src.database.models.building import RoomGroup
    from src.idf import IDF
    from src.utils.pinyin import PinyinConverter

    from .hvac_strategy import HVACStrategy
    from .manager import LookupTable

M3_PER_HOUR_TO_M3_PER_SECOND = 1.0 / 3600.0


class HVACConverter(BaseConverter[Room]):
    """Converter for DeST HVAC configuration to EnergyPlus HVACTemplate objects.

    Creates:
    - HVACTemplate:Thermostat (one per RoomGroup, shared by rooms in same group)
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

        thermostat_name = self._create_thermostat(room_group, room)
        fresh_air_flow = self._calculate_fresh_air_flow(room)
        zone_hvac = self._strategy.create_zone_hvac(
            zone_name, thermostat_name, fresh_air_flow
        )
        self.idf.add(zone_hvac)

        if fresh_air_flow is not None and fresh_air_flow > 0:
            logger.debug(
                f'Converted Room {room.id} ({zone_name}) HVAC -> '
                f'Thermostat: {thermostat_name}, Fresh air: {fresh_air_flow:.6f} m³/s'
            )
        else:
            logger.info(
                f'Room {room.id} ({zone_name}): No fresh air configured, '
                f'outdoor air method set to None'
            )
        self.stats.converted += 1
        return True

    def _create_thermostat(self, room_group: RoomGroup, room: Room) -> str:
        """Create HVACTemplateThermostat for a RoomGroup.

        Thermostats are cached by RoomGroup ID to avoid duplicates since
        multiple rooms in the same RoomGroup share the same thermostat.

        Args:
            room_group: RoomGroup instance with setpoint schedules.
            room: Room instance for error context.

        Returns:
            Name of the thermostat (existing or newly created).

        Raises:
            ValueError: If required setpoint schedules are missing.
        """
        if room_group.room_group_id in self._thermostat_cache:
            return self._thermostat_cache[room_group.room_group_id]

        heating_schedule = room_group.set_t_min_schedule_ref
        cooling_schedule = room_group.set_t_max_schedule_ref

        if heating_schedule is None:
            raise ValueError(
                f'RoomGroup {room_group.room_group_id} ({room_group.name}) '
                f'missing required heating setpoint schedule (set_t_min_schedule). '
                f'Room {room.id} ({room.name}) cannot be configured.'
            )

        if cooling_schedule is None:
            raise ValueError(
                f'RoomGroup {room_group.room_group_id} ({room_group.name}) '
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

        thermostat_name = self.make_name(
            'Thermostat', room_group.room_group_id, room_group.name
        )

        thermostat = HVACTemplateThermostat(
            name=thermostat_name,
            heating_setpoint_schedule_name=heating_schedule_name,
            cooling_setpoint_schedule_name=cooling_schedule_name,
        )
        self.idf.add(thermostat)

        self._thermostat_cache[room_group.room_group_id] = thermostat_name

        logger.debug(
            f'Created HVACTemplateThermostat: {thermostat_name} '
            f'(heating: {heating_schedule_name}, cooling: {cooling_schedule_name})'
        )
        return thermostat_name

    def _calculate_fresh_air_flow(self, room: Room) -> float | None:
        """Calculate fresh air flow rate for a room.

        Priority 1: Use Room.min_fresh_flow_num directly (m³/h)
        Priority 2: Calculate from OccupantGains.min_require_fresh_air × maxnumber × area

        Args:
            room: Room instance to calculate fresh air for.

        Returns:
            Fresh air flow rate in m³/s, or None if no fresh air configured.
        """
        if room.min_fresh_flow_num is not None and room.min_fresh_flow_num > 0:
            flow_m3_per_s = room.min_fresh_flow_num * M3_PER_HOUR_TO_M3_PER_SECOND
            logger.debug(
                f'Room {room.id}: Using min_fresh_flow_num = '
                f'{room.min_fresh_flow_num} m³/h = {flow_m3_per_s:.6f} m³/s'
            )
            return flow_m3_per_s

        stmt = select(OccupantGains).where(OccupantGains.of_room == room.id)
        occupant_gains_list = list(self.session.execute(stmt).scalars().all())

        for gains in occupant_gains_list:
            if (
                gains.min_require_fresh_air is not None
                and gains.min_require_fresh_air > 0
                and gains.maxnumber is not None
                and gains.maxnumber > 0
                and room.area is not None
                and room.area > 0
            ):
                flow_m3_per_h = (
                    gains.min_require_fresh_air * gains.maxnumber * room.area
                )
                flow_m3_per_s = flow_m3_per_h * M3_PER_HOUR_TO_M3_PER_SECOND
                logger.debug(
                    f'Room {room.id}: Calculated fresh air from OccupantGains = '
                    f'{flow_m3_per_h:.2f} m³/h = {flow_m3_per_s:.6f} m³/s '
                    f'(min_require={gains.min_require_fresh_air}, '
                    f'maxnumber={gains.maxnumber}, area={room.area})'
                )
                return flow_m3_per_s

        return None
