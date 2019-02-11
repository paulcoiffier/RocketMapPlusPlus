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
                       html: "<td>" + val['deviceid'] + '</td><input type="text" value="'+val['name'] + '" id="inputname-' + val['deviceid'] + '"/> <button id="buttonname-' + val['deviceid'] + '" name="changeName-' + val['deviceid'] + '" onclick="changeName(this)">Update Name</button></td><td>' + val['scans'] + "</td><td>" + val['scanning'] + "</td><td>" + val['fetching'] + ' - ' + val['route'] + "</td><td><a target=\"_blank\" href=\"https://www.google.com/maps/dir/Current+Location/"+val['latitude']+","+val['longitude']+'\">Check on map</a></td><td><input type="text" value="'+val['latitude']+","+val['longitude']+'" id="inputlocation-' + val['deviceid'] + '"/> <button id="buttonlocation-' + val['deviceid'] + '" name="changeLocation-' + val['deviceid'] + '" onclick="changeLocation(this)">Teleport to new location</button></td>'
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
    var newcoords = $(this).value;
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
    var newname = $(this).value;
    console.log(newname);
    $.post('new_name?name=' + newname + '&uuid=' + uuid)
  });
}
