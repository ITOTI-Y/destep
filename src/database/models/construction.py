from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ._base import Base

if TYPE_CHECKING:
    from .building import Room, Storey
    from .geometry import Surface
    from .misc import UserDefDll


class SysMaterial(Base):
    """System material model."""

    __tablename__ = 'sys_material'

    material_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Material ID'
    )
    color: Mapped[int | None] = mapped_column(Integer, comment='Color')
    group_id: Mapped[str | None] = mapped_column(
        String(50), comment='Group name')
    name: Mapped[str | None] = mapped_column(
        String(50), comment='Material name')
    cname: Mapped[str | None] = mapped_column(
        String(50), comment='Material name (Chinese)'
    )
    conductivity: Mapped[float | None] = mapped_column(
        Float, comment='Conductivity (W/m·K)'
    )
    density: Mapped[float | None] = mapped_column(
        Float, comment='Density (kg/m³)')
    specific_heat: Mapped[float | None] = mapped_column(
        Float, comment='Specific heat (J/kg·K)'
    )
    s: Mapped[float | None] = mapped_column(Float, comment='S value')
    steam: Mapped[float | None] = mapped_column(
        Float, comment='Steam coefficient')
    pattern: Mapped[int | None] = mapped_column(Integer, comment='Pattern')
    eraseflag: Mapped[int | None] = mapped_column(
        Integer, comment='Erase flag')
    flag: Mapped[int | None] = mapped_column(Integer, comment='Flag')
    anotation: Mapped[str | None] = mapped_column(
        String(255), comment='Annotation')

    # Relationships
    outwall_materials: Mapped[list[SysOutwallMaterial]] = relationship(
        'SysOutwallMaterial', back_populates='material'
    )
    inwall_materials: Mapped[list[SysInwallMaterial]] = relationship(
        'SysInwallMaterial', back_populates='material'
    )
    roof_materials: Mapped[list[SysRoofMaterial]] = relationship(
        'SysRoofMaterial', back_populates='material'
    )
    groundfloor_materials: Mapped[list[SysGroundfloorMaterial]] = relationship(
        'SysGroundfloorMaterial', back_populates='material'
    )
    middlefloor_materials: Mapped[list[SysMiddlefloorMaterial]] = relationship(
        'SysMiddlefloorMaterial', back_populates='material'
    )
    airfloor_materials: Mapped[list[SysAirfloorMaterial]] = relationship(
        'SysAirfloorMaterial', back_populates='material'
    )


class SysOutwall(Base):
    """System exterior wall construction model."""

    __tablename__ = 'sys_outwall'

    struct_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Structure ID'
    )
    group_id: Mapped[str | None] = mapped_column(
        String(50), comment='Group name')
    name: Mapped[str | None] = mapped_column(
        String(50), comment='Exterior wall name')
    cname: Mapped[str | None] = mapped_column(
        String(50), comment='Exterior wall name (Chinese)'
    )
    resi: Mapped[float | None] = mapped_column(Float, comment='Resistance')
    d: Mapped[float | None] = mapped_column(Float, comment='D value')
    spflag: Mapped[int | None] = mapped_column(Integer, comment='SP flag')
    flag: Mapped[int | None] = mapped_column(Integer, comment='Flag')
    eraseflag: Mapped[int | None] = mapped_column(
        Integer, comment='Erase flag')
    anotation: Mapped[str | None] = mapped_column(
        String(255), comment='Annotation')

    # Relationships
    materials: Mapped[list[SysOutwallMaterial]] = relationship(
        'SysOutwallMaterial', back_populates='outwall'
    )


