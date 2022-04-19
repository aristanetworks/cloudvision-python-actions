# Copyright (c) 2022 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

from time import sleep
from cloudvision.Connector.grpc_client import GRPCClient, create_query

path = ctx.changeControl.args.get("path").split("/")
dataset = ctx.changeControl.args.get("dataset")
key = ctx.changeControl.args.get("key")
value = ctx.changeControl.args.get("value")
attempts = ctx.changeControl.args.get("attempts")
if attempts.isnumeric():
    attempts = int(attempts)
else:
    err = "Number of attempts must be a numeric value"
    raise ValueError(err)
interval = ctx.changeControl.args.get("interval")
if interval.isnumeric():
    interval = int(interval)
else:
    err = "Interval must be a numeric value"
    raise ValueError(err)

client: GRPCClient = ctx.getCvClient()

query = [create_query([(path, [key])], dataset)]
for i in range(attempts):

    res = list(client.get(query))
    if res:
        kvp = res[0]["notifications"][0]["updates"]
        if key in kvp:
            if (not value) or (kvp[key] == value):
                break
    sleep(interval)
else:
    if value:
        err = f"value {value} not found in key {key} at path {'/'.join(path)}"
    else:
        err = f"key {key} not found in path {'/'.join(path)}"
    raise ValueError(err)
