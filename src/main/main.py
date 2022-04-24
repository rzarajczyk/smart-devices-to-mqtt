import logging
from logging import config as logging_config

import yaml
from apscheduler.schedulers.blocking import BlockingScheduler
from homie_helpers import HomieSettings

from devices.PhilipsHue import PhilipsHue
from devices.PrinterScanner import PrinterScanner
from devices.XiaomiAirHumidifier import XiaomiAirHumidifier
from devices.XiaomiAirPurifier import XiaomiAirPurifier
from devices.XiaomiAirQualityMonitor import XiaomiAirQualityMonitor
########################################################################################################################
# logging configuration

with open("logging.yaml", 'r') as f:
    config = yaml.full_load(f)
    logging_config.dictConfig(config)

LOGGER = logging.getLogger("main")
LOGGER.info("Starting application!")

########################################################################################################################
# application configuration

with open('config/smart-devices-to-mqtt.yaml', 'r') as f:
    config = yaml.full_load(f)

    MQTT_SETTINGS = HomieSettings(
        broker=config['mqtt']['host'],
        port=config['mqtt']['port'],
        username=config['mqtt']['user'],
        password=config['mqtt']['password']
    )

    DEVICES_CONFIG = config['devices']

########################################################################################################################
# core logic


DEVICE_CLASSES = {
    'xiaomi-air-monitor': XiaomiAirQualityMonitor,
    'xiaomi-air-purifier': XiaomiAirPurifier,
    'xiaomi-air-humidifier': XiaomiAirHumidifier,
    'philips-hue': PhilipsHue,
    'printer-scanner': PrinterScanner
}

LOGGER.info('Registered device classes:')
for device_class_name in DEVICE_CLASSES:
    LOGGER.info(' - %s : %s' % (device_class_name, str(DEVICE_CLASSES[device_class_name])))

scheduler = BlockingScheduler(timezone="Europe/Warsaw")

DEVICES = []

for device_id in DEVICES_CONFIG:
    device_config = DEVICES_CONFIG[device_id]
    device_type = device_config['type']
    device_class = DEVICE_CLASSES[device_type]
    LOGGER.info('Creating new device ≪%s≫ of type ≪%s≫' % (device_id, device_type))
    device = device_class(device_id, device_config, MQTT_SETTINGS, scheduler)
    DEVICES.append(device)

LOGGER.info('All created devices:')
for device in DEVICES:
    LOGGER.info(' - %s' % str(device))

scheduler.start()
