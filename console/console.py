# The WSGI entry-point for App Engine Console
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
import sys
import cgi
import code
import logging
import StringIO
import simplejson

# For some reason, sys.modules wants __builtin__ or else the InteractiveInterpreter
# will throw exceptions when evaluating expressions.
import __builtin__

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api import memcache

from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

class AppEngineInterpreter(code.InteractiveInterpreter):
    """An interactive interpreter suitable for running within the App Engine."""
    def __init__(self, *args, **kw):
        code.InteractiveInterpreter.__init__(self, *args, **kw)

        self.stdout = sys.stdout
        self.stderr = sys.stderr
        self.buf    = StringIO.StringIO()

        self.output  = None

    def getPending(self):
        pending = memcache.get('pending')
        if pending is None:
            pending = ''
        return pending
    
    def setPending(self, pending):
        result = memcache.set('pending', pending)
        if result == False:
            raise Exception, 'Failed to set the pending value in memcache'

    def runsource(self, source, *args, **kw):
        logging.debug('self: %s' % self)
        logging.debug('input source: %s' % source)

        pending = self.getPending()
        if pending:
            source = pending + source
            logging.debug('full source:\n%s' % source)
        else:
            logging.debug('not pending')

        sys.stdout, sys.stderr = self.buf, self.buf
        result = code.InteractiveInterpreter.runsource(self, source, *args, **kw)
        sys.stdout, sys.stderr = self.stdout, self.stderr

        if result == False:
            self.buf.seek(0)
            self.output = self.buf.read()
            self.buf.truncate(0)

            logging.debug('Execution completed: %s' % self.output)
            self.setPending('')
        else:
            logging.debug('Code not complete, saving pending source')
            self.setPending('%s\n' % source)
            self.output = ''

        return result

class Statement(webapp.RequestHandler):
    def __init__(self):
        self.engine = AppEngineInterpreter(globals())
        #self.engine = AppEngineInterpreter(locals())
        #self.engine = AppEngineInterpreter()

    def write(self, *args, **kw):
        self.response.out.write(*args, **kw)

    def get(self):
        code = self.request.get('code')

        result = self.engine.runsource(code)
        response = {
            'in' : code,
            'out': self.engine.output.strip(),
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

class Console(webapp.RequestHandler):
    def get(self):
        values = {
            'is_dev': os.environ['SERVER_SOFTWARE'].startswith('Dev'),
        }

        user = users.get_current_user()
        if user:
            values['user']     = user
            values['email']    = user.email()
            values['nickname'] = user.nickname()

        path = os.path.join(os.path.dirname(__file__), 'templates/console.html')
        self.response.out.write(template.render(path, values))

application = webapp.WSGIApplication([
    ('/'         , Console),
    ('/statement', Statement),
    ('/banner'   , Banner),
], debug=True)

def main():
    logging.getLogger().setLevel(logging.DEBUG)
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
