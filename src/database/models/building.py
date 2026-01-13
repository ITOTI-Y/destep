from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ._base import Base

if TYPE_CHECKING:
    from .fenestration import Door, Window
    from .geometry import Point, Surface
    from .hvac import AcSys, HeatingPipe
    from .misc import DistMode, RoomTypeData
    from .schedule import ScheduleYear


class Building(Base):
    """Building model."""

    __tablename__ = 'building'

    building_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Building ID'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='Building name')
    visible: Mapped[bool] = mapped_column(
        Boolean, nullable=False, comment='Visibility flag'
    )
    current_storey: Mapped[int | None] = mapped_column(
        Integer, comment='Current storey'
    )
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )

    # Relationships
    storeys: Mapped[list[Storey]] = relationship('Storey', back_populates='building')
    room_groups: Mapped[list[RoomGroup]] = relationship(
        'RoomGroup', back_populates='building'
    )


class StoreyGroup(Base):
    """Storey group model."""

    __tablename__ = 'storey_group'

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Storey group ID'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='Storey group name')

    # Relationships
    storeys: Mapped[list[Storey]] = relationship(
        'Storey', back_populates='storey_group'
    )


class Storey(Base):
    """Storey model."""

    __tablename__ = 'storey'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Storey ID')
    name: Mapped[str | None] = mapped_column(String(50), comment='Storey name')
    of_storey_group: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('storey_group.id'), comment='Storey group reference'
    )
    of_building: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('building.building_id'), comment='Building reference'
    )
    no: Mapped[int | None] = mapped_column(Integer, comment='Storey number')
    multiple: Mapped[int | None] = mapped_column(Integer, comment='Multiple')
    height: Mapped[float | None] = mapped_column(Float, comment='Storey height (mm)')
    visible: Mapped[bool | None] = mapped_column(Boolean, comment='Visibility flag')
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )

    # Relationships
    building: Mapped[Building | None] = relationship(
        'Building', back_populates='storeys'
    )
    storey_group: Mapped[StoreyGroup | None] = relationship(
        'StoreyGroup', back_populates='storeys'
    )
    rooms: Mapped[list[Room]] = relationship('Room', back_populates='storey')
    windows: Mapped[list[Window]] = relationship('Window', back_populates='storey')
    doors: Mapped[list[Door]] = relationship('Door', back_populates='storey')


class RoomGroup(Base):
    """Room group model."""

    __tablename__ = 'room_group'

    room_group_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Room group ID'
    )
    name: Mapped[str | None] = mapped_column(String(255), comment='Room group name')
    of_building: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('building.building_id'), comment='Building reference'
    )
    of_ac_sys: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('ac_sys.ac_sys_id'), comment='AC system reference'
    )
    is_ac_room: Mapped[bool | None] = mapped_column(
        Boolean, default=False, comment='Is air-conditioned room'
    )
    ac_schedule_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('schedule_year.schedule_id'), comment='AC schedule ID'
    )
    set_t_min_schedule: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('schedule_year.schedule_id'),
        comment='Min temperature setpoint schedule',
    )
    set_t_max_schedule: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('schedule_year.schedule_id'),
        comment='Max temperature setpoint schedule',
    )
    set_rh_min_schedule: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('schedule_year.schedule_id'),
        comment='Min humidity setpoint schedule',
    )
    set_rh_max_schedule: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('schedule_year.schedule_id'),
        comment='Max humidity setpoint schedule',
    )
    ac_t_min_schedule: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('schedule_year.schedule_id'),
        comment='AC min temperature schedule',
    )
    ac_t_max_schedule: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('schedule_year.schedule_id'),
        comment='AC max temperature schedule',
    )
    do_stiffen: Mapped[bool | None] = mapped_column(
        Boolean, default=False, comment='Enable stiffening'
    )
    stiffen_expect: Mapped[float | None] = mapped_column(
        Float, comment='Stiffening expectation'
    )
    do_zip_simular_landa: Mapped[bool | None] = mapped_column(
        Boolean, default=False, comment='Enable simulation parameter compression'
    )
    zip_tolerance: Mapped[float | None] = mapped_column(
        Float, comment='Compression tolerance'
    )
    hvac_gain_id: Mapped[int | None] = mapped_column(Integer, comment='HVAC gain ID')
    view_air_volume: Mapped[bool | None] = mapped_column(
        Boolean, default=False, comment='View air volume'
    )
    view_terminal_load: Mapped[bool | None] = mapped_column(
        Boolean, default=False, comment='View terminal load'
    )
    view_temperature: Mapped[bool | None] = mapped_column(
        Boolean, default=False, comment='View temperature'
    )
    view_damp: Mapped[bool | None] = mapped_column(
        Boolean, default=False, comment='View humidity'
    )
    view_base_temperature: Mapped[bool | None] = mapped_column(
        Boolean, default=False, comment='View base temperature'
    )
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )

    # Relationships
    building: Mapped[Building | None] = relationship(
        'Building', back_populates='room_groups'
    )
    ac_sys: Mapped[AcSys | None] = relationship('AcSys', back_populates='room_groups')
    rooms: Mapped[list[Room]] = relationship('Room', back_populates='room_group')
    ac_schedule: Mapped[ScheduleYear | None] = relationship(
        'ScheduleYear', foreign_keys=[ac_schedule_id]
    )
    set_t_min_schedule_ref: Mapped[ScheduleYear | None] = relationship(
        'ScheduleYear', foreign_keys=[set_t_min_schedule]
    )
    set_t_max_schedule_ref: Mapped[ScheduleYear | None] = relationship(
        'ScheduleYear', foreign_keys=[set_t_max_schedule]
    )
    set_rh_min_schedule_ref: Mapped[ScheduleYear | None] = relationship(
        'ScheduleYear', foreign_keys=[set_rh_min_schedule]
    )
    set_rh_max_schedule_ref: Mapped[ScheduleYear | None] = relationship(
        'ScheduleYear', foreign_keys=[set_rh_max_schedule]
    )
    ac_t_min_schedule_ref: Mapped[ScheduleYear | None] = relationship(
        'ScheduleYear', foreign_keys=[ac_t_min_schedule]
    )
    ac_t_max_schedule_ref: Mapped[ScheduleYear | None] = relationship(
        'ScheduleYear', foreign_keys=[ac_t_max_schedule]
    )


