from typing import Final, Protocol

from idfpy import IDF
from idfpy.models import (
    DesignSpecificationOutdoorAir,
    HVACTemplatePlantBoiler,
    HVACTemplatePlantChilledWaterLoop,
    HVACTemplatePlantChiller,
    HVACTemplatePlantHotWaterLoop,
    HVACTemplatePlantTower,
    HVACTemplateZoneFanCoil,
    HVACTemplateZoneIdealLoadsAirSystem,
    ScheduleConstant,
    SizingZone,
    ZoneHVACEquipmentConnections,
    ZoneHVACEquipmentList,
    ZoneHVACEquipmentListEquipmentItem,
    ZoneHVACIdealLoadsAirSystem,
)
from loguru import logger

from src.converters.hvac_data import (
    CentralPlantConfigSchema,
    MeteredIdealLoadsConfigSchema,
)


class HVACStrategy(Protocol):
    name: Final[str]

    def create_system_objects(self, idf: IDF) -> None:
        raise NotImplementedError

    def add_zone_hvac(
        self,
        idf: IDF,
        zone_name: str,
        thermostat_name: str,
        fresh_air_flow: float | None,
    ) -> None:
        raise NotImplementedError


class IdealLoadsStrategy:
    name: Final[str] = 'ideal-loads'

    def add_zone_hvac(
        self,
        idf: IDF,
        zone_name: str,
        thermostat_name: str,
        fresh_air_flow: float | None,
    ) -> None:
        if fresh_air_flow is not None and fresh_air_flow > 0:
            outdoor_air_method = 'Flow/Zone'
            outdoor_air_flow_rate_per_zone = fresh_air_flow
        else:
            outdoor_air_method = ''
            outdoor_air_flow_rate_per_zone = 0.0

        idf.add(
            HVACTemplateZoneIdealLoadsAirSystem(
                zone_name=zone_name,
                template_thermostat_name=thermostat_name,
                maximum_heating_supply_air_temperature=50.0,
                minimum_cooling_supply_air_temperature=13.0,
                heating_limit='NoLimit',
                cooling_limit='NoLimit',
                outdoor_air_method=outdoor_air_method,
                outdoor_air_flow_rate_per_zone=outdoor_air_flow_rate_per_zone,
            )
        )

    def create_system_objects(self, idf: IDF) -> None:
        return None


class MeteredIdealLoadsStrategy:
    name: Final[str] = 'metered-ideal-loads'

    def __init__(self, config: MeteredIdealLoadsConfigSchema) -> None:
        self._config = config
        self._cooling_efficiency_schedule_name = (
            f'{config.profile_name} Cooling Efficiency'
        )
        self._heating_efficiency_schedule_name = (
            f'{config.profile_name} Heating Efficiency'
        )

    def create_system_objects(self, idf: IDF) -> None:
        idf.add(
            ScheduleConstant(
                name=self._cooling_efficiency_schedule_name,
                hourly_value=self._config.cooling_efficiency,
            )
        )
        idf.add(
            ScheduleConstant(
                name=self._heating_efficiency_schedule_name,
                hourly_value=self._config.heating_efficiency,
            )
        )

    def add_zone_hvac(
        self,
        idf: IDF,
        zone_name: str,
        thermostat_name: str,
        fresh_air_flow: float | None,
    ) -> None:
        equipment_name = f'{zone_name} Ideal Loads Air System'
        equipment_list_name = f'{zone_name} Equipment'
        supply_node_name = f'{zone_name} Metered Ideal Loads Supply Inlet'
        zone_air_node_name = f'{zone_name} Zone Air Node'
        return_node_name = f'{zone_name} Return Outlet'

        outdoor_air_specification_name: str | None = None
        outdoor_air_node_name: str | None = None
        if fresh_air_flow is not None and fresh_air_flow > 0:
            outdoor_air_specification_name = f'DSOA {zone_name}'
            outdoor_air_node_name = f'{zone_name} Ideal Loads Outdoor Air Inlet'
            idf.add(
                DesignSpecificationOutdoorAir(
                    name=outdoor_air_specification_name,
                    outdoor_air_method='Flow/Zone',
                    outdoor_air_flow_per_person=0.0,
                    outdoor_air_flow_per_zone_floor_area=0.0,
                    outdoor_air_flow_per_zone=fresh_air_flow,
                )
            )

        idf.add(
            SizingZone(
                zone_or_zonelist_name=zone_name,
                zone_cooling_design_supply_air_temperature_input_method=(
                    'SupplyAirTemperature'
                ),
                zone_cooling_design_supply_air_temperature=13.0,
                zone_heating_design_supply_air_temperature_input_method=(
                    'SupplyAirTemperature'
                ),
                zone_heating_design_supply_air_temperature=50.0,
                zone_cooling_design_supply_air_humidity_ratio=0.0077,
                zone_heating_design_supply_air_humidity_ratio=0.0156,
                design_specification_outdoor_air_object_name=(
                    outdoor_air_specification_name
                ),
            )
        )

        idf.add(
            ZoneHVACIdealLoadsAirSystem(
                name=equipment_name,
                zone_supply_air_node_name=supply_node_name,
                maximum_heating_supply_air_temperature=50.0,
                minimum_cooling_supply_air_temperature=13.0,
                maximum_heating_supply_air_humidity_ratio=0.0156,
                minimum_cooling_supply_air_humidity_ratio=0.0077,
                heating_limit='NoLimit',
                cooling_limit='NoLimit',
                dehumidification_control_type='ConstantSensibleHeatRatio',
                cooling_sensible_heat_ratio=0.7,
                humidification_control_type='None',
                design_specification_outdoor_air_object_name=(
                    outdoor_air_specification_name
                ),
                outdoor_air_inlet_node_name=outdoor_air_node_name,
                demand_controlled_ventilation_type='None',
                outdoor_air_economizer_type='NoEconomizer',
                heat_recovery_type='None',
                heating_fuel_efficiency_schedule_name=(
                    self._heating_efficiency_schedule_name
                ),
                heating_fuel_type=self._config.heating_fuel_type,
                cooling_fuel_efficiency_schedule_name=(
                    self._cooling_efficiency_schedule_name
                ),
                cooling_fuel_type=self._config.cooling_fuel_type,
            )
        )

        idf.add(
            ZoneHVACEquipmentList(
                name=equipment_list_name,
                load_distribution_scheme='SequentialLoad',
                equipment=[
                    ZoneHVACEquipmentListEquipmentItem(
                        zone_equipment_object_type=('ZoneHVAC:IdealLoadsAirSystem'),
                        zone_equipment_name=equipment_name,
                        zone_equipment_cooling_sequence=1,
                        zone_equipment_heating_or_no_load_sequence=1,
                    )
                ],
            )
        )
        idf.add(
            ZoneHVACEquipmentConnections(
                zone_name=zone_name,
                zone_conditioning_equipment_list_name=equipment_list_name,
                zone_air_inlet_node_or_nodelist_name=supply_node_name,
                zone_air_node_name=zone_air_node_name,
                zone_return_air_node_or_nodelist_name=return_node_name,
            )
        )

        logger.debug(
            'Created metered Ideal Loads for {} with profile {} and thermostat {}',
            zone_name,
            self._config.profile_name,
            thermostat_name,
        )