class SysOutwallMaterial(Base):
    """System exterior wall material layer model."""

    __tablename__ = 'sys_outwall_material'

    struct_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('sys_outwall.struct_id'),
        primary_key=True,
        comment='Structure ID (exterior wall reference)',
    )
    layer_no: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Layer number'
    )
    material_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('sys_material.material_id'), comment='Material ID'
    )
    length: Mapped[float | None] = mapped_column(
        Float, comment='Length/Thickness (mm)')
    anotation: Mapped[str | None] = mapped_column(
        String(255), comment='Annotation')

    # Relationships
    outwall: Mapped[SysOutwall | None] = relationship(
        'SysOutwall', back_populates='materials'
    )
    material: Mapped[SysMaterial | None] = relationship(
        'SysMaterial', back_populates='outwall_materials'
    )


class SysInwall(Base):
    """System interior wall construction model."""

    __tablename__ = 'sys_inwall'

    struct_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Structure ID'
    )
    group_id: Mapped[str | None] = mapped_column(
        String(50), comment='Group name')
    name: Mapped[str | None] = mapped_column(
        String(50), comment='Interior wall name')
    cname: Mapped[str | None] = mapped_column(
        String(50), comment='Interior wall name (Chinese)'
    )
    resi: Mapped[float | None] = mapped_column(Float, comment='Resistance')
    d: Mapped[float | None] = mapped_column(Float, comment='D value')
    spflag: Mapped[int | None] = mapped_column(Integer, comment='SP flag')
    flag: Mapped[int | None] = mapped_column(Integer, comment='Flag')
    eraseflag: Mapped[int | None] = mapped_column(
        Integer, comment='Erase flag')
    anotation: Mapped[str | None] = mapped_column(
        String(255), comment='Annotation')

    # Relationships
    materials: Mapped[list[SysInwallMaterial]] = relationship(
        'SysInwallMaterial', back_populates='inwall'
    )


class SysInwallMaterial(Base):
    """System interior wall material layer model."""

    __tablename__ = 'sys_inwall_material'

    struct_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('sys_inwall.struct_id'),
        primary_key=True,
        comment='Structure ID (interior wall reference)',
    )
    layer_no: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Layer number'
    )
    material_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('sys_material.material_id'), comment='Material ID'
    )
    length: Mapped[float | None] = mapped_column(
        Float, comment='Length/Thickness (mm)')
    anotation: Mapped[str | None] = mapped_column(
        String(255), comment='Annotation')

    # Relationships
    inwall: Mapped[SysInwall | None] = relationship(
        'SysInwall', back_populates='materials'
    )
    material: Mapped[SysMaterial | None] = relationship(
        'SysMaterial', back_populates='inwall_materials'
    )


class SysRoof(Base):
    """System roof construction model."""

    __tablename__ = 'sys_roof'

    struct_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Structure ID'
    )
    group_id: Mapped[str | None] = mapped_column(
        String(50), comment='Group name')
    name: Mapped[str | None] = mapped_column(String(50), comment='Roof name')
    cname: Mapped[str | None] = mapped_column(
        String(50), comment='Roof name (Chinese)')
    resi: Mapped[float | None] = mapped_column(Float, comment='Resistance')
    d: Mapped[float | None] = mapped_column(Float, comment='D value')
    spflag: Mapped[int | None] = mapped_column(Integer, comment='SP flag')
    flag: Mapped[int | None] = mapped_column(Integer, comment='Flag')
    eraseflag: Mapped[int | None] = mapped_column(
        Integer, comment='Erase flag')
    anotation: Mapped[str | None] = mapped_column(
        String(255), comment='Annotation')

    # Relationships
    materials: Mapped[list[SysRoofMaterial]] = relationship(
        'SysRoofMaterial', back_populates='roof'
    )


class SysRoofMaterial(Base):
    """System roof material layer model."""

    __tablename__ = 'sys_roof_material'

    struct_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('sys_roof.struct_id'),
        primary_key=True,
        comment='Structure ID (roof reference)',
    )
    layer_no: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Layer number'
    )
    material_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('sys_material.material_id'), comment='Material ID'
    )
    length: Mapped[float | None] = mapped_column(
        Float, comment='Length/Thickness (mm)')
    anotation: Mapped[str | None] = mapped_column(
        String(255), comment='Annotation')

    # Relationships
    roof: Mapped[SysRoof | None] = relationship(
        'SysRoof', back_populates='materials')
    material: Mapped[SysMaterial | None] = relationship(
        'SysMaterial', back_populates='roof_materials'
    )


