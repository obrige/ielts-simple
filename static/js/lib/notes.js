var captured = null;
var highestZ = 0;
var highestId = 0;

function Note(options) {
    var self = this;

    options.contentEditable = typeof options.contentEditable === "boolean" ? options.contentEditable : true;
    options.additionalClass = options.additionalClass ? ' ' + options.additionalClass : '';

    var note = document.createElement('div');
    note.className = 'note' + options.additionalClass;
    note.addEventListener('click', function(event) { return self.onNoteClick(event); }, false);
    this.note = note;

    var close = document.createElement('div');
    close.className = 'close';
    close.addEventListener('click', function(event) { return self.hide(event) }, false);
    note.appendChild(close);

    var handle = document.createElement('div');
    handle.className = 'draghandle';
    handle.addEventListener('mousedown', function(e) { return self.onMouseDown(e); }, false);
    note.appendChild(handle);

    var edit = document.createElement('div');
    edit.className = 'edit';
    note.appendChild(edit);

    if (!options || options.highlightText) {
		var highlight = document.createElement('div');
		highlight.className = 'highlightText';
		highlight.style.display = 'none';
		highlight.setAttribute('contenteditable', options.contentEditable);
		highlight.addEventListener('keyup', function() { return self.onKeyUp(); }, false);
		edit.appendChild(highlight);
		this.highlightField = highlight;
	}

    var main = document.createElement('div');
    main.className = 'mainText';
    main.setAttribute('contenteditable', options.contentEditable);
    main.addEventListener('keyup', function() { return self.onKeyUp(); }, false);
    edit.appendChild(main);
    this.editField = main;

    document.body.appendChild(note);
    return this;
}

Note.prototype = {
    get id()
    {
        if (!("_id" in this))
            this._id = 0;
        return this._id;
    },

    set id(x)
    {
        this._id = x;
    },

    get text()
    {
        return this.editField.innerHTML;
    },

    set text(x)
    {
        this.editField.innerHTML = x;
    },

    get hText()
    {
        return this.highlightField.innerHTML;
    },

    set hText(x)
    {
        if (x) {
			this.highlightField.style.display = 'block';
		} else {
			this.highlightField.style.display = 'none';
		}
		jQuery(this.highlightField).text(x);
    },

    get left()
    {
        return this.note.style.left;
    },

    set left(x)
    {
        this.note.style.right = "unset";
        this.note.style.left = x;
    },

    get top()
    {
        return this.note.style.top;
    },

    set top(x)
    {
        this.note.style.bottom = "unset";
        this.note.style.top = x;
    },

    get zIndex()
    {
        return this.note.style.zIndex;
    },

    set zIndex(x)
    {
        this.note.style.zIndex = x;
    },

    hide: function(event)
    {
		jQuery(this.note).fadeOut(250);
    },

    close: function(event)
    {

        var note = this;

		jQuery(this.note).fadeOut(300, function() {
			$(this).remove();
		});
    },

    onMouseDown: function(e)
    {
        captured = this;
        this.startX = e.clientX - this.note.offsetLeft;
        this.startY = e.clientY - this.note.offsetTop;
        this.zIndex = ++highestZ;

        var self = this;
        if (!("mouseMoveHandler" in this)) {
            this.mouseMoveHandler = function(e) { return self.onMouseMove(e) }
            this.mouseUpHandler = function(e) { return self.onMouseUp(e) }
        }

        document.addEventListener('mousemove', this.mouseMoveHandler, true);
        document.addEventListener('mouseup', this.mouseUpHandler, true);

        return false;
    },

    onMouseMove: function(e)
    {
        if (this != captured)
            return true;

        this.left = e.clientX - this.startX + 'px';
        this.top = e.clientY - this.startY + 'px';
        return false;
    },

    onMouseUp: function(e)
    {
        document.removeEventListener('mousemove', this.mouseMoveHandler, true);
        document.removeEventListener('mouseup', this.mouseUpHandler, true);

        return false;
    },

    onNoteClick: function(e)
    {
        if (e.target.className === 'highlightText') {
			this.highlightField.focus();
		} else {
			this.editField.focus();
		}
    },

    onKeyUp: function()
    {
        this.dirty = true;
    },
}
