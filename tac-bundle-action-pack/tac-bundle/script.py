# Copyright (c) 2022 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.
dt = "$HOSTNAME-$(date +%Y_%m_%d.%H_%M_%S)"
srn: str = ctx.action.args.get("SRNumber")

cmd = ["show version"]
version = ctx.runDeviceCmds(cmd)[0]['response']['version']
ctx.info(str(version))
vl = version.split('.')

# If EOS is higher than 4.26.1F+ we can run the new support-bundle command
if int(vl[1]) >= 26 and int(vl[2].strip("FM")) >= 1:
    if not srn:
        baseline = ["send support-bundle flash:"]
    else:
        baseline = [f"send support-bundle flash: case-number {srn}"]
# Otherwise collect each logs individually
else:
    baseline = [
        f"bash timeout 10 sudo tar -cvf - /mnt/flash/schedule/tech-support/* > /mnt/flash/{srn}-hist-{dt}.tar",
        f"show tech-support | gzip > /mnt/flash/{srn}-show-tech-{dt}.log.gz",
        f"show agent logs | gzip > /mnt/flash/{srn}-show-agentlog-{dt}.log.gz",
        f"bash sudo tar -czvf - /var/log/qt/ > /mnt/flash/{srn}-qt-logs-{dt}.tar.gz",
        f"show aaa accounting logs | gzip >/mnt/flash/{srn}-show-aaa-accounting-{dt}.log.gz",
        f"show logging system | gzip >/mnt/flash/{srn}-show-logsys-{dt}.log.gz"
    ]
    if int(vl[1]) >= 21 and int(vl[2].strip("FM")) >= 0:
        baseline.append(f"show tech extended evpn | gzip > /mnt/flash/{srn}-show-tech-evpn-{dt}.log.gz")
        baseline.append(f"show arp vrf all | gzip > /mnt/flash/{srn}-show-arp-vrf-all-{dt}.log.gz")
    baseline.append(f"bash timeout 10 sudo tar -cvf - /mnt/flash/TAC-* > /mnt/flash/support-bundle-{srn}-{dt}.tar")

ctx.info(f"Gathering baseline logs from device {ctx.getDevice().ip}")
ctx.runDeviceCmds(baseline, fmt="text")

check_files = ["dir /all flash:"]
ctx.info(f"Listing the content of flash on device {ctx.getDevice().ip}")
result = ctx.runDeviceCmds(check_files)
ctx.info(str(result[0]['response']))
ctx.info("Please upload the support-bundle on the switch(es) flash to the TAC case.")
