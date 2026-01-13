import heapq
from collections import defaultdict
from pathlib import Path
from typing import Any

from loguru import logger
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from .accdb_reader import AccdbConfig, AccdbReader
from .models import Base
from .sqlite_manager import SQLiteManager


class DataExtractor:
    """Extract data from Access database to SQLite.

    Handles table dependency ordering via topological sort and
    provides robust error handling for individual row failures.
    """

    BATCH_SIZE = 5000

    def __init__(
        self,
        accdb_path: Path,
        sqlite_path: Path,
        ucanaccess_path: Path,
    ) -> None:
        self.accdb_config = AccdbConfig(accdb_path, ucanaccess_path)
        self.sqlite_path = sqlite_path
        self._table_model_map: dict[str, type[Base]] | None = None
        self._pk_values: dict[str, set[Any]] = {}

    def extract_all(self) -> None:
        """Extract all tables from Access to SQLite."""
        with (
            AccdbReader(self.accdb_config) as reader,
            SQLiteManager(self.sqlite_path) as db,
        ):
            db.create_tables()

            accdb_tables = {t.upper() for t in reader.get_table_names()}
            sorted_tables = self._get_sorted_tables()

            self._load_pk_values(reader, accdb_tables)

            extracted_count = 0
            for table_name in sorted_tables:
                if table_name.upper() in accdb_tables:
                    self._extract_table(reader, db.session, table_name)
                    extracted_count += 1

            logger.info(
                f'Extraction complete: {extracted_count} tables processed')

    def _extract_table(
        self,
        reader: AccdbReader,
        session: Session,
        table_name: str,
    ) -> None:
        """Extract a single table from Access to SQLite using bulk insert."""
        model_class = self._get_model_class(table_name)
        if model_class is None:
            logger.warning(f"No model for table '{table_name}', skipping")
            return

        fk_info = self._get_fk_info(table_name)
        batch: list[dict[str, Any]] = []
        success_count = 0
        error_count = 0

        for row in reader.iter_table(table_name):
            try:
                decoded_row = self._decode_row(row, fk_info)
                batch.append(decoded_row)

                if len(batch) >= self.BATCH_SIZE:
                    inserted, errors = self._flush_batch(
                        session, model_class, batch)
                    success_count += inserted
                    error_count += errors
                    batch = []
            except Exception as e:
                error_count += 1
                logger.warning(f"Failed to decode row in '{table_name}': {e}")

        # 处理剩余数据
        if batch:
            inserted, errors = self._flush_batch(session, model_class, batch)
            success_count += inserted
            error_count += errors

        session.commit()

        log_msg = f"Extracted {success_count} rows from '{table_name}'"
        if error_count > 0:
            log_msg += f' ({error_count} errors)'
        logger.info(log_msg)

    def _flush_batch(
        self,
        session: Session,
        model_class: type[Base],
        batch: list[dict[str, Any]],
    ) -> tuple[int, int]:
        """Flush batch to database. Returns (success_count, error_count)."""
        try:
            mapper = inspect(model_class)
            session.bulk_insert_mappings(mapper, batch)
            session.flush()
            return len(batch), 0
        except Exception as e:
            session.rollback()
            logger.warning(
                f'Batch insert failed, falling back to row-by-row: {e}')
            return self._insert_rows_individually(session, model_class, batch)

    def _insert_rows_individually(
        self,
        session: Session,
        model_class: type[Base],
        batch: list[dict[str, Any]],
    ) -> tuple[int, int]:
        """Insert rows one by one when batch fails. Returns (success, errors)."""
        success_count = 0
        error_count = 0

        for row_data in batch:
            savepoint = session.begin_nested()
            try:
                instance = model_class(**row_data)
                session.merge(instance)
                session.flush()
                savepoint.commit()
                success_count += 1
            except Exception as e:
                savepoint.rollback()
                error_count += 1
                logger.debug(f'Row insert failed: {e}')

        return success_count, error_count

    def _load_pk_values(self, reader: AccdbReader, accdb_tables: set[str]) -> None:
        """Pre-load primary key values from all tables for FK validation."""
        for table in Base.metadata.sorted_tables:
            table_name = table.name.upper()
            if table_name not in accdb_tables:
                continue

            pk_cols = [col.name for col in table.primary_key.columns]
            if len(pk_cols) != 1:
                continue

            pk_col = pk_cols[0].upper()
            cursor = reader.connection.cursor()
            cursor.execute(f'SELECT [{pk_col}] FROM [{table_name}]')
            self._pk_values[table_name] = {row[0] for row in cursor.fetchall()}
            cursor.close()

        logger.debug(f'Loaded PK values for {len(self._pk_values)} tables')

    def _decode_row(
        self, row: dict[str, Any], fk_info: dict[str, str]
    ) -> dict[str, Any]:
        """Normalize column names, and validate FK references."""
        result = {}
        for key, value in row.items():
            col_name = key.lower()

            if col_name in fk_info and value is not None:
                parent_table = fk_info[col_name]
                valid_pks = self._pk_values.get(parent_table, set())
                if value not in valid_pks:
                    value = None

            result[col_name] = value
        return result

    def _get_fk_info(self, table_name: str) -> dict[str, str]:
        """Get FK column -> parent table mapping for a table."""
        for table in Base.metadata.sorted_tables:
            if table.name.upper() == table_name.upper():
                return {
                    fk.parent.name.lower(): fk.column.table.name.upper()
                    for fk in table.foreign_keys
                }
        return {}

    def _get_sorted_tables(self) -> list[str]:
        """Get table names sorted by foreign key dependencies (topological sort)."""
        graph: dict[str, set[str]] = defaultdict(set)
        all_tables: set[str] = set()

        for table in Base.metadata.sorted_tables:
            table_name = table.name.upper()
            all_tables.add(table_name)
            _ = graph[table_name]  # Initialize empty dependency set

            for fk in table.foreign_keys:
                parent_table = fk.column.table.name.upper()
                if parent_table != table_name:
                    graph[table_name].add(parent_table)

        in_degree: dict[str, int] = {
            table: len([d for d in deps if d in all_tables])
            for table, deps in graph.items()
        }

        queue = [t for t, deg in in_degree.items() if deg == 0]
        heapq.heapify(queue)
        result: list[str] = []

        while queue:
            current = heapq.heappop(queue)
            result.append(current)

            for table, deps in graph.items():
                if current in deps:
                    in_degree[table] -= 1
                    if in_degree[table] == 0 and table not in result:
                        heapq.heappush(queue, table)

        remaining = all_tables - set(result)
        if remaining:
            logger.warning(f'Circular dependencies detected: {remaining}')
            result.extend(sorted(remaining))

        return result

    def _get_model_class(self, table_name: str) -> type[Base] | None:
        """Get SQLAlchemy model class by table name."""
        if self._table_model_map is None:
            self._table_model_map = self._build_table_model_map()
        return self._table_model_map.get(table_name.upper())

    def _build_table_model_map(self) -> dict[str, type[Base]]:
        """Build mapping from table names to model classes."""
        mapping: dict[str, type[Base]] = {}

        for mapper in Base.registry.mappers:
            model_class = mapper.class_
            if hasattr(model_class, '__tablename__'):
                table_name = model_class.__tablename__.upper()
                mapping[table_name] = model_class

        logger.debug(f'Built table-model mapping: {len(mapping)} models')
        return mapping
