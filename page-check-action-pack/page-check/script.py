# Copyright (c) 2022 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

from cloudvision.cvlib import ActionFailed

import paramiko

# Extract and ensure args are of the correct type
pageUrl = ctx.action.args.get("pageUrl")
failLimit = int(ctx.action.args.get("failCount"))
timeout = int(ctx.action.args.get("timeout"))
username = ctx.action.args.get("username")
password = ctx.action.args.get("password")

devicesStr: str = ctx.action.args.get("deviceList")
deviceList = [dev.strip() for dev in devicesStr.split(',')]
# split the comma seperated string and filter out empty values
deviceList = list(filter(None, deviceList))

host_port = 22
passed = 0
failed = 0

ctx.info(f"Checking Web Page connectivity to {pageUrl}")

# Initialise SSH
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# Start ping tests from devices in deviceList
for device_ip in deviceList:
    ctx.info("Connecting to {}".format(device_ip))
    ssh.connect(device_ip, port=host_port, username=username, password=password)
    stdin, stdout, stderr = ssh.exec_command("curl --insecure -I -m {} {}".format(timeout, pageUrl))
    output = stdout.readlines()
    error = str(stderr.readlines()[-1])
    ssh.close()
    if "Failed" in str(error) or "Error" in str(error):
        ctx.error(f"Access from {device_ip} to {pageUrl} failed, error: {error}")
        failed += 1
    else:
        response = output[0]
        if "200 OK" in response:
            ctx.info(f"Access from {device_ip} to {pageUrl} passed")
            passed += 1
        else:
            ctx.error(f"Access from {device_ip} to {pageUrl} failed, response: {response}")
            failed += 1

# If number of Page tests that failed exceeds failCount, fail the whole test
if failLimit > failed:
    ctx.info(f"Passed. {passed} devices of {len(deviceList)} can access {pageUrl}")
else:
    raise ActionFailed(f"Unable to access {pageUrl} on {failed} devices")
