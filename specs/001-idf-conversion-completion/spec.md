# Feature Specification: IDF Conversion Completion

**Feature Branch**: `001-idf-conversion-completion`
**Created**: 2026-01-26
**Status**: Draft
**Input**: User description: "完成DeST到EnergyPlus IDF转换，实现热收益、简化HVAC、通风系统和日程表自动收集"

## Clarifications

### Session 2026-01-27
- Q: HVAC对象类型命名确认 → A: 使用HVACTemplate:Zone:IdealLoadsAirSystem（非ZoneHVAC:IdealLoadsAirSystem），模型定义完整
- Q: IDF模型文件约束 → A: src/idf/models目录不允许修改，所有模型定义已完整且正确（自动生成自EnergyPlus schema）
- Q: FR-008与HVACTemplate使用模式冲突，是否需要手动创建ZoneHVAC:EquipmentList等对象？ → A: 移除FR-008，HVACTemplate在EnergyPlus运行时自动展开为底层对象

### Session 2026-01-26
- Q: 新风量单位转换策略：DeST使用m³/h，EnergyPlus使用m³/s，如何处理？ → A: 自动转换（m³/h ÷ 3600 = m³/s），在转换器内部处理
- Q: 人员散湿量(damp_per_person)如何处理？EnergyPlus People对象无直接对应字段 → A: 忽略该参数，使用EnergyPlus内置的代谢率-潜热模型
- Q: 人员代谢热量(heat_per_person)如何映射到EnergyPlus Activity Level？ → A: 直接使用heat_per_person(W/person)作为Activity Level Schedule值
- Q: 设备湿负荷(max_hum/min_hum)如何处理？EnergyPlus ElectricEquipment无直接对应字段 → A: 忽略，设备湿负荷在简化模拟中可忽略
- Q: 新风量数据来源：Room.min_fresh_flow_num vs OccupantGains.min_require_fresh_air？ → A: 优先使用Room.min_fresh_flow_num，若无则用min_require_fresh_air×人数计算

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Internal Gains Conversion (Priority: P1)

用户需要将DeST模型中的内部热收益数据（人员、照明、设备）完整转换到EnergyPlus IDF文件中，以便进行准确的建筑能耗模拟。

**Why this priority**: 内部热收益是建筑能耗模拟的核心输入，直接影响空调负荷计算和能耗预测的准确性。没有内部热收益数据，模拟结果将严重失真。

**Independent Test**: 可通过转换包含人员、照明、设备数据的DeST文件，验证生成的IDF包含正确的People、Lights、ElectricEquipment对象。

**Acceptance Scenarios**:

1. **Given** DeST数据库包含房间的OccupantGains数据, **When** 执行转换, **Then** IDF文件包含对应的People对象，人员密度(人/m²)和日程表正确关联
2. **Given** DeST数据库包含房间的LightGains数据, **When** 执行转换, **Then** IDF文件包含对应的Lights对象，功率密度(W/m²)正确转换
3. **Given** DeST数据库包含房间的EquipmentGains数据, **When** 执行转换, **Then** IDF文件包含对应的ElectricEquipment对象，功率密度(W/m²)正确转换
4. **Given** 热收益数据关联日程表, **When** 执行转换, **Then** 日程表被自动收集并转换

---

### User Story 2 - Simplified HVAC System (Priority: P2)

用户需要为建筑模型添加简化的HVAC系统，使用IdealLoadsAirSystem来降低复杂度，同时保证模拟可运行。

**Why this priority**: HVAC系统是完整能耗模拟的必要组成部分，但详细HVAC建模复杂度极高。IdealLoadsAirSystem提供了合理的简化方案，可快速获得有意义的模拟结果。

**Independent Test**: 可通过转换任意DeST文件，验证每个Zone都配置了IdealLoadsAirSystem，模拟可成功运行。

**Acceptance Scenarios**:

1. **Given** DeST数据库包含多个房间, **When** 执行转换, **Then** 每个Zone关联一个HVACTemplate:Zone:IdealLoadsAirSystem对象
2. **Given** Zone配置了IdealLoadsAirSystem, **When** 在EnergyPlus中运行模拟, **Then** 模拟成功完成，无HVAC相关错误
3. **Given** RoomGroup包含set_t_min_schedule/set_t_max_schedule设置, **When** 执行转换, **Then** IdealLoadsAirSystem使用对应的温度设定点日程表(°C)

