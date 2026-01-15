# Tasks: destep-py 项目重写

**Input**: Design documents from `/specs/001-destep-rewrite/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Tests are NOT explicitly requested in the feature specification, so only implementation tasks are included.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root (per plan.md)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project structure verification and missing dependencies

> **Note**: 根据 plan.md，Phase 1 和 Phase 2 已完成（Node 1.1 - 2.5）。Setup 阶段仅需验证现有结构。

- [X] T001 [Verify] Verify project structure matches plan.md specification
- [X] T002 [P] [Verify] Verify all required dependencies in pyproject.toml (Pydantic, SQLAlchemy, Typer, loguru, Jinja2, joblib)
- [X] T003 [P] [Verify] Verify existing modules: codegen/, database/, utils/, config.py are functional

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement IDF unified class in src/idf/idf.py (Node 3.1 - core container for all IDF objects)
- [X] T005 Implement IDF.add() method with duplicate prevention in src/idf/idf.py
- [X] T006 Implement IDF.get(), IDF.has(), IDF.all_of_type() methods in src/idf/idf.py
- [X] T007 Implement IDF.__iter__() and IDF.__len__() methods in src/idf/idf.py
- [X] T008 Implement IDF.save() method with FIELD_ORDER_REGISTRY in src/idf/idf.py
- [X] T009 Implement IDF.load() class method for IDF file parsing in src/idf/idf.py
- [X] T010 [P] Implement BaseConverter abstract class in src/converters/base.py (Node 4.1)
- [X] T011 [P] Implement UnitConverter utility class in src/converters/base.py
- [X] T012 [P] Implement ConversionStats dataclass in src/converters/base.py
- [X] T013 Implement BaseConverter.make_name() with pinyin conversion in src/converters/base.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - 数据提取与转换 (Priority: P1) 🎯 MVP

**Goal**: 将 DeST 模型数据转换为 EnergyPlus IDF 格式，支持完整的转换流程

**Independent Test**: 提供一个 DeST .accdb 文件，执行 `destep run input.accdb --output building.idf`，验证生成的 IDF 文件能被 EnergyPlus 成功解析

### Implementation for User Story 1

#### 4.2 Building 转换器

- [X] T014 [P] [US1] Create BuildingConverter class in src/converters/building.py
- [X] T015 [US1] Implement Building object generation in src/converters/building.py
- [X] T016 [US1] Implement Site:Location generation with lat/long in src/converters/building.py
- [X] T017 [US1] Implement GlobalGeometryRules configuration in src/converters/building.py

#### 4.3 Schedule 转换器

- [X] T018 [P] [US1] Create ScheduleConverter class in src/converters/schedule.py
- [X] T019 [US1] Implement Schedule:File generation from ScheduleYear in src/converters/schedule.py
- [X] T020 [US1] Implement ScheduleTypeLimits auto-generation in src/converters/schedule.py

#### 4.4 Construction 转换器

- [X] T021 [P] [US1] Create ConstructionConverter class in src/converters/construction.py
- [X] T022 [US1] Implement Material generation with thermal properties in src/converters/construction.py
- [X] T023 [US1] Implement Construction generation with correct layer order in src/converters/construction.py
- [X] T024 [US1] Handle missing material data with defaults in src/converters/construction.py

#### 4.5 Zone 转换器

- [X] T025 [P] [US1] Create ZoneConverter class in src/converters/zone.py
- [X] T026 [US1] Implement Room to Zone conversion with mm→m in src/converters/zone.py
- [X] T027 [US1] Implement multiplier handling in src/converters/zone.py
- [X] T028 [US1] Skip empty rooms with warning in src/converters/zone.py

#### 4.6 Surface 转换器

- [ ] T029 [US1] Create SurfaceConverter class in src/converters/surface.py
- [ ] T030 [US1] Implement vertex ordering in src/converters/surface.py: reorder vertices per EnergyPlus GlobalGeometryRules (UpperLeftCorner + Counterclockwise when viewed from outside along surface normal); [EC4] handle coordinate precision (merge vertices < 1e-10m apart with warning)
- [ ] T031 [US1] Implement boundary condition mapping (Ground/Outdoors/Surface) in src/converters/surface.py
- [ ] T032 [US1] Implement paired surface creation for interior walls in src/converters/surface.py
- [ ] T033 [US1] Implement floor/ceiling surface pairs between zones in src/converters/surface.py; [EC2] report geometry warning if zone surfaces do not form closed volume (generate IDF with warning comment)

#### 4.7 Fenestration 转换器

- [ ] T034 [US1] Create FenestrationConverter class in src/converters/fenestration.py
- [ ] T035 [US1] Implement Window/Door to FenestrationSurface:Detailed conversion in src/converters/fenestration.py
- [ ] T036 [US1] Validate window vertices within parent wall bounds in src/converters/fenestration.py; [EC4] handle coordinate precision for fenestration vertices
- [ ] T037 [US1] Apply default window sill height (0.9m) when missing in src/converters/fenestration.py

#### 4.8 Gains 转换器

- [ ] T038 [P] [US1] Create GainsConverter class in src/converters/gains.py
- [ ] T039 [US1] Implement People object generation from OccupantGains in src/converters/gains.py
- [ ] T040 [US1] Implement Lights object generation from LightGains in src/converters/gains.py
- [ ] T041 [US1] Implement ElectricEquipment generation from EquipmentGains in src/converters/gains.py

#### 4.9 HVAC Zone 转换器

- [ ] T042 [P] [US1] Create HVACZoneConverter class in src/converters/hvac_zone.py
- [ ] T043 [US1] Implement ZoneHVAC:FourPipeFanCoil generation in src/converters/hvac_zone.py
- [ ] T044 [US1] Implement ZoneHVAC:EquipmentList connection in src/converters/hvac_zone.py
- [ ] T045 [US1] Implement thermostat setpoint configuration in src/converters/hvac_zone.py

#### 4.10 转换管理器

- [ ] T046 [US1] Create ConversionManager class in src/converters/manager.py
- [ ] T047 [US1] Implement CONVERTER_ORDER with dependency sequence in src/converters/manager.py
- [ ] T048 [US1] Implement convert() orchestration method in src/converters/manager.py; [EC3] skip objects with missing foreign key references and log warnings (do not abort conversion)
- [ ] T049 [US1] Implement conversion statistics summary output in src/converters/manager.py

#### 5.2 & 5.3 CLI Commands

- [ ] T050 [US1] Implement `destep convert` command in main.py (Node 5.2)
- [ ] T051 [US1] Implement `destep run` command in main.py (Node 5.3)
- [ ] T052 [US1] Add `--keep-sqlite` option to run command in main.py

**Checkpoint**: User Story 1 完成后，用户可以将 DeST .accdb 文件转换为 EnergyPlus IDF 格式

---

## Phase 4: User Story 2 - IDF 模型代码生成 (Priority: P2)

**Goal**: 从 EnergyPlus JSON Schema 自动生成类型安全的 Pydantic 模型代码

**Independent Test**: 执行 `destep codegen --schema schema.epJSON --output src/idf/models/`，验证生成的 Python 模块可被正确导入且通过类型检查

> **Note**: 根据 plan.md，代码生成功能（Node 1.1 - 2.5）已完成。此阶段为验证和文档完善。

### Implementation for User Story 2

- [ ] T053 [P] [US2] Verify codegen module generates all 800+ object types in src/codegen/
- [ ] T054 [P] [US2] Verify OBJECT_TYPE_REGISTRY completeness in src/idf/models/__init__.py
- [ ] T055 [P] [US2] Verify FIELD_ORDER_REGISTRY correctness in src/idf/models/__init__.py
- [ ] T056 [US2] Verify generated models pass ruff check
- [ ] T057 [US2] Update `destep codegen` command help text in main.py

**Checkpoint**: User Story 2 验证通过，代码生成功能完整可用

---

## Phase 5: User Story 3 - EnergyPlus 模拟运行 (Priority: P3)

**Goal**: 支持从命令行运行 EnergyPlus 模拟，包括单文件和批量并行运行

**Independent Test**: 提供一个有效的 IDF 文件和气象文件，执行 `destep simulate building.idf --weather weather.epw`，验证 EnergyPlus 成功运行

### Implementation for User Story 3

#### 3.2 EnergyPlus 运行器

- [ ] T058 [P] [US3] Create RunnerConfig dataclass in src/idf/runner.py
- [ ] T059 [P] [US3] Create SimulationResult dataclass in src/idf/runner.py
- [ ] T060 [US3] Implement EnergyPlusRunner class in src/idf/runner.py
- [ ] T061 [US3] Implement run() method with subprocess execution in src/idf/runner.py
- [ ] T062 [US3] Implement realtime output streaming in src/idf/runner.py
- [ ] T063 [US3] Implement timeout handling with process termination in src/idf/runner.py
- [ ] T064 [US3] Collect output files (eso, err, csv) in SimulationResult in src/idf/runner.py

#### 3.3 并行运行器

- [ ] T065 [P] [US3] Create BatchResult dataclass in src/idf/runner.py
- [ ] T066 [US3] Implement ParallelRunner class in src/idf/runner.py
- [ ] T067 [US3] Implement run_batch() with joblib.Parallel in src/idf/runner.py
- [ ] T068 [US3] Create isolated output directories for each simulation in src/idf/runner.py
- [ ] T069 [US3] Implement run_parametric() method in src/idf/runner.py

#### 3.4 Simulate CLI 命令

- [ ] T070 [US3] Implement `destep simulate` command in main.py; [EC5] display clear installation guidance when EnergyPlus executable not found or path invalid
- [ ] T071 [US3] Add `--weather` option for EPW file path in main.py
- [ ] T072 [US3] Add `--batch` option for directory mode in main.py
- [ ] T073 [US3] Add `--jobs` option for parallel worker count in main.py
- [ ] T074 [US3] Add `--realtime` flag for live output in main.py
- [ ] T075 [US3] Implement progress bar for batch mode in main.py
- [ ] T076 [US3] Implement results summary output in main.py

**Checkpoint**: User Story 3 完成后，用户可以运行单个或批量 EnergyPlus 模拟

---

## Phase 6: User Story 4 - 分步数据处理 (Priority: P4)

**Goal**: 支持分步执行数据提取和转换，便于中间步骤检查

**Independent Test**: 分别执行 `destep extract` 和 `destep convert` 命令，验证中间 SQLite 文件正确生成

> **Note**: 根据 plan.md，extract 命令已完成。此阶段主要是验证和完善。

### Implementation for User Story 4

- [ ] T077 [P] [US4] Verify `destep extract` command functionality in main.py; [EC1] display clear error message and file integrity suggestion when .accdb is corrupted or unsupported
- [ ] T078 [US4] Add verbose output option to extract command in main.py
- [ ] T079 [US4] Add table statistics output after extraction in main.py

**Checkpoint**: User Story 4 完成后，用户可以分步处理数据

---

## Phase 7: User Story 5 - IDF 文件解析与编辑 (Priority: P5)

**Goal**: 解析现有 IDF/epJSON 文件，支持检查、修改和合并

**Independent Test**: 解析一个现有 IDF 文件，修改参数后重新写入，验证修改被正确保存

### Implementation for User Story 5

- [ ] T080 [P] [US5] Enhance IDF.load() to handle malformed files in src/idf/idf.py
- [ ] T081 [P] [US5] Implement epJSON format detection in src/idf/idf.py
- [ ] T082 [US5] Implement IDF.load_epjson() class method in src/idf/idf.py
- [ ] T083 [US5] Implement IDF.save_epjson() method in src/idf/idf.py
- [ ] T084 [US5] Add IDF merge functionality for combining files in src/idf/idf.py

**Checkpoint**: User Story 5 完成后，用户可以解析和编辑现有 IDF/epJSON 文件

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T085 [P] Update src/idf/__init__.py exports (IDF, EnergyPlusRunner, ParallelRunner)
- [ ] T086 [P] Update src/converters/__init__.py exports (ConversionManager, all converters)
- [ ] T087 Code cleanup and remove unused imports across all modules
- [ ] T088 [P] Add CLI help text and examples for all commands in main.py
- [ ] T089 Verify error messages are clear and actionable across all commands
- [ ] T090 Run full workflow validation per quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - verification only
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (T004-T013)
- **User Story 2 (Phase 4)**: Can start after Setup (verification only)
- **User Story 3 (Phase 5)**: Depends on Foundational (T004-T009 for IDF class)
- **User Story 4 (Phase 6)**: Minimal dependencies (extract already complete)
- **User Story 5 (Phase 7)**: Depends on T004-T009 (IDF class)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Primary MVP - requires full Foundational phase
  - Internal order: Building → Schedule → Construction → Zone → Surface → Fenestration → Gains → HVAC → Manager → CLI
- **User Story 2 (P2)**: Already complete - verification only
- **User Story 3 (P3)**: Can start after IDF class (T004-T009) - parallel with US1 converters
- **User Story 4 (P4)**: Already complete - verification only
- **User Story 5 (P5)**: Extends IDF class - can start after Foundational

### Within User Story 1 (Critical Path)

```
T014-T017 (Building) ─┐
T018-T020 (Schedule) ─┼── All parallel after T010-T013
T021-T024 (Construction)─┤
T025-T028 (Zone) ─────┘
         │
         v
