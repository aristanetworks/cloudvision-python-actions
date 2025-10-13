# Copyright (c) 2022 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

srn: str = ctx.action.args.get("SRNumber")
if not srn:
    bundleCmd = ["send support-bundle flash:"]
else:
    bundleCmd = [f"send support-bundle flash: case-number {srn}"]

ctx.info(f"Gathering baseline logs from device {ctx.getDevice().ip}")
ctx.runDeviceCmds(bundleCmd, fmt="text", timeout=800, diConnTimeout=600, diCliTimeout=600)
check_files = ["dir /all flash:"]
ctx.info(f"Listing the content of flash on device {ctx.getDevice().ip}")
result = ctx.runDeviceCmds(check_files)
ctx.info(str(result[0]["response"]))
ctx.info("Please upload the support-bundle on the switch(es) flash to the TAC case.")
