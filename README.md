# destep

DeST to EnergyPlus IDF converter.

## Features

- Extract DeST (.accdb) building models to SQLite via UCanAccess
- Convert extracted data to EnergyPlus IDF using [idfpy](https://pypi.org/project/idfpy/) models
- Building-type-aware HVAC conversion via strategy pattern
- Parallel batch extraction with joblib
- Run EnergyPlus simulations directly from the CLI

## Requirements

- Python 3.12+
- Java runtime + UCanAccess JDBC driver (place under `driver/`, for reading Access databases)
- EnergyPlus (for running simulations)

## Installation

```bash
uv sync
```

## Usage

All commands are exposed through the `destep` Typer CLI (`cli.py`):

```bash
# Extract a single .accdb to SQLite
uv run destep extract --accdb building.accdb [--output output/database/building.sqlite] [--driver driver/]

# Batch extract all .accdb files in a directory (parallel, skips existing outputs)
uv run destep extract-all [--accdb-dir database/]

# Convert SQLite to IDF (building type is matched from file name tokens against known types, e.g. CoA_Guangzhou_2015 -> CoA)
uv run destep convert --sqlite-path output/database/building.sqlite [--output-path ...] [--ddy-path ...]

# Batch convert all SQLite files in a directory
uv run destep convert-all [--sqlite-dir output/database/]

# Run an EnergyPlus simulation
uv run destep run --idf model.idf --weather weather.epw --output-dir output/simulation

# Check .accdb schema against SQLAlchemy models
uv run destep check-schema --accdb-path examples/LH_Guangzhou_2015.accdb
```

## Configuration

Default paths resolve relative to the working directory and can be overridden via environment variables (see `src/config.py`):

| Variable | Default | Purpose |
|----------|---------|---------|
| `DESTEP_PROJECT_ROOT` | `.` | Project root |
| `DESTEP_DATABASE_DIR` | `database/` | Input .accdb files |
| `DESTEP_UCANACCESS_PATH` | `driver/` | UCanAccess JDBC driver |
| `DESTEP_OUTPUT_DIR` | `output/` | Run outputs |
| `DESTEP_DDY_DIR` | `output/ddy/` | Design day files |
| `DESTEP_WEATHER_DIR` | `output/weather/` | Weather files |
| `DESTEP_IDF_DIR` | `output/idf/` | Generated IDF files |
| `DESTEP_LOG_DIR` | `log/` | Log files |

## Project Structure

```
cli.py                 # Typer CLI entry point (extract / convert / run / check-schema)
src/
├── config.py          # PathConfig: env-overridable path configuration
├── database/          # Access -> SQLite extraction
│   ├── accdb_reader.py       # Read .accdb files via UCanAccess (JDBC)
│   ├── extractor.py          # Extract data from Access to SQLite
│   ├── schema_checker.py     # Diff .accdb schema against ORM models
│   ├── sqlite_manager.py     # SQLite session management
│   └── models/               # SQLAlchemy ORM models for DeST tables
├── converters/        # SQLite -> IDF conversion
│   ├── manager.py            # ConverterManager: orchestrates all converters
│   ├── building.py           # Building, site, and global settings
│   ├── zone.py               # Thermal zones
│   ├── surface.py            # Building surfaces and geometry
│   ├── fenestration.py       # Windows and doors
│   ├── construction.py       # Constructions and materials
│   ├── schedule.py           # Schedules
│   ├── internal_gains.py     # People, lights, equipment
│   ├── hvac.py               # HVAC systems
│   ├── hvac_strategy.py      # Building-type-aware HVAC strategies
│   └── sizing.py             # Sizing parameters (uses DDY design days)
└── utils/             # Logging, pinyin conversion, DDY download
```

EnergyPlus IDF models are provided by the external `idfpy` package (type-safe Pydantic models generated from the EnergyPlus schema).

## Dependencies

- `idfpy` - EnergyPlus IDF Pydantic models and simulation runner
- `jaydebeapi` + `jpype1` - JDBC bridge to UCanAccess for reading Access databases
- `sqlalchemy` - ORM for the intermediate SQLite database
- `joblib` - Parallel batch extraction
- `trimesh` + `mapbox-earcut` + `scipy` - Geometry processing
- `pypinyin` - Chinese pinyin conversion for object naming
- `httpx` + `timezonefinder` - DDY/weather file download utilities
- `typer` - CLI framework
- `loguru` - Logging
