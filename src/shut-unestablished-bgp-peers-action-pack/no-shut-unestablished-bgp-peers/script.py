# Copyright (c) 2022 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

from typing import List, Dict
from google.protobuf.timestamp_pb2 import Timestamp
from cloudvision.Connector.grpc_client import GRPCClient, create_query, create_notification
from cloudvision.cvlib import ActionFailed

cmdOut: List[Dict] = ctx.runDeviceCmds(["enable", "show hostname"])
# Iterate through the list of responses for the commands, and if an error occurred in any of the
# commands, raise an exception
# Only consider the first error that is encountered as following commands require previous ones
# to succeed
errs: List[str] = [resp.get('error') for resp in cmdOut if resp.get('error')]
if errs:
    raise ActionFailed(f"Unable to get hostname, failed with: {errs[0]}")

hostname = cmdOut[1]["response"]["hostname"]

client: GRPCClient = ctx.getCvClient()

# Flag to mark that the command list needs to be deleted
commandsExist = False

# Query the path where we stored the command list previously
deviceId = ctx.getDevice().id if ctx.getDevice() else None
key = f"{hostname}-{deviceId}-commands" if deviceId else f"{hostname}-commands"
path = ["changecontrol", "actionTempStorage", "shut-bgp-action"]
for batch in client.get([create_query([(path, [key])], "cvp")]):
    for notif in batch["notifications"]:
        if len(notif["updates"]) == 0:
            ctx.info("No shutdown BGP peers to be restored")
            continue
        commandsExist = True
        for _, commandList in notif["updates"].items():
            cmds = [f"default {cmd}" if "shutdown" in cmd else cmd for cmd in commandList]
            cmdOut = ctx.runDeviceCmds(cmds)
            errs: List[str] = [resp.get('error') for resp in cmdOut if resp.get('error')]
            if errs:
                raise ActionFailed(f"Unable to run unshut commands, failed with: {errs[0]}")

# If a command list exist (and all commands ran successfully), issue a delete for it
if commandsExist:
    ts = Timestamp()
    ts.GetCurrentTime()
    client.publish(dId="cvp", notifs=[create_notification(ts, path, deletes=[key])])
    ctx.info("Shutdown BGP peers successfully restored")
