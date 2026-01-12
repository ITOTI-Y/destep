from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ._base import Base

if TYPE_CHECKING:
    from .building import Room


class Geometry(Base):
    """Geometry model."""

    __tablename__ = 'geometry'

    geometry_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Geometry ID'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='Geometry name')
    boundary_loop_id: Mapped[int | None] = mapped_column(
        Integer, comment='Boundary loop ID'
    )

    # Relationships
    surfaces: Mapped[list[Surface]] = relationship(
        'Surface', back_populates='geometry_ref'
    )


class Point(Base):
    """Point model."""

    __tablename__ = 'point'

    point_id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Point ID')
    name: Mapped[str | None] = mapped_column(String(50), comment='Point name')
    x: Mapped[float | None] = mapped_column(Float, comment='X coordinate (mm)')
    y: Mapped[float | None] = mapped_column(Float, comment='Y coordinate (mm)')
    z: Mapped[float | None] = mapped_column(Float, comment='Z coordinate (mm)')


class Plane(Base):
    """Plane model."""

    __tablename__ = 'plane'

    plane_id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Plane ID')
    name: Mapped[str | None] = mapped_column(String(50), comment='Plane name')
    geometry: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('geometry.geometry_id'), comment='Geometry reference'
    )
    base_line_start_point: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('point.point_id'), comment='Base line start point'
    )
    base_line_end_point: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('point.point_id'), comment='Base line end point'
    )


class LoopPoint(Base):
    """Loop point model."""

    __tablename__ = 'loop_point'

    loop_id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Loop ID')
    point_no: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Point number in loop'
    )
    point: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('point.point_id'), comment='Point reference'
    )
    of_geometry: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('geometry.geometry_id'), comment='Geometry reference'
    )


class Shading(Base):
    """Shading model."""

    __tablename__ = 'shading'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Shading ID')
    name: Mapped[str | None] = mapped_column(String(50), comment='Shading name')
    type: Mapped[int | None] = mapped_column(Integer, comment='Shading type')
    of_building: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('building.building_id'), comment='Building reference'
    )
    geometry: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('geometry.geometry_id'), comment='Geometry'
    )
    schedule: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('schedule_year.schedule_id'), comment='Schedule'
    )
    reflectance: Mapped[float | None] = mapped_column(Float, comment='Reflectance')
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )

    # Relationships
    surfaces: Mapped[list[Surface]] = relationship('Surface', back_populates='shading')


class Surface(Base):
    """Surface model."""

    __tablename__ = 'surface'

    surface_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Surface ID'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='Surface name')
    area: Mapped[float | None] = mapped_column(Float, comment='Area (m²)')
    azimuth: Mapped[float | None] = mapped_column(Float, comment='Azimuth angle')
    tilt: Mapped[float | None] = mapped_column(Float, comment='Tilt angle')
    of_room: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('room.id'), comment='Room reference'
    )
    type: Mapped[int | None] = mapped_column(Integer, comment='Surface type')
    surfacestate: Mapped[int | None] = mapped_column(Integer, comment='Surface state')
    geometry: Mapped[int] = mapped_column(
        Integer, ForeignKey('geometry.geometry_id'), comment='Geometry'
    )
    ventilation_coef: Mapped[float | None] = mapped_column(
        Float, comment='Ventilation coefficient'
    )
    blackness: Mapped[float] = mapped_column(Float, comment='Blackness')
    absorb_coef: Mapped[float] = mapped_column(Float, comment='Absorption coefficient')
    convect_t_id: Mapped[int | None] = mapped_column(
        Integer, comment='Convective heat transfer ID'
    )
    absorb_gain_id: Mapped[int | None] = mapped_column(
        Integer, comment='Absorption gain ID'
    )
    index_in_a_this_room: Mapped[int | None] = mapped_column(
        Integer, comment='Index in this room'
    )
    index_in_a_opp_room: Mapped[int | None] = mapped_column(
        Integer, comment='Index in opposite room'
    )
    sky_radia_coef: Mapped[float | None] = mapped_column(
        Float, comment='Sky radiation coefficient'
    )
    of_shading: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('shading.id'), comment='Shading reference'
    )
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )

    # Relationships
    room: Mapped[Room | None] = relationship('Room', back_populates='surfaces')
    geometry_ref: Mapped[Geometry | None] = relationship(
        'Geometry', back_populates='surfaces'
    )
    shading: Mapped[Shading | None] = relationship('Shading', back_populates='surfaces')


class SurfaceSunShadeMap(Base):
    """Surface sun shade map model."""

    __tablename__ = 'surface_sun_shade_map'

    surface_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Surface ID'
    )
    azimuth: Mapped[float | None] = mapped_column(Float, comment='Azimuth angle')
    tilt: Mapped[float | None] = mapped_column(Float, comment='Tilt angle')
    ratio: Mapped[float | None] = mapped_column(Float, comment='Ratio')
    window_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('window.id'), comment='Window ID'
    )
