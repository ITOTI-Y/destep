from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ._base import Base

if TYPE_CHECKING:
    from .building import Building, Room, RoomGroup
    from .misc import LibCurve, LibProduct
    from .schedule import ScheduleYear


class AcSys(Base):
    """Air conditioning system model."""

    __tablename__ = 'ac_sys'

    ac_sys_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='AC system ID'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='System name')
    ac_sys_type: Mapped[int | None] = mapped_column(
        SmallInteger, comment='AC system type'
    )
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )
    fresh_air_outside: Mapped[int | None] = mapped_column(Integer)
    fresh_air_type: Mapped[int | None] = mapped_column(SmallInteger)
    max_fresh_air_ratio: Mapped[float | None] = mapped_column(Float)
    max_fresh_air_volume: Mapped[float | None] = mapped_column(Float)
    min_fresh_air_ratio: Mapped[float | None] = mapped_column(Float)
    min_fresh_air_volume: Mapped[float | None] = mapped_column(Float)
    of_building: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('building.building_id')
    )
    of_storey: Mapped[int | None] = mapped_column(Integer, ForeignKey('storey.id'))
    supply_state_flag: Mapped[int | None] = mapped_column(SmallInteger)
    supply_t_max: Mapped[int | None] = mapped_column(Integer)
    supply_t_min: Mapped[int | None] = mapped_column(Integer)
    user_def_supply_d: Mapped[int | None] = mapped_column(Integer)
    user_def_supply_t: Mapped[int | None] = mapped_column(Integer)
    view_cool_load: Mapped[bool | None] = mapped_column(Boolean)
    view_flow: Mapped[bool | None] = mapped_column(Boolean)
    view_fresh_air_ratio: Mapped[bool | None] = mapped_column(Boolean)
    view_heat_load: Mapped[bool | None] = mapped_column(Boolean)
    view_humi_load: Mapped[bool | None] = mapped_column(Boolean)
    water_type: Mapped[int | None] = mapped_column(SmallInteger)
    x: Mapped[float | None] = mapped_column(Float)
    y: Mapped[float | None] = mapped_column(Float)
    z: Mapped[float | None] = mapped_column(Float)

    # Relationships
    room_groups: Mapped[list[RoomGroup]] = relationship(
        'RoomGroup', back_populates='ac_sys'
    )
    ahus: Mapped[list[Ahu]] = relationship('Ahu', back_populates='ac_sys')


class Ahu(Base):
    """Air handling unit model."""

    __tablename__ = 'ahu'

    ahu_id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='AHU ID')
    name: Mapped[str | None] = mapped_column(String(50), comment='Unit name')
    of_ac_sys: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('ac_sys.ac_sys_id'), comment='Parent AC system'
    )
    type: Mapped[int | None] = mapped_column(Integer, comment='Unit type')
    cooling_coil: Mapped[int | None] = mapped_column(Integer, comment='Cooling coil')
    coil_type: Mapped[int | None] = mapped_column(Integer, comment='Coil type')
    coil_num: Mapped[int | None] = mapped_column(Integer, comment='Coil count')
    sprayer: Mapped[int | None] = mapped_column(Integer, comment='Sprayer')
    heater: Mapped[int | None] = mapped_column(Integer, comment='Heater')
    humidifier: Mapped[int | None] = mapped_column(Integer, comment='Humidifier')
    reheat_type: Mapped[int | None] = mapped_column(Integer, comment='Reheat type')
    heat_recover: Mapped[int | None] = mapped_column(Integer, comment='Heat recovery')
    min_t_ex_coef: Mapped[float | None] = mapped_column(
        Float, comment='Minimum temperature exchange coefficient'
    )
    max_t_ex_coef: Mapped[float | None] = mapped_column(
        Float, comment='Maximum temperature exchange coefficient'
    )
    min_d_ex_coef: Mapped[float | None] = mapped_column(
        Float, comment='Minimum humidity exchange coefficient'
    )
    max_d_ex_coef: Mapped[float | None] = mapped_column(
        Float, comment='Maximum humidity exchange coefficient'
    )
    second_air: Mapped[bool | None] = mapped_column(
        Boolean, default=False, comment='Return air enabled'
    )
    min_second_air_ratio: Mapped[float | None] = mapped_column(
        Float, comment='Minimum return air ratio'
    )
    max_second_air_ratio: Mapped[float | None] = mapped_column(
        Float, comment='Maximum return air ratio'
    )
    fan: Mapped[int | None] = mapped_column(Integer, comment='Fan')
    ahures: Mapped[int | None] = mapped_column(Integer, comment='AHU result')
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )

    # Relationships
    ac_sys: Mapped[AcSys | None] = relationship('AcSys', back_populates='ahus')


class LibChiller(Base):
    """Chiller library model."""

    __tablename__ = 'lib_chiller'

    lib_chiller_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Library chiller ID'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='Unit name')
    type: Mapped[int | None] = mapped_column(Integer, comment='Unit type')
    capacity: Mapped[float | None] = mapped_column(
        Float, comment='Cooling capacity (kW)'
    )
    flowrate_cold: Mapped[float | None] = mapped_column(
        Float, comment='Chilled water flow rate (m³/h)'
    )
    flowrate_cool: Mapped[float | None] = mapped_column(
        Float, comment='Cooling water flow rate (m³/h)'
    )
    pressure_loss_cold: Mapped[float | None] = mapped_column(
        Float, comment='Chilled water pressure loss (kPa)'
    )
    pressure_loss_cool: Mapped[float | None] = mapped_column(
        Float, comment='Cooling water pressure loss (kPa)'
    )
    cop: Mapped[float | None] = mapped_column(Float, comment='COP')
    cop_curve: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('lib_curve.lib_curve_id'), comment='COP curve ID'
    )
    fuel_type: Mapped[int | None] = mapped_column(Integer, comment='Fuel type')
    fuel_heat_value: Mapped[float | None] = mapped_column(
        Float, comment='Fuel heat value (kJ/kg)'
    )
    consume_fuel: Mapped[float | None] = mapped_column(
        Float, comment='Fuel consumption'
    )
    consume_elec: Mapped[float | None] = mapped_column(
        Float, comment='Electricity consumption (kW)'
    )
    fanpump_num: Mapped[int | None] = mapped_column(Integer, comment='Fan/pump number')
    fanpump_power: Mapped[float | None] = mapped_column(
        Float, comment='Fan/pump power (kW)'
    )
    product_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('lib_product.product_id'), comment='Product ID'
    )
    blank_1: Mapped[float | None] = mapped_column(Float, comment='Reserved field 1')
    blank_2: Mapped[float | None] = mapped_column(Float, comment='Reserved field 2')
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )

    # Relationships
    cop_curve_obj: Mapped[LibCurve | None] = relationship('LibCurve')
    product: Mapped[LibProduct | None] = relationship('LibProduct')


class Chiller(Base):
    """Chiller model."""

    __tablename__ = 'chiller'

    chiller_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Chiller ID'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='Unit name')
    lib_chiller_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('lib_chiller.lib_chiller_id'), comment='Library chiller ID'
    )
    prime_pump: Mapped[int | None] = mapped_column(Integer, comment='Primary pump')
    second_pump: Mapped[int | None] = mapped_column(Integer, comment='Secondary pump')
    coolingtower: Mapped[int | None] = mapped_column(Integer, comment='Cooling tower')
    priority: Mapped[int | None] = mapped_column(Integer, comment='Priority')
    blank_1: Mapped[float | None] = mapped_column(Float, comment='Reserved field 1')
    blank_2: Mapped[float | None] = mapped_column(Float, comment='Reserved field 2')
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )

    # Relationships
    lib_chiller: Mapped[LibChiller | None] = relationship('LibChiller')


