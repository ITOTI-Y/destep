from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    Numeric,
    SmallInteger,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ._base import Base

if TYPE_CHECKING:
    from .schedule import ScheduleYear


class RoomTypeData(Base):
    """Room type data model."""

    __tablename__ = 'room_type_data'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Room type ID')
    name: Mapped[str | None] = mapped_column(String(50), comment='Room type name')
    furniture_coef: Mapped[float | None] = mapped_column(
        Float, comment='Furniture coefficient'
    )
    o_schedule: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('schedule_year.schedule_id'), comment='Occupant schedule'
    )
    o_maxnumber: Mapped[float | None] = mapped_column(
        Float, comment='Maximum occupants'
    )
    o_minnumber: Mapped[float | None] = mapped_column(
        Float, comment='Minimum occupants'
    )
    o_heat_per_person: Mapped[float | None] = mapped_column(
        Float, comment='Sensible heat per person (W/person)'
    )
    o_damp_per_person: Mapped[float | None] = mapped_column(
        Float, comment='Moisture load per person (g/h·person)'
    )
    o_min_require_fresh_air: Mapped[float | None] = mapped_column(
        Float, comment='Minimum fresh air requirement (m³/h·person)'
    )
    o_per_area: Mapped[int | None] = mapped_column(
        Integer, comment='Calculate occupants by area'
    )
    o_a: Mapped[float | None] = mapped_column(Float, comment='Occupant coefficient A')
    o_b: Mapped[float | None] = mapped_column(Float, comment='Occupant coefficient B')
    o_dist_mode: Mapped[int | None] = mapped_column(
        Integer, comment='Occupant distribution mode'
    )
    l_schedule: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('schedule_year.schedule_id'), comment='Lighting schedule'
    )
    l_maxpower: Mapped[float | None] = mapped_column(
        Float, comment='Maximum lighting power (W/m²)'
    )
    l_minpower: Mapped[float | None] = mapped_column(
        Float, comment='Minimum lighting power (W/m²)'
    )
    l_heat_rate: Mapped[float | None] = mapped_column(
        Float, comment='Lighting heat dissipation rate'
    )
    l_per_area: Mapped[int | None] = mapped_column(
        Integer, comment='Calculate lighting by area'
    )
    l_a: Mapped[float | None] = mapped_column(Float, comment='Lighting coefficient A')
    l_b: Mapped[float | None] = mapped_column(Float, comment='Lighting coefficient B')
    l_dist_mode: Mapped[int | None] = mapped_column(
        Integer, comment='Lighting distribution mode'
    )
    e_schedule: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('schedule_year.schedule_id'), comment='Equipment schedule'
    )
    e_maxpower: Mapped[float | None] = mapped_column(
        Float, comment='Maximum equipment power (W/m²)'
    )
    e_minpower: Mapped[float | None] = mapped_column(
        Float, comment='Minimum equipment power (W/m²)'
    )
    e_max_hum: Mapped[float | None] = mapped_column(
        Float, comment='Maximum equipment humidity load'
    )
    e_min_hum: Mapped[float | None] = mapped_column(
        Float, comment='Minimum equipment humidity load'
    )
    e_per_area: Mapped[int | None] = mapped_column(
        Integer, comment='Calculate equipment by area'
    )
    e_a: Mapped[float | None] = mapped_column(Float, comment='Equipment coefficient A')
    e_b: Mapped[float | None] = mapped_column(Float, comment='Equipment coefficient B')
    e_dist_mode: Mapped[int | None] = mapped_column(
        Integer, comment='Equipment distribution mode'
    )
    ac_schedule_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('schedule_year.schedule_id'), comment='AC schedule'
    )
    set_t_min_schedule: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('schedule_year.schedule_id'),
        comment='Set temperature min schedule',
    )
    set_t_max_schedule: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('schedule_year.schedule_id'),
        comment='Set temperature max schedule',
    )
    set_rh_min_schedule: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('schedule_year.schedule_id'),
        comment='Set relative humidity min schedule',
    )
    set_rh_max_schedule: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('schedule_year.schedule_id'),
        comment='Set relative humidity max schedule',
    )
    ac_t_min_schedule: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('schedule_year.schedule_id'),
        comment='AC temperature min schedule',
    )
    ac_t_max_schedule: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('schedule_year.schedule_id'),
        comment='AC temperature max schedule',
    )
    set_min_luminance: Mapped[float | None] = mapped_column(
        Float, comment='Minimum luminance setting (lux)'
    )
    remark: Mapped[str | None] = mapped_column(String(255), comment='Remark')
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )

    # Relationships
    occupant_schedule: Mapped[ScheduleYear | None] = relationship(
        'ScheduleYear', foreign_keys=[o_schedule]
    )
    lighting_schedule: Mapped[ScheduleYear | None] = relationship(
        'ScheduleYear', foreign_keys=[l_schedule]
    )
    equipment_schedule: Mapped[ScheduleYear | None] = relationship(
        'ScheduleYear', foreign_keys=[e_schedule]
    )
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


