import pytest

import rosreestr2coord.parser


@pytest.fixture(scope="module")
def area():
    return rosreestr2coord.parser.Area("38:06:144003:4723")


@pytest.fixture(scope="module")
def area_coords():
    _coords = [[[[104.63459668419641, 52.26667593254523],
                 [104.63449966614576, 52.26650612315831],
                 [104.63519043466663, 52.26635650036231],
                 [104.63528551235628, 52.26652631032228],
                 [104.63459668419641, 52.26667593254523]]]]
    return _coords

@pytest.fixture(scope="module")
def area_geometry(area_coords):
    _geom = '"geometry": {"type": "MultiPolygon", "coordinates": ' \
            f'{area_coords}' \
            '}'
    return _geom
