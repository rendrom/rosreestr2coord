import L from "leaflet";
import "leaflet-draw";
import {initProj4, transform} from "../../assets/msk2wgs";
import {getJSON} from "../services/Request";
import Mapster from "../services/Mapster";
import {AreaTypes} from "./page-builder";
import {serializeUrlParam} from "../utils";


let mapster = new Mapster('map');
let map = mapster.getMap();


let input = document.getElementById("area-code-input");
let goBtn = document.getElementById("get-area");
let coordSelect = document.getElementById("coord-select");
let coordOptions = document.getElementById("coord-options");
let coordsList = document.getElementById("coords-list");
let infoBlock = document.getElementById("info");
let btnDefVal = goBtn.innerHTML;
let getLink = document.getElementById("get-link");
let mapClickModeBtn = document.getElementById("map-click-mode");

let mapClickModeOn = false;

let types = new AreaTypes();

let code = input.value;

let LIST_WITH_GEODESY = false;

let COORD_DECIMAL = 6;

let POINT_ID = 0;

let featureGroup = new L.FeatureGroup();
featureGroup.addTo(map);

let icon = L.divIcon({
    iconAnchor: [10, 10],
    className: "ico",
    html: "<div class='div-icon div-ico-new'>&#215;</div>"
});


let options = {
    position: 'topright',
    draw: {
        polyline: false,
        polygon: false,
        circle: false, // Turns off this drawing tool
        rectangle: false,
        marker: {
            icon: icon
        }
    },
    edit: {
        featureGroup: featureGroup,
        remove: true
    }

};

let drawControl = new L.Control.Draw(options);

let startLoading = function () {
    clear();
    stopDraw();
    goBtn.innerHTML = "Загрузка...";
    goBtn.classList.add("disabled");
    map._container.style.cursor = "wait";
};
let stopLoading = function () {
    goBtn.innerHTML = btnDefVal;
    goBtn.classList.remove("disabled");
    setMapCursor();
};

let stopDraw = function () {
    if (drawControl._map) {
        map.removeControl(drawControl);
    }
    map.off('draw:created', onDrawCreated);
    map.off('draw:deletestop', onDrawDeleteStop);
    map.off('draw:editstop', onDrawEditStop);
};

let startDraw = function () {
    map.addControl(drawControl);
    map.on('draw:created', onDrawCreated);
    map.on('draw:deletestop', onDrawDeleteStop);
    map.on('draw:editstop', onDrawEditStop);
};

let onDrawCreated = function (e) {
    let type = e.layerType,
        layer = e.layer;

    if (type === 'marker') {
        let latlng = layer.getLatLng();
        let newCoord = [latlng.lng, latlng.lat];
        let num = prompt("Укажите номер новой точки", "" + (POINT_ID + 1));
        num = parseInt(num);
        if (num) {
            let cords = getMarkers().map(p => [p.x, p.y]);
            if (num <= cords.length) {
                cords.splice(parseInt(num), 0, newCoord);
                redrawMarkers(cords);
            } else {
                createMarkerFromCoord(newCoord);
            }
        } else {
            createMarkerFromCoord(newCoord);
        }
        changeCoord();
    }
};

let onDrawDeleteStop = function () {
    redrawMarkers();
    changeCoord();
};
let onDrawEditStop = function () {
    changeCoord();
};

let createMarkerFromCoord = function (coord, type) {
    let num = POINT_ID++;
    let icon = L.divIcon({
        iconSize: [28, 28],
        iconAnchor: [10, 10],
        className: "ico",
        html: "<div class='div-icon " + type + "'>&#215;" +
        "</div><div class='ico-label " + type + "'>" + num + "</div>"
    });
    let marker = L.marker([coord[1], coord[0]], {icon: icon});
    marker.num = coord[2] || num;
    marker.type = type;
    marker.bindPopup(num + ": " + coord[1] + " " + coord[0]);
    featureGroup.addLayer(marker);
    return marker;
};

let redrawMarkers = function (coords) {
    POINT_ID = 0;
    coords = coords || getMarkers().map(p => [p.x, p.y]);
    featureGroup.clearLayers();
    drawMarkers(coords);
};

