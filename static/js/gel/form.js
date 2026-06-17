$(function () {
	$('#bc_ad').on('click', function(e) {
		window.open('https://takeielts.britishcouncil.org/take-ielts/book?utm_source=network&utm_medium=display&utm_campaign=exams-all-ielts-global-global-gelbooknow','_blank');
	});
    $("form").on('input', "input, select", function (e) {
        validateInput($(e.target));
    });

    document.addEventListener('invalid', (function () {
        return function (e) {
            e.preventDefault();
        };
    }), true);

    /**
     * @param el
     */
    function validateInput(el) {
        let parent = el.closest('div.input.required');
        let msg = el.attr('data-validation-message');
        let name = el.attr('name');
        if (el.attr('required')) {
            if (parent !== undefined && parent.length) {
                if (isValid(el)) {
                    parent.removeClass('has-error');
                } else {
                    parent.addClass('has-error');
                }

                if (msg !== undefined && msg.length && name.length && !$(".validation-message[data-for=" + name + "]").length) {
                    parent.append("<span class='validation-message' data-for='" + name + "'>" + msg + "</span>");
                }
            }
        }

        /**
         * @param el
         * @returns {boolean|jQuery|undefined|null|*|{}}
         */
        function isValid(el) {
            if (el.is("select")) {
                return el.val().length > 0;
            }

            switch (el.attr('type')) {
                case 'text':
                case 'textarea':
                case 'password':
                    return el.val().length > 0;
                case 'checkbox':
                case 'radio':
                    return el.is(':checked');
                case 'email':
                    return typeof el[0].checkValidity === 'function' ? el[0].checkValidity() : /\S+@\S+\.\S+/.test(el.val());
            }
        }
    }
});
