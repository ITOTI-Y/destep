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

**Goal**: Configure IdealLoadsAirSystem for each Zone with thermostat setpoints

**Independent Test**: Convert any DeST file and verify each Zone has IdealLoadsAirSystem configured, simulation runs without HVAC errors

### Implementation for User Story 2

- [ ] T021 [US2] Create HVACConverter class skeleton in src/converters/hvac.py extending BaseConverter[Room]
- [ ] T022 [US2] Implement _create_equipment_connections method in src/converters/hvac.py:
  - Create ZoneHVACEquipmentConnections with proper node names
  - Node naming: {zone_name}_Inlet, {zone_name}_AirNode, {zone_name}_Return
- [ ] T023 [US2] Implement _create_equipment_list method in src/converters/hvac.py:
  - Create ZoneHVACEquipmentList with SequentialLoad scheme
  - Reference IdealLoadsAirSystem with priority 1
- [ ] T024 [US2] Implement _create_ideal_loads method in src/converters/hvac.py:
  - Create ZoneHVACIdealLoadsAirSystem
  - Set zone_supply_air_node_name to {zone_name}_Inlet
  - Set default heating/cooling temperatures (50°C/13°C)
- [ ] T025 [US2] Implement _create_thermostat method in src/converters/hvac.py:
  - Create ThermostatSetpointDualSetpoint from RoomGroup schedules
  - Create ZoneControlThermostat referencing DualSetpoint
  - Register set_t_min_schedule_id and set_t_max_schedule_id to REQUIRED_SCHEDULE_IDS
- [ ] T026 [US2] Create AlwaysDual ScheduleConstant (value=4) in src/converters/hvac.py for control type
- [ ] T027 [US2] Implement convert_one method in src/converters/hvac.py:
  - Get zone_name from LookupTable
  - Get RoomGroup for thermostat schedules
  - Create all HVAC objects in correct order
- [ ] T028 [US2] Implement error handling in src/converters/hvac.py:
  - Raise error if RoomGroup.set_t_min_schedule_id is None
  - Raise error if RoomGroup.set_t_max_schedule_id is None

**Checkpoint**: User Story 2 complete - HVAC system configured for all zones

---

## Phase 6: User Story 3 - Outdoor Air/Ventilation Conversion (Priority: P3)

**Goal**: Configure outdoor air (fresh air) settings for IdealLoadsAirSystem

**Independent Test**: Convert a DeST file with min_fresh_flow_num and verify DesignSpecification:OutdoorAir is created with correct flow rate

### Implementation for User Story 3

- [ ] T029 [US3] Implement _calculate_fresh_air_flow method in src/converters/hvac.py:
  - Priority 1: Use Room.min_fresh_flow_num (m³/h)
  - Priority 2: Calculate from OccupantGains.min_require_fresh_air × maxnumber × area
  - Convert m³/h to m³/s (÷3600)
  - Return None if no fresh air configured
- [ ] T030 [US3] Implement _create_outdoor_air_spec method in src/converters/hvac.py:
  - Create DesignSpecificationOutdoorAir with Flow/Zone method
  - Set outdoor_air_flow_per_zone to calculated value (m³/s)
- [ ] T031 [US3] Update _create_ideal_loads method in src/converters/hvac.py:
  - Add outdoor_air_inlet_node_name if fresh air configured
  - Add design_specification_outdoor_air_object_name if fresh air configured
- [ ] T032 [US3] Update convert_one method in src/converters/hvac.py:
  - Call fresh air calculation
  - Conditionally create DesignSpecificationOutdoorAir
  - Skip fresh air config gracefully if flow is 0 or None

**Checkpoint**: User Story 3 complete - Fresh air/ventilation configured

---

## Phase 7: User Story 5 - Door Interface Preservation (Priority: P4)

**Goal**: Preserve door conversion interface, skip actual conversion without errors

**Independent Test**: Convert a DeST file with Door data and verify no errors, doors are logged as skipped

### Implementation for User Story 5

- [ ] T033 [US5] Update FenestrationConverter in src/converters/fenestration.py to detect door objects
- [ ] T034 [US5] Implement door skip logic in src/converters/fenestration.py:
  - Check if fenestration is a door (by type or classification)
  - Log info message "Door skipped: {door_id}"
  - Return without generating IDF objects
  - Track skipped count for statistics

**Checkpoint**: User Story 5 complete - Door interface preserved

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Integration, registration, and final validation

- [X] T035 Register InternalGainsConverter in ConverterManager in src/converters/manager.py
- [ ] T036 Register HVACConverter in ConverterManager in src/converters/manager.py
- [ ] T037 Update converter execution order in ConverterManager:
  - InternalGainsConverter after FenestrationConverter
  - HVACConverter after InternalGainsConverter
  - ScheduleConverter last (to collect all required schedules)
- [ ] T038 Validate IDF output structure matches quickstart.md examples
- [ ] T039 Run conversion on sample DeST file and verify in EnergyPlus

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - verify existing code
- **Foundational (Phase 2)**: Depends on Setup - add missing models
- **User Stories (Phase 3-7)**: All depend on Foundational completion
  - US1 (P1): Can start immediately after Foundational
  - US4 (P2): Can start after US1 (needs schedule registration pattern)
  - US2 (P2): Can start after US4 (uses schedule collection)
  - US3 (P3): Depends on US2 (extends HVACConverter)
  - US5 (P4): Independent - can run in parallel with US2/US3
- **Polish (Phase 8)**: Depends on all user stories complete

### User Story Dependencies

```
Phase 2 (Foundational)
    ↓
Phase 3 (US1: Internal Gains) ──────────────────────┐
    ↓                                               │
Phase 4 (US4: Schedule Collection)    Phase 7 (US5: Door Interface)
    ↓                                               │
Phase 5 (US2: HVAC System)             ─────────────┘
    ↓
Phase 6 (US3: Outdoor Air)
    ↓
Phase 8 (Polish)
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
6. Add US5 (Door Interface) → Test → Complete feature

### Single Developer Strategy

1. Complete phases sequentially: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8
2. Validate at each checkpoint before proceeding
3. US5 can be done at any point after Phase 2

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story
- Each user story should be independently completable and testable
- Existing models/converters should be verified, not recreated
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Unit conversion: m³/h → m³/s (÷3600) for fresh air flow
