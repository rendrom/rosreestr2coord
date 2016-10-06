# coding: utf-8
from __future__ import print_function, division
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
    attrs = getattr(area, "attrs")
    cols = [
        {"name": "№", "value": attrs["cn"]},
        {"name": "Площадь", "value": attrs["area_value"]},
        {"name": "Цена", "value": attrs["cad_cost"]},
        {"name": "Координаты", "value": getattr(area, "xy")},
    ]

    if header:
        f.writerow(map(lambda x: x["name"], cols))

    f.writerow(map(lambda x: x["value"], cols))


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


def area_json_output(output, area):
    geojson = area.to_geojson_poly()
    if geojson:
        f = open(make_output(output, area.file_name, "geojson"), 'w')
        f.write(geojson)
        f.close()


def coords2geojson(coords, geom_type, coord):
    if coords:
        features = []
        feature_collection = {
            "type": "FeatureCollection",
            "crs": {"type": "name", "properties": {"name": coord}},
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
