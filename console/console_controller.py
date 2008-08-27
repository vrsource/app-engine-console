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
import logging
import simplejson

import console_model as model

from google.appengine.api        import users
from google.appengine.ext        import webapp
from google.appengine.ext.webapp import template

class Statement(webapp.RequestHandler):
    def __init__(self):
        self.engine = model.AppEngineInterpreter(globals())
        #self.engine = model.AppEngineInterpreter(locals())
        #self.engine = model.AppEngineInterpreter()

    def write(self, *args, **kw):
        self.response.out.write(*args, **kw)

    def get(self):
        id   = self.request.get('id')
        code = self.request.get('code')

        result = self.engine.runsource(code)
        response = {
            'id' : id,
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

class Page(webapp.RequestHandler):
    """A human-visible "page" that presents itself to a person."""
    templates = os.path.join(os.path.dirname(__file__), 'templates')
    appID = os.environ['APPLICATION_ID']
    appVersion = os.environ['CURRENT_VERSION_ID']

    def __init__(self, *args, **kw):
        webapp.RequestHandler.__init__(self, *args, **kw)

        myClass = re.search(r"<class '.*\.(.*)'", str(self.__class__)).groups()[0]
        self.page = myClass.lower()

        self.values = {}
        self.values['app']      = self.appID
        self.values['version']  = self.appVersion
        self.values['subpages'] = self.subpages
        self.values['is_dev']   = os.environ['SERVER_SOFTWARE'].startswith('Dev')
        self.values['pages']    = [ {'name':'Console', 'href':'/'},
                                    {'name':'Help'   , 'href':'/help/'} ]

        path = os.environ['PATH_INFO']
        self.values['path'] = path
        self.values['controller'] = self.page.capitalize()

        match = re.search(r'^/%s/(.+)$' % self.page, path)
        if match:
            # Handle a sub-path which is within the main controller path (e.g. /help/something instead of just /help).
            self.values['subpage'] = match.groups()[0]
        else:
            # The default sub-page is the first one in the list.
            self.values['subpage'] = self.subpages[0]

        templateFile = '%s_%s.html' % (self.page, self.values['subpage'])
        self.template = os.path.join(self.templates, templateFile)

    def write(self):
        logging.debug("Writing with '%s':\n%s" % (self.template, repr(self.values)))
        self.response.out.write(template.render(self.template, self.values))

class Console(Page):
    subpages = ['interactive']

    def get(self):
        user = users.get_current_user()
        if user:
            self.values['user']     = user
            self.values['email']    = user.email()
            self.values['nickname'] = user.nickname()

        self.write()

class Help(Page):
    subpages = ['usage', 'about']

    def get(self):
        self.write()

if __name__ == "__main__":
    logging.error('I should be running unit tests')
