from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Literal

import mapbox_earcut as earcut
import numpy as np
import trimesh
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from src.converters.base import BaseConverter
from src.converters.construction import ConstructionConverter, EnclosureKind
from src.converters.zone import ZoneConverter
from src.database.models import MainEnclosure
from src.database.models.building import Room
from src.database.models.fenestration import Door, Window
from src.database.models.geometry import Surface
from src.idf import IDF
from src.idf.models.thermal_zones import (
    BuildingSurfaceDetailed,
    BuildingSurfaceDetailedVerticesItem,
)
from src.utils.pinyin import PinyinConverter


@dataclass
class SurfaceType:
    INTERIOR_WALL = 0
    EXTERIOR_WALL = 1
    GROUND_FLOOR = 2
    AIR_FLOOR = 3
    MIDDLE_FLOOR = 4
    CEILING = 5


class SurfaceConverter(BaseConverter[Room]):
    def __init__(
        self,
        session: Session,
        idf: IDF,
        pinyin: PinyinConverter | None = None,
        zone_converter: ZoneConverter | None = None,
        construction_converter: ConstructionConverter | None = None,
    ) -> None:
        super().__init__(session, idf, pinyin)
        self.zone_converter = zone_converter or ZoneConverter(session, idf, pinyin)
        self.construction_converter = construction_converter or ConstructionConverter(
            session, idf, pinyin
        )

        self._surface_to_enclosure: dict[int, tuple[MainEnclosure, bool]] = {}
        self._build_enclosure_lookup()

        self._surface_to_fenestration: dict[int, Window | Door] = {}
        self._build_fenestration_lookup()

        self._created_surfaces: dict[int, BuildingSurfaceDetailed] = {}

    def _build_enclosure_lookup(self) -> None:
        """Build lookup table from Surface ID to MainEnclosure."""
        stmt = select(MainEnclosure)
        enclosures = list(self.session.execute(stmt).scalars().all())

        for enc in enclosures:
            if enc.side1 is not None:
                self._surface_to_enclosure[enc.side1] = (enc, True)
            if enc.side2 is not None:
                self._surface_to_enclosure[enc.side2] = (enc, False)

    def _build_fenestration_lookup(self) -> None:
        """Build lookup table from Surface ID to Window or Door."""
        stmt_windows = select(Window)
        stmt_doors = select(Door)
        windows = list(self.session.execute(stmt_windows).scalars().all())
        doors = list(self.session.execute(stmt_doors).scalars().all())
        for window in windows:
            if window.side1 is not None:
                self._surface_to_fenestration[window.side1] = window
            if window.side2 is not None:
                self._surface_to_fenestration[window.side2] = window
        for door in doors:
            if door.side1 is not None:
                self._surface_to_fenestration[door.side1] = door
            if door.side2 is not None:
                self._surface_to_fenestration[door.side2] = door

    def convert_all(self) -> None:
        stmt = select(Room).options(selectinload(Room.surfaces))
        rooms = self.session.execute(stmt).scalars().all()
        for room in rooms:
            if self.convert_one(room):
                self.stats.converted += 1

    def convert_one(self, instance: Room) -> bool:
        room = instance
        surfaces = [
            s
            for s in room.surfaces
            if s.surface_id not in self._surface_to_fenestration
        ]
        surface_by_types = defaultdict(list)
        interior_points = self._calculate_interior_points(
            [s for s in surfaces if s.type in [SurfaceType.MIDDLE_FLOOR]]
        )
        normals = self._get_outside_normals(surfaces, interior_points)

        _surfaces_ordered_vertices: list[
            tuple[BuildingSurfaceDetailed, np.ndarray, np.ndarray]
        ] = []
        for surface, normal in zip(surfaces, normals, strict=True):
            try:
                surface_by_types[surface.type].append(surface)
                ordered_points = self._order_points(surface, normal)
                boundary_condition, _ = self._determine_boundary_condition(surface)

                surface_name = self.make_name(
                    'Surface', surface.surface_id, surface.name
                )
                surface_type = self._determine_surface_type(surface)
                construction_name = self._get_construction_name(surface)
                zone_name = self._get_zone_name(surface.of_room)
                sun_exposure = self._get_sun_exposure(boundary_condition)
                wind_exposure = self._get_wind_exposure(boundary_condition)

                idf_surface = BuildingSurfaceDetailed(
                    name=surface_name,
                    surface_type=surface_type,
                    construction_name=construction_name,
                    zone_name=zone_name,
                    outside_boundary_condition=boundary_condition,
                    outside_boundary_condition_object=None,
                    sun_exposure=sun_exposure,
                    wind_exposure=wind_exposure,
                    vertices=[
                        BuildingSurfaceDetailedVerticesItem(
                            vertex_x_coordinate=v[0],
                            vertex_y_coordinate=v[1],
                            vertex_z_coordinate=v[2],
                        )
                        for v in ordered_points
                    ],
                )
                _surfaces_ordered_vertices.append((idf_surface, ordered_points, normal))
                self.idf.add(idf_surface)
                self._created_surfaces[surface.surface_id] = idf_surface

            except Exception as e:
                self.stats.add_warning(
                    f'Failed to convert surface {surface.surface_id}: {e}'
                )
                self.stats.skipped += 1
                continue

        if not self._validate_zone_geometry_closure(_surfaces_ordered_vertices):
            self.stats.skipped += 1
            return False
        return True

    def _calculate_interior_points(self, surfaces: list[Surface]) -> np.ndarray:
        interior_points = []
        for surface in surfaces:
            vertices = self._get_surface_vertices(surface)
        avg_z = np.mean(vertices[:, 2])
        face_indices = self._triangulate_polygon(vertices, np.array([0, 0, 1]))
        for face_index in face_indices:
            triangle_vertices = vertices[face_index]
            centroid = triangle_vertices.mean(axis=0)
            interior_points.append([centroid[0], centroid[1], avg_z])
        return np.array(interior_points)

    def _triangulate_polygon(self, pts: np.ndarray, normal: np.ndarray) -> np.ndarray:
        pts_2d = self._project_to_2d(pts, normal)
        pts_2d = pts_2d.astype(np.float64)
        rings = np.array([len(pts_2d)], dtype=np.uint32)
        result = earcut.triangulate_float64(pts_2d, rings)
        faces = np.array(result).reshape(-1, 3)
        return faces

    def _project_to_2d(self, pts: np.ndarray, normal: np.ndarray) -> np.ndarray:
        n = normal / np.linalg.norm(normal)
        u = pts[1] - pts[0]
        u = u - np.dot(u, n) * n
        u = u / np.linalg.norm(u)

        v = np.cross(n, u)

        origin = pts[0]
        pts_centered = pts - origin

        return np.column_stack([pts_centered @ u, pts_centered @ v])

    def _get_surface_vertices(self, surface: Surface) -> np.ndarray:
        vertices: list = []
        for lp in surface.geometry_ref.loop_points:  # type: ignore
            vertices.append([lp.point_ref.x, lp.point_ref.y, lp.point_ref.z])  # type: ignore
        return np.array(vertices)

    def _get_outside_normals(
        self, surfaces: list[Surface], interior_points: np.ndarray
    ) -> np.ndarray:
        normals: np.ndarray = np.zeros((len(surfaces), 3))
        for i, surface in enumerate(surfaces):
            if surface.type == SurfaceType.CEILING:
                normals[i] = [0, 0, -1]
            elif surface.type in [
                SurfaceType.GROUND_FLOOR,
                SurfaceType.AIR_FLOOR,
                SurfaceType.MIDDLE_FLOOR,
            ]:
                normals[i] = [0, 0, 1]
            else:
                vertices = self._get_surface_vertices(surface)
                centroid = vertices.mean(axis=0)
                interior_vector = (
                    interior_points[
                        np.argmin(np.linalg.norm(interior_points - centroid, axis=1))
                    ]
                    - centroid
                )
                v1, v2 = vertices[1] - vertices[0], vertices[2] - vertices[0]
                normal_vector = np.cross(v1, v2)
                if np.dot(normal_vector, interior_vector) > 0:
                    normal_vector = -normal_vector
                normals[i] = normal_vector / np.linalg.norm(normal_vector)
        return normals

    def _order_points(self, surface: Surface, normal: np.ndarray) -> np.ndarray:
        from functools import cmp_to_key

        def compare_points(idx1, idx2):
            v1 = points[idx1] - centroid
            v2 = points[idx2] - centroid

            cross = np.cross(v1, v2)

            sign = np.dot(cross, normal)

            if sign > 1e-10:
                return -1
            elif sign < -1e-10:
                return 1
            else:
                d1 = np.linalg.norm(v1)
                d2 = np.linalg.norm(v2)
                return -1 if d1 < d2 else 1

        points = self._get_surface_vertices(surface)
        centroid = points.mean(axis=0)

        sorted_indices = sorted(range(len(points)), key=cmp_to_key(compare_points))
        points = points[sorted_indices]
        top_left_index = self._get_top_left_corner_from_normal(points, normal)

        return np.roll(points, -top_left_index, axis=0)

    def _get_top_left_corner_from_normal(self, points, normal) -> np.ndarray:
        world_up = np.array([0, 0, 1])

        if abs(np.dot(normal, world_up)) > 0.99:
            if np.dot(normal, world_up) > 0:
                world_up = np.array([0, 1, 0])
            else:
                world_up = np.array([0, -1, 0])

        right = np.cross(world_up, normal)
        right /= np.linalg.norm(right)

        up = np.cross(normal, right)
        up /= np.linalg.norm(up)

        centroid = np.mean(points, axis=0)
        relative_points = points - centroid

        x_coords = np.dot(relative_points, right)
        y_coords = np.dot(relative_points, up)

        sort_keys = np.column_stack((-y_coords, x_coords))
        top_left_index = np.lexsort((sort_keys[:, 1], sort_keys[:, 0]))[0]

        return top_left_index

    def _determine_boundary_condition(
        self, surface: Surface
    ) -> tuple[Literal['Outdoors', 'Ground', 'Surface'], int | None]:
        enclosure_info = self._surface_to_enclosure.get(surface.surface_id)
        if enclosure_info is None:
            raise ValueError(f'Surface {surface.surface_id} has no enclosure info')
        enclosure, is_side1 = enclosure_info
        kind = enclosure.kind
        if kind == EnclosureKind.OUTWALL or kind == EnclosureKind.ROOF:
            return ('Outdoors', None)
        elif kind == EnclosureKind.GROUNDFLOOR:
            return ('Ground', None)
        elif kind == EnclosureKind.FLOOR_CEILLING:
            return ('Surface', enclosure.side2 if is_side1 else enclosure.side1)
        elif kind == EnclosureKind.AIRFLOOR:
            return ('Outdoors', None)
        elif kind == EnclosureKind.INWALL:
            return ('Surface', enclosure.side2 if is_side1 else enclosure.side1)
        else:
            raise ValueError(f'Unknown enclosure kind {kind}')

    def _determine_surface_type(
        self, surface: Surface
    ) -> Literal['Roof', 'Floor', 'Wall', 'Ceiling']:
        enclosure, _ = self._surface_to_enclosure[surface.surface_id]
        if enclosure.kind is None:
            raise ValueError(f'Surface {surface.surface_id} has no enclosure info')
        if enclosure.kind == EnclosureKind.ROOF:
            return 'Roof'
        elif (
            enclosure.kind == EnclosureKind.GROUNDFLOOR
            or enclosure.kind == EnclosureKind.AIRFLOOR
        ):
            return 'Floor'
        elif (
            enclosure.kind == EnclosureKind.INWALL
            or enclosure.kind == EnclosureKind.OUTWALL
        ):
            return 'Wall'
        elif enclosure.kind == EnclosureKind.FLOOR_CEILLING:
            if surface.type == SurfaceType.CEILING:
                return 'Ceiling'
            elif surface.type == SurfaceType.MIDDLE_FLOOR:
                return 'Floor'
            else:
                raise ValueError(f'Unknown surface type {surface.type}')
        else:
            raise ValueError(f'Unknown enclosure kind {enclosure.kind}')

    def _get_construction_name(self, surface: Surface) -> str:
        """Get IDF construction name for an enclosure."""
        enclosure, _ = self._surface_to_enclosure[surface.surface_id]
        if enclosure.kind is None or enclosure.construction is None:
            raise ValueError(f'Surface {surface.surface_id} has no enclosure info')

        name = None
        if self.construction_converter:
            name = self.construction_converter.get_construction_name(
                enclosure.kind, enclosure.construction
            )
        if name is None:
            raise ValueError(
                f'Construction name not found for surface {surface.surface_id}'
            )
        return name

    def _get_zone_name(self, room_id: int) -> str:
        """Get IDF zone name for a room."""
        if self.zone_converter:
            name = self.zone_converter.get_zone_name(room_id)
            if name is None:
                raise ValueError(f'Zone name not found for room {room_id}')
            return name
        raise ValueError(f'Zone converter not found for room {room_id}')

    def _get_sun_exposure(
        self, boundary_condition: str
    ) -> Literal['NoSun', 'SunExposed']:
        if boundary_condition == 'Outdoors':
            return 'SunExposed'
        return 'NoSun'

    def _get_wind_exposure(
        self, boundary_condition: str
    ) -> Literal['NoWind', 'WindExposed']:
        if boundary_condition == 'Outdoors':
            return 'WindExposed'
        return 'NoWind'

    def _validate_zone_geometry_closure(
        self,
        surfaces_ordered_vertices: list[
            tuple[BuildingSurfaceDetailed, np.ndarray, np.ndarray]
        ],
    ) -> bool:
        import trimesh

        mesh = self._surfaces_to_mesh(surfaces_ordered_vertices)
        if mesh is None or len(mesh.faces) < 4:
            return False

        if mesh.is_watertight:
            return True

        trimesh.repair.fill_holes(mesh)
        if mesh.is_watertight:
            return True

        mesh.export(f'debug_{surfaces_ordered_vertices[0][0].zone_name}.glb')
        return False

    def _surfaces_to_mesh(
        self, surfaces: list[tuple[BuildingSurfaceDetailed, np.ndarray, np.ndarray]]
    ):
        scene = trimesh.Scene()

        for i, (surface_obj, pts, normal) in enumerate(surfaces):
            faces = self._triangulate_polygon(pts, normal)

            mesh = trimesh.Trimesh(vertices=pts, faces=faces)

            scene.add_geometry(mesh, node_name=surface_obj.name or f'surface_{i}')

        return scene

    def get_surface_name(self, surface_id: int) -> str | None:
        stmt = select(Surface).where(Surface.surface_id == surface_id)
        surface = self.session.execute(stmt).scalars().first()
        if surface is None:
            return None
        return self.make_name('Surface', surface.surface_id, surface.name)
