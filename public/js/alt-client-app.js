var main = function () {
    $.getJSON("/last.json", function (response) {
        $("body").append("<p><b>created at:</b>"+response.created_at+"</p>");
        $("body").append("<p><b>user:</b>"+response.user.screen_name+"</p>");
        $("body").append("<p><b>text:</b>"+response.text+"</p>");
        $("body").append("<div class=fcuk><p><b>id:</b>"+response.id+"</p></div>")
    });
};

$(document).ready(main);