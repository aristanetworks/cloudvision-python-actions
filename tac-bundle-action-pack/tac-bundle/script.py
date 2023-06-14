# Copyright (c) 2022 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.
import re
dt = "$HOSTNAME-$(date +%Y_%m_%d.%H_%M_%S)"
srn: str = ctx.action.args.get("SRNumber")

cmd = ["show version"]
version = ctx.runDeviceCmds(cmd)[0]['response']['version']
ctx.info(str(version))
vl = version.split('.')
regex_new_version = re.match(r'([0-9]{1,2}).*', vl[2]).group(1)
# If EOS is higher than 4.26.1F+ we can run the new support-bundle command
if int(vl[1]) >= 26 and int(regex_new_version) >= 1:
    if not srn:
        baseline = ["send support-bundle flash:"]
    else:
        baseline = [f"send support-bundle flash: case-number {srn}"]
# Otherwise collect each logs individually
else:
    if not srn:
        prefix = "TAC"
        tar_prefix = ""
    else:
        prefix = "TAC-" + srn
        tar_prefix = "-SR" + srn
    baseline = [
        ("bash timeout 10 sudo tar -cvf - /mnt/flash/schedule/tech-support/* "
         f"> /mnt/flash/{prefix}-hist-{dt}.tar"),
        f"show tech-support | gzip > /mnt/flash/{prefix}-show-tech-{dt}.log.gz",
        f"show agent logs | gzip > /mnt/flash/{prefix}-show-agentlog-{dt}.log.gz",
        f"bash sudo tar -czvf - /var/log/qt/ > /mnt/flash/{prefix}-qt-logs-{dt}.tar.gz",
        f"show aaa accounting logs | gzip >/mnt/flash/{prefix}-show-aaa-accounting-{dt}.log.gz",
        f"show logging system | gzip >/mnt/flash/{prefix}-show-logsys-{dt}.log.gz"
    ]
    if int(vl[1]) >= 21 and int(regex_new_version) >= 0:
        baseline.append(
            f"show tech extended evpn | gzip > /mnt/flash/{prefix}-show-tech-evpn-{dt}.log.gz")
        baseline.append(
            f"show arp vrf all | gzip > /mnt/flash/{prefix}-show-arp-vrf-all-{dt}.log.gz")
    baseline.append(
        ("bash timeout 8 sudo tar -cvf - /mnt/flash/TAC-* "
         f"> /mnt/flash/support-bundle{tar_prefix}-{dt}.tar"))
ctx.info(f"Gathering baseline logs from device {ctx.getDevice().ip}")
ctx.runDeviceCmds(baseline, fmt="text")
check_files = ["dir /all flash:"]
ctx.info(f"Listing the content of flash on device {ctx.getDevice().ip}")
result = ctx.runDeviceCmds(check_files)
ctx.info(str(result[0]['response']))
ctx.info("Please upload the support-bundle on the switch(es) flash to the TAC case.")