---

### User Story 3 - Outdoor Air/Ventilation Conversion (Priority: P3)

用户需要将DeST中的新风量数据转换到IDF中，以准确反映建筑的新风需求。

**Why this priority**: 新风量影响室内空气品质和能耗，是建筑性能模拟的重要组成部分。

**Independent Test**: 可通过转换包含新风量参数的DeST文件，验证IDF中包含正确的新风配置。

**Acceptance Scenarios**:

1. **Given** Room包含min_fresh_flow_num数据(m³/h), **When** 执行转换, **Then** IdealLoadsAirSystem的新风量设置正确配置
2. **Given** 房间有设定的新风量需求, **When** 执行转换, **Then** 新风量(m³/h)正确转换到IDF对象中
3. **Given** 新风数据关联日程表, **When** 执行转换, **Then** 新风日程表被自动收集并转换

---

### User Story 4 - Automatic Schedule Collection (Priority: P2)

用户需要系统自动识别和收集所有被热收益、HVAC、新风等对象引用的日程表，无需手动指定。

**Why this priority**: 手动管理日程表依赖容易遗漏，导致模拟失败。自动收集可确保所有必要的日程表都被转换。

**Independent Test**: 可通过转换包含多种日程表引用的DeST文件，验证所有被引用的日程表都自动出现在IDF中。

**Acceptance Scenarios**:

1. **Given** People对象引用了occupation日程表, **When** 执行转换, **Then** 该日程表自动包含在IDF输出中
2. **Given** Lights对象引用了lighting日程表, **When** 执行转换, **Then** 该日程表自动包含在IDF输出中
3. **Given** IdealLoadsAirSystem引用温度设定日程表, **When** 执行转换, **Then** 该日程表自动包含在IDF输出中
4. **Given** 多个对象引用同一日程表, **When** 执行转换, **Then** 日程表仅转换一次，不重复

---

### User Story 5 - Door Interface Preservation (Priority: P4)

保留门转换器的接口，便于后续实现，但当前不进行实际转换。

**Why this priority**: 门对能耗模拟影响较小，可作为低优先级后续工作。保留接口确保架构完整性。

**Independent Test**: 可验证FenestrationConverter对门数据不会抛出错误，仅跳过处理。

**Acceptance Scenarios**:

1. **Given** DeST数据库包含Door数据, **When** 执行转换, **Then** 转换器跳过门数据，不产生错误
2. **Given** 门转换器被调用, **When** 检查转换统计, **Then** 门被记录为skipped状态

---

### Edge Cases

- 房间没有任何内部热收益数据时，该Zone不生成People/Lights/Equipment对象（正常跳过）
- 日程表数据不完整（少于8760小时）时，抛出错误
- 多个房间共享同一套热收益参数时，各自生成独立的热收益对象
- Room.min_fresh_flow_num为0或空时，不配置新风设置（正常跳过）
- RoomGroup没有温度设定日程表时，抛出错误
- 必要参数缺失时（如maxpower、maxnumber等），抛出错误并报告具体缺失字段

## Requirements *(mandatory)*

### Functional Requirements

**内部热收益转换**:
- **FR-001**: System MUST 将OccupantGains转换为People对象，包含以下参数：
  - maxnumber (人/m²): 最大人员密度
  - minnumber (人/m²): 最小人员密度
  - heat_per_person (W/person): 直接作为Activity Level Schedule值（无需单位转换）
  - schedule: 人员日程表引用
  - 注：damp_per_person被忽略，使用EnergyPlus内置代谢率-潜热模型
- **FR-002**: System MUST 将LightGains转换为Lights对象，包含以下参数：
  - maxpower (W/m²): 最大照明功率密度
  - minpower (W/m²): 最小照明功率密度
  - heat_rate: 散热率
  - schedule: 照明日程表引用
- **FR-003**: System MUST 将EquipmentGains转换为ElectricEquipment对象，包含以下参数：
  - maxpower (W/m²): 最大设备功率密度
  - minpower (W/m²): 最小设备功率密度
  - schedule: 设备日程表引用
  - 注：max_hum/min_hum被忽略，设备湿负荷在简化模拟中可忽略