class LibBoiler(Base):
    """Boiler library model."""

    __tablename__ = 'lib_boiler'

    lib_boiler_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Library boiler ID'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='Boiler name')
    type: Mapped[int | None] = mapped_column(Integer, comment='Boiler type')
    capacity: Mapped[float | None] = mapped_column(
        Float, comment='Heating capacity (kW)'
    )
    flowrate: Mapped[float | None] = mapped_column(Float, comment='Flow rate (m³/h)')
    pressure_loss: Mapped[float | None] = mapped_column(
        Float, comment='Pressure loss (kPa)'
    )
    steam_pressure: Mapped[float | None] = mapped_column(
        Float, comment='Steam pressure (kPa)'
    )
    supply_temperature: Mapped[float | None] = mapped_column(
        Float, comment='Supply temperature (°C)'
    )
    return_temperature: Mapped[float | None] = mapped_column(
        Float, comment='Return temperature (°C)'
    )
    efficiency: Mapped[float | None] = mapped_column(Float, comment='Efficiency')
    cop: Mapped[float | None] = mapped_column(Float, comment='COP')
    cop_curve: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('lib_curve.lib_curve_id'), comment='COP curve ID'
    )
    fuel_type: Mapped[int | None] = mapped_column(Integer, comment='Fuel type')
    fuel_heat_value: Mapped[float | None] = mapped_column(
        Float, comment='Fuel heat value (kJ/kg)'
    )
    consume_fuel: Mapped[float | None] = mapped_column(
        Float, comment='Fuel consumption'
    )
    consume_elec: Mapped[float | None] = mapped_column(
        Float, comment='Electricity consumption (kW)'
    )
    fanpump_num: Mapped[int | None] = mapped_column(Integer, comment='Fan/pump number')
    fanpump_power: Mapped[float | None] = mapped_column(
        Float, comment='Fan/pump power (kW)'
    )
    product_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('lib_product.product_id'), comment='Product ID'
    )
    blank_1: Mapped[float | None] = mapped_column(Float, comment='Reserved field 1')
    blank_2: Mapped[float | None] = mapped_column(Float, comment='Reserved field 2')
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )

    # Relationships
    cop_curve_obj: Mapped[LibCurve | None] = relationship('LibCurve')
    product: Mapped[LibProduct | None] = relationship('LibProduct')


class Boiler(Base):
    """Boiler model."""

    __tablename__ = 'boiler'

    boiler_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Boiler ID'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='Boiler name')
    lib_boiler_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('lib_boiler.lib_boiler_id'), comment='Library boiler ID'
    )
    prime_pump: Mapped[int | None] = mapped_column(Integer, comment='Primary pump')
    second_pump: Mapped[int | None] = mapped_column(Integer, comment='Secondary pump')
    heatsource_pump: Mapped[int | None] = mapped_column(
        Integer, comment='Heat source pump'
    )
    heatexchanger: Mapped[int | None] = mapped_column(Integer, comment='Heat exchanger')
    priority: Mapped[int | None] = mapped_column(Integer, comment='Priority')
    blank_1: Mapped[float | None] = mapped_column(Float, comment='Reserved field 1')
    blank_2: Mapped[float | None] = mapped_column(Float, comment='Reserved field 2')
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )

    # Relationships
    lib_boiler: Mapped[LibBoiler | None] = relationship('LibBoiler')


class HeatingSystem(Base):
    """Heating system model."""

    __tablename__ = 'heating_system'

    heating_system_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Heating system ID'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='System name')
    type: Mapped[int | None] = mapped_column(Integer, comment='System type')
    supply_t_schedule: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('schedule_year.schedule_id'),
        comment='Supply temperature schedule',
    )
    radiator_area_mode: Mapped[int | None] = mapped_column(
        Integer, comment='Radiator area mode'
    )
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )

    # Relationships
    supply_t_schedule_obj: Mapped[ScheduleYear | None] = relationship('ScheduleYear')
    heating_pipes: Mapped[list[HeatingPipe]] = relationship(
        'HeatingPipe', back_populates='heating_system'
    )


class HeatingPipe(Base):
    """Heating pipe model."""

    __tablename__ = 'heating_pipe'

    heating_pipe_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Heating pipe ID'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='Pipe name')
    of_heating_system: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('heating_system.heating_system_id'),
        comment='Parent heating system',
    )
    flow_schedule: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('schedule_year.schedule_id'), comment='Flow schedule'
    )
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )

    # Relationships
    heating_system: Mapped[HeatingSystem | None] = relationship(
        'HeatingSystem', back_populates='heating_pipes'
    )
    flow_schedule_obj: Mapped[ScheduleYear | None] = relationship('ScheduleYear')
    rooms: Mapped[list[Room]] = relationship('Room', back_populates='heating_pipe')


class FanCoil(Base):
    """Fan coil unit model."""

    __tablename__ = 'fan_coil'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='ID')
    name: Mapped[str | None] = mapped_column(String(50), comment='Name')
    of_room: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('room.id'), comment='Parent room'
    )
    pos_x: Mapped[float | None] = mapped_column(Float, comment='X position')
    pos_y: Mapped[float | None] = mapped_column(Float, comment='Y position')
    pos_z: Mapped[float | None] = mapped_column(Float, comment='Z position')

    # Relationships
    room: Mapped[Room | None] = relationship('Room')


class LibPump(Base):
    """Pump library model."""

    __tablename__ = 'lib_pump'

    lib_pump_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Pump library ID'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='Pump name')
    type: Mapped[int | None] = mapped_column(Integer, comment='Pump type')
    flowrate: Mapped[float | None] = mapped_column(Float, comment='Flow rate (m³/h)')
    pressure: Mapped[float | None] = mapped_column(Float, comment='Pressure (kPa)')
    efficiency: Mapped[float | None] = mapped_column(Float, comment='Efficiency')
    gp_curve: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('lib_curve.lib_curve_id'), comment='G-P curve reference'
    )
    geff_curve: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('lib_curve.lib_curve_id'),
        comment='G-Efficiency curve reference',
    )
    speed_ratio_max: Mapped[float | None] = mapped_column(
        Float, comment='Maximum speed ratio'
    )
    speed_ratio_min: Mapped[float | None] = mapped_column(
        Float, comment='Minimum speed ratio'
    )
    product_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('lib_product.product_id'), comment='Product ID'
    )
    blank_1: Mapped[float | None] = mapped_column(Float, comment='Reserved field 1')
    blank_2: Mapped[float | None] = mapped_column(Float, comment='Reserved field 2')
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )

    # Relationships
    gp_curve_obj: Mapped[LibCurve | None] = relationship(
        'LibCurve', foreign_keys=[gp_curve]
    )
    geff_curve_obj: Mapped[LibCurve | None] = relationship(
        'LibCurve', foreign_keys=[geff_curve]
    )
    product: Mapped[LibProduct | None] = relationship('LibProduct')


