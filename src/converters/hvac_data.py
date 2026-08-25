from typing import Annotated, Final, Literal, Self

from loguru import logger
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models import (
    Boiler,
    Chiller,
    Coolingtower,
    LibBoiler,
    LibChiller,
    LibCoolingtower,
    LibPump,
    Pump,
)

KILOWATTS_TO_WATTS: Final = 1000.0
KILOPASCALS_TO_PASCALS: Final = 1000.0
DEST_DISTRICT_HOT_WATER_TYPE: Final = 2
PRIMARY_CHILLED_WATER_PUMP_USAGE: Final = 0
CONDENSER_WATER_PUMP_USAGE: Final = 2

type PositiveFloat = Annotated[float, Field(gt=0)]
type AutosizableValue = PositiveFloat | Literal['Autosize']
type AutosizableNonNegativeValue = Annotated[float, Field(ge=0)] | Literal['Autosize']
type BoilerFuelType = Literal[
    'Coal',
    'Diesel',
    'Electricity',
    'FuelOilNo1',
    'FuelOilNo2',
    'Gasoline',
    'NaturalGas',
    'OtherFuel1',
    'OtherFuel2',
    'Propane',
]
type EnergyResourceType = (
    BoilerFuelType
    | Literal[
        'DistrictCooling',
        'DistrictHeatingSteam',
        'DistrictHeatingWater',
    ]
)
type EnergyPlusChillerType = Literal[
    'ElectricCentrifugalChiller',
    'ElectricReciprocatingChiller',
    'ElectricScrewChiller',
]
type EnergyPlusBoilerType = Literal['DistrictHotWater', 'HotWaterBoiler']


class MeteredIdealLoadsConfigSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    profile_name: str
    cooling_efficiency: PositiveFloat
    cooling_fuel_type: EnergyResourceType
    heating_efficiency: PositiveFloat
    heating_fuel_type: EnergyResourceType


class ChillerConfigSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    chiller_type: EnergyPlusChillerType
    capacity_w: AutosizableValue
    nominal_cop: PositiveFloat
    priority: int = Field(ge=1)


class CoolingTowerConfigSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    high_speed_nominal_capacity_w: AutosizableValue
    high_speed_fan_power_w: AutosizableValue
    free_convection_capacity_w: AutosizableNonNegativeValue
    priority: int = Field(ge=1)


class HeatingSourceConfigSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    boiler_type: EnergyPlusBoilerType
    capacity_w: AutosizableValue = 'Autosize'
    efficiency: PositiveFloat | None = None
    fuel_type: BoilerFuelType | None = None
    supply_temperature_c: float
    return_temperature_c: float
    water_outlet_upper_temperature_limit_c: float | None = None

    @model_validator(mode='after')
    def validate_heating_source(self) -> Self:
        if self.supply_temperature_c <= self.return_temperature_c:
            raise ValueError(
                'Heating supply temperature must exceed return temperature'
            )
        if self.boiler_type == 'HotWaterBoiler':
            if self.efficiency is None or self.fuel_type is None:
                raise ValueError('HotWaterBoiler requires efficiency and fuel_type')
        elif self.efficiency is not None or self.fuel_type is not None:
            raise ValueError('DistrictHotWater must not define efficiency or fuel_type')
        return self


class CentralPlantConfigSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    chillers: list[ChillerConfigSchema]
    cooling_towers: list[CoolingTowerConfigSchema]
    chilled_water_design_setpoint_c: float = 7.22
    condenser_water_design_setpoint_c: float = 32.0
    primary_chilled_water_pump_head_pa: PositiveFloat
    condenser_water_pump_head_pa: PositiveFloat
    heating_source: HeatingSourceConfigSchema

    @model_validator(mode='after')
    def validate_equipment_counts(self) -> Self:
        if not self.chillers:
            raise ValueError('Central plant requires at least one chiller')
        if len(self.chillers) != len(self.cooling_towers):
            raise ValueError('Each water-cooled chiller requires one cooling tower')
        return self


_PTHP_METERED_PROFILE: Final = MeteredIdealLoadsConfigSchema(
    profile_name='PTHP Proxy',
    cooling_efficiency=3.0,
    cooling_fuel_type='Electricity',
    heating_efficiency=2.75,
    heating_fuel_type='Electricity',
)
_VRF_METERED_PROFILE: Final = MeteredIdealLoadsConfigSchema(
    profile_name='VRF Proxy',
    cooling_efficiency=3.3,
    cooling_fuel_type='Electricity',
    heating_efficiency=3.4,
    heating_fuel_type='Electricity',
)

