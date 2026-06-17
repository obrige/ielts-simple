(function () {

    if (typeof window.CustomEvent === "function") return false;

    function CustomEvent(event, params) {
        params = params || {bubbles: false, cancelable: false, detail: null};
        var evt = document.createEvent('CustomEvent');
        evt.initCustomEvent(event, params.bubbles, params.cancelable, params.detail);
        return evt;
    }

    window.CustomEvent = CustomEvent;
})();

$(function () {
    $(".steps .step:not(:first-of-type)").hide();
    $(".steps .step:first-of-type").show({
        always: function (x, y) {
            window.dispatchEvent(new CustomEvent('stepsStarted'));
        }
    });

    $(".steps .next-button:not(.last-step)").on("click tap", function (e) {
        var next = $(this).attr("data-next-step");
        if (next) {
            toggleStep(next);
            window.dispatchEvent(new CustomEvent('stepsChanged'));
        }
    });

    $(".steps .next-button.last-step").on("click tap", function (e) {
        window.dispatchEvent(new CustomEvent('stepsEnded'));
    });

});

function toggleStep(step) {
    $(".step:not(step-" + step + ")").hide();
    $(".step.step-" + step).css('display', 'flex');
}