class SysGroundfloor(Base):
    """System ground floor construction model."""

    __tablename__ = 'sys_groundfloor'

    struct_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Structure ID'
    )
    group_id: Mapped[str | None] = mapped_column(
        String(50), comment='Group name')
    name: Mapped[str | None] = mapped_column(
        String(50), comment='Ground floor name')
    cname: Mapped[str | None] = mapped_column(
        String(50), comment='Ground floor name (Chinese)'
    )
    resi: Mapped[float | None] = mapped_column(Float, comment='Resistance')
    d: Mapped[float | None] = mapped_column(Float, comment='D value')
    spflag: Mapped[int | None] = mapped_column(Integer, comment='SP flag')
    flag: Mapped[int | None] = mapped_column(Integer, comment='Flag')
    eraseflag: Mapped[int | None] = mapped_column(
        Integer, comment='Erase flag')
    anotation: Mapped[str | None] = mapped_column(
        String(255), comment='Annotation')

    # Relationships
    materials: Mapped[list[SysGroundfloorMaterial]] = relationship(
        'SysGroundfloorMaterial', back_populates='groundfloor'
    )


class SysGroundfloorMaterial(Base):
    """System ground floor material layer model."""

    __tablename__ = 'sys_groundfloor_material'

    struct_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('sys_groundfloor.struct_id'),
        primary_key=True,
        comment='Structure ID (ground floor reference)',
    )
    layer_no: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Layer number'
    )
    material_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('sys_material.material_id'), comment='Material ID'
    )
    length: Mapped[float | None] = mapped_column(
        Float, comment='Length/Thickness (mm)')
    anotation: Mapped[str | None] = mapped_column(
        String(255), comment='Annotation')

    # Relationships
    groundfloor: Mapped[SysGroundfloor | None] = relationship(
        'SysGroundfloor', back_populates='materials'
    )
    material: Mapped[SysMaterial | None] = relationship(
        'SysMaterial', back_populates='groundfloor_materials'
    )


class SysMiddlefloor(Base):
    """System middle floor construction model."""

    __tablename__ = 'sys_middlefloor'

    struct_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Structure ID'
    )
    group_id: Mapped[str | None] = mapped_column(
        String(50), comment='Group name')
    name: Mapped[str | None] = mapped_column(
        String(50), comment='Middle floor name')
    cname: Mapped[str | None] = mapped_column(
        String(50), comment='Middle floor name (Chinese)'
    )
    resi: Mapped[float | None] = mapped_column(Float, comment='Resistance')
    d: Mapped[float | None] = mapped_column(Float, comment='D value')
    spflag: Mapped[int | None] = mapped_column(Integer, comment='SP flag')
    flag: Mapped[int | None] = mapped_column(Integer, comment='Flag')
    eraseflag: Mapped[int | None] = mapped_column(
        Integer, comment='Erase flag')
    anotation: Mapped[str | None] = mapped_column(
        String(255), comment='Annotation')

    # Relationships
    materials: Mapped[list[SysMiddlefloorMaterial]] = relationship(
        'SysMiddlefloorMaterial', back_populates='middlefloor'
    )


class SysMiddlefloorMaterial(Base):
    """System middle floor material layer model."""

    __tablename__ = 'sys_middlefloor_material'

    struct_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('sys_middlefloor.struct_id'),
        primary_key=True,
        comment='Structure ID (middle floor reference)',
    )
    layer_no: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Layer number'
    )
    material_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('sys_material.material_id'), comment='Material ID'
    )
    length: Mapped[float | None] = mapped_column(
        Float, comment='Length/Thickness (mm)')
    anotation: Mapped[str | None] = mapped_column(
        String(255), comment='Annotation')

    # Relationships
    middlefloor: Mapped[SysMiddlefloor | None] = relationship(
        'SysMiddlefloor', back_populates='materials'
    )
    material: Mapped[SysMaterial | None] = relationship(
        'SysMaterial', back_populates='middlefloor_materials'
    )


