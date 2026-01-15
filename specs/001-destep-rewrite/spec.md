# Feature Specification: destep-py 项目重写

**Feature Branch**: `001-destep-rewrite`
**Created**: 2026-01-15
**Status**: Draft
**Input**: DeST 到 EnergyPlus IDF 转换工具完整重写

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 数据提取与转换 (Priority: P1)

建筑能耗模拟工程师需要将 DeST 模型数据（.accdb 格式）转换为 EnergyPlus IDF 格式，以便使用 EnergyPlus 进行更精细的能耗模拟分析。

**Why this priority**: 这是工具的核心价值主张。没有数据转换功能，工具无任何用途。转换功能是所有其他功能的基础。

**Independent Test**: 可通过提供一个 DeST .accdb 文件，执行转换命令，验证生成的 IDF 文件能被 EnergyPlus 成功解析并运行模拟来测试。

**Acceptance Scenarios**:

1. **Given** 用户有一个有效的 DeST .accdb 数据库文件, **When** 用户执行 `destep run input.accdb --output building.idf`, **Then** 系统生成一个可被 EnergyPlus 解析的 IDF 文件
2. **Given** 用户有一个 DeST 数据库, **When** 用户执行转换, **Then** 所有热区、表面、构造、窗户、内部得热等对象正确转换为对应的 EnergyPlus 对象
3. **Given** DeST 数据库中包含中文名称, **When** 转换完成, **Then** IDF 对象名称使用拼音表示，保持可读性

---

### User Story 2 - IDF 模型代码生成 (Priority: P2)

开发者需要从 EnergyPlus JSON Schema 自动生成类型安全的 Pydantic 模型代码，避免手动维护 800+ 个对象类型定义。

**Why this priority**: 代码生成是转换器实现的技术基础。生成的模型确保数据类型安全和验证，减少运行时错误。

**Independent Test**: 可通过执行代码生成命令，验证生成的 Python 模块可被正确导入、类型检查通过、且包含所有 800+ 对象类型来测试。

**Acceptance Scenarios**:

1. **Given** 用户有 Energy+.schema.epJSON 文件, **When** 用户执行 `destep codegen --schema schema.epJSON --output src/idf/models/`, **Then** 系统生成完整的 Pydantic 模型代码
2. **Given** 生成的模型代码, **When** 运行代码检查工具, **Then** 代码通过 ruff 检查无错误
3. **Given** 生成的模型代码, **When** 创建模型实例, **Then** Pydantic 自动验证字段类型和约束

---

### User Story 3 - EnergyPlus 模拟运行 (Priority: P3)

用户需要直接从命令行运行 EnergyPlus 模拟，支持单文件和批量并行运行，查看实时输出和结果汇总。

**Why this priority**: 模拟运行是工作流程的最后一步，用户可以在转换后直接验证 IDF 文件的有效性。

**Independent Test**: 可通过提供一个有效的 IDF 文件和气象文件，执行模拟命令，验证 EnergyPlus 成功运行并生成结果文件来测试。

**Acceptance Scenarios**:

1. **Given** 用户有一个 IDF 文件和 EPW 气象文件, **When** 用户执行 `destep simulate building.idf --weather weather.epw`, **Then** EnergyPlus 模拟运行并实时显示输出
2. **Given** 用户有多个 IDF 文件, **When** 用户执行 `destep simulate --batch buildings/ --jobs 4`, **Then** 系统并行运行多个模拟并汇总结果
3. **Given** 模拟过程中发生超时, **When** 超时阈值达到, **Then** 系统自动终止模拟并报告错误

---

### User Story 4 - 分步数据处理 (Priority: P4)

高级用户需要分步执行数据提取和转换，以便在中间步骤进行数据检查或自定义处理。

**Why this priority**: 分步处理提供更大的灵活性，适合调试和高级用例，但不是基本工作流程必需的。

**Independent Test**: 可通过分别执行提取和转换命令，验证中间 SQLite 文件生成正确，且可独立使用来测试。

**Acceptance Scenarios**:

1. **Given** 用户有一个 .accdb 文件, **When** 用户执行 `destep extract input.accdb --output data.sqlite`, **Then** 系统生成包含所有表数据的 SQLite 文件
2. **Given** 用户有一个 SQLite 文件, **When** 用户执行 `destep convert data.sqlite --output building.idf`, **Then** 系统从 SQLite 生成 IDF 文件
3. **Given** 用户想保留中间文件, **When** 使用 `--keep-sqlite` 选项, **Then** 完整流程运行后 SQLite 文件被保留

---

### User Story 5 - IDF 文件解析与编辑 (Priority: P5)

用户需要解析现有 IDF 或 epJSON 文件，以便检查、修改或与其他数据合并。

**Why this priority**: 解析功能支持双向工作流和高级用例，但转换工具的核心是生成而非编辑。

**Independent Test**: 可通过解析一个现有 IDF 文件，修改某些参数，重新写入文件，验证修改被正确保存来测试。

**Acceptance Scenarios**:

1. **Given** 用户有一个 IDF 文件, **When** 系统解析该文件, **Then** 所有对象被正确加载为 Pydantic 模型实例
2. **Given** 用户有一个 epJSON 文件, **When** 系统解析该文件, **Then** 自动识别格式并正确加载
3. **Given** 用户修改了加载的模型, **When** 写入新文件, **Then** 更改被正确保存

---

### Edge Cases

- 当 .accdb 文件损坏或格式不受支持时，系统显示明确错误信息并建议检查文件完整性
- 当热区表面不形成封闭体积时，系统报告几何验证警告但仍生成 IDF（带警告注释）
- 当 DeST 数据库中存在缺失的外键引用时，系统跳过相关对象并记录警告
- 当单位转换后坐标过近（< 1e-10 米）时，系统自动合并或报告顶点精度警告
- 当 EnergyPlus 可执行文件不存在或路径错误时，模拟命令显示明确的安装指引

