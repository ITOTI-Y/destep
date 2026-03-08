"""Batch visualize all database models in the database/ directory."""

from __future__ import annotations

from pathlib import Path

from loguru import logger

from src.converters.manager import ConverterManager
from src.database import DataExtractor, SQLiteManager
from src.visualization import idf_render

DATABASE_DIR = Path('database')
OUTPUT_DIR = Path('output/visualization')


def process_one(accdb_path: Path) -> None:
    name = accdb_path.stem
    sqlite_path = OUTPUT_DIR / f'{name}.sqlite'
    idf_path = OUTPUT_DIR / f'{name}.idf'
    png_path = OUTPUT_DIR / f'{name}.png'

    if png_path.exists():
        logger.info(f'SKIP: {name} (already done)')
        return

    # Step 1: Extract accdb → sqlite
    if not sqlite_path.exists():
        logger.info(f'Extracting {name}...')
        extractor = DataExtractor(
            accdb_path=accdb_path,
            sqlite_path=sqlite_path,
            ucanaccess_path=Path('driver'),
        )
        extractor.extract_all()

    # Step 2: Convert sqlite → idf (with sizing error tolerance)
    logger.info(f'Converting {name}...')
    with SQLiteManager(sqlite_path) as db:
        manager = ConverterManager(db.session)

        for converter_type, converter_class in manager.CONVERTER_ORDER.items():
            try:
                logger.info(f'  Converting {converter_type}...')
                converter = converter_class(
                    session=manager.session,
                    idf=manager.idf,
                    lookup_table=manager.lookup_table,
                    pinyin=manager.pinyin,
                )
                converter.convert_all()
            except Exception as e:
                logger.warning(f'  {converter_type} failed: {e}')

        idf = manager.idf
        idf.save(idf_path)

    # Step 3: Render idf → png
    try:
        idf_render(idf, png_path)
        logger.info(f'OK: {name} → {png_path}')
    except Exception as e:
        logger.error(f'FAIL: {name} render error: {e}')


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    accdb_files = sorted(DATABASE_DIR.glob('*.accdb'))
    logger.info(f'Found {len(accdb_files)} database files')

    for accdb_path in accdb_files:
        try:
            process_one(accdb_path)
        except Exception as e:
            logger.error(f'FAIL: {accdb_path.stem}: {e}')


if __name__ == '__main__':
    main()
