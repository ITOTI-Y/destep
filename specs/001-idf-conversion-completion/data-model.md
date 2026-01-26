# Data Model: IDF Conversion Completion

**Feature**: 001-idf-conversion-completion
**Date**: 2026-01-26

## Overview

本文档定义了 DeST 到 EnergyPlus IDF 转换中涉及的数据实体、字段映射和验证规则。

---

## Source Entities (DeST)

### OccupantGains

**Source**: `src/database/models/gains.py`
**Table**: `OccupantGains`

| Field | Type | Description | Required | Validation |
|-------|------|-------------|----------|------------|
| id | int | Primary key | ✅ | - |
| maxnumber | float | 最大人员密度 (人/m²) | ✅ | > 0 |
| minnumber | float | 最小人员密度 (人/m²) | ❌ | ≥ 0 |
| heat_per_person | float | 人均显热散热量 (W/person) | ✅ | > 0, typical: 60-150 |
| damp_per_person | float | 人均散湿量 (g/h·person) | ❌ | **忽略** |
| min_require_fresh_air | float | 人均最小新风量 (m³/h·person) | ❌ | ≥ 0 |
| schedule_id | int | FK → ScheduleYear | ✅ | - |

### LightGains

**Source**: `src/database/models/gains.py`
**Table**: `LightGains`

| Field | Type | Description | Required | Validation |
|-------|------|-------------|----------|------------|
| id | int | Primary key | ✅ | - |
| maxpower | float | 最大照明功率密度 (W/m²) | ✅ | > 0 |
| minpower | float | 最小照明功率密度 (W/m²) | ❌ | ≥ 0 |
| heat_rate | float | 散热率 (0-1) | ❌ | 0-1 |
| schedule_id | int | FK → ScheduleYear | ✅ | - |

### EquipmentGains

**Source**: `src/database/models/gains.py`
**Table**: `EquipmentGains`

| Field | Type | Description | Required | Validation |
|-------|------|-------------|----------|------------|
| id | int | Primary key | ✅ | - |
| maxpower | float | 最大设备功率密度 (W/m²) | ✅ | > 0 |
| minpower | float | 最小设备功率密度 (W/m²) | ❌ | ≥ 0 |
| max_hum | float | 最大湿负荷 | ❌ | **忽略** |
| min_hum | float | 最小湿负荷 | ❌ | **忽略** |
| schedule_id | int | FK → ScheduleYear | ✅ | - |

### Room

**Source**: `src/database/models/building.py`
**Table**: `Room`

| Field | Type | Description | Required | Validation |
|-------|------|-------------|----------|------------|
| id | int | Primary key | ✅ | - |
| name | str | 房间名称 | ❌ | - |
| of_room_group | int | FK → RoomGroup | ✅ | - |
| area | float | 房间面积 (m²) | ✅ | > 0 |
| volume | float | 房间体积 (m³) | ✅ | > 0 |
| min_fresh_flow_num | float | 最小新风流量 (m³/h) | ❌ | ≥ 0 |

**Relationships**:
- `occupant_gains`: 1:N → OccupantGains
- `light_gains`: 1:N → LightGains
- `equipment_gains`: 1:N → EquipmentGains
- `room_group`: N:1 → RoomGroup

### RoomGroup

**Source**: `src/database/models/building.py`
**Table**: `RoomGroup`

| Field | Type | Description | Required | Validation |
|-------|------|-------------|----------|------------|
| id | int | Primary key | ✅ | - |
| set_t_min_schedule_id | int | FK → ScheduleYear (供暖设定点) | ✅ | **Error if missing** |
| set_t_max_schedule_id | int | FK → ScheduleYear (制冷设定点) | ✅ | **Error if missing** |
| ac_schedule_id | int | FK → ScheduleYear (空调可用性) | ❌ | - |

---

## Target Entities (EnergyPlus IDF)

### People

**Source**: `src/idf/models/internal_gains.py`
**IDF Object**: `People`

| Field | Type | Default | Mapping |
|-------|------|---------|---------|
| name | str | - | `People_{zone_name}` |
| zone_or_zonelist_or_space_or_spacelist_name | str | - | Zone name from LookupTable |
| number_of_people_schedule_name | str | - | Schedule from OccupantGains.schedule_id |
| number_of_people_calculation_method | str | - | `"People/Area"` |
| people_per_floor_area | float | - | OccupantGains.maxnumber |
| fraction_radiant | float | 0.3 | Fixed |
| sensible_heat_fraction | str | "Autocalculate" | Fixed |
| activity_level_schedule_name | str | - | `ActivityLevel_{zone_name}` (常量=heat_per_person) |

### Lights

**Source**: `src/idf/models/internal_gains.py`
**IDF Object**: `Lights`

| Field | Type | Default | Mapping |
|-------|------|---------|---------|
| name | str | - | `Lights_{zone_name}` |
| zone_or_zonelist_or_space_or_spacelist_name | str | - | Zone name from LookupTable |
| schedule_name | str | - | Schedule from LightGains.schedule_id |
| design_level_calculation_method | str | - | `"Watts/Area"` |
| watts_per_floor_area | float | - | LightGains.maxpower |
| fraction_radiant | float | 0.0 | Fixed (可由 heat_rate 调整) |
| fraction_visible | float | 0.0 | Fixed |
| return_air_fraction | float | 0.0 | Fixed |

### ElectricEquipment

**Source**: `src/idf/models/internal_gains.py`
**IDF Object**: `ElectricEquipment`

| Field | Type | Default | Mapping |
|-------|------|---------|---------|
| name | str | - | `Equipment_{zone_name}` |
| zone_or_zonelist_or_space_or_spacelist_name | str | - | Zone name from LookupTable |
| schedule_name | str | - | Schedule from EquipmentGains.schedule_id |
| design_level_calculation_method | str | - | `"Watts/Area"` |
| watts_per_floor_area | float | - | EquipmentGains.maxpower |
| fraction_latent | float | 0.0 | Fixed |
| fraction_radiant | float | 0.0 | Fixed |
| fraction_lost | float | 0.0 | Fixed |

### ZoneHVACIdealLoadsAirSystem

**Source**: `src/idf/models/zone_forced_air.py`
**IDF Object**: `ZoneHVAC:IdealLoadsAirSystem`

| Field | Type | Default | Mapping |
|-------|------|---------|---------|
| name | str | - | `{zone_name}_IdealLoads` |
| availability_schedule_name | str | None | Optional: RoomGroup.ac_schedule_id |
| zone_supply_air_node_name | str | - | `{zone_name}_Inlet` |
| zone_exhaust_air_node_name | str | None | - |
| maximum_heating_supply_air_temperature | float | 50.0 | Fixed (°C) |
| minimum_cooling_supply_air_temperature | float | 13.0 | Fixed (°C) |
| heating_limit | str | "NoLimit" | Fixed |
| cooling_limit | str | "NoLimit" | Fixed |
| outdoor_air_inlet_node_name | str | None | `{zone_name}_OAInlet` (if fresh air > 0) |
| design_specification_outdoor_air_object_name | str | None | `{zone_name}_DSOA` (if fresh air > 0) |

### DesignSpecificationOutdoorAir

**Source**: `src/idf/models/zone_equipment.py` (待确认)
**IDF Object**: `DesignSpecification:OutdoorAir`

| Field | Type | Default | Mapping |
|-------|------|---------|---------|
| name | str | - | `{zone_name}_DSOA` |
| outdoor_air_method | str | - | `"Flow/Zone"` |
| outdoor_air_flow_per_zone | float | - | Calculated fresh air (m³/s) |

### ZoneHVACEquipmentList

**Source**: `src/idf/models/zone_equipment.py`
**IDF Object**: `ZoneHVAC:EquipmentList`

| Field | Type | Default | Mapping |
|-------|------|---------|---------|
| name | str | - | `{zone_name}_EquipmentList` |
| load_distribution_scheme | str | "SequentialLoad" | Fixed |
| equipment | list | - | Single item: IdealLoadsAirSystem |

### ZoneHVACEquipmentConnections

**Source**: `src/idf/models/zone_equipment.py`
**IDF Object**: `ZoneHVAC:EquipmentConnections`

| Field | Type | Default | Mapping |
|-------|------|---------|---------|
| zone_name | str | - | Zone name from LookupTable |
| zone_conditioning_equipment_list_name | str | - | `{zone_name}_EquipmentList` |
| zone_air_inlet_node_or_nodelist_name | str | - | `{zone_name}_Inlet` |
| zone_air_exhaust_node_or_nodelist_name | str | None | - |
| zone_air_node_name | str | - | `{zone_name}_AirNode` |
| zone_return_air_node_or_nodelist_name | str | None | `{zone_name}_Return` |

### ThermostatSetpointDualSetpoint

**IDF Object**: `ThermostatSetpoint:DualSetpoint`

| Field | Type | Default | Mapping |
|-------|------|---------|---------|
| name | str | - | `{zone_name}_DualSetpoint` |
| heating_setpoint_temperature_schedule_name | str | - | RoomGroup.set_t_min_schedule |
| cooling_setpoint_temperature_schedule_name | str | - | RoomGroup.set_t_max_schedule |

### ZoneControlThermostat

**IDF Object**: `ZoneControl:Thermostat`

| Field | Type | Default | Mapping |
|-------|------|---------|---------|
| name | str | - | `{zone_name}_Thermostat` |
| zone_or_zonelist_name | str | - | Zone name |
| control_type_schedule_name | str | - | `"AlwaysDual"` (常量=4) |
| control_1_object_type | str | - | `"ThermostatSetpoint:DualSetpoint"` |
| control_1_name | str | - | `{zone_name}_DualSetpoint` |

### ScheduleConstant

**IDF Object**: `Schedule:Constant`

| Field | Type | Default | Mapping |
|-------|------|---------|---------|
| name | str | - | `ActivityLevel_{zone_name}` 或 `AlwaysDual` |
| schedule_type_limits_name | str | - | `"Any Number"` 或 `"Control Type"` |
| hourly_value | float | - | heat_per_person 或 4 |

---

## Field Mapping Summary

### OccupantGains → People

```
OccupantGains.maxnumber      → People.people_per_floor_area
OccupantGains.heat_per_person → ScheduleConstant (Activity Level)
OccupantGains.schedule_id    → People.number_of_people_schedule_name
OccupantGains.damp_per_person → [IGNORED]
```

### LightGains → Lights

```
LightGains.maxpower    → Lights.watts_per_floor_area
LightGains.heat_rate   → Lights.fraction_radiant (optional)
LightGains.schedule_id → Lights.schedule_name
```

### EquipmentGains → ElectricEquipment

```
EquipmentGains.maxpower    → ElectricEquipment.watts_per_floor_area
EquipmentGains.schedule_id → ElectricEquipment.schedule_name
EquipmentGains.max_hum     → [IGNORED]
EquipmentGains.min_hum     → [IGNORED]
```

### Room → Fresh Air Configuration

```
Room.min_fresh_flow_num (优先级1)
  OR
OccupantGains.min_require_fresh_air × maxnumber × area (优先级2)
  ↓ (÷3600)
DesignSpecificationOutdoorAir.outdoor_air_flow_per_zone (m³/s)
```

### RoomGroup → Thermostat Configuration

```
RoomGroup.set_t_min_schedule → ThermostatSetpoint:DualSetpoint.heating_setpoint_schedule
RoomGroup.set_t_max_schedule → ThermostatSetpoint:DualSetpoint.cooling_setpoint_schedule
RoomGroup.ac_schedule_id     → IdealLoadsAirSystem.availability_schedule_name (optional)
```

---

## Validation Rules

### Error Conditions (Fail-Fast)

| Condition | Error Message |
|-----------|---------------|
| OccupantGains.maxnumber is None/0 | `"OccupantGains {id} missing required field: maxnumber"` |
| LightGains.maxpower is None/0 | `"LightGains {id} missing required field: maxpower"` |
| EquipmentGains.maxpower is None/0 | `"EquipmentGains {id} missing required field: maxpower"` |
| RoomGroup.set_t_min_schedule_id is None | `"RoomGroup {id} missing required heating setpoint schedule"` |
| RoomGroup.set_t_max_schedule_id is None | `"RoomGroup {id} missing required cooling setpoint schedule"` |
| Schedule data < 8760 hours | `"Schedule {id} incomplete: expected 8760 hours, got {n}"` |

### Skip Conditions (No Error)

| Condition | Behavior |
|-----------|----------|
| Room has no OccupantGains | Skip People generation, log info |
| Room has no LightGains | Skip Lights generation, log info |
| Room has no EquipmentGains | Skip ElectricEquipment generation, log info |
| Room.min_fresh_flow_num is 0/None AND no OccupantGains | Skip fresh air config, log info |

---

## State Transitions

本功能不涉及状态机。所有转换为单次批处理操作。

---

## Entity Relationships Diagram

```
┌─────────────┐    1:N    ┌────────────────┐
│   Room      │ ─────────→│  OccupantGains │
│             │           └────────────────┘
│             │    1:N    ┌────────────────┐
│             │ ─────────→│   LightGains   │
│             │           └────────────────┘
│             │    1:N    ┌────────────────┐
│             │ ─────────→│ EquipmentGains │
│             │           └────────────────┘
│             │    N:1    ┌────────────────┐
│             │ ─────────→│   RoomGroup    │
└─────────────┘           │                │
                          │ set_t_min_schedule ─┐
                          │ set_t_max_schedule ─┼──→ ScheduleYear
                          │ ac_schedule_id ─────┘
                          └────────────────┘
        ↓
        ↓ Conversion
        ↓
┌─────────────┐
│    Zone     │
│  (existing) │
└─────────────┘
      │
      ├──→ People + ScheduleConstant (Activity Level)
      ├──→ Lights
      ├──→ ElectricEquipment
      ├──→ ZoneHVAC:EquipmentConnections
      ├──→ ZoneHVAC:EquipmentList
      ├──→ ZoneHVAC:IdealLoadsAirSystem
      │      └──→ DesignSpecification:OutdoorAir (optional)
      ├──→ ZoneControl:Thermostat
      │      └──→ ThermostatSetpoint:DualSetpoint
      └──→ ScheduleConstant (AlwaysDual, control type=4)
```
