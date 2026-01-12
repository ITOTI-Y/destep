# destep-py

DeST to EnergyPlus IDF converter.

## Features

- Convert DeST (.accdb) building models to EnergyPlus IDF format
- Type-safe Pydantic models generated from EnergyPlus schema
- Parallel simulation support with joblib

## Requirements

- Python 3.12+
- UCanAccess (for reading Access databases)
- EnergyPlus (for running simulations)

## Installation

```bash
uv sync
```