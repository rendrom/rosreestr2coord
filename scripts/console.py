#!/usr/bin/env python
# coding: utf-8
from __future__ import print_function, division

import re
import os
import signal
import time
import sys

from scripts.batch import batch_parser
from scripts.parser import Area, TYPES

def getopts():
    import argparse
    import textwrap

    """
    Get the command line options.
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""\
        Get geojson with coordinates of area by cadastral number.
        https://pkk5.rosreestr.ru/
        """)
    )
    parser.add_argument('-c', '--code', action='store', type=str, required=False,
                        help='area cadastral number')
    parser.add_argument('-t', '--area_type', action='store', type=int, required=False, default=1,
                        help='area types: %s' % "; ".join(["%s:%s" % (k, v) for k, v in TYPES.items()]))
    parser.add_argument('-p', '--path', action='store', type=str, required=False,
                        help='media path')
    parser.add_argument('-o', '--output', action='store', type=str, required=False,
                        help='output path')
    parser.add_argument('-w', '--wgs', action='store_const', const=True, required=False,
                        help='use WGS84 coordinate system')
    parser.add_argument('-l', '--list', action='store', type=str, required=False,
                        help='path of file with cadastral codes list')
    parser.add_argument('-a', '--attrs', action='store_const', const=True, required=False,
                        help='insert the area attributes in the geojson output')
    parser.add_argument('-d', '--display', action='store_const', const=True, required=False,
                        help='display plot (only for --code mode)')
    parser.add_argument('-D', '--delay', action='store', type=int, required=False, default=1,
                        help='delay between request (only for --list mode)')
    parser.add_argument('-r', '--refresh', action='store_const', const=True, required=False,
                        help='do not use catalog')
    # parser.add_argument('-x', '--csv', action='store_const', const=True, required=False,
    #                     help='create CSV table output, use only with --list')
    parser.add_argument('-e', '--epsilon', action='store', type=float, required=False, default=5,
                        help='Parameter specifying the approximation accuracy'
                             'This is the maximum distance between the original curve and its approximation. '
                             'Small value = hight detail = more points. '
                             '(default %(default).2f)')
    parser.add_argument('-C', '--center_only', action='store_const', const=True, required=False,
                        help='Use only the center of area')
    parser.add_argument('-P', '--proxy', action='store_const', const=True, required=False,
                        help='use proxies')
    opts = parser.parse_args()

    return opts


def _main():

    # area = Area("38:36:000021:1106")
    # area = Area("38:06:144003:4723")
    # area = Area("38:36:000033:375")
    # area = Area("38:06:143519:6153", area_type=5)
    # 47:16:0650002:317  # multipolygon

    # code, output, path, epsilon, area_type = "38:06:144003:4723", "", "", 5, 1)

    opt = getopts()
    code = opt.code
    output = opt.output if opt.output else os.path.join("output")
    delay = getattr(opt, "delay", 1000)
    path = opt.path
    epsilon = opt.epsilon if opt.epsilon else 5
    area_type = opt.area_type if opt.area_type else 1
    with_attrs = opt.attrs if opt.attrs else False
    center_only = opt.center_only if opt.center_only else False
    refresh = opt.refresh
    display = opt.display
    coord_out = "EPSG:4326" if opt.wgs else "EPSG:3857"
    # csv = opt.csv
    catalog_path = "" if refresh else os.path.join(os.getcwd(), "catalog.json")
    if opt.list:
        file_name = os.path.splitext(os.path.basename(opt.list))[0]
        f = open(opt.list, 'r')
        codes = f.readlines()
        # cadastral number like this 02:00:000000 is not valid
        # def code_filter(c):
        #     s = re.search('^\d\d:\d+:[0]+', c)
        #     return not s
        # codes = filter(code_filter, codes)
        f.close()
        batch_parser(codes, media_path=path, area_type=area_type, catalog_path=catalog_path, coord_out=coord_out,
                     output=output, file_name=file_name, with_attrs=with_attrs, delay=delay, center_only=center_only, with_proxy=opt.proxy)

    elif code:
        get_by_code(code, path, area_type, catalog_path, with_attrs, epsilon, coord_out, output, display, center_only, with_proxy=opt.proxy)


def get_by_code(code, path, area_type, catalog_path, with_attrs=False, epsilon=5,
                coord_out='EPSG:3857', output="output", display=False, center_only=False, with_log=True, with_proxy=False):
    area = Area(code, media_path=path, area_type=area_type, epsilon=epsilon, with_log=with_log, catalog=catalog_path,
                coord_out=coord_out, center_only=center_only, with_proxy=with_proxy)
    abspath = os.path.abspath(output)
    geojson = area.to_geojson_poly(with_attrs=with_attrs)
    if geojson:
        filename = '%s.geojson' % area.file_name.replace(":", "_")
        geojson_path = os.path.join(abspath, "geojson")
        if not os.path.isdir(geojson_path):
            os.makedirs(geojson_path)
        file_path = os.path.join(geojson_path, filename)
        f = open(file_path, 'w')
        f.write(geojson)
        f.close()
        print(file_path)
        if display:
            area.show_plot()
    return area


def main():
    def signal_handler(signal, frame):
        print('You pressed Ctrl+C')
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)
    print('Press Ctrl+C to exit')
    
    _main()



if __name__ == "__main__":
    main()

