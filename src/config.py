import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class PathConfig:
    """Project path configuration.

    Paths can be set via environment variables with DESTEP_ prefix:
        - DESTEP_PROJECT_ROOT
        - DESTEP_SCHEMA_PATH
        - DESTEP_UCANACCESS_PATH
        - DESTEP_OUTPUT_DIR
        - DESTEP_LOG_DIR
        - DESTEP_DATABASE_DIR
    """

    project_root: Path = field(default_factory=lambda: Path.cwd())
    schema_path: Path | None = None
    ucanaccess_path: Path = field(default_factory=lambda: Path.cwd() / 'driver')
    output_dir: Path = field(default_factory=lambda: Path.cwd() / 'output')
    log_dir: Path = field(default_factory=lambda: Path.cwd() / 'log')
    database_dir: Path = field(default_factory=lambda: Path.cwd() / 'database')
    output_database_dir: Path = field(
        default_factory=lambda: Path.cwd() / 'output' / 'database'
    )
    ddy_dir: Path = field(default_factory=lambda: Path.cwd() / 'output' / 'ddy')
    weather_dir: Path = field(default_factory=lambda: Path.cwd() / 'output' / 'weather')
    idf_dir: Path = field(default_factory=lambda: Path.cwd() / 'output' / 'idf')

    def __post_init__(self):
        if env_root := self._get_env_path('DESTEP_PROJECT_ROOT'):
            self.project_root = Path(env_root)
        if env_schema := self._get_env_path('DESTEP_SCHEMA_PATH'):
            self.schema_path = Path(env_schema)
        if env_ucanaccess := self._get_env_path('DESTEP_UCANACCESS_PATH'):
            self.ucanaccess_path = Path(env_ucanaccess)
        if env_output := self._get_env_path('DESTEP_OUTPUT_DIR'):
            self.output_dir = Path(env_output)
        if env_log := self._get_env_path('DESTEP_LOG_DIR'):
            self.log_dir = Path(env_log)
        if env_db := self._get_env_path('DESTEP_DATABASE_DIR'):
            self.database_dir = Path(env_db)
        if env_ddy := self._get_env_path('DESTEP_DDY_DIR'):
            self.ddy_dir = Path(env_ddy)
        if env_weather := self._get_env_path('DESTEP_WEATHER_DIR'):
            self.weather_dir = Path(env_weather)
        if env_idf := self._get_env_path('DESTEP_IDF_DIR'):
            self.idf_dir = Path(env_idf)

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.database_dir.mkdir(parents=True, exist_ok=True)
        self.ddy_dir.mkdir(parents=True, exist_ok=True)
        self.weather_dir.mkdir(parents=True, exist_ok=True)
        self.idf_dir.mkdir(parents=True, exist_ok=True)
        self.project_root = self.project_root.resolve()
        self.output_dir = self.output_dir.resolve()
        self.log_dir = self.log_dir.resolve()
        self.database_dir = self.database_dir.resolve()
        self.ddy_dir = self.ddy_dir.resolve()
        self.weather_dir = self.weather_dir.resolve()
        self.schema_path = self.schema_path.resolve() if self.schema_path else None
        self.ucanaccess_path = (
            self.ucanaccess_path.resolve() if self.ucanaccess_path else None
        )
        self.idf_dir = self.idf_dir.resolve()

    def _get_env_path(self, env_var: str) -> Path | None:
        if value := os.environ.get(env_var):
            return Path(value)
        return None
