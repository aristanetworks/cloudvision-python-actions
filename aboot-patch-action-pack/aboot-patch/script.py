# Copyright (c) 2022 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

url = ctx.changeControl.args.get("extensionURL")
extension = ctx.changeControl.args.get("extension")
vrf = ctx.changeControl.args.get("vrf")

cmdResponse = ctx.runDeviceCmds(["enable", "show hostname"])
hostname = cmdResponse[1]['response']['hostname']

ctx.alog(f"Running installation of Aboot patch on {hostname} over {vrf} VRF")
cmds = [
    "enable",
    f"cli vrf {vrf}",
    f"copy https:/{url}{extension} extension:",
    f"extension {extension}",
]
cmdResponses: list[dict] = ctx.runDeviceCmds(cmds)
# Iterate through the list of responses for the commands, and if an error occurred in
# any of the commands, raise an exception
# Only consider the first error that is encountered as following commands require previous ones to succeed
if next((err for resp in cmdResponses if (err := resp.get('error'))), None):
    raise UserWarning(f"Patch installation failed with: {err}")
ctx.alog("Patch successfully applied")
