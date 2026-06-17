$(function () {
    function count_word(val) {
        var wom = val.match(/\S+/g);
        return {
            words: wom ? wom.length : 0
        };
    }

    $("textarea").on("input", function (el) {
        var v = count_word(this.value);
        var qId = $(this).attr("data-question-id");
        $("#question-" + qId + " .word-count").html("Word count: " + v.words);
    });
});
