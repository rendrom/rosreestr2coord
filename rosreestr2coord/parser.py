# coding: utf-8
import json
import logging
import os
from typing import Dict, Optional, Union

from rosreestr2coord.request.exceptions import HTTPForbiddenException

from .export import coords2kml
from .logger import logger
from .request.proxy_handling import ProxyHandling
from .request.request import make_request
from .utils import clear_code, code_to_filename, transform_to_wgs

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


class NoCoordinatesException(Exception):
    pass


class Area:

    def __init__(
        self,
        code: str = "",
        area_type: int = 1,
        media_path: str = "",
        with_log: bool = True,
        coord_out: str = "EPSG:4326",
        with_proxy: bool = False,
        use_cache: bool = True,
        proxy_handler: Optional[ProxyHandling] = None,
        timeout: int = 5,
        logger: Optional[logging.Logger] = logger,
        proxy_url: Optional[str] = None,
    ):
        self.with_log = with_log
        self.area_type = area_type
        self.media_path = media_path

        self.code = code

        self.proxy_url = proxy_url

        self.file_name = code_to_filename(self.code[:])
        self.with_proxy = with_proxy
        self.proxy_handler = proxy_handler
        self.logger = logger
        self.use_cache = use_cache
        self.coord_out = coord_out
        self.timeout = timeout

        self.feature = None

        if not code:
            return
        self.tmp_path = self.create_tmp()
        self.workspace = self.create_workspace()

        try:
            geom = self.get_geometry()
            if not geom:
                self.log("Nothing found")
        except Exception as er:
            if hasattr(er, "reason"):
                self.log(er.reason)
            else:
                self.log(er)

    def create_tmp(self):
        if not self.media_path:
            self.media_path = os.getcwd()
        tmp_path = os.path.join(self.media_path, "tmp")
        if not os.path.isdir(tmp_path):
            os.makedirs(tmp_path)
        return tmp_path

    def create_workspace(self):
        area_path_name = code_to_filename(clear_code(self.code))
        workspace = os.path.join(self.tmp_path, area_path_name)
        if not os.path.isdir(workspace):
            os.makedirs(workspace)
        return workspace

    def search(self):
        url = "https://nspd.gov.ru/map_api/s_search/search"
        payload = {
            "text": self.code,
            "pageNumber": 0,
            "pageSize": 1,
        }
        resp = self.make_request(url, method="POST", body=payload)
        return resp["result"][0]

    def get_geometry(self):

        # cad_item = self.search()

        url = "https://nspd.gov.ru/api/geoportal/v2/search/geoportal"
        params = [
            f"thematicSearchId={self.area_type}",
            f"query={self.code}",
            # "service=wfs",
            # "version=2.0.0",
            # "OUTPUTFORMAT=application/json",
            # "REQUEST=GetFeature",
            # f"TYPENAME={cad_item["className"]}",
            # f"cql_filter=cad_num='{self.code}'",
            f"CRS={self.coord_out}",
        ]
        url = f"{url}?{'&'.join(params)}"

        resp = self.make_request(url)
        features = resp["data"]["features"]
        if len(features):
            feature = transform_to_wgs(features[0])
            self.feature = feature
            return feature
        return False

    # Deprecated use to_geojson for all cases
    def to_geojson_poly(self, dumps=True):
        return self.to_geojson(dumps)

    def to_geojson(self, dumps=True):
        feature_collection = self.feature
        if feature_collection:
            if dumps:
                return json.dumps(feature_collection)
            return feature_collection
        return False

    def to_kml(self):
        coords = [self.feature["geometry"]["coordinates"]]
        attrs = self.feature["properties"]
        return coords2kml(coords, attrs)

    def _make_request(
        self,
        url: str,
        method: str,
        body: Optional[Union[Dict, bytes]],
    ):
        proxy_path = os.path.join(self.tmp_path, "proxy.txt")
        proxy_handler = self.proxy_handler if self.proxy_handler else ProxyHandling(path=proxy_path)
        self.logger.debug(url)
        headers = {
            "Content-Type": "application/json",
        }
        response = make_request(
            url=url,
            body=body,
            method=method,
            with_proxy=self.with_proxy,
            proxy_handler=proxy_handler,
            logger=self.logger,
            timeout=self.timeout,
            headers=headers,
            proxy_url=self.proxy_url,
        )
        return response

    def make_request(
        self,
        url: str,
        method: str = "GET",
        body: Union[Dict, bytes, None] = None,
    ):
        return self._make_request(url, method, body)

    @staticmethod
    def clear_code(code):
        return clear_code(code)

    def log(self, msg):
        if self.with_log:
            print(msg)

    def error(self, msg):
        if self.with_log:
            self.logger.warning(msg)
