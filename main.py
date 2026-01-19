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
        Path, Option('--accdb-path', '-a', help='Path to the Access database')
    ] = Path('examples/LH_Guangzhou_2015.accdb'),
    output_dir: Annotated[
        Path, Option('--output-dir', '-o', help='Path to the output directory')
    ] = Path('output'),
    driver_path: Annotated[
        Path, Option('--driver', '-d', help='Path to the driver directory')
    ] = Path('driver'),
):
    from src.database import DataExtractor

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
def convert():
    from src.converters import (
        BuildingConverter,
        ConstructionConverter,
        ScheduleConverter,
        SurfaceConverter,
        ZoneConverter,
    )
    from src.database import SQLiteManager
    from src.idf import IDF
    from src.utils.pinyin import PinyinConverter

    with SQLiteManager(Path('output/destep.sqlite')) as db:
        session = db.session
        idf = IDF()
        pinyin = PinyinConverter()
        building_converter = BuildingConverter(session, idf, pinyin)
        building_converter.convert_all()
        zone_converter = ZoneConverter(session, idf, pinyin)
        zone_converter.convert_all()
        construction_converter = ConstructionConverter(session, idf, pinyin)
        construction_converter.convert_all()
        schedule_converter = ScheduleConverter(session, idf, pinyin)
        schedule_converter.convert_all()
        surface_converter = SurfaceConverter(
            session, idf, pinyin, zone_converter, construction_converter
        )
        surface_converter.convert_all()


if __name__ == '__main__':
    app()
