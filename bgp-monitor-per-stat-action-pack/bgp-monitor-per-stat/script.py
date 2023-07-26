# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

from time import sleep

from google.protobuf.timestamp_pb2 import Timestamp
from cloudvision.Connector.grpc_client import create_query
from cloudvision.Connector.codec import Path, Wildcard
from cloudvision.cvlib import ActionFailed


FIELD_ACTIVE = "Active"
FIELD_CONN = "Connect"
FIELD_EST = "Established"
FIELD_IDLE = "Idle"
FIELD_OCONF = "OpenConfirm"
FIELD_OSENT = "OpenSent"
FIELD_UNKNOWN = "Unknown"


BGP_STAT_FIELDS = [
    FIELD_ACTIVE, FIELD_CONN, FIELD_EST, FIELD_IDLE, FIELD_OCONF, FIELD_OSENT, FIELD_UNKNOWN
]


def extractDiffArgs(args) -> dict:
    '''
    Extracts the expected_difference_* arguments into a dict for later comparison
    '''
    expectedStatsDiff = {}

    if expectedStatsDiffActive := args.get("expected_difference_active"):
        expectedStatsDiff[FIELD_ACTIVE] = int(expectedStatsDiffActive)
    if expectedStatsDiffConnect := args.get("expected_difference_connect"):
        expectedStatsDiff[FIELD_CONN] = int(expectedStatsDiffConnect)
    if expectedStatsDiffEst := args.get("expected_difference_established"):
        expectedStatsDiff[FIELD_EST] = int(expectedStatsDiffEst)
    if expectedStatsDiffIdle := args.get("expected_difference_idle"):
        expectedStatsDiff[FIELD_IDLE] = int(expectedStatsDiffIdle)
    if expectedStatsDiffOpenConfirm := args.get("expected_difference_open_confirm"):
        expectedStatsDiff[FIELD_OCONF] = int(expectedStatsDiffOpenConfirm)
    if expectedStatsDiffOpenSent := args.get("expected_difference_open_sent"):
        expectedStatsDiff[FIELD_OSENT] = int(expectedStatsDiffOpenSent)
    if expectedStatsDiffUnknown := args.get("expected_difference_unknown"):
        expectedStatsDiff[FIELD_UNKNOWN] = int(expectedStatsDiffUnknown)

    return expectedStatsDiff


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


def computeActualDiff(prevStats, currentStats, useVrfCounts) -> dict:
    # Create a dict of the actual diffs present in the stats (combining all vrf
    # fields of the same type, etc.)
    actualDiff = {}
    for stat, prevStatCount in prevStats.items():
        # VRF stat names end with _<stat>, so in the case where we have a vrf stat,
        # need to prune the vrf name from the stat
        actDiffKey: str = stat
        if useVrfCounts and actDiffKey not in BGP_STAT_FIELDS:
            for field in BGP_STAT_FIELDS:
                if actDiffKey.endswith(f"_{field}"):
                    actDiffKey = field
                    break
        # Account for when we have multiple counts being tracked (as in the vrf case)
        if currentActStatDiffVal := actualDiff.get(actDiffKey):
            actualDiff[actDiffKey] = currentActStatDiffVal + currentStats[stat] - prevStatCount
        else:
            actualDiff[actDiffKey] = currentStats[stat] - prevStatCount

    return actualDiff


# Count the vrf specific BGP peers rather than just the device's BGP peers
# args are always in string format
useVrfCounts = ctx.action.args.get("vrfs") == "True"

# Extract all of the diff counts into a dict for later use
expectedStatsDiff = extractDiffArgs(ctx.action.args)

checkWait = ctx.action.args.get("check_wait")
checkWait = int(checkWait) if checkWait else 60

with ctx.getCvClient() as client:
    ccStartTs = ctx.action.getCCStartTime(client)
    if not ccStartTs:
        raise ActionFailed("No change control ID present")
    ccStart = Timestamp()
    ccStart.FromNanoseconds(int(ccStartTs))

    device = ctx.getDevice()
    if device is None:
        raise ActionFailed("Action must have a device associated with the context")
    if not device.id:
        raise ActionFailed("Action's associated device has no ID attribute")

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
    # The basic query is the global count (the sum of all vrf counts). To avoid double-counting
    # changes (changes in vrf A will reflect in the global counts and be counted as a change of 2),
    # do not include these if the vrfs flag has been passed
    if not useVrfCounts:
        # Do a point in time get to get counts from before the CC
        for batch in client.get(query, start=ccStart, end=ccStart):
            extractBGPStats(batch, prevBGPStats)
    else:
        # Get the vrf counts if parameter set
        for batch in client.get(vrfQuery, start=ccStart, end=ccStart):
            extractBGPStats(batch, prevBGPStats, useVrfCounts)

    ctx.info(f"sleeping for {checkWait} seconds before checking BGP stats again")
    # Wait the timeout before checking again, to allow for # of BGP peers to settle
    sleep(checkWait)

    # Get current bgp stats counts
    currBGPStats = {}
    # The basic query is the global count (the sum of all vrf counts). To avoid double-counting
    # changes (changes in vrf A will reflect in the global counts and be counted as a change of 2),
    # do not include these if the vrfs flag has been passed
    if not useVrfCounts:
        for batch in client.get(query):
            extractBGPStats(batch, currBGPStats)
    else:
        # Get the vrf counts if parameter set
        for batch in client.get(vrfQuery):
            extractBGPStats(batch, currBGPStats, useVrfCounts)

    actualStatsDiff = computeActualDiff(prevBGPStats, currBGPStats, useVrfCounts)

    # Check to ensure the actual difference between the stats match those
    # expected for the stats to check as defined by the user
    for stat, expStatDiff in expectedStatsDiff.items():
        actStatDiff = actualStatsDiff[stat]
        if expStatDiff != actStatDiff:
            err = (f"BGP peer counts across CC for Device {device.id} "
                   f"did not match expected difference of {expectedStatsDiff}. \n"
                   f"Before CC: {prevBGPStats} \n"
                   f"After CC: {currBGPStats} \n"
                   f"Actual diff: {actualStatsDiff}")
            raise ActionFailed(message=err)

ctx.info("BGP stats were stable across change control")
