# Implementation Plan: destep-py 项目重写

**Branch**: `001-destep-rewrite` | **Date**: 2026-01-15 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-destep-rewrite/spec.md`

## Summary

将 DeST 建筑能耗模拟数据转换为 EnergyPlus IDF 格式的完整工具链重写。核心功能包括：
- 从 EnergyPlus JSON Schema 自动生成 800+ Pydantic 模型（已完成）
- 从 DeST .accdb 数据库提取数据到 SQLite（已完成）
- 实现 8 个类型的转换器将 DeST 数据转换为 IDF 对象（待实现）
- IDF 文件解析、写入和 EnergyPlus 模拟运行（待实现）
- 完整的 CLI 命令集（部分完成）

**已完成节点**: Node 1.1 - 2.5（Phase 1 + Phase 2 全部完成）
**待实现节点**: Node 3.1 - 5.3（Phase 3 + Phase 4 + Phase 5）

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: Pydantic v2.10+, SQLAlchemy 2.0+, Typer 0.15+, loguru 0.7+, Jinja2 3.1+, joblib 1.4+
**Storage**: SQLite（中间存储）, IDF（输出格式）
**Target Platform**: Linux/Windows/macOS（跨平台 CLI 工具）
**Project Type**: Single project (CLI tool)
**Performance Goals**:
- 5 分钟内完成 100+ 热区建筑转换
- 30 秒内生成 800+ Pydantic 模型
- 支持 8 个并行模拟任务
**Constraints**:
- IDF 字段顺序必须与 EnergyPlus Schema 一致
- 坐标精度统一为 4 位小数
- 转换后热区面积误差 < 1%
**Scale/Scope**: 800+ IDF 对象类型, 143 个 DeST 数据表, 8 个转换器

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Modern Python First | ✅ PASS | 使用 Python 3.12+ 语法，`X \| Y` 联合类型 |
| II. Code Generation Over Manual Maintenance | ✅ PASS | IDF 模型已从 Schema 自动生成，含 `_refs.py` 引用验证 |
| III. Modular Architecture | ✅ PASS | 清晰的模块划分：codegen, idf, database, converters, utils |
| IV. Pydantic for Data Validation | ✅ PASS | 所有 IDF 模型继承 `IDFBaseModel`，配置 `extra="forbid"` |
| V. SQLAlchemy 2.0 for Database | ✅ PASS | 使用 `Mapped[T]` 和 `mapped_column()` |
| VI. Converter Pattern | ⏳ PENDING | 待 Phase 4 实现 `BaseConverter[T]` |
| VII. Simplicity Over Abstraction | ✅ PASS | 直接使用标准库和第三方库 API |
| VIII. Logging with loguru | ✅ PASS | 使用 `logger.info/debug/warning/error` |

## Project Structure

### Documentation (this feature)

```text
specs/001-destep-rewrite/
├── plan.md              # 本文件
├── research.md          # 技术研究记录
├── data-model.md        # 数据模型设计
├── quickstart.md        # 快速开始指南
├── contracts/           # 接口契约定义
└── tasks.md             # 任务列表（/speckit.tasks 生成）
```

### Source Code (repository root)

```text
src/
├── codegen/              # ✅ 已完成 - 代码生成工具
│   ├── __init__.py
│   ├── field_parser.py   # 字段解析器
│   ├── schema_parser.py  # Schema 解析器
│   ├── model_generator.py # 模型生成器
│   └── templates/        # Jinja2 模板
│
├── database/             # ✅ 已完成 - 数据库层
│   ├── __init__.py
│   ├── accdb_reader.py   # Access 数据库读取器
│   ├── sqlite_manager.py # SQLite 管理器
│   ├── extractor.py      # 数据提取器
│   └── models/           # 143 个 SQLAlchemy 模型
│
├── idf/                  # ⏳ 待实现 - IDF 核心模块
│   ├── __init__.py       # 导出 IDF 类
│   ├── models/           # ✅ 已完成 - 生成的 Pydantic 模型
│   │   ├── __init__.py   # OBJECT_TYPE_REGISTRY, FIELD_ORDER_REGISTRY, SCHEMA_VERSION
│   │   ├── _base.py      # IDFBaseModel 基类
│   │   ├── _refs.py      # ✅ 已完成 - 引用验证类型定义
│   │   └── *.py          # 44+ 模型文件
│   ├── idf.py            # ⏳ Node 3.1 - 统一的 IDF 类
│   └── runner.py         # ⏳ Node 3.2/3.3 - EnergyPlus 运行器
│
├── converters/           # ⏳ 待实现 - 转换器
│   ├── __init__.py
│   ├── base.py           # ⏳ Node 4.1 - 转换器基类
│   ├── building.py       # ⏳ Node 4.2 - Building 转换器
│   ├── schedule.py       # ⏳ Node 4.3 - Schedule 转换器
│   ├── construction.py   # ⏳ Node 4.4 - Construction 转换器
│   ├── zone.py           # ⏳ Node 4.5 - Zone 转换器
│   ├── surface.py        # ⏳ Node 4.6 - Surface 转换器
│   ├── fenestration.py   # ⏳ Node 4.7 - Fenestration 转换器
│   ├── gains.py          # ⏳ Node 4.8 - Gains 转换器
│   ├── hvac_zone.py      # ⏳ Node 4.9 - HVAC Zone 转换器
│   └── manager.py        # ⏳ Node 4.10 - 转换管理器
│
├── utils/                # ✅ 已完成 - 工具函数
│   ├── __init__.py
│   ├── log.py            # loguru 日志配置
│   └── pinyin.py         # 拼音转换器
│
└── config.py             # ✅ 已完成 - 路径配置

