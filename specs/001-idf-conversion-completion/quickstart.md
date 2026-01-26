# Quickstart: IDF Conversion Completion

**Feature**: 001-idf-conversion-completion
**Date**: 2026-01-26

## Prerequisites

- Python >= 3.12
- uv (package manager)
- EnergyPlus (用于验证生成的 IDF 文件)

## Installation

```bash
# 克隆仓库并进入目录
cd /home/pan/code/destep

# 安装依赖
uv sync
```

## Usage

### 基本转换

```bash
# 转换 DeST 数据库到 IDF
uv run python main.py convert input.accdb output.idf
```

### 转换流程

1. **加载 DeST 数据库**: 读取 .accdb 文件中的建筑数据
2. **几何转换**: Building → Zone → Surface → Fenestration
3. **内部热收益转换** (本功能新增):
   - OccupantGains → People
   - LightGains → Lights
   - EquipmentGains → ElectricEquipment
4. **HVAC 配置** (本功能新增):
   - 为每个 Zone 创建 IdealLoadsAirSystem
   - 配置温度设定点 (ThermostatSetpoint:DualSetpoint)
   - 配置新风系统 (DesignSpecification:OutdoorAir)
5. **日程表收集**: 自动转换所有被引用的日程表

## 转换器执行顺序

```
BuildingConverter       → Building, SiteLocation
ConstructionConverter   → Construction, Material
ZoneConverter          → Zone
SurfaceConverter       → BuildingSurface:Detailed
FenestrationConverter  → FenestrationSurface:Detailed
InternalGainsConverter → People, Lights, ElectricEquipment  [NEW]
HVACConverter          → IdealLoadsAirSystem, EquipmentList [NEW]
ScheduleConverter      → Schedule:File (仅被引用的日程表)
```

## 新增转换器说明

### InternalGainsConverter

将 DeST 内部热收益数据转换为 EnergyPlus 对象。

**输入**: Room 对象及其关联的 OccupantGains, LightGains, EquipmentGains
**输出**: People, Lights, ElectricEquipment, Schedule:Constant (Activity Level)

**映射关系**:
| DeST | EnergyPlus | 单位 |
|------|------------|------|
| OccupantGains.maxnumber | People.people_per_floor_area | 人/m² |
| OccupantGains.heat_per_person | Activity Level Schedule | W/person |
| LightGains.maxpower | Lights.watts_per_floor_area | W/m² |
| EquipmentGains.maxpower | ElectricEquipment.watts_per_floor_area | W/m² |

### HVACConverter

为每个 Zone 配置简化的 HVAC 系统。

**输入**: Room 对象及其关联的 RoomGroup
**输出**:
- ZoneHVAC:IdealLoadsAirSystem
- ZoneHVAC:EquipmentList
- ZoneHVAC:EquipmentConnections
- ZoneControl:Thermostat
- ThermostatSetpoint:DualSetpoint
- DesignSpecification:OutdoorAir (如果有新风需求)

**新风量计算**:
1. 优先使用 `Room.min_fresh_flow_num` (m³/h)
2. 如无，则使用 `OccupantGains.min_require_fresh_air × maxnumber × area` (m³/h)
3. 自动转换为 m³/s (÷3600)

## 示例输出

转换后的 IDF 文件将包含类似以下结构的对象:

