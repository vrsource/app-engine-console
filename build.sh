#!/bin/bash
#
# Script to build an App Engine Console distribution.
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

source version.sh

if [ ! "$tagged" ]; then
    echo "This script must run on a tagged revision." >&2
    echo "Current tags:" >&2
    git tag | sed 's/^/ - /' >&2
    exit 1
fi

package="AppEngineConsole-$app_version"
target="$PWD/$package"
zipfile="$PWD/$package.zip"

echo "Building $zipfile"

set -e

rm -vf "$zipfile"
mkdir -p "$target"

allow_modified=1
if [ -z "$allow_modified" ]; then
    if ! git diff-index --quiet --cached "$app_version" --; then
        echo 'Error: This checkout has been modified from the tagged version' >&2
        exit 1
    fi
    if ! git diff-files --quiet; then
        echo 'Error: This checkout has been modified from the tagged version' >&2
        exit 1
    fi
fi

cp -r console/console "$target/console"

# Prepare for packaging.
find "$target" -type f -name '*.py[co]' -exec rm {} \;

cd "$target"
zip -r "$zipfile" console

cd ..
#rm -rf "$target"
