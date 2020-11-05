# coding: utf-8

import copy
import json
import os
import re
import string

from rosreestr2coord.merge_tiles import PkkAreaMerger
from .export import coords2geojson
from .logger import logger
from .utils import xy2lonlat, make_request, TimeoutException
from rosreestr2coord.export import coords2kml

try:
    import urllib.parse
    from urllib.parse import urlencode
except ImportError:  # For Python 3
    import urllib.parse as urlparse
    from urllib.parse import urlencode

##############
# SEARCH URL #
##############
# https://pkk.rosreestr.ru/api/features/1
#   ?text=38:36:000021:1106
#   &tolerance=4
#   &limit=11
SEARCH_URL = 'https://pkk.rosreestr.ru/api/features/$area_type'

############################
# URL to get area metainfo #
############################
# https://pkk.rosreestr.ru/api/features/1/38:36:21:1106
FEATURE_INFO_URL = 'https://pkk.rosreestr.ru/api/features/$area_type/'

#########################
# URL to get area image #
#########################
# https://pkk.rosreestr.ru/arcgis/rest/services/PKK6/CadastreSelected/MapServer/export
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
#    'layerDefs' decode to {'6':'ID = '38:36:21:1106'','7':'ID = '38:36:21:1106''}
#    'f' may be `json` or `html`
#    set `&format=svg&f=json` to export image in svg !closed by rosreestr, now only PNG

TYPES = {
    'Участки': 1,
    'ОКС': 5,
    'Кварталы': 2,
    'Районы': 3,
    'Округа': 4,
    'Границы': 7,
    'ЗОУИТ': 10,
    'Тер. зоны': 6,
    'Красные линии': 13,
    'Лес': 12,
    'СРЗУ': 15,
    'ОЭЗ': 16,
    'ГОК': 9,
}


class NoCoordinatesException(Exception):
    pass


