import pytest
from rosreestr2coord.parser import Area


@pytest.mark.integration
@pytest.mark.parametrize(
    "code,area_type,label",
    [
        ("38:06:144003:4723", 1, "38:06:144003:4723"),
        ("75:09:300418", 2, "75:09:300418"),
        ("75:09-4.1", 4, "75:09-4.1"),
        ("75:09-9.2", 5, "75:09-9.2"),
        ("75:09-7.6", 7, "75:09-7.6"),
    ],
)
def test_area_api_response(code, area_type, label):
    area = Area(code, area_type=area_type, use_cache=False)
    geojson = area.to_geojson(dumps=False)

    assert geojson is not None, f"No GeoJSON returned for {code}"
    assert geojson["type"] == "Feature"
    assert geojson["geometry"]["type"] in ("Polygon", "MultiPolygon")
    assert len(geojson["geometry"]["coordinates"]) > 0
    assert geojson["properties"]["label"] == label

    kml = area.to_kml()
    assert kml is not None
