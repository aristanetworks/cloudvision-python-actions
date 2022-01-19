# Copyright (c) 2022 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

import paramiko

# Extract and ensure args are of the correct type
pageUrl = ctx.changeControl.args.get("pageUrl")
failLimit = int(ctx.changeControl.args.get("failCount"))
timeout = int(ctx.changeControl.args.get("timeout"))
username = ctx.changeControl.args.get("username")
password = ctx.changeControl.args.get("password")

devicesStr: str = ctx.changeControl.args.get("deviceList")
deviceList = [dev.strip() for dev in devicesStr.split(',')]
# split the comma seperated string and filter out empty values
deviceList = list(filter(None, deviceList))

host_port = 22
passed = 0
failed = 0

ctx.alog(f"page_check - checking Web Page connectivity to {pageUrl}")

# Initialise SSH
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# Start ping tests from devices in deviceList
for device_ip in deviceList:
    ctx.alog("page_check: Connecting to {}".format(device_ip))
    ssh.connect(device_ip, port=host_port, username=username, password=password)
    stdin, stdout, stderr = ssh.exec_command("curl --insecure -I -m {} {}".format(timeout, pageUrl))
    output = stdout.readlines()
    error = str(stderr.readlines()[-1])
    ssh.close()
    if "Failed" in str(error) or "Error" in str(error):
        ctx.alog(f"page_check: Access from {device_ip} to {pageUrl} failed, error: {error}")
        failed += 1
    else:
        response = output[0]
        if "200 OK" in response:
            ctx.alog(f"page_check: Access from {device_ip} to {pageUrl} passed")
            passed += 1
        else:
            ctx.alog(f"page_check: Access from {device_ip} to {pageUrl} failed, response: {response}")
            failed += 1

# If number of Page tests that failed exceeds failCount, fail the whole test
if failLimit > failed:
    ctx.alog(f"page_check: Passed. {passed} devices of {len(deviceList)} can access {pageUrl}")
else:
    raise UserWarning(f"page_check: Failed. {failed} devices were not able to access {pageUrl}")