class LibCoolingtower(Base):
    """Cooling tower library model."""

    __tablename__ = 'lib_coolingtower'

    lib_coolingtower_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Cooling tower library ID'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='Cooling tower name')
    type: Mapped[int | None] = mapped_column(Integer, comment='Cooling tower type')
    capacity: Mapped[float | None] = mapped_column(Float, comment='Capacity (kW)')
    flowrate: Mapped[float | None] = mapped_column(Float, comment='Flow rate (m³/h)')
    pressure_loss: Mapped[float | None] = mapped_column(
        Float, comment='Pressure loss (kPa)'
    )
    supply_temperature: Mapped[float | None] = mapped_column(
        Float, comment='Supply temperature (°C)'
    )
    return_temperature: Mapped[float | None] = mapped_column(
        Float, comment='Return temperature (°C)'
    )
    air_wetbulb_temperature: Mapped[float | None] = mapped_column(
        Float, comment='Air wet bulb temperature (°C)'
    )
    air_flowrate: Mapped[float | None] = mapped_column(
        Float, comment='Air flow rate (m³/h)'
    )
    fan_power: Mapped[float | None] = mapped_column(Float, comment='Fan power (kW)')
    refill_flowrate: Mapped[float | None] = mapped_column(
        Float, comment='Refill flow rate (m³/h)'
    )
    betaf: Mapped[float | None] = mapped_column(Float, comment='Beta factor')
    product_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('lib_product.product_id'), comment='Product ID'
    )
    blank_1: Mapped[float | None] = mapped_column(Float, comment='Reserved field 1')
    blank_2: Mapped[float | None] = mapped_column(Float, comment='Reserved field 2')
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )

    # Relationships
    product: Mapped[LibProduct | None] = relationship('LibProduct')


class CoolingTower(Base):
    """Cooling tower model."""

    __tablename__ = 'cooling_tower'

    tower_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Cooling tower ID'
    )
    of_cps: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('cps.cps_id'), comment='Parent CPS'
    )
    product_id: Mapped[int | None] = mapped_column(Integer, comment='Product ID')

    # Relationships
    cps: Mapped[Cps | None] = relationship('Cps')


class Coolingtower(Base):
    """Cooling tower model (alias table)."""

    __tablename__ = 'coolingtower'

    coolingtower_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Cooling tower ID'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='Cooling tower name')
    lib_coolingtower_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('lib_coolingtower.lib_coolingtower_id'),
        comment='Cooling tower library ID',
    )
    attribute_to: Mapped[int | None] = mapped_column(Integer)
    blank_1: Mapped[float | None] = mapped_column(Numeric)
    blank_2: Mapped[float | None] = mapped_column(Numeric)
    cooling_pump: Mapped[int | None] = mapped_column(Integer)
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )
    priority: Mapped[int | None] = mapped_column(Integer)
    refill_pump: Mapped[int | None] = mapped_column(Integer)

    # Relationships
    lib_coolingtower: Mapped[LibCoolingtower | None] = relationship('LibCoolingtower')


class Cps(Base):
    """Cooling and heating plant station model."""

    __tablename__ = 'cps'

    cps_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Plant station ID'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='Station name')
    water_sys: Mapped[int | None] = mapped_column(Integer)


class LibHeatexchanger(Base):
    """Heat exchanger library model."""

    __tablename__ = 'lib_heatexchanger'

    lib_heatexchanger_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Heat exchanger library ID'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='Name')
    type: Mapped[int | None] = mapped_column(Integer, comment='Type')
    capacity: Mapped[float | None] = mapped_column(Float, comment='Capacity')
    ex_area: Mapped[float | None] = mapped_column(Float, comment='Heat exchange area')
    k: Mapped[float | None] = mapped_column(
        Float, comment='Rated heat transfer coefficient'
    )
    k_curve: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('lib_curve.lib_curve_id'),
        comment='Heat transfer coefficient curve',
    )
    flowrate1: Mapped[float | None] = mapped_column(
        Float, comment='Primary side flow rate'
    )
    pressure_loss1: Mapped[float | None] = mapped_column(
        Float, comment='Primary side pressure loss'
    )
    tin1: Mapped[float | None] = mapped_column(
        Float, comment='Primary side inlet temperature'
    )
    tout1: Mapped[float | None] = mapped_column(
        Float, comment='Primary side outlet temperature'
    )
    flowrate2: Mapped[float | None] = mapped_column(
        Float, comment='Secondary side flow rate'
    )
    pressure_loss2: Mapped[float | None] = mapped_column(
        Float, comment='Secondary side pressure loss'
    )
    tin2: Mapped[float | None] = mapped_column(
        Float, comment='Secondary side inlet temperature'
    )
    tout2: Mapped[float | None] = mapped_column(
        Float, comment='Secondary side outlet temperature'
    )
    product_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('lib_product.product_id'), comment='Product ID'
    )
    blank_1: Mapped[float | None] = mapped_column(Float, comment='Reserved field 1')
    blank_2: Mapped[float | None] = mapped_column(Float, comment='Reserved field 2')
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )

    # Relationships
    k_curve_obj: Mapped[LibCurve | None] = relationship('LibCurve')
    product: Mapped[LibProduct | None] = relationship('LibProduct')


class Heatexchanger(Base):
    """Heat exchanger model."""

    __tablename__ = 'heatexchanger'

    heatexchanger_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Heat exchanger ID'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='Name')
    lib_heatexchanger_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('lib_heatexchanger.lib_heatexchanger_id'),
        comment='Heat exchanger library ID',
    )
    prime_pump: Mapped[int | None] = mapped_column(Integer, comment='Primary pump')
    second_pump: Mapped[int | None] = mapped_column(Integer, comment='Secondary pump')
    attribute_to: Mapped[int | None] = mapped_column(Integer, comment='Attribute to')
    priority: Mapped[int | None] = mapped_column(Integer, comment='Priority')
    blank_1: Mapped[int | None] = mapped_column(Integer, comment='Reserved field 1')
    blank_2: Mapped[int | None] = mapped_column(Integer, comment='Reserved field 2')
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )

    # Relationships
    lib_heatexchanger: Mapped[LibHeatexchanger | None] = relationship(
        'LibHeatexchanger'
    )


# VRV system models
class LibVrvTerminalV1(Base):
    """VRV terminal library V1 model."""

    __tablename__ = 'lib_vrv_terminal_v1'

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='VRV terminal library ID'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='Name')
    capacity_cool: Mapped[float | None] = mapped_column(Float)
    capacity_heat: Mapped[float | None] = mapped_column(Float)
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )
    fai_gas: Mapped[float | None] = mapped_column(Float)
    fai_liquid: Mapped[float | None] = mapped_column(Float)
    fan_flow_high: Mapped[float | None] = mapped_column(Float)
    fan_flow_low: Mapped[float | None] = mapped_column(Float)
    fan_power: Mapped[float | None] = mapped_column(Float)
    manufacturer: Mapped[str | None] = mapped_column(String(50))
    type: Mapped[str | None] = mapped_column(String(50))


