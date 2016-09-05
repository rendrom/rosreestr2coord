# coding: utf-8
from __future__ import print_function, division
import json
import urllib
import os

try:
    import urlparse
    from urllib import urlencode
except ImportError:  # For Python 3
    import urllib.parse as urlparse
    from urllib.parse import urlencode

##############
# SEARCH URL #
##############
# http://pkk5.rosreestr.ru/api/features/1
#   ?text=38:36:000021:1106
#   &tolerance=4
#   &limit=11
SEARCH_URL = "http://pkk5.rosreestr.ru/api/features/1"

############################
# URL to get area metainfo #
############################
# http://pkk5.rosreestr.ru/api/features/1/38:36:21:1106
FEATURE_INFO_URL = "http://pkk5.rosreestr.ru/api/features/1/"

#########################
# URL to get area image #
#########################
# http://pkk5.rosreestr.ru/arcgis/rest/services/Cadastre/CadastreSelected/MapServer/export
#   ?dpi=96
#   &transparent=true
#   &format=png32
#   &layers=show%3A6%2C7
#   &bbox=11612029.005008286%2C6849457.6834302815%2C11612888.921576614%2C6849789.706771941
#   &bboxSR=102100
#   &imageSR=102100
#   &size=1440%2C556
#   &layerDefs=%7B%226%22%3A%22ID%20%3D%20%2738%3A36%3A21%3A1106%27%22%2C%227%22%3A%22ID%20%3D%20%2738%3A36%3A21%3A1106%27%22%7D
#   &f=image
# WHERE:
#    "layerDefs" decode to {"6":"ID = '38:36:21:1106'","7":"ID = '38:36:21:1106'"}
#    "f" may be `json` or `html`
#    set `&format=svg&f=json` to export image in svg 
IMAGE_URL = "http://pkk5.rosreestr.ru/arcgis/rest/services/Cadastre/CadastreSelected/MapServer/export"


