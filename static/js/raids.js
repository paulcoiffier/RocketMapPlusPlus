   function load(){
            $("button[name='level']").each(function () {
           document.getElementById("filter_"+$(this).attr('id')).checked = JSON.parse(localStorage.getItem('filter_'+$(this).attr('id')));
           if(JSON.parse(localStorage.getItem('filter_'+$(this).attr('id')))){
               $(this).removeClass('inactive')
           }
          // $(this).toggleClass('inactive')
       });
   }

   function start(){
       load();
       showRaids(null);
   }

 function showRaids(position) {
       $('#myTable tbody > tr').remove();
       console.log("fetch raids");
       $.getJSON( "raw_raid", function( data ) {
           if (data != null){
                 var egg = ['', 'egg_normal.png', 'egg_normal.png', 'egg_rare.png','egg_rare.png','egg_legendary.png'];

                 console.log("got data no position");
                 let raids = data['raids'].sort(function(a, b) {
                    return a['end'] - b['end'];
                 });
                   $.each( raids, function( key, val ) {
                       $( "<tr/>", {
                       "class": (val['is_ex_raid_eligible']?'exraid':'my-new-list'),
                       "level": val['level'],
                       html: "<td>" + moment(val['start']).format('HH:mm') + " - " + moment(val['end']).format('HH:mm')  + "</td><td>"+(val['pokemon_id']?"<img src=\"/static/icons/"+ val['pokemon_id']+ ".png\">":"<img src=\"/static/images/raid/" + egg[val['level']] + "\">") + "</td><td><a target=\"_blank\" href=\"https://www.google.com/maps/dir/Current+Location/"+val['latitude']+","+val['longitude']+"\">" + val['name'] + "</a></br>Level "+val['level']+": "+val['pokemon_name']+ (val['move_1']?"("+val['move_1']:'') + (val['move_2']?"/"+val['move_2']+")":'') +"</br>Last scanned: "+ moment(val['last_scanned']).format('HH:mm') + "</td>"
                       }).appendTo( "tbody" );
                   });
                   applyFilter();
           }
   });
 }
   function changeClass(obj)
   {
       $('#' + obj.id).toggleClass('inactive');

       $("button[name='level']").each(function () {
           console.log($(this));
           if ( ! $(this).hasClass('inactive') ) {
               document.getElementById("filter_"+$(this).attr('id')).checked = true;
           } else {
               document.getElementById("filter_"+$(this).attr('id')).checked = false;
           }

           $("input[name='filterLevel']").each(function () {
               localStorage.setItem($(this).attr('id'), $(this).is(":checked"));
           });
       });
       applyFilter();
   }

       $("input[name='filterLevel']").change(function () {
           applyFilter();
           $("input[name='filterLevel']").each(function () {
               localStorage.setItem($(this).attr('id'), $(this).is(":checked"));
           });
       });

       function applyFilter(){
           var classes = [];
           $("input[name='filterLevel']").each(function () {
               if ($(this).is(":checked")) { classes.push($(this).val());}
           });
           var distance = $("select[name='FilterDist']").val();
           if (classes == "") {
               $("#myTable tbody tr").show();
           } else {
               $("#myTable tbody tr").hide();

               $("#myTable tbody tr").each(function () {
                   var show = true;
                   var row = $(this);
                   classes.forEach(function (className) {
                       if (row.attr("level") == className) { row.show(); }
                   });
               });
           }
   				// if (! $("button[name='exraid']").hasClass('inactive')) {
   				// 		$("#myTable tbody tr").each(function () {
   				// 				var show = false;
   				// 				var row = $(this);
   				// 				if (!row.hasClass('exraid')) { row.hide(); }
   				// 		});
   				// }
       }
