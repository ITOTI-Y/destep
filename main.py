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
    ] = Path('database/LH_Guangzhou_2015.accdb'),
    output_path: Annotated[
        Path, Option('--output', '-o', help='Path to the output SQLite database')
    ] = Path('output/destep.sqlite'),
    driver_dir: Annotated[
        Path, Option('--driver', '-d', help='Path to the driver directory')
    ] = Path('driver'),
):
    from src.database import DataExtractor

    path_config = PathConfig()
    output_path = output_path or path_config.output_dir / 'destep.sqlite'
    driver_dir = driver_dir or path_config.ucanaccess_path

    extractor = DataExtractor(
        accdb_path=accdb_path,
        sqlite_path=output_path,
        ucanaccess_path=driver_dir,
    )
    extractor.extract_all()


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
    from src.database.schema_checker import SchemaChecker

    """Check database schema against SQLAlchemy models."""
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
    output_path: Annotated[
        Path, Option('--output-path', '-o', help='Path to the output IDF file')
    ] = Path('output/destep.idf'),
    sqlite_path: Annotated[
        Path, Option('--sqlite-path', '-s', help='Path to the SQLite database')
    ] = Path('output/destep.sqlite'),
):
    from src.converters import ConverterManager
    from src.database import SQLiteManager

    with SQLiteManager(sqlite_path) as db:
        session = db.session
        converter_manager = ConverterManager(session)
        idf = converter_manager.convert()
        idf.save(output_path)


if __name__ == '__main__':
    app()
