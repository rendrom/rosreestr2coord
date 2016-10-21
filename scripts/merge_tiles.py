# coding=utf-8
from __future__ import print_function, unicode_literals, division

import json
import math
import os
import random
import threading
from itertools import chain, product

from PIL import Image

try:
    import Queue
    import urlparse
    from urllib import urlencode
except ImportError:  # For Python 3
    import urllib.parse as urlparse
    from urllib.parse import urlencode
    from queue import Queue

from scripts.utils import make_request

VERSION = "1.0.0"


def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in range(0, len(l), n):
        yield l[i:i + n]


def thread_download(target, xy_tile, total, thread_count=4):
    result = Queue.Queue()

    def task_wrapper(*args):
        result.put(target(*args))

    thread_count = total // 4 if total >= thread_count else total
    threads = [threading.Thread(target=task_wrapper, args=(p,)) for p in list(chunks(xy_tile, thread_count))]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return result


class TileMerger:
    """
    :param bbox: (minLat, minLng, maxLat, maxLng)
    :type bbox: tuple
    """
    output_dir = 'tmp'
    file_name_prefix = 'merge'
    crs = 3857
    stream_method = thread_download
    tile_size = tuple()
    use_cache = True

    def __init__(self, zoom, bbox, tile_format='.jpg', threads=7, file_name_prefix=None, output_dir=None,
                 with_log=True):
        if output_dir:
            self.output_dir = output_dir
        if file_name_prefix:
            self.file_name_prefix = file_name_prefix
        self.with_log = with_log
        self.stop = False
        self.threads = threads
        self.total = 0
        self.count = 0
        self.zoom = zoom
        self.tile_format = tile_format
        self.bbox = bbox
        self.xy_range = self.set_xy_range()
        self.total = self.calc_total()
        self.tile_dir = self.get_tile_dir(zoom)
        if not os.path.exists(self.tile_dir):
            os.makedirs(self.tile_dir)

    def get_tile_dir(self, zoom):
        return os.path.join(self.output_dir, "%s_%s" % (self.file_name_prefix, zoom))

    @staticmethod
    def write_image(image, path):
        with open(path, 'wb') as im:
            im.write(image)

    def set_xy_range(self):
        if len(self.bbox) != 4:
            raise Exception("Coordinate input error!")
        bbox = self.bbox
        keys = ("xMin", "xMax", "yMin", "yMax")
        if bbox:
            xy = list(chain(*map(sorted, zip(*[deg2num(l[0], l[1], self.zoom) for l in (bbox[:2], bbox[2:])]))))
            return dict(zip(keys, xy))
        else:
            return dict.fromkeys(keys, 0)

    def calc_total(self):
        xy = self.xy_range
        return (xy["xMax"] - xy["xMin"] + 1) * (xy["yMax"] - xy["yMin"] + 1)

    def download(self):
        self.log(u'Run download:')
        self.stop = False
        if self.bbox:
            self.bbox_download()
        else:
            self.lazy_download()
        if self.count == self.total:
            with Image.open(os.path.join(self.tile_dir, os.listdir(self.tile_dir)[0])) as im:
                self.tile_size = im.size
        self.log('Downloading completed. Uploaded tiles - %s' % self.count)
        return self.count

    @staticmethod
    def stream(*args, **kwargs):
        thread_download(*args, **kwargs)

    def bbox_download(self):
        xy = self.xy_range
        p = list(product(range(xy['xMin'], xy['xMax'] + 1), range(xy['yMin'], xy['yMax'] + 1)))
        self.stream(target=self.fetch_tile, xy_tile=p, total=self.total)
        if self.with_log:
            print()

    def fetch_tile(self, porties):
        for x, y in sorted(porties, key=lambda k: random.random()):
            if not self.stop:
                file_name = "%s_%s%s" % (x, y, self.tile_format)
                file_path = os.path.join(self.tile_dir, file_name)
                if not self.use_cache or not os.path.isfile(file_path):
                    url = self.get_url(x, y, self.zoom)
                    tile = make_request(url)
                    if tile:
                        self.write_image(tile.read(), file_path)
                        self.count += 1
                else:
                    self.count += 1
                if self.with_log:
                    print("\r%d%% %d/%d" % ((self.count / self.total) * 100, self.count, self.total), end='')

    def lazy_download(self):
        row, col = True, True
        x, y, count = 0, 0, 0
        while row:
            while col:
                url_path = self.get_url(x, y, self.zoom)
                tile = make_request(url_path)
                if tile.getcode() == 200:
                    self.write_image(tile.read(), os.path.join(self.tile_dir, "%s_%s%s" % (x, y, self.tile_format)))
                    if y > self.xy_range["yMax"]:
                        self.xy_range["yMax"] = y
                    count += 1
                    y += 1
                else:
                    col = False
            if y == 0:
                row = False
            else:
                self.xy_range["xMax"] = x
                col, x, y = True, x + 1, 0
        return count

    def merge_tiles(self):
        if self.count == self.total:
            self.log('Merging tiles...')
            xy_range = self.xy_range
            filename = '%s_%d_%s%s' % (self.file_name_prefix, self.zoom,
                                       ''.join(set([str(int(g)) for g in xy_range.values()])), self.tile_format)
            out = Image.new('RGB', ((xy_range["xMax"] + 1 - xy_range["xMin"]) * self.tile_size[0],
                                    (xy_range["yMax"] + 1 - xy_range["yMin"]) * self.tile_size[1]))
            imx = 0
            for x in range(xy_range["xMin"], xy_range["xMax"] + 1):
                imy = 0
                for y in range(xy_range["yMin"], xy_range["yMax"] + 1):
                    tile_file = os.path.join(self.tile_dir, "%s_%s%s" % (x, y, self.tile_format))
                    tile = Image.open(tile_file)
                    out.paste(tile, (imx, imy))
                    imy += self.tile_size[1]
                imx += self.tile_size[0]
            path = os.path.join(self.output_dir, filename)
            out.save(path)
            # self.create_raster_worldfile(path)
            # self.create_prj_file(path)
            outpath = os.path.abspath(path)
            self.log('You raster - %s' % outpath)
            return outpath

            # def create_raster_worldfile(self, path, xy_range=None):
            #     from globalmaptiles import GlobalMercator
            #     x_y = xy_range or self.xy_range
            #     im = Image.open(path)
            #     gw_path = ''.join(os.path.split(path)[-1].split('.')[:-1])
            #     world_file_path = os.path.join(os.path.curdir, os.path.join(self.output_dir, "%s.jgw" % gw_path))
            #     with open(world_file_path, 'w') as world:
            #         min_y, min_x = num2deg(x_y['xMin'], x_y['yMax'] + 1, self.zoom)
            #         max_y, max_x = num2deg(x_y['xMax'] + 1, x_y['yMin'], self.zoom)
            #         gm = GlobalMercator()
            #         min_x, min_y = gm.LatLonToMeters(min_y, min_x)
            #         max_x, max_y = gm.LatLonToMeters(max_y, max_x)
            #         x_pixel_size = (max_x - min_x) / im.size[0]
            #         y_pixel_size = (max_y - min_y) / im.size[1]
            #         world.write(b"%f\n" % x_pixel_size)  # pixel size in the x-direction in map units/pixel
            #         world.write(b"%f\n" % 0)  # rotation about y-axis
            #         world.write(b"%f\n" % 0)  # rotation about x-axis
            #         world.write(b"%f\n" % -(abs(y_pixel_size)))  # pixel size in the y-direction in map units. Always negative
            #         world.write(b"%f\n" % min_x)  # x-coordinate of the center of the upper left pixel
            #         world.write(b"%f\n" % max_y)  # y-coordinate of the center of the upper left pixel
            #
            # def create_prj_file(self, path, crs=None):
            #     crs = crs or self.crs
            #     prj_str = {
            #         4326: b"""
            #         GEOGCS["GCS_WGS_1984",DATUM["D_WGS84",SPHEROID["WGS84",6378137,298.257223563]],
            #         PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]]
            #         """,
            #         3857: b"""
            #         PROJCS["WGS_1984_Web_Mercator_Auxiliary_Sphere",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",
            #         SPHEROID["WGS_1984",6378137,0]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]],
            #         PROJECTION["Mercator"],PARAMETER["central_meridian",0],PARAMETER["standard_parallel_1",0],
            #         PARAMETER["false_easting",0],PARAMETER["false_northing",0],PARAMETER["Auxiliary_Sphere_Type",0],
            #         UNIT["Meter",1]]
            #         """
            #     }
            #     prj_path = ''.join(os.path.split(path)[-1].split('.')[:-1])
            #     prj_file_path = os.path.join(os.path.curdir, os.path.join(self.output_dir, "%s.prj" % prj_path))
            #     prj = open(prj_file_path, 'w')
            #     prj.write(prj_str[crs])
            #     prj.close()

    def log(self, msg):
        if self.with_log:
            print(msg)


