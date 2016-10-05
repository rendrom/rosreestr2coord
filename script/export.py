# coding: utf-8
from __future__ import print_function, division
import csv
import os


def area_csv_output(output, area):
    abspath = os.path.abspath(output)

    filename = '%s.csv' % area.file_name
    csv_path = os.path.join(abspath, "csv")
    if not os.path.isdir(csv_path):
        os.makedirs(csv_path)

    f = csv.writer(open(os.path.join(csv_path, filename), "wb+"))

    # Write CSV Header, If you dont need that, remove this line
    # f.writerow(["pk", "model", "codename", "name", "content_type"])

    attrs = getattr(area, "attrs")
    f.writerow([getattr(area, "code"),
                attrs["area_value"],
                attrs["cad_cost"],
                getattr(area, "xy")
                ])



def area_json_output(output, area):
    abspath = os.path.abspath(output)
    geojson = area.to_geojson_poly()
    if geojson:
        filename = '%s.geojson' % area.file_name
        geojson_path = os.path.join(abspath, "geojson")
        if not os.path.isdir(geojson_path):
            os.makedirs(geojson_path)
        file_path = os.path.join(geojson_path, filename)
        f = open(file_path, 'w')
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
