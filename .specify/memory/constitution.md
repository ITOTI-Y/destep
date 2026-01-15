<!--
Sync Impact Report
==================
Version change: 1.0.0 (initial)
Added sections:
  - 8 Core Principles
  - Technology Stack Requirements
  - Development Workflow
  - Governance Rules
Templates requiring updates:
  - .specify/templates/plan-template.md ✅ (Constitution Check section aligned)
  - .specify/templates/spec-template.md ✅ (Requirements section aligned)
  - .specify/templates/tasks-template.md ✅ (Phase structure aligned)
Follow-up TODOs: None
-->

# destep-py Constitution

DeST to EnergyPlus IDF 转换工具的开发治理原则

## Core Principles

### I. Modern Python First

项目必须(MUST)使用 Python 3.12+ 现代语法和特性。

**规范要求**：
- 类型联合使用 `X | Y` 语法，禁止 `Union[X, Y]`
- 泛型使用 `list[T]`、`dict[K, V]`，禁止从 `typing` 导入 `List`、`Dict`
- 所有公共函数必须(MUST)有完整的类型注解
- 使用 `ruff` 进行代码检查和格式化

**示例**：
```python
# 正确
def process(data: dict[str, Any], items: list[str] | None = None) -> bool: ...

# 错误 - 禁止
from typing import Dict, List, Optional
def process(data: Dict[str, Any], items: Optional[List[str]] = None) -> bool: ...
```

### II. Code Generation Over Manual Maintenance

EnergyPlus IDF 模型必须(MUST)通过代码生成工具从 `Energy+.schema.epJSON` 自动生成，禁止手动维护。

**规范要求**：
- 所有 800+ EnergyPlus 对象类型必须(MUST)自动生成
- 生成的代码必须(MUST)包含 `DO NOT EDIT MANUALLY` 注释
- 模型按 EnergyPlus group 分文件组织
- 生成器必须(MUST)同时生成类型注册表和字段顺序映射

**命令**：
```bash
destep codegen --schema examples/Energy+.schema.epJSON --output src/idf/models/
```

### III. Modular Architecture

项目必须(MUST)遵循清晰的模块划分，每个模块职责单一。

**模块结构**：
```
src/
├── codegen/          # 代码生成工具（解析 schema，生成模型）
├── idf/              # IDF 核心模块（模型、解析、写入、运行）
├── database/         # DeST 数据库层（ORM、读取、提取）
├── converters/       # DeST → EnergyPlus 转换器
└── utils/            # 工具函数（日志、拼音转换）
```

**规范要求**：
- 每个模块必须(MUST)有独立的 `__init__.py` 导出公共 API
- 模块间依赖必须(MUST)单向：`cli → converters → (idf, database) → utils`
- 禁止循环依赖

### IV. Pydantic for Data Validation

所有数据模型必须(MUST)使用 Pydantic v2 进行验证。

**规范要求**：
- IDF 模型必须(MUST)继承自统一的 `IDFBaseModel` 基类
- 必须(MUST)配置 `extra="forbid"` 防止未知字段
- 必须(MUST)配置 `validate_assignment=True` 启用赋值验证
- 字段约束（如 `ge=0`, `le=1`）必须(MUST)在模型中声明

**标准配置**：
```python
model_config = ConfigDict(
    populate_by_name=True,
    extra="forbid",
    validate_assignment=True,
    str_strip_whitespace=True,
)
```

### V. SQLAlchemy 2.0 for Database

数据库访问必须(MUST)使用 SQLAlchemy 2.0 ORM 风格。

**规范要求**：
- 使用 `Mapped[T]` 和 `mapped_column()` 声明字段
- 模型按功能分文件：building, geometry, construction, fenestration, hvac, schedule, gains, environment
- 外键关系必须(MUST)使用 `relationship()` 声明
- 所有模型必须(MUST)在 `models/__init__.py` 中导出

### VI. Converter Pattern

DeST 到 EnergyPlus 的转换必须(MUST)遵循统一的转换器模式。

**规范要求**：
- 所有转换器必须(MUST)继承 `BaseConverter[T]` 基类
- 必须(MUST)实现 `convert_all()` 和 `convert_one()` 方法
- 必须(MUST)使用 `ConversionStats` 跟踪转换统计
- 转换顺序必须(MUST)考虑依赖关系（如：构造 → 区域 → 表面）

**转换器链**：
```
BuildingConverter → ScheduleConverter → ConstructionConverter
→ ZoneConverter → SurfaceConverter → FenestrationConverter
→ GainsConverter → HVACZoneConverter
```

### VII. Simplicity Over Abstraction

避免过度封装，直接使用标准库和第三方库 API。

