# mqtt-to-graphite

Smart Devices integration via MQTT.

## Not recommended to general usage!
This code is written mainly for my personal purpose. I do not take any responsibility for this code,
and I will not provide any support for it. If you really want to use it - ok, but make sure you know
what you're doing.

### Usage
Build:
```shell
docker build -t rzarajczyk/smart-devices-to-mqtt:<<newtag>> .
docker tag rzarajczyk/smart-devices-to-mqtt:<<newtag>> rzarajczyk/mqtt-to-graphite:latest
```
Run:
```shell
docker run -it --rm  --network="host" --name smart-devices-to-mqtt -v $(pwd)/config:/smart-devices-to-mqtt/config -v $(pwd)/logs:/smart-devices-to-mqtt/logs rzarajczyk/smart-devices-to-mqtt:latest
```
Directories to mount:
- `/smart-devices-to-mqtt/config` - it will contain config file. If directory is empty, sample config will be created.
- `/smart-devices-to-mqtt/logs` - it will contain log file.