class LibVrvSource(Base):
    """VRV outdoor unit library model."""

    __tablename__ = 'lib_vrv_source'

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='VRV outdoor unit library ID'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='Name')
    alpha_1: Mapped[float | None] = mapped_column(Float)
    alpha_2: Mapped[float | None] = mapped_column(Float)
    capacity_cool: Mapped[float | None] = mapped_column(Float)
    capacity_heat: Mapped[float | None] = mapped_column(Float)
    ext_property: Mapped[float | None] = mapped_column(
        Float, comment='Extended property'
    )
    fai_gas: Mapped[float | None] = mapped_column(Float)
    fai_liquid: Mapped[float | None] = mapped_column(Float)
    fan_power_a: Mapped[float | None] = mapped_column(Float)
    fan_power_b: Mapped[float | None] = mapped_column(Float)
    fan_power_c: Mapped[float | None] = mapped_column(Float)
    fan_power_d: Mapped[float | None] = mapped_column(Float)
    fan_power_e: Mapped[float | None] = mapped_column(Float)
    fan_power_f: Mapped[float | None] = mapped_column(Float)
    fan_power_nom: Mapped[float | None] = mapped_column(Float)
    flowrate: Mapped[float | None] = mapped_column(Float)
    h_cppower_a: Mapped[float | None] = mapped_column(Float)
    h_cppower_b: Mapped[float | None] = mapped_column(Float)
    h_cppower_c: Mapped[float | None] = mapped_column(Float)
    h_cppower_d: Mapped[float | None] = mapped_column(Float)
    h_cppower_e: Mapped[float | None] = mapped_column(Float)
    h_cppower_f: Mapped[float | None] = mapped_column(Float)
    l_cppower_a: Mapped[float | None] = mapped_column(Float)
    l_cppower_b: Mapped[float | None] = mapped_column(Float)
    l_cppower_c: Mapped[float | None] = mapped_column(Float)
    l_cppower_d: Mapped[float | None] = mapped_column(Float)
    l_cppower_e: Mapped[float | None] = mapped_column(Float)
    l_cppower_f: Mapped[float | None] = mapped_column(Float)
    manufacturer: Mapped[str | None] = mapped_column(String(100))
    nom_air_flow: Mapped[float | None] = mapped_column(Float)
    nom_ref_flow: Mapped[float | None] = mapped_column(Float)
    plr_lowlimit: Mapped[float | None] = mapped_column(Float)
    power_comp_cool: Mapped[float | None] = mapped_column(Float)
    power_cool: Mapped[float | None] = mapped_column(Float)
    power_heat: Mapped[float | None] = mapped_column(Float)
    power_loss: Mapped[float | None] = mapped_column(Float)
    r_air: Mapped[float | None] = mapped_column(Float)
    r_ref: Mapped[float | None] = mapped_column(Float)
    sweptvolume: Mapped[float | None] = mapped_column(Float)
    type: Mapped[str | None] = mapped_column(String(100))


class LibVrvSourceV1(Base):
    """VRV outdoor unit library V1 model."""

    __tablename__ = 'lib_vrv_source_v1'

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='VRV outdoor unit library V1 ID'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='Name')
    capacity_cool: Mapped[float | None] = mapped_column(Float)
    capacity_heat: Mapped[float | None] = mapped_column(Float)
    c_cppower_a: Mapped[float | None] = mapped_column(Float)
    c_cppower_b: Mapped[float | None] = mapped_column(Float)
    c_cppower_c: Mapped[float | None] = mapped_column(Float)
    c_cppower_d: Mapped[float | None] = mapped_column(Float)
    c_cppower_e: Mapped[float | None] = mapped_column(Float)
    c_cppower_f: Mapped[float | None] = mapped_column(Float)
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )
    fai_gas: Mapped[float | None] = mapped_column(Float)
    fai_liquid: Mapped[float | None] = mapped_column(Float)
    fan_power_a: Mapped[float | None] = mapped_column(Float)
    fan_power_b: Mapped[float | None] = mapped_column(Float)
    fan_power_c: Mapped[float | None] = mapped_column(Float)
    fan_power_d: Mapped[float | None] = mapped_column(Float)
    fan_power_e: Mapped[float | None] = mapped_column(Float)
    fan_power_f: Mapped[float | None] = mapped_column(Float)
    fan_power_nom: Mapped[float | None] = mapped_column(Float)
    flowrate: Mapped[float | None] = mapped_column(Float)
    h_cppower_a: Mapped[float | None] = mapped_column(Float)
    h_cppower_b: Mapped[float | None] = mapped_column(Float)
    h_cppower_c: Mapped[float | None] = mapped_column(Float)
    h_cppower_d: Mapped[float | None] = mapped_column(Float)
    h_cppower_e: Mapped[float | None] = mapped_column(Float)
    h_cppower_f: Mapped[float | None] = mapped_column(Float)
    manufacturer: Mapped[str | None] = mapped_column(String(100))
    nom_air_flow: Mapped[float | None] = mapped_column(Float)
    nom_ref_flow: Mapped[float | None] = mapped_column(Float)
    plr_lowlimit: Mapped[float | None] = mapped_column(Float)
    power_comp_cool: Mapped[float | None] = mapped_column(Float)
    power_comp_heat: Mapped[float | None] = mapped_column(Float)
    power_cool: Mapped[float | None] = mapped_column(Float)
    power_heat: Mapped[float | None] = mapped_column(Float)
    type: Mapped[str | None] = mapped_column(String(100))


class LibVrvTerminal(Base):
    """VRV terminal library model."""

    __tablename__ = 'lib_vrv_terminal'

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='VRV terminal library ID'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='Name')
    capacity_cool: Mapped[float | None] = mapped_column(Float)
    capacity_heat: Mapped[float | None] = mapped_column(Float)
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )
    fai_gas: Mapped[float | None] = mapped_column(Float)
    fai_liquid: Mapped[float | None] = mapped_column(Float)
    fan_flow_high: Mapped[float | None] = mapped_column(Float)
    fan_flow_low: Mapped[float | None] = mapped_column(Float)
    fan_power: Mapped[float | None] = mapped_column(Float)
    manufacturer: Mapped[str | None] = mapped_column(String(50))
    r_air: Mapped[float | None] = mapped_column(Float)
    r_ref: Mapped[float | None] = mapped_column(Float)
    type: Mapped[str | None] = mapped_column(String(50))


# Duct system models
class Duct(Base):
    """Duct model."""

    __tablename__ = 'duct'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Duct ID')
    name: Mapped[str | None] = mapped_column(String(50), comment='Duct name')
    of_ac_sys: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('ac_sys.ac_sys_id'), comment='Parent AC system'
    )
    width: Mapped[float | None] = mapped_column(Float, comment='Duct width')
    height: Mapped[float | None] = mapped_column(Float, comment='Duct height')
    start: Mapped[int | None] = mapped_column(Integer, comment='Start node')
    end: Mapped[int | None] = mapped_column(Integer, comment='End node')

    # Relationships
    ac_sys: Mapped[AcSys | None] = relationship('AcSys')


class DuctJoint(Base):
    """Duct joint model."""

    __tablename__ = 'duct_joint'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Joint ID')
    type: Mapped[str | None] = mapped_column(String(50), comment='Joint type')
    name: Mapped[str | None] = mapped_column(String(50), comment='Joint name')
    pos_x: Mapped[float | None] = mapped_column(Float, comment='X position')
    pos_y: Mapped[float | None] = mapped_column(Float, comment='Y position')
    pos_z: Mapped[float | None] = mapped_column(Float, comment='Z position')


class DnFcu(Base):
    """DN fan coil unit model."""

    __tablename__ = 'dn_fcu'

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Fan coil unit ID'
    )
    area: Mapped[float | None] = mapped_column(Float)
    flow_rate: Mapped[float | None] = mapped_column(Float)
    flow_type: Mapped[int | None] = mapped_column(Integer, comment='Flow type')
    ksai: Mapped[float | None] = mapped_column(Float)
    point_id: Mapped[int | None] = mapped_column(Integer)
    room_id: Mapped[int | None] = mapped_column(Integer)


