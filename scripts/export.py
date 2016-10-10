# coding: utf-8
from __future__ import print_function, division

import copy
import csv
import os


def make_output(output, file_name, file_format, out_path=""):
    out_path = out_path if out_path else file_format
    abspath = os.path.abspath(output)
    filename = '%s.%s' % (file_name, file_format)
    path = os.path.join(abspath, out_path)
    if not os.path.isdir(path):
        os.makedirs(path)
    return os.path.join(path, filename)


def _write_csv_row(f, area, header=False):
    try:
        xy = copy.deepcopy(list(getattr(area, "xy")))
        for geom in xy:
            for poly in geom:
                for c in range(len(poly)):
                    poly[c] = poly[c][::-1]
        attrs = getattr(area, "attrs", {})
        cols = [
            {"name": "№", "value": attrs.get("cn", getattr(area, "code"))},
            {"name": "Площадь", "value": attrs.get("area_value", "")},
            {"name": "Цена", "value": attrs.get("cad_cost", "")},
            {"name": "Координаты", "value": xy},
        ]

        if header:
            f.writerow(map(lambda x: x["name"], cols))

        f.writerow(map(lambda x: x["value"], cols))
    except Exception as er:
        print(er)
        pass


def area_csv_output(output, area):
    path = make_output(output, area.file_name, "csv")
    f = csv.writer(open(path, "wb+"))
    _write_csv_row(f, area)


def batch_csv_output(output, areas, file_name):
    path = make_output(output, file_name, "csv")
    f = csv.writer(open(path, "wb+"))
    for a in range(len(areas)):
        _write_csv_row(f, areas[a], a == 0)
    return path


def area_json_output(output, area, with_attrs=False):
    geojson = area.to_geojson_poly(with_attrs)
    if geojson:
        f = open(make_output(output, area.file_name, "geojson"), 'w')
        f.write(geojson)
        f.close()


def coords2geojson(coords, geom_type, crs_name, attrs=None):
    if attrs is False:
        attrs = {}
    if coords:
        features = []
        feature_collection = {
            "type": "FeatureCollection",
            "crs": {"type": "name", "properties": {"name": crs_name}},
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
                       "properties": attrs,
                       "geometry": {"type": "MultiPolygon", "coordinates": multi_polygon}}
            features.append(feature)
        return feature_collection
    return False
