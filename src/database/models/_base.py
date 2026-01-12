import json
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import TypeDecorator


class JsonEncodedList(TypeDecorator):
    impl = Text
    cache_ok = True

    def process_bind_param(self, value: list[Any] | None, dialect: Any) -> str | None:
        if value is None:
            return value
        return json.dumps(value)

    def process_result_value(self, value: str | None, dialect: Any) -> list[Any] | None:
        if value is None:
            return value
        return json.loads(value)


class Base(DeclarativeBase):
    type_annotation_map = {
        str: String(255),
        int: Integer,
        float: Float,
        bool: Boolean,
        bytes: LargeBinary,
        Decimal: Numeric(19, 4),
        datetime: DateTime,
        list: JsonEncodedList,
    }
