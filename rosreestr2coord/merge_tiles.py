# coding=utf-8
import os
import json
import time
import math
import queue
import random
import base64
import threading
import urllib.parse
from itertools import chain, product

from PIL import Image

from rosreestr2coord.utils import make_request, TimeoutException
from .logger import logger

Image.MAX_IMAGE_PIXELS = 1000000000
Image.warnings.simplefilter("error", Image.DecompressionBombWarning)


def chunks(m, n):
    """Yield successive n-sized chunks from m."""
    for i in range(0, len(m), n):
        yield m[i : i + n]


def has_live_threads(threads):
    return True in [t.is_alive() for t in threads]


def thread_download(target, xy_tile, total, thread_count=4):
    result = queue.Queue()

    def task_wrapper(*args):
        try:
            result.put(target(*args))
        except TimeoutException:
            logger.warning("Waiting time exceeded")

    thread_count = total // 4 if total >= thread_count else total
    threads = [
        threading.Thread(target=task_wrapper, args=(p,))
        for p in list(chunks(xy_tile, thread_count))
    ]
    for t in threads:
        t.daemon = True
        t.start()

    while has_live_threads(threads):
        try:
            # synchronization timeout of threads kill
            [t.join(1) for t in threads if t is not None and t.is_alive()]
        except KeyboardInterrupt:
            # Ctrl-C handling and send kill to threads
            for t in threads:
                t.kill_received = True
                raise

    return result


class TileMerger:
    """
    :param bbox: (minLat, minLng, maxLat, maxLng)
    :type bbox: tuple
    """

    output_dir = "tmp"
    file_name_prefix = "merge"
    crs = 3857
    stream_method = thread_download
    tile_size = tuple()
    image_size = tuple()
    use_cache = True

    def __init__(
        self,
        zoom,
        bbox,
        tile_format=".jpg",
        threads=1,
        file_name_prefix=None,
        output_dir=None,
        with_log=True,
        requester=make_request,
    ):
        if output_dir:
            self.output_dir = output_dir
        if file_name_prefix:
            self.file_name_prefix = file_name_prefix
        self.with_log = with_log
        self.stop = False
        self.make_request = requester
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
        with open(path, "wb") as im:
            im.write(image)

    def set_xy_range(self):
        if len(self.bbox) != 4:
            raise Exception("Coordinate input error!")
        bbox = self.bbox
        keys = ("xMin", "xMax", "yMin", "yMax")
        if bbox:
            xy = list(
                chain(
                    *list(
                        map(
                            sorted,
                            list(
                                zip(
                                    *[
                                        deg2num(coord[0], coord[1], self.zoom)
                                        for coord in (bbox[:2], bbox[2:])
                                    ]
                                )
                            ),
                        )
                    )
                )
            )
            return dict(list(zip(keys, xy)))
        else:
            return dict.fromkeys(keys, 0)

    def calc_total(self):
        xy = self.xy_range
        return (xy["xMax"] - xy["xMin"] + 1) * (xy["yMax"] - xy["yMin"] + 1)

    def download(self):
        self.log("Get tiles:")
        self.stop = False
        if self.bbox:
            self.bbox_download()
        else:
            self.lazy_download()
        if self.count == self.total:
            first_image_name = ""
            for f in os.listdir(self.tile_dir):
                if f.endswith(self.tile_format):
                    first_image_name = f
                    break
            first_img_path = os.path.join(self.tile_dir, first_image_name)
            im = Image.open(first_img_path)
            im.load()
            self.image_size = im.size
        else:
            pass
            # raise Exception("Tile loading error!")
        self.log("")
        s = "s" if self.count > 1 else ""
        self.log("Completed, %s tile%s received" % (self.count, s))
        return self.count

    @staticmethod
    def stream(*args, **kwargs):
        thread_download(*args, **kwargs)

    def bbox_download(self):
        xy = self.xy_range
        p = list(
            product(
                range(xy["xMin"], xy["xMax"] + 1), range(xy["yMin"], xy["yMax"] + 1)
            )
        )
        self.stream(target=self.fetch_tile, xy_tile=p, total=self.total)
        if self.with_log:
            pass

    def fetch_tile(self, porties):
        for x, y in sorted(porties, key=lambda k: random.random()):
            if not self.stop:
                file_name = "%s_%s%s" % (x, y, self.tile_format)
                file_path = os.path.join(self.tile_dir, file_name)
                if not self.use_cache or not os.path.isfile(file_path):
                    url = self.get_url(x, y, self.zoom)
                    tile = self.make_request(url)
                    if tile:
                        self.write_image(tile, file_path)
                        self.count += 1
                else:
                    self.count += 1
                if self.with_log:
                    print(
                        "\r%d%% %d/%d"
                        % ((self.count / self.total) * 100, self.count, self.total),
                        end="",
                    )

    def lazy_download(self):
        row, col = True, True
        x, y, count = 0, 0, 0
        while row:
            while col:
                url_path = self.get_url(x, y, self.zoom)
                tile = self.make_request(url_path)
                if tile.getcode() == 200:
                    self.write_image(
                        tile.read(),
                        os.path.join(
                            self.tile_dir, "%s_%s%s" % (x, y, self.tile_format)
                        ),
                    )
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
            self.log("Merging tiles...")
            xy_range = self.xy_range
            filename = "%s_%d_%s%s" % (
                self.file_name_prefix,
                self.zoom,
                "".join(set([str(int(g)) for g in xy_range.values()])),
                self.tile_format,
            )
            out = Image.new(
                "RGB",
                (
                    (xy_range["xMax"] + 1 - xy_range["xMin"]) * self.image_size[0],
                    (xy_range["yMax"] + 1 - xy_range["yMin"]) * self.image_size[1],
                ),
            )
            imx = 0
            for x in range(xy_range["xMin"], xy_range["xMax"] + 1):
                imy = 0
                for y in range(xy_range["yMin"], xy_range["yMax"] + 1):
                    tile_file = os.path.join(
                        self.tile_dir, "%s_%s%s" % (x, y, self.tile_format)
                    )
                    tile = Image.open(tile_file)
                    out.paste(tile, (imx, imy))
                    imy += self.image_size[1]
                imx += self.image_size[0]
            path = os.path.join(self.output_dir, filename)
            out.save(path)
            # self.create_raster_worldfile(path)
            # self.create_prj_file(path)
            outpath = os.path.abspath(path)
            self.log("raster - %s" % outpath)
            return outpath

    def log(self, msg):
        if self.with_log:
            print(msg)


