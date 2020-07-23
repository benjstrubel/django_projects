
class PrefVector {
    INCREMENT_SIZE = .2;
    map = new Map();

    constructor(){
        this.map['entertainment'] = 0.0;
        this.map['health'] = 0.0;
        this.map['sports'] = 0.0;
        this.map['tech'] - 0.0;
        this.map['politics'] = 0.0;
    }

    getMap() {
        return this.map;
    }
    
    incrementByName(categoryName) {
        this.map[categoryName] += this.INCREMENT_SIZE;
    }

    toJSON() {
        var JSON = "{";
        for(const [k,v] of Object.entries(this.map)) {
            JSON += '"' + k + '":' + v + ",";
        }
        JSON = JSON.substring(0,length(JSON)-2)
        JSON += "}";
        return JSON;
    }
}