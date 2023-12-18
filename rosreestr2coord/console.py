#!/usr/bin/env python
# coding: utf-8
import argparse
import importlib.metadata
import os
import signal
import sys

from rosreestr2coord.batch import batch_parser
from rosreestr2coord.parser import TYPES, Area
from rosreestr2coord.utils import code_to_filename

__version__ = importlib.metadata.version("rosreestr2coord")


def getopts():
    """
    Get the command line options.
    """
    parser = argparse.ArgumentParser(
        description="Get geojson with coordinates of area by cadastral number (based on https://pkk.rosreestr.ru)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("-c", "--code", type=str, help="area cadastral number")
    parser.add_argument(
        "-t", "--area_type", type=int, default=1, help=f"area types: {', '.join(f'{k}:{v}' for k, v in TYPES.items())}"
    )
    parser.add_argument("-p", "--path", type=str, help="media path")
    parser.add_argument("-o", "--output", type=str, default=os.path.join(os.getcwd(), "output"), help="output path")
    parser.add_argument("-l", "--list", type=str, help="path of file with cadastral codes list")
    parser.add_argument("-d", "--display", action="store_true", help="display plot (only for --code mode)")
    parser.add_argument("-D", "--delay", type=float, default=1, help="delay between requests (only for --list mode)")
    parser.add_argument("-r", "--refresh", action="store_true", help="do not use cache")
    parser.add_argument("-e", "--epsilon", type=float, default=5, help="approximation accuracy")
    parser.add_argument("-T", "--timeout", type=float, default=5, help="delay between requests")
    parser.add_argument("-C", "--center_only", action="store_true", help="use only the center of area")
    parser.add_argument("-P", "--proxy", action="store_true", help="use proxies")
    parser.add_argument("-v", "--version", action="store_true", help="show current version")
    parser.add_argument("-u", "--proxy_url", type=str, help="set proxy URL")
    return parser.parse_args()


def handle_batch_processing(file_path, output, delay, kwargs):
    with open(file_path, "r") as file:
        codes = file.readlines()
    file_name = os.path.splitext(os.path.basename(file_path))[0]
    batch_parser(codes, output=output, delay=delay, file_name=file_name, **kwargs)


def get_by_code(code, output, display, **kwargs):
    area = Area(code, **kwargs)
    abspath = os.path.abspath(output)
    process_area(area, abspath, display)
    return area


def process_area(area, output_path, display):
    geojson = area.to_geojson_poly()
    kml = area.to_kml()
    file_name = code_to_filename(area.file_name)

    if kml:
        save_file(kml, output_path, file_name, "kml")
    if geojson:
        save_file(geojson, output_path, file_name, "geojson")
    if display:
        area.show_plot()


def save_file(content, output_path, file_name, extension):
    directory = os.path.join(output_path, extension)
    os.makedirs(directory, exist_ok=True)
    file_path = os.path.join(directory, f"{file_name}.{extension}")
    if isinstance(content, str):
        with open(file_path, "w") as file:
            file.write(content)
    else:
        content.write(file_path, encoding="UTF-8", xml_declaration=True)
    print(f"{extension} - {file_path}")


def run_console(opt):
    kwargs = {
        "media_path": opt.path,
        "with_proxy": opt.proxy,
        "epsilon": opt.epsilon,
        "area_type": opt.area_type,
        "center_only": opt.center_only,
        "use_cache": not opt.refresh,
        "coord_out": "EPSG:4326",
        "proxy_url": opt.proxy_url,
    }

    if opt.list:
        handle_batch_processing(opt.list, opt.output, opt.delay, kwargs)
    elif opt.code:
        get_by_code(opt.code, opt.output, opt.display, **kwargs)


def console():
    opt = getopts()
    if opt.version:
        print(__version__)
        return

    def signal_handler(signalnum, frame):
        print("You pressed Ctrl+C")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    print("Press Ctrl+C to exit")

    run_console(opt)
