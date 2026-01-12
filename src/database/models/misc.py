from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Integer, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from ._base import Base


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


class DefaultSetting(Base):
    """Default setting model (field default values)."""

    __tablename__ = 'default_setting'

    table_name: Mapped[str] = mapped_column(
        String(50), primary_key=True, comment='Table name'
    )
    field_name: Mapped[str] = mapped_column(
        String(50), primary_key=True, comment='Field name'
    )
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
    kind: Mapped[int | None] = mapped_column(Integer, comment='Kind')
    comment: Mapped[str | None] = mapped_column(String(255), comment='Comment')


class UserDefDll(Base):
    """User defined DLL model."""

    __tablename__ = 'user_def_dll'

    dll_id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='DLL ID')
    name: Mapped[str | None] = mapped_column(String(50), comment='DLL name')
    dll_path: Mapped[str | None] = mapped_column(String(255), comment='DLL path')
    type: Mapped[int | None] = mapped_column(Integer, comment='DLL type')
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )


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
        Integer, comment='Next property ID'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='Property name')
    type: Mapped[int | None] = mapped_column(Integer, comment='Property type')
    data_long: Mapped[int | None] = mapped_column(Integer, comment='Long data')
    data_double: Mapped[float | None] = mapped_column(Float, comment='Double data')
    data_string: Mapped[str | None] = mapped_column(String(255), comment='String data')
    data_bin: Mapped[bytes | None] = mapped_column(LargeBinary, comment='Binary data')


class Option(Base):
    """Option model."""

    __tablename__ = 'option'

    option_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Option ID'
    )
    keyword: Mapped[str | None] = mapped_column(String(50), comment='Keyword')
    explain: Mapped[str | None] = mapped_column(String(255), comment='Explanation')
    type: Mapped[int | None] = mapped_column(Integer, comment='Type')
    option_string: Mapped[str | None] = mapped_column(
        String(255), comment='Option string value'
    )


class VersionControl(Base):
    """Version control model."""

    __tablename__ = 'version_control'

    major: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Major version'
    )
    minor: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Minor version'
    )


class IdRegister(Base):
    """ID register model."""

    __tablename__ = 'id_register'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='ID')
    table_name: Mapped[str | None] = mapped_column(String(50), comment='Table name')
    object_id: Mapped[int | None] = mapped_column(Integer, comment='Object ID')
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )


class SysDuctModal(Base):
    """System duct modal model (duct size specifications)."""

    __tablename__ = 'sys_duct_modal'

    area: Mapped[float] = mapped_column(
        Float, primary_key=True, comment='Cross-section area'
    )
    width: Mapped[float | None] = mapped_column(Float, comment='Width (mm)')
    high: Mapped[float | None] = mapped_column(Float, comment='Height (mm)')
    anotation: Mapped[str | None] = mapped_column(String(255), comment='Annotation')


class SysGroups(Base):
    """System groups model."""

    __tablename__ = 'sys_groups'

    group_id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Group ID')
    name: Mapped[str | None] = mapped_column(String(50), comment='Group name')
    type: Mapped[int | None] = mapped_column(Integer, comment='Group type')
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )


class LibWindRatioType(Base):
    """Wind pressure ratio type library model."""

    __tablename__ = 'lib_wind_ratio_type'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Type ID')
    name: Mapped[str | None] = mapped_column(String(50), comment='Type name')
    group_name: Mapped[str | None] = mapped_column(String(50), comment='Group name')
    remark: Mapped[str | None] = mapped_column(String(255), comment='Remark')


class LibWindRatioModel(Base):
    """Wind pressure ratio model library model."""

    __tablename__ = 'lib_wind_ratio_model'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Model ID')
    name: Mapped[str | None] = mapped_column(String(50), comment='Model name')
    type_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('lib_wind_ratio_type.id'), comment='Type ID'
    )
    data: Mapped[bytes | None] = mapped_column(LargeBinary, comment='Model data')
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )


class LibWindRatioModelV1(Base):
    """Wind pressure ratio model library V1 model."""

    __tablename__ = 'lib_wind_ratio_model_v1'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Model ID')
    name: Mapped[str | None] = mapped_column(String(50), comment='Model name')
    type_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('lib_wind_ratio_type.id'), comment='Type ID'
    )
    data: Mapped[bytes | None] = mapped_column(LargeBinary, comment='Model data')
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )


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
    expire: Mapped[str | None] = mapped_column(String(50), comment='Expiration date')
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
    area: Mapped[float | None] = mapped_column(Float, comment='Area')
    efficiency: Mapped[float | None] = mapped_column(Float, comment='Efficiency')
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
