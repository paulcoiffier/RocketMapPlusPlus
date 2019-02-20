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
                       html: "<td>" + val['deviceid'] + '</td><td><input type="text" value="'+val['name'] + '" id="inputname-' + val['deviceid'] + '"/> <button id="buttonname-' + val['deviceid'] + '" name="changeName-' + val['deviceid'] + '" onclick="changeName(this)">Update Name</button></td><td>' + val['scans'] + "</td><td>" + val['scanning'] + "</td><td>" + val['fetching'] + (val['mapcontrolled']?' (Map Controlled)':'') + ' - ' + val['route'] + " Points left in schedule</td><td><a target=\"_blank\" href=\"https://www.google.com/maps/dir/Current+Location/"+val['latitude']+","+val['longitude']+'\">Check on map</a></td><td><input type="text" value="'+val['latitude']+","+val['longitude']+'" id="inputlocation-' + val['deviceid'] + '"/> <button id="buttonlocation-' + val['deviceid'] + '" name="changeLocation-' + val['deviceid'] + '" onclick="changeLocation(this)">Teleport</button></td><td><input type="text" value="'+val['endpoint']+'" id="inputendpoint-' + val['deviceid'] + '"/> <button id="buttonendpoint-' + val['deviceid'] + '" name="changeEndpoint-' + val['deviceid'] + '" onclick="changeEndpoint(this)">Update Endpoint</button></td>'
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
  var inputid = buttonid.replace("buttonlocation-", "inputlocation-");
  var uuid = buttonid.replace("buttonlocation-", "");

  $("input[id='" + inputid + "']").each(function () {
    console.log($(this));
    var newcoords = $(this).val();
    console.log(newcoords);
    $.post('next_loc?coords=' + newcoords + '&uuid=' + uuid)
  });
}

function changeName(obj) {
  var buttonid = obj.id;
  var inputid = buttonid.replace("buttonname-", "inputname-");
  var uuid = buttonid.replace("buttonname-", "");

  $("input[id='" + inputid + "']").each(function () {
    console.log($(this));
    var newname = $(this).val();
    console.log(newname);
    $.post('new_name?name=' + newname + '&uuid=' + uuid)
  });
}

function changeEndpoint(obj) {
  var buttonid = obj.id;
  var inputid = buttonid.replace("buttonendpoint-", "inputendpoint-");
  var uuid = buttonid.replace("buttonendpoint-", "");

  $("input[id='" + inputid + "']").each(function () {
    console.log($(this));
    var newendpoint = $(this).val();
    newendpoint = newendpoint.replace("?", "||");
    newendpoint = newendpoint.replace("&", "|");
    console.log(newendpoint);
    $.post('new_endpoint?uuid=' + uuid + '&endpoint=' + newendpoint)
  });
}
