(function () {
	var instructionsNote;
	let element = $("*[data-instructions-note]:visible");
    let instructionsNoteText = element.attr('data-instructions-note');

    setupInstructionsNote(instructionsNoteText);
    /**
     * @param instructionsNoteText
     */
    function setupInstructionsNote(instructionsNoteText) {
        if (instructionsNote === undefined) {
            instructionsNote = new Note({contentEditable: false, additionalClass: 'instructions-note'});
            instructionsNote.note.left = '80%';
            instructionsNote.note.top = '60%';
        }

        if (instructionsNoteText.length && instructionsNote) {
            instructionsNote.text = instructionsNoteText;
        } else if (instructionsNote) {
            instructionsNote.close();
        }
    }

    // Restore state from server on page load
    function restoreState() {
        let sessionId = $("#session").attr('data-session-id');
        if (!sessionId) return;

        $.ajax({
            url: "/state?session_id=" + encodeURIComponent(sessionId),
            type: 'GET',
            dataType: 'json',
            success: function(states) {
                for (var tid in states) {
                    var st = states[tid];
                    var $status = $('.info-status[data-test-id="' + tid + '"]');
                    var $startBtn = $('.btn.start-test[data-test-id="' + tid + '"]');
                    var $ready = $('.ready[data-test-id="' + tid + '"]');
                    var $completion = $('.one-test').eq(parseInt(tid) - 1).find('.completion-status');

                    // Update completion status
                    if (st.completed) {
                        $completion.removeClass('not-completed').addClass('completed').text('Completed');
                    }

                    // Update confirm status
                    if (st.confirmed || st.completed) {
                        $status.removeClass('not-confirmed').addClass('confirmed').text('Confirmed.');
                    }

                    // Show/hide start button and ready section
                    if (st.confirmed && !st.completed) {
                        $startBtn.show();
                        $ready.hide();
                    }
                }
            }
        });
    }

    restoreState();

    $(document).on('click tap', '.info-confirm', function (event) {
        console.log('confirm')
        let sessionId = $("#session").attr('data-session-id');
        let testId = $(this).attr('data-test-id');

        let data = {
            "session_id": sessionId,
            "test_id": testId
        };

        let target = $(this);
        $.ajax({
            url: "/confirm",
            beforeSend: function (request) {
                request.setRequestHeader('X-CSRF-Token', csrfToken);
            },
            xhrFields: {
                withCredentials: true
            },
            type: 'POST',
            dataType: 'json',
            contentType: 'application/json',
            success: function (data) {
                $('.info-status[data-test-id="' + testId + '"]').removeClass('not-confirmed').addClass('confirmed').html('Confirmed.');
                $('.btn.start-test[data-test-id="' + testId + '"]').show();
                $('.ready[data-test-id="' + testId + '"]').hide();
            },
            data: JSON.stringify(data)
        });
    });
})();
