from idfpy import IDF
from idfpy.models import (
    HVACTemplateThermostat,
    HVACTemplateZoneFanCoil,
    HVACTemplateZoneIdealLoadsAirSystem,
    IDFBaseModel,
    ZoneHVACIdealLoadsAirSystem,
)

from src.converters.hvac_data import (
    GENERIC_CENTRAL_PLANT_CONFIG,
    METERED_IDEAL_LOADS_CONFIGS,
)
from src.converters.hvac_strategy import (
    FanCoilCentralPlantStrategy,
    IdealLoadsStrategy,
    MeteredIdealLoadsStrategy,
)

AVAILABILITY = 'Schedule_6_kong_tiao_qi_ting'


def _only[T: IDFBaseModel](idf: IDF, model: type[T]) -> T:
    objects = list(idf.all_of_type(model).values())
    assert len(objects) == 1
    return objects[0]


def test_ideal_loads_template_gets_availability() -> None:
    idf = IDF()
    IdealLoadsStrategy().add_zone_hvac(idf, 'Z1', 'T1', None, AVAILABILITY)

    system = _only(idf, HVACTemplateZoneIdealLoadsAirSystem)
    assert system.system_availability_schedule_name == AVAILABILITY


def test_metered_ideal_loads_gets_availability() -> None:
    idf = IDF()
    idf.add(
        HVACTemplateThermostat(
            name='T1', constant_heating_setpoint=18, constant_cooling_setpoint=26
        )
    )
    strategy = MeteredIdealLoadsStrategy(
        next(iter(METERED_IDEAL_LOADS_CONFIGS.values()))
    )
    strategy.create_system_objects(idf)
    strategy.add_zone_hvac(idf, 'Z1', 'T1', None, AVAILABILITY)

    assert _only(idf, ZoneHVACIdealLoadsAirSystem).availability_schedule_name == (
        AVAILABILITY
    )


def test_fan_coil_gets_availability() -> None:
    idf = IDF()
    strategy = FanCoilCentralPlantStrategy(GENERIC_CENTRAL_PLANT_CONFIG)
    strategy.add_zone_hvac(idf, 'Z1', 'T1', 0.1, AVAILABILITY)

    fan_coil = _only(idf, HVACTemplateZoneFanCoil)
    assert fan_coil.system_availability_schedule_name == AVAILABILITY
