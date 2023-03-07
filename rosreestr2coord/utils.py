import re
import ssl
import json
import math
import urllib.error
import urllib.parse
from urllib.request import Request, urlopen

from .proxy_handling import ProxyHandling


def y2lat(y):
    return (2 * math.atan(math.exp(y / 6378137)) - math.pi / 2) / (math.pi / 180)


def x2lon(x):
    return x / (math.pi / 180.0) / 6378137.0


def xy2lonlat(x, y):
    return [x2lon(x), y2lat(y)]


USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 \
    Safari/537.36"


class TimeoutException(Exception):
    pass


def get_rosreestr_headers():
    return {
        "pragma": "no-cache",
        "referer": "https://pkk.rosreestr.ru/",
        "user-agent": USER_AGENT,
        "x-requested-with": "XMLHttpRequest",
    }


proxy_handling = ProxyHandling()


def make_request(url, with_proxy=False, proxy_handler=None):
    if url:
        if with_proxy:
            proxy_handler = proxy_handler if proxy_handler else proxy_handling
            return make_request_with_proxy(url, proxy_handler)
        try:
            headers = get_rosreestr_headers()
            request = Request(url, headers=headers)
            context = ssl._create_unverified_context()
            with urlopen(request, context=context, timeout=3000) as response:
                read = response.read()
            is_error = is_error_response(url, read)
            if is_error:
                raise Exception(is_error)
            return read
        except Exception as er:
            raise er
    raise ValueError("The url is not set")


def make_request_with_proxy(url, url_proxy):
    tries_per_proxy = 3
    tries_for_proxies = 20

    for j in range(0, tries_for_proxies):
        proxies = url_proxy.load_proxies()
        p = proxies.pop()

        for i in range(0, tries_per_proxy):
            try:
                proxy_handler = urllib.request.ProxyHandler({"http": p, "https": p})
                opener = urllib.request.build_opener(proxy_handler)
                urllib.request.install_opener(opener)
                headers = get_rosreestr_headers()

                request = Request(url, headers=headers)
                context = ssl._create_unverified_context()
                with urlopen(request, context=context, timeout=3000) as response:
                    read = response.read()
                return read
            except urllib.error.HTTPError as er:
                # 400 is not proxy problem
                if er.code == 400:
                    raise er
            except Exception as er:
                pass

        # remove useless proxy server
        proxies_ = url_proxy.get_proxies()
        if p in proxies_:
            proxies_.remove(p)
            url_proxy.dump_proxies(proxies_)

    raise Exception("Unable to upload via proxy")


def is_error_response(url, response):
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


def code_to_filename(code):
    return code.replace(":", "_").replace("/", "-")


def clear_code(code):
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
