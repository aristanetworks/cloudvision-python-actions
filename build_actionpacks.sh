#!/bin/sh

set -e

artifacts_dir=gen

for pkgDir in ./src/*; do
	pkg=`basename $pkgDir`
	version=`cat src/$pkg/config.yaml | grep version | awk '{print $2}'`
	tar -C src -cf $artifacts_dir/$pkg"_"$version.tar $pkg
done
