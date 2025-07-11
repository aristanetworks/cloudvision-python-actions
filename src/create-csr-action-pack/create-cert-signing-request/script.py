# Copyright (c) 2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

# This action will generate a certificate signing request and an associated key that can be used
# to request CA based certificate from a CA.
# Generated CSR is stored in the flash: with the file name <hostname>-csr.csr
# Generated CSR key is stored in the sslkey: with the file name <hostname>-csr.key
# Once CA provides CA based Certificate, using the below config builds the respective SSL profile.
# Example of configuration using the CA-based certificate and key on EOS:

# management security
#   ssl profile SSL_profile
#     tls versions 1.2
#     certificate <hostname-ca>.crt key <{hostname}-csr>.key
# management api http-commands
#   protocol https ssl profile SSL_profile

# 1. Setup:
device = ctx.getDevice()
ctx.info(
    f"device_id: [{device.id}] - ip: [{device.ip}] - hostname: [{device.hostName}]"
)
cmdResponse = ctx.runDeviceCmds(["enable", "show hostname"])
hostname = cmdResponse[1]["response"]["hostname"]
fqdn = cmdResponse[1]["response"]["fqdn"]
ctx.info(
    "Creating certificate signing request CSR for device with"
    + f" fqdn: {fqdn} - hostname: {hostname}"
)

# 2. Commands creation:
args = ctx.action.args
cmds = [
    "enable",
    f"security pki key generate rsa {args['key_length']} {hostname}-csr.key",
    (
        f"security pki certificate generate signing-request key {hostname}-csr.key"
        f" parameters common-name {fqdn} "
        f'country "{args.get("country", "")}" '
        f'state "{args.get("state", "")}" '
        f'locality "{args.get("locality", "")}" '
        f'organization "{args.get("organization", "")}" '
        f'organization-unit "{args.get("organization_unit", "")}" '
        f"email {args.get('email', '')} "
        f"subject-alternative-name dns {fqdn} email {args['email']} ip {device.ip}"
    ),
]
ctx.info(f"Command to run on the device: {cmds}")

# 3. Run the commands on the device
output_cmd_list = ctx.runDeviceCmds(cmds)
csr_generated = output_cmd_list[2]["response"]["messages"][0]

csr_content_cmd = (
    f' bash timeout 10 printf "%s" "{csr_generated} " > /mnt/flash/{hostname}-csr.csr '
)
# Uncomment the following line if you want to display CSR in CVP logs
# ctx.info(f"Command to run on the device: {csr_content_cmd}")
ctx.runDeviceCmds(["enable", csr_content_cmd])

# 4. Verification step:
flash_dir_output = ctx.runDeviceCmds(["enable", "dir flash:"])
key_dir_output = ctx.runDeviceCmds(["enable", "dir sslkey:"])
ctx.info(f"Verification - Flash directory: {flash_dir_output[1]['response']}")
ctx.info(f"Verification - Key directory: {key_dir_output[1]['response']}")
