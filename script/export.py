# coding: utf-8
from __future__ import print_function, division


def coords2geojson(coords, geom_type):
    if coords:
        features = []
        feature_collection = {
            "type": "FeatureCollection",
            "crs": {"type": "name", "properties": {"name": "EPSG:3857"}},
            "features": features
        }
        if geom_type.upper() == "POINT":
            for i in range(len(coords)):
                for j in range(len(coords[i])):
                    xy = coords[i][j]
                    for x, y in xy:
                        point = {"type": "Feature",
                                 "properties": {"hole": j > 0},
                                 "geometry": {"type": "Point", "coordinates": [x, y]}}
                        features.append(point)
        elif geom_type.upper() == "POLYGON":
            close_xy = []
            multi_polygon = []
            for fry in range(len(coords)):
                for j in range(len(coords[fry])):
                    xy = coords[fry][j]
                    xy.append(xy[0])
                    close_xy.append(xy)
                multi_polygon.append(close_xy)
            feature = {"type": "Feature",
                       "properties": {},
                       "geometry": {"type": "MultiPolygon", "coordinates": multi_polygon}}
            features.append(feature)
        return feature_collection
    return False
