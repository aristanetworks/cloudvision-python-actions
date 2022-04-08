def string_to_list(string_to_convert):
    numbers = []
    segments = [ segment.strip() for segment in string_to_convert.split(",") ]
    for segment in segments:
        if "-" in segment:
            for i in range(int(segment.split("-")[0]), int(segment.split("-")[1]) + 1):
                numbers.append(i)
        else:
            numbers.append(int(segment))    
    return numbers

switch = ctx.getDevice()
vlan_ids = ctx.changeControl.args['VLAN IDs']
ctx.alog("{}".format(ctx.alog(vlan_ids)))

if vlan_ids is not None:
    vlan_ids = string_to_list(vlan_ids)
else:
    ctx.alog("No VLAN IDs provided")

for vlan_id in vlan_ids:
    ctx.alog("Getting interface info on {} for Vlan {}".format(switch.ip, vlan_id))
    ctx.alog("show ip interface vlan {} output: {}".format(vlan_id, ctx.runDeviceCmds(["show ip interface vlan {}".format(vlan_id)])))
    try:
        interface_info = ctx.runDeviceCmds(["show ip interface vlan {}".format(vlan_id)])[0]["response"]["interfaces"]["Vlan{}".format(vlan_id)]
    except KeyError:
        ctx.alog("Couldn't retrieve IP interface details for {}.".format(vlan_id))
        continue

    try:
        svi_virtual_ip_address = interface_info["interfaceAddress"]["virtualIp"]["address"]
    except KeyError:
        ctx.alog("{} does not have a Virtual IP address assigned to it.".format("Vlan{}".format(vlan_id)))
    
    if svi_virtual_ip_address == "0.0.0.0":
        continue
    vrf_name = interface_info["vrf"]
    if vrf_name == "default":
        garp_command = "bash timeout 5 sudo /sbin/arping -A -c 1 -I {} {}".format("vlan{}".format(vlan_id), svi_virtual_ip_address)
    else:
        garp_command = "bash timeout 5 sudo ip netns exec ns-{} /sbin/arping -A -c 1 -I {} {}".format(
            vrf_name, "vlan{}".format(vlan_id),
            svi_virtual_ip_address
        )
    ctx.alog("Sending out GARP on {}".format("Vlan{}".format(vlan_id)))
    garp_output = ctx.runDeviceCmds([garp_command])
    ctx.alog("Result of GARP: {}".format(garp_output[0]["response"]))

ctx.alog("Executed GARP on all SVIs")