class Area:

    code = ''
    code_id = ''  # from feature info attr id
    buffer = 10
    xy = []  # [[[area1], [hole1], [holeN]], [[area2]]]
    image_xy_corner = []  # cartesian coord from image, for draw plot
    width = 0
    height = 0
    image_path = ''
    extent = {}
    image_extent = {}
    center = {'x': None, 'y': None}
    attrs = {}

    def __init__(self,
                 code='',
                 area_type=1,
                 epsilon=5,
                 media_path='',
                 with_log=True,
                 coord_out='EPSG:4326',
                 center_only=False,
                 with_proxy=False,
                 use_cache=True
                 ):
        """
        Initialize a new featureinfo object.

        Args:
            self: (todo): write your description
            code: (int): write your description
            area_type: (str): write your description
            epsilon: (float): write your description
            media_path: (str): write your description
            with_log: (todo): write your description
            coord_out: (str): write your description
            center_only: (bool): write your description
            with_proxy: (str): write your description
            use_cache: (bool): write your description
        """
        self.with_log = with_log
        self.area_type = area_type
        self.media_path = media_path
        self.center_only = center_only
        self.epsilon = epsilon
        self.code = code

        self.file_name = self.code[:].replace(':', '_')
        self.with_proxy = with_proxy
        self.use_cache = use_cache
        self.coord_out = coord_out

        t = string.Template(SEARCH_URL)
        self.search_url = t.substitute({'area_type': area_type})
        t = string.Template(FEATURE_INFO_URL)
        self.feature_info_url = t.substitute({'area_type': area_type})
        if not code:
            return
        self.workspace = self.create_workspace()
        feature_info = self.download_feature_info()
        if feature_info:
            self.get_geometry()
        else:
            self.log('Nothing found')

    def create_workspace(self):
        """
        Create the workspace.

        Args:
            self: (todo): write your description
        """
        if not self.media_path:
            self.media_path = os.getcwd()
        area_path_name = self.clear_code(self.code).replace(':', '_')
        workspace = os.path.join(
            self.media_path, 'tmp', area_path_name)
        if not os.path.isdir(workspace):
            os.makedirs(workspace)
        return workspace

    def get_coord(self):
        """
        Get coordinates : class : class

        Args:
            self: (todo): write your description
        """
        if self.xy:
            return self.xy
        center = self.get_center_xy()
        if center:
            return center
        return []

    def get_attrs(self):
        """
        Return the : attrs. attrs

        Args:
            self: (todo): write your description
        """
        return self.attrs

    def _prepare_attrs(self):
        """
        Prepare the attrs. attrs.

        Args:
            self: (todo): write your description
        """
        if self.attrs:
            for a in self.attrs:
                attr = self.attrs[a]
                if isinstance(attr, str):
                    try:
                        attr = attr.strip()
                        self.attrs[a] = attr
                    except Exception:
                        pass
        return self.attrs

    def to_geojson_poly(self, with_attrs=True, dumps=True):
        """
        Convert a geojson representation of this object as polygon object to a geojson.

        Args:
            self: (todo): write your description
            with_attrs: (bool): write your description
            dumps: (todo): write your description
        """
        return self.to_geojson('polygon', with_attrs, dumps)

    def to_geojson_center(self, with_attrs=True, dumps=True):
        """
        Return a geojson representation of the geojson.

        Args:
            self: (todo): write your description
            with_attrs: (todo): write your description
            dumps: (todo): write your description
        """
        current_center_status = self.center_only
        self.center_only = True
        to_return = self.to_geojson('point', with_attrs, dumps)
        self.center_only = current_center_status
        return to_return

    def to_geojson(self, geom_type='point', with_attrs=True, dumps=True):
        """
        Return a geojson representation of a geojson feature.

        Args:
            self: (todo): write your description
            geom_type: (str): write your description
            with_attrs: (bool): write your description
            dumps: (todo): write your description
        """
        attrs = False
        if with_attrs:
            attrs = self._prepare_attrs()
        xy = []
        if self.center_only:
            xy = self.get_center_xy()
            geom_type = 'point'
        else:
            xy = self.xy
        if xy and len(xy):
            feature_collection = coords2geojson(
                xy, geom_type, self.coord_out, attrs=attrs)
            if feature_collection:
                if dumps:
                    return json.dumps(feature_collection)
                return feature_collection
        return False

    def to_kml(self):
        """
        Converts the kml coordinates to a kml coordinates.

        Args:
            self: (todo): write your description
        """
        return coords2kml(self.xy, self._prepare_attrs())

    def get_center_xy(self):
        """
        Get the center of the image

        Args:
            self: (todo): write your description
        """
        center = self.attrs.get('center')
        if center:
            xy = [[[[center['x'], center['y']]]]]
            return xy
        return False

    def make_request(self, url):
        """
        Make a request.

        Args:
            self: (todo): write your description
            url: (str): write your description
        """
        response = make_request(url, self.with_proxy)
        return response

    def download_feature_info(self):
        """
        Download feature information

        Args:
            self: (todo): write your description
        """
        feature_info_path = os.path.join(self.workspace, 'feature_info.json')
        data = False
        if self.use_cache:
            try:
                with open(feature_info_path, 'r') as data_file:
                    data = json.loads(data_file.read())
            except Exception:
                pass
        try:
            if not data:
                search_url = self.feature_info_url + self.clear_code(self.code)
                self.log('Start downloading area info: %s' % search_url)
                resp = self.make_request(search_url)
                data = json.loads(resp)
                self.log('Area info downloaded.')
                with open(feature_info_path, 'w') as outfile:
                    json.dump(data, outfile)
            else:
                self.log(
                    'Area info loaded from file: {}'.format(feature_info_path))
            if data:
                feature = data.get('feature')
                if feature:
                    attrs = feature.get('attrs')
                    if attrs:
                        self.attrs = attrs
                        self.code_id = attrs['id']
                    if feature.get('extent'):
                        self.extent = feature['extent']
                    if feature.get('center'):
                        x = feature['center']['x']
                        y = feature['center']['y']
                        if self.coord_out == 'EPSG:4326':
                            (x, y) = xy2lonlat(x, y)
                        self.center = {'x': x, 'y': y}
                        self.attrs['center'] = self.center
                return feature
        except TimeoutException:
            raise TimeoutException()
        except Exception as error:
            self.error(error)
        return False

    @staticmethod
    def clear_code(code):
        '''remove first nulls from code  xxxx:00xx >> xxxx:xx'''
        if re.match(r'^\d+(\:\d+)', code):
            return ':'.join([str(int(x)) for x in code.split(':')])
        return code

    @staticmethod
    def get_extent_list(extent):
        '''convert extent dick to ordered array'''
        return [extent['xmin'], extent['ymin'], extent['xmax'], extent['ymax']]

    def get_buffer_extent_list(self):
        '''add some buffer to ordered extent array'''
        ex = self.extent
        buf = self.buffer
        if ex and ex['xmin']:
            ex = [ex['xmin'] - buf, ex['ymin'] - buf,
                  ex['xmax'] + buf, ex['ymax'] + buf]
        else:
            self.log('Area has no coordinates')
            # raise NoCoordinatesException()
        return ex

    def get_geometry(self):
        """
        Get the center of the image

        Args:
            self: (todo): write your description
        """
        if self.center_only:
            return self.get_center_xy()
        else:
            return self.parse_geometry_from_image()

    def parse_geometry_from_image(self):
        """
        Parse image geometry.

        Args:
            self: (todo): write your description
        """
        formats = ['png']

        for f in formats:
            bbox = self.get_buffer_extent_list()
            if bbox:
                image = PkkAreaMerger(bbox=self.get_buffer_extent_list(),
                                      output_format=f, with_log=self.with_log,
                                      clear_code=self.clear_code(self.code_id),
                                      output_dir=self.workspace,
                                      requester=self.make_request,
                                      use_cache=self.use_cache,
                                      area_type=self.area_type
                                      )
                image.download()
                self.image_path = image.merge_tiles()
                self.width = image.real_width
                self.height = image.real_height
                self.image_extent = image.image_extent

                if image:
                    return self.get_image_geometry()

    def get_image_geometry(self):
        '''
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
        '''
        image_xy_corner = self.image_xy_corner = self.get_image_xy_corner()
        if image_xy_corner:
            self.xy = copy.deepcopy(image_xy_corner)
            for geom in self.xy:
                for p in range(len(geom)):
                    geom[p] = self.image_corners_to_coord(geom[p])
            return self.xy
        return []

    def get_image_xy_corner(self):
        '''get сartesian coordinates from raster'''
        import cv2
        import numpy

        if not self.image_path:
            return False
        image_xy_corners = []

        try:
            # img = cv2.imread(self.image_path, cv2.IMREAD_GRAYSCALE)
            stream = open(self.image_path, "rb")
            bytes = bytearray(stream.read())
            numpyarray = numpy.asarray(bytes, dtype=numpy.uint8)
            img = cv2.imdecode(numpyarray, cv2.IMREAD_GRAYSCALE)
            imagem = (255 - img)
            ret, thresh = cv2.threshold(imagem, 10, 128, cv2.THRESH_BINARY)
            try:
                contours, hierarchy = cv2.findContours(
                    thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            except Exception:
                im2, contours, hierarchy = cv2.findContours(
                    thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

            hierarchy = hierarchy[0]
            hierarchy_contours = [[] for _ in range(len(hierarchy))]
            for fry in range(len(contours)):
                currentContour = contours[fry]
                currentHierarchy = hierarchy[fry]
                cc = []

                perimeter = cv2.arcLength(currentContour, True)
                # epsilon = 0.001 * cv2.arcLength(currentContour, True)
                # epsilon = epsilon * self.epsilon
                epsilon = self.epsilon
                approx = cv2.approxPolyDP(currentContour, epsilon, True)
                if len(approx) > 2:
                    for c in approx:
                        cc.append([c[0][0], c[0][1]])
                    parent_index = currentHierarchy[3]
                    index = fry if parent_index < 0 else parent_index
                    hierarchy_contours[index].append(cc)

            image_xy_corners = [c for c in hierarchy_contours if len(c) > 0]
            return image_xy_corners
        except Exception as ex:
            self.error(ex)
        return image_xy_corners

    def image_corners_to_coord(self, image_xy_corners):
        '''calculate spatial coordinates from cartesian'''
        ex = self.get_extent_list(self.image_extent)
        dx = ((ex[2] - ex[0]) / self.width)
        dy = ((ex[3] - ex[1]) / self.height)
        xy_corners = []
        for im_x, im_y in image_xy_corners:
            x = ex[0] + (im_x * dx)
            y = ex[3] - (im_y * dy)
            if self.coord_out == 'EPSG:4326':
                (x, y) = xy2lonlat(x, y)
            xy_corners.append([x, y])
        return xy_corners

    def show_plot(self):
        '''Development tool'''
        import cv2
        try:
            from matplotlib import pyplot as plt
        except ImportError:
            self.error('Matplotlib is not installed.')
            raise ImportError('Matplotlib is not installed.')

        img = cv2.imread(self.image_path)
        for polygones in self.image_xy_corner:
            for corners in polygones:
                for x, y in corners:
                    cv2.circle(img, (x, y), 3, 255, -1)
        plt.imshow(img), plt.show()

    def log(self, msg):
        """
        Log a message

        Args:
            self: (todo): write your description
            msg: (str): write your description
        """
        if self.with_log:
            print(msg)

    def error(self, msg):
        """
        Log an error.

        Args:
            self: (todo): write your description
            msg: (str): write your description
        """
        if self.with_log:
            logger.warning(msg)