class Area:
    search_url = SEARCH_URL
    feature_info_url = FEATURE_INFO_URL
    image_url = IMAGE_URL
    buffer = 10

    def __init__(self, code="", epsilon=5, media_path=""):
        if not code:
            raise ValueError('`code` is required')
        self.media_path = media_path
        self.image_url = ""
        self.xy = []  # [[[area1], [hole1], [holeN]], [[area2]]]
        self.width = 0
        self.height = 0
        self.image_path = ""
        self.extent = {}
        self.image_extent = {}
        self.center = {}
        self.attrs = {}
        self.epsilon = epsilon
        self.code = code
        self.code_id = ""
        self.file_name = self.code.replace(":", "-")

        if not self.media_path:
            # self.media_path = os.path.dirname(os.path.realpath(__file__))
            self.media_path = os.getcwd()
        if not os.path.isdir(self.media_path):
            os.makedirs(self.media_path)

        feature_info = self.download_feature_info()
        if feature_info:
            formats = ["png"]  # ["svg", "png"]
            for f in formats:
                self.image_url = self.get_image_url(f)
                if self.image_url:
                    image = self.download_image(f)
                    if image:
                        self.get_geometry(f)
                        break

    def get_coord(self):
        if self.xy:
            return self.xy
        return []


    def get_attrs(self):
        return self.attrs

    def to_geojson_poly(self):
        return self.to_geojson("polygon")

    def _to_geojson(self, type):
        if self.xy:
            features = []
            feature_collection = {
                "type": "FeatureCollection",
                "crs": {"type": "name", "properties": {"name": "EPSG:3857"}},
                "features": features
            }
            if type.upper() == "POINT":
                for i in range(len(self.xy)):
                    for j in range(len(self.xy[i])):
                        xy = self.xy[i][j]
                        for x, y in xy:
                            point = {"type": "Feature",
                                     "properties": {"hole": j > 0},
                                     "geometry": {"type": "Point", "coordinates": [x, y]}}
                            features.append(point)
            elif type.upper() == "POLYGON":
                close_xy = []
                multi_polygon = []
                for fry in range(len(self.xy)):
                    for j in range(len(self.xy[fry])):
                        xy = self.xy[fry][j]
                        xy.append(xy[0])
                        close_xy.append(xy)
                    multi_polygon.append(close_xy)
                feature = {"type": "Feature",
                           "properties": {},
                           "geometry": {"type": "MultiPolygon", "coordinates": multi_polygon}}
                features.append(feature)
            return feature_collection
        return False

    def to_geojson(self, type="point"):
        feature_collection = self._to_geojson(type)
        if feature_collection:
            return json.dumps(feature_collection)
        return False

    def get_image_url(self, format):
        if self.code_id and self.extent:
            ex = self.get_buffer_extent_list()
            dx, dy = map(lambda i: int((ex[i[0]] - ex[i[1]]) * 5), [[2, 0], [3, 1]])
            code = self.clear_code(self.code_id)
            layers = ["6", "7"]
            params = {
                "dpi": 96,
                "transparent": "false",
                "format": "png",
                "layers": "show:%s" % ",".join(layers),
                "bbox": ",".join(map(str, ex)),
                "bboxSR": 102100,
                "imageSR": 102100,
                "size": "%s,%s" % (dx, dy),
                "layerDefs": {layer: str("ID = '%s'" % code) for layer in layers},
                "f": "json"
            }
            if format:
                params["format"] = format
            url_parts = list(urlparse.urlparse(IMAGE_URL))
            query = dict(urlparse.parse_qsl(url_parts[4]))
            query.update(params)
            url_parts[4] = urlencode(query)
            meta_url = urlparse.urlunparse(url_parts)
            if meta_url:
                response = urllib.urlopen(meta_url)
                try:
                    read = response.read()
                    data = json.loads(read)
                    if data.get("href"):
                        image_url = meta_url.replace("f=json", "f=image")  # data["href"]
                        self.width = data["width"]
                        self.height = data["height"]
                        self.image_extent = data["extent"]
                        # print(meta_url)
                        return image_url
                    else:
                        print("Can't get image data from: %s" % meta_url)
                except Exception as er:
                    print(er)
        elif not self.extent:
            print("Can't get image without extent")
        return False

    def download_image(self, format="png"):
        try:
            print('Start image downloading')
            image_file = urllib.URLopener()
            basedir = self.media_path
            savedir = os.path.join(basedir, "tmp")
            if not os.path.isdir(savedir):
                os.makedirs(savedir)
            file_path = os.path.join(savedir, "%s.%s" % (self.file_name, format))
            image_file.retrieve(self.image_url, file_path)
            self.image_path = file_path
            print('Downloading complete')
            return image_file
        except Exception:
            print("Can not upload image")
        return False

    @staticmethod
    def get_extent_list(extent):
        return [extent["xmin"], extent["ymin"], extent["xmax"], extent["ymax"]]

    def get_buffer_extent_list(self):
        ex = self.extent
        buf = self.buffer
        ex = [ex["xmin"] - buf, ex["ymin"] - buf, ex["xmax"] + buf, ex["ymax"] + buf]
        return ex

    # def search(self):
    #     try:
    #         search_data = self.download_search_result()
    #         if search_data:
    #             features = search_data["features"]
    #             if features and len(features):
    #                 area = features[0]
    #                 attrs = area["attrs"]
    #                 if attrs["cn"] == self.code:
    #                     self.attrs["address"] = attrs["address"]
    #                     self.code_id = attrs["id"]
    #                     if area.get("extent"):
    #                         self.extent = area["extent"]
    #                     if area.get("center"):
    #                         self.center = area["center"]
    #                     return search_data
    #     except Exception as er:
    #         pass
    #     print("Nothing found")
    #     return False
    #
    # def download_search_result(self):
    #     search_url = SEARCH_URL + "?text=%s&tolerance=4&limit=1" % self.code
    #     response = urllib.urlopen(search_url)
    #     data = json.loads(response.read())
    #     return data

    def download_feature_info(self):
        try:
            search_url = FEATURE_INFO_URL + self.clear_code(self.code)
            response = urllib.urlopen(search_url)
            resp = response.read()
            data = json.loads(resp)
            if data:
                feature = data.get("feature")
                if feature:
                    if feature.get("attrs"):
                        self.attrs = feature["attrs"]
                        self.code_id = feature["attrs"]["id"]
                    if feature.get("extent"):
                        self.extent = feature["extent"]
                    if feature.get("center"):
                        self.center = feature["center"]
                return feature
        except Exception as error:
            print(error)
        return False

    @staticmethod
    def clear_code(code):
        """remove first nulls from code"""
        return ":".join(map(lambda x: str(int(x)), code.split(":")))

    def get_geometry(self, format):
        if format == "svg":
            self.xy = [self.read_svg()]
        else:
            image_xy_corner = self.get_image_xy_corner()
            if image_xy_corner:
                for i in range(len(image_xy_corner)):
                    # TODO: make multipolygon
                    xy = [self.image_corners_to_coord(image_xy_corner[i])]
                    self.xy.append(xy)
        return self.xy

    def read_svg(self):
        import svg

        svg_coord = []  # Set of poly coordinates set (area, hole1?, hole2?...)
        obj = svg.parse(self.image_path)
        self.get_svg_points(obj, svg_coord)
        for poly in range(len(svg_coord)):
            xy = self.image_corners_to_coord(svg_coord[poly])
            self.xy.append(xy)
        return self.xy

    def get_svg_points(self, obj, svg_coord):
        """get absolute coordinates from svg file"""
        if "items" in obj:
            for i in obj.items:
                dest = "dest" in i
                if dest:
                    svg_coord.append([])
                if "start" in i:
                    svg_coord[len(svg_coord) - 1].append([i.start.x, i.start.y])
                else:
                    self.get_svg_points(i, svg_coord)
        else:
            pass

    def get_image_xy_corner(self):
        """get coordinates from raster"""
        import numpy as np
        import cv2

        image_xy_corners = []
        img = cv2.imread(self.image_path, cv2.IMREAD_GRAYSCALE)
        imagem = (255 - img)

        try:
            ret, thresh = cv2.threshold(imagem, 10, 128, cv2.THRESH_BINARY)
            # epsilon = 0.0005*cv2.arcLength(contours[len(contours) - 1], True)
            try:
                contours, hierarchy = cv2.findContours(thresh, 1, 2)
            except:
                im2, contours, hierarchy = cv2.findContours(thresh, 1, 2)
            for i in range(len(contours) - 1, -1, -1):
                cc = []
                cnt = contours[i]
                approx = cv2.approxPolyDP(cnt, self.epsilon, True)
                for c in approx:
                    cc.append([c[0][0], c[0][1]])
                image_xy_corners.append(cc)
            return image_xy_corners
        except Exception as ex:
            print(ex)
        return image_xy_corners

    @staticmethod
    def calculate_gzn(from_xy, to_xy):
        from math import pi, atan
        c = 1e-7
        y1 = from_xy[0]
        x1 = from_xy[1]
        y2 = to_xy[0]
        x2 = to_xy[1]
        x = x2 - x1
        y = y2 - y1

        def sgn(i):
            s = 0
            if i > 0:
                s = 1
            elif i < 0:
                s = -1
            return s

        gzn = pi - pi * sgn(sgn(x) + 1) * sgn(y) + atan(y / (x + c))
        return gzn

    def image_corners_to_coord(self, image_xy_corners):
        ex = self.get_extent_list(self.image_extent)
        dx = ((ex[2] - ex[0]) / self.width)
        dy = ((ex[3] - ex[1]) / self.height)
        xy_corners = []
        for im_x, im_y in image_xy_corners:
            x = ex[0] + (im_x * dx)
            y = ex[3] - (im_y * dy)
            xy_corners.append([x, y])
        return xy_corners

    def show_plot(self, image_xy_corners):
        import cv2
        try:
            from matplotlib import pyplot as plt
        except ImportError:
            raise ImportError('Matplotlib is not installed.')

        corners = image_xy_corners
        img = cv2.imread(self.image_path)
        for x, y in corners:
            cv2.circle(img, (x, y), 3, 255, -1)
        plt.imshow(img), plt.show()


def getopts():
    import argparse
    import textwrap

    """
    Get the command line options.
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""\
        Get geojson with coordinates of area by cadastral number.
        http://pkk5.rosreestr.ru/
        """)
    )
    parser.add_argument('-c', '--code', action='store', type=str, required=True,
                        help='area cadastral number')
    parser.add_argument('-p', '--path', action='store', type=str, required=False,
                        help='media path')
    parser.add_argument('-o', '--output', action='store', type=str, required=False,
                        help='output path')
    parser.add_argument('-e', '--epsilon', action='store', type=int, required=False,
                        help='Parameter specifying the approximation accuracy. '
                             'This is the maximum distance between the original curve and its approximation.')
    opts = parser.parse_args()

    return opts


def main():
    # area = Area("38:36:000021:1106")
    # area = Area("38:06:144003:4723")
    # area = Area("38:36:000033:375")
    # code, output, path = "38:06:144003:4137", "", ""
    opt = getopts()
    path = opt.path
    epsilon = opt.epsilon if opt.epsilon else 5
    code = opt.code
    output = opt.output if opt.output else "."
    abspath = os.path.abspath(output)
    if code:
        area = Area(code, media_path=path, epsilon=epsilon)
        geojson = area.to_geojson_poly()
        if geojson:
            filename = '%s.geojson' % area.file_name
            file_path = os.path.join(abspath, filename)
            f = open(file_path, 'w')
            f.write(geojson)
            f.close()
            print(file_path)


if __name__ == "__main__":
    main()
