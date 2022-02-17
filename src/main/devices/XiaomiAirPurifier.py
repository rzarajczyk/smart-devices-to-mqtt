import logging

from apscheduler.schedulers.base import BaseScheduler
from homie.device_base import Device_Base
from miio import DeviceException
from miio.airpurifier import AirPurifier
from miio.airpurifier import OperationMode

from homie_helpers import add_property_float, add_property_enum


class XiaomiAirPurifier(Device_Base):
    def __init__(self, device_id, config, mqtt_settings, scheduler: BaseScheduler):
        super().__init__(device_id=device_id, name="Xiaomi Air Purifier 2", mqtt_settings=mqtt_settings)
        self.device = AirPurifier(
            ip=config['ip'],
            token=config['token']
        )

        self.property_temperature = add_property_float(self, "temperature", unit="°C")
        self.property_humidity = add_property_float(self, "humidity", unit="%", min_value=0, max_value=100)
        self.property_speed = add_property_enum(self, "speed",
                                                values=["off", "silent", "1", "2", "3", "4", "5", "6", "7", "8", "9",
                                                        "10", "11", "12", "13", "14", "15", "16", "auto"],
                                                set_handler=self.set_speed,
                                                parent_node_id="speed")
        self.start()
        scheduler.add_job(self.refresh, 'interval', seconds=config['fetch-interval-seconds'])

    def refresh(self):
        try:
            status = self.device.status()
            speed = self._create_speed(is_on=status.is_on, mode=status.mode, favorite_level=status.favorite_level)
            self.property_temperature.value = status.temperature
            self.property_humidity.value = status.humidity
            self.property_speed.value = speed
        except DeviceException as e:
            logging.getLogger('XiaomiAirPurifier').warning("Device unreachable: %s" % str(e))
            self.property_temperature.value = -1
            self.property_humidity.value = -1
            self.property_speed.value = 'off'

    @staticmethod
    def _create_speed(is_on, mode: OperationMode, favorite_level: int):
        if not is_on:
            return 'off'
        if mode != OperationMode.Favorite:
            return str(mode.value).lower()
        return str(favorite_level)

    def set_speed(self, speed):
        print("Setting speed to %s" % speed)
        if type(speed) == int or speed.isnumeric():
            self.device.set_favorite_level(int(speed))
            self.device.set_mode(OperationMode.Favorite)
        elif speed == 'off':
            self.device.off()
        elif speed == 'auto':
            self.device.set_mode(OperationMode.Auto)
        elif speed == 'silent':
            self.device.set_mode(OperationMode.Silent)
        else:
            raise Exception("Unsupported speed: %s" % speed)