METERED_IDEAL_LOADS_CONFIGS: Final[dict[str, MeteredIdealLoadsConfigSchema]] = {
    'coa': _VRF_METERED_PROFILE,
    'cob': _VRF_METERED_PROFILE,
    'goa': _VRF_METERED_PROFILE,
    'gob': _VRF_METERED_PROFILE,
    'inp': _VRF_METERED_PROFILE,
    'mall': _VRF_METERED_PROFILE,
    'highs': _PTHP_METERED_PROFILE,
    'hight': _PTHP_METERED_PROFILE,
    'low': _PTHP_METERED_PROFILE,
    'sh': _PTHP_METERED_PROFILE,
    'th': _PTHP_METERED_PROFILE,
}

GENERIC_CENTRAL_PLANT_CONFIG: Final = CentralPlantConfigSchema(
    chillers=[
        ChillerConfigSchema(
            name='Main_Chiller',
            chiller_type='ElectricCentrifugalChiller',
            capacity_w='Autosize',
            nominal_cop=3.2,
            priority=1,
        )
    ],
    cooling_towers=[
        CoolingTowerConfigSchema(
            name='Main_Cooling_Tower',
            high_speed_nominal_capacity_w='Autosize',
            high_speed_fan_power_w='Autosize',
            free_convection_capacity_w='Autosize',
            priority=1,
        )
    ],
    primary_chilled_water_pump_head_pa=179_352.0,
    condenser_water_pump_head_pa=179_352.0,
    heating_source=HeatingSourceConfigSchema(
        name='Main_Boiler',
        boiler_type='HotWaterBoiler',
        efficiency=0.8,
        fuel_type='NaturalGas',
        supply_temperature_c=60.0,
        return_temperature_c=50.0,
        water_outlet_upper_temperature_limit_c=90.0,
    ),
)


def _require_positive(value: float | None, field_name: str) -> float:
    if value is None or value <= 0:
        raise ValueError(f'{field_name} must be positive, got {value}')
    return float(value)


def _uniform_positive_value(values: list[float], field_name: str) -> float:
    if not values:
        raise ValueError(f'Missing {field_name}')
    unique_values = set(values)
    if len(unique_values) != 1:
        raise ValueError(
            f'{field_name} must be uniform for an HVACTemplate loop, '
            f'got {sorted(unique_values)}'
        )
    return values[0]


