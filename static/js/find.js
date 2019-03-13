function updateStopsGymsList() {
	// Bounds of the currently visible map
    var currentVisibleMap = map.getBounds()
	console.log("There can be only one")

        var stopGymList  = '<table><tr><th>Name</th></tr>'

	$.each(mapData.pokestops, function (key, value) {
            var thisPokestopLocation = { lat: mapData.pokestops[key]['latitude'], lng: mapData.pokestops[key]['longitude'] }
            var thisPokestopIsVisible = currentVisibleMap.contains(thisPokestopLocation)
	    console.log("Gym " + mapData.pokestops[key]['name'])
            stopGymList += '<tr><td>' + mapData.pokestops[key]['name'] + '</td></tr>'
	});
	$.each(mapData.gyms, function (key, value) {
            var thisGymLocation = { lat: mapData.gyms[key]['latitude'], lng: mapData.gyms[key]['longitude'] }
            var thisGymIsVisible = currentVisibleMap.contains(thisGymLocation)
	    console.log("Gym " + mapData.gyms[key]['name'])
            stopGymList += '<tr><td>' + mapData.gyms[key]['name'] + '</td></tr>'
	});
	stopGymList += '</table>'

	document.getElementById('findStopsGyms').innerHTML = stopGymList
}
