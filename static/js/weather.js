/**
 * Parses info about weather cell and draws icon
 * @param i index from $.each()
 * @param item weather cell data
 * @returns {boolean}
 */
function processWeather(i, item) {
    if (!Store.get('showWeatherCells') || item.gameplay_weather == null) {
        return false
    }

    if (item.s2_cell_id in mapData.weather) {
        item.marker = updateWeatherMarker(item, mapData.weather[item.s2_cell_id].marker)
    }
    else {
        // add marker to map and item to dict
        item.marker = setupWeatherMarker(item)
    }

    mapData.weather[item.s2_cell_id] = item
}


/**
 * Parses info about s2cell and draws polygon
 * @param i i index from $.each()
 * @param item s2cell data
 * @returns {boolean}
 */
function processS2Cell(i, item) {
    if (!Store.get('showS2Cells')) {
        return false
    }

    var s2CellId = item.s2_cell_id
    if (!(s2CellId in mapData.s2cells)) {
        safeDelMarker(item)
        item.marker = setupS2CellPolygon(item)
        mapData.s2cells[s2CellId] = item
    }
}


/**
 * Do main work with array of weather alerts
 * @param weatherAlerts
 */
function processWeatherAlerts(weatherAlerts) {
    deleteObsoleteWeatherAlerts(weatherAlerts)
    $.each(weatherAlerts, processWeatherAlert)
}


/**
 * Draws colored polygon for weather severity condition
 * @param i
 * @param item s2cell data
 * @returns {boolean}
 */
function processWeatherAlert(i, item) {
    if (!Store.get('showWeatherAlerts') || item.severity == null) {
        return false
    }

    var s2CellId = item.s2_cell_id
    var itemOld = mapData.weatherAlerts[s2CellId]
    if (itemOld == null) {
        safeDelMarker(item)
        item.marker = createCellAlert(item)
        mapData.weatherAlerts[s2CellId] = item
    } else if (itemOld.severity !== item.severity) {
        itemOld.marker.setMap(null)
        item.marker = createCellAlert(item)
        mapData.weatherAlerts[s2CellId] = item
    }
}


/**
 * If drawn cell not exist in new alert array, it should be removed
 * @param newAlerts
 */
function deleteObsoleteWeatherAlerts(newAlerts) {
    var toRemove = []
    $.each(mapData.weatherAlerts, function (i, item) {
        if (!(item['s2_cell_id'] in newAlerts)) {
            safeDelMarker(item)
            toRemove.push(i)
        }
    })
    $.each(toRemove, function (i, id) {
        delete mapData.weatherAlerts[id]
    })
}


/**
 * safe setMap(null)
 * @param item
 */
function safeDelMarker(item) {
    if (item.marker) {
        item.marker.setMap(null)
    }
}


/**
 * Creates path for weather icon based on gameplay_weather and time_of_day
 * @param item
 * @param dark dark or light version of image, default is dark
 * @returns {*}
 */
function getWeatherImageUrl(item, dark = true) {
    var weatherimageUrl
    if (item.time_of_day === 2) { // night
        if (![1, 3].includes(item.gameplay_weather)) { // common icons for day and night
          weatherimageUrl = 'static/images/weather/' + weatherImages[item.gameplay_weather]
        } else { // clear and partly cloudy
          weatherimageUrl = 'static/images/weather/' + weatherImages[item.gameplay_weather + 10]
        }
    } else {
      weatherimageUrl = 'static/images/weather/' + weatherImages[item.gameplay_weather]
    }
    if (!dark && item.severity == 0) {
      weatherimageUrl = weatherimageUrl.replace('weather_', 'weather_light_')
    }
    return weatherimageUrl
}

/**
 * Creates path for alert icon based on severity
 * @param item
 * @returns {*}
 */
function getalertImageUrl(item) {
    var alertimageUrl
    if (item.severity === 1) {
      alertimageUrl = 'static/images/weather/' + weatherImages[15]
    } else if (item.severity === 2) {
      alertimageUrl = 'static/images/weather/' + weatherImages[16]
    }
    return alertimageUrl
}

