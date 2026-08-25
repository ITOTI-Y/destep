from enum import StrEnum
from typing import Final


class HVACStrategyType(StrEnum):
    IDEAL_LOADS = 'ideal-loads'
    METERED_IDEAL_LOADS = 'metered-ideal-loads'
    FAN_COIL = 'fan-coil'


BUILDING_HVAC_MAP: Final[dict[str, HVACStrategyType]] = {
    'default': HVACStrategyType.IDEAL_LOADS,
    'coa': HVACStrategyType.METERED_IDEAL_LOADS,  # Commercial Office A
    'cob': HVACStrategyType.METERED_IDEAL_LOADS,  # Commercial Office B
    'goa': HVACStrategyType.METERED_IDEAL_LOADS,  # Government Office A
    'gob': HVACStrategyType.METERED_IDEAL_LOADS,  # Government Office B
    'highs': HVACStrategyType.METERED_IDEAL_LOADS,  # High Rise Apartment slab type
    'hight': HVACStrategyType.METERED_IDEAL_LOADS,  # High Rise Apartment tower type
    'inp': HVACStrategyType.METERED_IDEAL_LOADS,  # Inpatient
    'lh': HVACStrategyType.FAN_COIL,  # Large Hotel
    'low': HVACStrategyType.METERED_IDEAL_LOADS,  # Low Rise Apartment
    'mall': HVACStrategyType.METERED_IDEAL_LOADS,  # Shopping Mall
    'outp': HVACStrategyType.FAN_COIL,  # Outpatient
    'sch': HVACStrategyType.FAN_COIL,  # Primary/secondary school
    'sh': HVACStrategyType.METERED_IDEAL_LOADS,  # Small Hotel
    'th': HVACStrategyType.METERED_IDEAL_LOADS,  # Terraced House
    'uni': HVACStrategyType.FAN_COIL,  # University
}
