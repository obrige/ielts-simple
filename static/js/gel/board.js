$(function () {
    $(".intro-outro.intro .btn.academic, .intro-outro.intro .btn.general").on("click tap", function (e) {
        var type = $(this).attr('data-type');
        if (type) {
            toggleTestType(type);
        }
    });

    $(".intro-outro .btn.end").on("click tap", function (e) {
        $(".intro-outro.intro .btn").attr('disabled', 'disabled');
        var selected = $("#selected-type").attr("data-selected-type");
        if (selected === "academic") {
            window.location.href = "/tests/start/academic";
        } else if (selected === "general") {
            window.location.href = "/tests/start/general";
        } else {
            location.reload();
        }
    });
});

function toggleTestType(type) {
    $(".step .type:not(" + type + ")").hide();
    $("." + type).show();
    $("#selected-type").attr("data-selected-type", type);
}
