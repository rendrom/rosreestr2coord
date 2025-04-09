from typing import Dict, Optional, Union

from .base_adapter import RequestAdapter
from .exceptions import HTTPBadRequestException, HTTPErrorException, TimeoutException
from .proxy_handling import ProxyHandling
from .urlib_adapter import UrllibAdapter

proxy_handling = ProxyHandling()
request_adapter = UrllibAdapter()


def make_request(
    url: str,
    adapter: RequestAdapter = request_adapter,
    with_proxy: bool = False,
    proxy_handler: Optional[ProxyHandling] = None,
    logger: Optional[object] = None,
    timeout: int = 5,
    proxy_url: Optional[str] = None,
    headers: Optional[dict] = None,
    method: str = "GET",
    body: Union[Dict, bytes, None] = None,
) -> Union[bytes, None]:
    if not url:
        raise ValueError("The URL is not set")

    if proxy_url is not None:
        # Use a specified proxy
        return make_request_with_specified_proxy(url, proxy_url, logger, adapter, timeout, headers, method, body)
    elif with_proxy:
        # Use a pool of proxies
        proxy_handler = proxy_handler if proxy_handler else ProxyHandling()
        return make_request_with_proxy(url, proxy_handler, logger, adapter, timeout, headers, method, body)
    else:
        # Make a direct request without proxies
        try:
            return adapter.perform_request(url, None, logger, timeout, headers, method, body)
        except Exception as er:
            raise er


def make_request_with_specified_proxy(
    url: str,
    proxy: str,
    logger: Optional[object],
    adapter: RequestAdapter,
    timeout: int,
    headers: Optional[dict] = None,
    method: str = "GET",
    body: Union[Dict, bytes, None] = None,
) -> bytes:
    tries = 3
    for attempt in range(1, tries + 1):
        try:
            return adapter.perform_request(url, proxy, logger, timeout, headers, method, body)
        except HTTPBadRequestException as er:
            # Specific error; do not retry
            if logger:
                logger.error(f"HTTP 400 Bad Request: {er}")
            raise
        except (HTTPErrorException, Exception) as er:
            if logger:
                logger.error(f"Attempt {attempt} failed: {er}")
            if attempt == tries:
                raise TimeoutException(f"Failed to make request after {tries} attempts") from er
            else:
                if logger:
                    logger.debug(f"Retrying... (Attempt {attempt + 1} of {tries})")


def make_request_with_proxy(
    url: str,
    url_proxy: ProxyHandling,
    logger: Optional[object],
    adapter: RequestAdapter,
    timeout: int,
    headers: Optional[dict] = None,
    method: str = "GET",
    body: Union[Dict, bytes, None] = None,
) -> bytes:
    tries_per_proxy = 3
    tries_for_proxies = 5

    for _ in range(tries_for_proxies):
        proxies = url_proxy.load_proxies()
        if not proxies:
            break
        proxy = proxies.pop().strip()

        if logger:
            logger.debug(f"Using proxy {proxy}")

        for attempt in range(1, tries_per_proxy + 1):
            try:
                return adapter.perform_request(url, proxy, logger, timeout, headers, method, body)
            except HTTPBadRequestException as er:
                # Specific error; do not retry
                if logger:
                    logger.error(f"HTTP 400 Bad Request: {er}")
                raise
            except (HTTPErrorException, Exception) as er:
                if logger:
                    logger.error(f"Attempt {attempt} with proxy {proxy} failed: {er}")
                if attempt == tries_per_proxy:
                    # Remove the non-working proxy after failed attempts
                    proxies_remaining = url_proxy.get_proxies()
                    if proxy in proxies_remaining:
                        proxies_remaining.remove(proxy)
                        url_proxy.dump_proxies(proxies_remaining)
                    if logger:
                        logger.debug(f"Removing proxy {proxy} after {tries_per_proxy} failed attempts")
                else:
                    if logger:
                        logger.debug(f"Retrying with proxy {proxy}... (Attempt {attempt + 1} of {tries_per_proxy})")
    if logger:
        logger.error("Unable to make request via any proxy")
    raise TimeoutException("Failed to make request after using all proxies")