class UrlTileMerger(TileMerger, object):
    """ Read tile from custom URL
    :param url: query template 'http[s]://{s}.some_tile_service_address/{x}/{y}/{z}{f}'
                {x},{y} - tile position
                {z} - zoom level
                {s} - subdomains
                {f} - image format
    """

    def __init__(self, url, **kwargs):
        super(UrlTileMerger, self).__init__(**kwargs)
        self.url = url

    @staticmethod
    def simple_url(x, y, z, url, f='.jpg'):
        return url.format(**locals())

    def get_url(self, x, y, z):
        return self.simple_url(x, y, z, self.url, f=self.tile_format)


class BingMerger(TileMerger, object):
    url = "http://t{s}.tiles.virtualearth.net/tiles/a{q}.jpeg?g=1398"
    file_name_prefix = 'bing'
    crs = 3857

    def get_url(self, x, y, z):
        return self.url.format(q=self._quad_key(x, y, z), s=random.choice([0, 1, 2, 3, 4]))

    @staticmethod
    def _quad_key(x, y, z):
        quad_key = []
        for i in range(z, 0, -1):
            digit = 0
            mask = 1 << (i - 1)
            if (x & mask) != 0:
                digit += 1
            if (y & mask) != 0:
                digit += 2
            quad_key.append(str(digit))
        return ''.join(quad_key)