**规范要求**：
- 禁止为简单操作创建包装函数（如 `create_directory()` 包装 `Path.mkdir()`）
- 只在以下情况创建抽象：
  - 逻辑确实复杂且需要复用
  - 需要统一的接口规范（如 Converter 基类）
  - 涉及状态管理
- 异常应尽早抛出，让调用方处理

**示例**：
```python
# 正确 - 直接使用
output_dir.mkdir(parents=True, exist_ok=True)
timestamp = time.strftime("%Y%m%d_%H%M%S")

# 错误 - 过度封装
def create_dir_if_not_exists(path):
    Path(path).mkdir(parents=True, exist_ok=True)
```

### VIII. Logging with loguru

所有日志必须(MUST)使用 loguru，禁止使用标准 logging 模块。

**规范要求**：
- 使用 `logger.info/debug/warning/error` 记录日志
- 错误日志必须(MUST)包含 `exc_info=True`
- 禁止使用 `print()` 输出运行时信息
- 日志格式必须(MUST)包含时间、级别、模块、行号

## Technology Stack Requirements

项目必须(MUST)使用以下技术栈：

| 类别 | 技术选型 | 版本要求 |
|------|----------|----------|
| Python | Python | >= 3.12 |
| 类型验证 | Pydantic | v2.10+ |
| 数据库 ORM | SQLAlchemy | 2.0+ |
| CLI | Typer | 0.15+ |
| 日志 | loguru | 0.7+ |
| Access 读取 | UCanAccess + jaydebeapi | 5.x |
| 代码检查 | ruff | 0.8+ |
| 模板引擎 | Jinja2 | 3.1+ |
| 并行计算 | joblib | 1.4+ |

**ruff 配置**：
```toml
[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP", "SIM", "RUF", "N"]
ignore = ["E501", "N805", "N806"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
docstring-code-format = true
```

## Development Workflow

### 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 变量/函数 | snake_case | `user_name`, `get_data()` |
| 类 | PascalCase | `DataProcessor`, `ZoneConverter` |
| 常量 | UPPER_SNAKE_CASE | `MAX_RETRY`, `MM_TO_M` |
| Schema 类 | 添加 Schema 后缀 | `UserSchema`, `ZoneSchema` |
| 模型文件 | 小写下划线 | `building.py`, `hvac_zone.py` |

### Git 提交规范

使用 Conventional Commits 格式：`<type>(<scope>): <description>`

**类型**：
- `feat`: 新功能
- `fix`: 修复
- `docs`: 文档
- `refactor`: 重构
- `perf`: 性能优化
- `chore`: 构建/工具

**示例**：
```
feat(converter): add HVAC zone converter support
fix(parser): correct IDF field order parsing
refactor(codegen): split model generator by group
```

### 工具使用

**包管理（uv）**：
```bash
uv init project-name
uv add package
uv add --dev ruff
uv sync
uv run python script.py
uv run ruff check --fix . && uv run ruff format .
```

**CLI（Typer）**：
```python
from typer import Typer, Option, Argument

app = Typer(name="destep", help="DeST to EnergyPlus converter")

@app.command()
def convert(
    input_path: Path = Argument(..., help="Input file"),
    output: Path = Option(None, "--output", "-o"),
) -> None:
    """Convert DeST to IDF."""
    ...
```

### 文档字符串

仅在复杂函数添加，使用 Google 风格（英文）：

```python
def process_data(data: dict[str, Any], threshold: float = 0.5) -> ProcessResult:
    """Process input data and return result.

    Args:
        data: Input data dictionary.
        threshold: Filter threshold.

    Returns:
        Processed result object.

    Raises:
        ValidationError: If data validation fails.
    """
```

## Governance

### 原则优先级

Constitution 中的原则是项目开发的最高准则，所有代码审查必须(MUST)验证是否符合这些原则。

### 修订流程

1. 提出修订需求并说明理由
2. 更新 constitution.md 文档
3. 更新版本号（遵循语义化版本）
4. 更新受影响的模板文件
5. 提交 PR 并获得批准

### 版本规则

- **MAJOR**: 原则删除或重新定义（不兼容）
- **MINOR**: 新增原则或章节
- **PATCH**: 措辞修正、错别字修复

### 复杂度审查

任何违反原则的情况必须(MUST)在 PR 中明确说明理由：

| 违反项 | 需要说明 | 拒绝的替代方案 |
|--------|----------|----------------|
| 新增抽象层 | 为什么需要 | 直接实现为何不足 |
| 跳过代码生成 | 特殊情况 | 生成器为何不适用 |
| 非标准技术栈 | 必要性 | 标准栈为何不满足 |

**Version**: 1.0.0 | **Ratified**: 2026-01-15 | **Last Amended**: 2026-01-15