let drawMarkers = function (coords) {
    let area = [];
    let holes = [];
    for (let fry = 0; fry < coords.length; fry++) {
        let coord = coords[fry];
        let xy = [coord[0], coord[1]];
        if (coord.type) {
            holes.push(xy);
        } else {
            area.push(xy);
        }
    }
    createMarkers(area);
    createHoleMarkers(holes);
};

let createMarkers = function (coordinates, type) {
    // POINT_ID = 0;
    for (let fry = 0; fry < coordinates.length; fry++) {
        createMarkerFromCoord(coordinates[fry], type);
    }
};

let createHoleMarkers = function (coords) {
    createMarkers(coords, "hole");
};

let getMarkers = function () {
    return featureGroup.getLayers().filter(p => p.getLatLng).map((p) => {
        return {
            x: p.getLatLng().lng,
            y: p.getLatLng().lat,
            num: p.num,
            type: p.type
        };
    });
};

let getMarkerByNum = function (num) {
    return featureGroup.getLayers().find(x => x.num === num);
};

let showCoordList = function (markers) {
    coordsList.innerHTML = "";
    markers = markers || getMarkers();
    let prevCoord = null;
    for (let fry = 0; fry < markers.length; fry++) {
        let coord = markers[fry];
        let li = createCoordListItem(prevCoord, coord);
        coordsList.appendChild(li);
        prevCoord = coord;
    }
    // Close item = first item
    let closeLi = createCoordListItem(prevCoord, markers[0]);
    coordsList.appendChild(closeLi);
};

let createCoordListItem = function (prevCoord, coord) {
    let li = document.createElement("li");
    li.className = "selection list-group-item coords-list-item";
    if (coord.type) {
        li.className += " " + coord.type;
    }
    li.innerHTML = coord.num + ": " +
        parseFloat(coord.y).toFixed(COORD_DECIMAL) + " " +
        parseFloat(coord.x).toFixed(COORD_DECIMAL);
    li.onclick = function () {
        let marker = getMarkerByNum(coord.num);
        map.setView(marker.getLatLng(), 20, {animate: true});

    };
    if (prevCoord && LIST_WITH_GEODESY) {
        let transformed = transformCoord(prevCoord, coord);
        let trans_ex = transformed[0];
        let trans_to = transformed[1];
        let x1 = trans_ex[0],
            y1 = trans_ex[1],
            x2 = trans_to[0],
            y2 = trans_to[1];
        let gdzLi = document.createElement("li");
        gdzLi.className = "list-group-item gdz-list";
        //let distance = calculateDistance(y1,x1, y2, x2);
        let prevLatLng = getLatLngFromMarker(getMarkerByNum(prevCoord.num));
        let distance = prevLatLng.distanceTo(getLatLngFromMarker(getMarkerByNum(coord.num)));
        if (distance) {
            let distElement = document.createElement("span");
            distElement.className = "gzn-list-item";
            distElement.innerHTML = "d: " + distance.toFixed(2) + "м";
            gdzLi.appendChild(distElement);
        }
        let gzn = calculateGzn(y1, x1, y2, x2, coord.num, prevCoord.num);
        //let gzn = calculateGzn(prevCoord.y, prevCoord.x, coord.y, coord.x);
        //let gzn = checkGzn(coord.y - prevCoord.y, coord.x - prevCoord.x);
        if (gzn) {
            let aElement = document.createElement("span");
            aElement.className = "gzn-list-item";
            aElement.innerHTML = "A: " + gzn.toFixed(2) + "&#176;";
            gdzLi.appendChild(aElement);
        }
        if (distance || gzn) {
            coordsList.appendChild(gdzLi);
        }
    }
    return li;
};

let getLatLngFromMarker = function (marker) {
    return new L.LatLng(marker.getLatLng().lat, marker.getLatLng().lng);
};

let calculateDistance = function (x1, y1, x2, y2) {
    let xdiff = x2 - x1,
        ydiff = y2 - y1;
    return Math.pow((xdiff * xdiff + ydiff * ydiff), 0.5);
};

let checkGzn = function (x, y) {
    let a = Math.atan(y / x);
    if (x > 0 && y > 0) {
        return a;
    }
    else if (x < 0 && y > 0) {
        return Math.PI - a;
    }
    else if (x < 0 && y < 0) {
        return Math.PI + a;
    }
    else if (x > 0 && y < 0) {
        return 2 * Math.PI - a;
    }
    return false;
};

