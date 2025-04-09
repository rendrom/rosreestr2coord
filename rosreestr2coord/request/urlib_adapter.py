import json
import ssl
import urllib.error
import urllib.request
from typing import Dict, Optional, Union
from urllib.request import Request

from .base_adapter import RequestAdapter
from .exceptions import HTTPBadRequestException, HTTPForbiddenException, TimeoutException


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
        if body and isinstance(body, dict):
            body = json.dumps(body).encode("utf-8")

        request = Request(url, data=body, headers=headers, method=method)

        context = ssl._create_unverified_context()
        context.set_ciphers("ALL:@SECLEVEL=1")

        try:
            if proxy:
                proxy_handler = urllib.request.ProxyHandler({"http": proxy, "https": proxy})
                https_handler = urllib.request.HTTPSHandler(context=context)
                opener = urllib.request.build_opener(proxy_handler, https_handler)

                response = opener.open(request, timeout=30)
            else:
                response = urllib.request.urlopen(request, context=context, timeout=timeout)

            encoding = response.headers.get_content_charset() or "utf-8"
            data = response.read().decode(encoding)
            return json.loads(data)

        except urllib.error.HTTPError as e:
            if e.code == 403:
                raise HTTPForbiddenException(f"HTTP 403 Forbidden: {e.reason}") from e
            elif e.code == 400:
                raise HTTPBadRequestException("HTTP 400 Bad Request") from e
        except urllib.error.URLError as e:
            if isinstance(e.reason, TimeoutError):
                raise TimeoutException("The request timed out") from e
            else:
                raise

        except Exception as er:
            raise er

    def get_specific_http_error(self):
        """Returns the urllib HTTPError class."""
        return urllib.error.HTTPError

    def is_specific_error(self, er: Exception) -> bool:
        """Checks if the HTTP error code is 400."""
        return hasattr(er, "code") and er.code == 400
