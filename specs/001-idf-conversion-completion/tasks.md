# Tasks: IDF Conversion Completion

**Input**: Design documents from `/specs/001-idf-conversion-completion/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, quickstart.md ✅

**Tests**: Not requested - skipping test tasks

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/` at repository root
- Paths follow existing project structure from plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify existing infrastructure and prepare for new converters

- [X] T001 Verify existing BaseConverter and ConverterManager interfaces in src/converters/base.py and src/converters/manager.py
- [X] T002 [P] Verify existing IDF models in src/idf/models/internal_gains.py (People, Lights, ElectricEquipment)
- [X] T003 [P] Verify existing IDF models in src/idf/models/zone_forced_air.py (ZoneHVACIdealLoadsAirSystem)
- [X] T004 [P] Verify existing IDF models in src/idf/models/zone_equipment.py (ZoneHVACEquipmentList, ZoneHVACEquipmentConnections)
- [X] T005 [P] Verify existing database models in src/database/models/gains.py (OccupantGains, LightGains, EquipmentGains)
- [X] T006 [P] Verify existing database models in src/database/models/building.py (Room, RoomGroup relationships)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Verify existing IDF models and extend LookupTable for schedule collection

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

**Note**: src/idf/models目录不允许修改，所有模型已自动生成自EnergyPlus schema v25.1，定义完整且正确

- [X] T007 Verify ScheduleConstant model exists in src/idf/models/schedules.py (✅ Line 66-72, for Activity Level and AlwaysDual schedules)
- [X] T008 [P] Verify ThermostatSetpointDualSetpoint model exists in src/idf/models/zone_controls.py (✅ Line 26-34)
- [X] T009 [P] Verify ZoneControlThermostat model exists in src/idf/models/zone_controls.py (✅ Line 134-151)
- [X] T010 [P] Verify DesignSpecificationOutdoorAir model exists in src/idf/models/hvac_design.py (✅ Line 45-57)
- [X] T011 Verify LookupTable.REQUIRED_SCHEDULE_IDS set exists in src/converters/manager.py for schedule collection (✅ Line 40-41)

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Internal Gains Conversion (Priority: P1) 🎯 MVP

**Goal**: Convert DeST internal gains (occupant, lighting, equipment) to EnergyPlus People, Lights, ElectricEquipment objects

**Independent Test**: Convert a DeST file with OccupantGains/LightGains/EquipmentGains and verify IDF contains correct People/Lights/ElectricEquipment objects with proper zone associations

### Implementation for User Story 1

- [X] T012 [US1] Create InternalGainsConverter class skeleton in src/converters/internal_gains.py extending BaseConverter[Room]
- [X] T013 [US1] Implement _convert_occupant_gains method in src/converters/internal_gains.py:
  - Map OccupantGains.maxnumber → People.people_per_floor_area
  - Create ScheduleConstant for Activity Level (heat_per_person)
  - Register schedule_id to REQUIRED_SCHEDULE_IDS
- [X] T014 [P] [US1] Implement _convert_light_gains method in src/converters/internal_gains.py:
  - Map LightGains.maxpower → Lights.watts_per_floor_area
  - Map LightGains.heat_rate → Lights.fraction_radiant (optional)
  - Register schedule_id to REQUIRED_SCHEDULE_IDS
- [X] T015 [P] [US1] Implement _convert_equipment_gains method in src/converters/internal_gains.py:
  - Map EquipmentGains.maxpower → ElectricEquipment.watts_per_floor_area
  - Ignore max_hum/min_hum fields
  - Register schedule_id to REQUIRED_SCHEDULE_IDS
- [X] T016 [US1] Implement convert_one method in src/converters/internal_gains.py:
  - Iterate Room.occupant_gains, light_gains, equipment_gains
  - Skip gracefully if gains data is missing (log info)
  - Raise error if required fields (maxnumber, maxpower) are missing
- [X] T017 [US1] Implement error handling in src/converters/internal_gains.py:
  - Validate maxnumber > 0 for OccupantGains
  - Validate maxpower > 0 for LightGains/EquipmentGains
  - Clear error messages with field names

**Checkpoint**: User Story 1 complete - Internal gains conversion functional

---

## Phase 4: User Story 4 - Automatic Schedule Collection (Priority: P2)

