   function start(){
       showDevices(null);
   }

 function showDevices(position) {
       $('#myTable tbody > tr').remove();
       console.log("fetch devices");
       $.getJSON( "raw_devices", function( data ) {
           if (data != null){
                 console.log("got data no position");
                   $.each( data['devices'], function( key, val ) {
                       $( "<tr/>", {
                       "class": 'my-new-list',
                       html: "<td>" + val['deviceid'] + "</td><td>" + val['name']  + "</td><td>" + val['scans'] + "</td><td>" + val['scanning'] + "</td><td>" + val['fetching'] + ' - ' + val['route'] + "</td><td><a target=\"_blank\" href=\"https://www.google.com/maps/dir/Current+Location/"+val['latitude']+","+val['longitude']+'\">Check on map</a></td><td><input type="text" value="'+val['latitude']+","+val['longitude']+'" id="input-' + val['deviceid'] + '"/> <button id="button-' + val['deviceid'] + '" name="changeLocation-' + val['deviceid'] + '" onclick="changeLocation(this)">Teleport to new location</button></td>'
                       }).appendTo( "tbody" );
                   });
           }
   });
 }

   function changeClass(obj)
   {
       $('#' + obj.id).toggleClass('inactive');

   }

function changeLocation(obj) {
  var buttonid = obj.id;
  var inputid = buttonid.replace("button-", "input-");
  var uuid = buttonid.replace("button-", "");

  $("input[id='" + inputid + "']").each(function () {
    console.log($(this));
    var newcoords = $(this).attr('value');
    console.log(newcoords);
    $.post('next_loc?coords=' + newcoords + '&uuid=' + uuid)
  });
}