T029-T033 (Surface) ← depends on Zone, Construction
         │
         v
T034-T037 (Fenestration) ← depends on Surface
         │
T038-T041 (Gains) ← depends on Zone, Schedule (can parallel with Fenestration)
T042-T045 (HVAC) ← depends on Zone (can parallel with Fenestration)
         │
         v
T046-T049 (Manager) ← depends on all converters
         │
         v
T050-T052 (CLI) ← depends on Manager
```

### Parallel Opportunities

**Phase 2 (Foundational)**:
- T010, T011, T012 can run in parallel (different classes in base.py)

**Phase 3 (User Story 1)**:
- T014, T018, T021, T025 can run in parallel (different converter files)
- T038, T042 can run in parallel after Zone converter

**Phase 4 (User Story 2)**:
- T053, T054, T055 can all run in parallel (verification tasks)

**Phase 5 (User Story 3)**:
- T058, T059 can run in parallel (dataclasses)
- T065 can run parallel with T060-T064

**Cross-Phase Parallelism**:
- User Story 3 (Phase 5) can start after T004-T009, parallel with US1 converters
- User Story 2 (Phase 4) verification can run parallel with anything
- User Story 4 (Phase 6) verification can run parallel with anything

---

## Parallel Example: User Story 1 Converters

```bash
# After Foundational phase (T004-T013) completes, launch converter classes in parallel:
Task: "Create BuildingConverter class in src/converters/building.py"
Task: "Create ScheduleConverter class in src/converters/schedule.py"
Task: "Create ConstructionConverter class in src/converters/construction.py"
Task: "Create ZoneConverter class in src/converters/zone.py"

