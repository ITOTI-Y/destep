import numpy as np
import pytest

from src.converters.surface import (
    SurfaceConverter,
    is_zone_open,
    zone_closure_residual,
)
from src.database.models.geometry import Surface

# Total area of the reduced surface; assertAlmostEqual(places=8) equivalent.
EXPECTED_AREA = 500.96298554485116
AREA_TOLERANCE = 5e-9


@pytest.fixture
def converter() -> SurfaceConverter:
    return object.__new__(SurfaceConverter)


@pytest.fixture
def surface() -> Surface:
    return Surface(surface_id=742376)


@pytest.fixture
def loops() -> list[np.ndarray]:
    # Reduced from Guangzhou Mall surface 742376. The three vertices at
    # y=-58.0061553116 leave a collinear triangle after Earcut and merging.
    return [
        np.array(
            [
                [201.203388602, -108.616547681, 5.7],
                [203.359468274, -85.4088460413, 5.7],
                [189.322145194, -43.6337274981, 5.7],
                [211.015732024, -58.0061553116, 5.7],
                [214.269906203, -58.0061553116, 5.7],
                [222.472359615, -58.0061553116, 5.7],
                [216.772359615, -65.6061553116, 5.7],
                [213.872359615, -65.6061553116, 5.7],
            ]
        ),
        np.array(
            [
                [210.551430862, -58.7472716866, 5.7],
                [202.763556344, -62.7120078051, 5.7],
                [195.00557635, -47.4731185276, 5.7],
            ]
        ),
    ]


@pytest.mark.parametrize('direction', [1.0, -1.0])
def test_collinear_triangle_preserves_surface_area_and_winding(
    converter: SurfaceConverter,
    surface: Surface,
    loops: list[np.ndarray],
    monkeypatch: pytest.MonkeyPatch,
    direction: float,
) -> None:
    monkeypatch.setattr(converter, '_get_surface_plane_loops', lambda _: loops)
    normal = np.array([0.0, 0.0, direction])

    parts = converter._split_surface(surface, normal)

    total_area = 0.0
    for part in parts:
        relative = part - part[0]
        area_vector = (
            np.cross(relative, np.roll(relative, -1, axis=0)).sum(axis=0) / 2.0
        )
        assert float(area_vector @ normal) > 1e-10
        total_area += float(np.linalg.norm(area_vector))
    assert total_area == pytest.approx(EXPECTED_AREA, abs=AREA_TOLERANCE)


def test_all_degenerate_parts_raise_with_surface_id(
    converter: SurfaceConverter,
    surface: Surface,
    loops: list[np.ndarray],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    collinear = loops[0][3:6]
    monkeypatch.setattr(converter, '_get_surface_plane_loops', lambda _: loops)
    monkeypatch.setattr(converter, '_merge_triangles', lambda *_: [collinear])

    with pytest.raises(ValueError, match='Surface 742376.*non-degenerate'):
        converter._split_surface(surface, np.array([0.0, 0.0, 1.0]))


def _box_faces(width: float, depth: float, height: float) -> list[np.ndarray]:
    """Outward-wound faces of an axis-aligned box with its corner at the origin."""
    w, d, h = width, depth, height
    return [
        np.array([[0, 0, 0], [0, d, 0], [w, d, 0], [w, 0, 0]], dtype=float),
        np.array([[0, 0, h], [w, 0, h], [w, d, h], [0, d, h]], dtype=float),
        np.array([[0, 0, 0], [w, 0, 0], [w, 0, h], [0, 0, h]], dtype=float),
        np.array([[w, 0, 0], [w, d, 0], [w, d, h], [w, 0, h]], dtype=float),
        np.array([[w, d, 0], [0, d, 0], [0, d, h], [w, d, h]], dtype=float),
        np.array([[0, d, 0], [0, 0, 0], [0, 0, h], [0, d, h]], dtype=float),
    ]


def test_zone_with_t_junction_is_closed() -> None:
    faces = _box_faces(4.0, 3.0, 2.8)
    # Split the south wall where two adjacent rooms meet it; the floor and
    # ceiling edges along y=0 now meet two wall edges (a T-junction).
    faces.pop(2)
    faces += [
        np.array([[0, 0, 0], [1.5, 0, 0], [1.5, 0, 2.8], [0, 0, 2.8]]),
        np.array([[1.5, 0, 0], [4, 0, 0], [4, 0, 2.8], [1.5, 0, 2.8]]),
    ]

    residual, total_area = zone_closure_residual(faces)

    assert not is_zone_open(residual, total_area)


def test_zone_with_floor_larger_than_ceiling_is_open() -> None:
    faces = _box_faces(11.0, 10.4, 5.7)
    # Floor reaches 0.2 m further south than the ceiling, leaving a 2.2 m2 gap.
    faces[0] = np.array([[0, -0.2, 0], [0, 10.4, 0], [11, 10.4, 0], [11, -0.2, 0]])

    residual, total_area = zone_closure_residual(faces)

    assert residual == pytest.approx(2.2)
    assert is_zone_open(residual, total_area)
