import pytest
from idfpy import IDF
from idfpy.models import Construction, WindowMaterialSimpleGlazingSystem

from src.converters.fenestration import FenestrationConverter
from src.converters.manager import LookupTable
from src.database.models.fenestration import Window, WindowTypeData
from src.utils.pinyin import PinyinConverter


@pytest.fixture
def converter() -> FenestrationConverter:
    converter = object.__new__(FenestrationConverter)
    converter.idf = IDF()
    converter.lookup_table = LookupTable()
    converter.pinyin = PinyinConverter()
    converter._glass_data_by_type = {
        46: WindowTypeData(
            id=46, name='g46', k=2.4, sc=0.48045977, light_trans_ratio=0.78
        ),
        51: WindowTypeData(
            id=51, name='g51', k=3.0, sc=0.34942529, light_trans_ratio=0.78
        ),
    }
    converter._created_windows_constructions = {}
    return converter


def test_window_construction_follows_window_type(
    converter: FenestrationConverter,
) -> None:
    first = converter._create_window_construction(Window(id=1, type=46))
    second = converter._create_window_construction(Window(id=2, type=46))
    other = converter._create_window_construction(Window(id=3, type=51))

    assert first == second != other
    assert list(converter.idf.all_of_type(Construction)) == [first, other]
    glazing = converter.idf.all_of_type(WindowMaterialSimpleGlazingSystem)
    material = glazing[converter.make_name('WindowMaterial', 46, 'g46')]
    assert material.u_factor == pytest.approx(2.4)
    assert material.solar_heat_gain_coefficient == pytest.approx(0.418, abs=1e-3)
    assert material.visible_transmittance == pytest.approx(0.78)


def test_unknown_window_type_raises(converter: FenestrationConverter) -> None:
    with pytest.raises(ValueError, match='unknown window type 99'):
        converter._create_window_construction(Window(id=1, type=99))
