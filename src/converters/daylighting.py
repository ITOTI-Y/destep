"""Daylighting converter for DeST to EnergyPlus IDF conversion.

Adds Daylighting:Controls to every zone that has lighting, an exterior window
and a DeST room-type illuminance setpoint (RoomTypeData.set_min_luminance), so
that the zone lights dim with the daylight admitted by the window visible
transmittance.

One reference point per zone sits in front of the largest exterior window, at
mid-depth of the zone floor along the window's inward normal and at work-plane
height. It controls all zone lighting with continuous dimming.
"""

from __future__ import annotations

from typing import Final

import numpy as np
from idfpy.models import (
    BuildingSurfaceDetailed,
    DaylightingControls,
    DaylightingControlsControlDataItem,
    DaylightingReferencePoint,
    FenestrationSurfaceDetailed,
    Lights,
    Zone,
)
from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.converters.base import BaseConverter
from src.database.models.building import Room

WORK_PLANE_HEIGHT_M: Final[float] = 0.8
DEPTH_FRACTIONS: Final[tuple[float, ...]] = (0.5, 0.25, 0.1)
SKYLIGHT_HORIZONTAL_NORMAL: Final[float] = 0.1
DAYLIT_FENESTRATION_TYPES: Final[tuple[str, ...]] = ('Window', 'GlassDoor')


def _inside(point: np.ndarray, polygon: np.ndarray) -> bool:
    x, y = point
    xs, ys = polygon[:, 0], polygon[:, 1]
    xs_next, ys_next = np.roll(xs, -1), np.roll(ys, -1)
    crosses = (ys > y) != (ys_next > y)
    with np.errstate(divide='ignore', invalid='ignore'):
        x_cross = xs + (y - ys) * (xs_next - xs) / (ys_next - ys)
    return bool(np.count_nonzero(crosses & (x < x_cross)) % 2)


def reference_point(
    window: FenestrationSurfaceDetailed,
    floors: list[BuildingSurfaceDetailed],
) -> np.ndarray | None:
    """World coordinates of the reference point, or None if none fits the floor.

    The point starts at mid-depth of the floor in front of the window and moves
    towards the window until it lies on the floor, which keeps it inside
    L-shaped and other non-convex zones.
    """
    polygons = [np.asarray(floor.vertices_as_tuples) for floor in floors]
    floor_xy = np.vstack([polygon[:, :2] for polygon in polygons])
    z = min(float(polygon[:, 2].min()) for polygon in polygons) + WORK_PLANE_HEIGHT_M

    centroid = np.asarray(window.centroid)[:2]
    outward = np.asarray(window.normal)[:2]
    if np.linalg.norm(outward) < SKYLIGHT_HORIZONTAL_NORMAL:
        candidates = [centroid]
    else:
        inward = -outward / np.linalg.norm(outward)
        depth = float(((floor_xy - centroid) @ inward).max())
        candidates = [centroid + inward * depth * f for f in DEPTH_FRACTIONS]

    for candidate in candidates:
        if any(_inside(candidate, polygon[:, :2]) for polygon in polygons):
            return np.array([*candidate, z])
    return None


class DaylightingConverter(BaseConverter[Room]):
    """Converter for DeST room-type illuminance setpoints to EnergyPlus daylighting."""

    def convert_all(self) -> None:
        stmt = select(Room).options(selectinload(Room.room_type))
        rooms = list(self.session.execute(stmt).scalars().all())
        self.stats.total = len(rooms)

        for room in rooms:
            if self.convert_one(room):
                self.stats.converted += 1
            else:
                self.stats.skipped += 1

        self.log_stats()

    def convert_one(self, instance: Room) -> bool:
        room = instance
        zone_name = self.lookup_table.ROOM_TO_ZONE.get(room.id)
        if zone_name is None or room.room_type is None:
            return False
        setpoint = room.room_type.set_min_luminance
        if setpoint is None or setpoint <= 0:
            return False

        zone = self.idf.get(Zone, zone_name)
        if zone is None or not zone.referencing(Lights):
            return False

        surfaces = zone.referencing(BuildingSurfaceDetailed)
        windows = [
            window
            for surface in surfaces
            if surface.outside_boundary_condition == 'Outdoors'
            for window in surface.referencing(FenestrationSurfaceDetailed)
            if window.surface_type in DAYLIT_FENESTRATION_TYPES
        ]
        if not windows:
            return False
        floors = [surface for surface in surfaces if surface.surface_type == 'Floor']
        if not floors:
            raise ValueError(f'Zone {zone_name} has exterior windows but no floor')

        point = reference_point(max(windows, key=lambda w: w.area), floors)
        if point is None:
            message = f'No daylighting reference point fits the floor of {zone_name}'
            logger.warning(message)
            self.stats.add_warning(message)
            return False

        x, y, z = point
        point_name = self.make_name('DaylightingPoint', room.id, room.name)
        self.idf.add(
            DaylightingReferencePoint(
                name=point_name,
                zone_or_space_name=zone_name,
                x_coordinate_of_reference_point=round(float(x), 3),
                y_coordinate_of_reference_point=round(float(y), 3),
                z_coordinate_of_reference_point=round(float(z), 3),
            )
        )
        self.idf.add(
            DaylightingControls(
                name=self.make_name('Daylighting', room.id, room.name),
                zone_or_space_name=zone_name,
                daylighting_method='SplitFlux',
                lighting_control_type='Continuous',
                minimum_input_power_fraction_for_continuous_or_continuousoff_dimming_control=0.3,
                minimum_light_output_fraction_for_continuous_or_continuousoff_dimming_control=0.2,
                control_data=[
                    DaylightingControlsControlDataItem(
                        daylighting_reference_point_name=point_name,
                        fraction_of_lights_controlled_by_reference_point=1.0,
                        illuminance_setpoint_at_reference_point=setpoint,
                    )
                ],
            )
        )
        logger.debug(
            f'Added daylighting to {zone_name} ({room.room_type.name}, {setpoint:g} lx)'
        )
        return True
