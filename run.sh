#!/bin/sh
#
# Wrapper to run the application in the development SDK.
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

# Set this to your own application name.
my_app="console"

if [ -d "$PWD/google_appengine" ]; then
    PATH="$PATH:$PWD/google_appengine"
fi

# For Git, the software "version" will be the timestamp of the latest
# commit to the branch in the repository.
app_version=`git log --pretty=format:'%ct%n' HEAD^..`
export app_version

exec dev_appserver.py "$my_app"
