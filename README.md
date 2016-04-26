ROSREESTR TO COORDINATE
=======================
Инструмент, позволяющий получать координаты участка по его кадастровому номеру
Данные берутся с сайта публичной кадастровой карты [http://pkk5.rosreestr.ru/](http://pkk5.rosreestr.ru/)

# Requirements

*Python 2.7.x
*[OpenCV](http://opencv.org/)

# Usage

from console (geojson output):
    python rosreestr2coord -c "38:06:144003:4723"
    
programmatically:
    from rosreestr2coord import Area
    
    area = Area("38:06:144003:4723")
    area.to_geojson()
    area.xy