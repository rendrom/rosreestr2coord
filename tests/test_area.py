import json

import pytest


def test_multipolygon_with_holes(area, area_coords):
    """
    Multipoly area with area area.

    Args:
        area: (todo): write your description
        area_coords: (todo): write your description
    """
    _coords = area.xy
    assert len(_coords[0][0]) == 4
    assert _coords[0][0][0] == area_coords[0][0][0]


def test_to_geojson(area):
    """
    Convert a geojson - like geojsonjson.

    Args:
        area: (todo): write your description
    """
    _json = area.to_geojson()

    # Проверяем, что в Area есть все необходимые атрибуты
    assert all(
        [k in ('type', 'features', 'crs') for k in [*json.loads(_json).keys()]])

    # Проверяем, что геометрия в Area содержит точку Point
    assert '{"type": "Point", "coordinates": ' \
           '[104.63528551235628, 52.26652631032228]}' in _json


def test_to_geojson_poly(area, area_geometry):
    """
    Convert a geojson geometry to a polygon.

    Args:
        area: (todo): write your description
        area_geometry: (todo): write your description
    """
    _poly = area.to_geojson_poly()

    # Проверяем, что в Area есть все необходимые атрибуты
    assert all(
        [k in ('type', 'properties', 'geometry', 'crs')
         for k in [*json.loads(_poly).keys()]])

    # Проверяем, что геометрия в Area содержит точку Point
    assert area_geometry in _poly

# area.get_coord() # [[[area1_xy], [hole1_xy], [hole2_xy]], [[area2_xyl]]]
# area.get_attrs()
