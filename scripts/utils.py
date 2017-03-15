from __future__ import division
import math
import urllib
from logger import logger 


def y2lat(y):
    return (2 * math.atan(math.exp(y / 6378137)) - math.pi / 2) / (math.pi / 180)


def x2lon(x):
    return x / (math.pi / 180.0) / 6378137.0


def xy2lonlat(x, y):
    return [x2lon(x), y2lat(y)]


USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'


def make_request(url):
    try:
        url = url.encode('utf-8')
        logger.debug(url)
        resp = urllib.urlopen(url)
        return resp.read()
    except Exception as er:
        logger.info(url)
        logger.error(er)



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

# def make_request(url):
#     import urllib2
#     logger.debug(url)
#     try:
#         f = urllib2.urlopen(url)
#         return f.read()
#     except Exception as er:
#         logger.warning(er)