class DnAhu(Base):
    """DN air handling unit model."""

    __tablename__ = 'dn_ahu'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='AHU ID')
    flow_rate: Mapped[float | None] = mapped_column(Float)
    point_id: Mapped[int | None] = mapped_column(Integer)


class DnDuct(Base):
    """DN duct model."""

    __tablename__ = 'dn_duct'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Duct ID')
    color: Mapped[int | None] = mapped_column(Integer)
    end_point_id: Mapped[int | None] = mapped_column(Integer, comment='End point ID')
    flow_rate: Mapped[float | None] = mapped_column(Float)
    high: Mapped[float | None] = mapped_column(Float)
    is_given_dimension: Mapped[int | None] = mapped_column(SmallInteger)
    is_given_s: Mapped[int | None] = mapped_column(SmallInteger)
    line_type: Mapped[str | None] = mapped_column(String(50))
    of_building: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('building.building_id'), comment='Parent building'
    )
    s: Mapped[float | None] = mapped_column(Float)
    start_point_id: Mapped[int | None] = mapped_column(
        Integer, comment='Start point ID'
    )
    width: Mapped[float | None] = mapped_column(Float)

    # Relationships
    building: Mapped[Building | None] = relationship('Building')


# HACNET system models
class HacnetSubnet(Base):
    """HACNET subnet model."""

    __tablename__ = 'hacnet_subnet'

    subnet_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Subnet ID'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='Subnet name')
    backcolor: Mapped[int | None] = mapped_column(Integer)
    big_user: Mapped[int | None] = mapped_column(Integer)
    bkusebmp: Mapped[bool | None] = mapped_column(Boolean)
    bmpfile: Mapped[str | None] = mapped_column(String(255))
    dblzoomratio: Mapped[float | None] = mapped_column(Float)
    nprintsx: Mapped[int | None] = mapped_column(Integer)
    of_water_sys: Mapped[int | None] = mapped_column(Integer)
    scale: Mapped[float | None] = mapped_column(Float)
    start_node: Mapped[int | None] = mapped_column(Integer)
    szviewx: Mapped[int | None] = mapped_column(Integer)
    szviewy: Mapped[int | None] = mapped_column(Integer)


class HacnetNet(Base):
    """HACNET network model."""

    __tablename__ = 'hacnet_net'

    net_id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Network ID')
    active_subnet: Mapped[int | None] = mapped_column(Integer)
    baftercal: Mapped[bool | None] = mapped_column(Boolean)
    bdhcmode: Mapped[bool | None] = mapped_column(Boolean)
    dblflowtoarea: Mapped[float | None] = mapped_column(Float)
    dblheatcalfactor: Mapped[float | None] = mapped_column(Float)
    dblqtoarea: Mapped[float | None] = mapped_column(Float)
    precision: Mapped[float | None] = mapped_column(Float)
    single_line_net: Mapped[bool | None] = mapped_column(Boolean)
    sversion: Mapped[str | None] = mapped_column(String(50))


class HacnetNode(Base):
    """HACNET node model."""

    __tablename__ = 'hacnet_node'

    node_id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Node ID')
    name: Mapped[str | None] = mapped_column(String(50), comment='Name')
    x: Mapped[float | None] = mapped_column(Float, comment='X coordinate')
    y: Mapped[float | None] = mapped_column(Float, comment='Y coordinate')
    z: Mapped[float | None] = mapped_column(Float, comment='Z coordinate')
    lose_flow: Mapped[float | None] = mapped_column(Float, comment='Loss flow')
    pressure: Mapped[float | None] = mapped_column(Float, comment='Pressure')
    temperature: Mapped[float | None] = mapped_column(Float, comment='Temperature')
    of_subnet: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('hacnet_subnet.subnet_id'), comment='Parent subnet'
    )
    big_user: Mapped[int | None] = mapped_column(Integer, comment='Big user')
    static_point: Mapped[bool] = mapped_column(
        Boolean, default=False, comment='Static point'
    )
    b_font_show: Mapped[bool] = mapped_column(
        'bFontShow', Boolean, default=False, comment='Font display'
    )

    # Relationships
    subnet: Mapped[HacnetSubnet | None] = relationship('HacnetSubnet')


class HacnetBranch(Base):
    """HACNET branch model."""

    __tablename__ = 'hacnet_branch'

    branch_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Branch ID'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='Branch name')
    type: Mapped[int | None] = mapped_column(Integer, comment='Branch type')
    of_subnet: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('hacnet_subnet.subnet_id'), comment='Parent subnet'
    )
    start_node: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('hacnet_node.node_id'), comment='Start node'
    )
    end_node: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('hacnet_node.node_id'), comment='End node'
    )
    s: Mapped[float | None] = mapped_column(Float, comment='S parameter')
    length: Mapped[float | None] = mapped_column(Float, comment='Length')
    diameter: Mapped[int | None] = mapped_column(Integer, comment='Diameter')
    roughness: Mapped[float | None] = mapped_column(Float, comment='Roughness')
    flow: Mapped[float | None] = mapped_column(Float, comment='Flow')
    yczlinputdirect: Mapped[bool | None] = mapped_column(
        Boolean, default=False, comment='Direct resistance input'
    )
    yczlxishu: Mapped[float | None] = mapped_column(
        Float, comment='Resistance coefficient'
    )
    jzstyle: Mapped[int | None] = mapped_column(
        Integer, comment='Local resistance style'
    )
    jztodynhead: Mapped[float | None] = mapped_column(
        Float, comment='Local resistance to dynamic head'
    )
    jztoyc: Mapped[float | None] = mapped_column(
        Float, comment='Local resistance to remaining'
    )
    bfontshow: Mapped[bool | None] = mapped_column(
        Boolean, default=False, comment='Font display'
    )

    # Relationships
    subnet: Mapped[HacnetSubnet | None] = relationship('HacnetSubnet')
    start_node_ref: Mapped[HacnetNode | None] = relationship(
        'HacnetNode', foreign_keys=[start_node]
    )
    end_node_ref: Mapped[HacnetNode | None] = relationship(
        'HacnetNode', foreign_keys=[end_node]
    )


class HacnetBranchPoint(Base):
    """HACNET branch point model."""

    __tablename__ = 'hacnet_branch_point'

    point_id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Point ID')
    of_branch: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('hacnet_branch.branch_id'), comment='Parent branch'
    )
    of_branchline: Mapped[int | None] = mapped_column(
        Integer, comment='Parent branch line'
    )
    x: Mapped[float | None] = mapped_column(Float, comment='X coordinate')
    y: Mapped[float | None] = mapped_column(Float, comment='Y coordinate')

    # Relationships
    branch: Mapped[HacnetBranch | None] = relationship('HacnetBranch')


class HacnetLandafai(Base):
    """HACNET Landafai model."""

    __tablename__ = 'hacnet_landafai'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    index: Mapped[int | None] = mapped_column(Integer)
    landa: Mapped[float | None] = mapped_column(Float)
    fai: Mapped[float | None] = mapped_column(Float)
    terminal_id: Mapped[int | None] = mapped_column(Integer, comment='Terminal ID')


