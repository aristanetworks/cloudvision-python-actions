# Copyright (c) 2022 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

# Note: This script will become obsolete once the image studio system
# becomes available, after which this only serves as an example of script writing

from typing import List, Dict
from urllib.parse import urljoin

from cloudvision.cvlib import ActionFailed

authority = ctx.action.args.get("authority")
path = ctx.action.args.get("path")
eos = ctx.action.args.get("eos")
vrf = ctx.action.args.get("vrf")
imageUrl = urljoin(f"https://{authority}", path + eos)

ctx.info(f"Downloading EOS image from {imageUrl}")
cmds = [
    "enable",
    f"cli vrf {vrf}",
    f"copy {imageUrl} flash:",
]
cmdResponses: List[Dict] = ctx.runDeviceCmds(cmds)
# Iterate through the list of responses for the commands, and if an error occurred in
# any of the commands, raise an exception
# Only consider the first error that is encountered as following
# commands require previous ones to succeed
errs = [resp.get('error') for resp in cmdResponses if resp.get('error')]
if errs:
    raise ActionFailed(f"Preloading image failed with: {errs[0]}")
ctx.info("Downloading of Eos image completed successfully")
