# Copyright (c) 2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

import re
from cloudvision.cvlib import ActionFailed

ctx.info("--- Stage 0: Performing Pre-flight Checks ---")

source_swi = ctx.action.args.get("Source")
if not source_swi:
    raise ActionFailed("FAIL: Source SWI filename cannot be empty.")
ctx.info(f"Upgrade target image: {source_swi}")

# Check 1: Verify the source SWI file exists on the supervisor
ctx.info(f"Verifying that '{source_swi}' exists on the supervisor...")
file_check_cmd = ["enable", f"dir flash:{source_swi}"]
file_check_out = ctx.runDeviceCmds(file_check_cmd)
if not file_check_out[1].get("response"):
    raise ActionFailed(f"FAIL: Source file '{source_swi}' not found on flash.")
ctx.info("SUCCESS: Source SWI file found.")

ctx.info("\n--- Stage 1: Configure and Validate Supervisor ---")

# Set the boot-config on the supervisor
ctx.info(f"Setting boot system to {source_swi}")
ctx.runDeviceCmds(["enable", "configure", f"boot system flash:{source_swi}"])

# Verify the boot configuration was set correctly
cmd_out = ctx.runDeviceCmds(["enable", "show boot"])
boot_config = cmd_out[1]["response"].get("softwareImage", "")

if source_swi not in boot_config:
    raise ActionFailed(
        f"FAIL: Boot image not set correctly. "
        f"Expected '{source_swi}', found '{boot_config}'."
    )
ctx.info(f"SUCCESS: Supervisor boot image verified: {boot_config}")

# Get reference MD5 checksums from the supervisor
ctx.info("Calculating reference MD5 checksums on supervisor...")
md5_cmds = [
    "enable",
    f"bash timeout 300 md5sum /mnt/flash/{source_swi}",
    "bash timeout 300 md5sum /mnt/flash/boot-config"
]
md5_out = ctx.runDeviceCmds(md5_cmds)

try:
    # This parsing is a potential point of failure if command output changes
    swi_checksum_supervisor = re.match(
        r"^\s*([a-fA-F0-9]+)", md5_out[1]["response"]["messages"][0]
    ).group(1)
    boot_config_checksum_supervisor = re.match(
        r"^\s*([a-fA-F0-9]+)", md5_out[2]["response"]["messages"][0]
    ).group(1)
except (AttributeError, IndexError):
    raise ActionFailed("FAIL: Could not parse MD5 checksum output from the supervisor.")

ctx.info(f"Reference SWI checksum: {swi_checksum_supervisor}")
ctx.info(f"Reference boot-config checksum: {boot_config_checksum_supervisor}")

ctx.info("\n--- Stage 2: Synchronize and Verify Member Switches ---")

ctx.info(f"Copying and verifying '{source_swi}' on member(s)...")
sync_swi_cmd = (
    "bash timeout 1200 switch aggregation member other "
    f"bash -c \"wget --no-verbose -O /mnt/flash/{source_swi} "
    f"http://127.2.0.1:3102/mnt/flash/{source_swi} "
    f"&& md5sum /mnt/flash/{source_swi}\""
)
ctx.info("Copying and verifying 'boot-config' on member(s)...")
sync_boot_cmd = (
    "bash timeout 1200 switch aggregation member other "
    "bash -c \"wget --no-verbose -O /mnt/flash/boot-config "
    "http://127.2.0.1:3102/mnt/flash/boot-config "
    "&& md5sum /mnt/flash/boot-config\""
)

sync_output = ctx.runDeviceCmds(["enable", sync_swi_cmd, sync_boot_cmd])
ctx.info("File synchronization and remote verification complete.")

# Extract the message string from the dictionary before checking
member_swi_hashes_msg = sync_output[1]["response"]["messages"][0]
member_boot_config_hashes_msg = sync_output[2]["response"]["messages"][0]

ctx.info(f"Supervisor SWI hash: {swi_checksum_supervisor}")
ctx.info(f"Member SWI hashes output: {member_swi_hashes_msg}")

if swi_checksum_supervisor not in member_swi_hashes_msg:
    raise ActionFailed("FAIL: SWI checksum mismatch on member switches!")
ctx.info("SUCCESS: SWI checksums match on all members.")

ctx.info(f"Supervisor boot-config hash: {boot_config_checksum_supervisor}")
ctx.info(f"Member boot-config hashes output: {member_boot_config_hashes_msg}")

if boot_config_checksum_supervisor not in member_boot_config_hashes_msg:
    raise ActionFailed("FAIL: boot-config checksum mismatch on member switches!")
ctx.info("SUCCESS: boot-config checksums match on all members.")

ctx.info("\n--- Stage 3: Save Configuration and Staged Reload ---")

# Save the running-config to startup-config on all devices
ctx.info("Saving configuration on all devices...")
ctx.runDeviceCmds(["enable", "write memory"])
ctx.info("Configuration saved.")

# Reload the member/worker switches first to minimize downtime
ctx.info("Reloading MEMBER switches now...")
reload_cmds = [
    "enable",
    "reload switch aggregation member other"
]
ctx.runDeviceCmds(reload_cmds, validateResponse=False, timeout=3600)
ctx.info("MEMBER switches reload done.")
