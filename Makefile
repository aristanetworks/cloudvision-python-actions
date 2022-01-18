# Copyright (c) 2022 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

.PHONY: actionpacks lint

lint:
	flake8

# Packages up all actionpacks in the repo
actionpacks:
	mkdir gen
	find . -mindepth 1 -maxdepth 1 -name "*action-pack" -type d -execdir tar cf {}.tar {} \;
	mv *.tar gen