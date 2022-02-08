#!/bin/bash
TAG=$(date '+%Y%m%d')
docker build -t rzarajczyk/smart-devices-to-mqtt:$TAG .
docker tag rzarajczyk/smart-devices-to-mqtt:$TAG rzarajczyk/smart-devices-to-mqtt:latest
