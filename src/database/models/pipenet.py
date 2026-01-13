from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Boolean, Float, Integer, Numeric, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column

from ._base import Base


class DnFk(Base):
    """Duct valve model (DN_FK)."""

    __tablename__ = 'DN_FK'

    id: Mapped[int] = mapped_column('ID', Integer, primary_key=True, comment='Valve ID')
    type: Mapped[int | None] = mapped_column('TYPE', SmallInteger, comment='Valve type')
    flow_type: Mapped[int | None] = mapped_column(
        'FLOW_TYPE', SmallInteger, comment='Flow type'
    )
    point_id: Mapped[int | None] = mapped_column(
        'POINT_ID', Integer, comment='Point ID'
    )
    room_id: Mapped[int | None] = mapped_column('ROOM_ID', Integer, comment='Room ID')
    area: Mapped[float | None] = mapped_column('AREA', Float, comment='Area')
    flow_rate: Mapped[float | None] = mapped_column(
        'FLOW_RATE', Float, comment='Flow rate'
    )
    ksai: Mapped[float | None] = mapped_column(
        'KSAI', Float, comment='Resistance coefficient'
    )


class DnJoint(Base):
    """Duct joint model (DN_JOINT)."""

    __tablename__ = 'DN_JOINT'

    id: Mapped[int] = mapped_column('ID', Integer, primary_key=True, comment='Joint ID')
    type: Mapped[int | None] = mapped_column('TYPE', SmallInteger, comment='Joint type')
    point_id: Mapped[int | None] = mapped_column(
        'POINT_ID', Integer, comment='Point ID'
    )
    angle1: Mapped[float | None] = mapped_column('ANGLE1', Float, comment='Angle 1')
    angle2: Mapped[float | None] = mapped_column('ANGLE2', Float, comment='Angle 2')


class DnPoint(Base):
    """Duct point model (DN_POINT)."""

    __tablename__ = 'DN_POINT'

    id: Mapped[int] = mapped_column('ID', Integer, primary_key=True, comment='Point ID')
    storey_id: Mapped[int | None] = mapped_column(
        'STOREY_ID', Integer, comment='Storey ID'
    )
    x: Mapped[float | None] = mapped_column('X', Float, comment='X coordinate')
    y: Mapped[float | None] = mapped_column('Y', Float, comment='Y coordinate')
    z: Mapped[float | None] = mapped_column('Z', Float, comment='Z coordinate')
    p: Mapped[float | None] = mapped_column('P', Float, comment='Pressure')
    const_pressure: Mapped[bool | None] = mapped_column(
        'CONST_PRESSURE', Boolean, comment='Constant pressure flag'
    )


class PnStart(Base):
    """Pipe network start point model (PN_START)."""

    __tablename__ = 'PN_START'

    id: Mapped[int] = mapped_column(
        'ID', Integer, primary_key=True, comment='Start point ID'
    )
    point_id: Mapped[int | None] = mapped_column(
        'POINT_ID', Integer, comment='Point ID'
    )
    pipe_style: Mapped[int | None] = mapped_column(
        'PIPE_STYLE', SmallInteger, comment='Pipe style'
    )
    first_a: Mapped[Decimal | None] = mapped_column(
        'FIRST_A', Numeric(19, 4), comment='Primary side parameter A'
    )
    first_b: Mapped[Decimal | None] = mapped_column(
        'FIRST_B', Numeric(19, 4), comment='Primary side parameter B'
    )
    first_c: Mapped[Decimal | None] = mapped_column(
        'FIRST_C', Numeric(19, 4), comment='Primary side parameter C'
    )
    first_d: Mapped[Decimal | None] = mapped_column(
        'FIRST_D', Numeric(19, 4), comment='Primary side parameter D'
    )
    first_w: Mapped[Decimal | None] = mapped_column(
        'FIRST_W', Numeric(19, 4), comment='Primary side parameter W'
    )
    second_a: Mapped[Decimal | None] = mapped_column(
        'SECOND_A', Numeric(19, 4), comment='Secondary side parameter A'
    )
    second_b: Mapped[Decimal | None] = mapped_column(
        'SECOND_B', Numeric(19, 4), comment='Secondary side parameter B'
    )
    second_c: Mapped[Decimal | None] = mapped_column(
        'SECOND_C', Numeric(19, 4), comment='Secondary side parameter C'
    )
    second_d: Mapped[Decimal | None] = mapped_column(
        'SECOND_D', Numeric(19, 4), comment='Secondary side parameter D'
    )
    second_q: Mapped[Decimal | None] = mapped_column(
        'SECOND_Q', Numeric(19, 4), comment='Secondary side parameter Q'
    )


class PnTerm(Base):
    """Pipe network terminal model (PN_TERM)."""

    __tablename__ = 'PN_TERM'

    id: Mapped[int] = mapped_column(
        'ID', Integer, primary_key=True, comment='Terminal ID'
    )
    point_id: Mapped[int | None] = mapped_column(
        'POINT_ID', Integer, comment='Point ID'
    )
    flow_type: Mapped[int | None] = mapped_column(
        'FLOW_TYPE', SmallInteger, comment='Flow type'
    )
    flow_rate: Mapped[float | None] = mapped_column(
        'FLOW_RATE', Float, comment='Flow rate'
    )


class HacnetOption(Base):
    """HACNET option model (HACNET_OPTION)."""

    __tablename__ = 'HACNET_OPTION'

    point_id: Mapped[int] = mapped_column(
        'POINT_ID', Integer, primary_key=True, comment='Point ID'
    )
    of_branch: Mapped[int | None] = mapped_column(
        'OF_BRANCH', Integer, comment='Branch ID'
    )
    of_branchline: Mapped[int | None] = mapped_column(
        'OF_BRANCHLINE', Integer, comment='Branch line ID'
    )
    x: Mapped[float | None] = mapped_column('x', Float, comment='X coordinate')
    y: Mapped[float | None] = mapped_column('y', Float, comment='Y coordinate')