class FanCoilCentralPlantStrategy:
    name: Final[str] = 'fan-coil'

    CHILLED_WATER_LOOP_NAME: Final = 'Chilled_Water_Loop'
    HOT_WATER_LOOP_NAME: Final = 'Hot_Water_Loop'

    def __init__(self, config: CentralPlantConfigSchema) -> None:
        self._config = config

    def create_system_objects(self, idf: IDF) -> None:
        chiller_count = len(self._config.chillers)
        tower_count = len(self._config.cooling_towers)
        idf.add(
            HVACTemplatePlantChilledWaterLoop(
                name=self.CHILLED_WATER_LOOP_NAME,
                chilled_water_design_setpoint=self._config.chilled_water_design_setpoint_c,
                chilled_water_pump_configuration='ConstantPrimaryNoSecondary',
                primary_chilled_water_pump_rated_head=self._config.primary_chilled_water_pump_head_pa,
                condenser_water_temperature_control_type='SpecifiedSetpoint',
                condenser_water_design_setpoint=self._config.condenser_water_design_setpoint_c,
                condenser_water_pump_rated_head=self._config.condenser_water_pump_head_pa,
                chilled_water_primary_pump_type='PumpPerChiller'
                if chiller_count > 1
                else 'SinglePump',
                condenser_water_pump_type='PumpPerTower'
                if tower_count > 1
                else 'SinglePump',
            )
        )

        for chiller in self._config.chillers:
            idf.add(
                HVACTemplatePlantChiller(
                    name=chiller.name,
                    chiller_type=chiller.chiller_type,
                    capacity=chiller.capacity_w,
                    nominal_cop=chiller.nominal_cop,
                    condenser_type='WaterCooled',
                    priority=str(chiller.priority),
                )
            )

        for tower in self._config.cooling_towers:
            idf.add(
                HVACTemplatePlantTower(
                    name=tower.name,
                    tower_type='SingleSpeed',
                    high_speed_nominal_capacity=(tower.high_speed_nominal_capacity_w),
                    high_speed_fan_power=tower.high_speed_fan_power_w,
                    free_convection_capacity=tower.free_convection_capacity_w,
                    priority=str(tower.priority),
                )
            )

        heating_source = self._config.heating_source

        idf.add(
            HVACTemplatePlantHotWaterLoop(
                name=self.HOT_WATER_LOOP_NAME,
                hot_water_pump_configuration='VariableFlow',
                hot_water_design_setpoint=(heating_source.supply_temperature_c),
                loop_design_delta_temperature=(
                    heating_source.supply_temperature_c
                    - heating_source.return_temperature_c
                ),
            )
        )
        idf.add(
            HVACTemplatePlantBoiler(
                name=heating_source.name,
                boiler_type=heating_source.boiler_type,
                capacity=heating_source.capacity_w,
                efficiency=heating_source.efficiency,
                fuel_type=heating_source.fuel_type,
                priority='1',
                water_outlet_upper_temperature_limit=(
                    heating_source.water_outlet_upper_temperature_limit_c
                ),
            )
        )
        logger.debug(
            'Created central plant with {} chillers, {} towers, and {}',
            chiller_count,
            tower_count,
            heating_source.boiler_type,
        )

    def add_zone_hvac(
        self,
        idf: IDF,
        zone_name: str,
        thermostat_name: str,
        fresh_air_flow: float | None,
    ) -> None:
        if fresh_air_flow is not None and fresh_air_flow > 0:
            outdoor_air_method = 'Flow/Zone'
            outdoor_air_flow_rate_per_zone = fresh_air_flow
        else:
            outdoor_air_method = ''
            outdoor_air_flow_rate_per_zone = 0.0

        idf.add(
            HVACTemplateZoneFanCoil(
                zone_name=zone_name,
                template_thermostat_name=thermostat_name,
                outdoor_air_method=outdoor_air_method,
                outdoor_air_flow_rate_per_zone=outdoor_air_flow_rate_per_zone,
            )
        )
