//
// Stilen from https://stackoverflow.com/questions/1129216/sort-array-of-objects-by-string-property-value
//
function compare(a,b) {
  if (a.name < b.name)
    return -1;
  if (a.name > b.name)
    return 1;
  return 0;
}

function updateStopsGymsList() {
	// Bounds of the currently visible map
    var currentVisibleMap = map.getBounds()

        var stopGymList  = '<table><tr><th>Name</th></tr>'
	var list = filterStopsGyms(document.getElementById("fp_sg_filter").value.toLowerCase())
	list = list.sort(compare)


	$.each(list, function (key, value) {
            var thisPokestopLocation = { lat: list[key]['lat'], lng: list[key]['lng'] }
            if (currentVisibleMap.contains(thisPokestopLocation))
	    {
                stopGymList += '<tr onmouseover="fp_draw_circle('+ list[key]['lat'] + ', '+ list[key]['lng'] +')" onmouseout="fp_remove_circle()"><td>' + list[key]['name'] + '</td></tr>'
            }
	});

	document.getElementById('findStopsGyms').innerHTML = stopGymList
}

function filterStopsGyms(filter){
	var list = new Array()

        $.each(mapData.pokestops, function (key, value) {
 	    if (value['name'].toLowerCase().includes(filter) || filter == ''){
	        var stop = {
 	           name : value['name'],
	           lat : value['latitude'],
	           lng : value['longitude']
	        }
	        list.push(stop)
	    }
        });
        $.each(mapData.gyms, function (key, value) {
 	    if (value['name'].toLowerCase().includes(filter) || filter == ''){
	        var stop = {
  	            name : value['name'],
	            lat : value['latitude'],
	            lng : value['longitude']
		}
	        list.push(stop)
	    }
  	});

	return list
}

function fp_draw_circle(lat, lng){
      var center = {lat: lat, lng: lng}
      fp_circled = new google.maps.Circle({
              strokeColor: '#FF8000',
              strokeOpacity: 1,
              strokeWeight: 5,
              fillColor: '#000000',
              fillOpacity: 0.0,
              map: map,
              center: center,
              radius: 70
      });
}


function fp_remove_circle(){
      fp_circled.setMap(null);
}