class DefaultSetting(Base):
    """Default setting model (field default values)."""

    __tablename__ = 'default_setting'

    table_name: Mapped[str] = mapped_column(
        String(50), primary_key=True, comment='Table name'
    )
    field_name: Mapped[str] = mapped_column(
        String(50), primary_key=True, comment='Field name'
    )
    kind: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Kind')
    string: Mapped[str | None] = mapped_column(String(255), comment='String value')
    long: Mapped[int | None] = mapped_column(Integer, comment='Long value')
    double: Mapped[float | None] = mapped_column(  # type: ignore
        Float, comment='Double value'
    )
    float: Mapped[float | None] = mapped_column(  # type: ignore
        Float, comment='Float value'
    )
    short: Mapped[int | None] = mapped_column(Integer, comment='Short value')
    type: Mapped[int | None] = mapped_column(Integer, comment='Type')
    comment: Mapped[str | None] = mapped_column(String(255), comment='Comment')


class UserDefDll(Base):
    """User defined DLL model."""

    __tablename__ = 'user_def_dll'

    dll_id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='DLL ID')
    name: Mapped[str | None] = mapped_column(String(50), comment='DLL name')
    dll: Mapped[bytes | None] = mapped_column(LargeBinary, comment='DLL binary')
    type: Mapped[int | None] = mapped_column(Integer, comment='DLL type')


class DistMode(Base):
    """Distribution mode model (heat distribution ratios)."""

    __tablename__ = 'dist_mode'

    dist_mode_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Distribution mode ID'
    )
    dist_air: Mapped[float | None] = mapped_column(
        Float, comment='Air distribution ratio'
    )
    dist_roof: Mapped[float | None] = mapped_column(
        Float, comment='Roof distribution ratio'
    )
    dist_floor: Mapped[float | None] = mapped_column(
        Float, comment='Floor distribution ratio'
    )
    dist_around: Mapped[float | None] = mapped_column(
        Float, comment='Surrounding distribution ratio'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='Mode name')


class DpeStatus(Base):
    """DPE status/option model."""

    __tablename__ = 'dpe_status'

    option_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Option ID'
    )
    keyword: Mapped[str | None] = mapped_column(String(50), comment='Keyword')
    explain: Mapped[str | None] = mapped_column(String(255), comment='Explanation')
    type: Mapped[int | None] = mapped_column(Integer, comment='Type')
    option_string: Mapped[str | None] = mapped_column(
        String(255), comment='Option string value'
    )


class UniqueId(Base):
    """Unique ID model."""

    __tablename__ = 'unique_id'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='ID')
    remark: Mapped[str | None] = mapped_column(String(255), comment='Remark')


class ExtProperty(Base):
    """Extended property model."""

    __tablename__ = 'ext_property'

    property_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Extended property ID'
    )
    next_property: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('ext_property.property_id'), comment='Next property ID'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='Property name')
    type: Mapped[int | None] = mapped_column(Integer, comment='Property type')
    data_long: Mapped[int | None] = mapped_column(Integer, comment='Long data')
    data_double: Mapped[float | None] = mapped_column(Float, comment='Double data')
    data_string: Mapped[str | None] = mapped_column(String(255), comment='String data')
    data_bin: Mapped[bytes | None] = mapped_column(LargeBinary, comment='Binary data')

    # Relationships (self-referencing)
    next_property_ref: Mapped[ExtProperty | None] = relationship(
        'ExtProperty', remote_side=[property_id]
    )


class Option(Base):
    """Option model."""

    __tablename__ = 'option'

    keyword: Mapped[str] = mapped_column(
        String(50), primary_key=True, comment='Keyword'
    )
    option_id: Mapped[int | None] = mapped_column(Integer, comment='Option ID')
    explain: Mapped[str | None] = mapped_column(String(255), comment='Explanation')
    type: Mapped[int | None] = mapped_column(Integer, comment='Type')
    option_string: Mapped[str | None] = mapped_column(
        String(255), comment='Option string value'
    )