class SysAirfloor(Base):
    """System air floor construction model."""

    __tablename__ = 'sys_airfloor'

    struct_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Structure ID'
    )
    group_id: Mapped[str | None] = mapped_column(
        String(50), comment='Group name')
    name: Mapped[str | None] = mapped_column(
        String(50), comment='Air floor name')
    cname: Mapped[str | None] = mapped_column(
        String(50), comment='Air floor name (Chinese)'
    )
    resi: Mapped[float | None] = mapped_column(Float, comment='Resistance')
    d: Mapped[float | None] = mapped_column(Float, comment='D value')
    spflag: Mapped[int | None] = mapped_column(Integer, comment='SP flag')
    flag: Mapped[int | None] = mapped_column(Integer, comment='Flag')
    eraseflag: Mapped[int | None] = mapped_column(
        Integer, comment='Erase flag')
    anotation: Mapped[str | None] = mapped_column(
        String(255), comment='Annotation')

    # Relationships
    materials: Mapped[list[SysAirfloorMaterial]] = relationship(
        'SysAirfloorMaterial', back_populates='airfloor'
    )


class SysAirfloorMaterial(Base):
    """System air floor material layer model."""

    __tablename__ = 'sys_airfloor_material'

    struct_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('sys_airfloor.struct_id'),
        primary_key=True,
        comment='Structure ID (air floor reference)',
    )
    layer_no: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Layer number'
    )
    material_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('sys_material.material_id'), comment='Material ID'
    )
    length: Mapped[float | None] = mapped_column(
        Float, comment='Length/Thickness (mm)')
    anotation: Mapped[str | None] = mapped_column(
        String(255), comment='Annotation')

    # Relationships
    airfloor: Mapped[SysAirfloor | None] = relationship(
        'SysAirfloor', back_populates='materials'
    )
    material: Mapped[SysMaterial | None] = relationship(
        'SysMaterial', back_populates='airfloor_materials'
    )


class SysAppMaterial(Base):
    """System additional material model."""

    __tablename__ = 'sys_app_material'

    app_material_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Additional material ID'
    )
    color: Mapped[int | None] = mapped_column(Integer, comment='Color')
    group_id: Mapped[str | None] = mapped_column(
        String(50), comment='Group name')
    name: Mapped[str | None] = mapped_column(
        String(50), comment='Material name')
    cname: Mapped[str | None] = mapped_column(
        String(50), comment='Chinese name')
    conductivity: Mapped[float | None] = mapped_column(
        Float, comment='Conductivity (W/m·K)'
    )
    density: Mapped[float | None] = mapped_column(
        Float, comment='Density (kg/m³)')
    specific_heat: Mapped[float | None] = mapped_column(
        Float, comment='Specific heat (J/kg·K)'
    )
    s: Mapped[float | None] = mapped_column(Float, comment='S parameter')
    steam: Mapped[float | None] = mapped_column(
        Float, comment='Steam permeability')
    ex_coef: Mapped[float | None] = mapped_column(
        Float, comment='Emission coefficient')
    rf_coef: Mapped[float | None] = mapped_column(
        Float, comment='Reflection coefficient'
    )
    emissivity: Mapped[float | None] = mapped_column(
        Float, comment='Emissivity')
    thick: Mapped[float | None] = mapped_column(
        Float, comment='Thickness (mm)')
    pattern: Mapped[str | None] = mapped_column(String(50), comment='Pattern')
    eraseflag: Mapped[int | None] = mapped_column(
        Integer, comment='Erase flag')
    flag: Mapped[int | None] = mapped_column(Integer, comment='Flag')
    anotation: Mapped[str | None] = mapped_column(
        String(255), comment='Annotation')


