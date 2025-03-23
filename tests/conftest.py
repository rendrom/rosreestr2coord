from unittest.mock import patch

import pytest
from rosreestr2coord.parser import Area


@pytest.fixture
def feature_from_api():
    return {
        "id": 39128231,
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [104.63460275151176, 52.26667215769885],
                    [104.63450479864538, 52.266502806027226],
                    [104.63519493087094, 52.266352425260756],
                    [104.63529288601124, 52.266521776345144],
                    [104.63460275151176, 52.26667215769885],
                ]
            ],
            "crs": {"type": "name", "properties": {"name": "EPSG:3857"}},
        },
        "properties": {"label": "38:06:144003:4723", "options": {"cad_num": "38:06:144003:4723", "cost_value": 271540}},
    }


@pytest.fixture
def mock_area(feature_from_api):
    with patch("rosreestr2coord.parser.Area.get_geometry"):
        area = Area("38:06:144003:4723", area_type=1)
        area.feature = feature_from_api
        return area
