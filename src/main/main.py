import logging
import os
import shutil
from logging import config as logging_config

import yaml
from apscheduler.schedulers.blocking import BlockingScheduler

from devices.SonyBravia import SonyBravia
from devices.XiaomiAirHumidifier import XiaomiAirHumidifier
from devices.XiaomiAirPurifier import XiaomiAirPurifier
from devices.XiaomiAirQualityMonitor import XiaomiAirQualityMonitor

##

########################################################################################################################

ROOT = os.environ.get('APP_ROOT', ".")

########################################################################################################################
# logging configuration

LOGGER_CONFIGURATION = "%s/config/logging.yaml" % ROOT
if not os.path.isfile(LOGGER_CONFIGURATION):
    shutil.copy("%s/config-defaults/logging.yaml" % ROOT, LOGGER_CONFIGURATION)

with open(LOGGER_CONFIGURATION, 'r') as f:
    config = yaml.full_load(f)
    logging_config.dictConfig(config)

LOGGER = logging.getLogger("main")
LOGGER.info("Starting application!")

########################################################################################################################
# application configuration

CONFIGURATION = "%s/config/application.yaml" % ROOT
if not os.path.isfile(CONFIGURATION):
    shutil.copy("%s/config-defaults/application.yaml" % ROOT, CONFIGURATION)

with open(CONFIGURATION, 'r') as f:
    config = yaml.full_load(f)

    MQTT_SETTINGS = {
        'MQTT_BROKER': config['mqtt']['host'],
        'MQTT_PORT': config['mqtt']['port'],
        'MQTT_USERNAME': config['mqtt']['user'],
        'MQTT_PASSWORD': config['mqtt']['password'],
        'MQTT_SHARE_CLIENT': True
    }

    DEVICES_CONFIG = config['devices']

########################################################################################################################
# core logic


DEVICE_CLASSES = {
    'xiaomi-air-monitor': XiaomiAirQualityMonitor,
    'xiaomi-air-purifier': XiaomiAirPurifier,
    'xiaomi-air-humidifier': XiaomiAirHumidifier,
    'sony-bravia': SonyBravia
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
