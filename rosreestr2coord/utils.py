import json
import math
import re
import ssl
import urllib.error
import urllib.parse
from typing import Dict, List, Optional, Union
from urllib.request import Request, urlopen

from .proxy_handling import ProxyHandling


def y2lat(y: float) -> float:
    return (2 * math.atan(math.exp(y / 6378137)) - math.pi / 2) / (math.pi / 180)


def x2lon(x: float) -> float:
    return x / (math.pi / 180.0) / 6378137.0


def xy2lonlat(x: float, y: float) -> List[float]:
    return [x2lon(x), y2lat(y)]


USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 \
    Safari/537.36"


class TimeoutException(Exception):
    pass


def get_rosreestr_headers() -> Dict[str, str]:
    return {
        "pragma": "no-cache",
        "referer": "https://pkk.rosreestr.ru/",
        "user-agent": USER_AGENT,
        "x-requested-with": "XMLHttpRequest",
    }


proxy_handling = ProxyHandling()


def make_request(
    url: str,
    with_proxy: bool = False,
    proxy_handler: Optional[ProxyHandling] = None,
    logger: Optional[object] = None,
    timeout: int = 5,
    proxy_url: Optional[str] = None,
) -> Union[bytes, None]:
    if url:
        if proxy_url is not None:
            return make_request_with_specified_proxy(url, proxy_url, logger)
        elif with_proxy:
            proxy_handler = proxy_handler if proxy_handler else proxy_handling
            return make_request_with_proxy(url, proxy_handler, logger, timeout)
        try:
            return perform_request(url, None, logger, timeout)
        except Exception as er:
            raise er
    raise ValueError("The url is not set")


def perform_request(
    url: str,
    proxy_handler: Optional[urllib.request.ProxyHandler],
    logger: Optional[object],
    timeout: int,
) -> bytes:
    try:
        headers = get_rosreestr_headers()
        if proxy_handler:
            opener = urllib.request.build_opener(proxy_handler)
            urllib.request.install_opener(opener)
        request = Request(url, headers=headers)
        context = ssl._create_unverified_context()
        with urlopen(request, context=context, timeout=timeout) as response:
            read = response.read()
        is_error = is_error_response(url, read)
        if is_error:
            raise Exception(is_error)
        return read
    except urllib.error.HTTPError as er:
        if er.code == 400:
            raise er
        else:
            raise Exception(f"HTTPError: {er}")
    except Exception as er:
        if logger:
            logger.error(f"Request failed: {er}")
        raise


def make_request_with_specified_proxy(url: str, proxy_url: str, logger: Optional[object]) -> bytes:
    tries = 3
    for attempt in range(1, tries + 1):
        try:
            proxy_handler = urllib.request.ProxyHandler({"http": proxy_url, "https": proxy_url})
            return perform_request(url, proxy_handler, logger, timeout=5)
        except Exception as er:
            if logger:
                logger.error(f"Attempt {attempt} failed: {er}")
            if attempt == tries:
                raise TimeoutException(f"Failed to make request after {tries} attempts")
            else:
                if logger:
                    logger.debug(f"Retrying... (Attempt {attempt + 1} of {tries})")


def make_request_with_proxy(url: str, url_proxy: ProxyHandling, logger: Optional[object], timeout: int) -> bytes:
    tries_per_proxy = 3
    tries_for_proxies = 20

    for j in range(tries_for_proxies):
        proxies = url_proxy.load_proxies()
        p = proxies.pop()

        if logger:
            logger.debug(f"Using proxy {p}")

        for i in range(tries_per_proxy):
            try:
                proxy_handler = urllib.request.ProxyHandler({"http": p, "https": p})
                return perform_request(url, proxy_handler, logger, timeout)
            except urllib.error.HTTPError as er:
                # 400 is not proxy problem
                if er.code == 400:
                    raise er
            except Exception as er:
                if logger:
                    logger.error(er)
        # remove useless proxy server
        proxies_ = url_proxy.get_proxies()
        if p in proxies_:
            proxies_.remove(p)
            url_proxy.dump_proxies(proxies_)

    if logger:
        logger.error("Unable to upload via proxy")
    raise TimeoutException("Failed to make request after using all proxies")


def is_error_response(url: str, response: bytes) -> Union[bool, str]:
    is_error = False
    try:
        data = json.loads(response)
        error = data.get("error")
        if error:
            message = error.get("message")
            is_error = message if message else "error"
    except Exception:
        pass
    return is_error


def code_to_filename(code: str) -> str:
    return code.replace(":", "_").replace("/", "-")


def clear_code(code: str) -> str:
    """
    Remove first nulls from code xxxx:00xx >> xxxx:xx
    but if the cadastral number, for example "02:02-6.667",
    then the all parts will remain zeros
    """
    is_delimited_code = re.match(r"^\d+(\:\d+)", code)
    leave_zeros = "." in code
    if is_delimited_code and not leave_zeros:
        parts = []
        for x in code.split(":"):
            strip_zeros = x.lstrip("0")
            if strip_zeros:
                parts.append(strip_zeros)
            else:
                parts.append("0")
        return ":".join(parts)
    return code
