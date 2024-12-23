import math
import re
from typing import List


def y2lat(y: float) -> float:
    return (2 * math.atan(math.exp(y / 6378137)) - math.pi / 2) / (math.pi / 180)


def x2lon(x: float) -> float:
    return x / (math.pi / 180.0) / 6378137.0


def xy2lonlat(x: float, y: float) -> List[float]:
    return [x2lon(x), y2lat(y)]


def code_to_filename(code: str) -> str:
    return code.replace(":", "_").replace("/", "-")


def transform_to_wgs(geojson: dict) -> dict:
    def process_coords(coords):
        return [xy2lonlat(x, y) for x, y in coords]

    result = geojson.copy()
    geom = result["geometry"]

    if geom["type"] == "Polygon":
        geom["coordinates"] = [process_coords(ring) for ring in geom["coordinates"]]
    elif geom["type"] == "MultiPolygon":
        geom["coordinates"] = [[process_coords(ring) for ring in poly] for poly in geom["coordinates"]]

    return result


def clear_code(code: str) -> str:
    """
    Remove first nulls from code xxxx:00xx >> xxxx:xx
    but if the cadastral number, for example "02:02-6.667",
    then the all parts will remain zeros
    """
    is_delimited_code = re.match(r"^\d+(\:\d+)", code)
    leave_zeros = "." in code
    if is_delimited_code and not leave_zeros:
        parts = []
        for x in code.split(":"):
            strip_zeros = x.lstrip("0")
            if strip_zeros:
                parts.append(strip_zeros)
            else:
                parts.append("0")
        return ":".join(parts)
    return code
