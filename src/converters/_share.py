from enum import StrEnum
from typing import Final


class HVACStrategyType(StrEnum):
    IDEAL_LOADS = 'ideal-loads'
    PTHP = 'pthp'
    VRF = 'vrf'
    FAN_COIL = 'fan-coil'


BUILDING_HVAC_MAP: Final[dict[str, HVACStrategyType]] = {
    'default': HVACStrategyType.IDEAL_LOADS,
    'coa': HVACStrategyType.VRF,  # Commercial Office A
    'cob': HVACStrategyType.VRF,  # Commercial Office B
    'goa': HVACStrategyType.VRF,  # Government Office A
    'gob': HVACStrategyType.VRF,  # Government Office B
    'highs': HVACStrategyType.PTHP,  # High Rise Apartment slab type
    'hight': HVACStrategyType.PTHP,  # High Rise Apartment tower type
    'inp': HVACStrategyType.VRF,  # Inpatient
    'lh': HVACStrategyType.FAN_COIL,  # Large Hotel
    'sh': HVACStrategyType.PTHP,  # Small Hotel
    'low': HVACStrategyType.PTHP,  # Low Rise Apartment
    'mall': HVACStrategyType.VRF,  # Shopping Mall
    'outp': HVACStrategyType.VRF,  # Outpatient
    'sch': HVACStrategyType.FAN_COIL,  # Primary/secondary school
    'th': HVACStrategyType.PTHP,  # Terraced House
    'uni': HVACStrategyType.FAN_COIL,  # University
}