class HacnetTerminal(Base):
    """HACNET terminal model."""

    __tablename__ = 'hacnet_terminal'

    terminal_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Terminal ID'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='Name')
    type: Mapped[int | None] = mapped_column(Integer, comment='Branch type')
    bdirect: Mapped[bool | None] = mapped_column(Boolean)
    dblheatarea: Mapped[float | None] = mapped_column(Float)
    dblqtoarea: Mapped[float | None] = mapped_column(Float)
    dblsecondaveflow: Mapped[float | None] = mapped_column(Float)
    dblstationheatarea: Mapped[float | None] = mapped_column(Float)
    dblsteadyheatcalfactor: Mapped[float | None] = mapped_column(Float)
    design_flow: Mapped[float | None] = mapped_column(Float, comment='Design flow')
    design_pressuredrop: Mapped[float | None] = mapped_column(
        Float, comment='Design pressure drop'
    )
    of_branch: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('hacnet_branch.branch_id'), comment='Parent branch'
    )
    of_branchline: Mapped[int | None] = mapped_column(
        Integer, comment='Parent branch line'
    )
    of_room: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('room.id'), comment='Room ID'
    )
    of_subnet: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('hacnet_subnet.subnet_id'), comment='Parent subnet'
    )
    ratio_in_branchline: Mapped[float | None] = mapped_column(
        Float, comment='Ratio in branch line'
    )
    s: Mapped[float | None] = mapped_column(Float, comment='S parameter')

    # Relationships
    branch: Mapped[HacnetBranch | None] = relationship('HacnetBranch')
    subnet: Mapped[HacnetSubnet | None] = relationship('HacnetSubnet')
    room: Mapped[Room | None] = relationship('Room')


class HacnetPump(Base):
    """HACNET pump model."""

    __tablename__ = 'hacnet_pump'

    pump_id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Pump ID')
    name: Mapped[str | None] = mapped_column(String(50), comment='Name')
    a: Mapped[float | None] = mapped_column(Float)
    b: Mapped[float | None] = mapped_column(Float)
    c: Mapped[float | None] = mapped_column(Float)
    d: Mapped[float | None] = mapped_column(Float)
    bmain: Mapped[bool | None] = mapped_column(Boolean)
    countodtitle: Mapped[int | None] = mapped_column(Integer)
    dblflow: Mapped[float | None] = mapped_column(Float)
    of_branch: Mapped[int | None] = mapped_column(Integer)
    of_branchline: Mapped[int | None] = mapped_column(Integer)
    of_subnet: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('hacnet_subnet.subnet_id'), comment='Parent subnet'
    )
    of_water_sys: Mapped[int | None] = mapped_column(Integer)
    product_id: Mapped[int | None] = mapped_column(Integer)
    provide_id: Mapped[int | None] = mapped_column(Integer)
    ratioinbranchline: Mapped[float | None] = mapped_column(Float)
    realspeed: Mapped[int | None] = mapped_column(Integer)
    standspeed: Mapped[int | None] = mapped_column(Integer)

    # Relationships
    subnet: Mapped[HacnetSubnet | None] = relationship('HacnetSubnet')


class HacnetValve(Base):
    """HACNET valve model."""

    __tablename__ = 'hacnet_valve'

    valve_id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Valve ID')
    jzxishu: Mapped[float | None] = mapped_column(Float)
    name: Mapped[str | None] = mapped_column(String(50), comment='Name')
    of_branch: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('hacnet_branch.branch_id'), comment='Parent branch'
    )
    of_branchline: Mapped[int | None] = mapped_column(Integer)
    of_subnet: Mapped[int | None] = mapped_column(Integer)
    openwide: Mapped[int | None] = mapped_column(Integer)
    product_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('lib_product.product_id'), comment='Product ID'
    )
    ratioinbranchline: Mapped[float | None] = mapped_column(Float)
    zuliofopenvalve: Mapped[float | None] = mapped_column(Float)

    # Relationships
    product: Mapped[LibProduct | None] = relationship('LibProduct')
    branch: Mapped[HacnetBranch | None] = relationship('HacnetBranch')


class HacnetWpgnode(Base):
    """HACNET WPG node model."""

    __tablename__ = 'hacnet_wpgnode'

    wpgnode_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='WPG node ID'
    )
    indexinnodes: Mapped[int | None] = mapped_column(Integer)
    of_subnet: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('hacnet_subnet.subnet_id'), comment='Parent subnet'
    )
    pressure: Mapped[float | None] = mapped_column(Float)
    wpgname: Mapped[str | None] = mapped_column(String(50))

    # Relationships
    subnet: Mapped[HacnetSubnet | None] = relationship('HacnetSubnet')


class HacnetText(Base):
    """HACNET text model."""

    __tablename__ = 'hacnet_text'

    text_id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Text ID')
    color: Mapped[int | None] = mapped_column(Integer)
    kind: Mapped[int | None] = mapped_column(Integer)
    lfescapement: Mapped[int | None] = mapped_column(Integer)
    lffacename: Mapped[str | None] = mapped_column(String(50))
    lfheight: Mapped[int | None] = mapped_column(Integer)
    lforientation: Mapped[int | None] = mapped_column(Integer)
    lfweight: Mapped[int | None] = mapped_column(Integer)
    lfwidth: Mapped[int | None] = mapped_column(Integer)
    of_subnet: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('hacnet_subnet.subnet_id'), comment='Parent subnet'
    )
    show: Mapped[bool | None] = mapped_column(Boolean)
    text: Mapped[str | None] = mapped_column(String(255), comment='Text content')
    x: Mapped[int | None] = mapped_column(Integer)
    y: Mapped[int | None] = mapped_column(Integer)

    # Relationships
    subnet: Mapped[HacnetSubnet | None] = relationship('HacnetSubnet')


# PN system models
class PnPoint(Base):
    """PN point model."""

    __tablename__ = 'pn_point'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='PN point ID')
    x: Mapped[float | None] = mapped_column(Float, comment='X coordinate')
    y: Mapped[float | None] = mapped_column(Float, comment='Y coordinate')
    storey_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('storey.id'), comment='Storey ID'
    )


class PnPipe(Base):
    """PN pipe model."""

    __tablename__ = 'pn_pipe'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='PN pipe ID')
    color: Mapped[int | None] = mapped_column(Integer, comment='Color')
    d: Mapped[int | None] = mapped_column(SmallInteger, comment='Diameter')
    end_point_id: Mapped[int | None] = mapped_column(Integer, comment='End point ID')
    flow_rate: Mapped[float | None] = mapped_column(Float, comment='Flow rate')
    is_given_dimension: Mapped[int | None] = mapped_column(
        SmallInteger, comment='Is given dimension'
    )
    is_given_s: Mapped[int | None] = mapped_column(SmallInteger, comment='Is given S')
    line_type: Mapped[str | None] = mapped_column(String(50), comment='Line type')
    s: Mapped[float | None] = mapped_column(Float, comment='S value')
    start_point_id: Mapped[int | None] = mapped_column(
        Integer, comment='Start point ID'
    )


class PnValve(Base):
    """PN valve model."""

    __tablename__ = 'pn_valve'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='ID')
    length_fact: Mapped[float | None] = mapped_column(Float, comment='Length factor')
    open_fact: Mapped[int | None] = mapped_column(Integer, comment='Opening factor')
    resist_fact: Mapped[float | None] = mapped_column(
        Float, comment='Resistance factor'
    )
    pipe_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('pn_pipe.id'), comment='Pipe ID'
    )

    # Relationships
    pipe: Mapped[PnPipe | None] = relationship('PnPipe')


