#!/bin/bash
TAG=$(date '+%Y%m%d')
docker build -t rzarajczyk/smart-devices-to-graphite:$TAG .
docker tag rzarajczyk/smart-devices-to-graphite:$TAG rzarajczyk/smart-devices-to-graphite:latest