- **FR-004**: System MUST 自动关联热收益对象与对应的Zone

**简化HVAC系统**:
- **FR-005**: System MUST 为每个Zone创建HVACTemplate:Zone:IdealLoadsAirSystem对象
- **FR-006**: System MUST 使用RoomGroup的set_t_min_schedule作为供暖设定点日程表(°C)
- **FR-007**: System MUST 使用RoomGroup的set_t_max_schedule作为制冷设定点日程表(°C)
- ~~**FR-008**: (已移除) HVACTemplate对象在EnergyPlus运行时自动展开为底层HVAC对象，无需手动创建ZoneHVAC:EquipmentList等~~

**新风/通风系统**:
- **FR-009**: System MUST 按以下优先级确定新风量：
  1. 优先使用Room.min_fresh_flow_num (m³/h)
  2. 若Room.min_fresh_flow_num为空/0，则使用OccupantGains.min_require_fresh_air × maxnumber × area计算
- **FR-010**: System MUST 自动执行单位转换（m³/h ÷ 3600 = m³/s）后配置到IdealLoadsAirSystem

**日程表收集**:
- **FR-011**: System MUST 通过LookupTable自动追踪所有被引用的日程表ID
- **FR-012**: System MUST 在转换完成后自动转换所有被收集的日程表
- **FR-013**: System MUST 避免重复转换相同的日程表

**错误处理**:
- **FR-014**: System MUST 在必要参数缺失时抛出错误并报告具体缺失字段
- **FR-015**: System MUST 在日程表数据不完整时抛出错误

**门接口**:
- **FR-016**: System MUST 保留Door转换接口，当前实现返回跳过状态

### Key Entities

- **OccupantGains (DeST)**: 人员热收益数据源
  - maxnumber (人/m²): 最大人员密度
  - minnumber (人/m²): 最小人员密度
  - heat_per_person (W/person): 人均显热散热量 → 映射到Activity Level Schedule
  - damp_per_person (g/h·person): 人均散湿量（忽略，使用EnergyPlus内置模型）
  - min_require_fresh_air (m³/h·person): 人均最小新风量

- **LightGains (DeST)**: 照明热收益数据源
  - maxpower (W/m²): 最大照明功率密度
  - minpower (W/m²): 最小照明功率密度
  - heat_rate: 散热率

- **EquipmentGains (DeST)**: 设备热收益数据源
  - maxpower (W/m²): 最大设备功率密度
  - minpower (W/m²): 最小设备功率密度

- **Room (DeST)**: 房间数据
  - min_fresh_flow_num (m³/h): 最小新风流量
  - area (m²): 房间面积
  - volume (m³): 房间体积

- **People (EnergyPlus)**: 人员对象，人员密度(人/m²)、代谢率
- **Lights (EnergyPlus)**: 照明对象，功率密度(W/m²)
- **ElectricEquipment (EnergyPlus)**: 设备对象，功率密度(W/m²)
- **HVACTemplate:Zone:IdealLoadsAirSystem (EnergyPlus)**: 简化HVAC系统，支持新风和温度设定
- **LookupTable.SCHEDULE_TO_NAME**: 日程表ID到IDF名称的映射表

## Technical Constraints

- **TC-001**: `src/idf/models/` 目录下的所有模型文件**不允许修改**。这些模型是从 EnergyPlus schema (v25.1) 自动生成的，定义完整且正确。转换器实现必须适配现有模型接口。
- **TC-002**: 技术栈：Python >= 3.12 + Pydantic 2.x, SQLAlchemy 2.x, Loguru, Typer

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 包含热收益数据的DeST文件转换后，IDF文件包含正确数量的People、Lights、ElectricEquipment对象
- **SC-002**: 转换后的IDF文件可在EnergyPlus中成功运行完整年度模拟
- **SC-003**: 所有被热收益、HVAC、新风对象引用的日程表100%自动转换，无遗漏
- **SC-004**: 必要参数缺失时，转换过程抛出明确的错误信息，指明缺失字段
- **SC-005**: 每个Zone的IdealLoadsAirSystem配置完整，模拟时无"missing object"错误
