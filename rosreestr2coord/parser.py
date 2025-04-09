# coding: utf-8
import json
import logging
import os
import warnings
from typing import Dict, Optional, Union

from .export import coords2kml
from .logger import logger
from .request.proxy_handling import ProxyHandling
from .request.request import make_request
from .utils import clear_code, code_to_filename, transform_to_wgs

TYPES = {
    "Объекты недвижимости": 1,
    "Кадастровое деление": 2,
    "Административно-территориальное деление": 4,
    "Зоны и территории": 5,
    "Территориальные зоны": 7,
    "Комплексы объектов": 15,
}


class NoCoordinatesException(Exception):
    """Exception raised when no coordinates are found."""

    pass


class Area:
    def __init__(
        self,
        code: str = "",
        area_type: Optional[int] = 1,
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
        self.code: str = code
        self.area_type: Optional[int] = area_type
        self.media_path: str = media_path or os.getcwd()
        self.with_log: bool = with_log
        self.coord_out: str = coord_out
        self.with_proxy: bool = with_proxy
        self.use_cache: bool = use_cache
        self.timeout: int = timeout
        self.proxy_handler: Optional[ProxyHandling] = proxy_handler
        self.proxy_url: Optional[str] = proxy_url
        self.logger: logging.Logger = logger or logging.getLogger(__name__)

        self.file_name: str = code_to_filename(self.code)
        self.feature: Optional[dict] = None

        self.tmp_path: str = self.create_tmp()

        if not self.code:
            return

        if with_log:
            try:
                geom = self.get_geometry()
                if not geom:
                    self.log("Nothing found")
            except Exception as er:
                message = getattr(er, "reason", str(er))
                self.log(message)
        else:
            geom = self.get_geometry()

    def create_tmp(self) -> str:
        tmp_path = os.path.join(self.media_path, "tmp")
        os.makedirs(tmp_path, exist_ok=True)
        return tmp_path

    def _build_url(self, area_type: int) -> str:
        base_url = "https://nspd.gov.ru/api/geoportal/v2/search/geoportal"
        params = [
            f"thematicSearchId={area_type}",
            f"query={self.code}",
            f"CRS={self.coord_out}",
        ]
        return f"{base_url}?{'&'.join(params)}"

    def _query_with_area_type(self, area_type: int) -> Optional[dict]:
        url = self._build_url(area_type)
        resp = self.make_request(url)
        if resp:
            features = resp.get("data", {}).get("features", [])
            if features:
                feature = transform_to_wgs(features[0])
                if self._matches_criteria(feature):
                    self.feature = feature
                    return feature
        return None

    def get_geometry(self) -> Optional[dict]:
        if self.area_type is not None:
            if self.area_type not in TYPES.values():
                raise ValueError(
                    "Invalid area_type specified. Available options: "
                    + ", ".join([f"{k} - {v}" for k, v in TYPES.items()])
                )
            return self._query_with_area_type(self.area_type)

    def _matches_criteria(self, feature: dict) -> bool:
        return True

    def to_geojson_poly(self, dumps: bool = True) -> Union[str, dict, None]:
        warnings.warn("to_geojson_poly is deprecated. Use to_geojson instead.", DeprecationWarning)
        return self.to_geojson(dumps=dumps)

    def to_geojson(self, dumps: bool = True) -> Union[str, dict, None]:
        if self.feature:
            return json.dumps(self.feature) if dumps else self.feature
        return None

    def to_kml(self) -> str:
        if not self.feature:
            raise NoCoordinatesException("No geometry feature available for conversion to KML.")
        coords = [self.feature.get("geometry", {}).get("coordinates")]
        attrs = self.feature.get("properties", {})
        return coords2kml(coords, attrs)

    def _make_request(
        self,
        url: str,
        method: str,
        body: Optional[Union[Dict, bytes]] = None,
    ) -> dict:
        proxy_path = os.path.join(self.tmp_path, "proxy.txt")
        effective_proxy_handler = self.proxy_handler or ProxyHandling(path=proxy_path)
        self.logger.debug(f"Request URL: {url}")
        headers = {"Content-Type": "application/json"}
        response = make_request(
            url=url,
            body=body,
            method=method,
            with_proxy=self.with_proxy,
            proxy_handler=effective_proxy_handler,
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
        body: Optional[Union[Dict, bytes]] = None,
    ) -> dict:
        return self._make_request(url, method, body)

    @staticmethod
    def clear_code(code: str) -> str:
        return clear_code(code)

    def log(self, msg: str) -> None:
        if self.with_log:
            self.logger.info(msg)
            print(msg)

    def error(self, msg: str) -> None:
        if self.with_log:
            self.logger.warning(msg)
