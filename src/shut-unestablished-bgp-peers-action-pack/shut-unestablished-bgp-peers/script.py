# Copyright (c) 2022 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

from typing import List, Dict, Tuple
from google.protobuf.timestamp_pb2 import Timestamp
from cloudvision.Connector.grpc_client import GRPCClient, create_notification
from cloudvision.cvlib import ActionFailed

# Get the pending BGP peer status
cmdOut: List[Dict] = ctx.runDeviceCmds(["enable", "show hostname", "show bgp convergence vrf all"])

# Iterate through the list of responses for the commands, and if an error occurred in any of the
# commands, raise an exception
# Only consider the first error that is encountered as following commands require previous ones
# to succeed
errs: List[str] = [resp.get('error') for resp in cmdOut if resp.get('error')]
if errs:
    raise ActionFailed(f"Unable to get hostname/BGP convergence status, failed with: {errs[0]}")

hostname = cmdOut[1]["response"]["hostname"]
pendingBgpPeers = cmdOut[2]["response"]
pendingPeersVrfList = []
# Create a list of pending peers to shut down
for vrf in pendingBgpPeers['vrfs']:
    if pendingBgpPeers['vrfs'][vrf]['status']['peers']['pendingPeers'] != 0:
        pendingPeersVrfList.append(vrf)


cmdOut: List[Dict] = ctx.runDeviceCmds(["enable", "show ip bgp summary vrf all"])
errs: List[str] = [resp.get('error') for resp in cmdOut if resp.get('error')]
if errs:
    raise ActionFailed(f"Unable to get BGP summary, failed with: {errs[0]}")
bgpSummary = cmdOut[1]["response"]

checkEvpn = True
cmdOut: List[Dict] = ctx.runDeviceCmds(["enable", "show bgp evpn summary"])
errs: List[str] = [resp.get('error') for resp in cmdOut if resp.get('error')]
if errs:
    if errs[0] == "Not supported":
        checkEvpn = False
    else:
        raise ActionFailed(f"Unable to get BGP evpn summary, failed with: {errs[0]}")

shutdownBgpPeerList: List[Tuple] = []
if pendingPeersVrfList:
    bgpASN = None
    for vrf in pendingPeersVrfList:
        for peer in bgpSummary['vrfs'][vrf]['peers']:
            # Check to see that the reason the the peer state is
            # pending is not due to administrative action
            if (
                bgpSummary['vrfs'][vrf]['peers'][peer]['peerState'] != "Established"
                and not (
                    bgpSummary['vrfs'][vrf]['peers'][peer]['peerState'] == "Idle"
                    and bgpSummary['vrfs'][vrf]['peers'][peer]['peerStateIdleReason'] == "Admin"
                )
            ):
                shutdownBgpPeerList.append((vrf, peer))
                bgpASN = bgpSummary['vrfs'][vrf]['asn']
    if checkEvpn:
        bgpEvpnSummary = cmdOut[1]["response"]
        # Check the peer EVPN status for the default vrf
        for peer in bgpEvpnSummary['vrfs']['default']['peers']:
            peerSummary = bgpEvpnSummary['vrfs']['default']['peers'][peer]
            if (
                peerSummary['peerState'] != "Established"
                and not (
                    peerSummary['peerState'] == "Idle"
                    and peerSummary['peerStateIdleReason'] == "Admin"
                )
            ):
                shutdownBgpPeerList.append(('default', peer))
                bgpASN = bgpEvpnSummary['vrfs']['default']['asn']

    # Create the list of commands to run on the switch
    cmds = [
        "enable",
        "configure",
        f"router bgp {bgpASN}"
    ]
    for (vrf, peer) in shutdownBgpPeerList:
        if vrf != "default":
            cmds.append(f"vrf {vrf}")
        cmds.append(f"neighbor {peer} shutdown")

    # Record the commands used to shut down the bgp peers into the cloudvision database
    # for reversal later.
    # Note in the case of a failure in the list of commands this will still be written in case some
    # of the commands succeeded before encountering the failure

    # NOTE: This can be overwritten/accessed by other actions.
    # This action should be followed by the Restore Shut Unestablished BGP Peers
    # action to guarantee that the commands run here are reverted
    client: GRPCClient = ctx.getCvClient()

    ts = Timestamp()
    ts.GetCurrentTime()
    deviceId = ctx.getDevice().id if ctx.getDevice() else None
    key = f"{hostname}-{deviceId}-commands" if deviceId else f"{hostname}-commands"
    update = [(key, cmds)]
    path = ["changecontrol", "actionTempStorage", "shut-bgp-action"]
    client.publish(dId="cvp", notifs=[create_notification(ts, path, updates=update)])

    cmdOut = ctx.runDeviceCmds(cmds)
    # check to ensure that none of the commands failed
    errs: List[str] = [resp.get('error') for resp in cmdOut if resp.get('error')]
    if errs:
        raise ActionFailed(f"Failed to shut down all peers with: {errs[0]}")

    ctx.info("Inactive BGP peers successfully shutdown")
else:
    ctx.info("No inactive BGP peers to shutdown")
