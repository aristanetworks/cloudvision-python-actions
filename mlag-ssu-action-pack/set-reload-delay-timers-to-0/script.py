# Copyright (c) 2022 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

# This script is the first step in the workflow used to perform a hitless upgrade.
# It checks whether or not a switch is a member of an MLAG pair and if so, will set the reload
# delay timers of the switch to 0 in order to prevent interfaces from going into an errdisabled
# state after 'reload' which prevents traffic to/from single homed hosts from being dropped.


from typing import List, Dict
from cloudvision.cvlib import ActionFailed
from cloudvision.Connector.grpc_client import create_query
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


def get_reload_delay_timers_status():
    '''
    Returns True if reload delay timers are configured
    '''
    result = {}
    with ctx.getCvClient() as client:
        device = ctx.getDevice()
        if device is None:
            raise ActionFailed("Action must have a device associated with the context")
        if not device.id:
            raise ActionFailed("Action's associated device has no ID attribute")

        pathElts = [
            "Sysdb", "mlag", "config"  # "reloadDelayMlagConfigured"
        ]
        dataset = device.id

        query = [
            create_query([(pathElts, [])], dataset)
        ]
        for batch in client.get(query):
            ctx.info(f"{batch}")
            for notif in batch["notifications"]:
                result.update(notif["updates"])

        result = unfreeze(result)

    if result and result.get("reloadDelayMlagConfigured"):
        return True


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
    # Only consider the first error that is encountered as following commands require
    # previous ones to succeed
    errs = [resp.get('error') for resp in cmdResponses if resp.get('error')]
    if errs:
        raise ActionFailed(f"Setting reload delay timers failed with: {errs[0]}")


ctx.info("Checking to see if reload delay timers are set")

if get_reload_delay_timers_status():
    ctx.info("Reload delay timers are set.")
    ctx.info("Setting reload delay timers to 0.")
    set_reload_delay_timers(0, 0)
    ctx.info("Successfully set reload delay timers to 0.")
else:
    ctx.info("Reload delay timers are not set")

ctx.info("Complete.")
