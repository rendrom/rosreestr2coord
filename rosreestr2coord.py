#coding: utf-8
from __future__ import print_function, division
import json
import urllib
import os
try:
    import urlparse
    from urllib import urlencode
except: # For Python 3
    import urllib.parse as urlparse
    from urllib.parse import urlencode
    
##############
# SEARCH URL #
##############
# http://pkk5.rosreestr.ru/api/features/1
#   ?text=38:36:000021:1106
#   &tolerance=4
#   &limit=11
SEARCH_URL = "http://pkk5.rosreestr.ru/api/features/1"

############################
# URL to get area metainfo #
############################
# http://pkk5.rosreestr.ru/api/features/1/38:36:21:1106
META_URL = "http://pkk5.rosreestr.ru/api/features/1/"

#########################
# URL to get area image # 
#########################
# http://pkk5.rosreestr.ru/arcgis/rest/services/Cadastre/CadastreSelected/MapServer/export
#   ?dpi=96
#   &transparent=true
#   &format=png32
#   &layers=show%3A6%2C7
#   &bbox=11612029.005008286%2C6849457.6834302815%2C11612888.921576614%2C6849789.706771941
#   &bboxSR=102100
#   &imageSR=102100
#   &size=1440%2C556
#   &layerDefs=%7B%226%22%3A%22ID%20%3D%20%2738%3A36%3A21%3A1106%27%22%2C%227%22%3A%22ID%20%3D%20%2738%3A36%3A21%3A1106%27%22%7D
#   &f=image
# WHERE:
#    "layerDefs" decode to {"6":"ID = '38:36:21:1106'","7":"ID = '38:36:21:1106'"}
#    "f" may be `json`
IMAGE_URL = "http://pkk5.rosreestr.ru/arcgis/rest/services/Cadastre/CadastreSelected/MapServer/export"

class Area:
    media_path = ""
    buffer = 10
    
    def __init__(self, code):
        if not self.media_path:
            self.media_path = os.path.dirname(os.path.realpath(__file__))
        if not os.path.isdir(self.media_path):
            raise Exception("media_path is not set correct")
        self.code = code
        self.file_name = self.code.replace(":", "-")
        search_data = self.search()
        if search_data:
            self.image_url = self.get_image_url()
        if self.image_url:
            image = self.get_image()
            if image:
                image_xy_corner = self.get_image_xy_corner()
                if image_xy_corner:
                    self.xy = xy_coord = self.image_corners_to_coord()
                    # self.show_plot(image_xy_corner)

    
    def to_geojson(self):
        if self.xy:
            features = []
            object = {
                "type": "FeatureCollection", 
                "crs":{"type":"name","properties":{"name":"EPSG:3857"}},
                "features": features
                }           
            for x,y in self.xy:
                feature = {"type":"Feature", "geometry":{"type": "Point", "coordinates": [x,y]}}
                features.append(feature);
            return json.dumps(object)
        return False
            
                                  
    def get_image_url(self, format="image"):
        if self.code_id and self.extent:
            #extent_list = self.get_extent_list(self.extent)
            ex = self.get_buffer_extent_list()
            dx, dy = map(lambda i: int((ex[i[0]]-ex[i[1]])*5), [[2,0], [3,1]])
            self.width = dx
            self.height = dy
            code = self.code_id
            layers = ["6","7"]
            params = {
                "dpi": 96,
                "transperant": False,
                "format": "png32",
                "layers": "show:%s" % ",".join(layers),
                "bbox": ",".join(map(str, ex)),
                "bboxSR": 102100,
                "imageSR": 102100, 
                "size": "%s,%s" % (dx,dy),
                "layerDefs": {layer: str("ID = '%s'" % code) for layer in layers},
                "f": format
            }
            url_parts = list(urlparse.urlparse(IMAGE_URL))
            query = dict(urlparse.parse_qsl(url_parts[4]))
            query.update(params)
            url_parts[4] = urlencode(query)
            image_url = urlparse.urlunparse(url_parts)
            # print(image_url)
            return image_url
        return False
        
        
    def get_image(self):
        try:
            image_file = urllib.URLopener()
            basedir = self.media_path
            savedir = os.path.join(basedir, "tmp")
            if not os.path.isdir(savedir):
                os.makedirs(savedir)
            file_path = os.path.join(savedir, "%s.png" % self.file_name)
            image_file.retrieve(self.image_url, file_path)
            self.image_path = file_path
            return image_file    
        except Exception:
            print("Nothing found")
        return False


    def get_meta_url(self):
        return urlparse.urljoin(META_URL + prepare_code(self.code_id)) 
        
    @staticmethod
    def get_extent_list(extent):
        return [extent["xmin"], extent["ymin"], extent["xmax"], extent["ymax"]]
    

    def get_buffer_extent_list(self):
        ex = self.extent
        buf = self.buffer
        ex = [ex["xmin"] - buf, ex["ymin"] - buf, ex["xmax"] + buf, ex["ymax"] + buf]
        return ex

    def search(self):
        try:
            search_data = self.get_search_result()
            if search_data:
                features = search_data["features"]
                if features and len(features):
                    area = features[0]
                    attrs = area["attrs"]
                    if attrs["cn"] == self.code:
                        self.code_id = attrs["id"]
                        self.extent = area["extent"]
                        self.center = area["center"]
                        return search_data
        except Exception:
            pass
        print("Nothing found")
        return False
    
    
    def get_search_result(self):
        search_url = SEARCH_URL + "?text=%s&tolerance=4&limit=1" % self.code
        response = urllib.urlopen(search_url)
        data = json.loads(response.read())
        return data
        
        
    def get_image_xy_corner(self):
        import numpy as np
        import cv2    
        # from matplotlib import pyplot as plt
        
        image_xy_corners = []
        img = cv2.imread(self.image_path)  
        gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
        #gray = cv2.medianBlur(gray,5)        
        try:         
            corners = cv2.goodFeaturesToTrack(gray,100,0.01,1, useHarrisDetector=True)
            corners = np.int0(corners)
            for i in corners:
                x,y = i.ravel()
                image_xy_corners.append([x,y])
            self.image_xy_corners = image_xy_corners
            return image_xy_corners
        except Exception as ex:
            print(ex)
        return image_xy_corners
            
            
    def image_corners_to_coord(self):
        ex = self.get_buffer_extent_list()
        dx = ((ex[2] - ex[0]) / self.width)
        dy = ((ex[3] - ex[1]) / self.height)
        xy_corners = []
        for im_x, im_y in self.image_xy_corners:
            x = ex[0] + (im_x * dx)
            y = ex[3] - (im_y * dy)
            xy_corners.append([x,y])
        return xy_corners
                
            
            
    def show_plot(self, corners):
        import cv2
        from matplotlib import pyplot as plt
        
        img = cv2.imread(self.image_path)
        for x,y in corners:
            cv2.circle(img,(x,y),3,255,-1)
        plt.imshow(img),plt.show()
        

def getopts():
    import argparse
    import textwrap
    """
    Get the command line options.
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""\
        Get geojson with coordinates of area by cadastral number.
        http://pkk5.rosreestr.ru/
        """)
    )
    parser.add_argument('-c', '--code', action='store', type=str, required=True,
                        help='area cadastral number')

    opts = parser.parse_args()

    return opts
        
    
if __name__ == "__main__":
    # area = Area("38:36:000021:1106")
    # area = Area("38:06:144003:4723")
    abspath = os.path.abspath('.')
    opt = getopts()
    if opt.code:
        area = Area(opt.code)
        geojson = area.to_geojson()
        if geojson:
            filename = '%s.geojson' % area.file_name
            f = open(filename ,'w')
            f.write(geojson)
            f.close()
            print(os.path.join(abspath,filename))
        
    