from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from src.database.models.fenestration import Door, Window, WindowTypeData
from src.database.models.geometry import Plane, Surface
from src.idf import IDF
from src.idf.models import (
    Construction,
    FenestrationSurfaceDetailed,
    WindowMaterialSimpleGlazingSystem,
)
from src.utils.pinyin import PinyinConverter

from .base import BaseConverter, UnitConverter
from .construction import EnclosureKind

if TYPE_CHECKING:
    from .manager import LookupTable


EPSILON = 1e-10


class FenestrationConverter(BaseConverter[Window | Door]):
    def __init__(
        self,
        session: Session,
        idf: IDF,
        lookup_table: LookupTable,
        pinyin: PinyinConverter | None = None,
    ) -> None:
        super().__init__(session, idf, lookup_table, pinyin)

        self._plane_to_vertices: dict[int, Plane] = {}
        self._build_plane_lookup()

        self._window_id_to_glass_data: dict[int, WindowTypeData] = {}
        self._build_glass_data_lookup()

        self._created_windows_constructions: dict[int, str] = {}

    def _build_glass_data_lookup(self) -> None:
        stmt = select(WindowTypeData)
        type_data = list(self.session.execute(stmt).scalars().all())
        for data in type_data:
            self._window_id_to_glass_data[data.id] = data

    def _build_plane_lookup(self) -> None:
        stmt = select(Plane)
        planes = list(self.session.execute(stmt).scalars().all())
        for plane in planes:
            self._plane_to_vertices[plane.plane_id] = plane

    def _get_plane_vertices(self, plane_id: int) -> np.ndarray:
        plane = self._plane_to_vertices[plane_id]
        assert plane.geometry_ref is not None
        return self._extract_vertices_from_geometry(plane.geometry_ref)

    def _get_surface_vertices(self, surface: Surface) -> np.ndarray:
        """Extract 3D vertices from a surface geometry."""
        assert surface.geometry_ref is not None
        return self._extract_vertices_from_geometry(surface.geometry_ref)

    def _extract_vertices_from_geometry(self, geometry) -> np.ndarray:
        """Extract 3D vertices from a geometry object with loop_points."""
        vertices = [
            [lp.point_ref.x, lp.point_ref.y, lp.point_ref.z]
            for lp in geometry.loop_points
            if lp.point_ref is not None
        ]
        return np.array(vertices).reshape(-1, 3)

    def _project_to_2d(self, pts: np.ndarray, normal: np.ndarray) -> np.ndarray:
        n = normal / np.linalg.norm(normal)
        u = None
        for i in range(1, len(pts)):
            candidate = pts[i] - pts[0]
            candidate = candidate - np.dot(candidate, n) * n
            if np.linalg.norm(candidate) > EPSILON:
                u = candidate / np.linalg.norm(candidate)
                break

        if u is None:
            raise ValueError(
                'Cannot build a valid local coordinate system, all points may be collinear or coincident'
            )

        v = np.cross(n, u)

        origin = pts[0]
        pts_centered = pts - origin

        return np.column_stack([pts_centered @ u, pts_centered @ v])

    def _compute_signed_area(self, points: np.ndarray, normal: np.ndarray) -> float:
        """Compute signed area of polygon projected onto the plane perpendicular to normal.

        Positive = counterclockwise when viewed from the direction of normal
        Negative = clockwise when viewed from the direction of normal
        """
        n = len(points)
        if n < 3:
            return 0.0

        pts_2d = self._project_to_2d(points, normal)

        # Shoelace formula
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += pts_2d[i, 0] * pts_2d[j, 1]
            area -= pts_2d[j, 0] * pts_2d[i, 1]

        return area / 2.0

    def _get_top_left_corner_from_normal(
        self, points: np.ndarray, normal: np.ndarray
    ) -> int:
        """Find top-left corner index for EnergyPlus vertex ordering.

        EnergyPlus requires vertices to start from the upper-left corner
        when viewed from outside the surface.
        """
        world_up = np.array([0, 0, 1])

        if abs(np.dot(normal, world_up)) > 0.99:
            if np.dot(normal, world_up) > 0:
                world_up = np.array([0, 1, 0])
            else:
                world_up = np.array([0, -1, 0])

        right = np.cross(world_up, normal)
        right_norm = np.linalg.norm(right)
        if right_norm < EPSILON:
            return 0
        right /= right_norm

        up = np.cross(normal, right)
        up /= np.linalg.norm(up)

        centroid = np.mean(points, axis=0)
        relative_points = points - centroid

        x_coords = np.dot(relative_points, right)
        y_coords = np.dot(relative_points, up)

        sort_keys = np.column_stack((-y_coords, x_coords))
        top_left_index = np.lexsort((sort_keys[:, 1], sort_keys[:, 0]))[0]

        return int(top_left_index)

    def _project_to_surface(
        self, points: np.ndarray, plane_point: np.ndarray, plane_normal: np.ndarray
    ):
        n = plane_normal / np.linalg.norm(plane_normal)
        distances = (points - plane_point) @ n
        return points - np.outer(distances, n)

    def _order_points(self, points: np.ndarray, normal: np.ndarray) -> np.ndarray:
        signed_area = self._compute_signed_area(points, normal)
        if signed_area < 0:
            points = points[::-1]

        top_left_index = self._get_top_left_corner_from_normal(points, normal)
        points = np.roll(points, -top_left_index, axis=0)
        points = UnitConverter.round_coord_array(points)
        return points

    def _create_window_construction(self, window: Window) -> str:
        construction = window.window_construction_ref
        assert construction is not None
        if construction.window_id in self._created_windows_constructions:
            return self._created_windows_constructions[construction.window_id]

        name = construction.name or construction.cname

        material_name = self.make_name('WindowMaterial', construction.window_id, name)
        assert construction.heat_resistence is not None
        u_factor = 1 / construction.heat_resistence

        glass_data = self._window_id_to_glass_data[construction.window_id]
        sc = glass_data.sc
        light_trans_ratio = glass_data.light_trans_ratio

        assert sc is not None
        material_object = WindowMaterialSimpleGlazingSystem(
            name=material_name,
            u_factor=u_factor,
            solar_heat_gain_coefficient=sc,
            visible_transmittance=light_trans_ratio,
        )
        self.idf.add(material_object)

        construction_name = self.make_name(
            'WindowConstruction', construction.window_id, name
        )
        construction_object = Construction(
            name=construction_name,
            outside_layer=material_name,
        )
        self.idf.add(construction_object)

        self._created_windows_constructions[construction.window_id] = construction_name

        return construction_name

    def _convert_window(self, window: Window) -> bool:
        assert window.main_enclosure is not None
        enclosure = window.main_enclosure
        if enclosure.kind != EnclosureKind.OUTWALL:
            self.stats.skipped += 1
            logger.warning(
                f'Skipping window {window.id} because it is not an exterior wall'
            )
            return False
        surface_name = self.lookup_table.SURFACE_TO_NAME.get(
            enclosure.side1
        ) or self.lookup_table.SURFACE_TO_NAME.get(enclosure.side2)
        assert surface_name is not None
        assert enclosure.middle_plane_ref is not None

        surface = window.surface_side1 or window.surface_side2
        assert surface is not None
        points = self._get_surface_vertices(surface)

        plane_id = enclosure.middle_plane_ref.plane_id
        plane_vertices = self._get_plane_vertices(plane_id)
        normal = self.lookup_table.PLANE_TO_NORMAL[plane_id]

        points = self._project_to_surface(points, plane_vertices, normal)
        points = self._order_points(points, normal)
        window_name = self.make_name('Window', window.id, window.name)
        construction_name = self._create_window_construction(window)
        assert window_name is not None

        try:
            assert len(points) in [3, 4]
            window_object = FenestrationSurfaceDetailed(
                name=window_name,
                surface_type='Window',
                construction_name=construction_name,
                building_surface_name=surface_name,
                vertex_1_x_coordinate=points[0][0],
                vertex_1_y_coordinate=points[0][1],
                vertex_1_z_coordinate=points[0][2],
                vertex_2_x_coordinate=points[1][0],
                vertex_2_y_coordinate=points[1][1],
                vertex_2_z_coordinate=points[1][2],
                vertex_3_x_coordinate=points[2][0],
                vertex_3_y_coordinate=points[2][1],
                vertex_3_z_coordinate=points[2][2],
                vertex_4_x_coordinate=points[3][0] if len(points) == 4 else None,
                vertex_4_y_coordinate=points[3][1] if len(points) == 4 else None,
                vertex_4_z_coordinate=points[3][2] if len(points) == 4 else None,
            )
            self.idf.add(window_object)
            self.stats.converted += 1
        except Exception as e:
            logger.error(f'Failed to add window {window_name}: {e}')
            return False
        return True

    def _convert_door(self, door: Door) -> bool:
        return False

    def convert_all(self) -> None:
        stmt_windows = select(Window).options(selectinload(Window.main_enclosure))
        windows = list(self.session.execute(stmt_windows).scalars().all())
        for window in windows:
            if self.convert_one(window):
                logger.info(f'Converted window {window.id}')
                self.stats.converted += 1
            else:
                logger.warning(f'Failed to convert window {window.id}')
                self.stats.skipped += 1

    def convert_one(self, instance: Window | Door) -> bool:
        try:
            if isinstance(instance, Window):
                return self._convert_window(instance)
            elif isinstance(instance, Door):
                return self._convert_door(instance)
        except Exception as e:
            logger.error(f'Failed to convert {instance.__class__.__name__}: {e}')
            self.stats.add_warning(
                f'Failed to convert {instance.__class__.__name__}: {e}'
            )
            return False

    def get_window_name(self, window_id: int) -> str | None:
        stmt = select(Window).where(Window.id == window_id)
        window = self.session.execute(stmt).scalars().first()
        if window is None:
            return None
        return self.make_name('Window', window.id, window.name)
