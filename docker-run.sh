#!/bin/bash
docker run -it --rm  \
    --name smart-devices-to-mqtt \
    -v $(pwd)/config:/smart-devices-to-mqtt/config \
    -v $(pwd)/logs:/smart-devices-to-mqtt/logs \
    rzarajczyk/smart-devices-to-mqtt:latest
