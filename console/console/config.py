# The App Engine Console configuration options

# Set this to true if you want to hide the console from non-authorized users
# by returning HTTP 404 (file not found), instead of the normal behavior.
hide_from_invalid_users = False

# In production mode (hosted at Google), anonymous users may not use the console.
# But in development mode, anonymous users may.  If you still want to disallow
# anonymous users from using the console from the development SDK, set this
# variable to True.
require_login_during_development = False

# In production mode, only administrators may use the console. However, if you
# really want to allow any regular logged-in user to use the console, you can
# set this variable to True.
allow_any_user = False

# Set this to True to enable automatic HTML links to the Python documentation for
# exceptions, types, modules, etc.
python_doc_linking = True

# The location of the newer (Sphinx) Python documentation.  If you have a local
# copy, you can set this to use your own version instead.
PYTHON_DOC = 'http://docs.python.org/dev'
