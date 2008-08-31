# App Engine Console utility functions
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

def is_dev():
    """Return whether the application environment is in development mode."""
    return os.environ['SERVER_SOFTWARE'].startswith('Dev')

def is_production():
    return (not is_dev())

def app_id():
    """Return the application ID (i.e. <whatever>.appspot.com)."""
    return os.environ['APPLICATION_ID']

def is_my_website():
    """Returns True if this code is running at its own web site (con.appspot.com),
    since the functionality changes a little bit there.
    """
    return is_production() and (app_id() == 'con')
