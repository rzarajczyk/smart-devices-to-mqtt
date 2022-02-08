#!/bin/bash
docker run -it --rm  --network="host" --name smart-devices-to-graphite -v $(pwd)/config:/smart-devices-to-graphite/config -v $(pwd)/logs:/smart-devices-to-graphite/logs rzarajczyk/smart-devices-to-graphite:latest
