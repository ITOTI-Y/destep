from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ._base import Base

if TYPE_CHECKING:
    from .building import Storey
    from .construction import MainEnclosure
    from .geometry import Shading, Surface
    from .misc import DistMode, UserDefDll
    from .schedule import ScheduleYear


class SysWindow(Base):
    """System window construction model."""

    __tablename__ = 'sys_window'

    window_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Window construction ID'
    )
    group_id: Mapped[str | None] = mapped_column(String(50), comment='Group name')
    name: Mapped[str | None] = mapped_column(String(50), comment='Window name')
    cname: Mapped[str | None] = mapped_column(
        String(50), comment='Window name (Chinese)'
    )
    heat_resistence: Mapped[float | None] = mapped_column(
        Float, comment='Heat resistance'
    )
    glass_net_ratio: Mapped[float | None] = mapped_column(
        Float, comment='Glass net ratio'
    )
    reflect_co: Mapped[float | None] = mapped_column(
        Float, comment='Reflection coefficient'
    )
    flag: Mapped[int | None] = mapped_column(Integer, comment='Flag')
    spflag: Mapped[int | None] = mapped_column(Integer, comment='SP flag')
    eraseflag: Mapped[int | None] = mapped_column(Integer, comment='Erase flag')
    anotation: Mapped[str | None] = mapped_column(String(255), comment='Annotation')

    # Relationships
    materials: Mapped[list[SysWindowMaterial]] = relationship(
        'SysWindowMaterial', back_populates='window'
    )


class SysWindowMaterial(Base):
    """System window material layer model."""

    __tablename__ = 'sys_window_material'

    window_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('sys_window.window_id'),
        primary_key=True,
        comment='Window reference',
    )
    layer_no: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Layer number'
    )
    material_id: Mapped[int | None] = mapped_column(Integer, comment='Material ID')
    length: Mapped[float | None] = mapped_column(Float, comment='Length/Thickness (mm)')
    anotation: Mapped[str | None] = mapped_column(String(255), comment='Annotation')

    # Relationships
    window: Mapped[SysWindow | None] = relationship(
        'SysWindow', back_populates='materials'
    )


class SysDoor(Base):
    """System door construction model."""

    __tablename__ = 'sys_door'

    door_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Door construction ID'
    )
    group_id: Mapped[str | None] = mapped_column(String(50), comment='Group name')
    name: Mapped[str | None] = mapped_column(String(50), comment='Door name')
    cname: Mapped[str | None] = mapped_column(String(50), comment='Door name (Chinese)')
    conduct_co: Mapped[float | None] = mapped_column(
        Float, comment='Conductivity coefficient'
    )
    material_id: Mapped[int | None] = mapped_column(Integer, comment='Material ID')
    gap_length: Mapped[float | None] = mapped_column(Float, comment='Gap length')
    glass_rat: Mapped[float | None] = mapped_column(Float, comment='Glass ratio')
    app_id: Mapped[int | None] = mapped_column(Integer, comment='Appearance ID')
    app_flag: Mapped[int | None] = mapped_column(Integer, comment='Appearance flag')
    flag: Mapped[int | None] = mapped_column(Integer, comment='Flag')
    eraseflag: Mapped[int | None] = mapped_column(Integer, comment='Erase flag')
    anotation: Mapped[str | None] = mapped_column(String(255), comment='Annotation')


class SysCurtain(Base):
    """System curtain model."""

    __tablename__ = 'sys_curtain'

    curtain_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Curtain ID'
    )
    group_id: Mapped[str | None] = mapped_column(String(50), comment='Group name')
    name: Mapped[str | None] = mapped_column(String(50), comment='Curtain name')
    cname: Mapped[str | None] = mapped_column(
        String(50), comment='Curtain name (Chinese)'
    )
    ext_coef: Mapped[float | None] = mapped_column(
        Float, comment='Extinction coefficient'
    )
    ref_coef: Mapped[float | None] = mapped_column(
        Float, comment='Reflection coefficient'
    )
    long_wave_ref: Mapped[float | None] = mapped_column(
        Float, comment='Long wave reflectance'
    )
    shield_index: Mapped[float | None] = mapped_column(Float, comment='Shield index')
    anotation: Mapped[str | None] = mapped_column(String(255), comment='Annotation')


