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
from google.appengine.ext.webapp.util import run_wsgi_app

class AppEngineInterpreter(code.InteractiveInterpreter):
    """An interactive interpreter suitable for running within the App Engine."""
    __shared_state = {}

    def __init__(self, *args, **kw):
        self.__dict__ = self.__shared_state
        code.InteractiveInterpreter.__init__(self, *args, **kw)

        self.stdout = sys.stdout
        self.stderr = sys.stderr
        self.buf    = StringIO.StringIO()

        self.output  = None
        self.pending = ''
        
    def runsource(self, source, *args, **kw):
        logging.debug('self: %s' % self)
        logging.debug('input source: %s' % source)

        if self.pending:
            source = self.pending + source
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
            self.pending = ''
        else:
            logging.debug('Code not complete, saving pending source')
            self.pending = '%s\n' % source
            self.output = ''

        return result

class Console(webapp.RequestHandler):
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

application = webapp.WSGIApplication([('/console', Console)], debug=True)

def main():
    logging.getLogger().setLevel(logging.DEBUG)
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