```idf
! ========== Internal Gains ==========

People,
    People_Zone_101_bangs,           !- Name
    Zone_101_bangs,                  !- Zone Name
    Schedule_OccupancyRatio,         !- Number of People Schedule Name
    People/Area,                     !- Calculation Method
    ,                                !- Number of People
    0.1,                             !- People per Floor Area {person/m2}
    ,                                !- Floor Area per Person
    0.3,                             !- Fraction Radiant
    Autocalculate,                   !- Sensible Heat Fraction
    ActivityLevel_Zone_101_bangs;    !- Activity Level Schedule Name

Schedule:Constant,
    ActivityLevel_Zone_101_bangs,    !- Name
    Any Number,                      !- Schedule Type Limits Name
    126;                             !- Hourly Value {W/person}

Lights,
    Lights_Zone_101_bangs,           !- Name
    Zone_101_bangs,                  !- Zone Name
    Schedule_LightingRatio,          !- Schedule Name
    Watts/Area,                      !- Design Level Calculation Method
    ,                                !- Lighting Level
    12.0,                            !- Watts per Floor Area {W/m2}
    ,                                !- Watts per Person
    0.0,                             !- Return Air Fraction
    0.0,                             !- Fraction Radiant
    0.0;                             !- Fraction Visible

ElectricEquipment,
    Equipment_Zone_101_bangs,        !- Name
    Zone_101_bangs,                  !- Zone Name
    Schedule_EquipmentRatio,         !- Schedule Name
    Watts/Area,                      !- Design Level Calculation Method
    ,                                !- Design Level
    20.0,                            !- Watts per Floor Area {W/m2}
    ,                                !- Watts per Person
    0.0,                             !- Fraction Latent
    0.0,                             !- Fraction Radiant
    0.0;                             !- Fraction Lost

! ========== HVAC Configuration ==========

ZoneHVAC:IdealLoadsAirSystem,
    Zone_101_bangs_IdealLoads,       !- Name
    ,                                !- Availability Schedule Name
    Zone_101_bangs_Inlet,            !- Zone Supply Air Node Name
    ,                                !- Zone Exhaust Air Node Name
    50,                              !- Maximum Heating Supply Air Temperature {C}
    13,                              !- Minimum Cooling Supply Air Temperature {C}
    0.0156,                          !- Maximum Heating Supply Air Humidity Ratio
    0.0077,                          !- Minimum Cooling Supply Air Humidity Ratio
    NoLimit,                         !- Heating Limit
    ,                                !- Maximum Heating Air Flow Rate
    ,                                !- Maximum Sensible Heating Capacity
    NoLimit,                         !- Cooling Limit
    ,                                !- Maximum Cooling Air Flow Rate
    ,                                !- Maximum Total Cooling Capacity
    ,                                !- Heating Availability Schedule Name
    ,                                !- Cooling Availability Schedule Name
    None,                            !- Dehumidification Control Type
    0.7,                             !- Cooling Sensible Heat Ratio
    None,                            !- Humidification Control Type
    Zone_101_bangs_DSOA,             !- Design Specification Outdoor Air Object Name
    Zone_101_bangs_OAInlet;          !- Outdoor Air Inlet Node Name

DesignSpecification:OutdoorAir,
    Zone_101_bangs_DSOA,             !- Name
    Flow/Zone,                       !- Outdoor Air Method
    ,                                !- Outdoor Air Flow per Person
    ,                                !- Outdoor Air Flow per Floor Area
    0.00833;                         !- Outdoor Air Flow per Zone {m3/s}

ZoneHVAC:EquipmentList,
    Zone_101_bangs_EquipmentList,    !- Name
    SequentialLoad,                  !- Load Distribution Scheme
    ZoneHVAC:IdealLoadsAirSystem,    !- Zone Equipment 1 Object Type
    Zone_101_bangs_IdealLoads,       !- Zone Equipment 1 Name
    1,                               !- Zone Equipment 1 Cooling Priority
    1,                               !- Zone Equipment 1 Heating Priority
    ,                                !- Zone Equipment 1 Sequential Cooling Fraction
    ;                                !- Zone Equipment 1 Sequential Heating Fraction

ZoneHVAC:EquipmentConnections,
    Zone_101_bangs,                  !- Zone Name
    Zone_101_bangs_EquipmentList,    !- Zone Equipment List Name
    Zone_101_bangs_Inlet,            !- Zone Air Inlet Node Name
    ,                                !- Zone Air Exhaust Node Name
    Zone_101_bangs_AirNode,          !- Zone Air Node Name
    Zone_101_bangs_Return;           !- Zone Return Air Node Name

ZoneControl:Thermostat,
    Zone_101_bangs_Thermostat,       !- Name
    Zone_101_bangs,                  !- Zone Name
    AlwaysDual,                      !- Control Type Schedule Name
    ThermostatSetpoint:DualSetpoint, !- Control 1 Object Type
    Zone_101_bangs_DualSetpoint;     !- Control 1 Name

ThermostatSetpoint:DualSetpoint,
    Zone_101_bangs_DualSetpoint,     !- Name
    Schedule_HeatingSetpoint,        !- Heating Setpoint Schedule Name
    Schedule_CoolingSetpoint;        !- Cooling Setpoint Schedule Name

Schedule:Constant,
    AlwaysDual,                      !- Name
    Control Type,                    !- Schedule Type Limits Name
    4;                               !- Hourly Value (DualSetpoint)
```

## 错误处理

| 错误类型 | 原因 | 解决方案 |
|---------|------|---------|
| Missing maxnumber | OccupantGains 缺少人员密度 | 检查 DeST 数据完整性 |
| Missing maxpower | LightGains/EquipmentGains 缺少功率 | 检查 DeST 数据完整性 |
| Missing setpoint schedule | RoomGroup 缺少温度设定点日程表 | 配置 RoomGroup 的 set_t_min/max_schedule |
| Incomplete schedule | 日程表数据不足 8760 小时 | 补全日程表数据 |

## Verification

使用 EnergyPlus 验证生成的 IDF 文件:

```bash
# 使用 EnergyPlus 检查 IDF 语法
energyplus --idd Energy+.idd --idf output.idf --readvars

# 运行完整模拟验证
energyplus -w weather.epw -d output_dir output.idf
```

成功标准:
- 无 Severe 错误
- 无 "missing object" 警告
- 模拟完整运行 8760 小时
