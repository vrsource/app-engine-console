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

// Processing begins here.
var main = function() {
    console.debug('Starting');

    $('#console_statement').keyup(statementKeyUp);
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

var moveHistory = function(delta) {
    console.debug('Moving history by %d', delta);
};

/*
 * __END__
 */
$(document).ready(main);