# coding: utf-8

import os

from scripts.console import get_by_code

if os.path.isfile(os.path.join(os.getcwd(), "tests_area.py")):
    BASE_PATH = os.getcwd()
else:
    BASE_PATH = os.path.join(os.getcwd(), "tests")


def main():
    multipolygon_with_holes()


def multipolygon_with_holes():
    code, path, epsilon, area_type = "47:16:0650002:317", "", 5, 1
    output = os.path.join(BASE_PATH, "output")
    return get_by_code(code, path, area_type, with_attrs=False, epsilon=5, output=output, display=False, with_log=True)


if __name__ == "__main__":
    main()
