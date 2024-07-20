# coding: utf-8
import copy
import csv
import json
import os
import xml.etree.cElementTree as ET


def make_output(output, file_name, file_format, out_path=""):
    out_path = out_path if out_path else file_format
    abspath = os.path.abspath(output)
    filename = "%s.%s" % (file_name, file_format)
    path = os.path.join(abspath, out_path)
    if not os.path.isdir(path):
        os.makedirs(path)
    return os.path.join(path, filename)


def _write_csv_row(f, area, header=False):
    try:
        xy = copy.deepcopy(list(area.get_coord()))
        for geom in xy:
            for poly in geom:
                for c in range(len(poly)):
                    poly[c] = poly[c][::-1]
        attrs = getattr(area, "attrs", {})
        address = attrs.get("address", "")
        cols = [
            {"name": "code", "value": getattr(area, "code")},
            {"name": "area", "value": attrs.get("area_value", "")},
            {"name": "cost", "value": attrs.get("cad_cost", "")},
            {"name": "address", "value": address},
            {"name": "coordinates", "value": xy},
        ]

        if header:
            f.writerow([x["name"] for x in cols])

        f.writerow([x["value"] for x in cols])
    except Exception as er:
        print(er)


def area_csv_output(output, area):
    path = make_output(output, area.file_name, "csv")
    f = csv.writer(open(path, "w+", encoding="utf-8"))
    _write_csv_row(f, area)


def batch_csv_output(output, areas, file_name):
    path = make_output(output, file_name, "csv")
    f = csv.writer(open(path, "w+", encoding="utf-8"))
    for a in range(len(areas)):
        _write_csv_row(f, areas[a], a == 0)
    return path


def batch_json_output(output, areas, file_name, with_attrs=True, crs_name="EPSG:4326"):
    features = []
    feature_collection = {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": crs_name}},
        "features": features,
    }
    path = make_output(output, file_name, "geojson")
    for a in areas:
        feature = a.to_geojson_poly(with_attrs, dumps=False)
        if feature:
            features.append(feature)

    f = open(path, "w", encoding="utf-8")
    f.write(json.dumps(feature_collection))
    f.close()
    return path


def area_json_output(output, area, with_attrs=True):
    geojson = area.to_geojson_poly(with_attrs)
    if geojson:
        f = open(make_output(output, area.file_name, "geojson"), "w")
        f.write(geojson)
        f.close()
    return geojson


def coords2geojson(coords, geom_type, crs_name, attrs=None):
    if attrs is False:
        attrs = {}

    if len(coords):
        features = []
        feature_collection = {"type": "FeatureCollection", "features": features}
        if geom_type.upper() == "POINT":
            for i in range(len(coords)):
                if coords[i]:
                    for j in range(len(coords[i])):
                        xy = coords[i][j]
                        for x, y in xy:
                            point = {
                                "type": "Feature",
                                "properties": {"hole": j > 0},
                                "geometry": {"type": "Point", "coordinates": [x, y]},
                            }
                            features.append(point)
        elif geom_type.upper() == "POLYGON":
            multi_polygon = []
            for fry in range(len(coords)):
                polygon = []
                for j in range(len(coords[fry])):
                    xy = coords[fry][j]
                    # close polygon
                    if xy[-1] != xy[0]:
                        xy.append(xy[0])
                    polygon.append(xy)
                multi_polygon.append(polygon)
            feature = {
                "type": "Feature",
                "properties": attrs,
                "geometry": {"type": "MultiPolygon", "coordinates": multi_polygon},
            }
            feature_collection = feature
        feature_collection["crs"] = {"type": "name", "properties": {"name": crs_name}}
        return feature_collection
    return False


def coords2kml(coords, attrs):
    if len(coords):
        kml = ET.Element("kml", attrib={"xmlns": "http://www.opengis.net/kml/2.2"})
        doc = ET.SubElement(kml, "Document")
        folder = ET.SubElement(doc, "Folder")
        name = attrs["cn"] if "cn" in attrs else attrs["id"]
        ET.SubElement(folder, "name").text = name
        placemark = ET.SubElement(folder, "Placemark")

        style = ET.SubElement(placemark, "Style")

        line_style = ET.SubElement(style, "LineStyle")
        ET.SubElement(line_style, "color").text = "ff0000ff"

        poly_style = ET.SubElement(style, "PolyStyle")
        ET.SubElement(poly_style, "fill").text = "0"

        multi_geometry = ET.SubElement(placemark, "MultiGeometry")

        for i in range(len(coords)):
            polygon = ET.SubElement(multi_geometry, "Polygon")
            for j in range(len(coords[i])):
                if j:
                    # for holes
                    boundary = ET.SubElement(polygon, "innerBoundaryIs")
                else:
                    boundary = ET.SubElement(polygon, "outerBoundaryIs")
                xy = coords[i][j]
                xy.append(xy[0])
                linear_ring = ET.SubElement(boundary, "LinearRing")
                ET.SubElement(linear_ring, "coordinates").text = " ".join(map(lambda c: ",".join(map(str, c)), xy))
        # return ET.tostring(kml, encoding='utf8', method='xml')
        return ET.ElementTree(kml)
    return False
