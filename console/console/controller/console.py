# App Engine Console MVC Controller
#
# Copyright 2008 Proven Corporation Co., Ltd., Thailand
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
import sets
import string
import logging
import traceback
import exceptions

import pygments
import pygments.lexers
import pygments.formatters

import model

from google.appengine.api        import users
from google.appengine.ext        import db
from google.appengine.ext        import webapp
from google.appengine.ext.webapp import template
from django.utils                import simplejson

# In production mode (hosted at Google), anonymous users may not use the console.
# But in development mode, anonymous users may.  If you still want to disallow
# anonymous users from using the console from the development SDK, set this
# variable to True.
require_login_during_development = False

# In production mode, only administrators may use the console. However, if you
# really want to allow any regular logged-in user to use the console, you can
# set this variable to True.
allow_any_user = True

# Set this to True to enable automatic HTML links to the Python documentation for
# exceptions, types, modules, etc.
python_doc_linking = True

# The location of the newer (Sphinx) Python documentation.  If you have a local
# copy, you can set this to use your own version instead.
PYTHON_DOC = 'http://docs.python.org/dev'

#
# No more configuration settings below here
#

# Unpicklable statements to seed new sessions with.
INITIAL_UNPICKLABLES = [
    'try: from autoexec import *\nexcept ImportError: pass',
]

DOCUMENTED_EXCEPTIONS = sets.Set()
for name in dir(exceptions):
    e = getattr(exceptions, name)
    if (type(e) is type) and issubclass(e, exceptions.BaseException):
        DOCUMENTED_EXCEPTIONS.add(e)

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
    lexer           = pygments.lexers.PythonLexer()
    resultLexer     = pygments.lexers.PythonConsoleLexer()
    inputFormatter  = pygments.formatters.HtmlFormatter(cssclass='statement')
    outputFormatter = pygments.formatters.HtmlFormatter(cssclass='stdout')
    errorFormatter  = pygments.formatters.HtmlFormatter(cssclass='stderr')

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
                    raise nologin           # Unlogged-in user not allowed in development mode

    def post(self):
        code = self.request.get('code')
        session_key = self.request.get('session')
        output_templating = False
        out, err = '', ''

        engine = model.AppEngineConsole.get(session_key)

        username = users.get_current_user()
        if not username:
            username = '[Unknown User]'

        try:
            self.confirm_permission()
        except ConsoleError:
            exc_type, exc_value, tb = sys.exc_info()
            logging.info('Console error %s for: %s' % (exc_type, username))

            stack = (('<stdin>', 1, '<module>', code),)
            output = ('Traceback (most recent call last):\n' +
                      ''.join(traceback.format_list(stack)) +
                      ''.join(traceback.format_exception_only(exc_type, exc_value)))
            result = False
            output_templating = True
        else:
            # Access granted.
            result = engine.runsource(code)
            out = engine.out
            err = engine.err

        highlighting = (self.request.get('highlight') != '0')
        if highlighting:
            logging.debug('Highlighting code')
            code = pygments.highlight(code, self.lexer, self.inputFormatter)

            if out:
                out = self.highlight(out)
            if err:
                err = self.highlight(err, engine.exc_type)

        # XXX TODO: should make this only happen during highlighting
        if output_templating:
            err = string.Template(err).safe_substitute({
                'login_link' : ('<a href="%s">log in</a>' % users.create_login_url('/console/')),
                'logout_link': ('<a href="%s">log out</a>' % users.create_logout_url('/console/')),
            })

        response = {
            'in' : code,
            'out': out + err,
            'result': result,
        }

        self.response.headers['Content-Type'] = 'application/x-javascript'
        self.write(simplejson.dumps(response))

    def highlight(self, code, exc_type=None):
        """Return syntax-highlighted code using the PythonConsole lexer."""
        plain = code
        formatter = self.outputFormatter
        if exc_type:
            formatter = self.errorFormatter

        output = pygments.highlight(plain, self.resultLexer, formatter).strip()

        # Fancy linking to documented parts of Python.
        if not python_doc_linking:
            return output

        # Otherwise, try to find stuff to link to.
        name, link = None, None

        def doclink(path, name):
            """Return an HTML link to the documentation"""
            return '<a href="%s%s">%s</a>' % (PYTHON_DOC, path, name)

        if exc_type in DOCUMENTED_EXCEPTIONS:
            name = exc_type.__name__
            link = doclink('/library/exceptions.html#exceptions.%s' % name, name)

        match = re.search(r"<(module '(.*?)') \(built-in\)>$", plain)
        if match:
            name, mod_name = match.groups()
            name = name.replace("'", '&#39;')
            link = doclink('/library/%s.html' % mod_name, name)

        moduleRE = r"^<(module '(.*?)') from '%s/lib/python%d.%d/\2\.py[co]?'>$" % (sys.prefix, sys.version_info[0], sys.version_info[1])
        match = re.search(moduleRE, plain)
        if match:
            name, mod_name = match.groups()
            name = name.replace("'", '&#39;')
            link = doclink('/library/%s.html' % mod_name, name)

        match = re.search(r'^(None|False|True)$', plain)
        if match:
            name = match.groups()[0]
            link = doclink('/library/stdtypes.html#truth-value-testing', name)

        match = re.search(r"^<type '(int|float|long|complex)'>$", plain)
        if match:
            name = match.groups()[0]
            link = doclink('/library/stdtypes.html#numeric-types-int-float-long-complex', name)

        match = re.search(r"^<type '(str|unicode|list|tuple|buffer|xrange)'>$", plain)
        if match:
            name = match.groups()[0]
            link = doclink('/library/stdtypes.html#sequence-types-str-unicode-list-tuple-buffer-xrange', name)

        match = re.search(r"^<type '(set|frozenset)'>$", plain)
        if match:
            name = match.groups()[0]
            link = doclink('/library/stdtypes.html#set-types-set-frozenset', name)

        if plain == "<type 'dict'>":
            name = 'dict'
            link = doclink('/library/stdtypes.html#mapping-types-dict', name)

        if plain == "<type 'file'>":
            name = 'file'
            link = doclink('/library/stdtypes.html#file-objects', name)

        # Finally, do the replacing if needed.
        if name and link:
            logging.debug("Replacing output:\nold: %s\nnew: %s" % (name, link))
            output = output.replace(name, link)

        return output


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
    subpages = []

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

        self.values['pages']    = [ {'name':'Console'   , 'href':'/console/'},
                                    {'name':'Dashboard' , 'href':'/console/dashboard/'},
                                    {'name':'Help'      , 'href':'/console/help/'},
                                  ]

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

class Dashboard(Page):
    def do_get(self):
        if is_dev():
            options = ['Development', 'Production']
            #self.values['dashboard_url'] = '/_ah/admin'
            #self.values['settings'] = [ {'type':'link', 'name':'Production Dashboard',
        else:
            options = ['Production', 'Development']

        self.values['settings'] = [
            {'id':'dash_type', 'options':options},
            {'type':'hidden', 'id':'dash_url_pro', 'value':'http://appengine.google.com/dashboard?app_id=%s' % self.appID },
            {'type':'hidden', 'id':'dash_url_dev', 'value':'/_ah/admin'},
        ]

class Help(Page):
    subpages = ['usage', 'about']

class Root(Page):
    def do_get(self):
        self.redirect('/console/')
        self.done = True

__all__ = ['Console', 'Dashboard', 'Help', 'Statement', 'Banner', 'Root']

if __name__ == "__main__":
    logging.error('I should be running unit tests')
