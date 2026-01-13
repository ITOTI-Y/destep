from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Boolean, Float, Integer, Numeric, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column

from ._base import Base


class DnFk(Base):
    """Duct valve model (DN_FK)."""

    __tablename__ = 'dn_fk'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Valve ID')
    type: Mapped[int | None] = mapped_column(SmallInteger, comment='Valve type')
    flow_type: Mapped[int | None] = mapped_column(SmallInteger, comment='Flow type')
    point_id: Mapped[int | None] = mapped_column(Integer, comment='Point ID')
    room_id: Mapped[int | None] = mapped_column(Integer, comment='Room ID')
    area: Mapped[float | None] = mapped_column(Float, comment='Area')
    flow_rate: Mapped[float | None] = mapped_column(Float, comment='Flow rate')
    ksai: Mapped[float | None] = mapped_column(Float, comment='Resistance coefficient')


class DnJoint(Base):
    """Duct joint model (DN_JOINT)."""

    __tablename__ = 'dn_joint'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Joint ID')
    type: Mapped[int | None] = mapped_column(SmallInteger, comment='Joint type')
    point_id: Mapped[int | None] = mapped_column(Integer, comment='Point ID')
    angle1: Mapped[float | None] = mapped_column(Float, comment='Angle 1')
    angle2: Mapped[float | None] = mapped_column(Float, comment='Angle 2')


class DnPoint(Base):
    """Duct point model (DN_POINT)."""

    __tablename__ = 'dn_point'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Point ID')
    storey_id: Mapped[int | None] = mapped_column(Integer, comment='Storey ID')
    x: Mapped[float | None] = mapped_column(Float, comment='X coordinate')
    y: Mapped[float | None] = mapped_column(Float, comment='Y coordinate')
    z: Mapped[float | None] = mapped_column(Float, comment='Z coordinate')
    p: Mapped[float | None] = mapped_column(Float, comment='Pressure')
    const_pressure: Mapped[bool | None] = mapped_column(
        Boolean, comment='Constant pressure flag'
    )


class PnStart(Base):
    """Pipe network start point model (PN_START)."""

    __tablename__ = 'pn_start'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Start point ID')
    point_id: Mapped[int | None] = mapped_column(Integer, comment='Point ID')
    pipe_style: Mapped[int | None] = mapped_column(SmallInteger, comment='Pipe style')
    first_a: Mapped[Decimal | None] = mapped_column(
        Numeric(19, 4), comment='Primary side parameter A'
    )
    first_b: Mapped[Decimal | None] = mapped_column(
        Numeric(19, 4), comment='Primary side parameter B'
    )
    first_c: Mapped[Decimal | None] = mapped_column(
        Numeric(19, 4), comment='Primary side parameter C'
    )
    first_d: Mapped[Decimal | None] = mapped_column(
        Numeric(19, 4), comment='Primary side parameter D'
    )
    first_w: Mapped[Decimal | None] = mapped_column(
        Numeric(19, 4), comment='Primary side parameter W'
    )
    second_a: Mapped[Decimal | None] = mapped_column(
        Numeric(19, 4), comment='Secondary side parameter A'
    )
    second_b: Mapped[Decimal | None] = mapped_column(
        Numeric(19, 4), comment='Secondary side parameter B'
    )
    second_c: Mapped[Decimal | None] = mapped_column(
        Numeric(19, 4), comment='Secondary side parameter C'
    )
    second_d: Mapped[Decimal | None] = mapped_column(
        Numeric(19, 4), comment='Secondary side parameter D'
    )
    second_q: Mapped[Decimal | None] = mapped_column(
        Numeric(19, 4), comment='Secondary side parameter Q'
    )


class PnTerm(Base):
    """Pipe network terminal model (PN_TERM)."""

    __tablename__ = 'pn_term'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Terminal ID')
    point_id: Mapped[int | None] = mapped_column(Integer, comment='Point ID')
    flow_type: Mapped[int | None] = mapped_column(SmallInteger, comment='Flow type')
    flow_rate: Mapped[float | None] = mapped_column(Float, comment='Flow rate')


class HacnetOption(Base):
    """HACNET option model (HACNET_OPTION)."""

    __tablename__ = 'hacnet_option'

    point_id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Point ID')
    of_branch: Mapped[int | None] = mapped_column(Integer, comment='Branch ID')
    of_branchline: Mapped[int | None] = mapped_column(Integer, comment='Branch line ID')
    x: Mapped[float | None] = mapped_column(Float, comment='X coordinate')
    y: Mapped[float | None] = mapped_column(Float, comment='Y coordinate')
