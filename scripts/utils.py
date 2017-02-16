from __future__ import division
import math
import urllib


def y2lat(y):
    return (2 * math.atan(math.exp(y / 6378137)) - math.pi / 2) / (math.pi / 180)


def x2lon(x):
    return x / (math.pi / 180.0) / 6378137.0


def xy2lonlat(x, y):
    return [x2lon(x), y2lat(y)]


USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'



def make_request(url):
    import pycurl
    from StringIO import StringIO

    buffer = StringIO()
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    c.setopt(c.WRITEDATA, buffer)
    c.perform()
    c.close()

    body = buffer.getvalue()
    # Body is a string in some encoding.
    # In Python 2, we can print it without knowing what the encoding is.
    print(body)
    return body

# def make_request(url):
#     request = url
#     # request = urllib2.Request(url, None, {'User-Agent': USER_AGENT})
#     try:
#         return urllib.urlopen(request)
#     # except urllib2.HTTPError, e:
#     #     print('HTTPError = ' + str(e.code))
#     # except urllib2.URLError, e:
#     #     print('URLError = ' + str(e.reason))
#     # except httplib.HTTPException, e:
#     #     print('HTTPException')
#     except Exception:
#         # import traceback
#         pass  # print('generic exception: ' + traceback.format_exc())