**Goal**: Automatically identify and collect all schedules referenced by gains, HVAC, and ventilation objects

**Independent Test**: Convert a DeST file with multiple schedule references and verify all referenced schedules appear in the IDF output exactly once

### Implementation for User Story 4

- [X] T018 [US4] Verify ScheduleConverter reads from REQUIRED_SCHEDULE_IDS in src/converters/schedule.py
- [X] T019 [US4] Update ScheduleConverter to only convert schedules in REQUIRED_SCHEDULE_IDS set in src/converters/schedule.py
- [X] T020 [US4] Ensure schedule deduplication via set data structure in src/converters/manager.py

**Checkpoint**: User Story 4 complete - Schedule auto-collection working

---

## Phase 5: User Story 2 - Simplified HVAC System (Priority: P2)

**Goal**: Configure HVACTemplate:Zone:IdealLoadsAirSystem for each Zone with thermostat setpoints

**Independent Test**: Convert any DeST file and verify each Zone has HVACTemplate:Zone:IdealLoadsAirSystem configured, simulation runs without HVAC errors

**Note**: 使用 HVACTemplate 对象，EnergyPlus 运行时自动展开为底层 HVAC 对象（FR-008 已移除，无需手动创建 ZoneHVAC:EquipmentList 等）

### Implementation for User Story 2

- [X] T021 [US2] Create HVACConverter class skeleton in src/converters/hvac.py extending BaseConverter[Room]
- [X] T022 [US2] Implement _create_thermostat method in src/converters/hvac.py:
  - Create HVACTemplateThermostat from RoomGroup schedules
  - Name format: `Thermostat_{room_group_id}`
  - Set heating_setpoint_schedule_name from RoomGroup.set_t_min_schedule_id
  - Set cooling_setpoint_schedule_name from RoomGroup.set_t_max_schedule_id
  - Register schedule IDs to REQUIRED_SCHEDULE_IDS
  - Cache thermostat by room_group_id to avoid duplicates (multiple rooms share same RoomGroup)
- [X] T023 [US2] Implement _create_ideal_loads_template method in src/converters/hvac.py:
  - Create HVACTemplateZoneIdealLoadsAirSystem
  - Set zone_name from LookupTable
  - Set template_thermostat_name to reference the HVACTemplateThermostat
  - Set default heating/cooling supply air temperatures (50°C/13°C)
  - Set heating_limit and cooling_limit to "NoLimit"
- [X] T024 [US2] Implement convert_one method in src/converters/hvac.py:
  - Get zone_name from LookupTable
  - Get RoomGroup for thermostat schedules
  - Call _create_thermostat (skip if already created for this RoomGroup)
  - Call _create_ideal_loads_template
- [X] T025 [US2] Implement error handling in src/converters/hvac.py:
  - Raise error if RoomGroup.set_t_min_schedule_id is None
  - Raise error if RoomGroup.set_t_max_schedule_id is None
  - Clear error messages with room and RoomGroup context

**Checkpoint**: User Story 2 complete - HVAC system configured for all zones

---

## Phase 6: User Story 3 - Outdoor Air/Ventilation Conversion (Priority: P3)

**Goal**: Configure outdoor air (fresh air) settings in HVACTemplate:Zone:IdealLoadsAirSystem

**Independent Test**: Convert a DeST file with min_fresh_flow_num and verify HVACTemplate:Zone:IdealLoadsAirSystem has correct outdoor air settings (outdoor_air_method="Flow/Zone" and outdoor_air_flow_rate_per_zone)

**Note**: HVACTemplateZoneIdealLoadsAirSystem 内置新风配置字段，无需单独创建 DesignSpecification:OutdoorAir

### Implementation for User Story 3

- [X] T026 [US3] Implement _calculate_fresh_air_flow method in src/converters/hvac.py:
  - Priority 1: Use Room.min_fresh_flow_num (m³/h)
  - Priority 2: Calculate from OccupantGains.min_require_fresh_air × maxnumber × area
  - Convert m³/h to m³/s (÷3600)
  - Return None if no fresh air configured (value is 0 or missing)
- [X] T027 [US3] Update _create_ideal_loads_template method in src/converters/hvac.py to add outdoor air:
  - If fresh air flow > 0:
    - Set outdoor_air_method = "Flow/Zone"
    - Set outdoor_air_flow_rate_per_zone = calculated value (m³/s)
  - If fresh air flow is None/0:
    - Set outdoor_air_method = "None" (no outdoor air)
