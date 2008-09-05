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
if ! [ -d "$my_app" ]; then
    echo "App not found: $my_app" >&2
    exit 1
fi

if [ -d "$PWD/google_appengine" ]; then
    PATH="$PATH:$PWD/google_appengine"
fi

git_tag=''

# For Git, the software "version" will be the timestamp of the latest
# commit to the branch in the repository, unless it is a tagged version,
# in which case the tag name will be used.
app_version=`git log --pretty=format:'%ct%n' | head -1`
commit=`git log --pretty=format:%H%n | head -1`
for tag in .git/refs/tags/*; do
    if [ -f "$tag" ]; then
        if cat "$tag" | grep "$commit" >/dev/null; then
            # This is a tagged commit, so use the tag.
            app_version=`basename "$tag" | sed 's/\./-/g'`
            git_tag=`basename "$tag"`
        fi
    fi
done

echo "app_version=$app_version"
export app_version
