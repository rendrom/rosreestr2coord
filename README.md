ROSREESTR TO COORDINATE
=======================
Инструмент, позволяющий получать координаты участка по его кадастровому номеру
Данные берутся с сайта публичной кадастровой карты [http://pkk5.rosreestr.ru/](http://pkk5.rosreestr.ru/)

[DEMO](http://geonote.ru/pkk/)

## Requirements

* Python 2.7.x
* [OpenCV](http://opencv.org/)

## Usage

from console (geojson output):

    python rosreestr2coord.py -c "38:06:144003:4723"
    
programmatically:
    
    from rosreestr2coord import Area
        
    area = Area("38:06:144003:4723")
    area.to_geojson()
    area.get_coord()
    area.get_attrs()

## TODO

* Попытаться устранить смещение координат. Возможно это смещение добавлено специально. Если вручную выносить точки участка на сайте http://pkk5.rosreestr.ru/, а затем экспортировать в KML, то результат будет идентичен координатам, полученным при помощи данного приложения.
* Увеличить точность распознования углов
* Рисовать полигон
* В полигоне находить отверстия
