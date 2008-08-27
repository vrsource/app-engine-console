# Based on the Google App Engine Samples project.

# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
An interactive Python console "session".

The logging, os, sys, db, and users modules are imported automatically.

Interpreter state is stored in the datastore so that variables, function
definitions, and other values in the global and local namespaces can be used
across commands.

TODO: unit tests!
"""

import logging
import new
import os
import sys
import traceback
import types

from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp

import model

# Types that can't be pickled.
UNPICKLABLE_TYPES = (
    types.ModuleType,
    types.TypeType,
    types.ClassType,
    types.FunctionType,
)

class StatementHandler(webapp.RequestHandler):
  """Evaluates a python statement in a given session and returns the result.
  """

  def get(self):
    self.response.headers['Content-Type'] = 'text/plain'

    # extract the statement to be run
    statement = self.request.get('statement')
    if not statement:
      return

    # the python compiler doesn't like network line endings
    statement = statement.replace('\r\n', '\n')

    # add a couple newlines at the end of the statement. this makes
    # single-line expressions such as 'class Foo: pass' evaluate happily.
    statement += '\n\n'

    # log and compile the statement up front
    try:
      logging.info('Compiling and evaluating:\n%s' % statement)
      compiled = compile(statement, '<string>', 'single')
    except:
      self.response.out.write(traceback.format_exc())
      return

    # create a dedicated module to be used as this statement's __main__
    statement_module = new.module('__main__')

    # use this request's __builtin__, since it changes on each request.
    # this is needed for import statements, among other things.
    import __builtin__
    statement_module.__builtins__ = __builtin__

    # load the session from the datastore
    session = model.ConsoleSession.get(self.request.get('session'))

    # swap in our custom module for __main__. then unpickle the session
    # globals, run the statement, and re-pickle the session globals, all
    # inside it.
    old_main = sys.modules.get('__main__')
    try:
      sys.modules['__main__'] = statement_module
      statement_module.__name__ = '__main__'

      # re-evaluate the unpicklables
      for code in session.unpicklables:
        exec code in statement_module.__dict__

      # re-initialize the globals
      for name, val in session.globals_dict().items():
        try:
          statement_module.__dict__[name] = val
        except:
          msg = 'Dropping %s since it could not be unpickled.\n' % name
          self.response.out.write(msg)
          logging.warning(msg + traceback.format_exc())
          session.remove_global(name)

      # run!
      old_globals = dict(statement_module.__dict__)
      try:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        try:
          sys.stdout = self.response.out
          sys.stderr = self.response.out
          exec compiled in statement_module.__dict__
        finally:
          sys.stdout = old_stdout
          sys.stderr = old_stderr
      except:
        self.response.out.write(traceback.format_exc())
        return

      # extract the new globals that this statement added
      new_globals = {}
      for name, val in statement_module.__dict__.items():
        if name not in old_globals or val != old_globals[name]:
          new_globals[name] = val

      if True in [isinstance(val, UNPICKLABLE_TYPES)
                  for val in new_globals.values()]:
        # this statement added an unpicklable global. store the statement and
        # the names of all of the globals it added in the unpicklables.
        session.add_unpicklable(statement, new_globals.keys())
        logging.debug('Storing this statement as an unpicklable.')

      else:
        # this statement didn't add any unpicklables. pickle and store the
        # new globals back into the datastore.
        for name, val in new_globals.items():
          if not name.startswith('__'):
            session.set_global(name, val)

    finally:
      sys.modules['__main__'] = old_main

    session.put()

__all__ = ['StatementHandler']

def main():
    logging.error("I should be running unit tests!")

if __name__ == '__main__':
    main()