- [X] T028 [US3] Update convert_one method in src/converters/hvac.py:
  - Call _calculate_fresh_air_flow before creating IdealLoadsTemplate
  - Pass fresh air flow to _create_ideal_loads_template
  - Log info message when fresh air is skipped (value is 0 or missing)

**Checkpoint**: User Story 3 complete - Fresh air/ventilation configured

---

## Phase 7: User Story 5 - Door Interface Preservation (Priority: P4)

**Goal**: Preserve door conversion interface, skip actual conversion without errors

**Independent Test**: Convert a DeST file with Door data and verify no errors, doors are logged as skipped

### Implementation for User Story 5

- [X] T029 [US5] FenestrationConverter in src/converters/fenestration.py 已检测 Door 类型（convert_one 中 isinstance 判断）
- [X] T030 [US5] Door skip logic in src/converters/fenestration.py:
  - _convert_door 返回 False，不生成 IDF 对象
  - Door 转换有意跳过，当前不需要门对象转换

**Checkpoint**: User Story 5 complete - Door interface preserved

---

## Phase 8: User Story 6 - Sizing Period Auto-Add (Priority: P2)

**Goal**: Automatically add SizingPeriod:DesignDay objects based on building location

**Independent Test**: Convert a DeST file with location info and verify IDF contains correct SizingPeriod:DesignDay objects (winter heating and summer cooling)

**Note**: DDY 数据通过 src/utils/ddy_downloader.py 从 EnergyPlus 官方 GeoJSON 在线获取并解析，运行时需要网络连接

### Implementation for User Story 6

- [X] T031 [US6] Create DDY data downloader in src/utils/ddy_downloader.py:
  - DDY class从 EnergyPlus 官方 GeoJSON 在线获取气象站数据
  - 按城市名匹配（lowercase）获取对应 DDY 文件 URL
  - 下载并解析 DDY 文件为 SizingPeriodDesignDay IDF 模型

- [X] T032 [US6] Create SizingConverter class skeleton in src/converters/sizing.py extending BaseConverter[Environment]:
  - 使用 DDY 类在线获取设计日数据
  - MappingItem dataclass 定义冬夏设计日名称模式

- [X] T033 [US6] Implement _get_ddy_data method in src/converters/sizing.py:
  - 调用 DDY().get_weather_locations(city) 获取 IDF
  - 筛选 SizingPeriod:DesignDay 类型对象
  - 匹配失败时记录错误并返回空 dict

- [X] T034 [US6] City matching via DDY downloader:
  - DDY.get_weather_locations 按城市名 lowercase 匹配
  - 匹配失败时抛出 ValueError

- [X] T035 [US6] Design day object creation in src/converters/sizing.py:
  - DDY 解析器直接生成 SizingPeriodDesignDay IDF 模型实例
  - convert_one 按 MappingItem 中定义的名称模式筛选冬夏设计日

- [X] T036 [US6] Implement convert_all method in src/converters/sizing.py:
  - Query all Environment from database
  - Call convert_one for each Environment
  - Update stats

- [X] T037 [US6] Implement convert_one method in src/converters/sizing.py:
  - 调用 _get_ddy_data 获取设计日数据
  - 筛选 winter (Htg 99.6% Condns DB) 和 summer (Clg .4% Condns DB=>MWB) 设计日
  - 添加匹配的设计日到 IDF，跳过其余
  - Return True on success, False if no DDY data found

- [X] T038 [US6] Implement error handling in src/converters/sizing.py:
  - 城市不匹配时 stats.errors += 1 并记录 warning
  - 返回 False 跳过 sizing period
  - 包含城市名上下文的日志消息

**Checkpoint**: User Story 6 complete - Sizing Period auto-added

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Integration, registration, and final validation

- [X] T039 Register InternalGainsConverter in ConverterManager in src/converters/manager.py
- [X] T040 Register HVACConverter in ConverterManager in src/converters/manager.py
- [X] T041 Update converter execution order in ConverterManager:
  - InternalGainsConverter after FenestrationConverter
  - HVACConverter after InternalGainsConverter
  - ScheduleConverter last (to collect all required schedules)