class VersionControl(Base):
    """Version control model (no primary key in DB)."""

    __tablename__ = 'version_control'

    # Note: In the actual database, this table has no primary key.
    # We use major as a pseudo primary key for ORM compatibility.
    major: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Major version'
    )
    minor: Mapped[int | None] = mapped_column(Integer, comment='Minor version')


class IdRegister(Base):
    """ID register model."""

    __tablename__ = 'id_register'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='ID')
    allocator: Mapped[str | None] = mapped_column(String(50), comment='Allocator')
    datetime: Mapped[datetime | None] = mapped_column(  # type: ignore
        DateTime, comment='Datetime'
    )
    owner_object: Mapped[str | None] = mapped_column(String(50), comment='Owner object')
    owner_table: Mapped[str | None] = mapped_column(String(50), comment='Owner table')
    use_state: Mapped[bool | None] = mapped_column(Boolean, comment='Use state')


class SysDuctModal(Base):
    """System duct modal model (duct size specifications)."""

    __tablename__ = 'sys_duct_modal'

    area: Mapped[float] = mapped_column(
        Float, primary_key=True, comment='Cross-section area'
    )
    width: Mapped[int] = mapped_column(
        SmallInteger, primary_key=True, comment='Width (mm)'
    )
    high: Mapped[int] = mapped_column(
        SmallInteger, primary_key=True, comment='Height (mm)'
    )
    anotation: Mapped[str | None] = mapped_column(String(255), comment='Annotation')


class SysGroups(Base):
    """System groups model."""

    __tablename__ = 'sys_groups'

    group_id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Group ID')
    type: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Group type')
    name: Mapped[str | None] = mapped_column(String(50), comment='Group name')
    anotation: Mapped[str | None] = mapped_column(String(255), comment='Annotation')
    cname: Mapped[str | None] = mapped_column(String(50), comment='Chinese name')


class LibWindRatioType(Base):
    """Wind pressure ratio type library model."""

    __tablename__ = 'lib_wind_ratio_type'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Type ID')
    name: Mapped[str | None] = mapped_column(String(50), comment='Type name')
    group_name: Mapped[str | None] = mapped_column(String(50), comment='Group name')
    remark: Mapped[str | None] = mapped_column(String(255), comment='Remark')


class LibWindRatioModel(Base):
    """Wind pressure ratio model library model (no primary key in DB)."""

    __tablename__ = 'lib_wind_ratio_model'

    # Note: In the actual database, this table has no primary key.
    # We use id as a pseudo primary key for ORM compatibility.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Model ID')
    name: Mapped[str | None] = mapped_column(String(50), comment='Model name')
    d0: Mapped[float | None] = mapped_column(Float, comment='D0')
    d1: Mapped[float | None] = mapped_column(Float, comment='D1')
    d2: Mapped[float | None] = mapped_column(Float, comment='D2')
    d3: Mapped[float | None] = mapped_column(Float, comment='D3')
    d4: Mapped[float | None] = mapped_column(Float, comment='D4')
    d5: Mapped[float | None] = mapped_column(Float, comment='D5')
    d6: Mapped[float | None] = mapped_column(Float, comment='D6')
    d7: Mapped[float | None] = mapped_column(Float, comment='D7')
    d8: Mapped[float | None] = mapped_column(Float, comment='D8')
    remark: Mapped[str | None] = mapped_column(String(255), comment='Remark')


class LibWindRatioModelV1(Base):
    """Wind pressure ratio model library V1 model."""

    __tablename__ = 'lib_wind_ratio_model_v1'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Model ID')
    name: Mapped[str | None] = mapped_column(String(50), comment='Model name')
    d0: Mapped[float | None] = mapped_column(Float, comment='D0')
    d1: Mapped[float | None] = mapped_column(Float, comment='D1')
    d2: Mapped[float | None] = mapped_column(Float, comment='D2')
    d3: Mapped[float | None] = mapped_column(Float, comment='D3')
    d4: Mapped[float | None] = mapped_column(Float, comment='D4')
    d5: Mapped[float | None] = mapped_column(Float, comment='D5')
    d6: Mapped[float | None] = mapped_column(Float, comment='D6')
    d7: Mapped[float | None] = mapped_column(Float, comment='D7')
    d8: Mapped[float | None] = mapped_column(Float, comment='D8')
    d9: Mapped[float | None] = mapped_column(Float, comment='D9')
    d10: Mapped[float | None] = mapped_column(Float, comment='D10')
    d11: Mapped[float | None] = mapped_column(Float, comment='D11')
    d12: Mapped[float | None] = mapped_column(Float, comment='D12')
    d13: Mapped[float | None] = mapped_column(Float, comment='D13')
    d14: Mapped[float | None] = mapped_column(Float, comment='D14')
    d15: Mapped[float | None] = mapped_column(Float, comment='D15')
    remark: Mapped[str | None] = mapped_column(String(255), comment='Remark')


