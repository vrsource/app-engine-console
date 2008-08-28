# App Engine Console MVC Controller
#
# This file is part of App Engine Console.
#
# App Engine Console is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# App Engine Console is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with App Engine Console; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import os
import re
import sys
import cgi
import string
import logging
import traceback
import simplejson

import pygments
import pygments.lexers
import pygments.formatters

import model

from google.appengine.api        import users
from google.appengine.ext        import db
from google.appengine.ext        import webapp
from google.appengine.ext.webapp import template


# In production mode (hosted at Google), anonymous users may not use the console.
# But in development mode, anonymous users may.  If you still want to disallow
# anonymous users from using the console from the development SDK, set this
# variable to True.
require_login_during_development = False

# In production mode, only administrators may use the console. However, if you
# really want to allow any regular logged-in user to use the console, you can
# set this variable to True.
allow_any_user = False

#
# No more configuration settings below here
#

# Unpicklable statements to seed new sessions with.
INITIAL_UNPICKLABLES = [
    'try: from autoexec import *\nexcept ImportError: pass',
]


def is_dev():
    """Return whether the application environment is in development mode."""
    return os.environ['SERVER_SOFTWARE'].startswith('Dev')

def is_production():
    return (not is_dev())


class ConsoleError(Exception):
    """General error in console"""

class NotLoggedInError(ConsoleError):
    """Login required"""

class NotAdminError(ConsoleError):
    """Admin required"""

class Statement(webapp.RequestHandler):
    def __init__(self):
        self.lexer = pygments.lexers.PythonLexer()
        self.resultLexer = pygments.lexers.PythonConsoleLexer()
        self.formatter = pygments.formatters.HtmlFormatter()

    def write(self, *args, **kw):
        self.response.out.write(*args, **kw)

    def confirm_permission(self):
        """Raises an exception if the user does not have permission to execute a statement"""
        user = users.get_current_user()
        nologin = NotLoggedInError('Hello! Please $login_link to use this console')
        noadmin = NotAdminError('Please $logout_link, then log in as an administrator')

        if is_production():
            if not user:
                raise nologin
            else:
                if allow_any_user:
                    pass                    # Do what the man says.
                else:
                    if users.is_current_user_admin():
                        pass                # Grant access to the admin.
                    else:
                        raise noadmin       # Administrator access required in production mode
        else:
            if not require_login_during_development:
                pass                        # Unrestricted access during development mode
            else:
                if user:
                    pass                    # Logged-in user allowed, even in development mode.
                else:
                    raise nologin             # Unlogged-in user not allowed in development mode

    def get(self):
        id   = self.request.get('id')
        code = self.request.get('code')
        session_key = self.request.get('session')
        output_templating = False

        try:
            self.confirm_permission()
        except ConsoleError:
            exc_type, exc_value, tb = sys.exc_info()
            stack = traceback.extract_tb(tb)
            stack.insert(0, ('<stdin>', 1, '<module>', code))

            output = ('Traceback (most recent call last):\n' +
                      ''.join(traceback.format_list(stack)) +
                      ''.join(traceback.format_exception_only(exc_type, exc_value)))
            result = False
            output_templating = True
        else:
            # Access granted.
            engine = model.AppEngineConsole.get(session_key)
            result = engine.runsource(code)
            output = engine.output.strip()

        highlighting = (self.request.get('highlight') != '0')
        if highlighting:
            logging.debug('Highlighting code')
            code = pygments.highlight(code, self.lexer, self.formatter)
            code = code.strip().replace('\n', '')

            if result == False:
                output = pygments.highlight(output, self.resultLexer, self.formatter).strip()

        if output_templating:
            output = string.Template(output).safe_substitute({
                'login_link' : ('<a href="%s">log in</a>' % users.create_login_url('/console/')),
                'logout_link': ('<a href="%s">log out</a>' % users.create_logout_url('/console/')),
            })

        response = {
            'id' : id,
            'in' : code,
            'out': output,
            'result': result,
        }

        self.response.headers['Content-Type'] = 'application/x-javascript'
        self.write(simplejson.dumps(response))
        logging.debug('sending')

