from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ._base import Base


class Environment(Base):
    """Environment model."""

    __tablename__ = 'environment'

    environment_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Environment ID'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='Environment name')
    south_direction: Mapped[float | None] = mapped_column(
        Float, comment='South direction angle'
    )
    data_source: Mapped[int | None] = mapped_column(Integer, comment='Data source')
    city_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('sys_city.city_id'), comment='City ID'
    )
    city_name: Mapped[str | None] = mapped_column(String(50), comment='City name')
    province: Mapped[str | None] = mapped_column(String(50), comment='Province')
    country: Mapped[str | None] = mapped_column(String(50), comment='Country')
    latitude: Mapped[float | None] = mapped_column(Float, comment='Latitude')
    longitude: Mapped[float | None] = mapped_column(Float, comment='Longitude')
    elevation: Mapped[float | None] = mapped_column(Float, comment='Elevation (m)')
    air_pressure: Mapped[float | None] = mapped_column(
        Float, comment='Atmospheric pressure (Pa)'
    )
    property: Mapped[int | None] = mapped_column(Integer, comment='Property')
    ground_reflect_coef: Mapped[float | None] = mapped_column(
        Float, comment='Ground reflectance coefficient'
    )
    x: Mapped[float | None] = mapped_column(Float, comment='X coordinate')
    y: Mapped[float | None] = mapped_column(Float, comment='Y coordinate')
    z: Mapped[float | None] = mapped_column(Float, comment='Z coordinate')
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )

    # Relationships
    city: Mapped[SysCity | None] = relationship(
        'SysCity', back_populates='environments'
    )


class ClimateData(Base):
    """Climate data model (hourly weather data)."""

    __tablename__ = 'climate_data'

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Climate data ID'
    )
    hour: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Hour of year (0-8759)'
    )
    dry_bulb_t: Mapped[float | None] = mapped_column(
        Float, comment='Dry bulb temperature (°C)'
    )
    damp: Mapped[float | None] = mapped_column(Float, comment='Humidity ratio (g/kg)')
    hori_total_rad: Mapped[float | None] = mapped_column(
        Float, comment='Horizontal total radiation (W/m²)'
    )
    hori_scatter_rad: Mapped[float | None] = mapped_column(
        Float, comment='Horizontal scattered radiation (W/m²)'
    )
    t_ground: Mapped[float | None] = mapped_column(
        Float, comment='Ground temperature (°C)'
    )
    t_sky: Mapped[float | None] = mapped_column(Float, comment='Sky temperature (°C)')
    ws: Mapped[float | None] = mapped_column(Float, comment='Wind speed (m/s)')
    wd: Mapped[float | None] = mapped_column(Float, comment='Wind direction (°)')
    b: Mapped[float | None] = mapped_column(Float, comment='Atmospheric pressure (Pa)')



class SysCity(Base):
    """System city model."""

    __tablename__ = 'sys_city'

    city_id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='City ID')
    country: Mapped[str | None] = mapped_column(String(50), comment='Country (English)')
    ccountry: Mapped[str | None] = mapped_column(
        String(50), comment='Country (Chinese)'
    )
    province: Mapped[str | None] = mapped_column(
        String(50), comment='Province (English)'
    )
    cprovince: Mapped[str | None] = mapped_column(
        String(50), comment='Province (Chinese)'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='City name (English)')
    cname: Mapped[str | None] = mapped_column(String(50), comment='City name (Chinese)')
    longitude: Mapped[float | None] = mapped_column(Float, comment='Longitude')
    latitude: Mapped[float | None] = mapped_column(Float, comment='Latitude')
    elevation: Mapped[float | None] = mapped_column(Float, comment='Elevation (m)')
    weather_type: Mapped[int | None] = mapped_column(Integer, comment='Weather type')
    climate_id: Mapped[int | None] = mapped_column(
        Integer, comment='Climate data reference'
    )
    ground_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('ground.ground_id'), comment='Ground reference'
    )
    note: Mapped[str | None] = mapped_column(String(255), comment='Note')

    # Relationships
    ground: Mapped[Ground | None] = relationship('Ground', back_populates='cities')
    environments: Mapped[list[Environment]] = relationship(
        'Environment', back_populates='city'
    )


class Outside(Base):
    """Outside environment model."""

    __tablename__ = 'outside'

    outside_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Outside ID'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='Name')
    x: Mapped[float | None] = mapped_column(Float, comment='X coordinate')
    y: Mapped[float | None] = mapped_column(Float, comment='Y coordinate')
    z: Mapped[float | None] = mapped_column(Float, comment='Z coordinate')
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )


class OutsideData(Base):
    """Outside data model."""

    __tablename__ = 'outside_data'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='ID')
    hour: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Hour')
    t: Mapped[float | None] = mapped_column(Float, comment='Temperature')
    d: Mapped[float | None] = mapped_column(Float, comment='Humidity')


class Ground(Base):
    """Ground model."""

    __tablename__ = 'ground'

    ground_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment='Ground ID'
    )
    name: Mapped[str | None] = mapped_column(String(50), comment='Name')
    x: Mapped[float | None] = mapped_column(Float, comment='X coordinate')
    y: Mapped[float | None] = mapped_column(Float, comment='Y coordinate')
    z: Mapped[float | None] = mapped_column(Float, comment='Z coordinate')
    ext_property: Mapped[int | None] = mapped_column(
        Integer, comment='Extended property'
    )

    # Relationships
    cities: Mapped[list[SysCity]] = relationship('SysCity', back_populates='ground')
