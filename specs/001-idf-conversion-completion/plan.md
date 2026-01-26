# Implementation Plan: IDF Conversion Completion

**Branch**: `001-idf-conversion-completion` | **Date**: 2026-01-26 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-idf-conversion-completion/spec.md`

## Summary

完成 DeST 到 EnergyPlus IDF 转换的核心功能：实现内部热收益（人员、照明、设备）转换器，配置简化 HVAC 系统（IdealLoadsAirSystem），处理新风/通风系统，以及自动收集所有被引用的日程表。基于现有的 BaseConverter + ConverterManager + LookupTable 架构进行扩展。

## Technical Context

**Language/Version**: Python >= 3.12
**Primary Dependencies**: Pydantic 2.x, SQLAlchemy 2.x, Loguru, Typer
**Storage**: MS Access (.accdb) via UCanAccess/JDBC → SQLite (内存)
**Testing**: N/A
**Target Platform**: Linux/Windows CLI
**Project Type**: Single project (CLI 工具)
**Performance Goals**: N/A (批处理转换)
**Constraints**: 输出 IDF 文件必须在 EnergyPlus 中成功运行模拟
**Scale/Scope**: 单建筑模型转换（数百个 Zone）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Modern Python Syntax**: Uses Python 3.12+ features (`X | Y`, `list[T]`, `dict[K, V]`)
- [x] **No Over-Abstraction**: No unnecessary wrappers; direct library API usage (使用现有 BaseConverter 架构)
- [x] **SOTA Libraries First**: 使用 Pydantic (验证), SQLAlchemy (ORM), Loguru (日志)
- [x] **Clean Code**: No inline comments; self-documenting names
- [x] **Conventional Commits**: Commit messages follow `<type>(<scope>): <description>`
- [x] **Fail-Fast**: Exceptions raised early with clear context (现有转换器已遵循此模式)

## Project Structure

### Documentation (this feature)

```text
specs/001-idf-conversion-completion/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (N/A - 无 API)
└── tasks.md             # Phase 2 output (由 /speckit.tasks 生成)
```

### Source Code (repository root)

```text
src/
├── converters/           # 转换器核心模块
│   ├── base.py              # BaseConverter 抽象基类 (已存在)
│   ├── manager.py           # ConverterManager + LookupTable (已存在)
│   ├── internal_gains.py    # [新建] 内部热收益转换器
│   ├── hvac.py              # [新建] IdealLoadsAirSystem 转换器
│   └── schedule.py          # 日程表转换器 (已存在，需扩展)
├── database/models/
│   ├── gains.py             # OccupantGains, LightGains, EquipmentGains (已存在)
│   └── building.py          # Room, RoomGroup (已存在)
└── idf/models/
    ├── internal_gains.py    # People, Lights, ElectricEquipment (已存在)
    ├── zone_forced_air.py   # ZoneHVACIdealLoadsAirSystem (已存在)
    └── zone_equipment.py    # ZoneHVACEquipmentList/Connections (已存在)
