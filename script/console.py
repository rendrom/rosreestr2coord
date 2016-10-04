# coding: utf-8
from __future__ import print_function, division

import os

from script.parser import Area, TYPES


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
        http://pkk5.rosreestr.ru/
        """)
    )
    parser.add_argument('-c', '--code', action='store', type=str, required=True,
                        help='area cadastral number')
    parser.add_argument('-t', '--area_type', action='store', type=int, required=False, default=1,
                        help='area types: %s' % "; ".join(["%s:%s" % (k, v) for k, v in TYPES.items()]))
    parser.add_argument('-p', '--path', action='store', type=str, required=False,
                        help='media path')
    parser.add_argument('-o', '--output', action='store', type=str, required=False,
                        help='output path')
    parser.add_argument('-e', '--epsilon', action='store', type=int, required=False,
                        help='Parameter specifying the approximation accuracy. '
                             'This is the maximum distance between the original curve and its approximation.')
    opts = parser.parse_args()

    return opts


def main():
    # area = Area("38:36:000021:1106")
    # area = Area("38:06:144003:4723")
    # area = Area("38:36:000033:375")
    # area = Area("38:06:143519:6153", area_type=5)

    # code, output, path, epsilon, area_type = "38:06:144003:4723", "", "", 5, 1)

    opt = getopts()
    code = opt.code
    output = opt.output if opt.output else os.path.join("output")
    path = opt.path
    epsilon = opt.epsilon if opt.epsilon else 5
    area_type = opt.area_type if opt.area_type else 1

    catalog_path = os.path.join(os.getcwd(), "catalog.json")

    abspath = os.path.abspath(output)
    if code:
        area = Area(code, media_path=path, area_type=area_type, epsilon=epsilon, with_log=True, catalog=catalog_path)
        geojson = area.to_geojson_poly()
        if geojson:
            filename = '%s.geojson' % area.file_name
            geojson_path = os.path.join(abspath, "geojson")
            if not os.path.isdir(geojson_path):
                os.makedirs(geojson_path)
            file_path = os.path.join(geojson_path, filename)
            f = open(file_path, 'w')
            f.write(geojson)
            f.close()
            print(file_path)


if __name__ == "__main__":
    main()
