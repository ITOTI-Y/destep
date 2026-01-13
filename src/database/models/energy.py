from __future__ import annotations

from sqlalchemy import Float, Integer, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from ._base import Base


class EnergyDevice(Base):
    """Energy device model."""

    __tablename__ = 'ENERGY_DEVICE'

    id: Mapped[int] = mapped_column(
        'ID', Integer, primary_key=True, comment='Device ID'
    )
    name: Mapped[str | None] = mapped_column('NAME', String(50), comment='Device name')
    count: Mapped[int | None] = mapped_column('COUNT', Integer, comment='Count')
    power: Mapped[float | None] = mapped_column('POWER', Float, comment='Power')
    schedule: Mapped[int | None] = mapped_column(
        'SCHEDULE', Integer, comment='Operation schedule'
    )
    ext_property: Mapped[int | None] = mapped_column(
        'EXT_PROPERTY', Integer, comment='Extended property'
    )


class EnergyHotwater(Base):
    """Energy hotwater system model."""

    __tablename__ = 'ENERGY_HOTWATER'

    id: Mapped[int] = mapped_column(
        'ID', Integer, primary_key=True, comment='Hotwater system ID'
    )
    name: Mapped[str | None] = mapped_column('NAME', String(50), comment='System name')
    sys_type: Mapped[int | None] = mapped_column(
        'SYS_TYPE', SmallInteger, comment='System type'
    )
    fuel_type: Mapped[int | None] = mapped_column(
        'FUEL_TYPE', SmallInteger, comment='Fuel type'
    )
    mean_flowrate_day: Mapped[float | None] = mapped_column(
        'MEAN_FLOWRATE_DAY', Float, comment='Daily mean flow rate'
    )
    distance: Mapped[float | None] = mapped_column(
        'DISTANCE', Float, comment='Pipe distance'
    )
    insulation_level: Mapped[int | None] = mapped_column(
        'INSULATION_LEVEL', SmallInteger, comment='Insulation level'
    )
    count_pump: Mapped[int | None] = mapped_column(
        'COUNT_PUMP', SmallInteger, comment='Pump count'
    )
    flowrate_pump: Mapped[float | None] = mapped_column(
        'FLOWRATE_PUMP', Float, comment='Pump flow rate'
    )
    pressure_pump: Mapped[float | None] = mapped_column(
        'PRESSURE_PUMP', Float, comment='Pump pressure'
    )
    ratio_pump: Mapped[float | None] = mapped_column(
        'RATIO_PUMP', Float, comment='Pump efficiency'
    )
    schedule_supply: Mapped[int | None] = mapped_column(
        'SCHEDULE_SUPPLY', Integer, comment='Supply schedule'
    )
    schedule_hot_temp: Mapped[int | None] = mapped_column(
        'SCHEDULE_HOT_TEMP', Integer, comment='Hot water temperature schedule'
    )
    schedule_source_temp: Mapped[int | None] = mapped_column(
        'SCHEDULE_SOURCE_TEMP', Integer, comment='Source temperature schedule'
    )
    schedule_env_temp: Mapped[int | None] = mapped_column(
        'SCHEDULE_ENV_TEMP', Integer, comment='Environment temperature schedule'
    )
    schedule_pump: Mapped[int | None] = mapped_column(
        'SCHEDULE_PUMP', Integer, comment='Pump operation schedule'
    )
    ext_property: Mapped[int | None] = mapped_column(
        'EXT_PROPERTY', Integer, comment='Extended property'
    )


class EnergyLiftEscalator(Base):
    """Energy lift and escalator model."""

    __tablename__ = 'ENERGY_LIFT_ESCALATOR'

    id: Mapped[int] = mapped_column(
        'ID', Integer, primary_key=True, comment='Lift/escalator ID'
    )
    name: Mapped[str | None] = mapped_column('NAME', String(50), comment='Name')
    mode: Mapped[int | None] = mapped_column(
        'MODE', SmallInteger, comment='Operation mode'
    )
    count: Mapped[int | None] = mapped_column('COUNT', Integer, comment='Count')
    power: Mapped[float | None] = mapped_column('POWER', Float, comment='Power')
    standby: Mapped[float | None] = mapped_column(
        'STANDBY', Float, comment='Standby power'
    )
    density: Mapped[float | None] = mapped_column(
        'DENSITY', Float, comment='Usage density'
    )
    ratio: Mapped[float | None] = mapped_column('RATIO', Float, comment='Efficiency')
    schedule: Mapped[int | None] = mapped_column(
        'SCHEDULE', Integer, comment='Operation schedule'
    )
    ext_property: Mapped[int | None] = mapped_column(
        'EXT_PROPERTY', Integer, comment='Extended property'
    )


class EnergyPumpGroup(Base):
    """Energy pump group model."""

    __tablename__ = 'ENERGY_PUMP_GROUP'

    id: Mapped[int] = mapped_column(
        'ID', Integer, primary_key=True, comment='Pump group ID'
    )
    name: Mapped[str | None] = mapped_column('NAME', String(50), comment='Name')
    mode: Mapped[int | None] = mapped_column(
        'MODE', SmallInteger, comment='Operation mode'
    )
    count_major: Mapped[int | None] = mapped_column(
        'COUNT_MAJOR', Integer, comment='Major pump count'
    )
    count_minor: Mapped[int | None] = mapped_column(
        'COUNT_MINOR', Integer, comment='Minor pump count'
    )
    flowrate_major: Mapped[float | None] = mapped_column(
        'FLOWRATE_MAJOR', Float, comment='Major pump flow rate'
    )
    flowrate_minor: Mapped[float | None] = mapped_column(
        'FLOWRATE_MINOR', Float, comment='Minor pump flow rate'
    )
    pressure_major: Mapped[float | None] = mapped_column(
        'PRESSURE_MAJOR', Float, comment='Major pump pressure'
    )
    pressure_minor: Mapped[float | None] = mapped_column(
        'PRESSURE_MINOR', Float, comment='Minor pump pressure'
    )
    ratio_major: Mapped[float | None] = mapped_column(
        'RATIO_MAJOR', Float, comment='Major pump efficiency'
    )
    ratio_minor: Mapped[float | None] = mapped_column(
        'RATIO_MINOR', Float, comment='Minor pump efficiency'
    )
    mean_flowrate_day: Mapped[float | None] = mapped_column(
        'MEAN_FLOWRATE_DAY', Float, comment='Daily mean flow rate'
    )
    max_flowrate_cooling: Mapped[float | None] = mapped_column(
        'MAX_FLOWRATE_COOLING', Float, comment='Max cooling flow rate'
    )
    schedule: Mapped[int | None] = mapped_column(
        'SCHEDULE', Integer, comment='Operation schedule'
    )
    schedule_cooling: Mapped[int | None] = mapped_column(
        'SCHEDULE_COOLING', Integer, comment='Cooling operation schedule'
    )
    ext_property: Mapped[int | None] = mapped_column(
        'EXT_PROPERTY', Integer, comment='Extended property'
    )
