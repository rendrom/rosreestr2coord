from __future__ import print_function
from script.catalog import Catalog
from script.parser import Area


def batch_parser(codes, area_type=1, media_path="", with_log=False, catalog=""):
    catalog = Catalog(catalog)
    restores = []
    with_error = 0
    success = 0
    from_catalog = 0
    print("Launched parsing of of %i areas:" % len(codes))
    print("================================")
    for c in codes:
        code = c.strip()
        print("%s" % code, end="")
        restore = catalog.find(code)
        if not restore:
            try:
                area = Area(code, media_path=media_path, area_type=area_type, with_log=with_log)
                restore = catalog.update(area)
                print(" - ok")
                success += 1
            except Exception as er:
                print(" - error")
                with_error += 1
                pass
        else:
            print(" - ok, from catalog")
            success += 1
            from_catalog += 1
        restores.append(restore)
    catalog.close()

    print("=================")
    print("Parsing complate:")
    print("  success     : %i" % success)
    print("  error       : %i" % with_error)
    print("  from catalog: %i" % from_catalog)
    print("-----------------")