// А =PI-PI*sgn(sgn(X)+1)*sgn(Y)+arctg(Y/(X+C)).
// sgn - (знак числа; 1 если х>0; 0 если х=0; -1 если х<0.)
// C=1*10-7 пренебрегаемо  малая  константа, позволяющая избежать деления на ноль.
//          Результаты численных экспериментов показали ее состоятельность.
// Х= (Х2-Х1);  У=(У2-У1)  это координаты точек 1 и 2
let calculateGzn = function (x1, y1, x2, y2, num, prevNum) {
    let x = x2 - x1,
        y = y2 - y1;

    let sgn = function (i) {
        let s = 0;
        if (i > 0) {
            s = 1;
        } else if (i < 0) {
            s = -1
        }
        return s;
    };
    let gzn = Math.PI - Math.PI * sgn(sgn(x) + 1) * sgn(y) + Math.atan(y / x);
    let classicGzn = checkGzn(x, y);
    // if (gzn !== classicGzn) {
    //     console.warn("Ошибка вычисление азимута для " + prevNum + "-" + num + ":");
    //     console.log("x1: " + x1 + "; y1: " + y1 + "; x2: " + x2 + "; y2: " + y2);
    //     console.log("dx: " + x + "; dy: " + y);
    //     console.log("По формуле А =PI-PI*sgn(sgn(X)+1)*sgn(Y)+arctg(Y/X) =" + gzn);
    //     console.log("Классическое вычисление = " + classicGzn);
    // }
    return gzn * (180 / Math.PI);
};

let transformCoord = function (ex, to) {
    let lonLatSystem = ["WGS84", "EPSG:4326", "EPSG:4269"];
    let crsSource = document.getElementById("crsDest").value;
    let trans_ex, trans_to;
    if (lonLatSystem.indexOf(crsSource) !== -1) {
        let crsDestVal = "EPSG:3875";
        trans_ex = transform([ex.x, ex.y], crsDestVal, crsSource);
        trans_to = transform([to.x, to.y], crsDestVal, crsSource);
    } else {
        trans_ex = [ex.x, ex.y];
        trans_to = [to.x, to.y];
    }
    return [trans_ex, trans_to];
};

let changeCoord = function () {
    let transCoordList = [];
    let crsDest = document.getElementById("crsDest");
    let coords = getMarkers();
    if (crsDest) {
        let crsDestVal = crsDest.value;
        for (let fry = 0; fry < coords.length; fry++) {
            let coord = [coords[fry].x, coords[fry].y];
            let trans = transform(coord, crsDestVal);
            transCoordList.push({x: trans[0].toFixed(6), y: trans[1].toFixed(6), num: coords[fry].num});
        }
    }
    showCoordList(transCoordList);
};

let build = function (data) {
    POINT_ID = 0;
    prepare(data);
    if (data.area_type) {
        types.setTypeById(data.area_type);
    }
    if (data.coordinates) {
        // if (data.coordinates.length > 1000) {
        //     alert('Слишком много узлов в полигоне. Попробуйте уеличить параметр epsila в запросе: ' +
        //         '38:36:000021:1106e10');
        //     return;
        // }
        if (data.geojson) {
            let feature = JSON.parse(data.geojson);
            L.geoJSON(feature.features, {
                style: {
                    fillColor: "#2f4f50",
                    color: "#2f4f50",
                    weight: 1,
                    opacity: 1,
                    fillOpacity: 0.3
                }
            }).addTo(featureGroup);
        }
        let coords = data.coordinates;
        coords.forEach((c) => {
            buildArea(c[0]);
            // exclude closing point
            let holes = c.slice(1, c.length);
            holes.forEach((h) => {
                buildArea(h, "hole");
            });

        });
        map.fitBounds(featureGroup.getBounds());
        // map.flyToBounds(featureGroup.getBounds());
        showCoordList();
        // startDraw();
    }
};

let buildArea = function (coords, type) {
    // exclude closing point
    let first = coords[0];
    let last = coords[coords.length - 1];
    if (first[0] === last[0] && first[1] === last[1]) {
        coords = coords.slice(0, coords.length - 1);
    }
    createMarkers(coords, type);
};

