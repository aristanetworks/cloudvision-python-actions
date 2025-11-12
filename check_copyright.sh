#!/bin/bash
# Copyright (c) 2022 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

# This script checks if all the changed files in current revision
# have proper copyright headers
#
# Usage: ./check_copyright.sh [<branch>]
#
# 	branch is optional - you can provide base branch manually (e.g `trunk`)
#	otherwise it would use `git log --first-parent`

# egrep that comes with our Linux distro doesn't like \d, so use [0-9]
notice='Copyright \(c\) 20[0-9][0-9] Arista Networks, Inc.'
apacheNotice="Use of this source code is governed by the Apache License 2.0"
apacheNoticeSource="that can be found in the COPYING file."
confidential="Confidential and Proprietary"

# To omit dubious ownership git errors
repoFolder=`dirname "${BASH_SOURCE[0]}"`
cd $repoFolder && git config --global --add safe.directory $repoFolder

if [ ! -z "$1" ]; then
	branchBaseCommit=`git show $1 --format=format:%H --no-patch`
	exitCode=$?
	if [ $exitCode != "0" ]; then
		echo Error finding revision $1
		exit $exitCode
	fi
else
	branchBaseCommit=`git show --first-parent --format=format:%H --no-patch`
fi

files=`git diff-tree --no-commit-id --name-only --diff-filter=ACMR -r $branchBaseCommit | \
	egrep '\.(py|sh)$'`
status=0

for file in $files; do
	if egrep -q "$confidential" $file; then
		# Need to omit the check_copyright script from this check as it will always fail
		if [ "$file" != "check_copyright.sh" ]; then
			echo "$file: use of confidential material per copyright notice"
			status=1
		fi
	fi
	if ! egrep -q "$notice" $file; then
		echo "$file: missing or incorrect copyright notice for Arista"
		status=1
	fi
	if ! egrep -q "$apacheNotice" $file; then
		echo "$file: missing or incorrect Apache Licence 2.0 notice"
		status=1
	fi
	if ! egrep -q "$apacheNoticeSource" $file; then
		echo "$file: missing or incorrect Apache Licence 2.0 notice COPYING directive"
		status=1
	fi
done

exit $status
