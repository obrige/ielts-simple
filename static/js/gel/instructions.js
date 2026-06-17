$(function () {
    var instructionsNote;
    $(window).on('stepsStarted stepsChanged testFinished', function (e) {
        let element = $("*[data-instructions-note]:visible");
        let instructionsNoteText = element.attr('data-instructions-note');

        setupInstructionsNote(instructionsNoteText);
    });

    $(window).on('stepsEnded', function (e) {
        if (instructionsNote) {
            instructionsNote.close();
        }
    });

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
});
