/* App Engine Console client-side functionality
 *
 * This file is part of App Engine Console.
 *
 * App Engine Console is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, version 3 of the License.
 *
 * App Engine Console is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with App Engine Console; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 */

//(function() {

// Processing begins here.
var main = function() {
    console.debug('Starting');

    $('#console_form').submit(statementSubmit);
    $('#console_statement').keyup(statementKeyUp);
};

var statementSubmit = function(event) {
    try {
        var input = $('#console_statement');
        var statement = input.val();
        console.debug('Statement submitted: %s', statement);

        if(statement == 'clear') {
            cls();
            return;
        }

        var id = 'statement_' + uid();
        $('#console_output').append(
            $('<div>')
                .attr('id', id)
                .addClass('code').addClass('pygments')
                .append(
                    $('<span>')
                        .addClass('code')
                        .append(statement))
        ).append('<br/>');

        input.val('');

        scrollOutput();
    }
    finally {
        event.preventDefault();
    }
};

var statementKeyUp = function(event) {
    var orig = event.originalEvent;
    if(orig.shiftKey || orig.altKey || orig.metaKey || orig.ctrlKey) {
        console.debug('Ignoring keypress with a modifier key');
        return;
    }

    var key = event.charCode || event.keyCode || 0;
    switch(key) {
        case 38:
            moveHistory(-1);
            break;
        case 40:
            moveHistory(1);
            break;
    }
};

var cls = function() {
    console.debug('Clearing screen');
};

var moveHistory = function(delta) {
    console.debug('Moving history by %d', delta);
};

var scrollOutput = function() {
    console.debug('TODO: scroll output window');
};

/* Generate IDs unique for the current page load. It uses a closure to maintain state. */
var uid = (function() {
        var id = 0;
        return function() {
            return id++;
        };
    }
)();

//
// __END__
//

// Support no-op logging in a non-Firebug environment.
try {
    console;
}
catch(e) {
    var noop = function() {};
    console = {
        'debug' : noop,
        'info'  : noop,
        'error' : noop
    };
}

$(document).ready(main);

//})();
