# Copyright (c) 2022 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

from typing import List, Dict
from cloudvision.cvlib import ActionFailed

url = ctx.action.args.get("extensionURL")
extension = ctx.action.args.get("extension")
vrf = ctx.action.args.get("vrf")

cmdResponse = ctx.runDeviceCmds(["enable", "show hostname"])
hostname = cmdResponse[1]['response']['hostname']

ctx.info(f"Running installation of Aboot patch on {hostname} over {vrf} VRF")
cmds = [
    "enable",
    f"cli vrf {vrf}",
    f"copy https:/{url}{extension} extension:",
    f"extension {extension}",
]
cmdResponses: List[Dict] = ctx.runDeviceCmds(cmds)
# Iterate through the list of responses for the commands, and if an error occurred in
# any of the commands, raise an exception
# Only consider the first error that is encountered
# as following commands require previous ones to succeed
errs = [resp.get('error') for resp in cmdResponses if resp.get('error')]
if errs:
    raise ActionFailed(f"Patch installation failed with: {errs[0]}")
ctx.info("Patch successfully applied")