class GoogleMerger(UrlTileMerger):
    url = "http://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"  # "http://khm0.googleapis.com/kh?v=173&x={x}&y={y}&z={z}"
    file_name_prefix = 'google'
    crs = 3857

    def __init__(self, bbox, zoom, **kwargs):
        super(GoogleMerger, self).__init__(bbox=bbox, zoom=zoom, url=self.url, **kwargs)


class PkkAreaMerger(TileMerger, object):
    file_name_prefix = 'pkk'
    url = "http://pkk5.rosreestr.ru/arcgis/rest/services/Cadastre/CadastreSelected/MapServer/export"
    crs = 3857
    tile_size = (2000, 2000)
    use_cache = False

    def __init__(self, output_format, clear_code, **kwargs):
        super(PkkAreaMerger, self).__init__(zoom=0, tile_format='.%s' % output_format,
                                            file_name_prefix=clear_code, **kwargs)
        self.file_name_prefix = clear_code.replace(":", "_")
        self.output_format = output_format
        self.clear_code = clear_code
        self.extent = self.bbox

        self.real_width = 0
        self.real_height = 0

        self._image_extent_list = []
        self.image_extent = {}

    def get_tile_dir(self, zoom):
        return os.path.join(self.output_dir, "%s" % self.file_name_prefix.replace(":", "_"))

    def bbox_download(self):
        dx, dy = self._get_delta()
        p = list(product(range(dx), range(dy)))
        self.stream(target=self.fetch_tile, xy_tile=p, total=self.total)
        self.log("")

    def get_url(self, x, y, z=None):
        return self.get_image_url(x, y)

    def set_xy_range(self):
        if len(self.bbox) != 4:
            raise Exception("Coordinate input error!")
        bb = self.bbox
        keys = ("xMin", "xMax", "yMin", "yMax")
        if bb:
            return dict(zip(keys, [bb[0], bb[2], bb[1], bb[3]]))

    def _get_delta(self):
        xy = self.xy_range
        dx = int(math.ceil((xy["xMax"] - xy["xMin"]) / self.tile_size[0]))
        dy = int(math.ceil((xy["yMax"] - xy["yMin"]) / self.tile_size[1]))
        return dx, dy

    def calc_total(self):
        total = 1
        d = self._get_delta()
        for x in d:
            total *= x
        return total

    def _get_bbox_by_xy(self, x, y):
        bbox = self.xy_range
        xMin = bbox["xMin"] + (x * self.tile_size[0])
        xMax = bbox["xMin"] + ((x + 1) * self.tile_size[0])
        yMin = bbox["yMin"] + (y * self.tile_size[1])
        yMax = bbox["yMin"] + ((y + 1) * self.tile_size[1])
        return [xMax, yMax, xMin, yMin]

    def get_image_url(self, x, y):
        output_format = self.output_format

        if self.clear_code and self.extent:
            dx, dy = self.tile_size
            code = self.clear_code

            layers = map(str, range(0, 20))
            params = {
                "dpi": 96,
                "transparent": "false",
                "format": "png",
                "layers": "show:%s" % ",".join(layers),
                "bbox": ",".join(map(str, self._get_bbox_by_xy(x, y))),
                "bboxSR": 102100,
                "imageSR": 102100,
                "size": "%s,%s" % (dx * 10, dy * 10),
                "layerDefs": {layer: str("ID = '%s'" % code) for layer in layers},
                "f": "json"
            }
            if output_format:
                params["format"] = output_format
            url_parts = list(urlparse.urlparse(self.url))
            query = dict(urlparse.parse_qsl(url_parts[4]))
            query.update(params)
            url_parts[4] = urlencode(query)
            meta_url = urlparse.urlunparse(url_parts)
            if meta_url:
                try:
                    response = make_request(meta_url)
                    read = response.read()
                    data = json.loads(read)
                    if data.get("href"):
                        self._image_extent_list.append(data.get("extent"))
                        return meta_url.replace("f=json", "f=image")
                    else:
                        print("Can't get image meta data from: %s" % meta_url)
                except Exception as er:
                    print(er)
        elif not self.extent:
            print("Can't get image without extent")
        return False

    def merge_tiles(self):
        dx, dy = self._get_delta()
        if self.count == self.total:
            self.log('Merging tiles...')
            filename = '%s%s' % (self.file_name_prefix, self.tile_format)
            tiles = []
            imx = 0
            imy = 0
            for x in range(dx + 1):
                imy = 0
                height = 0
                for y in reversed(range(dy + 1)):
                    tile_file = os.path.join(self.tile_dir, "%s_%s%s" % (x, y, self.tile_format))
                    tile = Image.open(tile_file)
                    tiles.append((tile, (imx, imy)))
                    imy += tile.width
                    if tile.height > height:
                        height = tile.height
                imx += height
            path = os.path.join(self.output_dir, filename)

            self.real_width = imx
            self.real_height = imy

            bb = self.bbox
            xmax = max([x["xmax"] for x in self._image_extent_list])
            ymax = max([x["ymax"] for x in self._image_extent_list])
            self.image_extent = {"xmin": bb[0], "ymin": bb[1], "xmax": xmax, "ymax": ymax}
            out = Image.new('RGB', (self.real_width, self.real_height))
            for t in tiles:
                out.paste(t[0], t[1])
            out.save(path)
            outpath = os.path.abspath(path)
            self.log('You raster - %s' % outpath)
            return outpath


def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return (xtile, ytile)


def num2deg(xtile, ytile, zoom):
    """
    This returns the NW-corner of the square.
    Use the function with xtile+1 and/or ytile+1 to get the other corners.
    With xtile+0.5 & ytile+0.5 it will return the center of the tile.
    """
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)
    return (lat_deg, lon_deg)


LAYERS = {
    'Bing': BingMerger,
    'Google': GoogleMerger
}


def get_available_layers():
    return LAYERS


def check_bbox_str(bbox):
    b = map(float, bbox.split())
    if len(b) != 4:
        return False
    return all(map(lambda x: b[x + 2] - b[x] >= 0, [0, 1]))