# After Zone converter completes:
Task: "Create SurfaceConverter class in src/converters/surface.py"

# After Surface converter completes, launch in parallel:
Task: "Create FenestrationConverter class in src/converters/fenestration.py"
Task: "Create GainsConverter class in src/converters/gains.py"
Task: "Create HVACZoneConverter class in src/converters/hvac_zone.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (verification)
2. Complete Phase 2: Foundational (IDF class + BaseConverter)
3. Complete Phase 3: User Story 1 (all converters + CLI)
4. **STOP and VALIDATE**: Test with real DeST .accdb file
5. Verify IDF file can be parsed by EnergyPlus

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Full conversion pipeline (MVP!)
3. Add User Story 3 → Simulation support (extend workflow)
4. Add User Story 5 → IDF editing capabilities (advanced users)
5. Polish → Production ready

### Critical Path Summary

```
T001-T003 (Setup) → T004-T013 (Foundational) → T014-T052 (US1) → MVP Complete
                                              │
                                              └→ T058-T076 (US3) → Simulation Support
```

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- User Story 2 and 4 are primarily verification (already implemented)
- User Story 1 is the critical MVP path
- User Story 3 can be developed in parallel after Foundational phase
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- IDF 字段顺序必须使用 FIELD_ORDER_REGISTRY
- 坐标精度统一为 4 位小数
- 转换后热区面积误差 < 1%