main.py                   # ⏳ 部分完成 - CLI 入口
                          # ✅ extract, codegen
                          # ⏳ convert, run, simulate
```

**Structure Decision**: 采用 Single project 结构，所有源代码位于 `src/` 目录下，按功能模块划分。

---

## Phase 3: IDF 核心模块实现

### Node 3.1: IDF 统一类

**目标**: 实现统一的 IDF 类，整合对象容器、IDF 文件读写功能

**输出**: `src/idf/idf.py`

**核心接口**:
```python
class IDF:
    """EnergyPlus IDF 文件统一接口。

    整合对象容器、IDF 文件读写功能为一体。
    引用验证通过 _refs.py 中的 RefValidator 在添加时自动完成。
    """

    def __init__(self):
        self._objects: dict[str, dict[str, IDFBaseModel]] = {}

    @property
    def version(self) -> str:
        """从 SCHEMA_VERSION 常量获取版本号。"""
        from src.idf.models import SCHEMA_VERSION
        return SCHEMA_VERSION

    # ========== 对象管理 ==========

    def add(self, obj: IDFBaseModel) -> None:
        """添加对象。"""

    def get(self, object_type: str, name: str) -> IDFBaseModel | None:
        """获取对象。"""

    def has(self, object_type: str, name: str) -> bool:
        """检查对象是否存在。"""

    def all_of_type(self, object_type: str) -> dict[str, IDFBaseModel]:
        """获取某类型的所有对象。"""

    def __iter__(self) -> Iterator[IDFBaseModel]:
        """迭代所有对象。"""

    def __len__(self) -> int:
        """返回对象总数。"""

    # ========== IDF 文件读写 ==========

    @classmethod
    def load(cls, path: Path) -> "IDF":
        """从 IDF 文件加载。"""

    def save(self, path: Path) -> None:
        """保存到 IDF 文件。"""
```

**IDF 写入格式**:
- 使用 `FIELD_ORDER_REGISTRY` 确保字段顺序正确
- 浮点数格式: `{value:.6g}`
- 布尔值转换: `True` → `"Yes"`, `False` → `"No"`
- 注释行以 `!` 开头

**IDF 解析规则**:
- 移除 `!` 开头的注释
- 对象以 `;` 结束
- 字段以 `,` 分隔
- 使用 `OBJECT_TYPE_REGISTRY` 实例化对象

**验收标准**:
- [ ] 防止重复添加同名对象
- [ ] version 从 `SCHEMA_VERSION` 常量获取
- [ ] 引用验证通过 `_refs.py` 中的 RefValidator 自动完成（FR-005 覆盖：IDF 对象引用完整性验证由 RefValidator 在 Pydantic 模型层自动处理，无需显式任务）
- [ ] `load()` 能正确解析 IDF 文件
- [ ] `save()` 输出能被 EnergyPlus 解析

**依赖**: Node 2.4（IDF 模型生成，含 `_refs.py`）

---

### Node 3.2: EnergyPlus 运行器

**目标**: 单模拟运行，支持实时输出

**输出**: `src/idf/runner.py`

**核心接口**:
```python
@dataclass
class RunnerConfig:
    energyplus_path: Path
    timeout_seconds: int = 7200
    output_dir: Path | None = None

@dataclass
class SimulationResult:
    success: bool
    return_code: int
    stdout: str
    stderr: str
    output_files: dict[str, Path]
    duration_seconds: float

class EnergyPlusRunner:
    def run(
        self,
        idf_path: Path,
        weather_file: Path | None = None,
        realtime_output: bool = False,
    ) -> SimulationResult:
        """运行单个模拟。"""
```

**验收标准**:
- [ ] 实时输出到终端
- [ ] 超时自动终止进程
- [ ] 返回所有输出文件路径
- [ ] 正确处理 EnergyPlus 返回码

**依赖**: Node 3.1

---

### Node 3.3: 并行运行器

**目标**: 使用 joblib 并行运行多个模拟

**输出**: `src/idf/runner.py`（续）

**核心接口**:
```python
@dataclass
class BatchResult:
    total: int
    succeeded: int
    failed: int
    results: list[SimulationResult]

