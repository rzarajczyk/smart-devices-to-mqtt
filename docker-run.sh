#!/bin/bash
docker run -it --rm  \
    --name smart-devices-to-mqtt \
    -v $(pwd)/config:/smart-devices-to-mqtt/config \
    rzarajczyk/smart-devices-to-mqtt:latest bash
