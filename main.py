from pathlib import Path
from typing import Annotated

from typer import Option, Typer

from src.config import PathConfig
from src.database import DataExtractor
from src.database.schema_checker import SchemaChecker
from src.utils import setup_logging

setup_logging()
app = Typer()


@app.command()
def extract(
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
    path_config = PathConfig()
    output_dir = output_dir or path_config.output_dir
    driver_path = driver_path or path_config.ucanaccess_path

    extractor = DataExtractor(
        accdb_path=accdb_path,
        sqlite_path=output_dir / 'destep.sqlite',
        ucanaccess_path=driver_path,
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
def main():
    pass


if __name__ == '__main__':
    app()
