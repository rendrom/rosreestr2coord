import ssl
import urllib.error
import urllib.request
from typing import Optional
from urllib.request import Request, urlopen

from .base_adapter import RequestAdapter


class UrllibAdapter(RequestAdapter):
    def _make_request(
        self,
        url: str,
        proxy: Optional[str],
        headers: dict,
        timeout: int,
    ) -> bytes:
        """Performs an HTTP request using urllib with optional proxy settings."""
        if proxy:
            proxy_handler = urllib.request.ProxyHandler({"http": proxy, "https": proxy})
            opener = urllib.request.build_opener(proxy_handler)
            urllib.request.install_opener(opener)
        request = Request(url, headers=headers)
        context = ssl._create_unverified_context()
        context.set_ciphers("ALL:@SECLEVEL=1")
        with urlopen(request, context=context, timeout=timeout) as response:
            return response.read()

    def get_specific_http_error(self):
        """Returns the urllib HTTPError class."""
        return urllib.error.HTTPError

    def is_specific_error(self, er: Exception) -> bool:
        """Checks if the HTTP error code is 400."""
        return hasattr(er, "code") and er.code == 400