class Room(Base):
    """Room model."""

    __tablename__ = 'room'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Room ID')
    of_room_group: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('room_group.room_group_id'), comment='Room group reference'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='Room name')
    of_storey: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('storey.id'), comment='Storey reference'
    )
    type: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('room_type_data.id'), comment='Room type'
    )
    space_type: Mapped[int | None] = mapped_column(Integer, comment='Space type')
    area: Mapped[float | None] = mapped_column(Float, comment='Area (m²)')
    volume: Mapped[float | None] = mapped_column(Float, comment='Volume (m³)')
    min_fresh_flow_num: Mapped[float | None] = mapped_column(
        Float, comment='Minimum fresh air flow'
    )
    set_air_flownum_min: Mapped[float | None] = mapped_column(
        Float, comment='Setpoint minimum air flow'
    )
    set_air_flownum_max: Mapped[float | None] = mapped_column(
        Float, comment='Setpoint maximum air flow'
    )
    set_terminal_max: Mapped[float | None] = mapped_column(
        Float, comment='Setpoint terminal maximum'
    )
    set_fcu_max_cool: Mapped[float | None] = mapped_column(
        Float, comment='Setpoint FCU max cooling'
    )
    set_fcu_max_heat: Mapped[float | None] = mapped_column(
        Float, comment='Setpoint FCU max heating'
    )
    furniture_coef: Mapped[float | None] = mapped_column(
        Float, comment='Furniture coefficient'
    )
    positive_pressure: Mapped[float | None] = mapped_column(
        Float, comment='Positive pressure'
    )
    user_hvac_heat_gain: Mapped[int | None] = mapped_column(
        Integer, comment='User HVAC heat gain'
    )
    radiator_flow_schedule: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('schedule_year.schedule_id'),
        comment='Radiator flow schedule',
    )
    radiator_area: Mapped[float | None] = mapped_column(Float, comment='Radiator area')
    radiator_k_a: Mapped[float | None] = mapped_column(
        Float, comment='Radiator coefficient A'
    )
    radiator_k_b: Mapped[float | None] = mapped_column(
        Float, comment='Radiator coefficient B'
    )
    radiator_dist_mode: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('dist_mode.dist_mode_id'),
        comment='Radiator heat distribution mode',
    )
    of_heating_pipe: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('heating_pipe.heating_pipe_id'),
        comment='Heating pipe reference',
    )
    of_heating_pipe_no: Mapped[int | None] = mapped_column(
        Integer, comment='Heating pipe number'
    )
    x: Mapped[float | None] = mapped_column(Float, comment='X coordinate (mm)')
    y: Mapped[float | None] = mapped_column(Float, comment='Y coordinate (mm)')
    z: Mapped[float | None] = mapped_column(Float, comment='Z coordinate (mm)')
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )

    # Relationships
    room_group: Mapped[RoomGroup | None] = relationship(
        'RoomGroup', back_populates='rooms'
    )
    storey: Mapped[Storey | None] = relationship('Storey', back_populates='rooms')
    room_type: Mapped[RoomTypeData | None] = relationship(
        'RoomTypeData', foreign_keys=[type]
    )
    heating_pipe: Mapped[HeatingPipe | None] = relationship(
        'HeatingPipe', back_populates='rooms'
    )
    radiator_schedule: Mapped[ScheduleYear | None] = relationship(
        'ScheduleYear', foreign_keys=[radiator_flow_schedule]
    )
    radiator_mode: Mapped[DistMode | None] = relationship(
        'DistMode', foreign_keys=[radiator_dist_mode]
    )
    surfaces: Mapped[list[Surface]] = relationship('Surface', back_populates='room')


class RoomRelation(Base):
    """Room relation model."""

    __tablename__ = 'room_relation'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Relation ID')
    name: Mapped[str | None] = mapped_column(String(50), comment='Relation name')
    of_building: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('building.building_id'), comment='Building reference'
    )
    room_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('room.id'), comment='Room ID'
    )
    rela_room_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('room.id'), comment='Related room ID'
    )
    vent_schedule_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('schedule_year.schedule_id'),
        comment='Ventilation schedule ID',
    )
    vent_set_max: Mapped[int | None] = mapped_column(
        Integer, comment='Maximum ventilation setpoint'
    )
    vent_type: Mapped[int | None] = mapped_column(Integer, comment='Ventilation type')
    start_point_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('point.point_id'), comment='Start point ID'
    )
    end_point_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('point.point_id'), comment='End point ID'
    )
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )

    # Relationships
    building: Mapped[Building | None] = relationship('Building')
    room: Mapped[Room | None] = relationship('Room', foreign_keys=[room_id])
    related_room: Mapped[Room | None] = relationship(
        'Room', foreign_keys=[rela_room_id]
    )
    vent_schedule: Mapped[ScheduleYear | None] = relationship('ScheduleYear')
    start_point: Mapped[Point | None] = relationship(
        'Point', foreign_keys=[start_point_id]
    )
    end_point: Mapped[Point | None] = relationship('Point', foreign_keys=[end_point_id])