```

**Structure Decision**: 遵循现有 Single project 结构，新转换器放置在 `src/converters/` 目录下，遵循现有命名和架构模式。

## Complexity Tracking

> 无宪法违规需要记录。所有实现将遵循现有架构模式。

## Phase 0: Research Summary

### R-001: EnergyPlus IdealLoadsAirSystem 最佳实践

**Decision**: 使用 ZoneHVAC:IdealLoadsAirSystem 配合 ThermostatSetpoint:DualSetpoint

**Rationale**:
- IdealLoadsAirSystem 是 EnergyPlus 中最简单的 HVAC 系统，无需详细建模管道、风机等
- 适合负荷计算和能耗估算阶段使用
- 支持独立的供暖/制冷设定点温度日程表

**Alternatives considered**:
- HVACTemplate:Zone:IdealLoadsAirSystem: 更简单但灵活性较低
- Detailed HVAC: 过于复杂，不符合 "简化 HVAC" 需求

### R-002: 新风量单位转换

**Decision**: 在转换器内部自动执行 m³/h → m³/s 转换 (÷3600)

**Rationale**:
- DeST 使用 m³/h (中国标准)
- EnergyPlus 内部使用 m³/s (SI 单位)
- 转换逻辑封装在转换器内，对外透明

**Implementation**:
```python
outdoor_air_flow_rate_m3_per_s = outdoor_air_flow_rate_m3_per_h / 3600
```

### R-003: 人员代谢热量处理

**Decision**: 使用 Schedule:Constant 设置 Activity Level

**Rationale**:
- DeST `heat_per_person` 直接映射为 EnergyPlus Activity Level (W/person)
- Activity Level Schedule 值 = heat_per_person
- 无需单位转换

**Implementation approach**:
```python
activity_schedule_name = f"ActivityLevel_{people_name}"
activity_schedule = ScheduleConstant(
    name=activity_schedule_name,
    schedule_type_limits_name="Any Number",
    hourly_value=heat_per_person
)
```

### R-004: 日程表自动收集机制

**Decision**: 扩展现有 LookupTable.REQUIRED_SCHEDULE_IDS 机制

**Rationale**:
- 现有 ScheduleConverter 已支持仅转换被标记为 required 的日程表
- 新转换器只需在使用日程表时调用 `lookup_table.REQUIRED_SCHEDULE_IDS.add(schedule_id)`
- 无需修改 ScheduleConverter 核心逻辑

### R-005: Zone HVAC Equipment 配置

**Decision**: 为每个 Zone 创建完整的 HVAC 配置三元组

**Rationale**:
- EnergyPlus 要求: Zone → EquipmentConnections → EquipmentList → IdealLoadsAirSystem
- 必须正确设置节点名称以建立连接

**Configuration pattern**:
```
Zone: "Zone_123"
  ├─ ZoneHVAC:EquipmentConnections
  │   ├─ zone_name: "Zone_123"
  │   ├─ equipment_list_name: "Zone_123_EquipmentList"
  │   ├─ zone_air_inlet_node: "Zone_123_Inlet"
  │   ├─ zone_air_node_name: "Zone_123_AirNode"
  │   └─ zone_return_air_node: "Zone_123_Return"
  ├─ ZoneHVAC:EquipmentList
  │   ├─ name: "Zone_123_EquipmentList"
  │   └─ equipment[0]: (IdealLoadsAirSystem, "Zone_123_IdealLoads", 1, 1)
  └─ ZoneHVAC:IdealLoadsAirSystem
      ├─ name: "Zone_123_IdealLoads"
      ├─ zone_supply_air_node_name: "Zone_123_Inlet"
      └─ heating/cooling_setpoint_schedule_name: from RoomGroup
```

### R-006: 温度设定点日程表

**Decision**: 使用 ThermostatSetpoint:DualSetpoint + ZoneControl:Thermostat

**Rationale**:
- IdealLoadsAirSystem 需要设定点来控制供暖/制冷
- 设定点来自 RoomGroup.set_t_min_schedule (供暖) 和 set_t_max_schedule (制冷)
- DualSetpoint 支持独立的供暖/制冷温度控制

**Configuration pattern**:
```
ThermostatSetpoint:DualSetpoint
  ├─ name: "Zone_123_DualSetpoint"
  ├─ heating_setpoint_schedule: from RoomGroup.set_t_min_schedule
  └─ cooling_setpoint_schedule: from RoomGroup.set_t_max_schedule

ZoneControl:Thermostat
  ├─ name: "Zone_123_Thermostat"
  ├─ zone_name: "Zone_123"
  ├─ control_type_schedule: "Always On" (常量=4)
  └─ control_1_object_name: "Zone_123_DualSetpoint"
```

## Phase 1: Data Model

详见 [data-model.md](data-model.md)

## Phase 1: Contracts

本项目为 CLI 工具，无 API 接口。跳过 contracts/ 生成。

## Phase 1: Quickstart

详见 [quickstart.md](quickstart.md)

## Next Steps

运行 `/speckit.tasks` 生成详细的实现任务列表。
