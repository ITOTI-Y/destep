import heapq
from collections import defaultdict
from pathlib import Path
from typing import Any

from loguru import logger
from sqlalchemy.orm import Session

from .accdb_reader import AccdbConfig, AccdbReader
from .models import Base
from .sqlite_manager import SQLiteManager


class DataExtractor:
    """Extract data from Access database to SQLite.

    Handles table dependency ordering via topological sort and
    provides robust error handling for individual row failures.
    """

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

            # Pre-load primary key values for FK validation
            self._load_pk_values(reader, accdb_tables)

            extracted_count = 0
            for table_name in sorted_tables:
                if table_name.upper() in accdb_tables:
                    self._extract_table(reader, db.session, table_name)
                    extracted_count += 1

            logger.info(f'Extraction complete: {extracted_count} tables processed')

    def _extract_table(
        self,
        reader: AccdbReader,
        session: Session,
        table_name: str,
    ) -> None:
        """Extract a single table from Access to SQLite."""
        model_class = self._get_model_class(table_name)
        if model_class is None:
            logger.warning(f"No model for table '{table_name}', skipping")
            return

        fk_info = self._get_fk_info(table_name)
        success_count = 0
        error_count = 0

        for row in reader.iter_table(table_name):
            try:
                decoded_row = self._decode_row(row, fk_info)
                instance = model_class(**decoded_row)
                session.merge(instance)
                success_count += 1
            except Exception as e:
                error_count += 1
                session.rollback()
                logger.warning(f"Failed to insert row in '{table_name}': {e}")
                continue

        if success_count > 0:
            session.commit()
        log_msg = f"Extracted {success_count} rows from '{table_name}'"
        if error_count > 0:
            log_msg += f' ({error_count} errors)'
        logger.info(log_msg)

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
            if reader._connection is not None:
                cursor = reader._connection.cursor()
                cursor.execute(f'SELECT {pk_col} FROM {table_name}')
                self._pk_values[table_name] = {row[0] for row in cursor.fetchall()}
                cursor.close()
            else:
                logger.error(
                    f'Could not load PK values for {table_name}: No connection'
                )
                raise RuntimeError(
                    f'Could not load PK values for {table_name}: No connection'
                )

        logger.debug(f'Loaded PK values for {len(self._pk_values)} tables')

    def _decode_row(
        self, row: dict[str, Any], fk_info: dict[str, str]
    ) -> dict[str, Any]:
        """Decode BLOB fields, normalize column names, and validate FK references."""
        result = {}
        for key, value in row.items():
            col_name = key.lower()
            decoded_value = AccdbReader.decode_blob(value)

            # Validate foreign key references
            if col_name in fk_info and decoded_value is not None:
                parent_table = fk_info[col_name]
                valid_pks = self._pk_values.get(parent_table, set())
                if decoded_value not in valid_pks:
                    decoded_value = None

            result[col_name] = decoded_value
        return result

    def _get_fk_info(self, table_name: str) -> dict[str, str]:
        """Get FK column -> parent table mapping for a table."""
        for table in Base.metadata.sorted_tables:
            if table.name.upper() == table_name.upper():
                return {
                    fk.parent.name: fk.column.table.name.upper()
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
            graph[table_name]

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
