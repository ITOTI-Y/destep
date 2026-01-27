from dataclasses import dataclass, field

import numpy as np
from loguru import logger
from sqlalchemy.orm import Session

from src.idf import IDF
from src.idf.models import (
    OutputDiagnostics,
    OutputDiagnosticsDiagnosticsItem,
    OutputTableSummaryReports,
    OutputTableSummaryReportsReportsItem,
    RunPeriod,
    SimulationControl,
    Timestep,
    Version,
)
from src.utils.pinyin import PinyinConverter

from .base import BaseConverter
from .building import BuildingConverter
from .construction import ConstructionConverter
from .fenestration import FenestrationConverter
from .internal_gains import InternalGainsConverter
from .schedule import ScheduleConverter
from .surface import SurfaceConverter
from .zone import ZoneConverter


@dataclass
class LookupTable:
    # ROOM_TO_ZONE: Room ID -> Zone Name
    ROOM_TO_ZONE: dict[int, str] = field(default_factory=dict)

    # CONSTRUCTION_TO_NAME: Enclosure Kind, Enclosure Construction ID -> Construction Name
    CONSTRUCTION_TO_NAME: dict[tuple[int, int], str] = field(default_factory=dict)

    # SCHEDULE_TO_NAME: Schedule ID -> Schedule Name
    SCHEDULE_TO_NAME: dict[int, str] = field(default_factory=dict)

    # REQUIRED_SCHEDULE_IDS: Set of required schedule IDs
    REQUIRED_SCHEDULE_IDS: set[int] = field(default_factory=set)

    # SURFACE_TO_NAME: Surface ID -> Surface Name
    SURFACE_TO_NAME: dict[int, str] = field(default_factory=dict)

    # PLANE_TO_NORMAL: Plane ID -> Normal
    PLANE_TO_NORMAL: dict[int, np.ndarray] = field(default_factory=dict)


class ConverterManager:
    CONVERTER_ORDER: dict[str, type[BaseConverter]] = {
        'building': BuildingConverter,
        'construction': ConstructionConverter,
        'zone': ZoneConverter,
        'surface': SurfaceConverter,
        'fenestration': FenestrationConverter,
        'internal_gains': InternalGainsConverter,
        'schedule': ScheduleConverter,
    }

    def __init__(self, session: Session) -> None:
        self.session = session
        self.idf = IDF()
        self.pinyin = PinyinConverter()
        self.lookup_table = LookupTable()
        self._idf_init()

    def _idf_init(self) -> None:
        self.idf.add(Version())
        self.idf.add(SimulationControl())
        self.idf.add(Timestep())

        run_period = RunPeriod(
            name='Annual Run Period',
            begin_month=1,
            begin_day_of_month=1,
            end_month=12,
            end_day_of_month=31,
        )
        self.idf.add(run_period)

        output_table_summary = OutputTableSummaryReports(
            reports=[OutputTableSummaryReportsReportsItem(report_name='AllSummary')]
        )
        self.idf.add(output_table_summary)

        output_diagnostics = OutputDiagnostics(
            diagnostics=[OutputDiagnosticsDiagnosticsItem(key='DisplayExtraWarnings')]
        )
        self.idf.add(output_diagnostics)

    def convert(self) -> IDF:
        for converter_type, converter_class in self.CONVERTER_ORDER.items():
            logger.info(f'Converting {converter_type}...')
            converter = converter_class(
                session=self.session,
                idf=self.idf,
                lookup_table=self.lookup_table,
                pinyin=self.pinyin,
            )
            converter.convert_all()

        return self.idf