/**
 * Creates marker and then updates it
 * @param item
 * @returns {google.maps.Marker}
 */
function setupWeatherMarker(item) {
    var marker
    
    marker = new google.maps.Marker({
        position: item.center,
        map: map
    })

    updateWeatherMarker(item, marker)

    return marker
}

/**
 * Updates marker with image and text
 * @param item
 * @param marker
 * @returns {google.maps.Marker}
 */
function updateWeatherMarker(item, marker) {
    var weatherimageUrl = getWeatherImageUrl(item)

    marker.setIcon({
        url: weatherimageUrl,
        origin: new google.maps.Point(0, 0),
        anchor: new google.maps.Point(32, 32),
        labelOrigin: new google.maps.Point(32, 64)
    })

    var weatherText = weatherTexts[item.gameplay_weather]
    var boostedTypesText = weatherBoostedTypes[item.gameplay_weather]
    var currentTime = new Date()
    var currentHourTime = currentTime.setMinutes(0, 0, 0)
    var weatherTime = item.last_updated

    if (weatherTime < currentHourTime) {
        marker.setTitle("Weather: " + weatherText + " (Out of date)\nBoosted Types: " + boostedTypesText + "\nLast Updated: " + moment(weatherTime).format('dddd, Do MMMM Y, HH:mm'))

        marker.setLabel({
            text: weatherText,
            color: "#ff0000",
            fontSize: "14px",
            fontWeight: "bold"
        })

        marker.showingOldWeather = true
    } else {
        marker.setTitle("Weather: " + weatherText + "\nBoosted Types: " + boostedTypesText + "\nLast Updated: " + moment(weatherTime).format('dddd, Do MMMM Y, HH:mm'))

        marker.setLabel({
            text: weatherText,
            color: "#256377",
            fontSize: "14px",
            fontWeight: "bold"
        })

        marker.showingOldWeather = false
    }

    return marker
}

/**
 * Creates Polygon for s2cell
 * @param item
 * @returns {google.maps.Polygon}
 */
function setupS2CellPolygon(item) {
    return new google.maps.Polygon({
        paths: item.vertices,
        strokeColor: '#000000',
        strokeOpacity: 0.8,
        strokeWeight: 1,
        fillOpacity: 0,
        fillColor: '#00ff00'
    })
}


/**
 * Adds fillColor for s2cell polygon
 * @param item
 * @returns {google.maps.Polygon}
 */
function createCellAlert(item) {
    var cell = setupS2CellPolygon(item)
    cell.strokeOpacity = 0
    if (item.severity === 0) {
        cell.fillOpacity = 0.0
    } else if (item.severity === 1) {
        cell.fillOpacity = 0.2
        cell.fillColor = '#ffff00'
    } else if (item.severity === 2) {
        cell.fillOpacity = 0.2
        cell.fillColor = '#ff0000'
    }
    return cell
}


/**
 * Calculates square bound for s2cell
 * @param s2Cell
 * @returns {google.maps.LatLngBounds}
 */
function getS2CellBounds(s2Cell) {
    var bounds = new google.maps.LatLngBounds()
    // iterate over the vertices
    $.each(s2Cell.vertices, function (i, latLng) {
        // extend the bounds
        bounds.extend(latLng)
    })
    return bounds
}


// Weather top icon.
var $weatherInfo = document.querySelector('#weatherInfo')

/**
 * Update weather icon on top bar if there is single cell on the screen
 */
