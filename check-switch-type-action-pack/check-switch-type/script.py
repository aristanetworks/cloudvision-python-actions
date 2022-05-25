# Copyright (c) 2022 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

from cloudvision.cvlib import ActionFailed

switchType = ctx.action.args.get("switchType")

ctx.info("Running show version from script to check switch type")
cmds = [
    "enable",
    "show version",
    "show hostname",
]
cmdResponse = ctx.runDeviceCmds(cmds)

modelName = cmdResponse[1]["response"]["modelName"]
hostname = cmdResponse[2]["response"]["hostname"]

# Perform a partial match on the model name for cases such as where
# models differences account to being appended with -SSD or not
if switchType not in modelName:
    raise ActionFailed(f"Switch {hostname} is not of type {switchType} but is of type {modelName}")

ctx.info(f"Switch {hostname} is of type {modelName}")
