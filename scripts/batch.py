from __future__ import print_function, division

import os
from time import sleep
from scripts.catalog import Catalog
from scripts.export import area_json_output, area_csv_output, batch_csv_output
from scripts.parser import Area, restore_area, NoCoordinatesException
from scripts.utils import TimeoutException


def batch_parser(codes, area_type=1, media_path="", with_log=False, catalog_path="", coord_out="EPSG:3857",
                 file_name="example", output=os.path.join("output"), repeat=0, areas=None, with_attrs=False, delay=1):
    if areas is None:
        areas = []
    catalog = Catalog(catalog_path)
    restores = []
    with_error = []
    with_no_coord = []
    success = 0
    from_catalog = 0
    print("================================")
    print("Launched parsing of %i areas:" % len(codes))
    print("================================")
    need_sleep = 0
    for c in codes:
        area = None
        code = c.strip()
        print("%s" % code, end="")
        restore = catalog.find(code)
        if not restore:
            try:
                sleep(need_sleep)
                area = Area(code, media_path=media_path, area_type=area_type, with_log=with_log, coord_out=coord_out)
                need_sleep = delay
                restore = catalog.refresh(area)
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

            except Exception as er:
                print(" - error", end="")
                with_error.append(code)
        else:
            from_catalog += 1
            area = restore_area(restore, coord_out)
            if restore["image_path"]:
                print(" - ok, from catalog", end="")
                success += 1
            else:
                print(" - no_coord, from catalog", end="")
                with_no_coord.append(area)
        percent = ((success + len(with_error) + len(with_no_coord)) / len(codes)) * 100
        print(", %i%%" % percent)
        restores.append(restore)

        if area:
            areas.append(area)
            area_json_output(output, area, with_attrs)
            area_csv_output(output, area)

    catalog.close()

    print("=================")
    print("Parsing complate:")
    print("  success     : %i" % success)
    print("  error       : %i" % len(with_error))
    print("  no_coord    : %i" % len(with_no_coord))
    print("  from catalog: %i" % from_catalog)
    print("-----------------")

    if len(with_error) and repeat:
        print("Retries parse areas with error")
        batch_parser(with_error, area_type=area_type, media_path=media_path, with_log=with_log, file_name=file_name,
                     catalog_path=catalog_path, coord_out=coord_out, repeat=repeat - 1, areas=areas, output=output, delay=delay)
    else:
        path = batch_csv_output(output, areas, file_name)
        print("Create output complete: %s" % path)
        if len(with_no_coord):
            path = batch_csv_output(output, with_no_coord, "%s_no_coord" % file_name)
            print("Create output for no_coord complete: %s" % path)
        if len(with_error):
            print("-----------------")
            print("Error list:")
            for e in with_error:
                print(e)
