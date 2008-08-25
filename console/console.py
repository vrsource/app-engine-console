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

import cgi
import simplejson

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import logging

class Console(webapp.RequestHandler):
  def write(self, *args, **kw):
    self.response.out.write(*args, **kw)

  def get(self):
    code = self.request.get('code')
    result = code
    response = {
        'in' : code,
        'out': result,
    }

    self.response.headers['Content-Type'] = 'application/x-javascript'
    self.write(simplejson.dumps(response))

application = webapp.WSGIApplication([('/console', Console)], debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
