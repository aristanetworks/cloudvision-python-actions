# Copyright (c) 2022 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

from time import sleep
from cloudvision.Connector.grpc_client import GRPCClient, create_query
from cloudvision.cvlib import ActionFailed

path = ctx.action.args.get("path").split("/")
dataset = ctx.action.args.get("dataset")
key = ctx.action.args.get("key")
value = ctx.action.args.get("value")
attempts = ctx.action.args.get("attempts")
if attempts.isnumeric():
    attempts = int(attempts)
else:
    raise ActionFailed("'attempts' arg must be a numeric value")
interval = ctx.action.args.get("interval")
if interval.isnumeric():
    interval = int(interval)
else:
    raise ActionFailed("'interval' arg must be a numeric value")

client: GRPCClient = ctx.getCvClient()

query = [create_query([(path, [key])], dataset)]
for i in range(attempts):
    res = list(client.get(query))
    if res:
        kvp = res[0]["notifications"][0]["updates"]
        if key in kvp:
            if (not value) or (kvp[key] == value):
                break
            ctx.warning(f"Key {key} at path {'/'.join(path)} contains unexpected value {kvp[key]}")
    sleep(interval)
else:
    if value:
        err = f"Value {value} not found at key {key} at path {'/'.join(path)}"
    else:
        err = f"Key {key} not found at path {'/'.join(path)}"
    raise ActionFailed(err)