class WaterSys(Base):
    """Water system model."""

    __tablename__ = 'water_sys'

    water_sys_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Water system ID'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='Name')
    static_node_id: Mapped[int | None] = mapped_column(
        Integer, comment='Static node ID'
    )
    activated_net: Mapped[int | None] = mapped_column(
        Integer, comment='Activated network'
    )


class EnergyPumpFan(Base):
    """Energy pump and fan model."""

    __tablename__ = 'energy_pump_fan'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='ID')
    name: Mapped[str | None] = mapped_column(String(50), comment='Name')
    count: Mapped[int | None] = mapped_column(Integer)
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )
    flowrate: Mapped[float | None] = mapped_column(Float)
    inverter: Mapped[float | None] = mapped_column(Float)
    mode: Mapped[int | None] = mapped_column(Integer)
    pressure: Mapped[float | None] = mapped_column(Float)
    ratio: Mapped[float | None] = mapped_column(Float)
    schedule: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('schedule_year.schedule_id'), comment='Schedule'
    )

    # Relationships
    schedule_obj: Mapped[ScheduleYear | None] = relationship('ScheduleYear')


class AirSupplyPort(Base):
    """Air supply port model."""

    __tablename__ = 'air_supply_port'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='ID')
    name: Mapped[str | None] = mapped_column(String(50), comment='Name')
    of_room: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('room.id'), comment='Parent room'
    )
    of_duct_terminal: Mapped[int | None] = mapped_column(
        Integer, comment='Duct terminal ID'
    )
    pos_x: Mapped[float | None] = mapped_column(Float, comment='X position')
    pos_y: Mapped[float | None] = mapped_column(Float, comment='Y position')
    pos_z: Mapped[float | None] = mapped_column(Float, comment='Z position')
    resis_coef: Mapped[float | None] = mapped_column(
        Numeric, comment='Resistance coefficient'
    )
    need_resis_coef: Mapped[float | None] = mapped_column(
        Numeric, comment='Required resistance coefficient'
    )

    # Relationships
    room: Mapped[Room | None] = relationship('Room')


class ChillerPump(Base):
    """Chiller pump model."""

    __tablename__ = 'chiller_pump'

    pump_id: Mapped[str] = mapped_column(
        String(50), primary_key=True, comment='Pump ID'
    )
    of_chiller: Mapped[str | None] = mapped_column(String(50), comment='Parent chiller')
    product_id: Mapped[str | None] = mapped_column(String(50), comment='Product ID')


class CoolingTowerPump(Base):
    """Cooling tower pump model."""

    __tablename__ = 'cooling_tower_pump'

    pump_id: Mapped[str] = mapped_column(
        String(50), primary_key=True, comment='Pump ID'
    )
    of_tower: Mapped[str | None] = mapped_column(
        String(50), comment='Parent cooling tower'
    )
    product_id: Mapped[str | None] = mapped_column(String(50), comment='Product ID')


class Ductnet(Base):
    """Duct network model."""

    __tablename__ = 'ductnet'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='ID')
    name: Mapped[str | None] = mapped_column(String(50), comment='Name')
    ahu_type: Mapped[int | None] = mapped_column(SmallInteger, comment='AHU type')
    run_mode: Mapped[int | None] = mapped_column(SmallInteger, comment='Run mode')
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )
    s_fan: Mapped[int | None] = mapped_column(Integer, comment='Supply fan')
    f_fan: Mapped[int | None] = mapped_column(Integer, comment='Fresh air fan')
    e_fan: Mapped[int | None] = mapped_column(Integer, comment='Exhaust fan')
    r_fan: Mapped[int | None] = mapped_column(Integer, comment='Return fan')

    # Fresh duct dimensions (L/W/H)
    fresh_duct_l: Mapped[float | None] = mapped_column(
        Float, comment='Fresh duct length'
    )
    fresh_duct_w: Mapped[float | None] = mapped_column(
        Float, comment='Fresh duct width'
    )
    fresh_duct_h: Mapped[float | None] = mapped_column(
        Float, comment='Fresh duct height'
    )

    # Exhaust duct dimensions (L/W/H)
    exhaust_duct_l: Mapped[float | None] = mapped_column(
        Float, comment='Exhaust duct length'
    )
    exhaust_duct_w: Mapped[float | None] = mapped_column(
        Float, comment='Exhaust duct width'
    )
    exhaust_duct_h: Mapped[float | None] = mapped_column(
        Float, comment='Exhaust duct height'
    )

    # Elbow numbers (S/F/E/R)
    s_elbow_number: Mapped[int | None] = mapped_column(
        SmallInteger, comment='Supply elbow number'
    )
    f_elbow_number: Mapped[int | None] = mapped_column(
        SmallInteger, comment='Fresh elbow number'
    )
    e_elbow_number: Mapped[int | None] = mapped_column(
        SmallInteger, comment='Exhaust elbow number'
    )
    r_elbow_number: Mapped[int | None] = mapped_column(
        SmallInteger, comment='Return elbow number'
    )

    # Elbow Ksai values (S/F/E/R)
    s_elbow_ksai: Mapped[float | None] = mapped_column(
        Float, comment='Supply elbow Ksai'
    )
    f_elbow_ksai: Mapped[float | None] = mapped_column(
        Float, comment='Fresh elbow Ksai'
    )
    e_elbow_ksai: Mapped[float | None] = mapped_column(
        Float, comment='Exhaust elbow Ksai'
    )
    r_elbow_ksai: Mapped[float | None] = mapped_column(
        Float, comment='Return elbow Ksai'
    )

    # Muffler numbers (S/F/E/R)
    s_muffler_number: Mapped[int | None] = mapped_column(
        SmallInteger, comment='Supply muffler number'
    )
    f_muffler_number: Mapped[int | None] = mapped_column(
        SmallInteger, comment='Fresh muffler number'
    )
    e_muffler_number: Mapped[int | None] = mapped_column(
        SmallInteger, comment='Exhaust muffler number'
    )
    r_muffler_number: Mapped[int | None] = mapped_column(
        SmallInteger, comment='Return muffler number'
    )

    # Muffler Ksai values (S/F/E/R)
    s_muffler_ksai: Mapped[float | None] = mapped_column(
        Float, comment='Supply muffler Ksai'
    )
    f_muffler_ksai: Mapped[float | None] = mapped_column(
        Float, comment='Fresh muffler Ksai'
    )
    e_muffler_ksai: Mapped[float | None] = mapped_column(
        Float, comment='Exhaust muffler Ksai'
    )
    r_muffler_ksai: Mapped[float | None] = mapped_column(
        Float, comment='Return muffler Ksai'
    )

    # Filter G/P
    filter_g: Mapped[float | None] = mapped_column(Float, comment='Filter G')
    filter_p: Mapped[float | None] = mapped_column(Float, comment='Filter P')

    # Coil G/P
    coil_g: Mapped[float | None] = mapped_column(Float, comment='Coil G')
    coil_p: Mapped[float | None] = mapped_column(Float, comment='Coil P')

    # Spray room G/P
    sprayroom_g: Mapped[float | None] = mapped_column(Float, comment='Spray room G')
    sprayroom_p: Mapped[float | None] = mapped_column(Float, comment='Spray room P')

    # Recover heat G/P
    recoverheat_g: Mapped[float | None] = mapped_column(Float, comment='Recover heat G')
    recoverheat_p: Mapped[float | None] = mapped_column(Float, comment='Recover heat P')

    # Reheater G/P
    reheater_g: Mapped[float | None] = mapped_column(Float, comment='Reheater G')
    reheater_p: Mapped[float | None] = mapped_column(Float, comment='Reheater P')

    constant_p_point_value: Mapped[float | None] = mapped_column(
        Float, comment='Constant pressure point value'
    )


