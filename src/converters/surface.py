from __future__ import annotations

from collections import defaultdict
from enum import IntEnum
from typing import TYPE_CHECKING, Literal

import mapbox_earcut as earcut
import numpy as np
import trimesh
from idfpy import IDF
from idfpy.models import (
    BuildingSurfaceDetailed,
    BuildingSurfaceDetailedVerticesItem,
)
from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from src.converters.base import BaseConverter, UnitConverter
from src.converters.construction import EnclosureKind
from src.database.models import MainEnclosure
from src.database.models.building import Room
from src.database.models.fenestration import Door, Window
from src.database.models.geometry import LoopPoint, Surface
from src.utils.pinyin import PinyinConverter

if TYPE_CHECKING:
    from .manager import LookupTable

EPSILON = 1e-10


class SurfaceType(IntEnum):
    """DeST surface type enumeration."""

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
        lookup_table: LookupTable,
        pinyin: PinyinConverter | None = None,
    ) -> None:
        super().__init__(session, idf, lookup_table, pinyin)
        self._surface_pairings: dict[int, int] = {}

        self._surface_to_enclosure: dict[int, tuple[MainEnclosure, bool]] = {}
        self._build_enclosure_lookup()

        self._surface_to_fenestration: dict[int, Window | Door] = {}
        self._build_fenestration_lookup()

        self._created_surfaces: dict[str, BuildingSurfaceDetailed] = {}
        self._surface_part_names: dict[int, list[str]] = {}
        self._surface_parts: dict[int, list[np.ndarray]] = {}
        self._surface_normals: dict[int, np.ndarray] = {}

    def _build_enclosure_lookup(self) -> None:
        """Build lookup table from Surface ID to MainEnclosure."""
        stmt = select(MainEnclosure)
        enclosures = list(self.session.execute(stmt).scalars().all())

        for enc in enclosures:
            if enc.side1 is not None:
                self._surface_to_enclosure[enc.side1] = (enc, True)
                self._surface_pairings[enc.side1] = enc.side2
            if enc.side2 is not None:
                self._surface_to_enclosure[enc.side2] = (enc, False)
                self._surface_pairings[enc.side2] = enc.side1

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
        self._prepare_surface_parts(list(rooms))
        for room in rooms:
            if self.convert_one(room):
                logger.info(f'Converted room {room.id}')
                self.stats.converted += 1
            else:
                logger.warning(
                    f'Failed to convert room {room.id} or zone is not watertight'
                )

        if not self._surface_reference_check():
            raise ValueError('Surface reference check failed')
        else:
            logger.info('Surface reference check passed')

    def convert_one(self, instance: Room) -> bool:
        room = instance
        surfaces = [
            s
            for s in room.surfaces
            if s.surface_id not in self._surface_to_fenestration
        ]
        surface_by_types = defaultdict(list)
        for surface in surfaces:
            surface_by_types[surface.type].append(surface)
        normals = self._get_cached_normals(surfaces)
        _step_surface_ordered_vertices = []

        for surface, normal in zip(surfaces, normals, strict=True):
            try:
                parts = self._surface_parts.get(surface.surface_id)
                if parts is None:
                    parts = self._split_surface(surface, normal)
                    self._surface_parts[surface.surface_id] = parts

                boundary_condition, boundary_condition_object = (
                    self._determine_boundary_condition(surface)
                )

                base_surface_name = self.make_name(
                    'Surface', surface.surface_id, surface.name
                )
                surface_type = self._determine_surface_type(surface)
                construction_name = self._get_construction_name(surface)
                zone_name = self._get_zone_name(surface.of_room)
                sun_exposure = self._get_sun_exposure(boundary_condition)
                wind_exposure = self._get_wind_exposure(boundary_condition)

                names = self._surface_part_names.get(surface.surface_id)
                if names is None:
                    names = self._make_surface_part_names(base_surface_name, len(parts))
                    self._surface_part_names[surface.surface_id] = names
                self.lookup_table.SURFACE_PART_NAMES[surface.surface_id] = names
                self.lookup_table.SURFACE_PART_VERTICES[surface.surface_id] = parts
                for part_index, ordered_points in enumerate(parts):
                    surface_name = names[part_index]
                    idf_surface = BuildingSurfaceDetailed(
                        name=surface_name,
                        surface_type=surface_type,
                        construction_name=construction_name,
                        zone_name=zone_name,
                        outside_boundary_condition=boundary_condition,
                        outside_boundary_condition_object=(
                            self.get_surface_name(
                                boundary_condition_object,
                                self._find_matching_part_index(
                                    boundary_condition_object, ordered_points
                                ),
                            )
                            if boundary_condition_object is not None
                            else None
                        ),
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
                    _step_surface_ordered_vertices.append(
                        (idf_surface, ordered_points, normal)
                    )
                    self.idf.add(idf_surface)
                    self._created_surfaces[surface_name] = idf_surface
                self.lookup_table.SURFACE_TO_NAME[surface.surface_id] = names[0]

            except Exception as e:
                self.stats.add_warning(
                    f'Failed to convert surface {surface.surface_id}: {e}'
                )
                self.stats.skipped += 1
                continue
        return bool(
            self._validate_zone_geometry_closure(_step_surface_ordered_vertices)
        )

    def _prepare_surface_parts(self, rooms: list[Room]) -> None:
        """Precompute split surfaces so interzone references are deterministic."""
        for room in rooms:
            surfaces = [
                s
                for s in room.surfaces
                if s.surface_id not in self._surface_to_fenestration
            ]
            normals = self._get_cached_normals(surfaces)
            for surface, normal in zip(surfaces, normals, strict=True):
                parts = self._split_surface(surface, normal)
                self._surface_parts[surface.surface_id] = parts
                base_name = self.make_name('Surface', surface.surface_id, surface.name)
                names = self._make_surface_part_names(base_name, len(parts))
                self._surface_part_names[surface.surface_id] = names
                self.lookup_table.SURFACE_PART_NAMES[surface.surface_id] = names
                self.lookup_table.SURFACE_PART_VERTICES[surface.surface_id] = parts

    def _get_cached_normals(self, surfaces: list[Surface]) -> np.ndarray:
        missing = [
            surface
            for surface in surfaces
            if surface.surface_id not in self._surface_normals
        ]
        if missing:
            for surface, normal in zip(
                missing, self._get_outside_normals(missing), strict=True
            ):
                self._surface_normals[surface.surface_id] = normal
        return np.array(
            [self._surface_normals[surface.surface_id] for surface in surfaces]
        )

    def _make_surface_part_names(self, base_name: str, count: int) -> list[str]:
        if count == 1:
            return [base_name]
        return [f'{base_name}_Part_{index}' for index in range(1, count + 1)]

    def _split_surface(self, surface: Surface, normal: np.ndarray) -> list[np.ndarray]:
        """Split a surface with holes into simple polygons."""
        loops = self._get_surface_plane_loops(surface)
        if len(loops) == 1 or surface.type in [SurfaceType.INTERIOR_WALL,SurfaceType.EXTERIOR_WALL]:
            return [self._order_points_array(loops[0], normal, round_coordinates=False)]

        split_normal = normal.copy()
        if split_normal[np.argmax(np.abs(split_normal))] < 0:
            split_normal = -split_normal
        points, faces = self._triangulate_polygon_with_holes(loops, split_normal)
        ordered_parts = []
        for part in self._merge_triangles(points, faces, split_normal):
            if abs(self._compute_signed_area(part, normal)) < EPSILON:
                continue
            ordered_parts.append(
                self._order_points_array(part, normal, round_coordinates=False)
            )
        if not ordered_parts:
            raise ValueError(
                f'Surface {surface.surface_id} has no non-degenerate polygon parts'
            )
        return ordered_parts

    def _triangulate_polygon(self, pts: np.ndarray, normal: np.ndarray) -> np.ndarray:
        pts_2d = self._project_to_2d(pts, normal)
        pts_2d = pts_2d.astype(np.float64)
        rings = np.array([len(pts_2d)], dtype=np.uint32)
        result = earcut.triangulate_float64(pts_2d, rings)
        faces = np.array(result).reshape(-1, 3)
        return faces

    def _triangulate_polygon_with_holes(
        self, loops: list[np.ndarray], normal: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        """Triangulate an outer loop and its inner loops."""
        points = np.concatenate(loops, axis=0)
        points_2d = self._project_to_2d(points, normal).astype(np.float64)
        ring_ends = np.cumsum([len(loop) for loop in loops], dtype=np.uint32)
        result = earcut.triangulate_float64(points_2d, ring_ends)
        faces = np.asarray(result, dtype=np.uint32).reshape(-1, 3)
        if len(faces) == 0:
            raise ValueError('Polygon with holes could not be triangulated')
        return points, faces

    def _merge_triangles(
        self, points: np.ndarray, faces: np.ndarray, normal: np.ndarray
    ) -> list[np.ndarray]:
        """Merge adjacent triangles when their union remains one polygon."""
        points_2d = self._project_to_2d(points, normal)
        polygons: list[list[int]] = []
        for face in faces:
            polygon = [int(index) for index in face]
            if self._signed_area_indices(polygon, points_2d) < 0:
                polygon.reverse()
            polygons.append(polygon)

        while True:
            edge_to_polygons: dict[tuple[int, int], list[int]] = defaultdict(list)
            for polygon_index, polygon in enumerate(polygons):
                for start, end in zip(polygon, polygon[1:] + polygon[:1], strict=True):
                    edge = (min(start, end), max(start, end))
                    edge_to_polygons[edge].append(polygon_index)

            merged = False
            for polygon_indices in edge_to_polygons.values():
                if len(polygon_indices) != 2:
                    continue
                first, second = polygon_indices
                candidate = self._merge_polygon_indices(
                    polygons[first], polygons[second], points_2d
                )
                if candidate is None:
                    continue
                polygons = [
                    polygon
                    for index, polygon in enumerate(polygons)
                    if index not in (first, second)
                ]
                polygons.append(candidate)
                merged = True
                break
            if not merged:
                break

        result = []
        for polygon in polygons:
            polygon = self._remove_collinear_indices(polygon, points_2d)
            if len(polygon) >= 3:
                result.append(points[polygon])
        return result

    def _signed_area_indices(self, polygon: list[int], points_2d: np.ndarray) -> float:
        area = 0.0
        for start, end in zip(polygon, polygon[1:] + polygon[:1], strict=True):
            area += (
                points_2d[start, 0] * points_2d[end, 1]
                - points_2d[end, 0] * points_2d[start, 1]
            )
        return area / 2.0

    def _merge_polygon_indices(
        self,
        first: list[int],
        second: list[int],
        points_2d: np.ndarray,
    ) -> list[int] | None:
        first_edges = {
            (start, end)
            for start, end in zip(first, first[1:] + first[:1], strict=True)
        }
        second_edges = {
            (start, end)
            for start, end in zip(second, second[1:] + second[:1], strict=True)
        }
        shared = first_edges & {(end, start) for start, end in second_edges}
        if len(shared) != 1:
            return None

        edges = (
            (first_edges | second_edges)
            - shared
            - {(end, start) for start, end in shared}
        )
        next_vertex: dict[int, int] = {}
        for start, end in edges:
            if start in next_vertex:
                return None
            next_vertex[start] = end

        start = next(iter(next_vertex))
        polygon = [start]
        while True:
            end = next_vertex.get(polygon[-1])
            if end is None:
                return None
            if end == start:
                break
            if end in polygon:
                return None
            polygon.append(end)
        if len(polygon) < 3 or len(polygon) != len(next_vertex):
            return None
        if self._signed_area_indices(polygon, points_2d) < 0:
            polygon.reverse()
        return polygon

    def _remove_collinear_indices(
        self, polygon: list[int], points_2d: np.ndarray
    ) -> list[int]:
        changed = True
        while changed and len(polygon) > 3:
            changed = False
            for index in range(len(polygon)):
                a = points_2d[polygon[index - 1]]
                b = points_2d[polygon[index]]
                c = points_2d[polygon[(index + 1) % len(polygon)]]
                ab = b - a
                bc = c - b
                cross = ab[0] * bc[1] - ab[1] * bc[0]
                if abs(cross) <= EPSILON:
                    polygon.pop(index)
                    changed = True
                    break
        return polygon

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

    def _extract_vertices_from_geometry(self, geometry) -> np.ndarray:
        """Extract 3D vertices from a geometry object with loop_points.

        Removes consecutive duplicate vertices (distance < EPSILON).
        """
        vertices = [
            [lp.point_ref.x, lp.point_ref.y, lp.point_ref.z]
            for lp in geometry.loop_points
            if lp.point_ref is not None
        ]
        pts = np.array(vertices).reshape(-1, 3)
        if len(pts) < 3:
            return pts
        mask = np.ones(len(pts), dtype=bool)
        for i in range(len(pts)):
            j = (i + 1) % len(pts)
            if np.linalg.norm(pts[i] - pts[j]) < EPSILON:
                mask[j] = False
        return pts[mask]

    def _get_geometry_loops(self, geometry) -> list[np.ndarray]:
        """Extract the outer loop and all inner loops from a geometry."""
        stmt = (
            select(LoopPoint)
            .where(LoopPoint.of_geometry == geometry.geometry_id)
            .order_by(LoopPoint.loop_id, LoopPoint.point_no)
        )
        rows = self.session.execute(stmt).scalars().all()
        grouped: dict[int, list[list[float]]] = defaultdict(list)
        for loop_point in rows:
            point = loop_point.point_ref
            if point is None or point.x is None or point.y is None or point.z is None:
                raise ValueError(
                    f'Geometry {geometry.geometry_id} has a loop point '
                    'with missing coordinates'
                )
            grouped[loop_point.loop_id].append([point.x, point.y, point.z])
        boundary_loop_id = geometry.boundary_loop_id
        loop_ids = [
            boundary_loop_id,
            *sorted(loop_id for loop_id in grouped if loop_id != boundary_loop_id),
        ]
        return [
            np.asarray(grouped[loop_id], dtype=float)
            for loop_id in loop_ids
            if loop_id is not None and len(grouped[loop_id]) >= 3
        ]

    def _get_surface_vertices(self, surface: Surface) -> np.ndarray:
        """Extract 3D vertices from a surface geometry."""
        assert surface.geometry_ref is not None
        return self._extract_vertices_from_geometry(surface.geometry_ref)

    def _get_surface_plane_vertices(self, surface: Surface) -> np.ndarray:
        """Extract 3D vertices from a surface plane geometry."""
        enclosure, _ = self._surface_to_enclosure[surface.surface_id]
        middle_plane = enclosure.middle_plane_ref
        if middle_plane is None:
            raise ValueError(f'Surface {surface.surface_id} has no middle plane')
        assert middle_plane.geometry_ref is not None
        return self._extract_vertices_from_geometry(middle_plane.geometry_ref)

    def _get_surface_plane_loops(self, surface: Surface) -> list[np.ndarray]:
        enclosure, _ = self._surface_to_enclosure[surface.surface_id]
        middle_plane = enclosure.middle_plane_ref
        if middle_plane is None or middle_plane.geometry_ref is None:
            raise ValueError(f'Surface {surface.surface_id} has no middle plane')
        loops = self._get_geometry_loops(middle_plane.geometry_ref)
        if not loops:
            raise ValueError(f'Surface {surface.surface_id} has no geometry loops')
        return loops

    def _get_outside_normals(self, surfaces: list[Surface]) -> np.ndarray:
        """Calculate outward-facing normals for surfaces."""
        normals: np.ndarray = np.zeros((len(surfaces), 3))
        for i, surface in enumerate(surfaces):
            if surface.type == SurfaceType.CEILING:
                normals[i] = [0, 0, 1]
            elif surface.type in [
                SurfaceType.GROUND_FLOOR,
                SurfaceType.AIR_FLOOR,
                SurfaceType.MIDDLE_FLOOR,
            ]:
                normals[i] = [0, 0, -1]
            else:
                vertices = self._get_surface_plane_vertices(surface)
                current_center = vertices.mean(axis=0)
                normal_vector = self._find_polygon_normal(vertices)

                assert normal_vector is not None

                enclosure, is_side1 = self._surface_to_enclosure[surface.surface_id]
                other_surface = (
                    enclosure.surface_side2 if is_side1 else enclosure.surface_side1
                )

                assert other_surface is not None

                if not self._is_outside_direction(
                    normal_vector, current_center, other_surface
                ):
                    normal_vector = -normal_vector

                assert enclosure.middle_plane_ref is not None
                plane_id = enclosure.middle_plane_ref.plane_id
                self.lookup_table.PLANE_TO_NORMAL[plane_id] = normal_vector
                normals[i] = normal_vector
        return normals

    def _is_outside_direction(
        self, normal: np.ndarray, current_center: np.ndarray, other_surface: Surface
    ) -> bool:
        other_vertices = self._get_surface_vertices(other_surface)
        other_normal = self._find_polygon_normal(other_vertices)
        if other_normal is None:
            return True
        d = -np.dot(other_normal, other_vertices[0])

        denom = np.dot(normal, other_normal)
        if abs(denom) < EPSILON:
            return True  # parallel, no intersection

        t = -(np.dot(other_normal, current_center) + d) / denom

        return t > 0

    def _get_reference_points(
        self, surfaces_by_type: list[list[Surface]]
    ) -> np.ndarray:
        reference_points = []
        for surfaces in surfaces_by_type:
            if not surfaces:
                continue
            for surface in surfaces:
                pts = self._get_surface_plane_vertices(surface)
                reference_points.extend(pts)
        return np.unique(np.array(reference_points), axis=0)

    def _find_polygon_normal(self, pts: np.ndarray) -> np.ndarray | None:
        """Find surface normal from polygon vertices using Newell's method (O(n))."""
        n = len(pts)
        if n < 3:
            return None

        normal = np.zeros(3)
        for i in range(n):
            curr = pts[i]
            next_pt = pts[(i + 1) % n]
            normal[0] += (curr[1] - next_pt[1]) * (curr[2] + next_pt[2])
            normal[1] += (curr[2] - next_pt[2]) * (curr[0] + next_pt[0])
            normal[2] += (curr[0] - next_pt[0]) * (curr[1] + next_pt[1])

        norm_length = np.linalg.norm(normal)
        if norm_length < EPSILON:
            return None

        return normal / norm_length

    def _order_points_array(
        self,
        points: np.ndarray,
        normal: np.ndarray,
        *,
        round_coordinates: bool = True,
    ) -> np.ndarray:
        """Order one polygon according to EnergyPlus GlobalGeometryRules."""

        if len(points) < 3:
            raise ValueError('Polygon has fewer than 3 unique vertices')

        signed_area = self._compute_signed_area(points, normal)
        if abs(signed_area) < EPSILON:
            raise ValueError('Polygon has zero area (degenerate polygon)')
        if signed_area < 0:
            points = points[::-1]

        top_left_index = self._get_top_left_corner_from_normal(points, normal)
        points = np.roll(points, -top_left_index, axis=0)
        if round_coordinates:
            points = UnitConverter.round_coord_array(points)
        return points

    def _find_matching_part_index(self, surface_id: int, points: np.ndarray) -> int:
        """Find the corresponding split part on an adjacent surface."""
        parts = self._surface_parts.get(surface_id)
        if not parts:
            return 0
        target_centroid = points.mean(axis=0)
        target_normal = self._find_polygon_normal(points)
        if target_normal is None:
            return 0
        target_area = abs(self._compute_signed_area(points, target_normal))
        scores = []
        for index, part in enumerate(parts):
            part_normal = self._find_polygon_normal(part)
            if part_normal is None:
                scores.append((float('inf'), index))
                continue
            part_area = abs(self._compute_signed_area(part, part_normal))
            score = np.linalg.norm(part.mean(axis=0) - target_centroid) + abs(
                part_area - target_area
            )
            scores.append((score, index))
        return min(scores)[1]

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

    def _determine_boundary_condition(
        self, surface: Surface
    ) -> tuple[Literal['Outdoors', 'Ground', 'Surface'], int | None]:
        enclosure_info = self._surface_to_enclosure.get(surface.surface_id)
        if enclosure_info is None:
            raise ValueError(f'Surface {surface.surface_id} has no enclosure info')
        enclosure, is_side1 = enclosure_info
        kind = enclosure.kind
        if kind in (EnclosureKind.OUTWALL, EnclosureKind.ROOF, EnclosureKind.AIRFLOOR):
            return ('Outdoors', None)
        elif kind == EnclosureKind.GROUNDFLOOR:
            return ('Ground', None)
        elif kind in (EnclosureKind.FLOOR_CEILING, EnclosureKind.INWALL):
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
        elif enclosure.kind in (EnclosureKind.GROUNDFLOOR, EnclosureKind.AIRFLOOR):
            return 'Floor'
        elif enclosure.kind in (EnclosureKind.INWALL, EnclosureKind.OUTWALL):
            return 'Wall'
        elif enclosure.kind == EnclosureKind.FLOOR_CEILING:
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
        name = self.lookup_table.CONSTRUCTION_TO_NAME.get(
            (enclosure.kind, enclosure.construction)
        )
        assert name is not None, (
            f'Construction name not found for surface {surface.surface_id}'
        )
        return name

    def _get_zone_name(self, room_id: int | None) -> str:
        """Get IDF zone name for a room."""
        if room_id is None:
            raise ValueError('Room ID is None for surface')
        name = self.lookup_table.ROOM_TO_ZONE.get(room_id)
        assert name is not None, f'Zone name not found for room {room_id}'
        return name

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
        output_path: str | None = None,
    ) -> bool:
        """Validate that zone surfaces form a closed (watertight) geometry."""
        scene = self._surfaces_to_mesh(surfaces_ordered_vertices)
        if scene is None:
            logger.debug('Validation failed: scene is None')
            return False

        meshes = list(scene.geometry.values())
        if not meshes:
            logger.debug('Validation failed: no meshes')
            return False

        mesh = trimesh.util.concatenate(meshes)
        if mesh is None or len(mesh.faces) < 4:
            logger.debug(f'Validation failed: faces={len(mesh.faces) if mesh else 0}')
            return False

        mesh.merge_vertices()
        mesh.fix_normals()

        if mesh.is_watertight:
            return True

        if output_path is not None:
            scene.export(output_path)
        return False

    def _surfaces_to_mesh(
        self, surfaces: list[tuple[BuildingSurfaceDetailed, np.ndarray, np.ndarray]]
    ):
        scene = trimesh.Scene()

        for i, (surface_obj, pts, normal) in enumerate(surfaces):
            surface_name = surface_obj.name or f'surface_{i}'
            try:
                faces = self._triangulate_polygon(pts, normal)
            except Exception as e:
                self.stats.add_warning(
                    f'Failed to triangulate surface {surface_name}: {e}'
                )
                self.stats.skipped += 1
                continue
            mesh = trimesh.Trimesh(vertices=pts, faces=faces)
            scene.add_geometry(mesh, node_name=surface_name)

        return scene

    def _surface_reference_check(self) -> bool:
        for _, surface in self._created_surfaces.items():
            if surface.outside_boundary_condition_object is None:
                continue
            other_surface_name = surface.outside_boundary_condition_object
            if other_surface_name not in self._created_surfaces:
                return False
        return True

    def get_surface_name(self, surface_id: int, part_index: int = 0) -> str | None:
        names = self._surface_part_names.get(surface_id)
        if names is not None and part_index < len(names):
            return names[part_index]
        stmt = select(Surface).where(Surface.surface_id == surface_id)
        surface = self.session.execute(stmt).scalars().first()
        if surface is None:
            return None
        base_name = self.make_name('Surface', surface.surface_id, surface.name)
        return self._make_surface_part_names(base_name, 1)[0]
