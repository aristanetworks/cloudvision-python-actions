# Copyright (c) 2022 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

from cloudvision.cvlib import ActionFailed

from time import sleep
from google.protobuf.timestamp_pb2 import Timestamp
from cloudvision.Connector.grpc_client import create_query
from cloudvision.Connector.codec import Path, Wildcard

CHECK_PEERS_CMDS = ['enable', 'show ip bgp summary vrf all', 'show bgp evpn summary']
ESTABLISHED = "Established"


def extractBGPStats(batch, statsDict, useVrfs=False):
    for notif in batch["notifications"]:
        for stat in notif["updates"]:
            count = notif["updates"][stat]
            # Skip over any path pointers, such as to the vrf counts
            if isinstance(count, Path):
                continue
            # If using vrfs, append the vrf name to the stat to stop overlap
            # The vrf name is the last path element of the notification
            if useVrfs:
                stat = notif['path_elements'][-1] + "_" + stat
            statsDict[stat] = count


def IsStatsDiffExpected(prevStats, currentStats, expectedDiff: int):
    # Check to see if there is a difference in the stats, as expected by the user args
    # This allows for the user to add 2 spines to their network or retire a spine
    actualDiff = 0
    for stat, count in prevStats.items():
        actualDiff = actualDiff + currentStats[stat] - count

    return expectedDiff == actualDiff


# Count the vrf specific BGP peers rather than just the device's BGP peers
# args are always in string format
useVrfCounts = ctx.action.args.get("vrfs") == "True"
expectedStatsDiff = ctx.action.args.get("expected_difference")
# If not set by the user, the arg will be the empty string, so we need to parse
expectedStatsDiff = int(expectedStatsDiff) if expectedStatsDiff else 0
checkWait = ctx.action.args.get("check_wait")
checkWait = int(checkWait) if checkWait else 60
checkEstablished = ctx.action.args.get("check_established") == "True"

with ctx.getCvClient() as client:
    ccStartTs = ctx.action.getCCStartTime(client)
    if not ccStartTs:
        raise ActionFailed("No change control ID present")
    ccStart = Timestamp()
    ccStart.FromNanoseconds(int(ccStartTs))

    device = ctx.getDevice()
    if device is None or device.id is None:
        err = "Missing change control device" if device is None \
            else f"device {device} is missing 'id'"
        raise ActionFailed(err)

    # This block checks for the check_established flag, defaults to False
    # If set to True, this block will check that all BGP peers are "Established"
    # If any BGP peers are not Established, the CC will abort/fail
    failedPeers = []
    if checkEstablished:
        bgpPeerState = ctx.runDeviceCmds(CHECK_PEERS_CMDS)
        errs = [resp.get('error') for resp in bgpPeerState if resp.get('error')]
        if errs:
            raise ActionFailed(
                f"Running action command to check that all BGP peers are established failed with:"
                f" {errs[0]}")

        for vrf in bgpPeerState[1]["response"]["vrfs"]:
            for bgppeer in bgpPeerState[1]["response"]["vrfs"][vrf]["peers"]:
                if (bgpPeerState[1]["response"]["vrfs"][vrf]["peers"][bgppeer]["peerState"]
                   != ESTABLISHED):
                    bgpState = (
                        bgpPeerState[1]["response"]["vrfs"][vrf]["peers"][bgppeer]["peerState"])
                    failedPeers += [{bgppeer: bgpState}]

        for vrf in bgpPeerState[2]["response"]["vrfs"]:
            for evpnpeer in bgpPeerState[2]["response"]["vrfs"][vrf]["peers"]:
                if (bgpPeerState[2]["response"]["vrfs"]["default"]["peers"][evpnpeer]["peerState"]
                   != ESTABLISHED):
                    bgpState = (
                        bgpPeerState[2]["response"]["vrfs"][vrf]["peers"][bgppeer]["peerState"])
                    failedPeers += [{bgppeer: bgpState}]

        if len(failedPeers) > 0:
            raise ActionFailed(f"bgp peer down: {failedPeers}")

    pathElts = [
        "Devices", device.id, "versioned-data", "counts", "bgpState",
    ]
    query = [
        create_query([(pathElts, [])], "analytics")
    ]
    # Create a query for the vrfs
    vrfPathElts = pathElts + ["vrf", Wildcard()]
    vrfQuery = [
        create_query([(vrfPathElts, [])], "analytics")
    ]

    prevBGPStats = {}
    # Do a point in time get to get counts from before the CC
    for batch in client.get(query, start=ccStart, end=ccStart):
        extractBGPStats(batch, prevBGPStats)
    # Get the vrf counts if parameter set
    if useVrfCounts:
        for batch in client.get(vrfQuery, start=ccStart, end=ccStart):
            extractBGPStats(batch, prevBGPStats, useVrfCounts)

    # Wait the timeout before checking again, to allow for # of BGP peers to settle
    sleep(checkWait)

    # Get current bgp stats counts
    currBGPStats = {}
    for batch in client.get(query):
        extractBGPStats(batch, currBGPStats)
    # Get the vrf counts if parameter set
    if useVrfCounts:
        for batch in client.get(vrfQuery):
            extractBGPStats(batch, currBGPStats, useVrfCounts)

    if not IsStatsDiffExpected(prevBGPStats, currBGPStats, expectedStatsDiff):
        err = ("Inconsistent BGP counts for Device {} were not within expected difference of {}.\n"
               "Before CC: {}\n"
               "After CC: {}").format(device.id, expectedStatsDiff, prevBGPStats, currBGPStats)
        raise ActionFailed(err)

ctx.info("BGP stats were stable across change control")
