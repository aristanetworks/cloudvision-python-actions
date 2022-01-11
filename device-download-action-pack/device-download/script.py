# Copyright (c) 2021 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.


# https://bb/414515
# RFE: CVP - retrieve files from (show tech outputs, core files, etc)devices
# Customer would like to be able to use CVP to download files from managed devices.
# It would prompt for a destination (e.g. http or ftp & a destination URL), and then
# run show tech on each switch and upload that file to the destination server?
# It would still be useful to collect debug data without copying it (e.g. just saving it to disk on
# the switch), but would be even more useful if we can get it to some place TAC can access it
# automagically.
# I still think CC Actions are the best place for this, but note that on CVaaS TAC may not have
# permission to run these by default (I think that's ok though).


# How do
# Need to run whatever command on a device
#  - Do we want a default command that is run? e.g. Show tech?
#  - Where is the output going to be?
#     - is the output even in file form?
#        - If it is in a file format, is the file location customisable if so?
#           - If it is customisable, where do we put it and what do we name it
#     - if it is not in file form, do we need to pipe it into a temp file?
#        - where do we put it and what do we name it
# Sending file from device/switch to destination (download files from managed devices)
#  - From bug, should we by default collect data without copying it (e.g. save to switch disk)
#  - Protocol - HTTP or ftp
#     - What protocol by default? Do we just error if not specified?
#     - Will we need auth info for whereever we're sending the files to?
#        - How do we want to do that? Don't want pw as a param as it will be visible in UI in plaintext? Does hidden variable handles this?