let prepare = function (data) {
    if (!input.value && data.code) {
        input.value = data.code;
    }
    let address = data.attrs && data.attrs.address;
    let pkk_url;
    if (address) {
        let info = document.createElement("div");
        info.className = "info-item";
        info.innerHTML = address;
        infoBlock.appendChild(info);
    }
    // PKK link with Search
    // if (data.center_pkk && data.code) {
    //     let c = data.center_pkk;
    //     let link = document.createElement("a");
    //     let linkText = document.createTextNode("На сайте PKK");
    //     link.className = "info-item link";
    //     pkk_url = `http://pkk5.rosreestr.ru/#x=${c.x}&y=${c.y}&text=${data.code}&app=search&opened=1`;
    //     link.setAttribute('href', pkk_url);
    //     link.setAttribute('target', "_blank");
    //     link.appendChild(linkText);
    //     infoBlock.appendChild(link);
    // }

    // let filename, pom;
    // let name = data.code.replace(/:/g, "-");
    // if (data.kml) {
    //     let kmldata = `<?xml version="1.0" encoding="utf-8" ?>
    //         <kml xmlns="http://www.opengis.net/kml/2.2"><Document id="root_doc">
    //         <Style id="default0">
    //             <LineStyle><color>ff0000ff</color></LineStyle><PolyStyle><fill>0</fill></PolyStyle></Style>
    //         <Placemark>
    //         <description><![CDATA[
    //             ${ address ? address + '<br>' : "" }
    //             <a href="http://getpkk.ru/${name}">Координаты</a>
    //             ${pkk_url ? `, <a href="${pkk_url}">PKK</a>` : ``}
    //         ]]></description>
    //         <name>${data.code}</name><styleUrl>#default0</styleUrl>${data.kml}</Placemark></Document></kml>`;
    //     filename = name + ".kml";
    //     pom = createBlob(filename, kmldata, "Kml", "info-item link kml-link");
    //     infoBlock.appendChild(pom);
    // }
    //
    // if (data.geojson && data.code) {
    //     filename = name + ".geojson";
    //     pom = createBlob(filename, data.geojson, "Geojson", "info-item link geojson-link");
    //     infoBlock.appendChild(pom);
    // }

    // Change coordinates input
    if (data.coordinates && data.code) {
        if (initProj4) {
            let crsDest = document.createElement("select");
            crsDest.id = "crsDest";
            crsDest.className = "form-control";
            coordSelect.appendChild(crsDest);
            initProj4();
            crsDest.onchange = function () {
                changeCoord();
            };
        }

        // Draw geodesy btn
        let geodesyCheckbox = document.createElement("input");
        geodesyCheckbox.setAttribute("type", "checkbox");
        geodesyCheckbox.id = "is-geodesy-checkbox";
        geodesyCheckbox.className = "coord-options";
        geodesyCheckbox.checked = LIST_WITH_GEODESY;
        coordOptions.appendChild(geodesyCheckbox);
        let checkboxlabel = document.createElement("label");
        checkboxlabel.setAttribute("for", geodesyCheckbox.id);
        checkboxlabel.innerHTML = "геодезия";
        coordOptions.appendChild(checkboxlabel);
        geodesyCheckbox.onclick = onGeodesyCheckboxClick;

        // decimal places
        let decimalSelect = document.createElement("select");
        decimalSelect.id = "decimal-places";
        decimalSelect.className = "coord-options";
        coordOptions.appendChild(decimalSelect);
        let decimalSelectLabel = document.createElement("label");
        decimalSelectLabel.setAttribute("for", decimalSelect.id);
        decimalSelectLabel.innerHTML = "округление";
        coordOptions.appendChild(decimalSelectLabel);
        for (let fry = 0; fry < 7; fry++) {
            let option = document.createElement("option");
            option.value = fry;
            option.text = fry;
            decimalSelect.appendChild(option);
            if (fry === COORD_DECIMAL) {
                option.setAttribute('selected', "true");
            }
        }
        coordOptions.onchange = onDecimalSelectChange;

    } else {
        let warning = document.createElement("div");
        warning.className = "alert alert-danger not-coordinates-warning";
        warning.setAttribute("role", "alert");
        warning.innerHTML = "Не удаётся загрузить координаты с сервиса PKK";
        infoBlock.appendChild(warning)
    }

};

