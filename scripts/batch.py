from __future__ import print_function, division

import os

from scripts.catalog import Catalog
from scripts.export import area_json_output, area_csv_output, batch_csv_output
from scripts.parser import Area, restore_area


def batch_parser(codes, area_type=1, media_path="", with_log=False, catalog_path="", coord_out="EPSG:3857",
                 file_name="example", output=os.path.join("output"), repeat=5, areas=None, with_attrs=False):
    if areas is None:
        areas = []
    catalog = Catalog(catalog_path)
    restores = []
    with_error = []
    success = 0
    from_catalog = 0
    print("================================")
    print("Launched parsing of %i areas:" % len(codes))
    print("================================")
    for c in codes:
        code = c.strip()
        print("%s" % code, end="")
        restore = catalog.find(code)
        if not restore:
            try:
                area = Area(code, media_path=media_path, area_type=area_type, with_log=with_log, coord_out=coord_out)
                assert (len(area.get_coord()) > 0)
                restore = catalog.update(area)
                print(" - ok", end="")
                success += 1
            except Exception:
                area = None
                print(" - error", end="")
                with_error.append(code)
        else:
            print(" - ok, from catalog", end="")
            success += 1
            from_catalog += 1
            area = restore_area(restore, coord_out)
        percent = ((success + len(with_error)) / len(codes)) * 100
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
    print("  from catalog: %i" % from_catalog)
    print("-----------------")

    if len(with_error) and repeat:
        print("Retries parse areas with error")
        batch_parser(with_error, area_type=area_type, media_path=media_path, with_log=with_log, file_name=file_name,
                     catalog_path=catalog_path, coord_out=coord_out, repeat=repeat - 1, areas=areas, output=output)
    else:
        path = batch_csv_output(output, areas, file_name)
        print("Create output complete: %s" % path)
        if len(with_error):
            print("-----------------")
            print("Error list:")
            for e in with_error:
                print(e)
