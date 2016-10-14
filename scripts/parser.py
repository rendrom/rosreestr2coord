# coding: utf-8
from __future__ import print_function, division

import copy
import json
import string
import urllib
import os

from catalog import Catalog
from export import coords2geojson
from utils import xy2lonlat

try:
    import urlparse
    from urllib import urlencode
except ImportError:  # For Python 3
    import urllib.parse as urlparse
    from urllib.parse import urlencode

VERSION = "1.1.3"

##############
# SEARCH URL #
##############
# http://pkk5.rosreestr.ru/api/features/1
#   ?text=38:36:000021:1106
#   &tolerance=4
#   &limit=11
SEARCH_URL = "http://pkk5.rosreestr.ru/api/features/$area_type"

############################
# URL to get area metainfo #
############################
# http://pkk5.rosreestr.ru/api/features/1/38:36:21:1106
FEATURE_INFO_URL = "http://pkk5.rosreestr.ru/api/features/$area_type/"

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
#    set `&format=svg&f=json` to export image in svg !closed by rosreestr, now only PNG
IMAGE_URL = "http://pkk5.rosreestr.ru/arcgis/rest/services/Cadastre/CadastreSelected/MapServer/export"

TYPES = {
    "Участки": 1,
    "ОКС": 5,
    "Кварталы": 2,
    "Районы": 3,
    "Округа": 4,
    "Границы": 7,
    "ЗОУИТ": 10,
    "Тер. зоны": 6,
    "Красные линии": 13,
    "Лес": 12,
    "СРЗУ": 15,
    "ОЭЗ": 16,
    "ГОК": 9,
}


def restore_area(restore, coord_out):
    area = Area(coord_out=coord_out)
    area.restore(restore)
    return area


class Area:
    image_url = IMAGE_URL
    buffer = 10
    save_attrs = ["code", "area_type", "attrs", "image_path", "center", "extent", "image_extent", "width", "height"]

    def __init__(self, code="", area_type=1, epsilon=5, media_path="", with_log=False, catalog="",
                 coord_out="EPSG:3857"):
        self.with_log = with_log
        self.area_type = area_type
        self.media_path = media_path
        self.image_url = ""
        self.xy = []  # [[[area1], [hole1], [holeN]], [[area2]]]
        self.image_xy_corner = []  # cartesian coord from image, for draw plot
        self.width = 0
        self.height = 0
        self.image_path = ""
        self.extent = {}
        self.image_extent = {}
        self.center = {'x': None, 'y': None}
        self.attrs = {}
        self.epsilon = epsilon
        self.code = code
        self.code_id = ""
        self.file_name = self.code.replace(":", "-")

        self.coord_out = coord_out

        t = string.Template(SEARCH_URL)
        self.search_url = t.substitute({"area_type": area_type})
        t = string.Template(FEATURE_INFO_URL)
        self.feature_info_url = t.substitute({"area_type": area_type})

        if not self.media_path:
            # self.media_path = os.path.dirname(os.path.realpath(__file__))
            self.media_path = os.getcwd()
        if not os.path.isdir(self.media_path):
            os.makedirs(self.media_path)
        if catalog:
            self.catalog = Catalog(catalog)
            restore = self.catalog.find(self.code)
            if restore:
                self.restore(restore)
                self.log("%s - restored from %s" % (self.code, catalog))
                return
        if not code:
            return

        feature_info = self.download_feature_info()
        if feature_info:
            formats = ["png"]
            for f in formats:
                self.image_url = self.get_image_url(f)
                if self.image_url:
                    image = self.download_image(f)
                    if image:
                        self.get_geometry()
                        if catalog:
                            self.catalog.update(self)
                            self.catalog.close()
                        break

    def restore(self, restore):
        for a in self.save_attrs:
            setattr(self, a, restore[a])
        if self.coord_out:
            setattr(self, "coord_out", self.coord_out)
        self.get_geometry()
        self.file_name = self.code.replace(":", "-")

    def get_coord(self):
        if self.xy:
            return self.xy
        return []

    def get_attrs(self):
        return self.attrs

    def to_geojson_poly(self, with_attrs=False):
        return self.to_geojson("polygon", with_attrs)

    def to_geojson(self, geom_type="point", with_attrs=False):
        attrs = self.attrs if with_attrs and self.attrs else False
        feature_collection = coords2geojson(self.xy, geom_type, self.coord_out, attrs=attrs)
        if feature_collection:
            return json.dumps(feature_collection)
        return False

    def download_feature_info(self):
        try:
            search_url = self.feature_info_url + self.clear_code(self.code)
            self.log("Start downloading area info: %s" % search_url)
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
                        self.log("Area info downloaded.")
                return feature
        except Exception as error:
            self.log(error)
        return False

    def get_image_url(self, output_format):
        if self.code_id and self.extent:
            ex = self.get_buffer_extent_list()
            dx, dy = map(lambda i: int((ex[i[0]] - ex[i[1]]) * 30), [[2, 0], [3, 1]])
            code = self.clear_code(self.code_id)
            layers = map(str, range(0, 20))
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
            if output_format:
                params["format"] = output_format
            url_parts = list(urlparse.urlparse(IMAGE_URL))
            query = dict(urlparse.parse_qsl(url_parts[4]))
            query.update(params)
            url_parts[4] = urlencode(query)
            meta_url = urlparse.urlunparse(url_parts)
            if meta_url:
                self.log("Start downloading image meta.")
                try:
                    response = urllib.urlopen(meta_url)
                    read = response.read()
                    data = json.loads(read)
                    if data.get("href"):
                        image_url = meta_url.replace("f=json", "f=image")
                        self.width = data["width"]
                        self.height = data["height"]
                        self.image_extent = data["extent"]
                        # self.log(meta_url)
                        self.log("Meta info received.")
                        return image_url
                    else:
                        self.log("Can't get image meta data from: %s" % meta_url)
                except Exception as er:
                    self.log(er)
        elif not self.extent:
            self.log("Can't get image without extent")
        return False

    def download_image(self, output_format="png"):
        try:
            self.log('Start image downloading.')
            image_file = urllib.URLopener()
            basedir = self.media_path
            savedir = os.path.join(basedir, "tmp")
            if not os.path.isdir(savedir):
                os.makedirs(savedir)
            file_path = os.path.join(savedir, "%s.%s" % (self.file_name, output_format))
            image_file.retrieve(self.image_url, file_path)
            self.image_path = file_path
            self.log('Downloading complete.')
            return image_file
        except Exception:
            self.log("Can not upload image.")
        return False

    @staticmethod
    def clear_code(code):
        """remove first nulls from code  xxxx:00xx >> xxxx:xx"""
        return ":".join(map(lambda x: str(int(x)), code.split(":")))

    @staticmethod
    def get_extent_list(extent):
        """convert extent dick to ordered array"""
        return [extent["xmin"], extent["ymin"], extent["xmax"], extent["ymax"]]

    def get_buffer_extent_list(self):
        """add some buffer to ordered extent array"""
        ex = self.extent
        buf = self.buffer
        ex = [ex["xmin"] - buf, ex["ymin"] - buf, ex["xmax"] + buf, ex["ymax"] + buf]
        return ex

    def get_geometry(self):
        """
        get corner geometry array from downloaded image
        [area1],[area2] - may be multipolygon geometry
           |
        [self],[hole_1],[hole_N]     - holes is optional
           |
        [coord1],[coord2],[coord3]   - min 3 coord for polygon
           |
         [x,y]                       - coordinate pair

         Example:
             [[ [ [x,y],[x,y],[x,y] ], [ [x,y],[x,y],[x,y] ], ], [ [x,y],[x,y],[x,y] ], [ [x,y],[x,y],[x,y] ] ]
                -----------------first polygon-----------------  ----------------second polygon--------------
                ----outer contour---   --first hole contour-
        """
        image_xy_corner = self.image_xy_corner = self.get_image_xy_corner()
        self.xy = copy.deepcopy(image_xy_corner)
        for geom in self.xy:
            for p in range(len(geom)):
                geom[p] = self.image_corners_to_coord(geom[p])
        return self.xy

    def get_image_xy_corner(self):
        """get сartesian coordinates from raster"""
        import cv2

        image_xy_corners = []
        img = cv2.imread(self.image_path, cv2.IMREAD_GRAYSCALE)
        imagem = (255 - img)

        try:
            ret, thresh = cv2.threshold(imagem, 10, 128, cv2.THRESH_BINARY)
            try:
                contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            except Exception:
                im2, contours, hierarchy = cv2.findContours(thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

            hierarchy = hierarchy[0]
            hierarhy_contours = [[] for _ in range(len(hierarchy))]
            for fry in range(len(contours)):
                currentContour = contours[fry]
                currentHierarchy = hierarchy[fry]
                cc = []
                # epsilon = 0.0005 * cv2.arcLength(contours[len(contours) - 1], True)
                approx = cv2.approxPolyDP(currentContour, self.epsilon, True)
                if len(approx) > 2:
                    for c in approx:
                        cc.append([c[0][0], c[0][1]])
                    parent_index = currentHierarchy[3]
                    index = fry if parent_index < 0 else parent_index
                    hierarhy_contours[index].append(cc)

            image_xy_corners = [c for c in hierarhy_contours if len(c) > 0]

            return image_xy_corners
        except Exception as ex:
            self.log(ex)
        return image_xy_corners

    def image_corners_to_coord(self, image_xy_corners):
        """calculate spatial coordinates from cartesian"""
        ex = self.get_extent_list(self.image_extent)
        dx = ((ex[2] - ex[0]) / self.width)
        dy = ((ex[3] - ex[1]) / self.height)
        xy_corners = []
        for im_x, im_y in image_xy_corners:
            x = ex[0] + (im_x * dx)
            y = ex[3] - (im_y * dy)
            if self.coord_out == "EPSG:4326":
                (x, y) = xy2lonlat(x, y)
            xy_corners.append([x, y])
        return xy_corners

    def show_plot(self):
        """Development tool"""
        import cv2
        try:
            from matplotlib import pyplot as plt
        except ImportError:
            raise ImportError('Matplotlib is not installed.')

        img = cv2.imread(self.image_path)
        for corners in self.image_xy_corner:
            for x, y in corners:
                cv2.circle(img, (x, y), 3, 255, -1)
        plt.imshow(img), plt.show()

    def log(self, msg):
        if self.with_log:
            print(msg)