let createBlob = function (filename, exportData, html, className, type) {
    type = type || 'text/plain';
    let pom = document.createElement('a');
    let bb = new Blob([exportData], {type: type});
    pom.setAttribute('href', window.URL.createObjectURL(bb));
    pom.setAttribute('download', filename);
    pom.dataset.downloadurl = [type, pom.download, pom.href].join(':');
    pom.className = className;
    pom.innerHTML = html;
    return pom;
};

let onGeodesyCheckboxClick = function (e) {
    toogleGeodesy(e.target.checked);
};

let onDecimalSelectChange = function (e) {
    let val = parseInt(e.target.value);
    if (!isNaN(val) && val !== COORD_DECIMAL) {
        COORD_DECIMAL = val;
        changeCoord();
    }
};

let toogleGeodesy = function (withGeodesy) {
    if (withGeodesy !== LIST_WITH_GEODESY) {
        LIST_WITH_GEODESY = !LIST_WITH_GEODESY;
        changeCoord();
    }
};

let clear = function () {
    stopLoading();
    POINT_ID = 0;
    featureGroup.clearLayers();
    coordSelect.innerHTML = "";
    coordOptions.innerHTML = "";
    infoBlock.innerHTML = "";
    coordsList.innerHTML = "";
};

goBtn.onclick = function () {
    code = input.value;
    if (!code) {
        alert("Введите кадастровый номер");
        return;
    }
    getAreaByCode(code);

};

var onSearchClick = function () {

};
if (typeof MainWindow != 'undefined') {
    onSearchClick = function (code) {
        MainWindow.onSearchClick(code)
    };

}

window.onSearchResult = function (data) {
    stopLoading();
    input.value = data.code;
    build(data);
};

let getAreaByCode = function (code) {
    try {
        startLoading();
        if (code) {
            onSearchClick(code);
            // getJSON(`/get/${code}/${types.type}`, {method: "POST"})
            //     .then(data => {
            //         input.value = code;
            //         build(data);
            //         stopLoading();
            //     })
            //     .catch(() => {
            //         stopLoading();
            //         alert("Поиск не дал результатов. Измените кадастровый номер и попробуйте ещё раз.");
            //         console.log("Error");
            //     })
        }
    } catch (er) {
        // alert(er);
    }
};



// getLink.onclick = function () {
//     getLink.blur();
//     if (code) {
//         alert(`http://getpkk.ru/${types.type || 1}/${code}`);
//     } else {
//         alert("Введите кадастровый номер");
//     }
// };

// mapClickModeBtn.onclick = function () {
//     mapClickModeOn = !mapClickModeOn;
//     mapClickModeBtn.blur();
//     if (mapClickModeOn) {
//         mapClickModeBtn.classList.add("active");
//         map.on("click", onMapClickModeBtnClick, this);
//         setMapCursor();
//     } else {
//         mapClickModeBtn.classList.remove("active");
//         map.off("click", onMapClickModeBtnClick, this);
//         setMapCursor();
//     }
//
// };

let setMapCursor = function () {
    map._container.style.cursor = mapClickModeOn ? "crosshair" : "";
};

// let onMapClickModeBtnClick = function (e) {
//     getAreaFromLatLng(e.latlng);
// };

// let getAreaFromLatLng = function (latlng) {
//     let urlStr = serializeUrlParam({
//         text: [latlng.lat, latlng.lng].join(","),
//         tolerance: 1
//     });
//     startLoading();
//     return getJSON(`http://pkk5.rosreestr.ru/api/features?${urlStr}`).then((data) => {
//         stopLoading();
//         if (data && data.features) {
//             let pkkFeature = data.features.find((obj) => {
//                 return (obj.attrs && obj.attrs.cn && obj.attrs.cn.split(":").length === 4)
//             });
//             if (pkkFeature && pkkFeature.center) {
//                 getAreaByCode(pkkFeature.attrs.cn);
//             }
//         }
//     }).catch(()=> {
//         startLoading();
//     })
// };


// OTHER


// if (window && !window.build) {
//     window.build = build;
// }


