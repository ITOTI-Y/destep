from __future__ import annotations

from sqlalchemy import Float, Integer, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from ._base import Base


class EnergyDevice(Base):
    """Energy device model."""

    __tablename__ = 'energy_device'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Device ID')
    name: Mapped[str | None] = mapped_column(String(50), comment='Device name')
    count: Mapped[int | None] = mapped_column(Integer, comment='Count')
    power: Mapped[float | None] = mapped_column(Float, comment='Power')
    schedule: Mapped[int | None] = mapped_column(Integer, comment='Operation schedule')
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )


class EnergyHotwater(Base):
    """Energy hotwater system model."""

    __tablename__ = 'energy_hotwater'

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Hotwater system ID'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='System name')
    sys_type: Mapped[int | None] = mapped_column(SmallInteger, comment='System type')
    fuel_type: Mapped[int | None] = mapped_column(SmallInteger, comment='Fuel type')
    mean_flowrate_day: Mapped[float | None] = mapped_column(
        Float, comment='Daily mean flow rate'
    )
    distance: Mapped[float | None] = mapped_column(Float, comment='Pipe distance')
    insulation_level: Mapped[int | None] = mapped_column(
        SmallInteger, comment='Insulation level'
    )
    count_pump: Mapped[int | None] = mapped_column(SmallInteger, comment='Pump count')
    flowrate_pump: Mapped[float | None] = mapped_column(Float, comment='Pump flow rate')
    pressure_pump: Mapped[float | None] = mapped_column(Float, comment='Pump pressure')
    ratio_pump: Mapped[float | None] = mapped_column(Float, comment='Pump efficiency')
    schedule_supply: Mapped[int | None] = mapped_column(
        Integer, comment='Supply schedule'
    )
    schedule_hot_temp: Mapped[int | None] = mapped_column(
        Integer, comment='Hot water temperature schedule'
    )
    schedule_source_temp: Mapped[int | None] = mapped_column(
        Integer, comment='Source temperature schedule'
    )
    schedule_env_temp: Mapped[int | None] = mapped_column(
        Integer, comment='Environment temperature schedule'
    )
    schedule_pump: Mapped[int | None] = mapped_column(
        Integer, comment='Pump operation schedule'
    )
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )


class EnergyLiftEscalator(Base):
    """Energy lift and escalator model."""

    __tablename__ = 'energy_lift_escalator'

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Lift/escalator ID'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='Name')
    mode: Mapped[int | None] = mapped_column(SmallInteger, comment='Operation mode')
    count: Mapped[int | None] = mapped_column(Integer, comment='Count')
    power: Mapped[float | None] = mapped_column(Float, comment='Power')
    standby: Mapped[float | None] = mapped_column(Float, comment='Standby power')
    density: Mapped[float | None] = mapped_column(Float, comment='Usage density')
    ratio: Mapped[float | None] = mapped_column(Float, comment='Efficiency')
    schedule: Mapped[int | None] = mapped_column(Integer, comment='Operation schedule')
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )


class EnergyPumpGroup(Base):
    """Energy pump group model."""

    __tablename__ = 'energy_pump_group'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Pump group ID')
    name: Mapped[str | None] = mapped_column(String(50), comment='Name')
    mode: Mapped[int | None] = mapped_column(SmallInteger, comment='Operation mode')
    count_major: Mapped[int | None] = mapped_column(Integer, comment='Major pump count')
    count_minor: Mapped[int | None] = mapped_column(Integer, comment='Minor pump count')
    flowrate_major: Mapped[float | None] = mapped_column(
        Float, comment='Major pump flow rate'
    )
    flowrate_minor: Mapped[float | None] = mapped_column(
        Float, comment='Minor pump flow rate'
    )
    pressure_major: Mapped[float | None] = mapped_column(
        Float, comment='Major pump pressure'
    )
    pressure_minor: Mapped[float | None] = mapped_column(
        Float, comment='Minor pump pressure'
    )
    ratio_major: Mapped[float | None] = mapped_column(
        Float, comment='Major pump efficiency'
    )
    ratio_minor: Mapped[float | None] = mapped_column(
        Float, comment='Minor pump efficiency'
    )
    mean_flowrate_day: Mapped[float | None] = mapped_column(
        Float, comment='Daily mean flow rate'
    )
    max_flowrate_cooling: Mapped[float | None] = mapped_column(
        Float, comment='Max cooling flow rate'
    )
    schedule: Mapped[int | None] = mapped_column(Integer, comment='Operation schedule')
    schedule_cooling: Mapped[int | None] = mapped_column(
        Integer, comment='Cooling operation schedule'
    )
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )
