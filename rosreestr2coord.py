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

FEATURE_INFO_URL = "http://pkk5.rosreestr.ru/api/features/1/"

############################
# URL to get area metainfo #
############################
# http://pkk5.rosreestr.ru/api/features/1/38:36:21:1106
META_URL = "http://pkk5.rosreestr.ru/api/features/1/"

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
    meta_url = META_URL
    image_url = IMAGE_URL
    buffer = 10

    def __init__(self, code, media_path=""):
        self.media_path = media_path
        self.image_url = ""
        self.xy = []
        self.holes = []
        self.width = 0
        self.height = 0
        self.image_path = ""
        self.extent = {}
        self.image_extent = {}
        self.center = {}
        self.attrs = {}
        if not self.media_path:
            self.media_path = os.path.dirname(os.path.realpath(__file__))
        if not os.path.isdir(self.media_path):
            os.makedirs(self.media_path)
        self.code = code
        self.code_id = ""
        self.file_name = self.code.replace(":", "-")
        # search_data = self.search()
        feature_info = self.download_feature_info()
        self.download_meta()
        if feature_info:
            formats = ["svg", "png"]
            for f in formats:            
                self.image_url = self.get_image_url(f)
                if self.image_url:                  
                    image = self.download_image(f)
                    if image:
                        geom = self.get_geometry(f);
                        break
                        
    def get_coord(self):
        if self.xy:
            return self.xy[0]
        return []            
        
    def get_holes(self):
        holes = []
        for fry in range(len(self.xy)):
            if fry != 0:
                holes.append(self.xy[fry])
        return holes

    def get_attrs(self):
        return self.attrs
        
    def to_geojson_poly(self):
        return self.to_geojson("polygon")

    def to_geojson(self, type="point"):
        if self.xy:
            features = []
            feature_collection = {
                "type": "FeatureCollection",
                "crs": {"type": "name", "properties": {"name": "EPSG:3857"}},
                "features": features
            }
            if type.upper() == "POINT":
                for i in range(self.xy):
                    xy = self.xy[i]
                    for x, y in xy:
                        point = {"type": "Feature", "properties": {"hole": i > 0 }, "geometry": {"type": "Point", "coordinates": [x, y]}}
                        features.append(point)
            elif type.upper() == "POLYGON":
                feature = {"type": "Feature", "properties": {}}
                feature["geometry"] = {"type": "Polygon", "coordinates": self.xy}
                features.append(feature)
            return json.dumps(feature_collection)
        return False

    def get_image_url(self, format):
        if self.code_id and self.extent:
            ex = self.get_buffer_extent_list()
            dx, dy = map(lambda i: int((ex[i[0]] - ex[i[1]]) * 5), [[2, 0], [3, 1]])
            code = self.code_id
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
                        image_url = data["href"]
                        self.width = data["width"]
                        self.height = data["height"]
                        self.image_extent = data["extent"]
                        # print(image_url)
                        return image_url
                    else:
                        print("can't get image data from: %s" %meta_url) 
                except Exception as er:
                    print(er)
        elif not self.extent:
            print("can't get image without extent")
        return False

    def download_image(self, format="png"):
        try:
            image_file = urllib.URLopener()
            basedir = self.media_path
            savedir = os.path.join(basedir, "tmp")
            if not os.path.isdir(savedir):
                os.makedirs(savedir)
            file_path = os.path.join(savedir, "%s.%s" % (self.file_name, format))
            image_file.retrieve(self.image_url, file_path)
            self.image_path = file_path
            return image_file
        except Exception:
            print("Nothing found")
        return False

    def get_meta_url(self):
        if self.code_id:
            # url = urlparse.urljoin(self.meta_url, self.code_id)
            url = self.meta_url + str(self.code_id)
            return url
        return ""

    def download_meta(self):
        url = self.get_meta_url()
        if url:
            search_url = url
            response = urllib.urlopen(search_url)
            data = json.loads(response.read())
            if data["feature"] and data["feature"]["attrs"]:
                self.attrs = data["feature"]["attrs"]
                return self.attrs
        return False



    @staticmethod
    def get_extent_list(extent):
        return [extent["xmin"], extent["ymin"], extent["xmax"], extent["ymax"]]

    def get_buffer_extent_list(self):
        ex = self.extent
        buf = self.buffer
        ex = [ex["xmin"] - buf, ex["ymin"] - buf, ex["xmax"] + buf, ex["ymax"] + buf]
        return ex

    def search(self):
        try:
            search_data = self.download_search_result()
            if search_data:
                features = search_data["features"]
                if features and len(features):
                    area = features[0]
                    attrs = area["attrs"]
                    if attrs["cn"] == self.code:
                        self.attrs["address"] = attrs["address"]
                        self.code_id = attrs["id"]
                        if area.get("extent"):
                            self.extent = area["extent"]
                        if area.get("center"):
                            self.center = area["center"]
                        return search_data
        except Exception as er:
            pass
        print("Nothing found")
        return False

    def download_search_result(self):
        search_url = SEARCH_URL + "?text=%s&tolerance=4&limit=1" % self.code
        response = urllib.urlopen(search_url)
        data = json.loads(response.read())
        return data
        
    def download_feature_info(self):
        try:
            search_url = FEATURE_INFO_URL + self.clear_code(self.code)
            response = urllib.urlopen(search_url)
            resp = response.read()
            data = json.loads(resp)
            if data:
                feature = data.get("feature")
                if feature:
                    self.code_id = feature["_id"]
                    if feature.get("attrs"):
                        self.attrs = feature["attrs"]
                        self.code_id = feature["attrs"]["cn"]
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
        '''remove first nulls from code'''
        return ":".join(map(lambda x: str(int(x)), code.split(":")))
    

    def get_geometry(self, format):
        if format == "svg":
            self.xy = self.read_svg()
        else:
            image_xy_corner = self.get_image_xy_corner()
            if image_xy_corner:
                self.xy.append(self.image_corners_to_coord(image_xy_corner))
        return self.xy

    def read_svg(self):
        import svg

        svg_coord = [] # Set of poly coordinates set (area, hole1?, hole2?...)
        obj = svg.parse(self.image_path)
        self.get_svg_points(obj, svg_coord)
        for poly in range(len(svg_coord)):
            xy = self.image_corners_to_coord(svg_coord[poly])
            self.xy.append(xy)
        return self.xy

    def get_svg_points(self, obj, svg_coord):
        '''get absolute coordinates from svg file'''
        if obj.__dict__.has_key("items"):
            for i in obj.items:
                dest = i.__dict__.has_key("dest")
                if dest:
                    svg_coord.append([])
                if i.__dict__.has_key("start"):
                    svg_coord[len(svg_coord)-1].append([i.start.x, i.start.y])
                else:
                    self.get_svg_points(i, svg_coord)
        else:
            pass

    def get_image_xy_corner(self):
        '''get coodinates from raster'''
        import numpy as np
        import cv2

        image_xy_corners = []
        img = cv2.imread(self.image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # gray = cv2.medianBlur(gray,5)
        try:
            corners = cv2.goodFeaturesToTrack(gray, 100, 0.01, 1, useHarrisDetector=True)
            corners = np.int0(corners)
            for i in corners:
                x, y = i.ravel()
                image_xy_corners.append([x, y])
            return image_xy_corners
        except Exception as ex:
            print(ex)
        return image_xy_corners

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

    def show_plot(self, image_xy_corner):
        import cv2
        from matplotlib import pyplot as plt
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
    opts = parser.parse_args()

    return opts


if __name__ == "__main__":
    
    # area = Area("38:36:000021:1106")  
    # area = Area("38:06:144003:4723")
    # area = Area("38:36:000033:375")
    # code, output, path = "38:06:144003:4137", "", ""
    opt = getopts() 
    path = opt.path
    code = opt.code
    output = opt.output if opt.output else "."
    abspath = os.path.abspath(output)
    if code:
        area = Area(code, media_path=path)
        geojson = area.to_geojson_poly()
        if geojson:
            filename = '%s.geojson' % area.file_name
            file_path = os.path.join(abspath, filename)
            f = open(file_path, 'w')
            f.write(geojson)
            f.close()
            print(file_path)