class ParallelRunner:
    def run_batch(
        self,
        idf_files: list[Path],
        weather_file: Path | None = None,
    ) -> BatchResult:
        """批量运行多个模拟。"""

    def run_parametric(
        self,
        base_idf: IDF,
        parameter_sets: list[dict],
        modifier_func: Callable[[IDF, dict], IDF],
        weather_file: Path | None = None,
    ) -> BatchResult:
        """参数化运行。"""
```

**验收标准**:
- [ ] 并行数可配置 (`n_jobs`)
- [ ] 每个模拟独立输出目录
- [ ] 参数化运行支持自定义修改函数

**依赖**: Node 3.2

---

### Node 3.4: Simulate CLI 命令

**目标**: 添加 `destep simulate` 命令

**输出**: `main.py`（续）

**命令接口**:
```bash
# 单文件模拟
destep simulate input.idf --weather weather.epw [--output results/] [--realtime]

# 批量模拟
destep simulate --batch buildings/ --weather weather.epw [--jobs 4]
```

**验收标准**:
- [ ] 单文件和批量模式
- [ ] 进度条显示
- [ ] 结果汇总输出

**依赖**: Node 3.3

---

## Phase 4: 转换器实现

### Node 4.1: 转换器基类

**目标**: 定义转换器抽象基类和工具类

**输出**: `src/converters/base.py`

**核心接口**:
```python
class UnitConverter:
    MM_TO_M = 0.001

    @staticmethod
    def mm_to_m(value: float | None) -> float:
        if value is None:
            return 0.0
        return value * UnitConverter.MM_TO_M

@dataclass
class ConversionStats:
    total: int = 0
    converted: int = 0
    skipped: int = 0
    errors: int = 0

class BaseConverter(ABC, Generic[T]):
    def __init__(
        self,
        session: Session,
        idf: IDF,
        pinyin: PinyinConverter,
    ):
        self.session = session
        self.idf = idf
        self.pinyin = pinyin
        self.stats = ConversionStats()

    @abstractmethod
    def convert_all(self) -> None:
        """转换所有对象。"""

    @abstractmethod
    def convert_one(self, instance: T) -> bool:
        """转换单个对象，返回是否成功。"""

    def make_name(
        self,
        prefix: str,
        id_: int,
        chinese_name: str | None = None,
    ) -> str:
        """生成对象名称。"""
```

**验收标准**:
- [ ] 统计信息正确累加
- [ ] 名称生成含拼音转换
- [ ] 泛型类型正确约束

**依赖**: Node 1.3（拼音工具）, Node 3.1（IDF 类）

---

### Node 4.2: Building 转换器

**目标**: DeST Building → EnergyPlus Building + Site:Location

**输出**: `src/converters/building.py`

**映射关系**:
| DeST 源 | IDF 对象 | IDF 字段 |
|---------|----------|----------|
| Building.name | Building | name |
| Building.north_axis | Building | north_axis |
| Environment.latitude | Site:Location | latitude |
| Environment.longitude | Site:Location | longitude |

**验收标准**:
- [ ] Building 对象正确生成
- [ ] Site:Location 坐标正确
- [ ] GlobalGeometryRules 配置正确

**依赖**: Node 4.1

---

### Node 4.3: Schedule 转换器

**目标**: DeST ScheduleYear → EnergyPlus Schedule:Compact

**输出**: `src/converters/schedule.py`

**验收标准**:
- [ ] 时间表类型正确
- [ ] 值范围验证
- [ ] ScheduleTypeLimits 自动生成

**依赖**: Node 4.1

---

### Node 4.4: Construction 转换器

**目标**: DeST SysOutwall/SysInwall/... → EnergyPlus Construction + Material

**输出**: `src/converters/construction.py`

**验收标准**:
- [ ] 材料层顺序正确（从外到内）
- [ ] 热物性参数单位转换正确
- [ ] 处理缺失材料

**依赖**: Node 4.1

---

### Node 4.5: Zone 转换器

**目标**: DeST Room → EnergyPlus Zone

**输出**: `src/converters/zone.py`

**验收标准**:
- [ ] 坐标 mm → m 转换正确
- [ ] 空房间跳过
- [ ] multiplier 正确设置

**依赖**: Node 4.1

---

### Node 4.6: Surface 转换器

**目标**: DeST Surface + MainEnclosure → EnergyPlus BuildingSurface:Detailed

**输出**: `src/converters/surface.py`

**关键实现**（参考 idf-geometry-guidelines.md）:

1. **顶点排序**: UpperLeftCorner + Counterclockwise（从外部观察逆时针）
2. **边界条件映射**:
   | 表面类型 | 位置 | Outside Boundary Condition |
   |----------|------|---------------------------|
   | Floor | 首层 | Ground |
   | Floor | 非首层 | Surface |
   | Roof | 顶层 | Outdoors |
   | Ceiling | 非顶层 | Surface |
   | Wall | 外墙 | Outdoors |
   | Wall | 内墙 | Surface |

3. **配对表面**: 内墙和楼层间表面必须成对定义

**验收标准**:
- [ ] 顶点顺序正确（逆时针）
- [ ] boundary_condition 映射正确
- [ ] construction_name 引用有效
- [ ] 配对表面正确引用

**依赖**: Node 4.4, Node 4.5

---

### Node 4.7: Fenestration 转换器

**目标**: DeST Window/Door → EnergyPlus FenestrationSurface:Detailed

**输出**: `src/converters/fenestration.py`

**关键约束**:
- 窗户顶点必须完全位于父墙体平面上
- 窗户边缘距墙边最小距离: 0.1m
- 默认窗台高度: 0.9m

**验收标准**:
- [ ] 父表面引用正确
- [ ] 尺寸在表面范围内
- [ ] 玻璃/门框构造正确

**依赖**: Node 4.6

---

### Node 4.8: Gains 转换器

**目标**: DeST OccupantGains/LightGains/EquipmentGains → EnergyPlus People/Lights/ElectricEquipment

**输出**: `src/converters/gains.py`

**验收标准**:
- [ ] 功率密度转换正确
- [ ] 时间表引用正确
- [ ] 辐射/对流比例设置

**依赖**: Node 4.3, Node 4.5

---

### Node 4.9: HVAC Zone 转换器

**目标**: DeST FanCoil → EnergyPlus ZoneHVAC:FourPipeFanCoil

**输出**: `src/converters/hvac_zone.py`

**验收标准**:
- [ ] 盘管参数正确
- [ ] 连接 ZoneHVAC:EquipmentList
- [ ] 温控器设定正确

**依赖**: Node 4.5

---

### Node 4.10: 转换管理器

**目标**: 协调所有转换器执行

**输出**: `src/converters/manager.py`

**核心接口**:
```python
class ConversionManager:
    CONVERTER_ORDER: list[tuple[str, type[BaseConverter]]] = [
        ("building", BuildingConverter),
        ("schedules", ScheduleConverter),
        ("constructions", ConstructionConverter),
        ("zones", ZoneConverter),
        ("surfaces", SurfaceConverter),
        ("fenestration", FenestrationConverter),
        ("gains", GainsConverter),
        ("hvac_zone", HVACZoneConverter),
    ]

    def convert(self) -> IDF:
        """执行所有转换器，返回 IDF 实例。"""

    def save(self, output_path: Path) -> None:
        """保存到 IDF 文件。"""
```

**验收标准**:
- [ ] 转换顺序正确（依赖关系）
- [ ] 汇总统计输出

**依赖**: Node 4.2 ~ 4.9

---

## Phase 5: CLI 和集成

### Node 5.1: Extract 命令优化

**目标**: 完善 `destep extract` 命令

**命令**: `destep extract input.accdb --output output.sqlite`

**依赖**: Node 1.8（已完成）

---

### Node 5.2: Convert 命令

**目标**: 添加 `destep convert` 命令

**命令**: `destep convert input.sqlite --output building.idf`

**依赖**: Node 4.10

---

### Node 5.3: Run 命令

**目标**: 添加 `destep run` 一站式命令

**命令**: `destep run input.accdb --output output/ [--keep-sqlite]`

**依赖**: Node 5.1, Node 5.2

---

## 执行顺序建议

### 关键路径

```
3.1 (IDF类) → 4.1 → 4.2/4.3/4.4/4.5 (并行) → 4.6 → 4.7 → 4.8/4.9 (并行) → 4.10 → 5.2 → 5.3
    │
    └──→ 3.2 → 3.3 → 3.4
```

### 可并行节点

| Phase | 可并行执行 |
|-------|-----------|
| 3 | 3.2 可与 4.1 并行（都依赖 3.1） |
| 4 | 4.2, 4.3, 4.4, 4.5 (在 4.1 完成后); 4.8, 4.9 (在 4.5 完成后) |
| 5 | - |

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 顶点排序错误 | EnergyPlus 几何错误 | 使用验证函数检查法向量方向 |
| 配对表面不匹配 | 热传递计算错误 | 创建配对时同步生成两个表面 |
| 外键引用缺失 | 转换中断 | RefValidator 记录警告，不阻止流程 |
| EnergyPlus 路径错误 | 模拟失败 | 提供明确的安装指引错误信息 |

## Complexity Tracking

> 本项目未违反 Constitution 原则，无需记录复杂度追踪。
