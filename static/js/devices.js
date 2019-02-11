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
                       html: "<td>" + val['deviceid'] + "</td><td>" + val['name']  + "</td><td>" + val['scans'] + "</td><td>" + val['scanning'] + "</td><td>" + val['fetching'] + ' - ' + val['route'] + "</td>"
                       }).appendTo( "tbody" );
                       console.log(val['deviceid']);
                   });
           }
   });
 }

   function changeClass(obj)
   {
       $('#' + obj.id).toggleClass('inactive');

   }
