#!/bin/sh

set -e

artifacts_dir=gen
bundled_actions=`cat bundled.txt`

for pkg in $bundled_actions; do
	version=`cat src/$pkg/config.yaml | grep version | awk '{print $2}'`
	id=`basename $pkg`
	tar -C src -cf $artifacts_dir/$id"_"$version.tar $id
done