class LibCurve(Base):
    """Curve library model."""

    __tablename__ = 'lib_curve'

    lib_curve_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Curve library ID'
    )
    type: Mapped[int | None] = mapped_column(Integer, comment='Curve type')
    name: Mapped[str | None] = mapped_column(String(50), comment='Curve name')
    count: Mapped[int | None] = mapped_column(Integer, comment='Coefficient count')
    a: Mapped[float | None] = mapped_column(Float, comment='Coefficient A')
    b: Mapped[float | None] = mapped_column(Float, comment='Coefficient B')
    c: Mapped[float | None] = mapped_column(Float, comment='Coefficient C')
    d: Mapped[float | None] = mapped_column(Float, comment='Coefficient D')
    e: Mapped[float | None] = mapped_column(Float, comment='Coefficient E')
    f: Mapped[float | None] = mapped_column(Float, comment='Coefficient F')
    g: Mapped[float | None] = mapped_column(Float, comment='Coefficient G')
    h: Mapped[float | None] = mapped_column(Float, comment='Coefficient H')
    i: Mapped[float | None] = mapped_column(Float, comment='Coefficient I')
    j: Mapped[float | None] = mapped_column(Float, comment='Coefficient J')
    k: Mapped[float | None] = mapped_column(Float, comment='Coefficient K')
    l: Mapped[float | None] = mapped_column(Float, comment='Coefficient L')  # noqa: E741
    note: Mapped[str | None] = mapped_column(String(255), comment='Note')
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )


class LibProduct(Base):
    """Product library model."""

    __tablename__ = 'lib_product'

    product_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Product ID'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='Product name')
    producer: Mapped[str | None] = mapped_column(String(100), comment='Producer')
    contact: Mapped[str | None] = mapped_column(String(100), comment='Contact')
    price: Mapped[float | None] = mapped_column(Float, comment='Price')
    length: Mapped[float | None] = mapped_column(Float, comment='Length (mm)')
    width: Mapped[float | None] = mapped_column(Float, comment='Width (mm)')
    height: Mapped[float | None] = mapped_column(Float, comment='Height (mm)')
    weight: Mapped[float | None] = mapped_column(Float, comment='Weight (kg)')
    expire: Mapped[datetime | None] = mapped_column(DateTime, comment='Expiration date')
    picture: Mapped[bytes | None] = mapped_column(LargeBinary, comment='Picture')
    note: Mapped[str | None] = mapped_column(String(255), comment='Note')
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )


class LibSolarEnergyCollector(Base):
    """Solar energy collector library model."""

    __tablename__ = 'lib_solar_energy_collector'

    lib_solar_energy_collector_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Collector ID'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='Name')
    type: Mapped[int | None] = mapped_column(Integer, comment='Type')
    alpha: Mapped[float | None] = mapped_column(Float, comment='Alpha')
    area_ratio: Mapped[float | None] = mapped_column(Numeric, comment='Area ratio')
    fe: Mapped[float | None] = mapped_column(Float, comment='Fe')
    k: Mapped[float | None] = mapped_column(Float, comment='K')
    remark: Mapped[str | None] = mapped_column(String(255), comment='Remark')
    tao: Mapped[float | None] = mapped_column(Float, comment='Tao')
    tilt: Mapped[float | None] = mapped_column(Float, comment='Tilt')
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )


class LibShpDeviceV1(Base):
    """SHP device library V1 model."""

    __tablename__ = 'lib_shp_device_v1'

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='SHP device library ID'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='Name')
    a1: Mapped[float | None] = mapped_column(Float, comment='A1')
    b1: Mapped[float | None] = mapped_column(Float, comment='B1')
    p1: Mapped[float | None] = mapped_column(Float, comment='P1')
    a2: Mapped[float | None] = mapped_column(Float, comment='A2')
    b2: Mapped[float | None] = mapped_column(Float, comment='B2')
    p2: Mapped[float | None] = mapped_column(Float, comment='P2')
    a3: Mapped[float | None] = mapped_column(Float, comment='A3')
    b3: Mapped[float | None] = mapped_column(Float, comment='B3')
    p3: Mapped[float | None] = mapped_column(Float, comment='P3')
    remark: Mapped[str | None] = mapped_column(String(255), comment='Remark')


