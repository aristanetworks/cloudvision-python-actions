# Copyright (c) 2022 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

.PHONY: bundled_actionpacks actionpacks dist lint

lint:
	flake8
	./check_copyright.sh

# Packages up all actionpacks in the repo listed in the bundled.yaml file
bundled_actionpacks:
	./build_bundled_actionpacks.sh

# Packages up all actionpacks in the repo
actionpacks:
	./build_actionpacks.sh

dist: actionpacks
	cd gen && sha512sum * > CHECKSUMS.sha512
