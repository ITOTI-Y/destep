"""Internal gains converter for DeST to EnergyPlus IDF conversion.

Converts the occupant, lighting and equipment settings of each room's DeST
room type (RoomTypeData) to EnergyPlus People, Lights and ElectricEquipment.

The per-room gain records (occupant_gains, light_gains, equipment_gains) are
not used: in the DeST prototypes they hold one default set for every room
(0.2 person/m2, 40 W/person, 10 W/m2 lighting, 40 W/m2 equipment, generic
schedules), whereas DeST itself derives room data such as
Room.min_fresh_flow_num from the room type.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from idfpy.models import (
    ElectricEquipment,
    Lights,
    People,
    ScheduleConstant,
    ScheduleTypeLimits,
)
from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.converters.base import BaseConverter
from src.database.models.building import Room
from src.database.models.misc import RoomTypeData

if TYPE_CHECKING:
    from idfpy import IDF
    from sqlalchemy.orm import Session

    from src.database.models.schedule import ScheduleYear
    from src.utils.pinyin import PinyinConverter

    from .manager import LookupTable

LATENT_HEAT_J_PER_G: Final[float] = 2450.0
SECONDS_PER_HOUR: Final[float] = 3600.0


@dataclass(frozen=True)
class LightingCorrection:
    """Replacement for anomalous DeST room-type lighting.

    Attributes:
        basis: Why the DeST value is replaced, with the reference value used.
        power_w_m2: Lighting power density replacing DeST l_maxpower, or None
            to keep the DeST value.
        use_occupant_schedule: Use the occupant schedule instead of the DeST
            lighting schedule.
    """

    basis: str
    power_w_m2: float | None = None
    use_occupant_schedule: bool = False


_RESIDENTIAL_LIGHTING: Final[LightingCorrection] = LightingCorrection(
    basis='DeST lighting is 0; GB 50034-2013 Table 6.3.1 current value for residential households is 6.0 W/m².',
    power_w_m2=6.0,
)
_RESIDENTIAL_LIT_ROOMS: Final[tuple[str, ...]] = (
    '起居室',
    '主卧室',
    '次卧室',
    '书房',
    '厨房',
    '洗手间',
)

LIGHTING_CORRECTIONS: Final[dict[str, dict[str, LightingCorrection]]] = {
    **{
        building_type: dict.fromkeys(_RESIDENTIAL_LIT_ROOMS, _RESIDENTIAL_LIGHTING)
        for building_type in ('highs', 'hight', 'low', 'th')
    },
    'sch': {
        '走廊': LightingCorrection(
            basis='DeST lighting is 0; GB 50034-2013 Table 6.3.13 Corridor (General) current value is 2.5 W/m2',
            power_w_m2=2.5,
        ),
        '洗手间': LightingCorrection(
            basis='DeST lighting is 0; GB 50034-2013 Table 6.3.13 restrooms (general) current value is 3.5 W/m2',
            power_w_m2=3.5,
        ),
    },
    'mall': {
        '高档商店店铺': LightingCorrection(
            basis=(
                'DeST 45 W/m2 exceeds limit; GB 50034-2013 Table 6.3.4 high-end store current value is 16.0 W/m2 + spot lighting 5 W/m2'
            ),
            power_w_m2=21.0,
        ),
    },
    'uni': {
        '教室': LightingCorrection(
            basis='DeST classroom lighting schedule is 0; lighting follows classroom occupant schedule',
            use_occupant_schedule=True,
        ),
    },
}


def _is_per_area(flag: int | None, field: str, room_type: RoomTypeData) -> bool:
    """Interpret a DeST per-area flag: 1 means per m2, 0 means per room."""
    if flag not in (0, 1):
        raise ValueError(
            f'RoomTypeData {room_type.id} ({room_type.name}) has invalid '
            f'{field}={flag}, expected 0 or 1'
        )
    return flag == 1


def _require_zero_minimum(
    value: float | None,
    field: str,
    room_type: RoomTypeData,
) -> None:
    """Reject DeST minimum values, which EnergyPlus gains cannot represent.

    EnergyPlus scales the design level by the schedule only; a non-zero DeST
    minimum would silently be dropped.
    """
    if value is not None and value > 0:
        raise ValueError(
            f'RoomTypeData {room_type.id} ({room_type.name}) has unsupported '
            f'non-zero {field}={value}'
        )


def occupant_activity(
    sensible_w: float,
    moisture_g_per_h: float,
) -> tuple[float, float]:
    """Return (total activity W/person, sensible heat fraction).

    DeST stores sensible heat and moisture release separately, while EnergyPlus
    People takes the total metabolic rate plus a sensible fraction.
    """
    latent_w = moisture_g_per_h * LATENT_HEAT_J_PER_G / SECONDS_PER_HOUR
    total_w = sensible_w + latent_w
    return total_w, sensible_w / total_w


class InternalGainsConverter(BaseConverter[Room]):
    """Converter for DeST room-type internal gains to EnergyPlus.

    Converts, per room and from its RoomTypeData:
    - Occupants → People + ScheduleConstant (Activity Level)
    - Lighting → Lights
    - Equipment → ElectricEquipment

    Densities flagged per area become W/m2 or people/m2; otherwise they are
    totals for the room. Gains with a zero maximum (e.g. empty rooms, corridors
    without equipment) produce no object. Lighting of the room types listed in
    LIGHTING_CORRECTIONS for the building type is corrected. All gains are
    associated with a Zone through the Room → Zone mapping in the LookupTable.
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
        self._lighting_corrections: dict[str, LightingCorrection] = {}

    def set_building_type(self, building_type: str) -> None:
        self._lighting_corrections = LIGHTING_CORRECTIONS.get(building_type.lower(), {})

    def convert_all(self) -> None:
        """Convert all internal gains for all rooms."""
        stmt = select(Room).options(selectinload(Room.room_type))
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

        room_type = room.room_type
        if room_type is None:
            raise ValueError(
                f'Room {room.id} ({room.name}) has no room type '
                f'(type={room.type}); internal gains are defined per room type'
            )
        created = [
            self._convert_occupants(room_type, zone_name, room),
            self._convert_lighting(room_type, zone_name, room),
            self._convert_equipment(room_type, zone_name, room),
        ]

        if any(created):
            self.stats.converted += 1
            return True

        logger.debug(
            f'Room {room.id} ({zone_name}) of type {room_type.name} has no '
            'internal gains'
        )
        self.stats.skipped += 1
        return False

    def _schedule_name(
        self, schedule: ScheduleYear | None, field: str, room_type: RoomTypeData
    ) -> str:
        if schedule is None:
            raise ValueError(
                f'RoomTypeData {room_type.id} ({room_type.name}) missing '
                f'required schedule: {field}'
            )
        self.lookup_table.REQUIRED_SCHEDULE_IDS.add(schedule.schedule_id)
        return self.make_name('Schedule', schedule.schedule_id, schedule.name)

    def _convert_occupants(
        self, room_type: RoomTypeData, zone_name: str, room: Room
    ) -> bool:
        """Create People and its activity schedule; False if the type has none."""

        maximum = room_type.o_maxnumber
        if maximum is None or maximum <= 0:
            return False
        _require_zero_minimum(room_type.o_minnumber, 'o_minnumber', room_type)

        sensible_w = room_type.o_heat_per_person
        if sensible_w is None or sensible_w <= 0:
            raise ValueError(
                f'RoomTypeData {room_type.id} ({room_type.name}) has occupants '
                f'but o_heat_per_person={sensible_w}'
            )
        activity_w, sensible_fraction = occupant_activity(
            sensible_w, room_type.o_damp_per_person or 0.0
        )

        schedule_name = self._schedule_name(
            room_type.occupant_schedule, 'o_schedule', room_type
        )
        activity_schedule_name = self.make_name('ActivityLevel', room.id, room.name)
        self._ensure_activity_type_limits()
        self.idf.add(
            ScheduleConstant(
                name=activity_schedule_name,
                schedule_type_limits_name='Any Number',
                hourly_value=activity_w,
            )
        )

        per_area = _is_per_area(room_type.o_per_area, 'o_per_area', room_type)
        people_name = self.make_name('People', room.id, room.name)
        self.idf.add(
            People(
                name=people_name,
                zone_or_zonelist_or_space_or_spacelist_name=zone_name,
                number_of_people_schedule_name=schedule_name,
                number_of_people_calculation_method=(
                    'People/Area' if per_area else 'People'
                ),
                people_per_floor_area=maximum if per_area else None,
                number_of_people=None if per_area else maximum,
                fraction_radiant=0.3,
                sensible_heat_fraction=sensible_fraction,
                activity_level_schedule_name=activity_schedule_name,
            )
        )
        logger.debug(
            f'Converted occupants of {room_type.name} -> {people_name} '
            f'({maximum} {"people/m2" if per_area else "people"}, '
            f'activity={activity_w:.1f} W/person, '
            f'sensible fraction={sensible_fraction:.2f})'
        )
        return True

    def _convert_lighting(
        self, room_type: RoomTypeData, zone_name: str, room: Room
    ) -> bool:
        """Create Lights; False if the room type has no lighting.

        A LightingCorrection for the room type replaces the DeST power density
        (always per m2) and/or the schedule.
        """
        correction = self._lighting_corrections.get(room_type.name or '')
        if correction is not None and correction.power_w_m2 is not None:
            maximum: float | None = correction.power_w_m2
            per_area = True
        else:
            maximum = room_type.l_maxpower
            if maximum is None or maximum <= 0:
                return False
            _require_zero_minimum(room_type.l_minpower, 'l_minpower', room_type)
            per_area = _is_per_area(room_type.l_per_area, 'l_per_area', room_type)

        if correction is not None and correction.use_occupant_schedule:
            schedule_name = self._schedule_name(
                room_type.occupant_schedule, 'o_schedule', room_type
            )
        else:
            schedule_name = self._schedule_name(
                room_type.lighting_schedule, 'l_schedule', room_type
            )
        if correction is not None:
            logger.debug(
                f'Corrected lighting of room type {room_type.name}: {correction.basis}'
            )

        fraction_radiant = 0.0
        if room_type.l_heat_rate is not None and 0.0 <= room_type.l_heat_rate <= 1.0:
            fraction_radiant = room_type.l_heat_rate

        lights_name = self.make_name('Lights', room.id, room.name)
        self.idf.add(
            Lights(
                name=lights_name,
                zone_or_zonelist_or_space_or_spacelist_name=zone_name,
                schedule_name=schedule_name,
                design_level_calculation_method=(
                    'Watts/Area' if per_area else 'LightingLevel'
                ),
                watts_per_floor_area=maximum if per_area else None,
                lighting_level=None if per_area else maximum,
                fraction_radiant=fraction_radiant,
                fraction_visible=0.0,
                return_air_fraction=0.0,
            )
        )
        logger.debug(
            f'Converted lighting of {room_type.name} -> {lights_name} '
            f'({maximum} {"W/m2" if per_area else "W"})'
        )
        return True

    def _convert_equipment(
        self, room_type: RoomTypeData, zone_name: str, room: Room
    ) -> bool:
        """Create ElectricEquipment; False if the room type has no equipment.

        DeST equipment humidity loads (e_max_hum, e_min_hum) are not converted.
        """
        maximum = room_type.e_maxpower
        if maximum is None or maximum <= 0:
            return False
        _require_zero_minimum(room_type.e_minpower, 'e_minpower', room_type)

        schedule_name = self._schedule_name(
            room_type.equipment_schedule, 'e_schedule', room_type
        )
        per_area = _is_per_area(room_type.e_per_area, 'e_per_area', room_type)
        equipment_name = self.make_name('Equipment', room.id, room.name)
        self.idf.add(
            ElectricEquipment(
                name=equipment_name,
                zone_or_zonelist_or_space_or_spacelist_name=zone_name,
                schedule_name=schedule_name,
                design_level_calculation_method=(
                    'Watts/Area' if per_area else 'EquipmentLevel'
                ),
                watts_per_floor_area=maximum if per_area else None,
                design_level=None if per_area else maximum,
                fraction_latent=0.0,
                fraction_radiant=0.0,
                fraction_lost=0.0,
            )
        )
        logger.debug(
            f'Converted equipment of {room_type.name} -> {equipment_name} '
            f'({maximum} {"W/m2" if per_area else "W"})'
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