class Sky(Base):
    """Sky model."""

    __tablename__ = 'sky'

    sky_id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Sky ID')
    name: Mapped[str | None] = mapped_column(String(50), comment='Name')
    sky_data_id: Mapped[int | None] = mapped_column(Integer, comment='Sky data ID')
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )


class LibRoofunitDevice(Base):
    """Roofunit device library model."""

    __tablename__ = 'lib_roofunit_device'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Device ID')
    name: Mapped[str | None] = mapped_column(String(50), comment='Name')
    flowrate: Mapped[float | None] = mapped_column(Float, comment='Flow rate')
    cool_cap: Mapped[float | None] = mapped_column(Float, comment='Cooling capacity')
    heat_cap: Mapped[float | None] = mapped_column(Float, comment='Heating capacity')
    cool_power: Mapped[float | None] = mapped_column(Float, comment='Cooling power')
    heat_power: Mapped[float | None] = mapped_column(Float, comment='Heating power')
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )


class DefaultCoef(Base):
    """Default coefficient model."""

    __tablename__ = 'default_coef'

    default_coef_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Default coefficient ID'
    )
    coef_name: Mapped[str | None] = mapped_column(
        String(30), comment='Coefficient name'
    )
    value: Mapped[float | None] = mapped_column(Float, comment='Coefficient value')
    comment: Mapped[str | None] = mapped_column(String(255), comment='Comment')
    note_file: Mapped[str | None] = mapped_column(String(255), comment='Note file')


class EquipmentTemp(Base):
    """Temporary equipment model."""

    __tablename__ = 'equipment_temp'

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Temporary equipment ID'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='Equipment name')
    of_room: Mapped[int | None] = mapped_column(Integer, comment='Room ID')
    equipment_type: Mapped[int | None] = mapped_column(
        Integer, comment='Equipment type'
    )


class GainRefer(Base):
    """Gain reference model."""

    __tablename__ = 'gain_refer'

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Gain reference ID'
    )
    type: Mapped[int | None] = mapped_column(Integer, comment='Type')
    gain_id: Mapped[int | None] = mapped_column(Integer, comment='Gain ID')
    of_room_group: Mapped[int | None] = mapped_column(Integer, comment='Room group ID')
    index: Mapped[int | None] = mapped_column(Integer, comment='Index')
    rooom_index: Mapped[int | None] = mapped_column(Integer, comment='Room index')


class GroundQ(Base):
    """Ground heat model."""

    __tablename__ = 'ground_q'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Ground heat ID')
    qa: Mapped[float | None] = mapped_column(Numeric, comment='QA value')
    qf: Mapped[float | None] = mapped_column(Numeric, comment='QF value')
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )


class LibWindRatioTypeModel(Base):
    """Wind ratio type model library model."""

    __tablename__ = 'lib_wind_ratio_type_model'

    type_id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Type ID')
    percent: Mapped[int] = mapped_column(
        SmallInteger, primary_key=True, comment='Percent'
    )
    model_id: Mapped[int | None] = mapped_column(Integer, comment='Model ID')


class SolarEnergyCollector(Base):
    """Solar energy collector model."""

    __tablename__ = 'solar_energy_collector'

    room_id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Room ID')
    enclosure: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Enclosure'
    )
    lib_solar_energy_collector_id: Mapped[int | None] = mapped_column(
        Integer, comment='Solar energy collector library ID'
    )
    area_ratio: Mapped[float | None] = mapped_column(Numeric, comment='Area ratio')
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )


class SysOption(Base):
    """System option model."""

    __tablename__ = 'sys_option'

    option_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Option ID'
    )
    keyword: Mapped[str | None] = mapped_column(String(100), comment='Keyword')
    option_string: Mapped[str | None] = mapped_column(
        String(255), comment='Option string'
    )
    type: Mapped[int | None] = mapped_column(Integer, comment='Type')
    explain: Mapped[str | None] = mapped_column(String(255), comment='Explanation')


class UserDefDev(Base):
    """User defined device model."""

    __tablename__ = 'user_def_dev'

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='User defined device ID'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='Device name')
    of_room: Mapped[int | None] = mapped_column(Integer, comment='Room ID')
    dll_file_name: Mapped[str | None] = mapped_column(
        String(255), comment='DLL file name'
    )
