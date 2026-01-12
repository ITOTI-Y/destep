from pathlib import Path
from types import TracebackType

from loguru import logger
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from .models._base import Base


@event.listens_for(Engine, 'connect')
def _set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable foreign key support for SQLite."""
    cursor = dbapi_connection.cursor()
    cursor.execute('PRAGMA foreign_keys=ON')
    cursor.close()


class SQLiteManager:
    """SQLite database manager with context manager support.

    Args:
        db_path: Path to SQLite database file.

    Example:
        >>> with SQLiteManager(Path('data.sqlite')) as db:
        ...     session = db.session
        ...     # perform queries
    """

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._engine: Engine | None = None
        self._session_factory: sessionmaker[Session] | None = None
        self._session: Session | None = None

    def __enter__(self) -> 'SQLiteManager':
        self._connect()
        self.create_tables()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self._close()

    @property
    def session(self) -> Session:
        if self._session is None:
            if self._session_factory is None:
                raise RuntimeError('Database not connected')
            self._session = self._session_factory()
        return self._session

    def create_tables(self) -> None:
        if self._engine is None:
            raise RuntimeError('Database not connected')
        Base.metadata.create_all(self._engine)
        logger.info(f'Created tables in {self.db_path}')

    def _connect(self) -> None:
        self._engine = create_engine(f'sqlite:///{self.db_path}')
        self._session_factory = sessionmaker(bind=self._engine)
        logger.info(f'Connected to {self.db_path}')

    def _close(self) -> None:
        """Close session and engine."""
        if self._session is not None:
            try:
                self._session.commit()
            except Exception:
                self._session.rollback()
                raise
            finally:
                self._session.close()
                self._session = None

        if self._engine is not None:
            self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info(f'Disconnected from {self.db_path}')