class Banner(webapp.RequestHandler):
    def get(self):
        logging.debug('Fetching banner')

        copyright = 'Type "help", "copyright", "credits" or "license" for more information.'
        banner = "Python %s on %s\n%s\n(%s)" % (sys.version, sys.platform, copyright, os.environ['SERVER_SOFTWARE'])

        self.response.headers['Content-Type'] = 'application/x-javascript'
        self.response.out.write(simplejson.dumps({'banner':banner}))

class Page(webapp.RequestHandler):
    """A human-visible "page" that presents itself to a person."""
    templates = os.path.join(
        os.path.dirname(
            os.path.dirname(__file__)),
        'view',
        'templates')
    appID = os.environ['APPLICATION_ID']
    appVersion = os.environ['CURRENT_VERSION_ID']

    def __init__(self, *args, **kw):
        webapp.RequestHandler.__init__(self, *args, **kw)

        myClass = re.search(r"<class '.*\.(.*)'", str(self.__class__)).groups()[0]
        self.page = myClass.lower()

        path = os.environ['PATH_INFO']

        self.values = {}
        self.values['app']        = self.appID
        self.values['path']       = path
        self.values['is_dev']     = is_dev()
        self.values['log_in']     = users.create_login_url(path)
        self.values['log_out']    = users.create_logout_url(path)
        self.values['version']    = self.appVersion
        self.values['subpages']   = self.subpages
        self.values['controller'] = self.page.capitalize()

        self.values['pages']    = [ {'name':'Console', 'href':'/console/'},
                                    {'name':'Help'   , 'href':'/console/help/'} ]


        match = re.search(r'^/console/%s/(.+)$' % self.page, path)
        if match:
            # Handle a sub-path which is within the main controller path (e.g. /help/something instead of just /help).
            self.values['subpage'] = match.groups()[0]
        else:
            self.values['subpage'] = ''
            if self.subpages:
                # The default sub-page is the first one in the list.
                self.values['subpage'] = self.subpages[0]

        templateFile = '%s_%s.html' % (self.page, self.values['subpage'])
        self.template = os.path.join(self.templates, templateFile)

    def write(self):
        logging.debug("Writing with '%s':\n%s" % (self.template, repr(self.values)))
        self.response.out.write(template.render(self.template, self.values))

    def do_get(self):
        """This is called upon an HTTP GET.  It may be implemented by the subclass."""
        pass

    def get(self):
        self.values['user'] = users.get_current_user()
        self.do_get()
        if not hasattr(self, 'done') or self.done != True:
            self.write()

class Console(Page):
    subpages = []

    def do_get(self):
        # Set up the session. TODO: garbage collect old shell sessions
        session_key = self.request.get('session')
        if session_key:
            session = model.AppEngineConsole.get(session_key)
        else:
            # Create a new session.
            session = model.AppEngineConsole()
            session.unpicklables = [db.Text(line) for line in INITIAL_UNPICKLABLES]
            session_key = session.put()

        room = '%s-appengine-console' % self.appID

        self.values['session']  = str(session_key)
        self.values['settings'] = [
            {'id':'session'  , 'value':session_key       , 'type':'hidden'},
            {'id':'room'     , 'value':room              , 'type':'hidden'},

            {'id':'highlight', 'options': ['Highlighting', 'No highlighting']},
            {'id':'teamwork' , 'options': ['Flying Solo' , 'Pastebin', 'Chatting']},
        ]

class Help(Page):
    subpages = ['usage', 'about']

class Root(Page):
    subpages = []
    def do_get(self):
        self.redirect('/console/')
        self.done = True

__all__ = ['Console', 'Help', 'Statement', 'Banner', 'Root']

if __name__ == "__main__":
    logging.error('I should be running unit tests')
