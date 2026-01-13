"""Access database and SQLAlchemy model schema consistency checker."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

from .accdb_reader import AccdbConfig, AccdbReader
from .models import Base


@dataclass
class ColumnInfo:
    """Column metadata from database."""

    name: str
    type_name: str
    type_code: int
    size: int
    nullable: bool
    ordinal: int


@dataclass
class TableMetadata:
    """Table metadata from database."""

    name: str
    columns: dict[str, ColumnInfo] = field(default_factory=dict)
    primary_keys: list[str] = field(default_factory=list)
    foreign_keys: list[dict[str, str]] = field(default_factory=list)
    row_count: int = 0


@dataclass
class TableDiff:
    """Differences found in a single table."""

    missing_columns: list[str] = field(default_factory=list)
    extra_columns: list[str] = field(default_factory=list)
    type_mismatches: list[dict[str, str]] = field(default_factory=list)
    pk_mismatch: dict[str, list[str]] | None = None
    fk_issues: list[dict[str, Any]] = field(default_factory=list)

    def has_diff(self) -> bool:
        """Check if there are any differences."""
        return bool(
            self.missing_columns
            or self.extra_columns
            or self.type_mismatches
            or self.pk_mismatch
            or self.fk_issues
        )


@dataclass
class SchemaDiff:
    """Schema comparison result."""

    missing_tables: list[str] = field(default_factory=list)
    extra_tables: list[str] = field(default_factory=list)
    table_diffs: dict[str, TableDiff] = field(default_factory=dict)
    missing_table_info: dict[str, TableMetadata] = field(default_factory=dict)


class SchemaChecker:
    """Check Access database schema against SQLAlchemy models.

    Args:
        accdb_path: Path to Access database file.
        ucanaccess_path: Path to UCanAccess driver directory.

    Example:
        >>> checker = SchemaChecker(
        ...     Path('examples/LH_Guangzhou_2015.accdb'),
        ...     Path('driver'),
        ... )
        >>> diff = checker.check()
        >>> checker.generate_report(diff, Path('output/schema_diff.md'))
    """

    # JDBC type code to SQLAlchemy type name mapping
    TYPE_MAPPING: dict[int, list[str]] = {
        4: ['Integer'],  # INTEGER
        5: ['SmallInteger', 'Integer'],  # SMALLINT
        6: ['Float'],  # FLOAT
        8: ['Float'],  # DOUBLE
        12: ['String'],  # VARCHAR
        16: ['Boolean'],  # BOOLEAN
        -1: ['String', 'Text'],  # LONGVARCHAR
        -4: ['LargeBinary'],  # LONGVARBINARY
        -5: ['Integer'],  # BIGINT
        -6: ['Integer'],  # TINYINT
        -7: ['Boolean'],  # BIT
        91: ['DateTime', 'Date'],  # DATE
        93: ['DateTime'],  # TIMESTAMP
        2: ['Numeric', 'Float'],  # NUMERIC
        3: ['Numeric', 'Float'],  # DECIMAL
        2004: ['LargeBinary'],  # BLOB
    }

    def __init__(self, accdb_path: Path, ucanaccess_path: Path) -> None:
        self.config = AccdbConfig(accdb_path, ucanaccess_path)
        self._db_metadata: dict[str, TableMetadata] = {}
        self._model_metadata: dict[str, dict[str, Any]] = {}

    def check(self) -> SchemaDiff:
        """Execute schema consistency check.

        Returns:
            SchemaDiff object containing all differences found.
        """
        logger.info('Starting schema consistency check...')

        with AccdbReader(self.config) as reader:
            self._load_db_metadata(reader)

        self._load_model_metadata()
        diff = self._compare_schemas()

        logger.info(
            f'Check completed: {len(diff.missing_tables)} missing tables, '
            f'{len(diff.table_diffs)} tables with differences'
        )
        return diff

    def _load_db_metadata(self, reader: AccdbReader) -> None:
        """Load metadata from Access database."""
        tables = reader.get_table_names()
        logger.info(f'Found {len(tables)} tables in database')

        for i, table_name in enumerate(tables, 1):
            logger.debug(f'Loading metadata for table {i}/{len(tables)}: {table_name}')

            table_meta = TableMetadata(name=table_name)

            # Load columns
            columns = reader.get_table_columns(table_name)
            for col in columns:
                col_info = ColumnInfo(
                    name=col['name'],
                    type_name=col['type_name'],
                    type_code=col['type_code'],
                    size=col['size'],
                    nullable=col['nullable'],
                    ordinal=col['ordinal'],
                )
                table_meta.columns[col['name'].upper()] = col_info

            # Load primary keys
            pk_columns = reader.get_primary_keys(table_name)
            table_meta.primary_keys = [pk.upper() for pk in pk_columns]

            # Load foreign keys
            fk_list = reader.get_foreign_keys(table_name)
            table_meta.foreign_keys = [
                {
                    'column': fk['column'].upper() if fk['column'] else '',
                    'ref_table': fk['ref_table'].upper() if fk['ref_table'] else '',
                    'ref_column': fk['ref_column'].upper() if fk['ref_column'] else '',
                }
                for fk in fk_list
            ]

            # Get row count
            table_meta.row_count = reader.get_row_count(table_name)

            self._db_metadata[table_name.upper()] = table_meta

    def _load_model_metadata(self) -> None:
        """Load metadata from SQLAlchemy models."""
        for mapper in Base.registry.mappers:
            model_class = mapper.class_
            table = model_class.__table__
            table_name = table.name.upper()

            columns = {}
            for col in table.columns:
                columns[col.name.upper()] = {
                    'name': col.name,
                    'type': type(col.type).__name__,
                    'nullable': col.nullable,
                    'primary_key': col.primary_key,
                }

            self._model_metadata[table_name] = {
                'columns': columns,
                'primary_keys': [c.name.upper() for c in table.primary_key.columns],
                'foreign_keys': [
                    {
                        'column': fk.parent.name.upper(),
                        'ref_table': fk.column.table.name.upper(),
                        'ref_column': fk.column.name.upper(),
                    }
                    for fk in table.foreign_keys
                ],
            }

        logger.info(f'Loaded {len(self._model_metadata)} model definitions')

    def _compare_schemas(self) -> SchemaDiff:
        """Compare database and model schemas."""
        diff = SchemaDiff()

        db_tables = set(self._db_metadata.keys())
        model_tables = set(self._model_metadata.keys())

        diff.missing_tables = sorted(db_tables - model_tables)
        diff.extra_tables = sorted(model_tables - db_tables)

        # Store metadata for missing tables
        for table_name in diff.missing_tables:
            diff.missing_table_info[table_name] = self._db_metadata[table_name]

        # Compare common tables
        common_tables = db_tables & model_tables
        for table_name in sorted(common_tables):
            table_diff = self._compare_table(table_name)
            if table_diff.has_diff():
                diff.table_diffs[table_name] = table_diff

        return diff

    def _compare_table(self, table_name: str) -> TableDiff:
        """Compare a single table between database and model."""
        db_table = self._db_metadata[table_name]
        model_table = self._model_metadata[table_name]

        diff = TableDiff()

        db_cols = set(db_table.columns.keys())
        model_cols = set(model_table['columns'].keys())

        diff.missing_columns = sorted(db_cols - model_cols)
        diff.extra_columns = sorted(model_cols - db_cols)

        # Type comparison
        for col_name in db_cols & model_cols:
            db_col = db_table.columns[col_name]
            model_col = model_table['columns'][col_name]
            if not self._types_compatible(db_col.type_code, model_col['type']):
                diff.type_mismatches.append(
                    {
                        'column': col_name,
                        'db_type': db_col.type_name,
                        'db_type_code': str(db_col.type_code),
                        'model_type': model_col['type'],
                    }
                )

        # Primary key comparison
        db_pk = set(db_table.primary_keys)
        model_pk = set(model_table['primary_keys'])
        if db_pk != model_pk:
            diff.pk_mismatch = {
                'db_pk': sorted(db_pk),
                'model_pk': sorted(model_pk),
            }

        # Foreign key validation
        for fk in model_table['foreign_keys']:
            ref_table = fk['ref_table']
            if ref_table not in self._db_metadata:
                diff.fk_issues.append(
                    {
                        'type': 'ref_table_not_in_db',
                        'column': fk['column'],
                        'ref_table': ref_table,
                        'ref_column': fk['ref_column'],
                    }
                )

        return diff

    def _types_compatible(self, jdbc_type: int, sqlalchemy_type: str) -> bool:
        """Check if JDBC type is compatible with SQLAlchemy type."""
        expected = self.TYPE_MAPPING.get(jdbc_type, [])
        # Also accept JsonEncodedList for BLOB types
        if jdbc_type == -4:
            expected = expected + ['JsonEncodedList']
        return sqlalchemy_type in expected

    def generate_report(self, diff: SchemaDiff, output_path: Path) -> None:
        """Generate Markdown report.

        Args:
            diff: Schema comparison result.
            output_path: Path to output markdown file.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        lines = [
            '# Access Database vs SQLAlchemy Models Schema Consistency Report',
            '',
            f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            f'Database file: {self.config.db_path.name}',
            '',
            '## Summary',
            '',
            '| Item | Count |',
            '|------|-------|',
            f'| Total tables in database | {len(self._db_metadata)} |',
            f'| Model definitions | {len(self._model_metadata)} |',
            f'| Missing models | {len(diff.missing_tables)} |',
            f'| Tables with differences | {len(diff.table_diffs)} |',
            f'| Extra models | {len(diff.extra_tables)} |',
            '',
        ]

        # Missing tables section
        if diff.missing_tables:
            lines.extend(
                [
                    '## 1. Missing Models (in database but not in models)',
                    '',
                    '| Table | Columns | Rows | Primary Key |',
                    '|-------|---------|------|-------------|',
                ]
            )
            for table_name in diff.missing_tables:
                info = diff.missing_table_info[table_name]
                pk_str = ', '.join(info.primary_keys) if info.primary_keys else '(none)'
                lines.append(
                    f'| {table_name} | {len(info.columns)} | {info.row_count} | {pk_str} |'
                )
            lines.append('')

            # Detail for missing tables
            lines.extend(
                [
                    '### Column Details for Missing Tables',
                    '',
                ]
            )
            for table_name in diff.missing_tables:
                info = diff.missing_table_info[table_name]
                lines.extend(
                    [
                        f'#### {table_name}',
                        '',
                        '| Column | Type | Size | Nullable |',
                        '|--------|------|------|----------|',
                    ]
                )
                for col_name in sorted(info.columns.keys()):
                    col = info.columns[col_name]
                    nullable = 'Yes' if col.nullable else 'No'
                    lines.append(
                        f'| {col.name} | {col.type_name} | {col.size} | {nullable} |'
                    )
                lines.append('')

        # Extra tables section
        if diff.extra_tables:
            lines.extend(
                [
                    '## 2. Extra Models (in models but not in database)',
                    '',
                ]
            )
            for table_name in diff.extra_tables:
                lines.append(f'- {table_name}')
            lines.append('')

        # Table differences section
        if diff.table_diffs:
            lines.extend(
                [
                    '## 3. Table Differences',
                    '',
                ]
            )
            for table_name, table_diff in sorted(diff.table_diffs.items()):
                lines.append(f'### {table_name}')
                lines.append('')

                if table_diff.missing_columns:
                    lines.append(
                        f'**Missing columns (in database but not in model):** {", ".join(table_diff.missing_columns)}'
                    )
                    lines.append('')

                if table_diff.extra_columns:
                    lines.append(
                        f'**Extra columns (in model but not in database):** {", ".join(table_diff.extra_columns)}'
                    )
                    lines.append('')

                if table_diff.type_mismatches:
                    lines.extend(
                        [
                            '**Type mismatches:**',
                            '',
                            '| Column | Database Type | Model Type |',
                            '|--------|---------------|------------|',
                        ]
                    )
                    for mismatch in table_diff.type_mismatches:
                        lines.append(
                            f'| {mismatch["column"]} | {mismatch["db_type"]} (code={mismatch["db_type_code"]}) | {mismatch["model_type"]} |'
                        )
                    lines.append('')

                if table_diff.pk_mismatch:
                    lines.extend(
                        [
                            '**Primary key mismatch:**',
                            f'- Database PK: {", ".join(table_diff.pk_mismatch["db_pk"]) or "(none)"}',
                            f'- Model PK: {", ".join(table_diff.pk_mismatch["model_pk"]) or "(none)"}',
                            '',
                        ]
                    )

                if table_diff.fk_issues:
                    lines.extend(
                        [
                            '**Foreign key issues:**',
                            '',
                        ]
                    )
                    for issue in table_diff.fk_issues:
                        lines.append(
                            f'- Column `{issue["column"]}` references table `{issue["ref_table"]}` which does not exist in database'
                        )
                    lines.append('')

        # Summary
        lines.extend(
            [
                '## 4. Recommended Actions',
                '',
            ]
        )

        if diff.missing_tables:
            lines.extend(
                [
                    '### Models to Add',
                    '',
                ]
            )
            for table_name in diff.missing_tables:
                info = diff.missing_table_info[table_name]
                lines.append(
                    f'- `{table_name}` ({len(info.columns)} columns, {info.row_count} rows)'
                )
            lines.append('')

        if diff.table_diffs:
            tables_with_missing = [
                name for name, d in diff.table_diffs.items() if d.missing_columns
            ]
            if tables_with_missing:
                lines.extend(
                    [
                        '### Models Needing Additional Columns',
                        '',
                    ]
                )
                for table_name in tables_with_missing:
                    missing = diff.table_diffs[table_name].missing_columns
                    lines.append(f'- `{table_name}`: {", ".join(missing)}')
                lines.append('')

        output_path.write_text('\n'.join(lines), encoding='utf-8')
        logger.info(f'Report generated: {output_path}')
