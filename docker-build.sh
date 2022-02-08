#!/bin/bash
TAG=$1
if [ -z $TAG ]; then
    echo "TAG is required"
    exit 1
fi

docker build -t rzarajczyk/smart-devices-to-graphite:$TAG .
docker tag rzarajczyk/smart-devices-to-graphite:$TAG rzarajczyk/smart-devices-to-graphite:latest
