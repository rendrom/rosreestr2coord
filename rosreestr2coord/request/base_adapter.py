from abc import ABC, abstractmethod
from typing import Optional

from .exceptions import HTTPBadRequestException, HTTPErrorException, RequestException
from .helpers import get_rosreestr_headers, is_error_response


class RequestAdapter(ABC):
    @abstractmethod
    def _make_request(
        self,
        url: str,
        proxy: Optional[str],
        headers: dict,
        timeout: int,
    ) -> bytes:
        pass

    def perform_request(
        self,
        url: str,
        proxy: Optional[str],
        logger: Optional[object],
        timeout: int,
    ) -> bytes:
        """Performs the HTTP request."""
        headers = get_rosreestr_headers()
        try:
            response = self._make_request(url, proxy, headers, timeout)
            is_error = is_error_response(url, response)
            if is_error:
                raise RequestException(is_error)
            return response
        except self.get_specific_http_error() as er:
            if self.is_specific_error(er):
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