class SysShading(Base):
    """System shading construction model."""

    __tablename__ = 'sys_shading'

    shield_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Shading ID'
    )
    group_id: Mapped[str | None] = mapped_column(String(50), comment='Group name')
    name: Mapped[str | None] = mapped_column(String(50), comment='Shading name')
    cname: Mapped[str | None] = mapped_column(
        String(50), comment='Shading name (Chinese)'
    )
    a: Mapped[float | None] = mapped_column(Float, comment='Coefficient A')
    b: Mapped[float | None] = mapped_column(Float, comment='Coefficient B')
    c: Mapped[float | None] = mapped_column(Float, comment='Coefficient C')
    d: Mapped[float | None] = mapped_column(Float, comment='Coefficient D')
    e: Mapped[float | None] = mapped_column(Float, comment='Coefficient E')
    f: Mapped[float | None] = mapped_column(Float, comment='Coefficient F')
    g: Mapped[float | None] = mapped_column(Float, comment='Coefficient G')
    h1: Mapped[float | None] = mapped_column(Float, comment='Coefficient H1')
    h2: Mapped[float | None] = mapped_column(Float, comment='Coefficient H2')
    anotation: Mapped[str | None] = mapped_column(String(255), comment='Annotation')


class LibShading(Base):
    """Shading library model."""

    __tablename__ = 'lib_shading'

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Shading library ID'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='Shading name')
    b0: Mapped[float | None] = mapped_column(Float, comment='B0 coefficient')
    b1: Mapped[float | None] = mapped_column(Float, comment='B1 coefficient')
    b2: Mapped[float | None] = mapped_column(Float, comment='B2 coefficient')
    deg: Mapped[float | None] = mapped_column(Float, comment='Degree angle')
    dist: Mapped[float | None] = mapped_column(Float, comment='Distance')
    w: Mapped[float | None] = mapped_column(Float, comment='Width')
    n: Mapped[int | None] = mapped_column(Integer, comment='Number')
    hf: Mapped[float | None] = mapped_column(Float, comment='Height front')
    hl: Mapped[float | None] = mapped_column(Float, comment='Height left')
    wl: Mapped[float | None] = mapped_column(Float, comment='Width left')
    degl: Mapped[float | None] = mapped_column(Float, comment='Degree left')
    hr: Mapped[float | None] = mapped_column(Float, comment='Height right')
    wr: Mapped[float | None] = mapped_column(Float, comment='Width right')
    degr: Mapped[float | None] = mapped_column(Float, comment='Degree right')
    price: Mapped[float | None] = mapped_column(Float, comment='Price')
    image: Mapped[str | None] = mapped_column(String(255), comment='Image path')
    group: Mapped[str | None] = mapped_column(String(50), comment='Group name')
    note: Mapped[str | None] = mapped_column(String(255), comment='Note')
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )


