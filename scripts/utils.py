from __future__ import division
import math
import urllib


def y2lat(y):
    return (2 * math.atan(math.exp(y / 6378137)) - math.pi / 2) / (math.pi / 180)


def x2lon(x):
    return x / (math.pi / 180.0) / 6378137.0


def xy2lonlat(x, y):
    return [x2lon(x), y2lat(y)]


def make_request(url):
    request = url
    # request = urllib2.Request(url, None, {'User-Agent': 'Mozilla/5.0'})
    try:
        return urllib.urlopen(request)
    # except urllib2.HTTPError, e:
    #     print('HTTPError = ' + str(e.code))
    # except urllib2.URLError, e:
    #     print('URLError = ' + str(e.reason))
    # except httplib.HTTPException, e:
    #     print('HTTPException')
    except Exception:
        # import traceback
        pass  # print('generic exception: ' + traceback.format_exc())