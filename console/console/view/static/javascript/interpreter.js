/*

    Interpreter: JavaScript Interactive Interpreter

*/
InterpreterManager = function () {
    bindMethods(this);
};

InterpreterManager.prototype.initialize = function () {
    var interpreter = getElement("interpreter_text");
    if(interpreter != null)
        interpreter.focus();

    this.lines = [];
    this.history = [];
    this.currentHistory = "";
    this.historyPos = -1;
    this.blockingOn = null;
    if (typeof(this.doEval) == "undefined") {
        // detect broken eval, warn at some point if a namespace ever gets used
        this.doEval = function () {
            return eval(arguments[0]);
        }
    }

    window.help = this.help;
    this.help.NAME = 'type help(func) for help on a MochiKit function';

    if(getElement('setting_teamwork') != null) {
        connect('setting_teamwork', 'onchange', this.setTeamwork);

        // Also, get the current setting as some browsers cache the choice through a reload.
        this.setTeamwork();
    }
};

InterpreterManager.prototype.doScroll = function () {
    var p = getElement("interpreter_output").lastChild;
    if (typeof(p) == "undefined" || p == null) {
        return;
    }
    var area = getElement("interpreter_area");
    if (area.offsetHeight > area.scrollHeight) {
        area.scrollTop = 0;
    } else {
        area.scrollTop = area.scrollHeight;
    }
};

InterpreterManager.prototype.moveHistory = function (dir) {
    // totally bogus value
    if (dir == 0 || this.history.length == 0) {
        return;
    }
    var elem = getElement("interpreter_text");
    if (this.historyPos == -1) {
        this.currentHistory = elem.value;
        if (dir > 0) {
            return;
        }
        this.historyPos = this.history.length - 1;
        elem.value = this.history[this.historyPos];
        return;
    }
    if (this.historyPos == 0 && dir < 0) {
        return;
    }
    if (this.historyPos == this.history.length - 1 && dir > 0) {
        this.historyPos = -1;
        elem.value = this.currentHistory;
        return;
    } 
    this.historyPos += dir;
    elem.value = this.history[this.historyPos];
}

InterpreterManager.prototype.doSubmit = function () {
    var elem = getElement("interpreter_text");
    var code = elem.value;

    this.runCode(allCode, id);

    var consoleWindow = this;

    try {
        var values = {
            'id'       : id,
            'session'  : getElement('setting_session').value,
            'highlight': highlight,
            'code'     : allCode
        };

        var d = loadJSONDoc('/console/statement', values);

        var fetchSuccess = function(response) {
            var oldCode = getElement(response.id);
            oldCode.innerHTML = response.in;
            
            if(!isEmpty(response.out))
                consoleWindow.showResult(response.out);

            window.showPrompt(response.result);
        };

        var fetchFail = function(err) {
            alert('Query failed');
            // TODO: Perhaps append the prompt.
        };

        d.addCallbacks(fetchSuccess, fetchFail);
    } catch (e) {
        // mozilla shows some keys more than once!
        this.showError(e);
        return;
    }
};

window.writeln = function () {
    appendChildNodes("interpreter_output",
        SPAN({"class": "data"}, arguments),
        BR()
    );
    interpreterManager.doScroll();
};

window.clear = function () {
    replaceChildNodes("interpreter_output");
    getElement("interpreter_area").scrollTop = 0;
};

interpreterManager = new InterpreterManager();
addLoadEvent(interpreterManager.initialize);

InterpreterManager.prototype.setTeamwork = function (e) {
    /* Handle the various teamwork settings. */
    var choice = getElement('setting_teamwork').value;
    var talkinator = getElement('talkinator');
    var pastebin   = getElement('pastebin');
    var console    = getElement('console_interface');

    /* Talkinator stuff */
    var showTalkinator = function() {
        var room = getElement('setting_room').value;
        console.style.width = '75%';
        talkinator.style.width = '24.5%';
        talkinator.style.display = 'block';
        talkinator.innerHTML = 
            '<iframe width="250" height="540" marginwidth="0" marginheight="0" scrolling="no"' +
            '       style="border: 2px solid #93b7fa" frameborder="0"'                         +
            '       src="http://t8r4.info/$r?s=0&t=h&w=250&h=540&c=93b7fa&b=' + room + '"> '   +
            '</iframe>';
    };
    var hideTalkinator = function() {
        talkinator.innerHTML = '';
        talkinator.style.display = 'none';
        talkinator.style.width = '0';
        console.style.width = '100%';
    };

    /* Pastebin stuff */
    var showPastebin = function() {
        pastebin.style.display = 'block';
        pastebin.innerHTML = 
            '<iframe width="100%" height="400" marginwidth="0" marginheight="0" scrolling="yes"' +
            '       style="border: 2px solid #93b7fa" frameborder="0"'                          +
            '       src="http://pastebin.com/"> '                                               +
            '</iframe>';
    };
    var hidePastebin = function() {
        pastebin.innerHTML = '';
        pastebin.style.display = 'none';
    };

    if(choice == 'Chatting') {
        hidePastebin();
        showTalkinator();
    }
    else if(choice == 'Pastebin') {
        hideTalkinator();
        showPastebin();
    }
    else {
        hidePastebin();
        hideTalkinator();
    }
};
