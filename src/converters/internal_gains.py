"""Internal gains converter for DeST to EnergyPlus IDF conversion.

Converts DeST OccupantGains, LightGains, and EquipmentGains to EnergyPlus
People, Lights, and ElectricEquipment objects.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger
from sqlalchemy import select

from src.converters.base import BaseConverter
from src.database.models.building import Room
from src.database.models.gains import EquipmentGains, LightGains, OccupantGains
from src.idf.models.internal_gains import ElectricEquipment, Lights, People
from src.idf.models.schedules import ScheduleConstant, ScheduleTypeLimits

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from src.idf import IDF
    from src.utils.pinyin import PinyinConverter

    from .manager import LookupTable


class InternalGainsConverter(BaseConverter[Room]):
    """Converter for DeST internal gains to EnergyPlus.

    Converts:
    - OccupantGains → People + ScheduleConstant (Activity Level)
    - LightGains → Lights
    - EquipmentGains → ElectricEquipment

    All gains are associated with a Zone through the Room → Zone mapping
    in the LookupTable.
    """

    def __init__(
        self,
        session: Session,
        idf: IDF,
        lookup_table: LookupTable,
        pinyin: PinyinConverter | None = None,
    ) -> None:
        super().__init__(session, idf, lookup_table, pinyin)
        self._created_activity_type_limits = False

    def convert_all(self) -> None:
        """Convert all internal gains for all rooms."""
        stmt = select(Room)
        rooms = list(self.session.execute(stmt).scalars().all())
        self.stats.total = len(rooms)

        for room in rooms:
            self.convert_one(room)

        self.log_stats()

    def convert_one(self, instance: Room) -> bool:
        """Convert internal gains for a single room.

        Args:
            instance: Room instance to process.

        Returns:
            True if at least one gain was converted successfully.
        """
        room = instance
        zone_name = self.lookup_table.ROOM_TO_ZONE.get(room.id)
        if zone_name is None:
            logger.debug(f'Room {room.id} has no associated zone, skipping gains')
            self.stats.skipped += 1
            return False

        converted_any = False

        occupant_gains = self._get_occupant_gains(room.id)
        for gains in occupant_gains:
            if self._convert_occupant_gains(gains, zone_name, room):
                converted_any = True

        light_gains = self._get_light_gains(room.id)
        for gains in light_gains:
            if self._convert_light_gains(gains, zone_name, room):
                converted_any = True

        equipment_gains = self._get_equipment_gains(room.id)
        for gains in equipment_gains:
            if self._convert_equipment_gains(gains, zone_name, room):
                converted_any = True

        if converted_any:
            self.stats.converted += 1
        else:
            logger.info(f'Room {room.id} ({zone_name}) has no internal gains')
            self.stats.skipped += 1

        return converted_any

    def _get_occupant_gains(self, room_id: int) -> list[OccupantGains]:
        """Query occupant gains for a room."""
        stmt = select(OccupantGains).where(OccupantGains.of_room == room_id)
        return list(self.session.execute(stmt).scalars().all())

    def _get_light_gains(self, room_id: int) -> list[LightGains]:
        """Query light gains for a room."""
        stmt = select(LightGains).where(LightGains.of_room == room_id)
        return list(self.session.execute(stmt).scalars().all())

    def _get_equipment_gains(self, room_id: int) -> list[EquipmentGains]:
        """Query equipment gains for a room."""
        stmt = select(EquipmentGains).where(EquipmentGains.of_room == room_id)
        return list(self.session.execute(stmt).scalars().all())

    def _convert_occupant_gains(
        self, gains: OccupantGains, zone_name: str, room: Room
    ) -> bool:
        """Convert OccupantGains to People and Activity Level schedule.

        Args:
            gains: OccupantGains instance.
            zone_name: Target zone name.
            room: Room instance for naming.

        Returns:
            True if conversion succeeded.
        """
        if gains.maxnumber is None or gains.maxnumber <= 0:
            raise ValueError(
                f'OccupantGains {gains.gain_id} missing required field: '
                f'maxnumber (got {gains.maxnumber})'
            )

        if gains.schedule_year is None:
            raise ValueError(
                f'OccupantGains {gains.gain_id} missing required field: schedule'
            )

        self.lookup_table.REQUIRED_SCHEDULE_IDS.add(gains.schedule_year.schedule_id)

        schedule_name = self.make_name(
            'Schedule', gains.schedule_year.schedule_id, gains.schedule_year.name
        )

        activity_schedule_name = self.make_name('ActivityLevel', room.id, room.name)
        heat_per_person = gains.heat_per_person or 120.0

        self._ensure_activity_type_limits()

        activity_schedule = ScheduleConstant(
            name=activity_schedule_name,
            schedule_type_limits_name='Any Number',
            hourly_value=heat_per_person,
        )
        self.idf.add(activity_schedule)

        people_name = self.make_name('People', room.id, room.name)
        people = People(
            name=people_name,
            zone_or_zonelist_or_space_or_spacelist_name=zone_name,
            number_of_people_schedule_name=schedule_name,
            number_of_people_calculation_method='People/Area',
            people_per_floor_area=gains.maxnumber,
            fraction_radiant=0.3,
            sensible_heat_fraction='Autocalculate',
            activity_level_schedule_name=activity_schedule_name,
        )
        self.idf.add(people)

        logger.debug(
            f'Converted OccupantGains {gains.gain_id} -> {people_name} '
            f'(density={gains.maxnumber}, activity={heat_per_person}W/person)'
        )
        return True

    def _convert_light_gains(
        self, gains: LightGains, zone_name: str, room: Room
    ) -> bool:
        """Convert LightGains to Lights.

        Args:
            gains: LightGains instance.
            zone_name: Target zone name.
            room: Room instance for naming.

        Returns:
            True if conversion succeeded.
        """
        if gains.maxpower is None or gains.maxpower <= 0:
            raise ValueError(
                f'LightGains {gains.gain_id} missing required field: '
                f'maxpower (got {gains.maxpower})'
            )

        if gains.schedule_year is None:
            raise ValueError(
                f'LightGains {gains.gain_id} missing required field: schedule'
            )

        self.lookup_table.REQUIRED_SCHEDULE_IDS.add(gains.schedule_year.schedule_id)

        schedule_name = self.make_name(
            'Schedule', gains.schedule_year.schedule_id, gains.schedule_year.name
        )

        fraction_radiant = 0.0
        if gains.heat_rate is not None and 0.0 <= gains.heat_rate <= 1.0:
            fraction_radiant = gains.heat_rate

        lights_name = self.make_name('Lights', room.id, room.name)
        lights = Lights(
            name=lights_name,
            zone_or_zonelist_or_space_or_spacelist_name=zone_name,
            schedule_name=schedule_name,
            design_level_calculation_method='Watts/Area',
            watts_per_floor_area=gains.maxpower,
            fraction_radiant=fraction_radiant,
            fraction_visible=0.0,
            return_air_fraction=0.0,
        )
        self.idf.add(lights)

        logger.debug(
            f'Converted LightGains {gains.gain_id} -> {lights_name} '
            f'(power={gains.maxpower}W/m²)'
        )
        return True

    def _convert_equipment_gains(
        self, gains: EquipmentGains, zone_name: str, room: Room
    ) -> bool:
        """Convert EquipmentGains to ElectricEquipment.

        Args:
            gains: EquipmentGains instance.
            zone_name: Target zone name.
            room: Room instance for naming.

        Returns:
            True if conversion succeeded.

        Note:
            max_hum and min_hum fields are ignored as per specification.
        """
        if gains.maxpower is None or gains.maxpower <= 0:
            raise ValueError(
                f'EquipmentGains {gains.gain_id} missing required field: '
                f'maxpower (got {gains.maxpower})'
            )

        if gains.schedule_year is None:
            raise ValueError(
                f'EquipmentGains {gains.gain_id} missing required field: schedule'
            )

        self.lookup_table.REQUIRED_SCHEDULE_IDS.add(gains.schedule_year.schedule_id)

        schedule_name = self.make_name(
            'Schedule', gains.schedule_year.schedule_id, gains.schedule_year.name
        )

        equipment_name = self.make_name('Equipment', room.id, room.name)
        equipment = ElectricEquipment(
            name=equipment_name,
            zone_or_zonelist_or_space_or_spacelist_name=zone_name,
            schedule_name=schedule_name,
            design_level_calculation_method='Watts/Area',
            watts_per_floor_area=gains.maxpower,
            fraction_latent=0.0,
            fraction_radiant=0.0,
            fraction_lost=0.0,
        )
        self.idf.add(equipment)

        logger.debug(
            f'Converted EquipmentGains {gains.gain_id} -> {equipment_name} '
            f'(power={gains.maxpower}W/m²)'
        )
        return True

    def _ensure_activity_type_limits(self) -> None:
        """Ensure ScheduleTypeLimits for Activity Level exists."""
        if self._created_activity_type_limits:
            return

        type_limits = ScheduleTypeLimits(
            name='Any Number',
            lower_limit_value=None,
            upper_limit_value=None,
            numeric_type='Continuous',
            unit_type='Dimensionless',
        )
        self.idf.add(type_limits)
        self._created_activity_type_limits = True
