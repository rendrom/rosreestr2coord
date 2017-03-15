import {AREA_TYPES} from "./area_types";
// import 'bootstrap.native/lib/V3/dropdown-native'
import 'bootstrap.native';

export class AreaTypes {

    constructor() {
        this.dropdown = document.getElementById("area-types-btn");
        this.dropdownUl = document.getElementById("area-types-options");
        this._fillAreaTypeOptions();
        this._type = null;

        this.setType("Участки");
    }

    get type() {
        return this._type;
    }

    _fillAreaTypeOptions() {
        if (this.dropdown) {
            AREA_TYPES.forEach((value, key) => {
                let option = document.createElement("li");
                let a = document.createElement("a");
                a.href = "#";
                a.innerHTML = key;
                a.onclick = () => {
                    this.setType(key)
                };
                option.appendChild(a);
                this.dropdownUl.appendChild(option);
            })
        }

    }

    setType(key) {
        if (this.dropdown) {
            this._type = AREA_TYPES.get(key);
            this.dropdown.getElementsByClassName("type-selected")[0].innerHTML = key;
            this.close();
        }
    }

    setTypeById(id) {
        AREA_TYPES.forEach((value, key) => {
            if (value === parseInt(id)) {
                this.setType(key);
                return true;
            }
        })
    }

    close() {
        this.dropdown.parentNode.className = this.dropdown.parentNode.className.replace(/\bopen/, '');
        this.dropdown.setAttribute('aria-expanded', false);
    }
}