class DuctTerminal(Base):
    """Duct terminal model."""

    __tablename__ = 'duct_terminal'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='ID')
    name: Mapped[str | None] = mapped_column(String(50), comment='Name')
    pos_x: Mapped[float | None] = mapped_column(Float, comment='X position')
    pos_y: Mapped[float | None] = mapped_column(Float, comment='Y position')
    pos_z: Mapped[float | None] = mapped_column(Float, comment='Z position')
    resis_coef: Mapped[float | None] = mapped_column(
        Numeric, comment='Resistance coefficient'
    )


class Fan(Base):
    """Fan model."""

    __tablename__ = 'fan'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='ID')
    flowrate: Mapped[float | None] = mapped_column(Numeric, comment='Flow rate')
    pressure: Mapped[float | None] = mapped_column(Numeric, comment='Pressure')
    efficiency: Mapped[float | None] = mapped_column(Numeric, comment='Efficiency')
    curve_pf: Mapped[int | None] = mapped_column(Integer, comment='P-F curve')
    curve_ef: Mapped[int | None] = mapped_column(Integer, comment='E-F curve')
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )


class Pump(Base):
    """Pump model."""

    __tablename__ = 'pump'

    pump_id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Pump ID')
    name: Mapped[str | None] = mapped_column(String(50), comment='Name')
    usage: Mapped[int | None] = mapped_column(Integer, comment='Usage')
    lib_pump_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('lib_pump.lib_pump_id'), comment='Library pump ID'
    )
    attribute_to: Mapped[int | None] = mapped_column(Integer, comment='Attribute to')
    priority: Mapped[int | None] = mapped_column(Integer, comment='Priority')
    bypass: Mapped[int | None] = mapped_column(Integer, comment='Bypass')
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )
    blank_1: Mapped[float | None] = mapped_column(Numeric, comment='Reserved field 1')
    blank_2: Mapped[float | None] = mapped_column(Numeric, comment='Reserved field 2')

    # Relationships
    lib_pump: Mapped[LibPump | None] = relationship('LibPump')


class VrvSource(Base):
    """VRV outdoor unit model."""

    __tablename__ = 'vrv_source'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='ID')
    name: Mapped[str | None] = mapped_column(String(50), comment='Name')
    lib_id: Mapped[int | None] = mapped_column(Integer, comment='Library ID')
    x: Mapped[float | None] = mapped_column(Numeric, comment='X coordinate')
    y: Mapped[float | None] = mapped_column(Numeric, comment='Y coordinate')
    z: Mapped[float | None] = mapped_column(Numeric, comment='Z coordinate')
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )


class VrvTerminal(Base):
    """VRV indoor unit model."""

    __tablename__ = 'vrv_terminal'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='ID')
    name: Mapped[str | None] = mapped_column(String(50), comment='Name')
    lib_id: Mapped[int | None] = mapped_column(Integer, comment='Library ID')
    of_sys: Mapped[int | None] = mapped_column(Integer, comment='Parent system')
    of_sys_no: Mapped[int | None] = mapped_column(SmallInteger, comment='System number')
    of_room_group: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('room_group.room_group_id'), comment='Room group'
    )
    x: Mapped[float | None] = mapped_column(Float, comment='X coordinate')
    y: Mapped[float | None] = mapped_column(Float, comment='Y coordinate')
    z: Mapped[float | None] = mapped_column(Float, comment='Z coordinate')
    cx: Mapped[float | None] = mapped_column(Float, comment='CX coordinate')
    cy: Mapped[float | None] = mapped_column(Float, comment='CY coordinate')
    cz: Mapped[float | None] = mapped_column(Float, comment='CZ coordinate')
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )

    # Relationships
    room_group: Mapped[RoomGroup | None] = relationship('RoomGroup')


class WaterSystem(Base):
    """Water system model."""

    __tablename__ = 'water_system'

    water_system_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Water system ID'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='Name')
    four_pipe_sys: Mapped[int | None] = mapped_column(
        SmallInteger, comment='Four pipe system'
    )
    heatexchanger: Mapped[int | None] = mapped_column(
        SmallInteger, comment='Heat exchanger'
    )
    heatsource_pump: Mapped[int | None] = mapped_column(
        SmallInteger, comment='Heat source pump'
    )
    second_pump_cool: Mapped[int | None] = mapped_column(
        Integer, comment='Secondary pump cool'
    )
    second_pump_heat: Mapped[int | None] = mapped_column(
        Integer, comment='Secondary pump heat'
    )
    water_temperature: Mapped[int | None] = mapped_column(
        Integer, comment='Water temperature'
    )
    hot_water_temperature: Mapped[int | None] = mapped_column(
        Integer, comment='Hot water temperature'
    )
    pressure_loss1_cool: Mapped[float | None] = mapped_column(
        Float, comment='Pressure loss 1 cool'
    )
    pressure_loss1_heat: Mapped[float | None] = mapped_column(
        Float, comment='Pressure loss 1 heat'
    )
    pressure_loss2_cool: Mapped[float | None] = mapped_column(
        Float, comment='Pressure loss 2 cool'
    )
    pressure_loss2_heat: Mapped[float | None] = mapped_column(
        Float, comment='Pressure loss 2 heat'
    )
    prim_pump_ctrl_cool: Mapped[int | None] = mapped_column(
        Integer, comment='Primary pump control cool'
    )
    prim_pump_ctrl_heat: Mapped[int | None] = mapped_column(
        Integer, comment='Primary pump control heat'
    )
    secd_pump_ctrl_cool: Mapped[int | None] = mapped_column(
        Integer, comment='Secondary pump control cool'
    )
    secd_pump_ctrl_heat: Mapped[int | None] = mapped_column(
        Integer, comment='Secondary pump control heat'
    )
    cool_pump_ctrl: Mapped[int | None] = mapped_column(
        Integer, comment='Cooling pump control'
    )
    heat_pump_ctrl: Mapped[int | None] = mapped_column(
        Integer, comment='Heat pump control'
    )
    coolingtower_ctrl: Mapped[int | None] = mapped_column(
        Integer, comment='Cooling tower control'
    )
    heatexchanger_ctrl: Mapped[int | None] = mapped_column(
        Integer, comment='Heat exchanger control'
    )
    refill_pump_ctrl: Mapped[int | None] = mapped_column(
        Integer, comment='Refill pump control'
    )
    tank_bypass_cool: Mapped[int | None] = mapped_column(
        Integer, comment='Tank bypass cool'
    )
    tank_bypass_heat: Mapped[int | None] = mapped_column(
        Integer, comment='Tank bypass heat'
    )
    blank_1: Mapped[float | None] = mapped_column(Numeric, comment='Reserved field 1')
    blank_2: Mapped[float | None] = mapped_column(Numeric, comment='Reserved field 2')
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )
