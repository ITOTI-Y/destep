# Research: IDF Conversion Completion

**Feature**: 001-idf-conversion-completion
**Date**: 2026-01-26

## Overview

本文档记录了实现 DeST 到 EnergyPlus IDF 转换（内部热收益、HVAC、新风、日程表）过程中的技术调研结果。

---

## R-001: EnergyPlus IdealLoadsAirSystem 最佳实践

### Context

需要为每个 Zone 配置简化的 HVAC 系统，支持供暖和制冷负荷计算。

### Decision

使用 `ZoneHVAC:IdealLoadsAirSystem` 配合 `ThermostatSetpoint:DualSetpoint` 和 `ZoneControl:Thermostat`。

### Rationale

1. **简单性**: IdealLoadsAirSystem 是 EnergyPlus 中最简单的 HVAC 选项，无需建模风机、管道、盘管等详细组件
2. **适用场景**: 适合负荷计算、概念设计阶段，可提供合理的能耗估算
3. **灵活性**: 支持独立的供暖/制冷设定点、新风配置、除湿控制
4. **兼容性**: 可与 EnergyPlus 所有版本兼容

### Alternatives Considered

| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| HVACTemplate:Zone:IdealLoadsAirSystem | 配置更简单 | 灵活性较低，无法精细控制新风 | 不采用 |
| Detailed HVAC (AHU, VAV, etc.) | 精确建模 | 复杂度过高，超出 "简化 HVAC" 需求 | 不采用 |
| ZoneHVAC:IdealLoadsAirSystem | 简单且灵活 | 需要配置多个对象 | **采用** |

### Implementation Notes

```
Zone
  ├─ ZoneControl:Thermostat (控制类型选择)
  │   └─ ThermostatSetpoint:DualSetpoint (供暖/制冷设定点)
  ├─ ZoneHVAC:EquipmentConnections (节点连接)
  ├─ ZoneHVAC:EquipmentList (设备列表)
  └─ ZoneHVAC:IdealLoadsAirSystem (核心对象)
```

---

## R-002: 新风量单位转换

### Context

DeST 使用 m³/h（符合中国标准 GB 50189），EnergyPlus 内部使用 m³/s（SI 单位）。

### Decision

在转换器内部自动执行单位转换：`m³/s = m³/h ÷ 3600`

### Rationale

1. **透明性**: 单位转换对用户透明，无需手动干预
2. **一致性**: 与现有 UnitConverter (mm→m) 模式一致
3. **准确性**: 避免用户计算错误

### Implementation

```python
def convert_fresh_air_flow(flow_m3_per_h: float) -> float:
    return flow_m3_per_h / 3600
```

### Alternatives Considered

| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| 要求用户预处理 | 无实现成本 | 用户体验差，易出错 | 不采用 |
| 配置文件指定单位 | 灵活 | 过度工程化 | 不采用 |
| 内部自动转换 | 简单可靠 | 无 | **采用** |

---

## R-003: 人员代谢热量处理

### Context

DeST `heat_per_person` 字段表示人均显热散热量（W/person），需要映射到 EnergyPlus 的 Activity Level。

### Decision

使用 `Schedule:Constant` 创建常量日程表表示 Activity Level。

### Rationale

1. **直接映射**: EnergyPlus Activity Level 单位也是 W/person，无需转换
2. **简单实现**: 使用常量日程表避免创建复杂的小时值日程表
3. **语义一致**: DeST 假设代谢热量恒定，常量日程表准确反映这一假设

### Implementation

```python
activity_schedule = ScheduleConstant(
    name=f"ActivityLevel_{zone_name}",
    schedule_type_limits_name="Any Number",
    hourly_value=occupant_gains.heat_per_person
)

people = People(
    name=f"People_{zone_name}",
    activity_level_schedule_name=activity_schedule.name,
    ...
)
```

### Alternatives Considered

| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| 硬编码默认值 (120W) | 简单 | 丢失 DeST 数据 | 不采用 |
| Schedule:Compact | 更紧凑 | 语法复杂，易出错 | 不采用 |
| Schedule:Constant | 最简单，语义清晰 | 无 | **采用** |

---

## R-004: 日程表自动收集机制

### Context

系统需要自动识别和收集所有被 People、Lights、Equipment、HVAC 对象引用的日程表。

### Decision

扩展现有 `LookupTable.REQUIRED_SCHEDULE_IDS` 机制。

### Rationale

1. **现有基础**: ScheduleConverter 已实现仅转换被标记的日程表
2. **低耦合**: 各转换器通过 LookupTable 通信，无直接依赖
3. **避免重复**: 多个对象引用同一日程表时自动去重（set 数据结构）

### Implementation

```python
class InternalGainsConverter(BaseConverter[Room]):
    def convert_one(self, room: Room) -> bool:
        if room.occupant_gains:
            schedule_id = room.occupant_gains.schedule_id
            self.lookup_table.REQUIRED_SCHEDULE_IDS.add(schedule_id)
            ...
```

### Alternatives Considered

| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| 预扫描所有日程表引用 | 集中处理 | 需要额外遍历，复杂 | 不采用 |
| 即时转换日程表 | 立即完成 | 可能重复转换 | 不采用 |
| 标记后统一转换 | 简单，利用现有机制 | 无 | **采用** |

---

## R-005: Zone HVAC Equipment 配置

### Context

EnergyPlus 要求 Zone 与 HVAC 设备之间有明确的连接关系，通过节点（Node）建立。

### Decision

为每个 Zone 创建完整的 HVAC 配置三元组：EquipmentConnections + EquipmentList + IdealLoadsAirSystem。

### Rationale

1. **完整性**: EnergyPlus 运行要求这三个对象同时存在
2. **命名规范**: 使用一致的命名模式便于调试和理解
3. **节点一致性**: 确保节点名称在相关对象间匹配

### Implementation Pattern

```
Zone: "Zone_{room_id}[_{pinyin}]"

节点命名:
  - Zone Air Inlet Node: "{zone_name}_Inlet"
  - Zone Air Node: "{zone_name}_AirNode"
  - Zone Return Air Node: "{zone_name}_Return"

对象命名:
  - EquipmentList: "{zone_name}_EquipmentList"
  - EquipmentConnections: "{zone_name}_EquipmentConnections"
  - IdealLoadsAirSystem: "{zone_name}_IdealLoads"
```

---

## R-006: 温度设定点日程表

### Context

IdealLoadsAirSystem 需要温度设定点来控制供暖和制冷。DeST 通过 RoomGroup 定义温度设定日程表。

### Decision

使用 `ThermostatSetpoint:DualSetpoint` + `ZoneControl:Thermostat` 配置温度控制。

### Rationale

1. **双设定点**: DualSetpoint 支持独立的供暖/制冷温度
2. **日程表驱动**: 直接引用 RoomGroup 中的日程表 ID
3. **标准做法**: 这是 EnergyPlus 中最常见的 HVAC 控制配置

### Implementation

```python
dual_setpoint = ThermostatSetpointDualSetpoint(
    name=f"{zone_name}_DualSetpoint",
    heating_setpoint_temperature_schedule_name=heating_schedule_name,
    cooling_setpoint_temperature_schedule_name=cooling_schedule_name
)

thermostat = ZoneControlThermostat(
    name=f"{zone_name}_Thermostat",
    zone_or_zonelist_name=zone_name,
    control_type_schedule_name="AlwaysDual",  # 常量=4
    control_1_object_type="ThermostatSetpoint:DualSetpoint",
    control_1_name=dual_setpoint.name
)
```

### Schedule for Control Type

需要一个常量日程表值为 4（DualSetPointWithDeadBand）：

```python
always_dual_schedule = ScheduleConstant(
    name="AlwaysDual",
    schedule_type_limits_name="Control Type",
    hourly_value=4
)
```

---

## R-007: 缺失数据处理策略

### Context

部分 Room 可能没有完整的热收益数据或 HVAC 设定点。

### Decision

采用 Fail-Fast 策略，遵循宪法原则 VI。

### Handling Rules

| 情况 | 行为 |
|------|------|
| Room 无 OccupantGains | 跳过 People 生成，不报错 |
| Room 无 LightGains | 跳过 Lights 生成，不报错 |
| Room 无 EquipmentGains | 跳过 ElectricEquipment 生成，不报错 |
| RoomGroup 无 set_t_min_schedule | 抛出错误："RoomGroup {id} missing heating setpoint schedule" |
| RoomGroup 无 set_t_max_schedule | 抛出错误："RoomGroup {id} missing cooling setpoint schedule" |
| OccupantGains.maxnumber 为空 | 抛出错误："OccupantGains {id} missing maxnumber" |
| LightGains.maxpower 为空 | 抛出错误："LightGains {id} missing maxpower" |

---

## Summary

| 研究项 | 决定 | 状态 |
|--------|------|------|
| R-001 | 使用 IdealLoadsAirSystem + DualSetpoint | ✅ Resolved |
| R-002 | 内部自动执行 m³/h → m³/s 转换 | ✅ Resolved |
| R-003 | 使用 Schedule:Constant 表示 Activity Level | ✅ Resolved |
| R-004 | 扩展现有 REQUIRED_SCHEDULE_IDS 机制 | ✅ Resolved |
| R-005 | 创建完整的 HVAC 配置三元组 | ✅ Resolved |
| R-006 | 使用 DualSetpoint + ZoneControl:Thermostat | ✅ Resolved |
| R-007 | 采用 Fail-Fast 策略处理缺失数据 | ✅ Resolved |

所有 NEEDS CLARIFICATION 已解决，可进入 Phase 1 设计阶段。
