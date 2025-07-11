# Copyright (c) 2022 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

from cloudvision.cvlib import ActionFailed

interfacesStr: str = ctx.action.args.get("interfaces")
# Split the comma separated string on the comma and strip of any whitespace
interfacesList = [intf.strip() for intf in interfacesStr.split(',')]
# Filter out empty values from the split
interfaces = list(filter(None, interfacesList))
# If the list is empty, raise an error
if not interfaces:
    raise ActionFailed("Interface list passed to script is empty")

ctx.info("Running 'show interfaces status' to check if any important interfaces are down")
cmds = [
    "enable",
    "show interfaces status",
]
cmdResponse = ctx.runDeviceCmds(cmds)
interfaceStatuses = cmdResponse[1]['response'].get('interfaceStatuses')
if not interfaceStatuses:
    raise ActionFailed(f"Show interfaces status failed with: {cmdResponse[1]['error']}")

down = []
for interface in interfaces:
    intfStatus: dict = interfaceStatuses[interface]
    if intfStatus.get('lineProtocolStatus') != 'up' or intfStatus.get('linkStatus') != 'connected':
        down.append(interface)

# If any of the interfaces are down, report an error
if down:
    downStr = ', '.join([str(elem) for elem in down])
    raise ActionFailed(f"Interface(s) in down state: {downStr}")

ctx.info("All specified interfaces are up")
