import os
from time import sleep

from rosreestr2coord.export import area_json_output, batch_csv_output, batch_json_output
from rosreestr2coord.parser import Area
from rosreestr2coord.utils import TimeoutException


def batch_parser(codes, with_log=False, file_name="example", areas=None,
                 output=os.path.join("output"), repeat=0, delay=1, **kwargs):
    """
    Print a list of - features.

    Args:
        codes: (todo): write your description
        with_log: (todo): write your description
        file_name: (str): write your description
        areas: (todo): write your description
        output: (todo): write your description
        os: (todo): write your description
        path: (str): write your description
        join: (todo): write your description
        repeat: (int): write your description
        delay: (todo): write your description
    """
    if areas is None:
        areas = []
    with_error = []
    with_no_coord = []
    success = 0
    print("================================")
    print("Launched parsing of %i areas:" % len(codes))
    print("================================")
    need_sleep = 0
    features = []
    for c in codes:
        area = None
        code = c.strip()
        print("%s" % code, end="")
        try:
            sleep(need_sleep)
            area = Area(code, with_log=with_log, **kwargs)
            need_sleep = delay
            if not (len(area.get_coord()) > 0):
                print(" - no coord", end="")
                with_no_coord.append(area)
            else:
                print(" - ok", end="")
                success += 1
        except TimeoutException:
            print(" - error")
            print("Your IP is probably blocked. Try later or use proxy")
            break
        except Exception:
            print(" - error", end="")
            with_error.append(code)

        percent = ((success + len(with_error) +
                    len(with_no_coord)) / len(codes)) * 100
        print(", %i%%" % percent)

        if area:
            areas.append(area)
            feature = area_json_output(output, area)
            if feature:
                features.append(feature)
            # area_csv_output(output, area)

    print("=================")
    print("Parsing complete:")
    print("  success     : %i" % success)
    print("  error       : %i" % len(with_error))
    print("  no_coord    : %i" % len(with_no_coord))
    print("-----------------")

    if len(with_error) and repeat:
        print("Retries parse areas with error")
        batch_parser(with_error, with_log=with_log, file_name=file_name,
                     repeat=repeat - 1, areas=areas, output=output,
                     delay=delay, **kwargs)
    else:
        path = batch_csv_output(output, areas, file_name)
        if len(with_no_coord):
            path = batch_csv_output(
                output, with_no_coord, "%s_no_coord" % file_name)
            print("Create output for no_coord complete: %s" % path)
        if len(features):
            path = batch_json_output(output, areas, file_name)
            print("Create output complete: %s" % path)
        if len(with_error):
            print("-----------------")
            print("Error list:")
            for e in with_error:
                print(e)
