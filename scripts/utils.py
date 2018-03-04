from __future__ import division
import proxy_handling
import urllib2

# Try to send request through a TOR
# try:
#     import socks  # SocksiPy module
#     import socket
#     SOCKS_PORT = 9150 # 9050
#     def create_connection(address, timeout=None, source_address=None):
#         sock = socks.socksocket()
#         sock.connect(address)
#         return sock
#     socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", SOCKS_PORT)
#     socket.socket = socks.socksocket
#     socket.create_connection = create_connection
#     print("WITH PROXY")
# except:
#     pass

import socket
# import urllib
import math
from logger import logger 


def y2lat(y):
    return (2 * math.atan(math.exp(y / 6378137)) - math.pi / 2) / (math.pi / 180)


def x2lon(x):
    return x / (math.pi / 180.0) / 6378137.0


def xy2lonlat(x, y):
    return [x2lon(x), y2lat(y)]


USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'


class TimeoutException(Exception):
    pass

# def make_request(url):
#     try:
#         url = url.encode('utf-8')
#         logger.debug(url)
#         resp = urllib.urlopen(url)
#         read = resp.read()
#         return read
#     except Exception as er:
#         logger.info(url)
#         logger.error(er)


# def make_request(url):
#     import pycurl
#     from StringIO import StringIO

#     buffer = StringIO()
#     c = pycurl.Curl()
#     c.setopt(c.URL, url)
#     c.setopt(c.WRITEDATA, buffer)
#     c.perform()
#     c.close()

#     body = buffer.getvalue()
#     # Body is a string in some encoding.
#     # In Python 2, we can print it without knowing what the encoding is.
#     print(body)
#     return body


def make_request(url):
    # original function
    if url:
        url = url.encode('utf-8')
        logger.debug(url)
        proxies = proxy_handling.load_proxies_from_file()
        if proxies == None or (len(proxies) != 0 and proxies[0] == 'None'):
            try:
                f = urllib2.urlopen(url)
                read = f.read()
                return read
            except Exception as er:
                logger.warning(er)
                raise TimeoutException()
        else:
            return make_request_with_proxy(url)
    return False


def make_request_with_proxy(url):
    while True:
        proxies = proxy_handling.load_proxies_from_file()
        if not proxies:
            proxy_handling.update_proxies()
            proxies = proxy_handling.load_proxies_from_file()
        removed = False
        tries = 3  # number of tries for each proxy
        for proxy in proxies:
            for i in range(1, tries+1):  # how many tries for each proxy
                try:
                    print('%i iteration of proxy %s' % (i, proxy))
                    proxy_handler = urllib2.ProxyHandler({'http': proxy, 'https': proxy})
                    opener = urllib2.build_opener(proxy_handler)
                    urllib2.install_opener(opener)
                    headers = {
                        'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36',
                        'referer': 'htpps://www.google.com/'}
                    request = urllib2.Request(url, headers=headers)
                    f = urllib2.urlopen(request)
                    read = f.read()
                    return read
                except Exception as er:
                    logger.warning(er)
                if i == tries:
                    proxies.remove(proxy)
                    removed = True
        if removed:
            proxy_handling.dump_proxies_to_file(proxies)
    return False
