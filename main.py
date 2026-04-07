from pathlib import Path
from typing import Annotated

from typer import Option, Typer

from src.config import PathConfig
from src.utils import setup_logging

setup_logging()
app = Typer()


@app.command()
def extract(
    accdb_path: Annotated[
        Path, Option('--accdb', '-a', help='Path to the Access database')
    ],
    output_path: Annotated[
        Path | None, Option('--output', '-o', help='Path to the output SQLite database')
    ],
    driver_dir: Annotated[
        Path | None, Path, Option('--driver', '-d', help='Path to the driver directory')
    ],
):
    from src.database import DataExtractor

    path_config = PathConfig()
    output_path = (
        output_path or path_config.output_database_dir / f'{accdb_path.stem}.sqlite'
    )
    driver_dir = driver_dir or path_config.ucanaccess_path

    extractor = DataExtractor(
        accdb_path=accdb_path,
        sqlite_path=output_path,
        ucanaccess_path=driver_dir,
    )
    extractor.extract_all()


@app.command()
def extract_all(
    accdb_dir: Annotated[
        Path | None, Option('--accdb-dir', '-d', help='Path to the Access database directory')
    ] = None,
):
    path_config = PathConfig()
    accdb_dir = accdb_dir or path_config.database_dir
    for accdb_path in accdb_dir.glob('*.accdb'):
        extract(accdb_path, output_path=None, driver_dir=None)


@app.command()
def check_schema(
    accdb_path: Annotated[
        Path, Option('--accdb-path', '-a', help='Path to the Access database')
    ] = Path('examples/LH_Guangzhou_2015.accdb'),
    output_dir: Annotated[
        Path, Option('--output-dir', '-o', help='Path to the output directory')
    ] = Path('output'),
    driver_path: Annotated[
        Path, Option('--driver', '-d', help='Path to the driver directory')
    ] = Path('driver'),
):
    """Check database schema against SQLAlchemy models."""
    from src.database.schema_checker import SchemaChecker

    path_config = PathConfig()
    output_dir = output_dir or path_config.output_dir
    driver_path = driver_path or path_config.ucanaccess_path

    checker = SchemaChecker(
        accdb_path=accdb_path,
        ucanaccess_path=driver_path,
    )
    diff = checker.check()
    checker.generate_report(diff, output_dir / 'schema_diff_report.md')


@app.command()
def codegen(
    schema_path: Annotated[
        Path, Option('--schema-path', '-s', help='Path to the schema file')
    ] = Path('examples/Energy+.schema.epJSON'),
    output_dir: Annotated[
        Path, Option('--output-dir', '-o', help='Path to the output directory')
    ] = Path('src/idf/models/'),
):
    from src.codegen import ModelGenerator, SchemaParser

    parser = SchemaParser(schema_path=schema_path)
    specs = parser.parse()
    schema_version = parser.get_version()
    generator = ModelGenerator(output_dir=output_dir)
    generator.generate_all(specs, schema_version=schema_version)


@app.command()
def convert(
    sqlite_path: Annotated[
        Path, Option('--sqlite-path', '-s', help='Path to the SQLite database')
    ],
    output_path: Annotated[
        Path | None, Option('--output-path', '-o', help='Path to the output IDF file')
    ],
):
    from src.converters import ConverterManager
    from src.database import SQLiteManager

    path_config = PathConfig()
    output_path = (
        output_path
        or path_config.idf_dir / f'{sqlite_path.stem}/{sqlite_path.stem}.idf'
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    building_type = sqlite_path.stem.split('_')[0]

    with SQLiteManager(sqlite_path) as db:
        session = db.session
        converter_manager = ConverterManager(session, building_type=building_type)
        _idf = converter_manager.convert(output_path=output_path, save=True)


@app.command()
def convert_all(
    sqlite_dir: Annotated[
        Path | None, Option('--sqlite-dir', '-s', help='Path to the SQLite database directory')
    ] = None,
):
    path_config = PathConfig()
    sqlite_dir = sqlite_dir or path_config.output_database_dir
    for sqlite_path in sqlite_dir.glob('*.sqlite'):
        convert(sqlite_path, output_path=None)


@app.command()
def run(
    idf_path: Annotated[Path, Option('--idf', '-i', help='Path to the IDF file')],
    weather_path: Annotated[
        Path, Option('--weather', '-w', help='Path to the EPW weather file')
    ],
    output_dir: Annotated[
        Path,
        Option('--output-dir', '-o', help='Output directory for simulation results'),
    ],
):
    from src.idf import IDF

    path_config = PathConfig()
    output_dir = output_dir or path_config.output_dir / 'simulation'

    idf = IDF()
    raise SystemExit(idf.run(idf_path, weather_path, output_dir))


if __name__ == '__main__':
    app()
