#!/usr/bin/env python
from __future__ import division

import json
import os
import copy

from PyQt4 import QtCore, QtGui, QtWebKit

from scripts.console import get_by_code
from scripts.export import coords2geojson

_client_dist = os.path.join(*['gui', 'client', 'dist'])

# 38:6:144003:4723


class MainWindow(QtGui.QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi()
        self.show()
        self.raise_()

    def setupUi(self):
        vbox = QtGui.QVBoxLayout()
        # self.setFixedSize(800, 500)
        self.setWindowTitle("ROSREESTR2COORD")
        # self.setWindowIcon(QtGui.QIcon('r2c.ico'))
        self.setLayout(vbox)

        view = self.view = QtWebKit.QWebView()
        view.page().mainFrame().addToJavaScriptWindowObject("MainWindow", self)
        view.load(QtCore.QUrl(os.path.join(_client_dist, 'index.html')))
        view.loadFinished.connect(self.onLoadFinished)
        vbox.addWidget(view)

    def onLoadFinished(self):
        frame = self.view.page().mainFrame()

        def load_script(scr):
            with open(scr, 'r') as f:
                frame.evaluateJavaScript(f.read())

        map(load_script, [
            os.path.join(_client_dist, 'polyfills.js'),
            os.path.join(_client_dist, 'vendor.js'),
            os.path.join(_client_dist, 'app.js')
        ])

    @QtCore.pyqtSlot(str)
    def onSearchClick(self, code, area_type=1):
        code = str(code)
        print(code)
        area = get_by_code(code, path="", area_type=area_type, catalog_path="", with_attrs=False, epsilon=5,
                coord_out='EPSG:4326', output="output", display=False, with_log=True)

        data = {"code": code, "area_type": area_type}

        xy = area.get_coord()
        if len(xy) and len(xy[0]):
            data["coordinates"] = copy.deepcopy(xy)
            if area.center:
                data["center_pkk"] = area.center
            attrs = area.get_attrs()
            if attrs:
                data["attrs"] = attrs

            geojson_poly = coords2geojson(data["coordinates"], "polygon", area.coord_out)
            if geojson_poly:
                data["geojson"] = json.dumps(geojson_poly)

        self.onSearchResult(data)

    def onSearchResult(self, data):
        frame = self.view.page().mainFrame()
        data = json.dumps(data)
        frame.evaluateJavaScript('window.onSearchResult({});'.format(data))


if __name__ == '__main__':
    app = QtGui.QApplication([])
    w = MainWindow()
    app.exec_()
