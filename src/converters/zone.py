"""Zone converter for DeST to EnergyPlus IDF conversion.

This module converts DeST Room models to EnergyPlus Zone objects.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger
from sqlalchemy import select

from src.converters.base import BaseConverter, UnitConverter
from src.database.models.building import Room
from src.idf.models.thermal_zones import Zone

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from src.idf import IDF
    from src.utils.pinyin import PinyinConverter


class ZoneConverter(BaseConverter[Room]):
    """Converter for DeST Room to EnergyPlus Zone.

    Each Room in DeST becomes a Zone in EnergyPlus.
    Handles coordinate conversion (mm → m) and multiplier from storey.
    """

    def __init__(
        self,
        session: Session,
        idf: IDF,
        pinyin: PinyinConverter | None = None,
    ) -> None:
        """Initialize converter.

        Args:
            session: SQLAlchemy session for database queries.
            idf: IDF instance to add converted objects to.
            pinyin: PinyinConverter for Chinese name conversion.
        """
        super().__init__(session, idf, pinyin)
        # Track created zones to avoid duplicates
        self._created_zones: set[int] = set()

    def convert_all(self) -> None:
        """Convert all rooms to zones."""
        stmt = select(Room)
        rooms = list(self.session.execute(stmt).scalars().all())
        self.stats.total = len(rooms)

        for room in rooms:
            self.convert_one(room)

        self.log_stats()

    def convert_one(self, instance: Room) -> bool:
        """Convert a single Room to a Zone.

        Args:
            instance: Room instance to convert.

        Returns:
            True if conversion succeeded.
        """
        room = instance

        # Skip if already converted
        if room.id in self._created_zones:
            return True

        # Skip empty rooms (no area or volume)
        if self._is_empty_room(room):
            logger.warning(
                f'Skipping empty room {room.id} (name={room.name}): '
                f'area={room.area}, volume={room.volume}'
            )
            self.stats.skipped += 1
            return False

        # Generate zone name
        zone_name = self.make_name('Zone', room.id, room.name)

        # Get multiplier from storey
        multiplier = self._get_multiplier(room)

        # Convert coordinates from mm to m
        x_origin = UnitConverter.round_coord(UnitConverter.mm_to_m(room.x))
        y_origin = UnitConverter.round_coord(UnitConverter.mm_to_m(room.y))
        z_origin = UnitConverter.round_coord(UnitConverter.mm_to_m(room.z))

        # Create Zone object
        zone = Zone(
            name=zone_name,
            x_origin=x_origin,
            y_origin=y_origin,
            z_origin=z_origin,
            multiplier=multiplier if multiplier and multiplier > 1 else None,
            # Let EnergyPlus autocalculate these from geometry
            ceiling_height='Autocalculate',
            volume='Autocalculate',
            floor_area='Autocalculate',
        )

        self.idf.add(zone)
        self._created_zones.add(room.id)
        self.stats.converted += 1

        logger.debug(
            f'Converted room {room.id} to zone {zone_name} '
            f'(origin={x_origin},{y_origin},{z_origin}, multiplier={multiplier})'
        )

        return True

    def _is_empty_room(self, room: Room) -> bool:
        """Check if a room is empty (should be skipped).

        A room is considered empty if:
        - Area is None, 0, or negative
        - Volume is None, 0, or negative
        - Has no surfaces

        Args:
            room: Room to check.

        Returns:
            True if room is empty.
        """
        # Check area
        if room.area is None or room.area <= 0:
            return True

        # Check volume
        if room.volume is None or room.volume <= 0:
            return True

        # Check if room has surfaces
        return not room.surfaces

    def _get_multiplier(self, room: Room) -> int:
        """Get zone multiplier from storey.

        Args:
            room: Room to get multiplier for.

        Returns:
            Multiplier value (minimum 1).
        """
        if room.storey is None:
            return 1

        # Get multiplier from storey
        if room.storey.multiple is not None and room.storey.multiple > 1:
            return room.storey.multiple

        return 1

    def get_zone_name(self, room_id: int) -> str | None:
        """Get the generated zone name for a room ID.

        Useful for other converters that need to reference zones.

        Args:
            room_id: Room ID to look up.

        Returns:
            Zone name if room was converted, None otherwise.
        """
        if room_id not in self._created_zones:
            return None

        # Query room to get name
        stmt = select(Room).where(Room.id == room_id)
        room = self.session.execute(stmt).scalars().first()
        if room is None:
            return None

        return self.make_name('Zone', room.id, room.name)
