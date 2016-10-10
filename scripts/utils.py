from __future__ import division
import math


def y2lat(y):
    return (2 * math.atan(math.exp(y / 6378137)) - math.pi / 2) / (math.pi / 180)


def x2lon(x):
    return x / (math.pi / 180.0) / 6378137.0


def xy2lonlat(x, y):
    return [x2lon(x), y2lat(y)]
