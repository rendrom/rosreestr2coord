// import * as proj4 from 'proj4'
import * as proj4 from 'proj4'
import './projCode/merc'
import './projCode/tmerc'
import './msk'
var projHash = {};

export function initProj4() {
    var crsDest = document.getElementById('crsDest');
    var optIndex = 0;
    for (var def in proj4.defs) {
        if (proj4.defs.hasOwnProperty(def)) {
            try {
                let proj = projHash[def];
                if (!proj) {
                    proj = projHash[def] = new proj4.Proj(def);
                }
                var label = def + " - " + (proj.title ? proj.title : '');
                crsDest.options[optIndex] = new Option(label, def);
                ++optIndex;
            } catch (er) {console.log(er);}
        }
    }
}

export function transform(point, crsDest, crsSource) {
    crsSource = crsSource || "EPSG:4326";
    if (crsSource !== crsDest) {
        var projSource = projHash[crsSource];
        var projDest = projHash[crsDest];
        if (projDest && projSource) {
            var pointSource = new proj4.Point(point);
            var pointDest = proj4.transform(projSource, projDest, pointSource);
            return [pointDest.x, pointDest.y];
        }
    } else {
        return point;
    }
    return false;
}
