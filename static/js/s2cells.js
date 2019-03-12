function calculateS2Cells(latlng, level){
var cell = S2.S2Cell.FromLatLng(latlng, level);
var Lv12Cells = []
//var map = {}
//map['vertices'] = cell.getCornerLatLngs()
Lv12Cells.push({s2_cell_id : cell.toHilbertQuadkey(), vertices: cell.getCornerLatLngs()})
//var Lv12NeighborsPri = cell.getNeighbors()
//Lv12NeighborsPri.forEach(function(cellPri) {
//  Lv12NeighborsSec = cellPri.getNeighbors()
//  Lv12NeighborsSec.forEach(function(cellSec) {
//    if (Lv12Cells.includes(cellSec.getCornerLatLngs()) == false) {
//      Lv12Cells.push(cellSec.getCornerLatLngs())
//    }
//    console.log("Cells=" + Lv12Cells.length)
//  });
//});
return Lv12Cells
};


//var Lv12Cells = calculateS2Cells(latlng, 12)
//var myJSON = JSON.stringify(Lv12Cells);
//console.log("latlng:" + myJSON);
//console.log("lat:" + map.getcenter().lat);
//

function processS2CellLv17(i, item) {
    if (!Store.get('showS2CellsLv17')) {
        return false
    }

    var s2CellId = item.s2_cell_id
    if (!(s2CellId in mapData.s2cellsLv17)) {
        safeDelMarker(item)
        item.marker = setupS2CellPolygon(item, 1.5 ,'#006400')
        mapData.s2cellsLv17[s2CellId] = item
    }
}
function processS2CellLv14(i, item) {
    if (!Store.get('showS2CellsLv14')) {
        return false
    }

    var s2CellId = item.s2_cell_id
    if (!(s2CellId in mapData.s2cellsLv14)) {
        safeDelMarker(item)
        item.marker = setupS2CellPolygon(item, 1.5 ,'#FFA500')
        mapData.s2cellsLv14[s2CellId] = item
    }
}