class MainEnclosure(Base):
    """Main enclosure model."""

    __tablename__ = 'main_enclosure'

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Enclosure ID')
    name: Mapped[str | None] = mapped_column(
        String(50), comment='Enclosure name')
    side1: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('surface.surface_id'), comment='Side 1'
    )
    side2: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('surface.surface_id'), comment='Side 2'
    )
    middle_plane: Mapped[int | None] = mapped_column(
        Integer, comment='Middle plane')
    kind: Mapped[int | None] = mapped_column(Integer, comment='Enclosure kind')
    construction: Mapped[int | None] = mapped_column(
        Integer, comment='Construction ID')
    user_def_dll: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('user_def_dll.dll_id'), comment='User defined DLL'
    )
    cal_num_shares: Mapped[int | None] = mapped_column(
        Integer, comment='Calculation shares number'
    )
    fourier_num: Mapped[int | None] = mapped_column(
        Integer, comment='Fourier number')
    of_storey: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('storey.id'), comment='Storey reference'
    )
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
    user_def_dll_ref: Mapped[UserDefDll | None] = relationship('UserDefDll')
    storey: Mapped[Storey | None] = relationship('Storey')


class LibPhaseChangeMat(Base):
    """Phase change material library model."""

    __tablename__ = 'lib_phase_change_mat'

    lib_phase_change_mat_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='PCM ID'
    )
    name: Mapped[str | None] = mapped_column(
        String(50), comment='Material name')
    tm: Mapped[float | None] = mapped_column(
        Float, comment='Phase change temperature (°C)'
    )
    cp_s: Mapped[float | None] = mapped_column(
        Float, comment='Solid specific heat (J/kg·K)'
    )
    cp_m: Mapped[float | None] = mapped_column(
        Float, comment='Mushy zone specific heat (J/kg·K)'
    )
    cp_l: Mapped[float | None] = mapped_column(
        Float, comment='Liquid specific heat (J/kg·K)'
    )
    rou: Mapped[float | None] = mapped_column(Float, comment='Density (kg/m³)')
    lamda: Mapped[float | None] = mapped_column(
        Float, comment='Thermal conductivity (W/m·K)'
    )
    remark: Mapped[str | None] = mapped_column(String(255), comment='Remark')
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )


class PhaseChangeMat(Base):
    """Phase change material model."""

    __tablename__ = 'phase_change_mat'

    room_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('room.id'), primary_key=True, comment='Room ID'
    )
    enclosure: Mapped[int | None] = mapped_column(Integer, ForeignKey(
        'main_enclosure.id'), primary_key=True, comment='Enclosure ID')
    thickness: Mapped[float | None] = mapped_column(
        Float, comment='Thickness (mm)')
    area_ratio: Mapped[float | None] = mapped_column(
        Float, comment='Area ratio')
    lib_phase_change_mat_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('lib_phase_change_mat.lib_phase_change_mat_id'),
        comment='PCM library ID',
    )
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )

    # Relationships
    room: Mapped[Room | None] = relationship('Room')
    lib_phase_change_mat: Mapped[LibPhaseChangeMat | None] = relationship(
        'LibPhaseChangeMat'
    )
    enclosure: Mapped[MainEnclosure | None] = relationship('MainEnclosure')


class GroundConstruction(Base):
    """Ground construction model."""

    __tablename__ = 'ground_construction'

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Ground construction ID'
    )
    name: Mapped[str | None] = mapped_column(
        String(50), comment='Construction name')
    type: Mapped[int | None] = mapped_column(
        Integer, comment='Construction type')
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )


class GroundData(Base):
    """Ground data model (hourly ground temperature)."""

    __tablename__ = 'ground_data'

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Ground data ID')
    hour: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Hour of year (0-8759)'
    )
    t: Mapped[float | None] = mapped_column(Float, comment='Temperature (°C)')
