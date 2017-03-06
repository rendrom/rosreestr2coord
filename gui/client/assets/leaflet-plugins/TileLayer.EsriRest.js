import L from "leaflet";
/*
 * L.TileLayer.EsriRest is used for putting ESRI REST tile layers on the map.
 */


L.TileLayer.EsriRest = L.TileLayer.extend({

	defaultEsriParams: {
		layers: '',
		format: 'png',
		transparent: false,
        dpi: '92',
        f: 'image'
	},

	initialize: function (url, options) { // (String, Object)

		this._url = url;

		var esriParams = L.extend({}, this.defaultEsriParams),
		    tileSize = options.tileSize || this.options.tileSize;

		if (options.detectRetina && L.Browser.retina) {
            esriParams.size = [tileSize * 2, tileSize * 2].join(',');
		} else {
            esriParams.size = [tileSize, tileSize].join(',');
        }

		for (var i in options) {
			// all keys that are not TileLayer options go to ESRI params
			if (!this.options.hasOwnProperty(i)) {
				esriParams[i] = options[i];
			}
		}

		this.esriParams = esriParams;

		L.setOptions(this, options);
	},

	onAdd: function (map) {

		this.esriParams['bboxSR'] = map.options.crs.code.substring(5);
        this.esriParams['imageSR'] = map.options.crs.code.substring(5);
        this.esriParams['layers'] = "show:" + this.esriParams['layers'];

		L.TileLayer.prototype.onAdd.call(this, map);
	},

	getTileUrl: function (tilePoint, zoom) { // (Point, Number) -> String

		var map = this._map,
		    crs = map.options.crs,
		    tileSize = this.options.tileSize,

		    nwPoint = tilePoint.multiplyBy(tileSize),
		    sePoint = nwPoint.add([tileSize, tileSize]),

		    nw = crs.project(map.unproject(nwPoint, zoom)),
		    se = crs.project(map.unproject(sePoint, zoom)),

		    bbox = [nw.x, se.y, se.x, nw.y].join(','),

		    url = L.Util.template(this._url, {s: this._getSubdomain(tilePoint)});

		return url + '/export' + L.Util.getParamString(this.esriParams, url, true) + '&bbox=' + bbox;
	},

    getIdentifyUrl: function(point, params) {

        params = params ? params : {};

        var defaultIdentifyParams = {
            geometryType: 'esriGeometryPoint',
            sr: '4326',
            layers: this.esriParams['layers'].substring(5),
            tolerance: 0,
            imageDisplay: this.esriParams.size + ',' + this.esriParams.dpi,
            returnGeometry: false,
            f: 'pjson',
            geometry: [point.x, point.y].join(','),
            mapExtent: [map.getBounds()._northEast.lng, map.getBounds()._northEast.lat, map.getBounds()._southWest.lng, map.getBounds()._southWest.lat].join(','),
            showLayers: 'visible'
        };

        for (var i in defaultIdentifyParams) {
            // all keys that are not TileLayer options go to ESRI params
            if (!params.hasOwnProperty(i)) {
                params[i] = defaultIdentifyParams[i];
            }
        }

        params['layers'] = params['showLayers'] + ":" + params['layers'];

        url = L.Util.template(this._url, {s: this._getSubdomain(point)});
        return url + '/identify' + L.Util.getParamString(params, url, true);
    },

	setParams: function (params, noRedraw) {

		L.extend(this.esriParams, params);

		if (!noRedraw) {
			this.redraw();
		}

		return this;
	}
});

L.tileLayer.esri = function (url, options) {
	return new L.TileLayer.ESRI(url, options);
};/**
 * Created by artemiy on 08/09/16.
 */
