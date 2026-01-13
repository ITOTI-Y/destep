from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ._base import Base

if TYPE_CHECKING:
    from .building import Room, Storey
    from .misc import DistMode
    from .schedule import ScheduleYear


class OccupantGains(Base):
    """Occupant heat gains model."""

    __tablename__ = 'occupant_gains'

    gain_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Occupant gains ID'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='Name')
    of_room: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('room.id'), comment='Room reference'
    )
    schedule: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('schedule_year.schedule_id'), comment='Schedule'
    )
    user_defined: Mapped[int | None] = mapped_column(
        Integer, comment='User defined flag'
    )
    maxnumber: Mapped[float | None] = mapped_column(Float, comment='Maximum occupants')
    minnumber: Mapped[float | None] = mapped_column(Float, comment='Minimum occupants')
    heat_per_person: Mapped[float | None] = mapped_column(
        Float, comment='Sensible heat per person (W/person)'
    )
    damp_per_person: Mapped[float | None] = mapped_column(
        Float, comment='Moisture load per person (g/h·person)'
    )
    min_require_fresh_air: Mapped[float | None] = mapped_column(
        Float, comment='Minimum fresh air (m³/h·person)'
    )
    per_area: Mapped[int | None] = mapped_column(Integer, comment='Calculate by area')
    a: Mapped[float | None] = mapped_column(Float, comment='Coefficient A')
    b: Mapped[float | None] = mapped_column(Float, comment='Coefficient B')
    dist_mode: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('dist_mode.dist_mode_id'), comment='Distribution mode'
    )
    of_storey: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('storey.id'), comment='Storey reference'
    )
    x: Mapped[float | None] = mapped_column(Float, comment='X coordinate')
    y: Mapped[float | None] = mapped_column(Float, comment='Y coordinate')
    z: Mapped[float | None] = mapped_column(Float, comment='Z coordinate')

    # Relationships
    room: Mapped[Room | None] = relationship('Room')
    schedule_year: Mapped[ScheduleYear | None] = relationship('ScheduleYear')
    dist_mode_ref: Mapped[DistMode | None] = relationship('DistMode')
    storey: Mapped[Storey | None] = relationship('Storey')


class LightGains(Base):
    """Lighting heat gains model."""

    __tablename__ = 'light_gains'

    gain_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Lighting gains ID'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='Name')
    of_room: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('room.id'), comment='Room reference'
    )
    schedule: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('schedule_year.schedule_id'), comment='Schedule'
    )
    maxpower: Mapped[float | None] = mapped_column(
        Float, comment='Maximum power (W/m²)'
    )
    minpower: Mapped[float | None] = mapped_column(
        Float, comment='Minimum power (W/m²)'
    )
    heat_rate: Mapped[float | None] = mapped_column(
        Float, comment='Heat dissipation rate'
    )
    per_area: Mapped[int | None] = mapped_column(Integer, comment='Calculate by area')
    a: Mapped[float | None] = mapped_column(Float, comment='Coefficient A')
    b: Mapped[float | None] = mapped_column(Float, comment='Coefficient B')
    dist_mode: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('dist_mode.dist_mode_id'), comment='Distribution mode'
    )
    of_storey: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('storey.id'), comment='Storey reference'
    )
    x: Mapped[float | None] = mapped_column(Float, comment='X coordinate')
    y: Mapped[float | None] = mapped_column(Float, comment='Y coordinate')
    z: Mapped[float | None] = mapped_column(Float, comment='Z coordinate')

    # Relationships
    room: Mapped[Room | None] = relationship('Room')
    schedule_year: Mapped[ScheduleYear | None] = relationship('ScheduleYear')
    dist_mode_ref: Mapped[DistMode | None] = relationship('DistMode')
    storey: Mapped[Storey | None] = relationship('Storey')


class EquipmentGains(Base):
    """Equipment heat gains model."""

    __tablename__ = 'equipment_gains'

    gain_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Equipment gains ID'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='Name')
    of_room: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('room.id'), comment='Room reference'
    )
    schedule: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('schedule_year.schedule_id'), comment='Schedule'
    )
    maxpower: Mapped[float | None] = mapped_column(
        Float, comment='Maximum power (W/m²)'
    )
    minpower: Mapped[float | None] = mapped_column(
        Float, comment='Minimum power (W/m²)'
    )
    max_hum: Mapped[float | None] = mapped_column(
        Float, comment='Maximum humidity load'
    )
    min_hum: Mapped[float | None] = mapped_column(
        Float, comment='Minimum humidity load'
    )
    per_area: Mapped[int | None] = mapped_column(Integer, comment='Calculate by area')
    a: Mapped[float | None] = mapped_column(Float, comment='Coefficient A')
    b: Mapped[float | None] = mapped_column(Float, comment='Coefficient B')
    dist_mode: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('dist_mode.dist_mode_id'), comment='Distribution mode'
    )
    of_storey: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('storey.id'), comment='Storey reference'
    )
    x: Mapped[float | None] = mapped_column(Float, comment='X coordinate')
    y: Mapped[float | None] = mapped_column(Float, comment='Y coordinate')
    z: Mapped[float | None] = mapped_column(Float, comment='Z coordinate')

    # Relationships
    room: Mapped[Room | None] = relationship('Room')
    schedule_year: Mapped[ScheduleYear | None] = relationship('ScheduleYear')
    dist_mode_ref: Mapped[DistMode | None] = relationship('DistMode')
    storey: Mapped[Storey | None] = relationship('Storey')
