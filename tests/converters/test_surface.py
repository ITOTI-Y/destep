import unittest
from typing import override
from unittest.mock import patch

import numpy as np

from src.converters.surface import SurfaceConverter
from src.database.models.geometry import Surface


class SurfacePartsTests(unittest.TestCase):
    @override
    def setUp(self) -> None:
        self.converter = object.__new__(SurfaceConverter)
        self.surface = Surface(surface_id=742376)
        # Reduced from Guangzhou Mall surface 742376. The three vertices at
        # y=-58.0061553116 leave a collinear triangle after Earcut and merging.
        self.loops = [
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

    def test_collinear_triangle_preserves_surface_area_and_winding(self) -> None:
        for direction in (1.0, -1.0):
            with (
                self.subTest(direction=direction),
                patch.object(
                    self.converter, '_get_surface_plane_loops', return_value=self.loops
                ),
            ):
                normal = np.array([0.0, 0.0, direction])
                parts = self.converter._split_surface(self.surface, normal)

                total_area = 0.0
                for part in parts:
                    relative = part - part[0]
                    area_vector = (
                        np.cross(relative, np.roll(relative, -1, axis=0)).sum(axis=0)
                        / 2.0
                    )
                    self.assertGreater(float(area_vector @ normal), 1e-10)
                    total_area += float(np.linalg.norm(area_vector))
                self.assertAlmostEqual(total_area, 500.96298554485116, places=8)

    def test_all_degenerate_parts_raise_with_surface_id(self) -> None:
        collinear = self.loops[0][3:6]
        with (
            patch.object(
                self.converter, '_get_surface_plane_loops', return_value=self.loops
            ),
            patch.object(self.converter, '_merge_triangles', return_value=[collinear]),
            self.assertRaisesRegex(ValueError, 'Surface 742376.*non-degenerate'),
        ):
            self.converter._split_surface(self.surface, np.array([0.0, 0.0, 1.0]))


if __name__ == '__main__':
    unittest.main()
