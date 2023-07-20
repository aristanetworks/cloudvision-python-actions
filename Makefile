# Copyright (c) 2022 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

.PHONY: actionpacks dist lint

lint:
	flake8
	./check_copyright.sh

# Packages up all actionpacks in the repo
actionpacks:
	mkdir -p gen
	find . -mindepth 1 -maxdepth 1 -name "*action-pack" -type d -execdir tar cf {}.tar {} \;
	mv *.tar gen

# Use this option for OS X systems. It includes the `--disable-copyfile` flag which stops copyfiles
# being added to the tar file. If these are in the tar file the actions endpoint rejects the pack
actionpacks-mac:
	mkdir -p gen
	find . -mindepth 1 -maxdepth 1 -name "*action-pack" -type d -execdir tar --disable-copyfile -cf {}.tar {} \;
	mv *.tar gen

dist: actionpacks
	cd gen && sha512sum * > CHECKSUMS.sha512