class PkkAreaMerger(TileMerger, object):
    file_name_prefix = "pkk"
    url = "https://pkk.rosreestr.ru/arcgis/rest/services/PKK6/CadastreSelected/MapServer/export"
    crs = 3857
    # tile_size = (300000, 300000)
    tile_size = (1000, 1000)
    use_cache = True
    max_count = 50
    area_type = 1

    def __init__(self, output_format, clear_code, use_cache, area_type=1, **kwargs):
        super(PkkAreaMerger, self).__init__(
            zoom=0,
            tile_format=".%s" % output_format,
            file_name_prefix=clear_code,
            **kwargs
        )
        self.file_name_prefix = clear_code.replace(":", "_")
        self.output_format = output_format
        self.clear_code = clear_code
        self.extent = self.bbox
        self.area_type = area_type
        self.use_cache = use_cache

        self.real_width = 0
        self.real_height = 0

        self._image_extent_list = []
        self.image_extent = {}

        if self.total == 1:
            xy = self.xy_range
            max_size = max(
                int(math.ceil((xy["xMax"] - xy["xMin"]))),
                int(math.ceil((xy["yMax"] - xy["yMin"]))),
            )
            self.tile_size = (max_size, max_size)
        elif self.total > self.max_count:
            self._optimize_tile_size(self.max_count)

    def get_tile_dir(self, zoom):
        return os.path.join(self.output_dir, "{}_{}".format(*self.tile_size))

    def bbox_download(self):
        dx, dy = self._get_delta()
        p = list(product(range(dx), range(dy)))
        self.stream(target=self.fetch_tile, xy_tile=p, total=self.total)

    def fetch_tile(self, porties):
        for x, y in sorted(porties, key=lambda k: random.random()):
            if not self.stop:
                file_name = "%s_%s%s" % (x, y, self.tile_format)
                file_path = os.path.join(self.tile_dir, file_name)

                imgstring = self.get_image(x, y)
                if imgstring:
                    tile = base64.b64decode(imgstring)
                    if tile:
                        self.write_image(tile, file_path)
                        self.count += 1
                #     else:
                #         self.log("Tile {} not loaded".format(file_path))
                # else:
                #     self.log("Tile {} not loaded".format(file_path))

                if self.with_log:
                    print(
                        "\r%d%% %d/%d"
                        % ((self.count / self.total) * 100, self.count, self.total),
                        end="",
                    )

    def get_url(self, x, y, z=None):
        return self.get_image_url(x, y)

    def set_xy_range(self):
        if len(self.bbox) != 4:
            raise Exception("Coordinate input error!")
        bb = self.bbox
        keys = ("xMin", "xMax", "yMin", "yMax")
        if bb:
            return dict(zip(keys, [bb[0], bb[2], bb[1], bb[3]]))

    def _get_delta(self, tile_size=False):
        tile_size = tile_size if tile_size else self.tile_size
        xy = self.xy_range
        dx = int(math.ceil((xy["xMax"] - xy["xMin"]) / tile_size[0]))
        dy = int(math.ceil((xy["yMax"] - xy["yMin"]) / tile_size[1]))
        return dx, dy

    def _optimize_tile_size(self, count):
        h = count ** 0.5
        xy = self.xy_range
        x = int((xy["xMax"] - xy["xMin"]) / h)
        y = int((xy["yMax"] - xy["yMin"]) / h)
        max_value = max([x, y])
        self.tile_size = [max_value, max_value]
        self.total = self.calc_total()

    def calc_total(self, d=False):
        d = d if d else self._get_delta()
        total = 1
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

    def get_image(self, x, y):
        output_format = self.output_format
        if self.clear_code and self.extent:
            if self.total == 1:
                dx, dy = [x if x > 500 else 500 for x in self.tile_size]
            else:
                dx, dy = self.tile_size
            code = self.clear_code

            layerDefs = ""
            # TODO: Understand how the layerDefs parameter works.
            if self.area_type == 10:
                layers = [0, 1, 2, 6]
                layerDefs = (
                    '{"0":"ID = \'%s\'","1":"objectid = -1","2":"objectid = -1","6":"objectid = -1"}'
                    % code
                )
            elif self.area_type == 7:
                layers = [0, 1, 5, 2, 6, 3, 7, 4]

                # This formatting does not work for area_type = 1
                format_layer_defs = "{"
                id_format = [
                    ('"%s":"' % layer) + ("ID = '%s'" % code) + '"'
                    for layer in sorted(layers)
                ]
                format_layer_defs += ",".join(id_format)
                format_layer_defs += "}"
                safe_string = urllib.parse.quote_plus(format_layer_defs)
                layerDefs = safe_string.replace("+", "%20")
            else:
                layers = list(map(str, range(0, 21)))
                layerDefs = {layer: str("ID = '{}'".format(code)) for layer in layers}

            params = {
                "dpi": 96,
                "transparent": "false",
                "format": "png32",
                "layers": "show:{}".format(",".join([str(l) for l in layers])),
                "bbox": ",".join(map(str, self._get_bbox_by_xy(x, y))),
                "bboxSR": 102100,
                "imageSR": 102100,
                "size": "%s,%s" % (dx, dy),
                "layerDefs": layerDefs,
                "f": "json",
                "timestamp": int(round(time.time() * 1000)),
            }
            if output_format:
                params["format"] = output_format

            url = self.url
            if self.area_type == 10:
                url = url.replace("CadastreSelected", "ZONESSelected")

            meta_url = url + "?" + urllib.parse.urlencode(params)
            if meta_url:
                data = False
                cache_path = os.path.join(self.tile_dir, "{}_{}.json".format(x, y))
                if self.use_cache:
                    try:
                        with open(cache_path, "r") as data_file:
                            data = json.loads(data_file.read())
                            if not data.get("imageData") or not data.get("extent"):
                                data = False
                    except Exception:
                        # not in cache yet
                        pass
                try:
                    if not data:
                        response = self.make_request(meta_url)
                        data = json.loads(response.decode("utf-8"))
                        if data.get("imageData") and data.get("extent"):
                            with open(cache_path, "w") as outfile:
                                json.dump(data, outfile)
                    if data and data.get("imageData"):
                        self._image_extent_list.append(data.get("extent"))
                        return data.get("imageData")
                    else:
                        logger.warning("Can't get image meta data from: %s" % meta_url)
                except Exception as er:
                    logger.warning(er)
        elif not self.extent:
            logger.warning("Can't get image without extent")
        return False

    def _merge_tiles(self):
        dx, dy = self._get_delta()

        filename = "%s%s" % (self.file_name_prefix, self.tile_format)
        path = os.path.join(self.tile_dir, filename)

        if not self.use_cache or not os.path.isfile(path):
            self.log("Merging tiles...")
            tiles = []
            imx = 0
            imy = 0
            for x in range(dx):
                imy = 0
                height = 0
                for y in reversed(range(dy)):
                    tile_file = os.path.join(
                        self.tile_dir, "%s_%s%s" % (x, y, self.tile_format)
                    )
                    try:
                        tile = Image.open(tile_file)
                        tiles.append((tile, (imx, imy)))
                        imy += tile.width
                        if tile.height > height:
                            height = tile.height
                    except Exception as er:
                        logger.warning(er)
                imx += height

            self.real_width = imx
            self.real_height = imy

            out = Image.new("L", (self.real_width, self.real_height))
            for t in tiles:
                out.paste(t[0].convert("L"), t[1])
                t[0].close()
            out.save(path)
        return path

    def merge_tiles(self):
        if self.count == self.total:
            if self.count > 1:
                path = self._merge_tiles()
            else:
                path = os.path.join(self.tile_dir, "%s_%s%s" % (0, 0, self.tile_format))
            tile = Image.open(path)
            self.real_width = tile.width
            self.real_height = tile.height
            tile.close()
            bb = self.bbox
            xmax = max([x["xmax"] for x in self._image_extent_list])
            ymax = max([x["ymax"] for x in self._image_extent_list])
            self.image_extent = {
                "xmin": bb[0],
                "ymin": bb[1],
                "xmax": xmax,
                "ymax": ymax,
            }
            outpath = os.path.abspath(path)
            create_raster_worldfile(path, self.image_extent)
            create_prj_file(path)
            self.log("raster - %s" % outpath)
            return outpath


