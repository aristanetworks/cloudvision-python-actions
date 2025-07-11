# Copyright (c) 2022 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

from cloudvision.cvlib import ActionFailed, TimeoutExpiry

from time import sleep
from google.protobuf import wrappers_pb2 as wrappers

# Import the inventory resource API models to be able to easily parse the rAPI output
from arista.inventory.v1 import models
# Import the python service implementations of the inventory rAPI to be able to
# handle sending and receiving requests and responses from the rAPI
from arista.inventory.v1.services import DeviceServiceStub, DeviceStreamRequest

# Base case assumption where we assume device to be streaming initially
currentStreamingStatus = models.STREAMING_STATUS_ACTIVE

# Maximum amount of time to wait for the device to reboot
monitorTimeout = ctx.action.args.get("monitorTimeout")
# As args are strings, we need to convert these to an int
monitorTimeout = int(monitorTimeout) if monitorTimeout else 1200

deviceID = ctx.getDevice().id

ctx.info(f"Reloading device {deviceID}")
cmds = [
    'enable',
    'reload now',
]
# As the device reboot commands causes the device to reboot, the command response
# contains heartbeat errors as the device is no longer online. We explicitly do not expect
# a response here so that no exceptions are raised due to the presence of these errors
ctx.runDeviceCmds(cmds, validateResponse=False)
ctx.info(f"Device {deviceID} was reloaded, monitoring streaming status to come back up")

# Create a filter to only receive updates for the device we want from the resource API
# Create a deviceKey with the device serial number to use for filtering
device_key = models.DeviceKey(device_id=wrappers.StringValue(value=deviceID))
# Create the filter using the device device model
filter = models.Device(key=device_key)

# Create a stream request for the rAPI and append the filter to it
req = DeviceStreamRequest()
req.partial_eq_filter.append(filter)

# Create a stub to the inventory rAPI so we can send and receive requests and responses
stub = ctx.getApiClient(DeviceServiceStub)


def monitor():
    '''
    Monitor function to pass to the doWithTimeout context method.
    Subscribes to the devices resource API and updates the current streaming status of the device
    '''
    global currentStreamingStatus
    # Subscribe to updates from our device
    for resp in stub.Subscribe(req, timeout=monitorTimeout):
        # resp.value is the device object, which has all the fields we want
        updateStreamingStatus = resp.value.streaming_status
        # Device can either be in STREAMING_STATUS_INACTIVE or STREAMING_STATUS_UNSPECIFIED
        # When the device comes back up, only allow for inactive case to pass the check
        if currentStreamingStatus == models.STREAMING_STATUS_INACTIVE and \
                updateStreamingStatus == models.STREAMING_STATUS_ACTIVE:
            ctx.info(f"Device {deviceID} is streaming, finishing after 5 second grace period")
            # The device has come back up. Wait a 5 second grace period to ensure SSH process
            # is back online after device streaming status is back up
            sleep(5)
            break
        # Otherwise update the current streaming status to what the device's current one is
        currentStreamingStatus = updateStreamingStatus


try:
    ctx.doWithTimeout(monitor, monitorTimeout)
# ctx.doWithTimeout raises a TimeoutExpiry when the timeout is exceeded. Handle this here
# All other exceptions raised will fail the script
except TimeoutExpiry:
    # Timer expired without ever seeing the streaming status change from active post-reload
    # Allow script to succeed but warn user of what happened
    if currentStreamingStatus == models.STREAMING_STATUS_ACTIVE:
        ctx.warning(f"Device {deviceID} is currently streaming but a reload was not seen.\n\
            Device {deviceID} may not have reloaded properly")
    else:
        raise ActionFailed(
            f"Device {deviceID} didn't respond within {monitorTimeout} seconds post-reload")
