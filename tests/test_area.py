import json

import pytest


def test_geojson_structure(mock_area):
    geojson_str = mock_area.to_geojson()
    geojson = json.loads(geojson_str)

    assert geojson["type"] == "Feature"
    assert "geometry" in geojson
    assert geojson["geometry"]["type"] == "Polygon"
    assert isinstance(geojson["geometry"]["coordinates"], list)


def test_geojson_coordinates_content(mock_area):
    coords = mock_area.feature["geometry"]["coordinates"][0]
    assert coords[0] == [104.63460275151176, 52.26667215769885]
    assert len(coords) == 5
    assert coords[0] == coords[-1]


def test_geojson_properties(mock_area):
    props = mock_area.feature["properties"]
    assert props["label"] == "38:06:144003:4723"
    assert props["options"]["cost_value"] == 271540


def test_to_geojson_poly_warns_and_returns(mock_area):
    with pytest.warns(DeprecationWarning):
        result = mock_area.to_geojson_poly()
    assert '"type": "Feature"' in result
    assert '"coordinates": [[[104.63460275151176' in result
