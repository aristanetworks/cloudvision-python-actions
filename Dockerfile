# Copyright (c) 2022 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

FROM python:3.8
LABEL maintainer="Arista Networks support@arista.com"

RUN python -m pip install flake8==3.8.3 mypy==0.782
