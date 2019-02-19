function start(){
    showQuests(null);

    window.setInterval(updateLabelDiffTime, 1000)
}

 function showQuests(position) {
       $('#myTable tbody > tr').remove();
       console.log("fetch quests");
       $.getJSON( "raw_quests", function( data ) {
           if (data != null){
                 console.log("got data no position");
                   $.each( data['quests'], function( key, val ) {
                      let imgSrc
                      if (val['url'] === '') {
                          imgSrc = 'static/images/pokestop/Pokestop_Quest.png'
                      } else {
                          imgSrc = val['url']
                      }

                      $( "<tr/>", {
                       "class": 'my-new-list',
                       "type": val['reward_type'],
                       html: "<td><img class='reward-icon' src='static/icons/" + val['icon'] +".png'></td><td><a target=\"_blank\" href=\"https://www.google.com/maps/dir/Current+Location/"+val['latitude']+","+val['longitude']+"\">" + val['name'] + "</a></br> \
															 Quest: "+ val['quest_text']+ "</br> \
															 Reward: "+ val['reward_text'] + "</br> \
                                                             </td><td><img class='pokestop img sprite' src='" + imgSrc + "'></td><td>"+ moment(val['last_scanned']).format('HH:mm') + " - <span class='label-countdown' disappears-at='" + val['expiration'] + "'>00m00s</span> left</td>"
                       }).appendTo( "tbody" );
                   });
                   applyFilter();
           }
   });
 }

function applyFilter() {
    var input, filter, table, tr, td, i;
    input = document.getElementById("quest");
    filter = input.value.toUpperCase();
    table = document.getElementById("myTable");
    tr = table.getElementsByTagName("tr");
    for (i = 0; i < tr.length; i++) {
        td = tr[i].getElementsByTagName("td")[1];
        if (td) {
            if (td.innerHTML.toUpperCase().indexOf(filter) > -1) {
                tr[i].style.display = "";
            } else {
                tr[i].style.display = "none";
            }
        }
    }
}

function lpad(str, len, padstr) {
    return Array(Math.max(len - String(str).length + 1, 0)).join(padstr) + str
}

function getTimeUntil(time) {
    var now = Date.now()
    var tdiff = time - now

    var sec = Math.floor((tdiff / 1000) % 60)
    var min = Math.floor((tdiff / 1000 / 60) % 60)
    var hour = Math.floor((tdiff / (1000 * 60 * 60)) % 24)

    return {
        'total': tdiff,
        'hour': hour,
        'min': min,
        'sec': sec,
        'now': now,
        'ttime': time
    }
}

var updateLabelDiffTime = function () {
    $('.label-countdown').each(function (index, element) {
        var disappearsAt = getTimeUntil(parseInt(element.getAttribute('disappears-at')))

        var hours = disappearsAt.hour
        var minutes = disappearsAt.min
        var seconds = disappearsAt.sec
        var timestring = ''

        if (disappearsAt.ttime < disappearsAt.now) {
            timestring = '(expired)'
        } else {
            timestring = lpad(hours, 2, 0) + ':' + lpad(minutes, 2, 0) + ':' + lpad(seconds, 2, 0)
        }

        $(element).text(timestring)
    })
}