## Clarifications

### Session 2026-01-16

- Q: Schedule 数据如何处理和导出？ → A: DeST 的 schedule_year 包含 8760 小时数据，通过 Schedule:File 格式引用外部 CSV 文件，按实际引用按需导出（非全量导出 100+ 时间表）

## Requirements *(mandatory)*

### Functional Requirements

**数据提取与转换**:

- **FR-001**: 系统必须(MUST)能够读取 DeST .accdb 数据库文件并提取全部 141 个表的数据
- **FR-002**: 系统必须(MUST)将 DeST 数据转换为 EnergyPlus IDF 格式，支持以下对象类型：
  - Building, Site:Location
  - Zone (热区)
  - BuildingSurface:Detailed (墙、地面、屋顶)
  - FenestrationSurface:Detailed (窗、门)
  - Construction, Material (构造和材料)
  - Schedule:File (时间表，引用外部 CSV 文件存储 8760 小时逐时数据)
  - People, Lights, ElectricEquipment (内部得热)
  - ZoneHVAC:FourPipeFanCoil (风机盘管)
- **FR-003**: 系统必须(MUST)将中文对象名称转换为拼音，确保 IDF 文件的 ASCII 兼容性
- **FR-004**: 系统必须(MUST)正确进行单位转换（DeST 毫米 → EnergyPlus 米）
- **FR-005**: 系统必须(MUST)验证转换后的 IDF 对象引用完整性

**几何处理**:

- **FR-006**: 系统必须(MUST)按照 EnergyPlus GlobalGeometryRules 要求排列表面顶点（UpperLeftCorner + Counterclockwise）
- **FR-007**: 系统必须(MUST)为每个热区生成封闭的几何体（6 个表面：4 墙 + 地面 + 屋顶/天花板）
- **FR-008**: 系统必须(MUST)正确设置表面边界条件（Ground, Outdoors, Surface, Adiabatic）
- **FR-009**: 系统必须(MUST)为内墙和楼层间表面创建配对引用
- **FR-010**: 系统必须(MUST)确保窗户顶点完全位于父墙体表面内

**代码生成**:

- **FR-011**: 系统必须(MUST)从 Energy+.schema.epJSON 解析全部 800+ 对象类型定义
- **FR-012**: 系统必须(MUST)生成符合 Python 3.12+ 语法的 Pydantic v2 模型代码
- **FR-013**: 系统必须(MUST)按 EnergyPlus group 分类将模型组织到多个文件
- **FR-014**: 系统必须(MUST)生成对象类型注册表和字段顺序映射

**模拟运行**:

- **FR-015**: 系统必须(MUST)支持调用 EnergyPlus 可执行文件运行模拟
- **FR-016**: 系统必须(MUST)支持实时终端输出显示
- **FR-017**: 系统必须(MUST)支持可配置的超时控制
- **FR-018**: 系统必须(MUST)支持使用 joblib 并行运行多个模拟

**CLI**:

- **FR-019**: 系统必须(MUST)提供 `extract` 命令用于数据提取
- **FR-020**: 系统必须(MUST)提供 `convert` 命令用于数据转换
- **FR-021**: 系统必须(MUST)提供 `run` 命令用于完整流程
- **FR-022**: 系统必须(MUST)提供 `codegen` 命令用于代码生成
- **FR-023**: 系统必须(MUST)提供 `simulate` 命令用于模拟运行

### Key Entities

- **Building**: 建筑基本信息，包含名称、位置、方向等属性
- **Zone**: 热区，代表建筑中的独立热环境空间，关联到楼层和房间
- **Surface**: 建筑表面（墙、地面、屋顶），包含顶点坐标、边界条件、构造引用
- **Fenestration**: 门窗对象，关联到父表面，包含尺寸和玻璃/框架构造
- **Construction**: 构造层定义，由多层材料组成
- **Material**: 材料属性，包含热物性参数（导热系数、密度、比热等）
- **Schedule**: 时间表，定义随时间变化的数值（人员密度、照明功率等）。DeST 中的 `schedule_year` 包含 8760 小时的逐时数值数据（约 100+ 个时间表），转换时通过导出为 `Schedule:File` 格式引用外部 CSV 文件，仅导出实际被其他对象引用的时间表（按需导出），而非全量导出
- **InternalGains**: 内部得热（人员、照明、设备），关联到热区和时间表
- **HVACEquipment**: HVAC 设备（如风机盘管），关联到热区

### Assumptions

- EnergyPlus 版本为 24.2 或兼容版本
- DeST 数据库使用 Access 2007+ 格式（.accdb）
- 用户系统已安装 Java Runtime Environment（UCanAccess 依赖）
- 转换仅支持 Zone 级别 HVAC（风机盘管），不包括系统级 HVAC 设备
- 默认窗墙比为 0.3，窗台高度为 0.9 米（当原始数据缺失时）
- 坐标精度统一为 4 位小数

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 用户能够在 5 分钟内完成典型 DeST 项目（10 层建筑，100+ 热区）的转换流程
- **SC-002**: 转换生成的 IDF 文件能被 EnergyPlus 成功解析，无 Severe Error
- **SC-003**: 转换后的热区面积与原始 DeST 数据误差小于 1%
- **SC-004**: 代码生成工具能在 30 秒内生成全部 800+ 对象类型的 Pydantic 模型
- **SC-005**: 并行模拟运行支持至少 8 个同时进行的模拟任务
- **SC-006**: 90% 的常见 DeST 项目能够完整转换，无需手动干预
- **SC-007**: 几何验证能够检测并报告 95% 以上的表面顶点排序错误
