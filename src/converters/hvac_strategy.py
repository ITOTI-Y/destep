from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from loguru import logger

from src.idf.models.hvac_templates import (
    HVACTemplatePlantBoiler,
    HVACTemplatePlantChilledWaterLoop,
    HVACTemplatePlantChiller,
    HVACTemplatePlantHotWaterLoop,
    HVACTemplateSystemVRF,
    HVACTemplateZoneFanCoil,
    HVACTemplateZoneIdealLoadsAirSystem,
    HVACTemplateZonePTHP,
    HVACTemplateZoneVRF,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from src.idf import IDF
    from src.idf.models._base import IDFBaseModel


class HVACStrategy(Protocol):
    name: str

    def create_zone_hvac(
        self,
        zone_name: str,
        thermostat_name: str,
        fresh_air_flow: float | None,
    ) -> IDFBaseModel: ...

    def create_system_objects(self, idf: IDF) -> None: ...


class IdealLoadsStrategy:
    name: str = 'ideal-loads'

    def create_zone_hvac(
        self,
        zone_name: str,
        thermostat_name: str,
        fresh_air_flow: float | None,
    ) -> HVACTemplateZoneIdealLoadsAirSystem:
        if fresh_air_flow is not None and fresh_air_flow > 0:
            outdoor_air_method = 'Flow/Zone'
            outdoor_air_flow_rate_per_zone = fresh_air_flow
        else:
            outdoor_air_method = ''
            outdoor_air_flow_rate_per_zone = 0.0

        return HVACTemplateZoneIdealLoadsAirSystem(
            zone_name=zone_name,
            template_thermostat_name=thermostat_name,
            maximum_heating_supply_air_temperature=50.0,
            minimum_cooling_supply_air_temperature=13.0,
            heating_limit='NoLimit',
            cooling_limit='NoLimit',
            outdoor_air_method=outdoor_air_method,
            outdoor_air_flow_rate_per_zone=outdoor_air_flow_rate_per_zone,
        )

    def create_system_objects(self, idf: IDF) -> None:
        pass


class PTHPStrategy:
    name: str = 'pthp'

    def create_zone_hvac(
        self,
        zone_name: str,
        thermostat_name: str,
        fresh_air_flow: float | None,
    ) -> HVACTemplateZonePTHP:
        if fresh_air_flow is not None and fresh_air_flow > 0:
            outdoor_air_method = 'Flow/Zone'
            outdoor_air_flow_rate_per_zone = fresh_air_flow
        else:
            outdoor_air_method = ''
            outdoor_air_flow_rate_per_zone = 0.0

        return HVACTemplateZonePTHP(
            zone_name=zone_name,
            template_thermostat_name=thermostat_name,
            outdoor_air_method=outdoor_air_method,
            outdoor_air_flow_rate_per_zone=outdoor_air_flow_rate_per_zone,
        )

    def create_system_objects(self, idf: IDF) -> None:
        pass


class VRFStrategy:
    name: str = 'vrf'
    VRF_SYSTEM_NAME: str = 'VRF_System_001'

    def create_zone_hvac(
        self,
        zone_name: str,
        thermostat_name: str,
        fresh_air_flow: float | None,
    ) -> HVACTemplateZoneVRF:
        if fresh_air_flow is not None and fresh_air_flow > 0:
            outdoor_air_method = 'Flow/Zone'
            outdoor_air_flow_rate_per_zone = fresh_air_flow
        else:
            outdoor_air_method = ''
            outdoor_air_flow_rate_per_zone = 0.0

        return HVACTemplateZoneVRF(
            zone_name=zone_name,
            template_vrf_system_name=self.VRF_SYSTEM_NAME,
            template_thermostat_name=thermostat_name,
            outdoor_air_method=outdoor_air_method,
            outdoor_air_flow_rate_per_zone=outdoor_air_flow_rate_per_zone,
        )

    def create_system_objects(self, idf: IDF) -> None:
        vrf_system = HVACTemplateSystemVRF(name=self.VRF_SYSTEM_NAME)
        idf.add(vrf_system)
        logger.debug(f'Created HVACTemplateSystemVRF: {self.VRF_SYSTEM_NAME}')


class FanCoilChillerBoilerStrategy:
    name: str = 'fan-coil'

    CHILLED_WATER_LOOP_NAME = 'Chilled_Water_Loop'
    HOT_WATER_LOOP_NAME = 'Hot_Water_Loop'
    CHILLER_NAME = 'Main_Chiller'
    BOILER_NAME = 'Main_Boiler'

    # Default values for chiller and boiler (if database not provided)
    DEFAULT_CHILLER_COP = 3.2
    DEFAULT_BOILER_EFFICIENCY = 0.8

    def __init__(self, session: Session | None = None) -> None:
        self._chiller_cop = self.DEFAULT_CHILLER_COP
        self._boiler_efficiency = self.DEFAULT_BOILER_EFFICIENCY

        if session is not None:
            self._load_plant_data(session)

    def _load_plant_data(self, session: Session) -> None:
        from sqlalchemy import select

        from src.database.models.hvac import Boiler, Chiller, LibBoiler, LibChiller

        stmt = (
            select(LibChiller.cop)
            .join(Chiller, Chiller.lib_chiller_id == LibChiller.lib_chiller_id)
            .where(LibChiller.cop.is_not(None))
            .limit(1)
        )

        result = session.execute(stmt).scalar_one_or_none()
        if result is not None and result > 0:
            self._chiller_cop = result
            logger.info(f'Using chiller COP from database: {self._chiller_cop}')

        stmt = (
            select(LibBoiler.efficiency)
            .join(Boiler, Boiler.lib_boiler_id == LibBoiler.lib_boiler_id)
            .where(LibBoiler.efficiency.is_not(None))
            .limit(1)
        )
        result = session.execute(stmt).scalar_one_or_none()
        if result is not None and 0 < result <= 1:
            self._boiler_efficiency = result
            logger.info(
                f'Using boiler efficiency from database: {self._boiler_efficiency}'
            )

    def create_zone_hvac(
        self,
        zone_name: str,
        thermostat_name: str,
        fresh_air_flow: float | None,
    ) -> HVACTemplateZoneFanCoil:
        if fresh_air_flow is not None and fresh_air_flow > 0:
            outdoor_air_method = 'Flow/Zone'
            outdoor_air_flow_rate_per_zone = fresh_air_flow
        else:
            outdoor_air_method = ''
            outdoor_air_flow_rate_per_zone = 0.0

        return HVACTemplateZoneFanCoil(
            zone_name=zone_name,
            template_thermostat_name=thermostat_name,
            outdoor_air_method=outdoor_air_method,
            outdoor_air_flow_rate_per_zone=outdoor_air_flow_rate_per_zone,
        )

    def create_system_objects(self, idf: IDF) -> None:
        idf.add(HVACTemplatePlantChilledWaterLoop(name=self.CHILLED_WATER_LOOP_NAME))

        idf.add(
            HVACTemplatePlantChiller(
                name=self.CHILLER_NAME,
                chiller_type='ElectricCentrifugalChiller',
                nominal_cop=self._chiller_cop,
                condenser_type='AirCooled',
                priority='1',
            )
        )

        idf.add(HVACTemplatePlantHotWaterLoop(name=self.HOT_WATER_LOOP_NAME))

        idf.add(
            HVACTemplatePlantBoiler(
                name=self.BOILER_NAME,
                boiler_type='HotWaterBoiler',
                efficiency=self._boiler_efficiency,
                fuel_type='NaturalGas',
                priority='1',
            )
        )

        logger.debug(
            f'Created plant objects: chiller COP={self._chiller_cop}, '
            f'boiler eff={self._boiler_efficiency}'
        )
