function start(){
    showQuests(null);
}

 function showQuests(position) {
       $('#myTable tbody > tr').remove();
       console.log("fetch quests");
       $.getJSON( "raw_quests", function( data ) {
           if (data != null){
                 console.log("got data no position");
                   $.each( data['quests'], function( key, val ) {
                       $( "<tr/>", {
                       "class": 'my-new-list',
                       "type": val['reward_type'],
                       html: "<td><a target=\"_blank\" href=\"https://www.google.com/maps/dir/Current+Location/"+val['latitude']+","+val['longitude']+"\">" + val['name'] + "</a></br> \
															 Quest: "+ val['quest_text']+ "</br> \
															 Reward: "+ val['reward_text'] + "<img class='reward-icon' src='static/icons/" + val['icon'] +".png'>" + "</br> \
                                                             </td><td>"+ moment(val['last_scanned']).format('HH:mm') + "</td>"
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
        td = tr[i].getElementsByTagName("td")[0];
        if (td) {
            if (td.innerHTML.toUpperCase().indexOf(filter) > -1) {
                tr[i].style.display = "";
            } else {
                tr[i].style.display = "none";
            }
        }
    }
}
