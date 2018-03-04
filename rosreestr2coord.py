#!/usr/bin/env python
from scripts.console import main
from scripts.parser import Area
if __name__ == "__main__":
    main()
    area = Area('21:01:010305:101')
    print(area.to_geojson_poly())