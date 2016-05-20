ROSREESTR TO COORDINATE
=======================
Инструмент, позволяющий получать координаты участка по его кадастровому номеру
Данные берутся с сайта публичной кадастровой карты [http://pkk5.rosreestr.ru/](http://pkk5.rosreestr.ru/)

[DEMO](http://geonote.ru/pkk/)

## Requirements

* Python 2.7.x
* [OpenCV](http://opencv.org/) (опционально, для png)

## Usage

Из консоли:

    python rosreestr2coord.py -c 38:06:144003:4723
    
Опции:

  -h - справка
  -c - кадастровый номер
  -p - путь для промежуточных файлов
  -o - путь для полученого geojson файла
    
programmatically:
    
    from rosreestr2coord import Area
        
    area = Area("38:06:144003:4723") # media-path=MEDIA
    area.to_geojson()
    area.to_geojson_poly()
    area.get_coord() # [x,y] - только координаты участка
    area.get_holes() # [[h1_x,h2_y], [h2_x, h2_y]] - кординаты отверстий, если есть
    area.get_attrs()

## TODO

* ~~Рисовать полигон~~ по SVG
* ~~В полигоне находить отверстия~~ по SVG
* ~~Увеличить точность распознования углов~~ Увеличино за счёт обработки SVG