function updateMainCellWeather() {
    if ($weatherInfo == null) {
        return // updating the top bar is not required if it does not exist
    }
    // remove old weather icon
    while ($weatherInfo.firstChild) {
        $weatherInfo.removeChild($weatherInfo.firstChild)
    }
    var s2Cell = getMainS2Cell()
    if (s2Cell != null) {
        var weatherimgUrl = getWeatherImageUrl(s2Cell, false)
        var alertimgUrl = getalertImageUrl(s2Cell)
        if (s2Cell.severity >= 1) {
          // Alert Text
          var alert = alertTexts[s2Cell.severity]
          var alerttext = document.createElement('span')
          alerttext.textContent ? alerttext.textContent = weather : alerttext.innerText = alert
          alerttext.setAttribute('style', 'font-size: 10px; position: relative; left: -2px;')
          // Alert Icon
          var alerticon = document.createElement('img')
          alerticon.setAttribute('src', alertimgUrl)
          alerticon.setAttribute('style', 'height: 25px; vertical-align: middle;')
          $weatherInfo.appendChild(alerticon)
          $weatherInfo.appendChild(alerttext)
        }
        // Weather Text
        var weather = weatherTexts[s2Cell.gameplay_weather]
        var weathertext = document.createElement('span')
        weathertext.textContent ? weathertext.textContent = weather : weathertext.innerText = weather
        weathertext.setAttribute('style', 'font-size: 10px; position: relative; left: -2px;')
        // Weather Icon
        var weathericon = document.createElement('img')
        weathericon.setAttribute('src', weatherimgUrl)
        weathericon.setAttribute('style', 'height: 25px; vertical-align: middle;')
        // Wind Text
        var winddirection = degreesToCardinal(s2Cell.wind_direction)
        var windtext = document.createElement('span')
        windtext.textContent ? windtext.textContent = winddirection : windtext.innerText = winddirection
        windtext.setAttribute('style', 'font-size: 10px; position: relative; left: -2px;')
        // Wind Icon
        var windIcon = document.createElement('img')
        windIcon.setAttribute('src', '/static/images/weather/wind_streaks.png')
        windIcon.setAttribute('style', 'height: 25px; vertical-align: middle;')
        // Make It Happen
        $weatherInfo.appendChild(weathericon)
        $weatherInfo.appendChild(weathertext)
        $weatherInfo.appendChild(windIcon)
        $weatherInfo.appendChild(windtext)
    }
}


function degreesToCardinal(d) {
    var dirs = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
        'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    var ix = Math.floor((d + 11.25) / 22.5 - 0.02)
    return dirs[ix % 16]
}

/**
 * Finds weather data for s2cell, that covers more than a half of the screen
 * @returns {*}
 */
function getMainS2Cell() {
    if (typeof window.orientation !== 'undefined' || isMobileDevice()) {
        if (map.getZoom() < 12) { // viewport my contain many cells
            return
        }
    } else {
        if (map.getZoom() < 13) { // viewport my contain many cells
            return
        }
    }

    var geometryFactory = new jsts.geom.GeometryFactory()

    var bounds = map.getBounds()
    var viewportPath = [
        {'lat': bounds.getNorthEast().lat(), 'lng': bounds.getNorthEast().lng()},
        {'lat': bounds.getNorthEast().lat(), 'lng': bounds.getSouthWest().lng()},
        {'lat': bounds.getSouthWest().lat(), 'lng': bounds.getSouthWest().lng()},
        {'lat': bounds.getSouthWest().lat(), 'lng': bounds.getNorthEast().lng()}
    ]
    var jstsViewport = createJstsPolygon(geometryFactory, viewportPath)
    var viewportArea = jstsViewport.getArea()
    var maxCoverageData
    $.each(mapData.weather, function (i, s2cell) {
        var jstsS2cell = createJstsPolygon(geometryFactory, s2cell.vertices)
        var area = jstsViewport.intersection(jstsS2cell).getArea()
        if (viewportArea < area * 2) {  // more then a half of the screen covered by cell
            maxCoverageData = s2cell
        }
    })
    return maxCoverageData
}


/**
 * Creates jsts polygon from coordinates array
 * @param geometryFactory
 * @param path
 * @returns {*}
 */
function createJstsPolygon(geometryFactory, path) {
    var coordinates = path.map(function name(coord) {
        return new jsts.geom.Coordinate(coord.lat, coord.lng)
    })
    if (coordinates[0].compareTo(coordinates[coordinates.length - 1]) !== 0) {
        coordinates.push(coordinates[0])
    }
    var shell = geometryFactory.createLinearRing(coordinates)
    return geometryFactory.createPolygon(shell)
}
