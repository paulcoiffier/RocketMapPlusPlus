function calculateS2Cells(latlng, level){
  var cell = S2.S2Cell.FromLatLng(latlng, level);
  var Cells = []
  var visited = []
  var i;
  Cells.push({s2_cell_id : cell.toHilbertQuadkey(), vertices: cell.getCornerLatLngs()})
  visited.push(cell.toHilbertQuadkey())
  var nextlevel = cell.getNeighbors()
  var currentlevel;
  for (i = 0; i < 7; i++) {
    currentlevel = nextlevel
    var nextlevel = []
    currentlevel.forEach(function(cell){
      if (visited.includes(cell.toHilbertQuadkey()) == false){
        Cells.push({s2_cell_id : cell.toHilbertQuadkey(), vertices: cell.getCornerLatLngs()})
        var newcells = cell.getNeighbors()
        newcells.forEach(function(cell2){
          if(visited.includes(cell2.toHilbertQuadkey()) == false)
          {
            nextlevel.push(cell2)
          }
        });
        nextlevel.concat(newcells)
        visited.push(cell.toHilbertQuadkey())
      }
    });
  }
  return Cells
};

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
