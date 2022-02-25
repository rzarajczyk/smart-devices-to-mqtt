#!/bin/bash
TMP=$(mktemp -d)
cp $(pwd)/config/smart-devices-to-mqtt.yaml $TMP
echo "Temp directory is $TMP"
docker run -it --rm  \
    --add-host "mosquitto:192.168.86.159" \
    --name smart-devices-to-mqtt \
    -v $TMP:/smart-devices-to-mqtt/config \
    rzarajczyk/smart-devices-to-mqtt:latest
