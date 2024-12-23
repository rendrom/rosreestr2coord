from abc import ABC, abstractmethod
from typing import Dict, Optional, Union

from .exceptions import (
    HTTPBadRequestException,
    HTTPErrorException,
    HTTPForbiddenException,
    RequestException,
)
from .helpers import get_rosreestr_headers, is_error_response


class RequestAdapter(ABC):
    @abstractmethod
    def _make_request(
        self,
        url: str,
        proxy: Optional[str],
        timeout: int,
        headers: dict,
        method: str = "GET",
        body: Optional[Union[Dict, bytes]] = None,
    ) -> bytes:
        pass

    def perform_request(
        self,
        url: str,
        proxy: Optional[str],
        logger: Optional[object],
        timeout: int,
        headers: Optional[dict] = None,
        method: str = "GET",
        body: Optional[Union[Dict, bytes]] = None,
    ) -> bytes:
        """Performs the HTTP request."""
        default_headers = get_rosreestr_headers()
        headers = {**default_headers, **(headers or {})}

        try:
            response = self._make_request(url, proxy, timeout, headers, method, body)
            is_error = is_error_response(url, response)
            if is_error:
                raise RequestException(is_error)
            return response
        except self.get_specific_http_error() as er:
            if hasattr(er, "code") and er.code == 403:
                raise HTTPForbiddenException(f"HTTP 403 Forbidden: {er.reason}") from er
            elif self.is_specific_error(er):
                raise HTTPBadRequestException("HTTP 400 Bad Request") from er
            else:
                raise HTTPErrorException(f"HTTP Error: {str(er)}") from er
        except Exception as er:
            self.handle_exception(er, logger)
            raise

    def handle_exception(self, er: Exception, logger: Optional[object]) -> None:
        if logger:
            logger.error(f"Request failed: {er}")
        raise RequestException(er)

    @abstractmethod
    def get_specific_http_error(self):
        pass

    @abstractmethod
    def is_specific_error(self, er: Exception) -> bool:
        """Determines if the exception is a specific error that should be propagated."""
        pass
