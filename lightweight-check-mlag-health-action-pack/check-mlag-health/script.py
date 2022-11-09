# Copyright (c) 2022 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

from cloudvision.cvlib import ActionFailed

import time

# The MLAG check built into CVP is sometimes a little too clever for its own good.
# It checks the output of mlag config-sanity and if there are inconsistencies, the check will fail.
# This can cause issues if one wanted to use the check in an upgrade scenario where a difference
# in EOS version may cause cosmetic inconsistencies in the output. This MLAG Check simply checks
# whether there is an MLAG reload delay timer in progress and waits until it has expired
# before declaring success.

# Interval in seconds when mlag checks occur normally
pollInterval = 30


def isMlagUp():
    '''
    Runs an mlag health check to see if it is up
    Returns a help status if it is not up
    '''
    # Run the 'show mlag' command on the device
    cmdResponse = ctx.runDeviceCmds(["show mlag"])
    if all(key in cmdResponse for key in ["errorCode", "errorMessage"]):
        errCode = cmdResponse["errorCode"]
        errMsg = cmdResponse["errorMessage"]
        raise ActionFailed(f"Commands could not be run on device, returned {errCode}:\"{errMsg}\"")
    # Check to see if an error occurred with running the command,
    # if so, return false with the status to allow for a retry later
    cmdErr = cmdResponse[0].get('error')
    if cmdErr:
        raise ActionFailed(f"\"show mlag\" command failed with: \"{cmdErr}\"")

    response = cmdResponse[0]["response"]
    status = ""
    # portsErrdisabledTime being present in the response indicates
    # a reload delay timer being present
    if "portsErrdisabledTime" in response:
        status = "Active MLAG reload delay timer present"
    elif "portsErrdisabled" in response:
        # portsErrdisabled being present in the response and being 'True'
        # informs us that the ports are 'errdisabled'
        if response["portsErrdisabled"]:
            status = "MLAG Ports are errdisabled"
        else:
            return True, status
    else:
        # Neither portsErrdisabledTime or portsErrdisabled being present
        # in the response indicates that mlag is not yet up
        status = "MLAG is on its way up"
    return False, status


# Retrieve and parse the string arg
duration = int(ctx.action.args.get("checkDuration"))
ctx.info(f"Checking MLAG Health for a maximum of {duration} seconds")

# Keep checking mlag while there is still time remaining
while duration:
    mlagUp, status = isMlagUp()
    if mlagUp:
        break
    # If mlag is not up, log it's current status
    ctx.info(status)
    # Calculate how long before next check, and ensure that we don't go over the timeout
    sleepTime = min(pollInterval, duration)
    time.sleep(sleepTime)
    # Update the remaining time
    duration -= sleepTime
else:
    # This else will execute if the duration is exceeded (i.e. duration reaches 0 and the while
    # loop exits based on its looping condition, using the break does not execute this)
    # We do one final check before failing to cover cases when the checkDuration is a number
    # like 123 seconds that doesn't fit nicely in the polling interval
    mlagUp, status = isMlagUp()
    if not mlagUp:
        # Raise an uncaught exception indicating that the script action has failed
        raise ActionFailed((f"MLAG ports are still disabled after {duration} seconds.\n"
                           f"Final mlag check reported current status of mlag as \"{status}\""))

ctx.info("MLAG ports are now active.")
