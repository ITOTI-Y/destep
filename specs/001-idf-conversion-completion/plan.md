# Implementation Plan: IDF Conversion Completion

**Branch**: `001-idf-conversion-completion` | **Date**: 2026-01-27 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-idf-conversion-completion/spec.md`

## Summary

完成 DeST 到 EnergyPlus IDF 的转换功能，包括：
1. 内部热收益转换 (People, Lights, ElectricEquipment)
2. 简化 HVAC 系统 (HVACTemplate:Zone:IdealLoadsAirSystem)
3. 新风/通风配置
4. 日程表自动收集
5. 门接口保留
6. **Sizing Period 自动添加** (新增) - 根据建筑位置自动添加设计日数据

## Technical Context

**Language/Version**: Python >= 3.12
**Primary Dependencies**: Pydantic 2.x, SQLAlchemy 2.x, Loguru, Typer
**Storage**: SQLite (DeST database)
**Testing**: pytest
**Target Platform**: Linux/Windows
**Project Type**: Single project
**Performance Goals**: N/A (batch processing)
**Constraints**: src/idf/models/ 目录不允许修改
**Scale/Scope**: 单个建筑模型转换

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Modern Python Syntax**: Uses Python 3.12+ features (`X | Y`, `list[T]`, `dict[K, V]`)
- [x] **No Over-Abstraction**: No unnecessary wrappers; direct library API usage
- [x] **SOTA Libraries First**: Using Pydantic, SQLAlchemy, Loguru
- [x] **Clean Code**: No inline comments; self-documenting names
- [x] **Conventional Commits**: Commit messages follow `<type>(<scope>): <description>`
- [x] **Fail-Fast**: Exceptions raised early with clear context

## Project Structure

### Documentation (this feature)

```text
specs/001-idf-conversion-completion/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── converters/
│   ├── base.py              # BaseConverter 抽象基类
│   ├── manager.py           # ConverterManager + LookupTable
│   ├── internal_gains.py    # 内部热收益转换 (US1)
│   ├── schedule.py          # 日程表转换 (US4)
│   ├── hvac.py              # HVAC 系统转换 (US2, US3)
│   ├── fenestration.py      # 门窗转换 (US5)
│   └── sizing.py            # Sizing Period 转换 (US6) [NEW]
├── database/
│   └── models/
│       ├── environment.py   # Environment, SysCity 位置信息
│       └── ...
├── idf/
│   └── models/
│       ├── location.py      # SizingPeriodDesignDay 模型
│       └── ...
└── data/
    └── ddy/                 # 内嵌 DDY 数据 [NEW]
        └── china_cities.json  # 中国主要城市设计日参数
```

**Structure Decision**: 单项目结构，新增 `src/converters/sizing.py` 用于 Sizing Period 转换，新增 `src/data/ddy/` 目录存放内嵌的设计日数据。

## User Story 6: Sizing Period Auto-Add - Technical Design

### Overview

SizingPeriod:DesignDay 是 EnergyPlus 进行 HVAC 系统设计计算的必要输入。设计日数据包含典型极端气候条件下的气象参数，用于计算供暖/制冷设计负荷。

### DDY Data Source Strategy

**数据来源优先级**：
1. **内嵌数据** (推荐): 将中国主要城市的 DDY 数据预处理并以 JSON 格式内嵌在 `src/data/ddy/china_cities.json`
2. **EnergyPlus 官方源**: 作为备选，可从 [energyplus.net/weather](https://energyplus.net/weather) 或 [climate.onebuilding.org](https://climate.onebuilding.org/) 获取

**内嵌数据格式** (JSON):
```json
{
  "Beijing": {
    "winter_design_day": {
      "name": "Beijing Heating 99% Design Day",
      "month": 1,
      "day_of_month": 21,
      "day_type": "WinterDesignDay",
      "maximum_dry_bulb_temperature": -9.6,
      "daily_dry_bulb_temperature_range": 0,
      "humidity_condition_type": "WetBulb",
      "wetbulb_or_dewpoint_at_maximum_dry_bulb": -12.6,
      "wind_speed": 2.1,
      "wind_direction": 0,
      "solar_model_indicator": "ASHRAEClearSky",
      "sky_clearness": 0.0
    },
    "summer_design_day": {
      "name": "Beijing Cooling 1% Design Day",
      "month": 7,
      "day_of_month": 21,
      "day_type": "SummerDesignDay",
      "maximum_dry_bulb_temperature": 33.5,
      "daily_dry_bulb_temperature_range": 10.0,
      "humidity_condition_type": "WetBulb",
      "wetbulb_or_dewpoint_at_maximum_dry_bulb": 26.4,
      "wind_speed": 3.4,
      "wind_direction": 180,
      "solar_model_indicator": "ASHRAETau2017",
      "ashrae_clear_sky_optical_depth_for_beam_irradiance_taub": 0.556,
      "ashrae_clear_sky_optical_depth_for_diffuse_irradiance_taud": 1.779
    }
  }
}
```

### SizingConverter Implementation

**类设计**：
```python
class SizingConverter(BaseConverter[Environment]):
    """Converter for adding SizingPeriod:DesignDay objects.

    Reads building location from DeST Environment/SysCity tables,
    matches to embedded DDY data, and creates design day IDF objects.
    """

    def __init__(self, session, idf, lookup_table, pinyin=None):
        super().__init__(session, idf, lookup_table, pinyin)
        self._ddy_data = self._load_embedded_ddy_data()

    def _load_embedded_ddy_data(self) -> dict:
        """Load embedded DDY data from JSON file."""

    def _match_city(self, environment: Environment) -> str | None:
        """Match DeST environment to DDY city name."""

    def _create_design_day(self, params: dict) -> SizingPeriodDesignDay:
        """Create SizingPeriodDesignDay from parameter dict."""

    def convert_all(self) -> None:
        """Convert sizing periods for the project."""

    def convert_one(self, instance: Environment) -> bool:
        """Add design days based on environment location."""
```

**城市匹配逻辑**：
1. 优先使用 `Environment.city_name` 直接匹配
2. 通过 `Environment.city_id` 关联 `SysCity.name` / `SysCity.cname` 匹配
3. 无匹配时使用默认城市 (Beijing) 并发出警告

### Integration with ConverterManager

SizingConverter 应在其他转换器之前执行，因为设计日数据是模拟配置的基础：

```
SizingConverter (Phase 0) → BuildingConverter → ZoneConverter → ...
```

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| 内嵌 DDY JSON 数据 | 避免运行时网络依赖，提高可靠性 | 实时下载可能失败，且增加外部依赖 |
