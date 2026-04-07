from enum import StrEnum
from typing import Final


class HVACStrategyType(StrEnum):
    IDEAL_LOADS = 'ideal-loads'
    PTHP = 'pthp'
    VRF = 'vrf'
    FAN_COIL = 'fan-coil'


BUILDING_HVAC_MAP: Final[dict[str, HVACStrategyType]] = {
    'default': HVACStrategyType.IDEAL_LOADS,
    'coa': HVACStrategyType.FAN_COIL,  # Commercial Office A
    'cob': HVACStrategyType.FAN_COIL,  # Commercial Office B
    'goa': HVACStrategyType.FAN_COIL,  # Government Office A
    'gob': HVACStrategyType.FAN_COIL,  # Government Office B
    'highs': HVACStrategyType.FAN_COIL,  # High Rise Apartment slab type
    'hight': HVACStrategyType.FAN_COIL,  # High Rise Apartment tower type
    'inp': HVACStrategyType.FAN_COIL,  # Inpatient
    'lh': HVACStrategyType.FAN_COIL,  # Large Hotel
    'sh': HVACStrategyType.FAN_COIL,  # Small Hotel
    'low': HVACStrategyType.FAN_COIL,  # Low Rise Apartment
    'mall': HVACStrategyType.FAN_COIL,  # Shopping Mall
    'outp': HVACStrategyType.FAN_COIL,  # Outpatient
    'sch': HVACStrategyType.FAN_COIL,  # Primary/secondary school
    'th': HVACStrategyType.FAN_COIL,  # Terraced House
    'uni': HVACStrategyType.FAN_COIL,  # University
}
