# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

# This script just saves the running config of a device and acts
# as an example for running other commands.

from typing import List, Dict
from cloudvision.cvlib import ActionFailed

ctx.info("Saving Running-Config.")
cmds = [
    "enable",
    "copy running-config startup-config"
]
cmdResponses: List[Dict] = ctx.runDeviceCmds(cmds)
# Iterate through the list of responses for the commands, and if an error occurred in
# any of the commands, raise an exception
# Only consider the first error that is encountered
# as following commands require previous ones to succeed
errs = [resp.get('error') for resp in cmdResponses if resp.get('error')]
if errs:
    raise ActionFailed(f"Saving running config failed with: {errs[0]}")