- [X] T042 Validate IDF output structure matches quickstart.md examples
- [X] T043 Run conversion on sample DeST file and verify in EnergyPlus
- [X] T044 [US6] Register SizingConverter in ConverterManager in src/converters/manager.py:
  - Add SizingConverter to converters list
  - Execute SizingConverter FIRST (before other converters)
- [X] T045 [US6] main.py convert 命令通过 ConverterManager 自动执行 SizingConverter（已在 CONVERTER_ORDER 中注册为第一项）
- [X] T046 Run full conversion with Sizing Period and verify in EnergyPlus:
  - Verify SizingPeriod:DesignDay objects present in IDF
  - Verify HVAC sizing calculation completes without errors

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - verify existing code
- **Foundational (Phase 2)**: Depends on Setup - add missing models
- **User Stories (Phase 3-8)**: All depend on Foundational completion
  - US1 (P1): Can start immediately after Foundational
  - US4 (P2): Can start after US1 (needs schedule registration pattern)
  - US2 (P2): Can start after US4 (uses schedule collection)
  - US3 (P3): Depends on US2 (extends HVACConverter)
  - US5 (P4): Independent - can run in parallel with US2/US3
  - **US6 (P2)**: Independent - can run in parallel with US1-US5 (no data dependencies)
- **Polish (Phase 9)**: Depends on all user stories complete

### User Story Dependencies

```
Phase 2 (Foundational)
    ↓
Phase 3 (US1: Internal Gains) ──────────────────────┐
    ↓                                               │
Phase 4 (US4: Schedule Collection)    Phase 7 (US5: Door Interface)
    ↓                                               │
Phase 5 (US2: HVAC System)             ─────────────┤
    ↓                                               │
Phase 6 (US3: Outdoor Air)            Phase 8 (US6: Sizing Period) [NEW]
    ↓                                               │
    └───────────────────────────────────────────────┘
                        ↓
                 Phase 9 (Polish)
```

### Parallel Opportunities

**Within Phase 1 (Setup)**:
```
T002, T003, T004, T005, T006 can run in parallel
```

**Within Phase 2 (Foundational)**:
```
T008, T009, T010 can run in parallel (after T007)
```

**Within Phase 3 (US1)**:
```
T014, T015 can run in parallel (after T013)
```

**US5 parallel execution**:
```
US5 (Phase 7) can run in parallel with US2/US3 (Phases 5-6)
```

**US6 parallel execution** [NEW]:
```
US6 (Phase 8) can run in parallel with US1-US5 (independent of other user stories)
T032, T033, T034, T035 can run in parallel within Phase 8
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup verification
2. Complete Phase 2: Foundational models
3. Complete Phase 3: User Story 1 (Internal Gains)
4. **STOP and VALIDATE**: Convert sample file, verify People/Lights/Equipment in IDF
5. Can deploy MVP with basic internal gains support

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 (Internal Gains) → Test → MVP!
3. Add US4 (Schedule Collection) → Test → Schedules auto-collected
4. Add US2 (HVAC) → Test → Full simulation capable
5. Add US3 (Outdoor Air) → Test → Ventilation support
6. Add US5 (Door Interface) → Test → Door interface preserved
7. **Add US6 (Sizing Period) → Test → HVAC sizing calculation ready** [NEW]

### Single Developer Strategy

1. Complete phases sequentially: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9
2. Validate at each checkpoint before proceeding
3. US5 can be done at any point after Phase 2
4. **US6 can be done at any point after Phase 2** (independent of other user stories)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story
- Each user story should be independently completable and testable
- Existing models/converters should be verified, not recreated
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Unit conversion: m³/h → m³/s (÷3600) for fresh air flow
- **HVACTemplate 模式**: 使用 HVACTemplate:Zone:IdealLoadsAirSystem + HVACTemplate:Thermostat，EnergyPlus 运行时自动展开为底层对象，无需手动创建 ZoneHVAC:EquipmentList 等
- **Sizing Period 数据源**: DDY 数据通过 src/utils/ddy_downloader.py 从 EnergyPlus 官方 GeoJSON (GitHub) 在线获取，运行时需要网络连接
- **SizingConverter 执行顺序**: 已在 ConverterManager.CONVERTER_ORDER 中排第一位，在 BuildingConverter 之前执行
