import struct
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jaydebeapi
import jpype
from loguru import logger


@dataclass(frozen=True)
class AccdbConfig:
    """Access database configuration."""

    db_path: Path
    ucanaccess_path: Path

    def __post_init__(self) -> None:
        if not self.db_path.exists():
            raise FileNotFoundError(f'Database file not found: {self.db_path}')
        if not self.ucanaccess_path.is_dir():
            raise NotADirectoryError(
                f'UCanAccess directory not found: {self.ucanaccess_path}'
            )


class AccdbReader:
    """Access database reader with context manager support.

    Args:
        config: Database configuration containing paths.

    Example:
        >>> config = AccdbConfig(Path('data.accdb'), Path('driver/ucanaccess'))
        >>> with AccdbReader(config) as reader:
        ...     rows = reader.query('SELECT * FROM Building')
        ...     for row in reader.iter_table('Room', batch_size=500):
        ...         process(row)
    """

    def __init__(self, config: AccdbConfig) -> None:
        self.config = config
        self._connection: jaydebeapi.Connection | None = None
        self._classpath = self._build_classpath()

    def __enter__(self) -> 'AccdbReader':
        self.connect()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        self.close()

    def connect(self) -> None:
        if self._connection is not None:
            return

        jdbc_url = f'jdbc:ucanaccess://{self.config.db_path}'
        self._connection = jaydebeapi.connect(
            jclassname='net.ucanaccess.jdbc.UcanaccessDriver',
            url=jdbc_url,
            driver_args=['', ''],
            jars=self._classpath,
        )
        logger.info(f'Connected to {self.config.db_path}')

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None
            logger.info('Database connection closed')

    def get_table_names(self) -> list[str]:
        """Get all user table names from database."""
        if self._connection is None:
            raise RuntimeError('Not connected to database')

        metadata = self._connection.jconn.getMetaData()
        result_set = metadata.getTables(None, None, '%', ['TABLE'])

        tables = []
        while result_set.next():
            table_name = result_set.getString('TABLE_NAME')
            if not table_name.startswith('~') and not table_name.startswith('MSys'):
                tables.append(table_name)
        return sorted(tables)

    def query(self, sql: str) -> list[dict[str, Any]]:
        """Execute SQL query and return results as list of dicts.

        Args:
            sql: SQL query string.

        Returns:
            List of row dictionaries with decoded BLOB fields.
        """
        if self._connection is None:
            raise RuntimeError('Not connected to database')

        cursor = self._connection.cursor()
        try:
            cursor.execute(sql)
            columns = [desc[0] for desc in cursor.description]
            rows = []
            for row in cursor.fetchall():
                row_dict = {}
                for col, val in zip(columns, row, strict=True):
                    row_dict[col] = self.decode_blob(val)
                rows.append(row_dict)
            return rows
        finally:
            cursor.close()

    def iter_table(
        self, table_name: str, batch_size: int = 1000
    ) -> Iterator[dict[str, Any]]:
        """Iterate over table rows in batches.

        Args:
            table_name: Name of table to read.
            batch_size: Number of rows to fetch per batch.

        Yields:
            Row dictionaries with decoded BLOB fields.
        """

        if self._connection is None:
            raise RuntimeError('Not connected to database')

        cursor = self._connection.cursor()
        try:
            cursor.execute(f'SELECT * FROM [{table_name}]')
            columns = [desc[0] for desc in cursor.description]

            while True:
                rows = cursor.fetchmany(batch_size)
                if not rows:
                    break
                for row in rows:
                    row_dict = {}
                    for col, val in zip(columns, row, strict=True):
                        row_dict[col] = self.decode_blob(val)
                    yield row_dict
        finally:
            cursor.close()

    def _build_classpath(self) -> list[str]:
        uca_dir = self.config.ucanaccess_path

        main_jars = list(uca_dir.glob('ucanaccess-*.jar'))
        if not main_jars:
            raise FileNotFoundError(f'UCanAccess JAR not found in: {uca_dir}')
        main_jar = main_jars[0]

        lib_dir = uca_dir / 'lib'
        if not lib_dir.is_dir():
            raise FileNotFoundError(f"UCanAccess 'lib' directory not found: {lib_dir}")

        dep_jars = list(lib_dir.glob('*.jar'))
        return [str(main_jar)] + [str(jar) for jar in dep_jars]

    @staticmethod
    def decode_blob(raw_value: Any) -> Any:
        """Decode BLOB field to float64 array or scalar.

        DeST stores numeric arrays as little-endian double (float64) binary data.
        This method handles both raw bytes and Java Blob objects.

        Args:
            raw_value: Raw value from database (bytes, Blob, or other).

        Returns:
            Decoded value: single float if 1 element, list[float] if multiple, or original value if not a valid BLOB.
        """
        raw_bytes: bytes | None = None

        if isinstance(raw_value, jpype.JClass('java.sql.Blob')):
            try:
                blob_length = int(raw_value.length())
                if blob_length > 0:
                    raw_bytes = bytes(raw_value.getBytes(1, blob_length))
                else:
                    return None
            except Exception as e:
                logger.warning(f'Failed to extract bytes from Blob: {e}')
                return None

        elif isinstance(raw_value, (bytes, bytearray)):
            raw_bytes = bytes(raw_value)

        else:
            return raw_value

        if raw_bytes is None or len(raw_bytes) == 0:
            return None
        if len(raw_bytes) % 8 != 0:
            return raw_bytes

        count = len(raw_bytes) // 8
        try:
            values = list(struct.unpack(f'<{count}d', raw_bytes))
        except struct.error:
            return raw_bytes

        values = [round(v, 1) for v in values]

        return values
