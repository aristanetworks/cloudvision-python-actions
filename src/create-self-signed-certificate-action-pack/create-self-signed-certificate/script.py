# Copyright (c) 2022 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

# This action will generate a self-signed certificate and an associate key that can be used
# in an SSL profile.
# Example of configuration using the generated certificate and key on EOS:

# management security
#   ssl profile SSL_profile
#     tls versions 1.2
#     certificate self-signed.crt key self-signed.key
# management api http-commands
#   protocol https ssl profile SSL_profile

from cloudvision.cvlib import ActionFailed

# 1. Setup:
device = ctx.getDevice()
ctx.info(f"device_id: [{device.id}] - ip: [{device.ip}] - hostname: [{device.hostName}]")
cmdResponse = ctx.runDeviceCmds(["enable", "show hostname"])
hostname = cmdResponse[1]["response"]["hostname"]
fqdn = cmdResponse[1]["response"]["fqdn"]
ctx.info(f"Creating self-signed certificate for device with fqdn: {fqdn} - hostname: {hostname}")


# 2. Commands creation:
args = ctx.action.args
cmds = [
    "enable",
    f"security pki key generate rsa {args['key_length']} {args['key_file']}",
    (
        f"security pki certificate generate self-signed {args['cert_file']} "
        f"key {args['key_file']} "
        f"validity {args['validity']} "
        f"parameters common-name {hostname} "
        f'country "{args["country"]}" '
        f'state "{args["state"]}" '
        f'locality "{args["locality"]}" '
        f'organization "{args["organization"]}" '
        f'organization-unit "{args["organization_unit"]}" '
        f'email "{args["email"]}" '
        f'subject-alternative-name dns {fqdn} email "{args["email"]}" ip {device.ip}'
    ),
]
ctx.info(f"Command to run on the device: {cmds}")


# 3. Run the commands on the device and check for errors:
output_cmd_list = ctx.runDeviceCmds(cmds)
ctx.info(f"Outputs: {output_cmd_list}")
for index, cmdOutput in enumerate(output_cmd_list):
    if "error" in cmdOutput.keys() and cmdOutput["error"]:
        raise ActionFailed(f"Error: switch {fqdn} - Command: '{cmds[index]}' \n Error: {cmdOutput}")


# 4. Verification step:
cert_dir_output = ctx.runDeviceCmds(["enable", "dir certificate:"])
key_dir_output = ctx.runDeviceCmds(["enable", "dir sslkey:"])
ctx.info(f"Verification - Certificate directory: {cert_dir_output[1]['response']}")
ctx.info(f"Verification - Key directory: {key_dir_output[1]['response']}")