def create_raster_worldfile(path, xy_range):
    x_y = xy_range
    im = Image.open(path)
    output_dir = os.path.dirname(path)
    gw_path = "".join(os.path.split(path)[-1].split(".")[:-1])
    world_file_path = os.path.join(output_dir, "%s.pgw" % gw_path)
    with open(world_file_path, "w") as world:
        min_x, max_x = x_y["xmin"], x_y["xmax"]
        min_y, max_y = x_y["ymin"], x_y["ymax"]

        x_pixel_size = (max_x - min_x) / im.size[0]
        y_pixel_size = (max_y - min_y) / im.size[1]
        # pixel size in the x-direction in map units/pixel
        world.write("%s\n" % x_pixel_size)
        world.write("%s\n" % 0)  # rotation about y-axis
        world.write("%s\n" % 0)  # rotation about x-axis
        # pixel size in the y-direction in map units. Always negative
        world.write("%s\n" % -(abs(y_pixel_size)))
        # x-coordinate of the center of the upper left pixel
        world.write("%s\n" % min_x)
        # y-coordinate of the center of the upper left pixel
        world.write("%s\n" % max_y)


def create_prj_file(path, crs=3857):
    output_dir = os.path.dirname(path)
    prj_str = {
        4326: """
        GEOGCS["GCS_WGS_1984",DATUM["D_WGS84",SPHEROID["WGS84",6378137,298.257223563]],
        PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]]
        """,
        3857: """
        PROJCS["WGS_1984_Web_Mercator_Auxiliary_Sphere",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",
        SPHEROID["WGS_1984",6378137,0]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]],
        PROJECTION["Mercator"],PARAMETER["central_meridian",0],PARAMETER["standard_parallel_1",0],
        PARAMETER["false_easting",0],PARAMETER["false_northing",0],PARAMETER["Auxiliary_Sphere_Type",0],
        UNIT["Meter",1]]
        """,
    }
    prj_path = "".join(os.path.split(path)[-1].split(".")[:-1])
    prj_file_path = os.path.join(output_dir, "%s.prj" % prj_path)
    prj = open(prj_file_path, "w")
    prj.write(prj_str[crs])
    prj.close()


def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int(
        (1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi)
        / 2.0
        * n
    )
    return xtile, ytile


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
    return lat_deg, lon_deg


def check_bbox_str(bbox):
    b = map(float, bbox.split())
    if len(b) != 4:
        return False
    return all([b[x + 2] - b[x] >= 0 for x in [0, 1]])
