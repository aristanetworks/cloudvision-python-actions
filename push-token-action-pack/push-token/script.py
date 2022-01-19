# Copyright (c) 2022 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

token = ctx.changeControl.args.get("token")
filename = ctx.changeControl.args.get("filename")

cmds = [
    "enable",
    {"cmd": f"copy terminal: file:{filename}", "input": token},
]
cmdResponses: list[dict] = ctx.runDeviceCmds(cmds)
# Iterate through the list of responses for the commands, and if an error occurred in
# any of the commands, raise an exception
# Only consider the first error that is encountered as following commands require previous ones to succeed
if next((err for resp in cmdResponses if (err := resp.get('error'))), None):
    raise UserWarning(f"Copying of token to {filename} failed with: {err}")
