# Copyright (c) 2022 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

import ipaddress


def string_to_list(string_to_convert):
    """ Returns the input string as a list object """
    numbers = []
    segments = [segment.strip() for segment in string_to_convert.split(",")]
    for segment in segments:
        if "-" in segment:
            for i in range(int(segment.split("-")[0]), int(segment.split("-")[1]) + 1):
                numbers.append(i)
        else:
            numbers.append(int(segment))
    return numbers


switch = ctx.getDevice()
vlan_ids = ctx.action.args['VLAN IDs']

if vlan_ids is not None:
    ctx.info(f"Supplied VLANs: {vlan_ids}")
    vlan_ids = string_to_list(vlan_ids)
else:
    ctx.info("No VLAN IDs provided")

for vlan_id in vlan_ids:
    ctx.info(f"Getting interface info on {switch.ip} for Vlan{vlan_id}")
    show_ip_interface_output = ctx.runDeviceCmds([f"show ip interface vlan {vlan_id}"])
    ctx.info(f"show ip interface vlan {vlan_id} output: {show_ip_interface_output}")
    try:
        interface_info = show_ip_interface_output[0]["response"]["interfaces"][f"Vlan{vlan_id}"]
    except KeyError:
        ctx.error(f"Couldn't retrieve IP interface details for Vlan{vlan_id}.")
        continue

    try:
        ip_address = interface_info["interfaceAddress"]["virtualIp"]["address"]
        subnet_mask = interface_info["interfaceAddress"]["virtualIp"]["maskLen"]

        if ip_address == "0.0.0.0":
            ip_address = interface_info["interfaceAddress"]["primaryIp"]["address"]
            subnet_mask = interface_info["interfaceAddress"]["primaryIp"]["maskLen"]
    except KeyError:
        ctx.error(f"Unable to retrieve IP address for interface Vlan{vlan_id}.")
        continue

    if ip_address == "0.0.0.0":
        ctx.warning(f"No IP address configured on interface Vlan{vlan_id}.")
        continue

    ip_address_object = ipaddress.ip_interface(f"{ip_address}/{subnet_mask}")
    ip_network_hosts = list(ip_address_object.network.hosts())
    vrf_name = interface_info["vrf"]
    ping_commands = []
    for host_address in ip_network_hosts:
        if vrf_name == "default":
            ping_command = f"ping ip {host_address} repeat 1 timeout 1"
        else:
            ping_command = f"ping vrf {vrf_name} ip {host_address} repeat 1 timeout 1"
        ping_commands.append(ping_command)

    # Ping individuallly
    for ping_command in ping_commands:
        ping_output = ctx.runDeviceCmds([ping_command])[0]["response"]
        ctx.info(f"{ping_command} output: {ping_output}")

ctx.info("Successfully attempted to ping all hosts on all supplied SVI subnets")
