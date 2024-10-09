# Copyright (c) 2022 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

# This script is the final step in the workflow used to perform a hitless upgrade.
# It will attempt to set the reload delay timer values to what they were at the beginning
# of the change control so that the switch is in compliance with its Designed Config.

from google.protobuf.timestamp_pb2 import Timestamp
from cloudvision.Connector.grpc_client import create_query
from cloudvision.cvlib import ActionFailed
from cloudvision.Connector.codec.custom_types import FrozenDict


def unfreeze(o):
    ''' Used to unfreeze Frozen dictionaries'''
    if isinstance(o, (dict, FrozenDict)):
        return dict({k: unfreeze(v) for k, v in o.items()})

    if isinstance(o, (str)):
        return o

    try:
        return [unfreeze(i) for i in o]
    except TypeError:
        pass

    return o


def get_original_reload_delay_values():
    mlag_reload_delay_timer_value = None
    non_mlag_reload_delay_timer_value = None

    result = {}

    with ctx.getCvClient() as client:
        ccStartTs = ctx.action.getCCStartTime(client)
        if not ccStartTs:
            raise ActionFailed("No change control ID present")
        ccStart = Timestamp()
        ccStart.FromNanoseconds(int(ccStartTs))

        device = ctx.getDevice()
        if device is None:
            raise ActionFailed("Action must have a device associated with the context")
        if not device.id:
            raise ActionFailed("Action's associated device has no ID attribute")

        pathElts = [
            "Sysdb", "mlag", "config"
        ]
        dataset = device.id

        query = [
            create_query([(pathElts, [])], dataset)
        ]

        for batch in client.get(query, start=ccStart, end=ccStart):
            for notif in batch["notifications"]:
                result.update(notif["updates"])

        result = unfreeze(result)

    if result:
        mlag_reload_delay_timer = result.get("reloadDelay")
        non_mlag_reload_delay_timer = result.get("reloadDelayNonMlag")

        if mlag_reload_delay_timer.get("reloadDelayType", {}).get("Value"):
            mlag_reload_delay_timer_value = mlag_reload_delay_timer["delay"]

        if non_mlag_reload_delay_timer.get("reloadDelayType", {}).get("Value"):
            non_mlag_reload_delay_timer_value = non_mlag_reload_delay_timer["delay"]

        if mlag_reload_delay_timer_value and non_mlag_reload_delay_timer_value:
            ctx.info(f"MLAG Reload Delay Timer: {mlag_reload_delay_timer_value}")
            ctx.info(f"Non-MLAG Reload Delay Timer: {non_mlag_reload_delay_timer_value}")

    return mlag_reload_delay_timer_value, non_mlag_reload_delay_timer_value


def set_reload_delay_timers(mlag_reload_delay, non_mlag_reload_delay):
    ctx.info("Setting reload delay timers on switch to 0.")
    cmds = [
        "enable",
        "configure",
        "mlag configuration",
        f"reload-delay mlag {int(mlag_reload_delay)}",
        f"reload-delay non-mlag {int(non_mlag_reload_delay)}",
        "copy running-config startup-config",
    ]
    cmdResponses: List[Dict] = ctx.runDeviceCmds(cmds)
    # Iterate through the list of responses for the commands, and if an error occurred in
    # any of the commands, raise an exception
    # Only consider the first error that is encountered as following commands
    # require previous ones to succeed
    errs = [resp.get('error') for resp in cmdResponses if resp.get('error')]
    if errs:
        raise ActionFailed(f"Setting reload delay timers failed with: {errs[0]}")


ctx.info("Getting original reload delay timers.")

mlag_reload_delay_timer, non_mlag_reload_delay_timer = get_original_reload_delay_values()

if mlag_reload_delay_timer and non_mlag_reload_delay_timer:
    ctx.info("Retrieved original reload delay timers.")
    ctx.info("Setting reload delay timers back to original values")
    set_reload_delay_timers(mlag_reload_delay_timer, non_mlag_reload_delay_timer)
    ctx.info("Set reload delay timers back to their original values")
else:
    ctx.info("Reload delay timers were not set at start of the change control")

ctx.info("Complete.")
