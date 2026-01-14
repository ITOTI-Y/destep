# destep-py

DeST to EnergyPlus IDF converter.

## Features

- Convert DeST (.accdb) building models to EnergyPlus IDF format
- Type-safe Pydantic models generated from EnergyPlus schema
- Parallel simulation support with joblib
- Code generation tools for EnergyPlus Pydantic models

## Requirements

- Python 3.12+
- UCanAccess (for reading Access databases)
- EnergyPlus (for running simulations)

## Installation

```bash
uv sync
```

## Project Structure

```
src/
├── codegen/           # EnergyPlus schema code generation
│   ├── schema_parser.py      # Parse EnergyPlus JSON schema
│   ├── field_parser.py       # Parse field definitions
│   ├── model_generator.py    # Generate Pydantic models
│   ├── template_filters.py   # Jinja2 template filters
│   └── templates/            # Jinja2 templates
├── database/          # Database operations
│   ├── accdb_reader.py       # Read Access (.accdb) files via UCanAccess
│   ├── extractor.py          # Extract data from Access to SQLite
│   ├── sqlite_manager.py     # SQLite session management
│   └── models/               # SQLAlchemy ORM models
├── idf/               # EnergyPlus IDF models
│   └── models/               # Auto-generated Pydantic models
└── utils/             # Utility functions
```

## Usage

### Code Generation

Generate Pydantic models from EnergyPlus schema:

```python
from pathlib import Path
from src.codegen import ModelGenerator
from src.codegen.schema_parser import SchemaParser

# Parse EnergyPlus schema
parser = SchemaParser(Path('Energy+.schema.epJSON'))
specs = parser.parse()

# Generate Pydantic models
generator = ModelGenerator(Path('src/idf/models'))
generator.generate_all(specs, schema_version='24.2.0')
```

### Data Extraction

Extract DeST data from Access database:

```python
from pathlib import Path
from src.database import DataExtractor

extractor = DataExtractor(
    accdb_path=Path('building.accdb'),
    sqlite_path=Path('output.db'),
    ucanaccess_path=Path('/path/to/UCanAccess'),
)
extractor.extract_all()
```

## Dependencies

- `jaydebeapi` - JDBC database connectivity
- `jpype1` - Java bridge for UCanAccess
- `jinja2` - Template engine for code generation
- `loguru` - Logging
- `pypinyin` - Chinese pinyin conversion
- `sqlalchemy` - ORM for database operations
- `typer` - CLI framework