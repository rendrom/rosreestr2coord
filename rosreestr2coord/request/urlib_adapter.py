import json
import ssl
import urllib.error
import urllib.request
from typing import Dict, Optional, Union
from urllib.request import Request, urlopen

from .base_adapter import RequestAdapter
from .exceptions import HTTPBadRequestException, HTTPForbiddenException


class UrllibAdapter(RequestAdapter):
    def _make_request(
        self,
        url: str,
        proxy: Optional[str],
        timeout: int,
        headers: dict,
        method: str = "GET",
        body: Optional[Union[Dict, bytes]] = None,
    ) -> bytes:
        """Performs an HTTP request using urllib with optional proxy settings."""
        if proxy:
            proxy_handler = urllib.request.ProxyHandler({"http": proxy, "https": proxy})
            opener = urllib.request.build_opener(proxy_handler)
            urllib.request.install_opener(opener)

        if body and isinstance(body, dict):
            body = json.dumps(body).encode("utf-8")

        request = Request(url, data=body, headers=headers, method=method)
        context = ssl._create_unverified_context()
        context.set_ciphers("ALL:@SECLEVEL=1")

        try:
            with urlopen(request, context=context, timeout=timeout) as response:
                encoding = response.headers.get_content_charset() or "utf-8"
                data = response.read().decode(encoding)

                return json.loads(data)

        except urllib.error.HTTPError as e:
            if e.code == 403:
                raise HTTPForbiddenException(f"HTTP 403 Forbidden: {e.reason}") from e
            elif e.code == 400:
                raise HTTPBadRequestException("HTTP 400 Bad Request") from e
        except Exception as er:
            raise

    def get_specific_http_error(self):
        """Returns the urllib HTTPError class."""
        return urllib.error.HTTPError

    def is_specific_error(self, er: Exception) -> bool:
        """Checks if the HTTP error code is 400."""
        return hasattr(er, "code") and er.code == 400
