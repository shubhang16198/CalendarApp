function gettime(date) {
    var hours = date.getHours();
    var minutes = date.getMinutes();
    hours = hours % 12;
    hours = hours ? hours : 12; // the hour '0' should be '12'
    minutes = minutes < 10 ? '0'+minutes : minutes;
    var strTime = hours + ':' + minutes
    return strTime;
}

function getAMPM(date) {
    var ampm = date.getHours() >= 12 ? 'pm' : 'am';
    return ampm;
}

function get_events_list(object, d){
    url = "/all/" + d.getFullYear() + "/" + (parseInt(d.getMonth()) + 1) + "/" + d.getDate();
    var noevents = false;
    $.getJSON(url, function (data) {
        if (data.length == 0) {
            object.innerHTML = "<li class='sidebar-events'> No events today :( </li>";
            noevents = true;
            return;
        }
        else {
            var l = "<ul>";
            for (var i = 0; i < data.length; ++i)
            {
                var item = data[i];
                var element = "<li class='sidebar-events' >" + item.name + "</li>";
                l += element;
            }
            l += "</ul>";
            object.innerHTML = l;
        }

    });
    if (noevents) {
        return;
    }
}
/*$(document).ready(function () {

})


$.ajax({
    dataType: "json",
    url:

})*/