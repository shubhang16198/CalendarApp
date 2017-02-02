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

function get_events_list(object){
     var events;
    var d = new Date();
    var url = "/all/" + d.getFullYear() + "/" + d.getMonth() + 1 + "/" + d.getDate();
    $.getJSON(url, function (data) {
        var items = data.items.map(function(item) {
            return item.key + ": " + item.value;
        });
    });
}
/*$(document).ready(function () {

})


$.ajax({
    dataType: "json",
    url:

})*/