class Window(Base):
    """Window model."""

    __tablename__ = 'window'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Window ID')
    name: Mapped[str | None] = mapped_column(String(50), comment='Window name')
    side1: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('surface.surface_id'), comment='Side 1'
    )
    side2: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('surface.surface_id'), comment='Side 2'
    )
    middle_plane: Mapped[int | None] = mapped_column(Integer, comment='Middle plane')
    of_enclosure: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('main_enclosure.id'), comment='Enclosure reference'
    )
    window_construction: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('sys_window.window_id'), comment='Window construction'
    )
    shading: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('sys_shading.shield_id'), comment='Shading'
    )
    shadingid: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('shading.id'), comment='Shading ID'
    )
    curtain: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('sys_curtain.curtain_id'), comment='Curtain'
    )
    cur_ref_schedule: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('schedule_year.schedule_id'),
        comment='Curtain reference schedule',
    )
    schedule: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('schedule_year.schedule_id'), comment='Schedule ID'
    )
    user_def_dll: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('user_def_dll.dll_id'), comment='User defined DLL'
    )
    sun_trans_dist_mode: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('dist_mode.dist_mode_id'),
        comment='Solar transmission distribution mode',
    )
    of_storey: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('storey.id'), comment='Storey reference'
    )
    type: Mapped[int | None] = mapped_column(Integer, comment='Window type')
    k: Mapped[float | None] = mapped_column(Float, comment='Heat transfer coefficient')
    sc: Mapped[float | None] = mapped_column(Float, comment='Shading coefficient')
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )

    # Relationships
    surface_side1: Mapped[Surface | None] = relationship(
        'Surface', foreign_keys=[side1]
    )
    surface_side2: Mapped[Surface | None] = relationship(
        'Surface', foreign_keys=[side2]
    )
    main_enclosure: Mapped[MainEnclosure | None] = relationship('MainEnclosure')
    window_construction_ref: Mapped[SysWindow | None] = relationship('SysWindow')
    shading_ref: Mapped[SysShading | None] = relationship(
        'SysShading', foreign_keys=[shading]
    )
    shading_lib: Mapped[Shading | None] = relationship(
        'Shading', foreign_keys=[shadingid]
    )
    curtain_ref: Mapped[SysCurtain | None] = relationship('SysCurtain')
    cur_schedule: Mapped[ScheduleYear | None] = relationship(
        'ScheduleYear', foreign_keys=[cur_ref_schedule]
    )
    schedule_ref: Mapped[ScheduleYear | None] = relationship(
        'ScheduleYear', foreign_keys=[schedule]
    )
    dll: Mapped[UserDefDll | None] = relationship('UserDefDll')
    dist_mode: Mapped[DistMode | None] = relationship('DistMode')
    storey: Mapped[Storey | None] = relationship('Storey', back_populates='windows')


class Door(Base):
    """Door model."""

    __tablename__ = 'door'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Door ID')
    name: Mapped[str | None] = mapped_column(String(50), comment='Door name')
    side1: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('surface.surface_id'), comment='Side 1'
    )
    side2: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('surface.surface_id'), comment='Side 2'
    )
    middle_plane: Mapped[int | None] = mapped_column(Integer, comment='Middle plane')
    of_enclosure: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('main_enclosure.id'), comment='Enclosure reference'
    )
    door_construction: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('sys_door.door_id'), comment='Door construction'
    )
    schedule: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('schedule_year.schedule_id'), comment='Schedule ID'
    )
    of_storey: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('storey.id'), comment='Storey reference'
    )
    type: Mapped[int | None] = mapped_column(Integer, comment='Door type')
    k: Mapped[float | None] = mapped_column(Float, comment='Heat transfer coefficient')
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )

    # Relationships
    surface_side1: Mapped[Surface | None] = relationship(
        'Surface', foreign_keys=[side1]
    )
    surface_side2: Mapped[Surface | None] = relationship(
        'Surface', foreign_keys=[side2]
    )
    main_enclosure: Mapped[MainEnclosure | None] = relationship('MainEnclosure')
    door_construction_ref: Mapped[SysDoor | None] = relationship('SysDoor')
    schedule_ref: Mapped[ScheduleYear | None] = relationship('ScheduleYear')
    storey: Mapped[Storey | None] = relationship('Storey', back_populates='doors')


class WindowTypeData(Base):
    """Window type data model."""

    __tablename__ = 'window_type_data'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Window type ID')
    name: Mapped[str | None] = mapped_column(String(50), comment='Type name')
    layer_num: Mapped[int | None] = mapped_column(Integer, comment='Number of layers')
    k: Mapped[float | None] = mapped_column(Float, comment='Heat transfer coefficient')
    sc: Mapped[float | None] = mapped_column(Float, comment='Shading coefficient')
    energy_trans_ratio: Mapped[float | None] = mapped_column(
        Float, comment='Energy transmittance ratio'
    )
    energy_reflect_ratio: Mapped[float | None] = mapped_column(
        Float, comment='Energy reflectance ratio'
    )
    light_trans_ratio: Mapped[float | None] = mapped_column(
        Float, comment='Light transmittance ratio'
    )
    light_reflect_ratio: Mapped[float | None] = mapped_column(
        Float, comment='Light reflectance ratio'
    )
    remark: Mapped[str | None] = mapped_column(String(255), comment='Remark')
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )
