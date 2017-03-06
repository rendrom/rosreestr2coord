import L from 'leaflet'
// import '../../assets/leaflet-plugins/TileLayer.EsriRest'

const OSM = L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 22
});

export default class {

    constructor(id) {
        this.id = id;
        this._map = null;
    };

    getMap() {
        if (!this._map) {
            this._map = this.build();
        }
        return this._map;
    }

    build() {
        let map = L.map(this.id, {
            layers: [OSM],
            center: [60, 100],
            zoom: 3,
            maxZoom: 22
        });

        L.tileLayer.wms("http://pkk5.rosreestr.ru/arcgis/services/Cadastre/CadastreWMS/MapServer/WmsServer", {
                layers: '24,23,22,21,20,19,18,16,15,14,13,12,11,10,9,7,6,5,2,1',
                subdomains: "abcd",
                format: 'image/png24',
                transparent: true,
                attribution: "РосРеестр",
                maxZoom: 22
            }).addTo(map);

        // if (L.TileLayer.EsriRest) {
        //
        //     new L.TileLayer.EsriRest("http://pkk5.rosreestr.ru/arcgis/rest/services/Cadastre/Cadastre/MapServer", {
        //         subdomains: "abcd",
        //         layers: '0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,21',
        //         transparent: true,
        //         maxZoom: 22
        //     }).addTo(map);
        // }
        return map
    }
}