def load_central_plant_config(session: Session) -> CentralPlantConfigSchema:
    chiller_rows = session.execute(
        select(Chiller, LibChiller)
        .join(
            LibChiller,
            Chiller.lib_chiller_id == LibChiller.lib_chiller_id,
        )
        .order_by(Chiller.chiller_id)
    ).all()
    tower_rows = session.execute(
        select(Coolingtower, LibCoolingtower)
        .join(
            LibCoolingtower,
            Coolingtower.lib_coolingtower_id == LibCoolingtower.lib_coolingtower_id,
        )
        .order_by(Coolingtower.coolingtower_id)
    ).all()
    pump_rows = session.execute(
        select(Pump, LibPump)
        .join(LibPump, Pump.lib_pump_id == LibPump.lib_pump_id)
        .order_by(Pump.pump_id)
    ).all()
    boiler_rows = session.execute(
        select(Boiler, LibBoiler)
        .join(LibBoiler, Boiler.lib_boiler_id == LibBoiler.lib_boiler_id)
        .order_by(Boiler.boiler_id)
    ).all()

    if not chiller_rows:
        if tower_rows or boiler_rows or pump_rows:
            raise ValueError(
                'Incomplete selected central plant equipment without chillers'
            )
        logger.warning(
            'No selected central plant equipment; using generic central plant'
        )
        return GENERIC_CENTRAL_PLANT_CONFIG.model_copy(deep=True)

    if len(tower_rows) != len(chiller_rows):
        raise ValueError(
            'Selected water-cooled chillers and cooling towers must have '
            f'equal counts, got {len(chiller_rows)} and {len(tower_rows)}'
        )
    linked_chiller_ids = {chiller.chiller_id for chiller, _ in chiller_rows}
    tower_chiller_ids = {tower.attribute_to for tower, _ in tower_rows}
    if tower_chiller_ids != linked_chiller_ids:
        raise ValueError(
            'Cooling tower attribute_to values do not match selected chillers'
        )

    valid_pump_ids = {pump.pump_id for pump, _ in pump_rows}
    dangling_second_pumps = sorted(
        chiller.second_pump
        for chiller, _ in chiller_rows
        if chiller.second_pump is not None
        and chiller.second_pump > 0
        and chiller.second_pump not in valid_pump_ids
    )
    if dangling_second_pumps:
        logger.warning(
            'Ignoring {} dangling chiller second_pump references: {}',
            len(dangling_second_pumps),
            dangling_second_pumps,
        )

    primary_pump_head_pa = _uniform_positive_value(
        [
            _require_positive(library.pressure, 'primary pump pressure')
            * KILOPASCALS_TO_PASCALS
            for pump, library in pump_rows
            if pump.usage == PRIMARY_CHILLED_WATER_PUMP_USAGE
        ],
        'primary chilled water pump head',
    )
    condenser_pump_head_pa = _uniform_positive_value(
        [
            _require_positive(library.pressure, 'condenser pump pressure')
            * KILOPASCALS_TO_PASCALS
            for pump, library in pump_rows
            if pump.usage == CONDENSER_WATER_PUMP_USAGE
        ],
        'condenser water pump head',
    )

    if len(boiler_rows) != 1:
        raise ValueError(
            'Data-driven central plant requires exactly one selected heat '
            f'source, got {len(boiler_rows)}'
        )
    boiler, boiler_library = boiler_rows[0]
    if boiler_library.type != DEST_DISTRICT_HOT_WATER_TYPE:
        raise ValueError(
            f'Unsupported selected DeST boiler type: {boiler_library.type}'
        )

    chillers = [
        ChillerConfigSchema(
            name=chiller.name or f'Chiller_{index}',
            chiller_type='ElectricCentrifugalChiller',
            capacity_w=(
                _require_positive(library.capacity, 'chiller capacity')
                * KILOWATTS_TO_WATTS
            ),
            nominal_cop=_require_positive(library.cop, 'chiller COP'),
            priority=index,
        )
        for index, (chiller, library) in enumerate(chiller_rows, start=1)
    ]
    cooling_towers = [
        CoolingTowerConfigSchema(
            name=tower.name or f'CoolingTower_{index}',
            high_speed_nominal_capacity_w=(
                _require_positive(library.capacity, 'cooling tower capacity')
                * KILOWATTS_TO_WATTS
            ),
            high_speed_fan_power_w=(
                _require_positive(library.fan_power, 'cooling tower fan power')
                * KILOWATTS_TO_WATTS
            ),
            free_convection_capacity_w=0.0,
            priority=index,
        )
        for index, (tower, library) in enumerate(tower_rows, start=1)
    ]
    condenser_water_setpoint_c = _uniform_positive_value(
        [
            _require_positive(
                library.supply_temperature,
                'cooling tower supply temperature',
            )
            for _, library in tower_rows
        ],
        'condenser water design setpoint',
    )
    heating_supply_temperature_c = _require_positive(
        boiler_library.supply_temperature,
        'district heating supply temperature',
    )
    heating_return_temperature_c = _require_positive(
        boiler_library.return_temperature,
        'district heating return temperature',
    )

    config = CentralPlantConfigSchema(
        chillers=chillers,
        cooling_towers=cooling_towers,
        condenser_water_design_setpoint_c=condenser_water_setpoint_c,
        primary_chilled_water_pump_head_pa=primary_pump_head_pa,
        condenser_water_pump_head_pa=condenser_pump_head_pa,
        heating_source=HeatingSourceConfigSchema(
            name=boiler.name or 'District_Hot_Water',
            boiler_type='DistrictHotWater',
            supply_temperature_c=heating_supply_temperature_c,
            return_temperature_c=heating_return_temperature_c,
        ),
    )
    logger.info(
        'Loaded central plant: {} chillers, {} cooling towers, heat source {}',
        len(config.chillers),
        len(config.cooling_towers),
        config.heating_source.boiler_type,
    )
    return config
