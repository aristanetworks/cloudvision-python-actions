# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

import math
import statistics

from google.protobuf.timestamp_pb2 import Timestamp
from google.protobuf import wrappers_pb2 as wrapperpb

from cloudvision.cvlib import ActionFailed, TimeoutExpiry

from arista.connectivitymonitor.v1.services import (
    ProbeStatsServiceStub,
    ProbeStatsStreamRequest,
    ProbeStatsRequest
)

from arista.connectivitymonitor.v1 import models
from arista.subscriptions.subscriptions_pb2 import Operation


ONE_SECOND_NS = 1000000000

stub = ctx.getApiClient(ProbeStatsServiceStub)

monitorTimeout = ctx.action.args.get("Monitor Timeout")
timeout = int(monitorTimeout) if monitorTimeout else 300

anomaly_score_threshold = ctx.action.args.get("Anomaly Score Threshold")
anomaly_threshold = int(anomaly_score_threshold) if anomaly_score_threshold else 100

critical_level = ctx.action.args.get("Critical Level")
critical_lvl = int(critical_level) if critical_level else 3

historical_get_duration = ctx.action.args.get("Historical Data Gathering Duration")
get_duration = int(historical_get_duration) if historical_get_duration else 3600

device_id = ctx.action.args.get("DeviceID")
host = ctx.action.args.get("Host")
vrf = ctx.action.args.get("VRF")
source_intf = ctx.action.args.get("Source Interface")
stat = ctx.action.args.get("Statistic")

if not (device_id and host and stat):
    raise ActionFailed("Required arguments not found")

host = host.strip()
stat = stat.casefold().strip()

if stat not in ["latency", "jitter", "http_response", "packet_loss"]:
    raise ActionFailed("Invalid statistic name given")

if timeout < 1 or anomaly_threshold < 0 or critical_lvl < 0 or get_duration < 0:
    raise ActionFailed(("'timeout', 'anomaly_score_threshold', 'critical_level',"
                       " 'historical_get_duration' must all have positive values"))

# convert historical get duration to nanoseconds as the get time
# range only accepts nanosecond timestamps
get_duration_ns = get_duration * ONE_SECOND_NS

probeStatsKey = (f"Device = {device_id}, Host = {host},"
                 f" VRF = {vrf}, Source interface = {source_intf}")

ctx.info((f"Monitoring the Connectivity Monitor probe ({probeStatsKey})"
          f" for anomalies in {stat} for {timeout} seconds"))

with ctx.getCvClient() as client:
    ccStartTs = ctx.action.getCCStartTime(client)
    if not ccStartTs:
        raise ActionFailed("No change control ID present")
    ccStart = Timestamp()
    ccStart.FromNanoseconds(int(ccStartTs))

key = models.ProbeStatsKey(
    device_id=wrapperpb.StringValue(value=device_id),
    host=wrapperpb.StringValue(value=host),
    vrf=wrapperpb.StringValue(value=vrf),
    source_intf=wrapperpb.StringValue(value=source_intf)
)

connectivity_filter = models.ProbeStats(
    key=key
)

prev_hr = int(ccStartTs) - get_duration_ns

get = ProbeStatsRequest(
    key=key,
    time=ccStart
)

get_range = ProbeStatsStreamRequest()

get_range.time.start.FromNanoseconds(prev_hr)
get_range.time.end.FromNanoseconds(int(ccStartTs))

get_range.partial_eq_filter.append(connectivity_filter)

baseline_stats = []

baseline_value = 0

nan_count = 0

for resp in stub.GetAll(get_range, timeout=timeout):
    device_stats = resp.value

    match stat:
        case "latency":
            baseline_value = device_stats.latency_millis.value
        case "jitter":
            baseline_value = device_stats.jitter_millis.value
        case "http_response":
            baseline_value = device_stats.http_response_time_millis.value
        case "packet_loss":
            baseline_value = device_stats.packet_loss_percent.value

    if math.isnan(baseline_value):
        nan_count = nan_count + 1
        continue

    baseline_stats.append(baseline_value)

if nan_count > 0:
    ctx.warning(f"Received NaN {nan_count} times from historical data")

if len(baseline_stats) < 2:
    raise ActionFailed((f"Not enough valid data received for the probe ({probeStatsKey}). "
                        "Requires at least 2 data points, instead received "
                        f"{len(baseline_stats)} data point(s)"))

baseline_stats_mean = statistics.mean(baseline_stats)

baseline_stats_sd = statistics.stdev(baseline_stats)

updates_received = False

valid_stats = True

ctx.debug(f"Baseline {stat} mean: {baseline_stats_mean}, baseline {stat} sd: {baseline_stats_sd},"
          f" anomaly score theshold: {anomaly_threshold}, critical level: {critical_lvl}")


def monitor():
    subscribe = ProbeStatsStreamRequest()

    subscribe.partial_eq_filter.append(connectivity_filter)

    cusum_hi = 0
    cusum_lo = 0

    latest_stat = 0

    global updates_received
    global valid_stats

    for resp in stub.Subscribe(subscribe, timeout=timeout):
        # Discard anything that is not the initial and update phase of subscribe
        if resp.type not in {Operation.INITIAL, Operation.UPDATED}:
            continue

        if resp.type is Operation.UPDATED:
            updates_received = True

        device_stats = resp.value

        match stat:
            case "latency":
                latest_stat = device_stats.latency_millis.value
            case "jitter":
                latest_stat = device_stats.jitter_millis.value
            case "http_response":
                latest_stat = device_stats.http_response_time_millis.value
            case "packet_loss":
                latest_stat = device_stats.packet_loss_percent.value

        if math.isnan(latest_stat):
            # Set valid_stats to false so action will fail if last data point is NaN
            valid_stats = False
            continue
        else:
            valid_stats = True

        # when there is no deviation in baseline stats,
        # any value greater than 0 is infinite deviation
        if baseline_stats_sd == 0:
            if latest_stat == 0:
                continue
            raise ActionFailed(f"Connectivity monitor probe '{probeStatsKey}' detected anomaly"
                               f" for {stat} statistic")

        else:
            # We use a statistical approach here known as CUSUM to detect anomalies,
            # more information can be found here: https://en.wikipedia.org/wiki/CUSUM
            normalised_stat = (latest_stat - baseline_stats_mean) / baseline_stats_sd

            # calculate the upper and lower CUSUM values
            cusum_hi = max(0, cusum_hi + normalised_stat - critical_lvl)
            cusum_lo = min(0, cusum_lo + normalised_stat + critical_lvl)

            ctx.debug(f"{stat} value: {latest_stat}, normalised value: {normalised_stat},"
                      f" cusum_hi: {cusum_hi}, cusum_lo: {cusum_lo}")

            # fail the action if any of the CUSUM values exceed the threshold value
            if (cusum_hi > anomaly_threshold or abs(cusum_lo) > anomaly_threshold):
                raise ActionFailed(f"Connectivity monitor probe '{probeStatsKey}' detected anomaly"
                                   f" for {stat} statistic for a prolonged period of time")


try:
    ctx.doWithTimeout(monitor, timeout)
# ctx.doWithTimeout raises a TimeoutExpiry when the timeout is exceeded. Handle this here
# All other exceptions raised will fail the script
except TimeoutExpiry:
    # On timeout expiry, if no stat changes have occurred, fail the action
    if not updates_received:
        raise ActionFailed(f"No updates received from probe ({probeStatsKey})")
    # If the last data point is NaN, fail the action
    if not valid_stats:
        raise ActionFailed(f"Invalid stats received for probe ({probeStatsKey}),"
                           f" it is possible that either the probe or interface is down")
