from typing import Optional

import httpx

from .base_adapter import RequestAdapter


class HttpxAdapter(RequestAdapter):
    def _make_request(
        self,
        url: str,
        proxy: Optional[str],
        headers: dict,
        timeout: int,
    ) -> bytes:
        proxies = {"http://": f"http://{proxy}", "https://": f"http://{proxy}"} if proxy else None
        with httpx.Client(proxies=proxies, verify=False, timeout=timeout) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()
            return response.content

    def get_specific_http_error(self):
        return httpx.HTTPStatusError

    def is_specific_error(self, er: Exception) -> bool:
        """Checks if the HTTP status code is 400."""
        return hasattr(er, "response") and er.response.status_code == 400
